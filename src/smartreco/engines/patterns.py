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
    contradicts: tuple[str, ...] = ()  # BC-xxx contradicted (patterns' Contradicting rules)

    @property
    def dedup_key(self) -> tuple:
        return (self.pattern_id, tuple(sorted(self.supporting_event_ids)), self.contradicts)


def evaluate_patterns(events: list[EventView], policies: PolicyCatalog) -> list[EvidenceDraft]:
    drafts: list[EvidenceDraft] = []
    sessions: dict[str, list[EventView]] = {}
    for event in events:
        sessions.setdefault(event.session_id, []).append(event)

    for session_events in sessions.values():
        for evaluator in (_evaluate_bp001,
                          lambda se: _evaluate_bp002(se, events),
                          lambda se: _evaluate_bp002_contradiction(se),
                          _evaluate_bp003,
                          lambda se: _evaluate_bp004(se, events),
                          _evaluate_bp005, _evaluate_bp006,
                          lambda se: _evaluate_bp007(se, events),
                          _evaluate_bp008,
                          lambda se: _evaluate_bp009(se, events),
                          _evaluate_bp011, _evaluate_bp012):
            result = evaluator(session_events)
            if isinstance(result, EvidenceDraft):
                drafts.append(result)
            elif result:
                drafts.extend(result)
    drafts.extend(_evaluate_bp010(events))  # journey-scoped, product-scoped
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


BP004_DOC_TOPICS = {"compliance", "audit", "retention", "ediscovery"}
BP007_DOC_TOPICS = {"workflows", "automation", "triggers"}
BP007_SEARCH_TERMS = {"automate", "automation", "workflow", "workflows"}
BP008_DOC_TOPICS = {"integrations", "api", "connectors"}
BP011_TRIGGERS = {"TRIAL_STARTED", "DEMO_REQUESTED", "ADD_TO_CART",
                  "CHECKOUT_STARTED", "PURCHASE_COMPLETED"}
BP011_VERY_STRONG = {"CHECKOUT_STARTED", "PURCHASE_COMPLETED"}


def _evaluate_bp002_contradiction(session_events: list[EventView]) -> EvidenceDraft | None:
    """BP-002 Contradicting: repeated PRICING_VIEWED on individual/free tiers
    (Domain 02) — contradicts BC-002 Enterprise Evaluation."""
    low_tier = [e for e in session_events
                if e.event_type == "PRICING_VIEWED"
                and e.metadata.get("tier") in ("individual", "free", "personal")]
    if len(low_tier) < 2:
        return None
    return EvidenceDraft(
        pattern_id="BP-002", strength="MEDIUM", concept_ids=[],
        supporting_event_ids=[e.event_id for e in low_tier],
        contradicts=("BC-002",),
        explanation=f"BP-002 contradicting: {len(low_tier)} individual/free-tier pricing view(s)")


def _evaluate_bp004(session_events: list[EventView], journey_events: list[EventView]) -> EvidenceDraft | None:
    """BP-004 Compliance Evaluation: ≥2 among DOC topic compliance/audit/
    retention/ediscovery, SECURITY_VIEWED topic certifications. Strong with
    qualifying events across ≥2 sessions."""
    def quals(events):
        return [e for e in events
                if (e.event_type == "DOCUMENTATION_VIEWED"
                    and e.metadata.get("topic") in BP004_DOC_TOPICS)
                or (e.event_type == "SECURITY_VIEWED"
                    and e.metadata.get("topic") == "certifications")]

    session_qualifying = quals(session_events)
    if len(session_qualifying) < 2:
        return None
    journey_qualifying = quals(journey_events)
    multi_session = len({e.session_id for e in journey_qualifying}) >= 2
    supporting = journey_qualifying if multi_session else session_qualifying
    strength = "STRONG" if multi_session else "MEDIUM"
    return EvidenceDraft(
        pattern_id="BP-004", strength=strength, concept_ids=["BC-004"],
        supporting_event_ids=[e.event_id for e in supporting],
        explanation=f"BP-004 activated: {len(session_qualifying)} compliance signal(s) -> {strength}")


