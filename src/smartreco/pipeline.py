"""Deterministic workflow — plain-function pipeline (Phase 1; ADK graph wraps
these functions in Phase 2 per docs/core/21).

Per run: trigger gates → journey resolution → BRE → confidence → requirements →
stage → retrieval → matching → readiness → (stubbed) AAR — every step a pure
engine; this module only moves Runtime Objects between them and persists new
versions through the insert-only repository layer. Every run — including SKIP —
writes one workflow_runs row (docs/core/23).
"""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from smartreco import models, repos
from smartreco.models import utcnow
from smartreco.domain.software_buying import BC_TO_REQ, REQ_TO_CAP, REQUIREMENTS
from smartreco.engines.confidence import EvidenceInput, compute_confidence
from smartreco.engines.journey_resolution import resolve
from smartreco.engines.matching import evaluate_readiness, rank_products
from smartreco.engines.patterns import EventView, evaluate_patterns
from smartreco.engines.requirements import derive_requirements
from smartreco.engines.stages import determine_stage
from smartreco.advisor import (
    MalformedResponse,
    assemble_aar_sections,
    generate_sections,
)
from smartreco.domain.software_buying import CAPABILITIES
from smartreco.engines.triggers import TriggerContext, evaluate_trigger
from smartreco.gateway import GatewayUnavailable
from smartreco.policies import PolicyCatalog
from smartreco.retrieval import (
    EmbeddingBackend,
    compose_query_document,
    retrieve_with_refinement,
)

_CAP_NAME = {cap_id: name for cap_id, name, _domain, _narrative in CAPABILITIES}


def _today(now: datetime) -> str:
    return now.strftime("%Y-%m-%d")


def _usage_calls(db: OrmSession, user_id: int, day: str, tier: str) -> int:
    row = db.get(models.AIUsage, (user_id, day, tier))
    return row.calls if row else 0


def record_ai_call(db: OrmSession, user_id: int, tier: str, now: datetime) -> None:
    """Every Tier-classified gateway call increments the counter — including
    failed and malformed calls; they spent budget (data-model §ai_usage)."""
    key = (user_id, _today(now), tier)
    row = db.get(models.AIUsage, key)
    if row is None:
        db.add(models.AIUsage(user_id=user_id, day=key[1], tier=tier, calls=1))
    else:
        row.calls += 1


def _behavior_summary(events: list[models.Event]) -> str:
    """Deterministic plain-language summary of observed behavior for prompts —
    display vocabulary only, sourced from journey events."""
    searches, topics, product_names = [], [], []
    for e in events:
        md = e.event_metadata or {}
        if e.event_type == "SEARCH" and md.get("query"):
            searches.append(str(md["query"]))
        elif md.get("topic"):
            topics.append(str(md["topic"]))
    parts = []
    if searches:
        parts.append("searched for: " + "; ".join(dict.fromkeys(searches)))
    if topics:
        parts.append("read documentation and pages about: "
                     + ", ".join(dict.fromkeys(topics)))
    return ". ".join(parts) or "browsed the catalog"


def _now(now: datetime | None) -> datetime:
    return now or utcnow()


def _entities(events: list[models.Event]) -> set[str]:
    """Deterministic entity set: product IDs, categories, doc topics, search tokens."""
    out: set[str] = set()
    for e in events:
        md = e.event_metadata or {}
        for key in ("product_id", "category", "topic"):
            if md.get(key):
                out.add(str(md[key]).lower())
        if md.get("query"):
            out.update(str(md["query"]).lower().split())
    return out


def _histogram(events: list[models.Event]) -> dict[str, int]:
    hist: dict[str, int] = {}
    for e in events:
        hist[e.event_type] = hist.get(e.event_type, 0) + 1
    return hist


