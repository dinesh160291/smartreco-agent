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
from smartreco.engines.triggers import TriggerContext, evaluate_trigger
from smartreco.policies import PolicyCatalog
from smartreco.retrieval import EmbeddingBackend, retrieve_candidates

STUB_PROMPT_VERSION = "stub-1"


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


def _query_document(requirements: list[dict]) -> str:
    from smartreco.retrieval import _CAP_BY_ID

    lines = []
    for entry in requirements:
        lines.append(REQUIREMENTS.get(entry["req_id"], entry["req_id"]))
        for cap_id in REQ_TO_CAP.get(entry["req_id"], {}):
            name, _domain, narrative = _CAP_BY_ID[cap_id]
            lines.append(f"{name}. {narrative}")
    return "\n".join(lines)


def run_workflow(
    db: OrmSession,
    chroma_client,
    backend: EmbeddingBackend,
    policies: PolicyCatalog,
    user_id: int,
    trigger_type: str,
    now: datetime | None = None,
) -> models.WorkflowRun:
    """One orchestration workflow execution (Core 21 shape, plain functions)."""
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
        tier1_calls_today=0,  # AI calls arrive in Phase 2; budgets recorded then
        tier2_calls_today=0,
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

    # --- Retrieval (candidate set) + Matching + Readiness + stubbed AAR ---
    rpkg = None
    if requirements:
        query_document = _query_document(requirements)
        candidates = retrieve_candidates(db, chroma_client, backend, query_document, policies)
        cs = models.CandidateSet(
            cs_id=f"CS-{uuid.uuid4().hex[:10]}", journey_id=journey_id,
            rp_id=latest_rp.rp_id, query_document=query_document,
            params={"top_k": policies.param("POL-RETR-001", "top_k")},
            candidates=candidates, refinement_history=[], created_at=now)
        repos.insert_candidate_set(db, cs)
        nodes.append({"node": "retrieval", "class": "tier2-deterministic",
                      "candidates": len(candidates)})

        product_caps: dict[str, set[str]] = {}
        for c in candidates:
            caps = db.execute(
                select(models.ProductCapability.capability_id).where(
                    models.ProductCapability.product_id == c["product_id"])
            ).scalars().all()
            product_caps[c["product_id"]] = set(caps)
        entries = rank_products(requirements, [c["product_id"] for c in candidates],
                                product_caps, REQ_TO_CAP, policies)
        top = policies.param("POL-REC-003", "top_entries")
        alternatives = policies.param("POL-REC-003", "max_alternatives")
        published_entries = entries[: top + alternatives]

        high_signal = sum(1 for e in journey_events if e.signal_class == "HIGH")
        readiness = evaluate_readiness(requirements, high_signal, policies)

        constraints = {}
        if not any(e.event_type == "PRICING_VIEWED" for e in journey_events):
            constraints["budget"] = "Unknown"  # POL-REC-004

        latest_pkg = db.execute(
            select(models.RecommendationPackage)
            .where(models.RecommendationPackage.journey_id == journey_id)
            .order_by(models.RecommendationPackage.created_at.desc())
        ).scalars().first()
        if (latest_pkg is None or latest_pkg.entries != published_entries
                or latest_pkg.readiness != readiness):
            rpkg = models.RecommendationPackage(
                rpkg_id=f"RPKG-{uuid.uuid4().hex[:10]}", journey_id=journey_id,
                rp_id=latest_rp.rp_id, cs_id=cs.cs_id, entries=published_entries,
                readiness=readiness, constraints=constraints,
                policy_version=policies.version, created_at=now)
            repos.insert_recommendation_package(db, rpkg)
            db.flush()  # AAR row references the package; enforce insert order
        else:
            rpkg = latest_pkg
        nodes.append({"node": "matching", "class": "deterministic",
                      "readiness": readiness})

        aar_exists = db.execute(
            select(models.AdvisoryResponse).where(
                models.AdvisoryResponse.rpkg_id == rpkg.rpkg_id,
                models.AdvisoryResponse.prompt_version == STUB_PROMPT_VERSION,
                models.AdvisoryResponse.surface == "ONSITE")
        ).scalars().first()
        if aar_exists is None and readiness == "READY":
            repos.insert_advisory_response(db, models.AdvisoryResponse(
                aar_id=f"AAR-{uuid.uuid4().hex[:10]}", rpkg_id=rpkg.rpkg_id,
                surface="ONSITE", prompt_version=STUB_PROMPT_VERSION, model_id="stub",
                sections={"summary": "stubbed advisory response (Phase 2 replaces)"},
                created_at=now))
        nodes.append({"node": "aar", "class": "tier1-stub"})

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