def _evaluate_bp007(session_events: list[EventView], journey_events: list[EventView]) -> EvidenceDraft | None:
    """BP-007 Automation Evaluation: ≥2 among DOC workflows/automation/triggers,
    PV in an automation category, SEARCH with automation terms. Strong at ≥4
    qualifying or multi-session recurrence."""
    def quals(events):
        out = []
        for e in events:
            if e.event_type == "DOCUMENTATION_VIEWED" and e.metadata.get("topic") in BP007_DOC_TOPICS:
                out.append(e)
            elif e.event_type == "PRODUCT_VIEWED" and "automation" in str(e.metadata.get("category", "")).lower():
                out.append(e)
            elif e.event_type == "SEARCH" and _tokens(e.metadata.get("query", "")) & BP007_SEARCH_TERMS:
                out.append(e)
        return out

    session_qualifying = quals(session_events)
    if len(session_qualifying) < 2:
        return None
    journey_qualifying = quals(journey_events)
    multi_session = len({e.session_id for e in journey_qualifying}) >= 2
    strong = len(session_qualifying) >= 4 or multi_session
    supporting = journey_qualifying if multi_session else session_qualifying
    strength = "STRONG" if strong else "MEDIUM"
    return EvidenceDraft(
        pattern_id="BP-007", strength=strength, concept_ids=["BC-007"],
        supporting_event_ids=[e.event_id for e in supporting],
        explanation=f"BP-007 activated: {len(session_qualifying)} automation signal(s) -> {strength}")


def _evaluate_bp008(session_events: list[EventView]) -> EvidenceDraft | None:
    """BP-008 Integration Evaluation: ≥2 DOC topic integrations/api/connectors.
    Strong when API reference and connector pages both appear. Co-supports
    BC-009 Technical Evaluation."""
    qualifying = [e for e in session_events
                  if e.event_type == "DOCUMENTATION_VIEWED"
                  and e.metadata.get("topic") in BP008_DOC_TOPICS]
    if len(qualifying) < 2:
        return None
    topics = {e.metadata.get("topic") for e in qualifying}
    strength = "STRONG" if {"api", "connectors"} <= topics else "MEDIUM"
    return EvidenceDraft(
        pattern_id="BP-008", strength=strength, concept_ids=["BC-008", "BC-009"],
        supporting_event_ids=[e.event_id for e in qualifying],
        explanation=f"BP-008 activated: topics {sorted(t for t in topics if t)} -> {strength}")


def _evaluate_bp009(session_events: list[EventView], journey_events: list[EventView]) -> EvidenceDraft | None:
    """BP-009 Commercial Evaluation: ≥2 PRICING_VIEWED, or 1 PRICING + 1
    COMPARISON_STARTED, within a session. Strong with pricing views across
    ≥2 sessions. Repeated same-tier focus co-supports BC-014."""
    pricing = [e for e in session_events if e.event_type == "PRICING_VIEWED"]
    comparisons = [e for e in session_events if e.event_type == "COMPARISON_STARTED"]
    if not (len(pricing) >= 2 or (len(pricing) >= 1 and len(comparisons) >= 1)):
        return None
    journey_pricing = [e for e in journey_events if e.event_type == "PRICING_VIEWED"]
    multi_session = len({e.session_id for e in journey_pricing}) >= 2
    strength = "STRONG" if multi_session else "MEDIUM"
    supporting = (journey_pricing if multi_session else pricing) + comparisons[:1]
    tiers = [e.metadata.get("tier") for e in journey_pricing if e.metadata.get("tier")]
    same_tier_repeat = len(tiers) >= 2 and len(set(tiers)) == 1
    concepts = ["BC-010", "BC-014"] if same_tier_repeat else ["BC-010"]
    return EvidenceDraft(
        pattern_id="BP-009", strength=strength, concept_ids=concepts,
        supporting_event_ids=[e.event_id for e in supporting],
        explanation=f"BP-009 activated: {len(pricing)} pricing view(s) -> {strength}")


