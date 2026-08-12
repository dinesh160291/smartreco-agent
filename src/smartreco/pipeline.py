"""Deterministic workflow — the 13-node graph as named stage functions
(docs/core/21). Each stage delegates to its owning engine; orchestration never
implements engine logic. The explicit stage list (WORKFLOW_GRAPH) is the
framework-neutral graph contract; the ADK wrapper (smartreco.orchestration)
binds the same stages to the agent framework — swapping frameworks changes no
engine, contract, or Runtime Object.

Per run: trigger gates → resolve_journey → reason → score_confidence →
infer_requirements → resolve_stage → decide_retrieve/retrieve/evaluate/refine
(bounded loop inside the Semantic Retrieval Engine) → match → readiness_gate →
clarify/generate (Tier 1) → persist. Every run — including SKIP — writes one
workflow_runs row (docs/core/23).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as OrmSession

from smartreco import models, repos
from smartreco.advisor import (
    MalformedResponse,
    assemble_aar_sections,
    generate_sections,
)
from smartreco.domain.software_buying import (
    BC_TO_REQ, CAPABILITIES, INTENT_CONCEPTS, REQ_TO_CAP, REQUIREMENTS)
from smartreco.engines.confidence import EvidenceInput, compute_confidence
from smartreco.engines.journey_resolution import resolve, subject_abandoned
from smartreco.engines.learning import derive_traits, reinforced_strength
from smartreco.engines.lifecycle import evaluate_closure, should_go_dormant
from smartreco.engines.matching import evaluate_readiness, rank_products
from smartreco.engines.patterns import EventView, evaluate_patterns
from smartreco.engines.requirements import derive_requirements
from smartreco.engines.stages import apply_regression, determine_stage
from smartreco.engines.triggers import TriggerContext, evaluate_trigger
from smartreco.gateway import GatewayUnavailable
from smartreco.models import utcnow
from smartreco.policies import PolicyCatalog
from smartreco.retrieval import (
    EmbeddingBackend,
    catalog_index_version,
    compose_query_document,
    retrieve_with_refinement,
)

_CAP_NAME = {cap_id: name for cap_id, name, _domain, _narrative in CAPABILITIES}


# ---- shared helpers ----

def _now(now: datetime | None) -> datetime:
    return now or utcnow()


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
        # Sessions run autoflush=False and Session.get consults the identity
        # map, so a row added earlier in this same run is invisible to it —
        # the second Tier-2 call would add a duplicate key and the flush would
        # fail the whole run. Look through the pending inserts instead of
        # flushing: flushing here would take SQLite's write lock early and
        # hold it across the gateway call that follows, which turns ordinary
        # concurrency into "database is locked" for everyone else.
        row = next((pending for pending in db.new
                    if isinstance(pending, models.AIUsage)
                    and (pending.user_id, pending.day, pending.tier) == key), None)
    if row is None:
        db.add(models.AIUsage(user_id=user_id, day=key[1], tier=tier, calls=1))
    else:
        row.calls += 1


def _behavior_summary(events: list[models.Event]) -> str:
    """Deterministic plain-language summary of observed behavior for prompts —
    display vocabulary only, sourced from journey events."""
    searches, topics = [], []
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


def _concept_name(bc_id: str) -> str:
    from smartreco.domain.software_buying import BEHAVIORAL_CONCEPTS

    return BEHAVIORAL_CONCEPTS.get(bc_id, bc_id)


def _strength_ge(strength: str, minimum: str) -> bool:
    from smartreco.enums import EVIDENCE_STRENGTH

    return EVIDENCE_STRENGTH.index(strength) >= EVIDENCE_STRENGTH.index(minimum)


# ---- journey lifecycle: dormancy / closure sweep + learning ----

def apply_closure_learning(db: OrmSession, journey: models.Journey,
                           policies: PolicyCatalog, now: datetime) -> list[str]:
    """POL-LEARN-001: only CLOSED journeys feed the Learning Engine. Traits are
    concept-derived from the journey's final active hypotheses."""
    final = {
        h.concept_id: h.confidence
        for h in repos.current_hypotheses(db, journey.journey_id).values()
        if h.status != "RETIRED"
    }
    created = []
    for trait in derive_traits(final, policies):
        row = db.get(models.BehavioralTrait, (journey.user_id, trait["trait_name"]))
        if row is None:
            db.add(models.BehavioralTrait(
                user_id=journey.user_id, trait_name=trait["trait_name"],
                strength=reinforced_strength(None, trait["final_confidence"], policies),
                reinforcement_count=1, last_reinforced=now,
                decay_explanation=""))
        else:
            row.strength = reinforced_strength(row.strength, trait["final_confidence"], policies)
            row.reinforcement_count += 1
            row.last_reinforced = now
        created.append(trait["trait_name"])
    return created


