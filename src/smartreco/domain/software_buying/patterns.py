"""Behavioral pattern evaluators — Software Buying (Domain Pack doc 02).

The activation rules for BP-001…BP-012, moved out of `engines/patterns.py`.
They are statements about *this domain*: which document topics count as
security research, which pricing tier signals an enterprise evaluation. A
travel pack would supply entirely different predicates against the same
engine.

The engine keeps the mechanism — session windowing, dedup, ordering — and
calls `PATTERN_EVALUATORS` below. Bodies are unchanged from the engine
version; this was a move, not a rewrite.

Event metadata conventions (Core 13 leaves the shapes to the domain):
  SECURITY_VIEWED: {page, topic?} · DOCUMENTATION_VIEWED: {product_id, topic?}
  PRICING_VIEWED: {product_id?, tier} · DWELL: {topic?, seconds}
  SEARCH: {query} · PRODUCT_VIEWED: {product_id, category?}
  CATEGORY_VIEWED: {category}
"""

from smartreco.engines.evidence import EventView, EvidenceDraft

BP001_DOC_TOPICS = {"security", "sso", "mfa"}
BP002_DOC_TOPICS = {"admin", "provisioning", "federation"}
BP002_SECURITY_TOPICS = {"compliance", "audit"}
BP002_ENTERPRISE_TIER = "enterprise"

# The documentation a shopper reads *after* choosing a product. Named here
# because both BP-011 and the Adoption stage milestone key on it, and because
# the surface that emits it has to ask the pack which word to use.
#
# Both words were unemitted until Decision #052, which is worse here than dead
# vocabulary elsewhere: the Adoption stage milestone requires one of them, so
# Adoption was unreachable from a browser entirely. An owned product's Docs tab
# now reports onboarding and its Integrations tab migration — reading either
# after you have bought the thing is exactly what those words mean.
ADOPTION_ONBOARDING_TOPIC = "onboarding"
ADOPTION_MIGRATION_TOPIC = "migration"
ADOPTION_DOC_TOPICS = frozenset({ADOPTION_ONBOARDING_TOPIC, ADOPTION_MIGRATION_TOPIC})
BP003_SEARCH_TERMS = {"ai", "copilot", "assistant"}