def resolve_sessions(db: OrmSession, policies: PolicyCatalog, user_id: int,
                     now: datetime | None = None) -> None:
    """Assign journey ownership to sessions with unassigned events (core 12).
    Ownership is determined exactly once per session."""
    now = _now(now)
    unassigned_sessions = db.execute(
        select(models.Event.session_id).where(
            models.Event.user_id == user_id, models.Event.journey_id.is_(None)
        ).distinct()
    ).scalars().all()

    for session_id in unassigned_sessions:
        session_row = db.get(models.Session, session_id)
        if session_row is not None and session_row.journey_id:
            repos.assign_journey(db, session_id, session_row.journey_id)
            continue

        session_events = db.execute(
            select(models.Event).where(models.Event.session_id == session_id)
        ).scalars().all()

        candidates = []
        for journey in db.execute(
            select(models.Journey).where(models.Journey.user_id == user_id)
        ).scalars().all():
            j_events = repos.journey_events(db, journey.journey_id)
            last_ts = max((e.ts for e in j_events), default=journey.created_at)
            days_inactive = max(0.0, (now - last_ts).total_seconds() / 86400)
            candidates.append({
                "journey_id": journey.journey_id,
                "lifecycle": journey.lifecycle,
                "entities": _entities(j_events),
                "histogram": _histogram(j_events),
                "days_inactive": days_inactive,
            })

        decision = resolve(_entities(session_events), _histogram(session_events),
                           candidates, policies)
        if decision.action == "CREATE":
            journey_id = f"J-{user_id}-{uuid.uuid4().hex[:8]}"
            db.add(models.Journey(journey_id=journey_id, user_id=user_id,
                                  lifecycle="ACTIVE", created_at=now))
            repos.insert_journey_transition(db, models.JourneyTransition(
                journey_id=journey_id, from_state="NEW", to_state="ACTIVE",
                reason=decision.explanation, policy_version=policies.version, ts=now))
            db.flush()  # journey row must exist before events reference it (FK)
        else:
            journey_id = decision.journey_id
            journey = db.get(models.Journey, journey_id)
            if decision.action == "REACTIVATE":
                repos.insert_journey_transition(db, models.JourneyTransition(
                    journey_id=journey_id, from_state=journey.lifecycle, to_state="ACTIVE",
                    reason=decision.explanation, policy_version=policies.version, ts=now))
                journey.lifecycle = "ACTIVE"

        repos.assign_journey(db, session_id, journey_id)
        if session_row is not None:
            session_row.journey_id = journey_id
    db.commit()
    db.expire_all()  # raw UPDATEs bypass the identity map; drop stale attribute state


def _update_hypotheses(db: OrmSession, policies: PolicyCatalog, journey_id: str,
                       now: datetime) -> dict[str, float]:
    """BRE hypothesis management + Confidence Engine. Returns active
    {concept_id: confidence}."""
    min_evidence = policies.param("POL-BEH-001", "min_supporting_evidence")
    single_min_strength = policies.param("POL-BEH-001", "single_evidence_min_strength").upper()

    evidence = repos.journey_evidence(db, journey_id)
    events_by_id = {e.event_id: e for e in repos.journey_events(db, journey_id)}
    by_concept: dict[str, list[models.Evidence]] = {}
    for ev in evidence:
        for concept in ev.concept_ids:
            by_concept.setdefault(concept, []).append(ev)

    current = repos.current_hypotheses(db, journey_id)
    active: dict[str, float] = {}

    for concept, concept_evidence in by_concept.items():
        strengths = [ev.strength for ev in concept_evidence]
        promoted = len(concept_evidence) >= min_evidence or any(
            _strength_ge(s, single_min_strength) for s in strengths)
        hypothesis_id = f"H-{journey_id}-{concept}"
        existing = current.get(hypothesis_id)
        if not promoted and existing is None:
            continue
        if existing is not None and existing.status == "RETIRED":
            continue  # retired hypotheses contribute nothing (POL-REQ-003)

        seq = [
            EvidenceInput(
                pattern_id=ev.pattern_id,
                strength=ev.strength,
                event_type_composition=tuple(sorted(
                    events_by_id[eid].event_type for eid in ev.supporting_event_ids
                    if eid in events_by_id)),
            )
            for ev in concept_evidence
        ]
        result = compute_confidence(seq, policies)

        if existing is None:
            status = "CREATED"
        elif result.confidence > existing.confidence:
            status = "STRENGTHENED"
        elif result.confidence < existing.confidence:
            status = "WEAKENED"
        else:
            status = "STABLE"

        if existing is None or existing.confidence != result.confidence or existing.status != status:
            version = 1 if existing is None else existing.version + 1
            row = models.Hypothesis(
                hypothesis_id=hypothesis_id, version=version, journey_id=journey_id,
                concept_id=concept, status=status, confidence=result.confidence,
                confidence_explanation=result.explanation, created_at=now)
            repos.insert_hypothesis_version(db, row)
            for ev in concept_evidence:
                db.merge(models.HypothesisEvidence(
                    hypothesis_id=hypothesis_id, evidence_id=ev.evidence_id,
                    relation="SUPPORTING"))
        if status != "RETIRED":
            active[concept] = result.confidence
    return active