def close_journey(db: OrmSession, journey: models.Journey, outcome: str, reason: str,
                  policies: PolicyCatalog, now: datetime) -> None:
    repos.insert_journey_transition(db, models.JourneyTransition(
        journey_id=journey.journey_id, from_state=journey.lifecycle, to_state="CLOSED",
        reason=reason, policy_version=policies.version, ts=now))
    journey.lifecycle = "CLOSED"
    journey.outcome = outcome
    journey.closed_at = now
    apply_closure_learning(db, journey, policies, now)


def lifecycle_sweep(db: OrmSession, policies: PolicyCatalog, user_id: int,
                    now: datetime) -> None:
    """Dormancy + closure evaluation for a user's open journeys (POL-JRES-002/003).
    Time alone never closes; every transition is policy-authorized and logged."""
    journeys = db.execute(
        select(models.Journey).where(models.Journey.user_id == user_id,
                                     models.Journey.lifecycle.in_(("NEW", "ACTIVE", "DORMANT")))
    ).scalars().all()
    for journey in journeys:
        events = repos.journey_events(db, journey.journey_id)
        last_activity = max((e.ts for e in events), default=journey.created_at)
        trial_ts = max((e.ts for e in events if e.event_type == "TRIAL_STARTED"),
                       default=None)
        has_purchase = any(e.event_type == "PURCHASE_COMPLETED" for e in events)

        if journey.lifecycle == "ACTIVE" and should_go_dormant(last_activity, now, policies):
            repos.insert_journey_transition(db, models.JourneyTransition(
                journey_id=journey.journey_id, from_state="ACTIVE", to_state="DORMANT",
                reason="inactive beyond POL-JRES-002 dormancy window",
                policy_version=policies.version, ts=now))
            journey.lifecycle = "DORMANT"

        dormant_since = None
        if journey.lifecycle == "DORMANT":
            dormant_transition = db.execute(
                select(models.JourneyTransition)
                .where(models.JourneyTransition.journey_id == journey.journey_id,
                       models.JourneyTransition.to_state == "DORMANT")
                .order_by(models.JourneyTransition.ts.desc())
            ).scalars().first()
            dormant_since = dormant_transition.ts if dormant_transition else last_activity

        outcome, reason = evaluate_closure(
            lifecycle=journey.lifecycle, has_purchase=has_purchase,
            last_trial_ts=trial_ts, last_activity_ts=last_activity,
            dormant_since=dormant_since, now=now, policies=policies)
        if outcome is not None:
            close_journey(db, journey, outcome, reason, policies, now)
    db.commit()


# ---- journey resolution (node 1 engine work) ----

def _session_has_settled(db: OrmSession, policies: PolicyCatalog, user_id: int,
                         session_id: str, session_events: list[models.Event],
                         now: datetime) -> bool:
    """Has this session said enough for its ownership to be decided? (core 12)

    Ownership is decided exactly once per session, so deciding early is
    deciding wrong permanently: a two-event session scores near-nothing on
    topic and behavioural similarity and forks a journey that the same session,
    a few clicks later, would plainly have continued.

    Settled when any of these holds — the last two exist so deferral is
    bounded, because leaving events unowned forever is no better than filing
    them wrongly:

      * it has at least POL-JRES-001 min_session_events events;
      * a newer session exists, proving this one is over;
      * its last event predates the POL-TRACK-003 inactivity window, so the
        session has timed out and no further events are coming.
    """
    if not session_events:
        return False

    # Nothing to fork from: with no candidate journey the decision is CREATE at
    # two events and at two hundred, so waiting only starves a cold start of
    # the journey it needs (Story 3 — one significant event must still be
    # answered). The guard protects a comparison, and there is none to protect.
    has_candidate = db.execute(
        select(models.Journey.journey_id).where(
            models.Journey.user_id == user_id,
            models.Journey.lifecycle.notin_(("CLOSED", "ARCHIVED")))
    ).scalars().first()
    if has_candidate is None:
        return True

    if len(session_events) >= policies.param("POL-JRES-001", "min_session_events"):
        return True

    last_ts = max(event.ts for event in session_events)
    idle_minutes = policies.param("POL-TRACK-003", "inactivity_minutes")
    if (now - last_ts).total_seconds() >= idle_minutes * 60:
        return True

    newer = db.execute(
        select(models.Event.event_id).where(
            models.Event.user_id == user_id,
            models.Event.session_id != session_id,
            models.Event.ts > last_ts)
    ).scalars().first()
    return newer is not None


