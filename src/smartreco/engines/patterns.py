"""Behavioral Reasoning Engine — pattern evaluation (docs/core/19; Domain 02).

Pure deterministic function over the journey's event history: identical events
always produce identical Evidence drafts. The caller persists drafts whose
dedup key (pattern_id, supporting event-id set) is new (core 19 dedup rule).

Implemented: BP-001/002 (Phase 1), BP-003/005/006/012 (Phase 2 — needed by
Stories 2 and 4); BP-004/007/008/009/010/011 land in Phase 4.

Event metadata conventions (Core 13 leaves shapes to the implementation):
  SECURITY_VIEWED: {page, topic?} · DOCUMENTATION_VIEWED: {topic}
  PRICING_VIEWED: {product_id?, tier} · DWELL: {topic?, seconds}
  SEARCH: {query} · PRODUCT_VIEWED: {product_id, category?}
  CATEGORY_VIEWED: {category}
"""

from dataclasses import dataclass, field

from smartreco.policies import PolicyCatalog

BP001_DOC_TOPICS = {"security", "sso", "mfa"}
BP002_DOC_TOPICS = {"admin", "provisioning", "federation"}
BP002_SECURITY_TOPICS = {"compliance", "audit"}
BP002_ENTERPRISE_TIER = "enterprise"
BP003_SEARCH_TERMS = {"ai", "copilot", "assistant"}
BP005_DOC_TOPICS = {"messaging", "meetings", "co-editing"}
BP006_DOC_TOPICS = {"productivity", "templates", "tasks"}
BP006_SEARCH_TERMS = {"productivity", "templates", "tasks"}


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
        for evaluator in (_evaluate_bp001,
                          lambda se: _evaluate_bp002(se, events),
                          _evaluate_bp003, _evaluate_bp005, _evaluate_bp006,
                          _evaluate_bp012):
            draft = evaluator(session_events)
            if draft:
                drafts.append(draft)
    return drafts


def _tokens(query: str) -> set[str]:
    return set(query.lower().split())


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


def _evaluate_bp003(session_events: list[EventView]) -> EvidenceDraft | None:
    """BP-003 AI Evaluation: ≥2 among DOCUMENTATION_VIEWED topic=ai,
    PRODUCT_VIEWED in an AI-focused category, SEARCH with AI terms.
    Strong at ≥4 qualifying (or supporting dwell ≥60s on AI pages)."""
    qualifying = []
    for e in session_events:
        if e.event_type == "DOCUMENTATION_VIEWED" and e.metadata.get("topic") == "ai":
            qualifying.append(e)
        elif e.event_type == "PRODUCT_VIEWED" and "ai" in str(e.metadata.get("category", "")).lower().split():
            qualifying.append(e)
        elif e.event_type == "SEARCH" and _tokens(e.metadata.get("query", "")) & BP003_SEARCH_TERMS:
            qualifying.append(e)
    if len(qualifying) < 2:
        return None
    dwell_seconds = sum(e.metadata.get("seconds", 0) for e in session_events
                        if e.event_type == "DWELL" and e.metadata.get("topic") == "ai")
    strength = "STRONG" if len(qualifying) >= 4 or dwell_seconds >= 60 else "MEDIUM"
    return EvidenceDraft(
        pattern_id="BP-003", strength=strength, concept_ids=["BC-003"],
        supporting_event_ids=[e.event_id for e in qualifying],
        explanation=f"BP-003 activated: {len(qualifying)} AI signal(s) -> {strength}")