def _strength_ge(strength: str, minimum: str) -> bool:
    from smartreco.enums import EVIDENCE_STRENGTH

    return EVIDENCE_STRENGTH.index(strength) >= EVIDENCE_STRENGTH.index(minimum)


def _concept_name(bc_id: str) -> str:
    from smartreco.domain.software_buying import BEHAVIORAL_CONCEPTS

    return BEHAVIORAL_CONCEPTS.get(bc_id, bc_id)


def _tier1_node(db, gateway, policies, user_id, rpkg, requirements, journey_events,
                stage, constraints, tier1_allowed, nodes, now) -> None:
    """Nodes 12a/12b: clarify (NOT_READY) / generate (READY) — Tier 1.
    Cache-first (POL-CACHE-001); budget gate serves the last stored AAR;
    malformed twice / gateway failure → package stands without a fresh AAR."""
    from smartreco.advisor import PROMPT_VERSION_CLARIFY, PROMPT_VERSION_GENERATE

    readiness = rpkg.readiness
    surface = "ONSITE"
    prompt_version = (PROMPT_VERSION_GENERATE if readiness == "READY"
                      else PROMPT_VERSION_CLARIFY)
    node_name = "generate" if readiness == "READY" else "clarify"

    existing = db.execute(
        select(models.AdvisoryResponse).where(
            models.AdvisoryResponse.rpkg_id == rpkg.rpkg_id,
            models.AdvisoryResponse.prompt_version == prompt_version,
            models.AdvisoryResponse.surface == surface)
    ).scalars().first()
    if existing is not None:
        nodes.append({"node": node_name, "class": "tier1", "cache_hit": True})
        return
    if gateway is None:
        nodes.append({"node": node_name, "class": "tier1",
                      "skipped": "gateway unavailable"})
        return
    if not tier1_allowed:
        nodes.append({"node": node_name, "class": "tier1",
                      "skipped": "budget-gated; serving last stored AAR"})
        return

    products = []
    for entry in rpkg.entries[:3]:
        product = db.get(models.Product, entry["product_id"])
        covered = sorted({
            _CAP_NAME.get(cap_id, cap_id)
            for per_req in entry["per_requirement"].values()
            for cap_id in per_req["supported_capability_ids"]})
        products.append({
            "name": product.name, "vendor": product.vendor,
            "coverage": entry["overall_coverage"],
            "covered": covered,
            "missing": [_CAP_NAME.get(c, c) for c in entry["missing_capability_ids"]],
            "narrative": product.business_value_narrative or product.description,
        })
    facts = {
        "products": products,
        "requirements": [
            {"name": REQUIREMENTS.get(r["req_id"], r["req_id"]),
             "priority": r["priority"].title(), "confidence": r["confidence"]}
            for r in requirements],
        "stage": stage,
        "behavior_summary": _behavior_summary(journey_events),
        "alternatives": [
            db.get(models.Product, e["product_id"]).name for e in rpkg.entries[3:]],
        "constraints": constraints,
    }

    try:
        payload, version, calls = generate_sections(gateway, facts, readiness)
    except MalformedResponse as exc:
        for _ in range(2):  # both attempts spent budget
            record_ai_call(db, user_id, "tier1", now)
        nodes.append({"node": node_name, "class": "tier1",
                      "failure": f"malformed twice: {exc}"})
        return
    except GatewayUnavailable as exc:
        record_ai_call(db, user_id, "tier1", now)
        nodes.append({"node": node_name, "class": "tier1", "failure": str(exc)})
        return

    for _ in range(calls):
        record_ai_call(db, user_id, "tier1", now)
    repos.insert_advisory_response(db, models.AdvisoryResponse(
        aar_id=f"AAR-{uuid.uuid4().hex[:10]}", rpkg_id=rpkg.rpkg_id,
        surface=surface, prompt_version=version, model_id=gateway.model,
        sections=assemble_aar_sections(payload, facts, readiness),
        created_at=now))
    nodes.append({"node": node_name, "class": "tier1", "cache_hit": False,
                  "prompt_version": version, "model_id": gateway.model})