def _intent_profile(events: list[models.Event],
                    policies: PolicyCatalog) -> tuple[str | None, set[str]]:
    """(dominant subject, all subjects) for a block of behavior — Decision #056.

    The Domain Pack names the subject-bearing concepts; the platform only asks
    the pattern engine which of them the evidence supports. Dominance is by
    weight of supporting evidence, so a subject touched once does not outrank
    the one the journey is actually about.
    """
    views = [EventView(event_id=e.event_id, event_type=e.event_type,
                       session_id=e.session_id, metadata=e.event_metadata or {})
             for e in events]
    weight: dict[str, int] = {}
    for draft in evaluate_patterns(views, policies):
        for concept_id in set(draft.concept_ids) & INTENT_CONCEPTS:
            weight[concept_id] = max(weight.get(concept_id, 0),
                                     len(draft.supporting_event_ids))
    if not weight:
        return None, set()
    dominant = max(sorted(weight), key=lambda c: weight[c])  # sorted() = deterministic ties
    return dominant, set(weight)


def _resolve_continuation(db: OrmSession, policies: PolicyCatalog, user_id: int,
                          session_id: str, owner_id: str, now: datetime) -> str:
    """Which journey the *new* events of an already-owned session belong to.

    Decision #041 settled journey ownership exactly once per session, which was
    right about the danger it addressed — judging a two-event session forks a
    journey the same session would plainly have continued — and wrong that once
    per session is the only way to avoid it. A shopper who moves from analytics
    to DevOps mid-session was filed under one journey, so both intents shared a
    Requirement Profile and the earlier one kept the higher priority band
    (Decision #056).

    Ownership is now decided once per *settled block* of events rather than
    once per session. The protection is unchanged: a block too small to judge
    inherits, exactly as before.

    Returning to an earlier subject continues that journey rather than opening a
    third — which is the whole point of splitting them, since the abandoned
    journey keeps its hypotheses at the confidence they reached.
    """
    fork_min = policies.param("POL-JRES-001", "fork_min_events")
    window = policies.param("POL-JRES-001", "recent_window_events")
    pending = db.execute(
        select(models.Event).where(
            models.Event.session_id == session_id, models.Event.user_id == user_id,
            models.Event.journey_id.is_(None))
    ).scalars().all()
    if len(pending) < fork_min:
        return owner_id  # too little to judge on — inherit, revisit next run

    # Before and after, sampled from disjoint slices. "Established" must not
    # include the activity it is being compared against, or a long enough new
    # subject simply becomes the dominant one and there is nothing left to
    # abandon (Decision #057).
    combined = list(repos.journey_events(db, owner_id)) + list(pending)
    established, _older_subjects = _intent_profile(combined[:-window], policies)
    _dominant_now, recent_subjects = _intent_profile(combined[-window:], policies)
    if not subject_abandoned(established, recent_subjects):
        return owner_id

    new_intent = recent_subjects
    for journey in db.execute(
        select(models.Journey).where(
            models.Journey.user_id == user_id,
            models.Journey.lifecycle.in_(("NEW", "ACTIVE", "DORMANT")))
    ).scalars().all():
        if journey.journey_id == owner_id:
            continue
        _dominant, subjects = _intent_profile(
            repos.journey_events(db, journey.journey_id), policies)
        if subjects & new_intent:
            if journey.lifecycle == "DORMANT":
                repos.insert_journey_transition(db, models.JourneyTransition(
                    journey_id=journey.journey_id, from_state=journey.lifecycle,
                    to_state="ACTIVE", policy_version=policies.version, ts=now,
                    reason=f"resumed subject within session {session_id} (POL-JRES-004)"))
                journey.lifecycle = "ACTIVE"
            return journey.journey_id

    journey_id = f"J-{user_id}-{uuid.uuid4().hex[:8]}"
    db.add(models.Journey(journey_id=journey_id, user_id=user_id,
                          lifecycle="ACTIVE", created_at=now))
    repos.insert_journey_transition(db, models.JourneyTransition(
        journey_id=journey_id, from_state="NEW", to_state="ACTIVE",
        reason=(f"subject abandoned within session {session_id}: "
                f"{established} -> {sorted(new_intent)} (POL-JRES-004)"),
        policy_version=policies.version, ts=now))
    db.flush()  # journey row must exist before events reference it (FK)
    return journey_id