def _evaluate_bp010(journey_events: list[EventView]) -> list[EvidenceDraft]:
    """BP-010 Product Affinity (journey-scoped, product-scoped): ≥3 same-product
    views across ≥2 sessions, or ≥2 views + 1 same-product pricing. Strong at
    ≥5 qualifying. Contradicting: COMPARISON_STARTED introducing new
    alternatives after affinity formed."""
    drafts: list[EvidenceDraft] = []
    by_product: dict[str, list[tuple[int, EventView]]] = {}
    for index, e in enumerate(journey_events):
        pid = e.metadata.get("product_id")
        if not pid:
            continue
        if e.event_type in ("PRODUCT_VIEWED", "PRICING_VIEWED"):
            by_product.setdefault(str(pid), []).append((index, e))

    for product_id, indexed in by_product.items():
        views = [(i, e) for i, e in indexed if e.event_type == "PRODUCT_VIEWED"]
        pricing = [(i, e) for i, e in indexed if e.event_type == "PRICING_VIEWED"]
        view_sessions = {e.session_id for _, e in views}
        multi_session_views = len(views) >= 3 and len(view_sessions) >= 2
        views_plus_pricing = len(views) >= 2 and len(pricing) >= 1
        if not (multi_session_views or views_plus_pricing):
            continue
        qualifying = views + pricing
        strength = "STRONG" if len(qualifying) >= 5 else "MEDIUM"
        drafts.append(EvidenceDraft(
            pattern_id="BP-010", strength=strength, concept_ids=["BC-012"],
            supporting_event_ids=[e.event_id for _, e in qualifying],
            explanation=f"BP-010 activated for a product: {len(qualifying)} signal(s) -> {strength}"))

        # Contradicting: comparison introducing a new alternative after affinity
        affinity_index = sorted(i for i, _ in qualifying)[
            min(2, len(qualifying) - 1)]
        contradicting = [
            e for i, e in enumerate(journey_events)
            if i > affinity_index and e.event_type == "COMPARISON_STARTED"
            and any(str(e.metadata.get(k)) not in (product_id, "None")
                    for k in ("product_a", "product_b"))]
        if contradicting:
            drafts.append(EvidenceDraft(
                pattern_id="BP-010", strength="MEDIUM", concept_ids=[],
                supporting_event_ids=[e.event_id for e in contradicting],
                contradicts=("BC-012",),
                explanation="BP-010 contradicting: comparison introduced new alternatives after affinity formed"))
    return drafts


def _evaluate_bp011(session_events: list[EventView]) -> list[EvidenceDraft]:
    """BP-011 Adoption Readiness (product-scoped): any single trigger event.
    Strong for trial/demo/cart; Very Strong for checkout/purchase. Co-supports
    BC-016 Decision Confidence."""
    triggers = [e for e in session_events if e.event_type in BP011_TRIGGERS]
    if not triggers:
        return []
    onboarding = [e for e in session_events
                  if e.event_type == "DOCUMENTATION_VIEWED"
                  and e.metadata.get("topic") in ("onboarding", "migration")]
    by_product: dict[str, list[EventView]] = {}
    for e in triggers:
        by_product.setdefault(str(e.metadata.get("product_id") or "journey"), []).append(e)
    # A product-less trigger (e.g. CHECKOUT_STARTED) belongs to the same adoption
    # act as the session's sole product-scoped trigger group — never its own draft.
    if "journey" in by_product and len(by_product) == 2:
        orphan = by_product.pop("journey")
        next(iter(by_product.values())).extend(orphan)
    drafts = []
    for _product_id, events in by_product.items():
        very_strong = any(e.event_type in BP011_VERY_STRONG for e in events)
        drafts.append(EvidenceDraft(
            pattern_id="BP-011",
            strength="VERY_STRONG" if very_strong else "STRONG",
            concept_ids=["BC-015", "BC-016"],
            supporting_event_ids=[e.event_id for e in events + onboarding],
            explanation=f"BP-011 activated: {[e.event_type for e in events]}"))
    return drafts


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