# Topics whose *reading time* can stand in for volume of activity.
#
# Security Evaluation is the only pattern with that clause, and doc 02 is
# deliberate about it: security interest can only be shown on a product's
# security page, and each product has exactly one, so reaching the four
# qualifying events that mean "Strong" requires visiting four separate
# products. Sixty seconds of reading is the fair alternative for someone who
# instead studies one product closely.
#
# No other pattern needs that escape hatch. AI Evaluation, for instance,
# qualifies on docs *and* product views *and* searches, so four events
# accumulate inside a single product without any special allowance — which is
# why doc 02 gives it no dwell path, and why the code must not invent one.
#
# Named here rather than left as a literal so a surface can ask which topics
# are worth running a heartbeat for instead of hardcoding the answer.
SECURITY_DWELL_TOPIC = "security"
DWELL_TOPICS = frozenset({SECURITY_DWELL_TOPIC})
BP005_DOC_TOPICS = {"messaging", "meetings", "co-editing"}
BP006_DOC_TOPICS = {"productivity", "templates", "tasks"}
BP006_SEARCH_TERMS = {"productivity", "templates", "tasks"}


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
                    if e.event_type == "DWELL"
                    and e.metadata.get("topic") == SECURITY_DWELL_TOPIC]
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
    Strong at ≥4 qualifying — no dwell path, per doc 02.

    The code carried one until Decision #045. It was never specified: unlike
    Security Evaluation, this pattern qualifies on three different event kinds,
    so four of them accumulate inside a single product without needing reading
    time to stand in. Promoting on dwell here made Strong cheaper for AI
    research than for anything else, for no stated reason.
    """
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
    strength = "STRONG" if len(qualifying) >= 4 else "MEDIUM"
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
# "automation" removed in Decision #052: a synonym no surface emitted, while
# "workflows" and "triggers" both do. Nothing observable changed.
BP007_DOC_TOPICS = {"workflows", "triggers"}
BP007_SEARCH_TERMS = {"automate", "automation", "workflow", "workflows"}
# "integrations" removed in Decision #055: it was the generic fallback the
# Integrations tab emitted for every product with no connective capability, so
# the pattern's cheapest activation path carried no integration meaning at all.
# What remains are the two words the pattern's own Strong clause is written
# around — an API reference and a connector page.
BP008_DOC_TOPICS = {"api", "connectors"}
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
        # "Sustained affinity co-supports BC-016 Decision Confidence" (doc 02).
        # Sustained is this pattern's own Strong bar: below it the shopper is
        # still looking, at it they have converged.
        concepts = ["BC-012", "BC-016"] if strength == "STRONG" else ["BC-012"]
        drafts.append(EvidenceDraft(
            pattern_id="BP-010", strength=strength, concept_ids=concepts,
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
                  and e.metadata.get("topic") in ADOPTION_DOC_TOPICS]
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


def _bp002_administration_signals(events: list[EventView]) -> list[EventView]:
    """The qualifying events that actually carry the identity meaning.

    Doc 06 maps this concept Primary to Identity Management because
    "organizational adoption hinges first on centralized identity". Only the
    administration half of the evidence supports that: admin, provisioning and
    federation pages are about running identities at organizational scale.
    Enterprise pricing tiers and compliance posture pages are read by shoppers
    in every domain, so on their own they state company size, not need.
    """
    return [e for e in events
            if e.event_type == "DOCUMENTATION_VIEWED"
            and e.metadata.get("topic") in BP002_DOC_TOPICS]


def _evaluate_bp002(session_events: list[EventView], journey_events: list[EventView]) -> EvidenceDraft | None:
    """BP-002 Enterprise Evaluation: ≥2 qualifying events within a session, at
    least one of them an administration page (Decision #049). Strong with ≥3
    qualifying events across ≥2 sessions (journey lookback)."""
    session_qualifying = _bp002_qualifying(session_events)
    if len(session_qualifying) < 2:
        return None
    if not _bp002_administration_signals(session_events):
        # Commercial and compliance signals alone. Pricing behaviour is already
        # BP-009's; counting it here too let four enterprise-tier clicks on four
        # CRM products publish an Identity Management need (Decision #049).
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

# ---- v1.2 domain research patterns (doc 14 Table 2) ----
#
# Seven patterns with one shape: ≥2 qualifying signals activate, ≥4 make it
# Strong — the same ladder as BP-003 and BP-007, deliberately, so shopping for
# a CRM is no harder to recognise than shopping for AI.
#
# A table rather than seven near-identical functions: there are seven concrete
# uses, and what is worth reading here is the *vocabulary* — which words and
# categories mean "this person is shopping for payroll" — not the control flow
# repeated seven times. Each row is a claim about this domain, which is exactly
# what a Domain Pack is for.
#
# Every topic below must appear in the UI vocabulary (UI_DOC_TOPICS) or the
# pattern cannot fire from a browser; test_ui_tracking_contract pins that both
# ways.

DOMAIN_RESEARCH_PATTERNS = (
    # (pattern_id, concept_id, doc topics, product categories, search terms)
    ("BP-013", "BC-019",
     {"pipeline", "crm", "tickets"},
     {"crm", "customer support"},
     {"crm", "pipeline", "leads", "lead", "ticketing", "helpdesk"}),
    ("BP-014", "BC-020",
     {"payroll", "hiring", "performance"},
     {"hr"},
     {"hr", "payroll", "ats", "onboarding", "recruiting", "hiring"}),
    ("BP-015", "BC-021",
     {"accounting", "billing", "expenses", "forecasting"},
     {"finance"},
     {"accounting", "invoicing", "invoice", "expenses", "ledger", "budgeting"}),
    ("BP-016", "BC-022",
     {"campaigns", "seo", "experiments"},
     {"marketing"},
     {"marketing", "campaign", "campaigns", "seo", "newsletter"}),
    ("BP-017", "BC-023",
     {"cicd", "monitoring", "incidents", "containers"},
     {"devops"},
     {"devops", "cicd", "kubernetes", "observability", "monitoring", "deployment"}),
    ("BP-018", "BC-024",
     {"warehouse", "pipelines-data", "dashboards"},
     {"data & analytics"},
     {"warehouse", "etl", "bi", "analytics", "dashboard", "dashboards"}),
    # No certifications clause, though doc 14 Table 2 sketched one: that topic
    # already qualifies BP-004 Compliance Evaluation, and handing the same page
    # to two patterns is how one journey's evidence publishes another journey's
    # need (Decisions #049, #050).
    ("BP-019", "BC-025",
     {"threat", "dlp"},
     {"security"},
     {"edr", "xdr", "siem", "dlp", "threat", "endpoint", "antivirus", "vulnerability"}),
)


# ---- UI vocabulary (Domain Pack artifact 11; doc 14 Table 4) ----
#
# Which topic each tracked tab reports, per product. Ordered — first capability
# the product holds wins — and it lives here rather than in the web layer
# because it is domain knowledge: the contract lists "per-tab tracked topics"
# as a pack artifact, and a pattern keyed on a topic no surface emits cannot
# fire from a browser at all (Decision #044).
#
# Ordering is by *specificity*, not by version, and it is load-bearing in both
# directions. Identity comes first so a suite holding single sign-on still
# describes its docs as identity docs. The v1.2 product-type topics come next,
# so a CRM stops describing its docs as workflow automation — which is exactly
# how a CRM journey was read as automation research. Threat and data-loss
# topics come last, after governance, so a content-governance product still
# reports compliance.

UI_DOC_TOPICS = (
    # Endpoint detection is the least ambiguous entry in this table and so leads
    # it: nothing acquires it by being large, and a product holding it is a
    # security-operations product whatever else it also does (Decision #074).
    ("CAP-059", "threat"),                                     # BP-019 Security Ops
    ("CAP-001", "sso"), ("CAP-002", "mfa"),                    # BP-001 Security
    ("CAP-004", "admin"),                                      # BP-002 Enterprise
    # v1.2 product-type topics. Support before sales: a helpdesk product must
    # not describe itself as a sales pipeline.
    ("CAP-056", "tasks"), ("CAP-057", "templates"),
    ("CAP-058", "productivity"),                               # BP-006 Productivity
    ("CAP-031", "tickets"), ("CAP-032", "tickets"),
    ("CAP-029", "pipeline"), ("CAP-028", "crm"), ("CAP-030", "crm"),
    ("CAP-035", "payroll"), ("CAP-036", "payroll"),
    ("CAP-033", "hiring"), ("CAP-034", "hiring"), ("CAP-037", "performance"),
    ("CAP-040", "accounting"), ("CAP-038", "billing"), ("CAP-042", "billing"),
    ("CAP-039", "expenses"), ("CAP-041", "forecasting"),
    ("CAP-044", "campaigns"), ("CAP-043", "campaigns"), ("CAP-045", "campaigns"),
    ("CAP-046", "seo"), ("CAP-047", "experiments"),
    ("CAP-048", "cicd"), ("CAP-049", "monitoring"), ("CAP-050", "monitoring"),
    ("CAP-051", "incidents"), ("CAP-052", "containers"),
    ("CAP-054", "pipelines-data"), ("CAP-055", "warehouse"), ("CAP-053", "dashboards"),
    # v1 generic platform topics
    ("CAP-020", "ai"), ("CAP-021", "ai"), ("CAP-022", "ai"),
    ("CAP-023", "ai"), ("CAP-024", "ai"),                      # BP-003 AI
    ("CAP-005", "messaging"), ("CAP-006", "meetings"),
    ("CAP-007", "co-editing"),                                 # BP-005 Collaboration
    ("CAP-015", "workflows"), ("CAP-017", "triggers"),          # BP-007 Automation
    ("CAP-012", "compliance"), ("CAP-013", "retention"),
    ("CAP-014", "ediscovery"), ("CAP-027", "compliance"),
    ("CAP-010", "audit"),                                      # BP-004 Compliance
    ("CAP-025", "threat"), ("CAP-026", "dlp"),                 # BP-019 Security Ops
    ("CAP-060", "threat"), ("CAP-061", "threat"), ("CAP-062", "threat"),
)
UI_DOC_TOPIC_DEFAULT = "api"

# The Security & Compliance pane is a threat surface on a product that detects and
# responds to attacks, a certifications surface when the product carries governance
# capabilities, an audit surface when it only logs, and a general posture page
# otherwise (BP-019 keys on "threat"; BP-004 on "certifications"; BP-002 on
# "compliance"/"audit").
#
# The threat rows lead, and their absence was a bug in its own right: with no
# threat entry at all, the security pane of every endpoint-security product fell
# to the "compliance" default and voted for Enterprise Evaluation. A shopper
# reading CrowdStrike's security page was emitting evidence that they were vetting
# a vendor's paperwork (Decision #074).
#
# Threat Protection is deliberately *not* one of the threat rows here. Twenty-one
# products hold it, including content-management and analytics suites, so on this
# pane it discriminates nothing; endpoint detection and security monitoring are
# held only by products whose job this is. Ordering CAP-025 first made Microsoft
# 365 report its security pane as a threat surface and put Compliance Evaluation
# out of reach of the browser entirely.
UI_SECURITY_TOPICS = (
    ("CAP-059", "threat"),                                     # EDR: unambiguous
    ("CAP-012", "certifications"), ("CAP-013", "certifications"),
    ("CAP-014", "certifications"), ("CAP-027", "certifications"),
    ("CAP-010", "audit"),
    ("CAP-061", "threat"),        # monitoring, on a product with no governance duties
)
UI_SECURITY_TOPIC_DEFAULT = "compliance"

UI_INTEGRATION_TOPICS = (
    ("CAP-003", "provisioning"), ("CAP-008", "federation"),    # BP-002 Enterprise
    ("CAP-016", "connectors"), ("CAP-019", "api"),             # BP-008 Integration
)
# No fallback (Decision #055). A product holding none of the four capabilities
# above has no integration story to research, and its pane says exactly that:
# "none of which are specifically connective — integration here will mean a
# generic API or an intermediary rather than a purpose-built connector."
# Emitting `integrations` there made 153 of 250 products claim research they
# cannot support, and two such clicks were enough to activate BP-008.
#
# A pane with nothing to declare declares nothing. The visit is still tracked —
# a DOCUMENTATION_VIEWED carrying the product but no `topic` — so the read is
# recorded and counts toward accumulation while no topic-keyed clause can act
# on it. SECURITY_VIEWED has always worked this way.
UI_INTEGRATION_TOPIC_DEFAULT = None


def _evaluate_domain_research(session_events: list[EventView],
                              journey_events: list[EventView], pattern_id: str,
                              concept_id: str, doc_topics: set[str],
                              categories: set[str],
                              search_terms: set[str]) -> EvidenceDraft | None:
    """Strong at ≥4 qualifying signals in a session, **or** on recurrence across
    ≥2 sessions (Decision #056).

    The multi-session clause is not new to the domain — BP-004, BP-007 and
    BP-009 have carried it since v1, on the reasoning that coming back to a
    subject after leaving it is itself evidence of intent, and stronger than
    the same volume of clicking in one sitting. The v1.2 patterns were built
    from a flat count ladder and were the only ones without it, so returning to
    a subject the next day counted for nothing beyond the clicks themselves.
    """
    def quals(events):
        out = []
        for e in events:
            if e.event_type == "DOCUMENTATION_VIEWED" and e.metadata.get("topic") in doc_topics:
                out.append(e)
            elif e.event_type in ("PRODUCT_VIEWED", "CATEGORY_VIEWED"):
                category = str(e.metadata.get("category", "")).lower()
                if category and any(name in category for name in categories):
                    out.append(e)
            elif e.event_type == "SEARCH" and _tokens(e.metadata.get("query", "")) & search_terms:
                out.append(e)
        return out

    qualifying = quals(session_events)
    if len(qualifying) < 2:
        return None
    journey_qualifying = quals(journey_events)
    multi_session = len({e.session_id for e in journey_qualifying}) >= 2
    strong = len(qualifying) >= 4 or multi_session
    supporting = journey_qualifying if multi_session else qualifying
    strength = "STRONG" if strong else "MEDIUM"
    return EvidenceDraft(
        pattern_id=pattern_id, strength=strength, concept_ids=[concept_id],
        supporting_event_ids=[e.event_id for e in supporting],
        explanation=(f"{pattern_id} activated: {len(qualifying)} signal(s) in session; "
                     f"{len(journey_qualifying)} across "
                     f"{len({e.session_id for e in journey_qualifying})} session(s) -> {strength}"))


# The concepts that say *what the shopper is shopping for*, as opposed to how far
# along they are or how they behave. Assembled from the same table the
# evaluators are generated from, so a new domain pattern joins this set for
# free (Decision #056).
#
# Journey resolution reads this to decide when a shopper has changed subject
# mid-session: Data & Insight giving way to Engineering Delivery is a different
# buying effort, whereas Commercial Evaluation appearing beside either is the
# same effort maturing. Only these concepts carry that meaning, which is why
# the platform is handed a set rather than left to guess from entity overlap.
INTENT_CONCEPTS = frozenset(concept_id for _p, concept_id, *_rest in DOMAIN_RESEARCH_PATTERNS)


def _domain_research_evaluator(row):
    pattern_id, concept_id, doc_topics, categories, search_terms = row
    return lambda se, all_events: _evaluate_domain_research(
        se, all_events, pattern_id, concept_id, doc_topics, categories, search_terms)


# Evaluation order is part of the contract: session-scoped evaluators run per
# session, then journey-scoped ones over the whole history. `journey_events`
# is passed to evaluators whose rules look beyond the current session.
SESSION_EVALUATORS = (
    lambda se, all_events: _evaluate_bp001(se),
    lambda se, all_events: _evaluate_bp002(se, all_events),
    lambda se, all_events: _evaluate_bp002_contradiction(se),
    lambda se, all_events: _evaluate_bp003(se),
    lambda se, all_events: _evaluate_bp004(se, all_events),
    lambda se, all_events: _evaluate_bp005(se),
    lambda se, all_events: _evaluate_bp006(se),
    lambda se, all_events: _evaluate_bp007(se, all_events),
    lambda se, all_events: _evaluate_bp008(se),
    lambda se, all_events: _evaluate_bp009(se, all_events),
    lambda se, all_events: _evaluate_bp011(se),
    lambda se, all_events: _evaluate_bp012(se),
) + tuple(_domain_research_evaluator(row) for row in DOMAIN_RESEARCH_PATTERNS)

JOURNEY_EVALUATORS = (_evaluate_bp010,)   # product-scoped, spans the journey


# Every topic any evaluator reads. Assembled from the same constants the
# evaluators use, so it cannot drift from them — and exported so the UI
# reachability ratchet checks against the pack rather than restating the list in
# a test, which is how a topic went unread for three patterns (Decision #044).
PATTERN_TOPICS = frozenset(
    BP001_DOC_TOPICS | BP002_DOC_TOPICS | BP002_SECURITY_TOPICS
    | BP004_DOC_TOPICS | BP005_DOC_TOPICS | BP006_DOC_TOPICS
    | BP007_DOC_TOPICS | BP008_DOC_TOPICS
    # Read as literals inside an evaluator rather than via a constant:
    # BP-003's "ai", BP-004's "certifications", BP-011's onboarding/migration.
    | {SECURITY_DWELL_TOPIC, "ai", "certifications"} | ADOPTION_DOC_TOPICS
    | {topic for _p, _c, topics, _cat, _s in DOMAIN_RESEARCH_PATTERNS for topic in topics}
)
