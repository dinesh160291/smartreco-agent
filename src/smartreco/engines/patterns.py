"""Behavioral Reasoning Engine — pattern evaluation (docs/core/19; Domain 02).

Pure deterministic function over the journey's event history: identical events
always produce identical Evidence drafts. The caller persists drafts whose
dedup key (pattern_id, supporting event-id set) is new (core 19 dedup rule).

Phase 1 implements BP-001 and BP-002 (the plan's minimum for the vertical
slice); the registry structure extends to the remaining patterns in Phase 4.

Event metadata conventions (Core 13 leaves shapes to the implementation):
  SECURITY_VIEWED: {page, topic?} · DOCUMENTATION_VIEWED: {topic}
  PRICING_VIEWED: {product_id?, tier} · DWELL: {topic?, seconds}
  SEARCH: {query} · PRODUCT_VIEWED: {product_id, category?}
"""

from dataclasses import dataclass, field

from smartreco.policies import PolicyCatalog

BP001_DOC_TOPICS = {"security", "sso", "mfa"}
BP002_DOC_TOPICS = {"admin", "provisioning", "federation"}
BP002_SECURITY_TOPICS = {"compliance", "audit"}
BP002_ENTERPRISE_TIER = "enterprise"


@dataclass(frozen=True)
class EventView:
    event_id: str
    event_type: str
    session_id: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceDraft:
    pattern_id: str
    strength: str
    concept_ids: list[str]
    supporting_event_ids: list[str]
    explanation: str

    @property
    def dedup_key(self) -> tuple:
        return (self.pattern_id, tuple(sorted(self.supporting_event_ids)))


def evaluate_patterns(events: list[EventView], policies: PolicyCatalog) -> list[EvidenceDraft]:
    drafts: list[EvidenceDraft] = []
    sessions: dict[str, list[EventView]] = {}
    for event in events:
        sessions.setdefault(event.session_id, []).append(event)

    for session_events in sessions.values():
        draft = _evaluate_bp001(session_events)
        if draft:
            drafts.append(draft)
        draft = _evaluate_bp002(session_events, events)
        if draft:
            drafts.append(draft)
    return drafts


def _evaluate_bp001(session_events: list[EventView]) -> EvidenceDraft | None:
    """BP-001 Security Evaluation: ≥2 SECURITY_VIEWED on distinct pages, OR
    1 SECURITY_VIEWED + 1 DOCUMENTATION_VIEWED topic security/sso/mfa, within a
    session. Strong at ≥4 qualifying events or supporting dwell ≥60s."""
    security_views = [e for e in session_events if e.event_type == "SECURITY_VIEWED"]
    security_docs = [e for e in session_events
                     if e.event_type == "DOCUMENTATION_VIEWED"
                     and e.metadata.get("topic") in BP001_DOC_TOPICS]
    distinct_pages = {e.metadata.get("page") for e in security_views}

    activated = len(distinct_pages) >= 2 or (len(security_views) >= 1 and len(security_docs) >= 1)
    if not activated:
        return None

    qualifying = security_views + security_docs
    dwell_events = [e for e in session_events
                    if e.event_type == "DWELL" and e.metadata.get("topic") == "security"]
    dwell_seconds = sum(e.metadata.get("seconds", 0) for e in dwell_events)

    strength = "STRONG" if len(qualifying) >= 4 or dwell_seconds >= 60 else "MEDIUM"
    supporting = qualifying + (dwell_events if dwell_seconds >= 60 else [])
    return EvidenceDraft(
        pattern_id="BP-001",
        strength=strength,
        concept_ids=["BC-001"],
        supporting_event_ids=[e.event_id for e in supporting],
        explanation=(
            f"BP-001 activated: {len(security_views)} security view(s), "
            f"{len(security_docs)} security-topic doc view(s), dwell {dwell_seconds}s -> {strength}"
        ),
    )


def _bp002_qualifying(events: list[EventView]) -> list[EventView]:
    out = []
    for e in events:
        if e.event_type == "DOCUMENTATION_VIEWED" and e.metadata.get("topic") in BP002_DOC_TOPICS:
            out.append(e)
        elif e.event_type == "PRICING_VIEWED" and e.metadata.get("tier") == BP002_ENTERPRISE_TIER:
            out.append(e)
        elif e.event_type == "SECURITY_VIEWED" and e.metadata.get("topic") in BP002_SECURITY_TOPICS:
            out.append(e)
    return out


def _evaluate_bp002(session_events: list[EventView], journey_events: list[EventView]) -> EvidenceDraft | None:
    """BP-002 Enterprise Evaluation: ≥2 qualifying events within a session.
    Strong with ≥3 qualifying events across ≥2 sessions (journey lookback)."""
    session_qualifying = _bp002_qualifying(session_events)
    if len(session_qualifying) < 2:
        return None

    journey_qualifying = _bp002_qualifying(journey_events)
    journey_sessions = {e.session_id for e in journey_qualifying}
    strong = len(journey_qualifying) >= 3 and len(journey_sessions) >= 2

    supporting = journey_qualifying if strong else session_qualifying
    strength = "STRONG" if strong else "MEDIUM"
    return EvidenceDraft(
        pattern_id="BP-002",
        strength=strength,
        concept_ids=["BC-002"],
        supporting_event_ids=[e.event_id for e in supporting],
        explanation=(
            f"BP-002 activated: {len(session_qualifying)} enterprise signal(s) in session; "
            f"{len(journey_qualifying)} across {len(journey_sessions)} session(s) -> {strength}"
        ),
    )