def resolve_sessions(db: OrmSession, policies: PolicyCatalog, user_id: int,
                     now: datetime | None = None) -> None:
    """Assign journey ownership to sessions with unassigned events (core 12).
    Ownership is determined exactly once per session."""
    now = _now(now)
    lifecycle_sweep(db, policies, user_id, now)  # dormancy/closure before candidacy
    unassigned_sessions = db.execute(
        select(models.Event.session_id).where(
            models.Event.user_id == user_id, models.Event.journey_id.is_(None)
        ).distinct()
    ).scalars().all()

    for session_id in unassigned_sessions:
        session_row = db.get(models.Session, session_id)
        if session_row is not None and session_row.journey_id:
            target = _resolve_continuation(db, policies, user_id, session_id,
                                           session_row.journey_id, now)
            repos.assign_journey(db, session_id, target, user_id)
            session_row.journey_id = target
            continue

        session_events = db.execute(
            select(models.Event).where(models.Event.session_id == session_id)
        ).scalars().all()

        if not _session_has_settled(db, policies, user_id, session_id,
                                    session_events, now):
            continue  # too little to judge on; revisit on a later run

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

        repos.assign_journey(db, session_id, journey_id, user_id)
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
    by_concept: dict[str, list[tuple[models.Evidence, str]]] = {}
    for ev in evidence:
        for concept in ev.concept_ids:
            by_concept.setdefault(concept, []).append((ev, "SUPPORTING"))
        for concept in (ev.contradicts_concept_ids or []):
            by_concept.setdefault(concept, []).append((ev, "CONTRADICTING"))

    current = repos.current_hypotheses(db, journey_id)
    active: dict[str, float] = {}

    for concept, concept_evidence in by_concept.items():
        supporting_only = [ev for ev, rel in concept_evidence if rel == "SUPPORTING"]
        promoted = len(supporting_only) >= min_evidence or any(
            _strength_ge(ev.strength, single_min_strength) for ev in supporting_only)
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
                relation=relation,
            )
            for ev, relation in concept_evidence
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
            for ev, relation in concept_evidence:
                db.merge(models.HypothesisEvidence(
                    hypothesis_id=hypothesis_id, evidence_id=ev.evidence_id,
                    relation=relation))
        if status != "RETIRED":
            active[concept] = result.confidence
    return active


# ---- graph context and stages ----

@dataclass
class WorkflowContext:
    db: OrmSession
    chroma: object
    backend: EmbeddingBackend
    gateway: object
    policies: PolicyCatalog
    user_id: int
    now: datetime
    tier1_allowed: bool
    tier2_allowed: bool
    nodes: list = field(default_factory=list)


def stage_resolve_journey(ctx: WorkflowContext, state: dict) -> bool:
    """Node 1: journey ownership. Returns False to halt (no work)."""
    resolve_sessions(ctx.db, ctx.policies, ctx.user_id, ctx.now)
    target = ctx.db.execute(
        select(models.Event).where(
            models.Event.user_id == ctx.user_id, models.Event.processed_at.is_(None),
            models.Event.journey_id.is_not(None))
        .order_by(models.Event.ts.desc())
    ).scalars().first()
    if target is None:
        return False
    state["journey_id"] = target.journey_id
    state["journey_events"] = repos.journey_events(ctx.db, target.journey_id)
    ctx.nodes.append({"node": "resolve_journey", "class": "deterministic"})
    return True


def stage_reason(ctx: WorkflowContext, state: dict) -> bool:
    """Node 2: BRE pattern evaluation + evidence dedup."""
    journey_id = state["journey_id"]
    views = [EventView(event_id=e.event_id, event_type=e.event_type,
                       session_id=e.session_id, metadata=e.event_metadata or {})
             for e in state["journey_events"]]
    drafts = evaluate_patterns(views, ctx.policies)
    existing_keys = {
        (ev.pattern_id, tuple(sorted(ev.supporting_event_ids)),
         tuple(ev.contradicts_concept_ids or ()))
        for ev in repos.journey_evidence(ctx.db, journey_id)
    }
    new_count = 0
    for draft in drafts:
        if draft.dedup_key in existing_keys:
            continue
        existing_keys.add(draft.dedup_key)  # same draft may surface once per session window
        new_count += 1
        repos.insert_evidence(ctx.db, models.Evidence(
            evidence_id=f"BE-{uuid.uuid4().hex[:10]}",
            journey_id=journey_id, pattern_id=draft.pattern_id,
            strength=draft.strength,
            supporting_event_ids=sorted(draft.supporting_event_ids),
            concept_ids=draft.concept_ids,
            contradicts_concept_ids=list(draft.contradicts),
            explanation=draft.explanation,
            created_at=ctx.now))
    ctx.db.commit()
    ctx.nodes.append({"node": "reason", "class": "deterministic",
                      "new_evidence": new_count})
    return True


def stage_score_confidence(ctx: WorkflowContext, state: dict) -> bool:
    """Node 3: Confidence Engine → hypothesis versions."""
    state["active"] = _update_hypotheses(ctx.db, ctx.policies, state["journey_id"], ctx.now)
    ctx.db.commit()
    ctx.nodes.append({"node": "score_confidence", "class": "deterministic",
                      "active_hypotheses": dict(sorted(state["active"].items()))})
    return True