def _evaluate_bp005(session_events: list[EventView]) -> EvidenceDraft | None:
    """BP-005 Collaboration Evaluation: ≥2 among PRODUCT_VIEWED in a
    collaboration category, DOCUMENTATION_VIEWED topic messaging/meetings/
    co-editing, CATEGORY_VIEWED collaboration. Strong at ≥4. Co-supports
    BC-006 when productivity topics co-occur in the session."""
    qualifying = []
    for e in session_events:
        if e.event_type == "PRODUCT_VIEWED" and "collaboration" in str(e.metadata.get("category", "")).lower():
            qualifying.append(e)
        elif e.event_type == "DOCUMENTATION_VIEWED" and e.metadata.get("topic") in BP005_DOC_TOPICS:
            qualifying.append(e)
        elif e.event_type == "CATEGORY_VIEWED" and "collaboration" in str(e.metadata.get("category", "")).lower():
            qualifying.append(e)
    if len(qualifying) < 2:
        return None
    productivity_co_occurs = any(
        (e.event_type == "DOCUMENTATION_VIEWED" and e.metadata.get("topic") in BP006_DOC_TOPICS)
        or (e.event_type == "SEARCH" and _tokens(e.metadata.get("query", "")) & BP006_SEARCH_TERMS)
        for e in session_events)
    concepts = ["BC-005", "BC-006"] if productivity_co_occurs else ["BC-005"]
    strength = "STRONG" if len(qualifying) >= 4 else "MEDIUM"
    return EvidenceDraft(
        pattern_id="BP-005", strength=strength, concept_ids=concepts,
        supporting_event_ids=[e.event_id for e in qualifying],
        explanation=f"BP-005 activated: {len(qualifying)} collaboration signal(s) -> {strength}")


def _evaluate_bp006(session_events: list[EventView]) -> EvidenceDraft | None:
    """BP-006 Productivity Evaluation: ≥2 among DOCUMENTATION_VIEWED topic
    productivity/templates/tasks, SEARCH with productivity terms,
    PRODUCT_VIEWED in productivity categories. Weak; Medium at ≥3.
    No Strong level defined (Domain 02)."""
    qualifying = []
    for e in session_events:
        if e.event_type == "DOCUMENTATION_VIEWED" and e.metadata.get("topic") in BP006_DOC_TOPICS:
            qualifying.append(e)
        elif e.event_type == "SEARCH" and _tokens(e.metadata.get("query", "")) & BP006_SEARCH_TERMS:
            qualifying.append(e)
        elif e.event_type == "PRODUCT_VIEWED" and "productivity" in str(e.metadata.get("category", "")).lower():
            qualifying.append(e)
    if len(qualifying) < 2:
        return None
    strength = "MEDIUM" if len(qualifying) >= 3 else "WEAK"
    return EvidenceDraft(
        pattern_id="BP-006", strength=strength, concept_ids=["BC-006"],
        supporting_event_ids=[e.event_id for e in qualifying],
        explanation=f"BP-006 activated: {len(qualifying)} productivity signal(s) -> {strength}")


def _evaluate_bp012(session_events: list[EventView]) -> EvidenceDraft | None:
    """BP-012 Product Discovery: ≥3 among CATEGORY_VIEWED/SEARCH/PRODUCT_VIEWED
    spanning ≥2 distinct products or categories, no single product > 2 views.
    Weak; Medium at ≥5. No Strong level defined (Domain 02)."""
    qualifying = [e for e in session_events
                  if e.event_type in ("CATEGORY_VIEWED", "SEARCH", "PRODUCT_VIEWED")]
    if len(qualifying) < 3:
        return None
    entities: set[str] = set()
    product_views: dict[str, int] = {}
    for e in qualifying:
        if e.event_type == "PRODUCT_VIEWED" and e.metadata.get("product_id"):
            pid = str(e.metadata["product_id"])
            entities.add(pid)
            product_views[pid] = product_views.get(pid, 0) + 1
        elif e.event_type == "CATEGORY_VIEWED" and e.metadata.get("category"):
            entities.add(str(e.metadata["category"]))
    if len(entities) < 2:
        return None
    if any(count > 2 for count in product_views.values()):
        return None  # concentration on one product — BP-010 territory
    strength = "MEDIUM" if len(qualifying) >= 5 else "WEAK"
    return EvidenceDraft(
        pattern_id="BP-012", strength=strength, concept_ids=["BC-011"],
        supporting_event_ids=[e.event_id for e in qualifying],
        explanation=f"BP-012 activated: {len(qualifying)} discovery event(s) across "
                    f"{len(entities)} entities -> {strength}")


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