def run_workflow(
    db: OrmSession,
    chroma_client,
    backend: EmbeddingBackend,
    policies: PolicyCatalog,
    user_id: int,
    trigger_type: str,
    now: datetime | None = None,
    gateway=None,
) -> models.WorkflowRun:
    """One orchestration workflow execution (Core 21 shape, plain functions).
    gateway=None runs fully deterministic (Tier 1/2 degrade per Core 21/23)."""
    now = _now(now)
    run_id = f"WR-{uuid.uuid4().hex[:12]}"
    nodes: list[dict] = []

    # --- Trigger gates ---
    unprocessed = db.execute(
        select(models.Event).where(
            models.Event.user_id == user_id,
            models.Event.processed_at.is_(None),
            models.Event.signal_class.in_(("HIGH", "MEDIUM")))
    ).scalars().all()
    newest_age = min(
        ((now - e.received_at).total_seconds() for e in unprocessed), default=1e9)
    last_run_ts = db.execute(
        select(func.max(models.WorkflowRun.finished_at)).where(
            models.WorkflowRun.user_id == user_id,
            models.WorkflowRun.status == "COMPLETED")
    ).scalar()
    in_flight = db.execute(
        select(func.count()).select_from(models.WorkflowRun).where(
            models.WorkflowRun.user_id == user_id,
            models.WorkflowRun.status == "RUNNING")
    ).scalar()

    ctx = TriggerContext(
        unprocessed_high_medium_events=len(unprocessed),
        newest_event_age_seconds=newest_age,
        seconds_since_last_run=(now - last_run_ts).total_seconds() if last_run_ts else None,
        run_in_flight=bool(in_flight),
        tier1_calls_today=_usage_calls(db, user_id, _today(now), "tier1"),
        tier2_calls_today=_usage_calls(db, user_id, _today(now), "tier2"),
    )
    decision = evaluate_trigger(trigger_type, ctx, policies)
    gates = {"trigger": trigger_type, "decision": decision.reason,
             "tier1_allowed": decision.tier1_allowed, "tier2_allowed": decision.tier2_allowed}

    if not decision.run:
        run = models.WorkflowRun(run_id=run_id, user_id=user_id, journey_id=None,
                                 trigger_type=trigger_type, gates=gates, nodes=[],
                                 policy_version=policies.version, status="SKIPPED",
                                 started_at=now, finished_at=now)
        repos.insert_workflow_run(db, run)
        db.commit()
        return run

    # --- Journey resolution ---
    resolve_sessions(db, policies, user_id, now)
    target = db.execute(
        select(models.Event).where(
            models.Event.user_id == user_id, models.Event.processed_at.is_(None),
            models.Event.journey_id.is_not(None))
        .order_by(models.Event.ts.desc())
    ).scalars().first()
    if target is None:
        run = models.WorkflowRun(run_id=run_id, user_id=user_id, journey_id=None,
                                 trigger_type=trigger_type, gates=gates, nodes=[],
                                 policy_version=policies.version, status="SKIPPED",
                                 started_at=now, finished_at=now)
        repos.insert_workflow_run(db, run)
        db.commit()
        return run
    journey_id = target.journey_id
    nodes.append({"node": "journey_resolution", "class": "deterministic"})

    # --- BRE: pattern evaluation + evidence dedup ---
    journey_events = repos.journey_events(db, journey_id)
    views = [EventView(event_id=e.event_id, event_type=e.event_type,
                       session_id=e.session_id, metadata=e.event_metadata or {})
             for e in journey_events]
    drafts = evaluate_patterns(views, policies)
    existing_keys = {
        (ev.pattern_id, tuple(sorted(ev.supporting_event_ids)))
        for ev in repos.journey_evidence(db, journey_id)
    }
    new_count = 0
    for draft in drafts:
        if draft.dedup_key in existing_keys:
            continue
        existing_keys.add(draft.dedup_key)  # same draft may surface once per session window
        new_count += 1
        repos.insert_evidence(db, models.Evidence(
            evidence_id=f"BE-{uuid.uuid4().hex[:10]}",
            journey_id=journey_id, pattern_id=draft.pattern_id,
            strength=draft.strength,
            supporting_event_ids=sorted(draft.supporting_event_ids),
            concept_ids=draft.concept_ids, explanation=draft.explanation,
            created_at=now))
    db.commit()
    nodes.append({"node": "behavioral_reasoning", "class": "deterministic",
                  "new_evidence": new_count})

    # --- Confidence (hypothesis versions) ---
    active = _update_hypotheses(db, policies, journey_id, now)
    db.commit()
    nodes.append({"node": "confidence", "class": "deterministic",
                  "active_hypotheses": {k: v for k, v in sorted(active.items())}})

    # --- Stage ---
    evidence_dicts = [
        {"evidence_id": ev.evidence_id, "pattern_id": ev.pattern_id,
         "strength": ev.strength, "concept_ids": ev.concept_ids}
        for ev in repos.journey_evidence(db, journey_id)
    ]
    event_types = [e.event_type for e in journey_events]
    stage, stage_conf, stage_explanation = determine_stage(
        evidence_dicts, active, event_types, policies)
    latest_stage = db.execute(
        select(models.JourneyStage).where(models.JourneyStage.journey_id == journey_id)
        .order_by(models.JourneyStage.version.desc())
    ).scalars().first()
    if latest_stage is None or latest_stage.stage != stage:
        repos.insert_journey_stage(db, models.JourneyStage(
            journey_id=journey_id,
            version=1 if latest_stage is None else latest_stage.version + 1,
            stage=stage, confidence=stage_conf, explanation=stage_explanation,
            created_at=now))
    nodes.append({"node": "journey_stage", "class": "deterministic", "stage": stage})

    # --- Requirements ---
    requirements = derive_requirements(active, BC_TO_REQ, stage, policies)
    latest_rp = db.execute(
        select(models.RequirementProfile)
        .where(models.RequirementProfile.journey_id == journey_id)
        .order_by(models.RequirementProfile.version.desc())
    ).scalars().first()
    if latest_rp is None or latest_rp.requirements != requirements:
        rp = models.RequirementProfile(
            rp_id=f"RP-{uuid.uuid4().hex[:10]}", journey_id=journey_id,
            version=1 if latest_rp is None else latest_rp.version + 1,
            requirements=requirements, created_at=now)
        repos.insert_requirement_profile(db, rp)
        latest_rp = rp
    db.commit()
    nodes.append({"node": "requirements", "class": "deterministic",
                  "published": [r["req_id"] for r in requirements]})

    # --- decide_retrieve → retrieve/evaluate/refine (Tier 2) → match → readiness ---
    high_signal = sum(1 for e in journey_events if e.signal_class == "HIGH")
    readiness = evaluate_readiness(requirements, high_signal, policies)
    constraints = {}
    if not any(e.event_type == "PRICING_VIEWED" for e in journey_events):
        constraints["budget"] = "Unknown"  # POL-REC-004

    cs = None
    published_entries: list[dict] = []
    if requirements:
        ttl = policies.param("POL-RETR-003", "ttl_seconds")
        cached_cs = db.execute(
            select(models.CandidateSet)
            .where(models.CandidateSet.journey_id == journey_id,
                   models.CandidateSet.rp_id == latest_rp.rp_id)
            .order_by(models.CandidateSet.created_at.desc())
        ).scalars().first()
        cache_valid = (cached_cs is not None
                       and (now - cached_cs.created_at).total_seconds() <= ttl)

        if cache_valid:
            cs = cached_cs
            nodes.append({"node": "retrieve", "class": "tier2",
                          "cache_hit": True, "candidates": len(cs.candidates)})
        else:
            concept_names = sorted(
                f"{_concept_name(c)}" for c in active)
            recent_terms = list(dict.fromkeys(
                str((e.event_metadata or {}).get("query"))
                for e in journey_events
                if e.event_type == "SEARCH" and (e.event_metadata or {}).get("query")))
            query_document = compose_query_document(
                requirements, concept_names, stage, recent_terms, REQUIREMENTS)
            tier2_budget = policies.param("POL-TRIG-003", "tier2_calls_per_user_per_day")

            def _tier2_call():
                record_ai_call(db, user_id, "tier2", now)

            try:
                if backend is gateway:  # gateway embeddings spend Tier 2 budget
                    _tier2_call()
                candidates, history, final_query = retrieve_with_refinement(
                    db, chroma_client, backend, gateway, query_document, policies,
                    tier2_llm_allowed=(
                        decision.tier2_allowed
                        and _usage_calls(db, user_id, _today(now), "tier2") < tier2_budget),
                    record_tier2_call=_tier2_call)
                cs = models.CandidateSet(
                    cs_id=f"CS-{uuid.uuid4().hex[:10]}", journey_id=journey_id,
                    rp_id=latest_rp.rp_id, query_document=final_query,
                    params={"top_k": policies.param("POL-RETR-001", "top_k"),
                            "query_template": "qd-v1"},
                    candidates=candidates, refinement_history=history, created_at=now)
                repos.insert_candidate_set(db, cs)
                db.flush()
                nodes.append({"node": "retrieve", "class": "tier2", "cache_hit": False,
                              "candidates": len(candidates),
                              "refinements": len([h for h in history
                                                  if h.get("action") == "refine"])})
            except GatewayUnavailable as exc:
                # Tier 2 failure ladder: best available cached set, else
                # full-catalog matching with a null Candidate Set ref (Core 21)
                cs = cached_cs
                nodes.append({"node": "retrieve", "class": "tier2", "cache_hit": cs is not None,
                              "failure": str(exc)})

        if cs is not None:
            candidate_ids = [c["product_id"] for c in cs.candidates]
        else:
            candidate_ids = db.execute(
                select(models.Product.product_id).where(
                    models.Product.sync_status == "SYNCED",
                    models.Product.deleted_at.is_(None))
            ).scalars().all()
            nodes.append({"node": "match_fallback", "class": "deterministic",
                          "mode": "full-catalog"})

        product_caps: dict[str, set[str]] = {}
        for product_id in candidate_ids:
            caps = db.execute(
                select(models.ProductCapability.capability_id).where(
                    models.ProductCapability.product_id == product_id)
            ).scalars().all()
            product_caps[product_id] = set(caps)
        entries = rank_products(requirements, list(candidate_ids), product_caps,
                                REQ_TO_CAP, policies)
        top = policies.param("POL-REC-003", "top_entries")
        alternatives = policies.param("POL-REC-003", "max_alternatives")
        published_entries = entries[: top + alternatives]

    latest_pkg = db.execute(
        select(models.RecommendationPackage)
        .where(models.RecommendationPackage.journey_id == journey_id)
        .order_by(models.RecommendationPackage.created_at.desc())
    ).scalars().first()
    if (latest_pkg is None or latest_pkg.entries != published_entries
            or latest_pkg.readiness != readiness):
        rpkg = models.RecommendationPackage(
            rpkg_id=f"RPKG-{uuid.uuid4().hex[:10]}", journey_id=journey_id,
            rp_id=latest_rp.rp_id if latest_rp else None,
            cs_id=cs.cs_id if cs is not None else None,
            entries=published_entries, readiness=readiness, constraints=constraints,
            policy_version=policies.version, created_at=now)
        repos.insert_recommendation_package(db, rpkg)
        db.flush()  # AAR row references the package; enforce insert order
    else:
        rpkg = latest_pkg
    nodes.append({"node": "match", "class": "deterministic", "readiness": readiness})

    # --- readiness_gate → clarify / generate (Tier 1) ---
    _tier1_node(db, gateway, policies, user_id, rpkg, requirements, journey_events,
                stage, constraints, decision.tier1_allowed, nodes, now)

    # --- Finish: stamp processed, record run ---
    repos.stamp_processed(db, [e.event_id for e in unprocessed], now)
    run = models.WorkflowRun(
        run_id=run_id, user_id=user_id, journey_id=journey_id,
        trigger_type=trigger_type, gates=gates, nodes=nodes,
        policy_version=policies.version, status="COMPLETED",
        started_at=now, finished_at=now)
    repos.insert_workflow_run(db, run)
    db.commit()
    return run