def stage_infer_requirements(ctx: WorkflowContext, state: dict) -> bool:
    """Node 4: Requirement Engine. Priority banding uses the stored Journey
    Stage (node 5 resolves the new one — canonical core 21 order)."""
    journey_id = state["journey_id"]
    stored_stage = ctx.db.execute(
        select(models.JourneyStage).where(models.JourneyStage.journey_id == journey_id)
        .order_by(models.JourneyStage.version.desc())
    ).scalars().first()
    banding_stage = stored_stage.stage if stored_stage else "Awareness"
    requirements = derive_requirements(state["active"], BC_TO_REQ, banding_stage, ctx.policies)

    latest_rp = ctx.db.execute(
        select(models.RequirementProfile)
        .where(models.RequirementProfile.journey_id == journey_id)
        .order_by(models.RequirementProfile.version.desc())
    ).scalars().first()
    if latest_rp is None or latest_rp.requirements != requirements:
        rp = models.RequirementProfile(
            rp_id=f"RP-{uuid.uuid4().hex[:10]}", journey_id=journey_id,
            version=1 if latest_rp is None else latest_rp.version + 1,
            requirements=requirements, created_at=ctx.now)
        repos.insert_requirement_profile(db=ctx.db, row=rp)
        latest_rp = rp
    ctx.db.commit()
    state["requirements"] = requirements
    state["latest_rp"] = latest_rp
    ctx.nodes.append({"node": "infer_requirements", "class": "deterministic",
                      "published": [r["req_id"] for r in requirements]})
    return True


def stage_resolve_stage(ctx: WorkflowContext, state: dict) -> bool:
    """Node 5: Journey Stage Engine."""
    journey_id = state["journey_id"]
    evidence_dicts = [
        {"evidence_id": ev.evidence_id, "pattern_id": ev.pattern_id,
         "strength": ev.strength, "concept_ids": ev.concept_ids}
        for ev in repos.journey_evidence(ctx.db, journey_id)
    ]
    stage_events = [{"event_type": e.event_type, "metadata": e.event_metadata or {}}
                    for e in state["journey_events"]]
    stage, stage_conf, stage_explanation = determine_stage(
        evidence_dicts, state["active"], stage_events, ctx.policies)
    recent_high = [e.event_type for e in state["journey_events"]
                   if e.signal_class == "HIGH"]
    regressed = apply_regression(stage, recent_high, ctx.policies)
    if regressed is not None:
        stage_explanation = (f"{regressed}: regressed from {stage} — last high-signal "
                             f"events characteristic of an earlier stage (POL-STAGE-002)")
        stage, stage_conf = regressed, 0.0
    latest_stage = ctx.db.execute(
        select(models.JourneyStage).where(models.JourneyStage.journey_id == journey_id)
        .order_by(models.JourneyStage.version.desc())
    ).scalars().first()
    if latest_stage is None or latest_stage.stage != stage:
        repos.insert_journey_stage(ctx.db, models.JourneyStage(
            journey_id=journey_id,
            version=1 if latest_stage is None else latest_stage.version + 1,
            stage=stage, confidence=stage_conf, explanation=stage_explanation,
            created_at=ctx.now))
        ctx.db.commit()
    state["stage"] = stage
    ctx.nodes.append({"node": "resolve_stage", "class": "deterministic", "stage": stage})
    return True


def stage_retrieval(ctx: WorkflowContext, state: dict) -> bool:
    """Nodes 6-9: decide_retrieve → retrieve → evaluate → refine. The bounded
    evaluate→refine loop lives inside the Semantic Retrieval Engine
    (POL-RETR-002); this node delegates and records the loop history.
    Skip branch exists only into a valid cached Candidate Set (core 21)."""
    state["cs"] = None
    if not state["requirements"]:
        return True  # no requirements → nothing to retrieve; Story 3 stays Tier-2-free

    db, journey_id, latest_rp = ctx.db, state["journey_id"], state["latest_rp"]
    ttl = ctx.policies.param("POL-RETR-003", "ttl_seconds")
    cached_cs = db.execute(
        select(models.CandidateSet)
        .where(models.CandidateSet.journey_id == journey_id,
               models.CandidateSet.rp_id == latest_rp.rp_id)
        .order_by(models.CandidateSet.created_at.desc())
    ).scalars().first()
    index_version = catalog_index_version(db)
    cache_valid = (cached_cs is not None
                   and (ctx.now - cached_cs.created_at).total_seconds() <= ttl
                   and cached_cs.params.get("index_version") == index_version)

    if cache_valid:
        state["cs"] = cached_cs
        ctx.nodes.append({"node": "retrieve", "class": "tier2",
                          "cache_hit": True, "candidates": len(cached_cs.candidates)})
        return True

    concept_names = sorted(_concept_name(c) for c in state["active"])
    recent_terms = list(dict.fromkeys(
        str((e.event_metadata or {}).get("query"))
        for e in state["journey_events"]
        if e.event_type == "SEARCH" and (e.event_metadata or {}).get("query")))
    query_document = compose_query_document(
        state["requirements"], concept_names, state["stage"], recent_terms, REQUIREMENTS)
    tier2_budget = ctx.policies.param("POL-TRIG-003", "tier2_calls_per_user_per_day")

    def _tier2_call():
        record_ai_call(db, ctx.user_id, "tier2", ctx.now)

    try:
        if ctx.backend is ctx.gateway:  # gateway embeddings spend Tier 2 budget
            _tier2_call()
        candidates, history, final_query = retrieve_with_refinement(
            db, ctx.chroma, ctx.backend, ctx.gateway, query_document, ctx.policies,
            tier2_llm_allowed=(
                ctx.tier2_allowed
                and _usage_calls(db, ctx.user_id, _today(ctx.now), "tier2") < tier2_budget),
            record_tier2_call=_tier2_call)
        cs = models.CandidateSet(
            cs_id=f"CS-{uuid.uuid4().hex[:10]}", journey_id=journey_id,
            rp_id=latest_rp.rp_id, query_document=final_query,
            params={"top_k": ctx.policies.param("POL-RETR-001", "top_k"),
                    "query_template": "qd-v1", "index_version": index_version},
            candidates=candidates, refinement_history=history, created_at=ctx.now)
        repos.insert_candidate_set(db, cs)
        db.flush()
        state["cs"] = cs
        ctx.nodes.append({"node": "retrieve", "class": "tier2", "cache_hit": False,
                          "candidates": len(candidates),
                          "refinements": len([h for h in history
                                              if h.get("action") == "refine"])})
    except GatewayUnavailable as exc:
        # Tier 2 failure ladder: best available cached set, else full-catalog
        # matching with a null Candidate Set ref (Core 21)
        state["cs"] = cached_cs
        ctx.nodes.append({"node": "retrieve", "class": "tier2",
                          "cache_hit": cached_cs is not None, "failure": str(exc)})
    return True


def stage_match(ctx: WorkflowContext, state: dict) -> bool:
    """Nodes 10-11: Recommendation Engine matching + readiness gate."""
    db = ctx.db
    journey_events = state["journey_events"]
    high_signal = sum(1 for e in journey_events if e.signal_class == "HIGH")
    readiness = evaluate_readiness(state["requirements"], high_signal, ctx.policies)
    constraints = {}
    if not any(e.event_type == "PRICING_VIEWED" for e in journey_events):
        constraints["budget"] = "Unknown"  # POL-REC-004

    published_entries: list[dict] = []
    if state["requirements"]:
        cs = state["cs"]
        if cs is not None:
            candidate_ids = [c["product_id"] for c in cs.candidates]
        else:
            candidate_ids = db.execute(
                select(models.Product.product_id).where(
                    models.Product.sync_status == "SYNCED",
                    models.Product.deleted_at.is_(None))
            ).scalars().all()
            ctx.nodes.append({"node": "match_fallback", "class": "deterministic",
                              "mode": "full-catalog"})
        product_caps: dict[str, set[str]] = {}
        for product_id in candidate_ids:
            caps = db.execute(
                select(models.ProductCapability.capability_id).where(
                    models.ProductCapability.product_id == product_id)
            ).scalars().all()
            product_caps[product_id] = set(caps)
        entries = rank_products(state["requirements"], list(candidate_ids),
                                product_caps, REQ_TO_CAP, ctx.policies)
        top = ctx.policies.param("POL-REC-003", "top_entries")
        alternatives = ctx.policies.param("POL-REC-003", "max_alternatives")
        published_entries = entries[: top + alternatives]

    latest_pkg = db.execute(
        select(models.RecommendationPackage)
        .where(models.RecommendationPackage.journey_id == state["journey_id"])
        .order_by(models.RecommendationPackage.created_at.desc())
    ).scalars().first()
    if (latest_pkg is None or latest_pkg.entries != published_entries
            or latest_pkg.readiness != readiness):
        rpkg = models.RecommendationPackage(
            rpkg_id=f"RPKG-{uuid.uuid4().hex[:10]}", journey_id=state["journey_id"],
            rp_id=state["latest_rp"].rp_id,
            cs_id=state["cs"].cs_id if state["cs"] is not None else None,
            entries=published_entries, readiness=readiness, constraints=constraints,
            policy_version=ctx.policies.version, created_at=ctx.now)
        repos.insert_recommendation_package(db, rpkg)
        db.flush()  # AAR row references the package; enforce insert order
    else:
        rpkg = latest_pkg
    state["rpkg"] = rpkg
    state["constraints"] = constraints
    ctx.nodes.append({"node": "match", "class": "deterministic", "readiness": readiness})
    return True


def stage_tier1(ctx: WorkflowContext, state: dict) -> bool:
    """Nodes 12a/12b: clarify (NOT_READY) / generate (READY) — Tier 1.
    Cache-first (POL-CACHE-001); budget gate serves the last stored AAR;
    malformed twice / gateway failure → package stands without a fresh AAR."""
    from smartreco.advisor import PROMPT_VERSION_CLARIFY, PROMPT_VERSION_GENERATE

    db, rpkg = ctx.db, state["rpkg"]
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
        ctx.nodes.append({"node": node_name, "class": "tier1", "cache_hit": True})
        return True
    if ctx.gateway is None:
        ctx.nodes.append({"node": node_name, "class": "tier1",
                          "skipped": "gateway unavailable"})
        return True
    if not ctx.tier1_allowed:
        ctx.nodes.append({"node": node_name, "class": "tier1",
                          "skipped": "budget-gated; serving last stored AAR"})
        return True

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
            for r in state["requirements"]],
        "stage": state["stage"],
        "behavior_summary": _behavior_summary(state["journey_events"]),
        "alternatives": [
            db.get(models.Product, e["product_id"]).name for e in rpkg.entries[3:]],
        "constraints": state["constraints"],
    }

    try:
        payload, version, calls = generate_sections(ctx.gateway, facts, readiness)
    except MalformedResponse as exc:
        for _ in range(2):  # both attempts spent budget
            record_ai_call(db, ctx.user_id, "tier1", ctx.now)
        ctx.nodes.append({"node": node_name, "class": "tier1",
                          "failure": f"malformed twice: {exc}"})
        return True
    except GatewayUnavailable as exc:
        record_ai_call(db, ctx.user_id, "tier1", ctx.now)
        ctx.nodes.append({"node": node_name, "class": "tier1", "failure": str(exc)})
        return True

    for _ in range(calls):
        record_ai_call(db, ctx.user_id, "tier1", ctx.now)
    repos.insert_advisory_response(db, models.AdvisoryResponse(
        aar_id=f"AAR-{uuid.uuid4().hex[:10]}", rpkg_id=rpkg.rpkg_id,
        surface=surface, prompt_version=version, model_id=ctx.gateway.model,
        sections=assemble_aar_sections(payload, facts, readiness),
        created_at=ctx.now))
    ctx.nodes.append({"node": node_name, "class": "tier1", "cache_hit": False,
                      "prompt_version": version, "model_id": ctx.gateway.model})
    return True


# The explicit framework-neutral graph: named stages in canonical order.
WORKFLOW_GRAPH = [
    ("resolve_journey", stage_resolve_journey),
    ("reason", stage_reason),
    ("score_confidence", stage_score_confidence),
    ("infer_requirements", stage_infer_requirements),
    ("resolve_stage", stage_resolve_stage),
    ("retrieval", stage_retrieval),
    ("match", stage_match),
    ("tier1", stage_tier1),
]


def _execute_plain(ctx: WorkflowContext, state: dict) -> None:
    for _name, stage_fn in WORKFLOW_GRAPH:
        if not stage_fn(ctx, state):
            break


def run_workflow(
    db: OrmSession,
    chroma_client,
    backend: EmbeddingBackend,
    policies: PolicyCatalog,
    user_id: int,
    trigger_type: str,
    now: datetime | None = None,
    gateway=None,
    executor=None,
) -> models.WorkflowRun:
    """One orchestration workflow execution. `executor` runs the stage graph
    (default: plain sequential executor; the ADK wrapper supplies its own —
    same stages, same state, different framework)."""
    now = _now(now)
    run_id = f"WR-{uuid.uuid4().hex[:12]}"

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

    trigger_ctx = TriggerContext(
        unprocessed_high_medium_events=len(unprocessed),
        newest_event_age_seconds=newest_age,
        seconds_since_last_run=(now - last_run_ts).total_seconds() if last_run_ts else None,
        run_in_flight=bool(in_flight),
        tier1_calls_today=_usage_calls(db, user_id, _today(now), "tier1"),
        tier2_calls_today=_usage_calls(db, user_id, _today(now), "tier2"),
    )
    decision = evaluate_trigger(trigger_type, trigger_ctx, policies)
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

    # Claim the slot before doing any work, and commit so a concurrent
    # evaluation on another connection can see it. POL-TRIG-005's gate reads
    # status RUNNING; until this existed nothing ever wrote that value, so the
    # gate was unreachable and two background evaluations would both proceed —
    # each resolving sessions, each creating a cold-start journey, and both
    # inserting journey stage v1 until the unique constraint raised.
    run = models.WorkflowRun(run_id=run_id, user_id=user_id, journey_id=None,
                             trigger_type=trigger_type, gates=gates, nodes=[],
                             policy_version=policies.version, status="RUNNING",
                             started_at=now, finished_at=now)
    repos.insert_workflow_run(db, run)
    try:
        db.commit()
    except IntegrityError:
        # Lost the race: another evaluation claimed the slot between our gate
        # check and this insert. That is precisely POL-TRIG-005's case — record
        # the SKIP and leave the events for the next evaluation. Caught
        # narrowly: only the one-running-run index can raise here.
        db.rollback()
        gates["decision"] = "SKIP (already-running) per POL-TRIG-005"
        skipped = models.WorkflowRun(
            run_id=run_id, user_id=user_id, journey_id=None,
            trigger_type=trigger_type, gates=gates, nodes=[],
            policy_version=policies.version, status="SKIPPED",
            started_at=now, finished_at=now)
        repos.insert_workflow_run(db, skipped)
        db.commit()
        return skipped

    ctx = WorkflowContext(db=db, chroma=chroma_client, backend=backend,
                          gateway=gateway, policies=policies, user_id=user_id,
                          now=now, tier1_allowed=decision.tier1_allowed,
                          tier2_allowed=decision.tier2_allowed)
    state: dict = {}
    try:
        (executor or _execute_plain)(ctx, state)
    except Exception:
        # Fail loud, but never fail *stuck*: a claim that outlives its run
        # would skip every later trigger for this user forever.
        db.rollback()
        run = db.get(models.WorkflowRun, run_id)
        run.status = "FAILED"
        run.finished_at = now
        db.commit()
        raise

    if "journey_id" not in state:
        run.status = "SKIPPED"
        run.finished_at = now
        db.commit()
        return run

    # --- Node 13: persist_deliver — closure, stamp processed, record run ---
    if any(e.event_type == "PURCHASE_COMPLETED" for e in unprocessed):
        journey = db.get(models.Journey, state["journey_id"])
        if journey is not None and journey.lifecycle != "CLOSED":
            close_journey(db, journey, "PURCHASED",
                          "PURCHASE_COMPLETED -> immediate closure (POL-JRES-003)",
                          policies, now)
    repos.stamp_processed(db, [e.event_id for e in unprocessed], now)
    run.journey_id = state["journey_id"]
    run.nodes = ctx.nodes
    run.status = "COMPLETED"
    run.finished_at = now
    db.commit()
    return run


def session_end_sweep(db: OrmSession, chroma_client, backend: EmbeddingBackend,
                      policies: PolicyCatalog, now: datetime | None = None,
                      gateway=None, executor=None) -> list[models.WorkflowRun]:
    """Raise SESSION_END for every shopper whose session closed with unprocessed
    activity (Core 23 Trigger Types).

    Event ingestion can only ever raise EVENT_ACCUMULATION, and that trigger
    needs POL-TRIG-001's five pending events. A shopper who stops below the
    threshold — the common case at the end of a visit, and the certain case
    after a purchase, which is the last thing anyone does — leaves work that
    nothing will ever pick up, because the only thing that wakes the evaluator
    is another event from the shopper who has left.

    The boundary is inactivity: POL-TRACK-003's window, already the session
    boundary for the tracking client and for journey resolution. Candidates are
    pre-filtered here rather than left to the evaluator so a sweep every few
    minutes does not write a SKIPPED row per idle user per tick; the evaluator
    still re-checks both halves of the condition and remains the authority.

    Self-limiting: a completed run stamps the events processed, so the next
    sweep finds nothing for that shopper.
    """
    now = _now(now)
    cutoff = now - timedelta(
        minutes=policies.param("POL-TRACK-003", "inactivity_minutes"))
    departed = db.execute(
        select(models.Event.user_id)
        .where(models.Event.processed_at.is_(None),
               models.Event.signal_class.in_(("HIGH", "MEDIUM")))
        .group_by(models.Event.user_id)
        .having(func.max(models.Event.received_at) < cutoff)
    ).scalars().all()
    return [
        run_workflow(db, chroma_client, backend, policies, user_id, "SESSION_END",
                     now=now, gateway=gateway, executor=executor)
        for user_id in departed
    ]
