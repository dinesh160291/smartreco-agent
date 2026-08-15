"""Signature tests: the v1.2 domain research patterns (Domain Pack doc 14).

The catalog carries 55 capabilities; the five original requirements reach 21 of
them, so 82 of the 250 catalog products could be searched, viewed and added to
a cart but never recommended — coverage scoring had nothing to score them on.
Observed live: a shopper searching "crm" and "sales pipeline" across four CRM
products was told to buy Microsoft 365 and ServiceNow, with Salesforce fifth.

These pin the chain that was missing. A requirement alone is inert — no concept
feeds it. A concept alone never forms — no pattern produces it. So each test
follows one journey the whole way: clicks the browser can actually emit →
pattern → concept → published requirement → coverage that ranks the right
product first.
"""

import json
from itertools import zip_longest
from pathlib import Path

import pytest

from smartreco.domain.software_buying import (
    BC_TO_REQ,
    DOMAIN_RESEARCH_PATTERNS,
    REQ_TO_CAP,
    REQUIREMENTS,
)
from smartreco.engines.matching import rank_products
from smartreco.engines.patterns import EventView, evaluate_patterns
from smartreco.engines.requirements import derive_requirements
from smartreco.policies import load_policies

SEED = Path(__file__).resolve().parents[1] / "seed" / "products.json"


@pytest.fixture(scope="module")
def policies():
    return load_policies()


@pytest.fixture(scope="module")
def catalog():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    return {p["name"]: set(p["capabilities"]) for p in seed["products"]}


def E(i, etype, session="s1", **metadata):
    return EventView(event_id=f"e{i}", event_type=etype, session_id=session,
                     metadata=metadata)


def fired(events, policies):
    return {d.pattern_id: d for d in evaluate_patterns(events, policies)}


def qualifying(doc_topics, categories, terms, n):
    """`n` distinct qualifying events built from the routes a pattern declares.

    These tests used to reach for `sorted(doc_topics)[0]`, which silently
    assumed every domain research pattern owns at least one documentation
    topic. BP-020 and BP-021 own none on purpose — every topic that would
    belong to them is already read by the lens pattern of the same name, and
    both concepts sit Primary on the same requirement as that lens, so sharing
    a topic would count one page twice (Decision #077). The assumption would
    have made the two new patterns untestable instead of making itself visible.

    Routes are interleaved rather than concatenated so a small `n` still draws
    on more than one kind of signal — which is the point of the
    cross-contamination test below.
    """
    docs = [("DOCUMENTATION_VIEWED", {"topic": t}) for t in sorted(doc_topics)]
    searches = [("SEARCH", {"query": t}) for t in sorted(terms)]
    cats = []
    for category in sorted(categories):
        cats += [("PRODUCT_VIEWED", {"category": category}),
                 ("CATEGORY_VIEWED", {"category": category})]
    routes = []
    for group in zip_longest(docs, searches, cats):
        routes += [route for route in group if route is not None]
    assert len(routes) >= n, f"pattern declares only {len(routes)} routes, needed {n}"
    return [E(i + 1, etype, **metadata)
            for i, (etype, metadata) in enumerate(routes[:n])]


# --- Activation --------------------------------------------------------------

def test_every_domain_pattern_activates_on_two_signals(policies):
    """One ladder for all seven, matching BP-003 and BP-007: two qualifying
    signals activate at Medium. Shopping for payroll must be no harder to
    recognise than shopping for AI."""
    for pattern_id, concept_id, doc_topics, categories, terms in DOMAIN_RESEARCH_PATTERNS:
        events = qualifying(doc_topics, categories, terms, 2)
        draft = fired(events, policies).get(pattern_id)
        assert draft is not None, f"{pattern_id} did not activate on two signals"
        assert draft.strength == "MEDIUM"
        assert draft.concept_ids == [concept_id]


def test_one_signal_is_never_enough(policies):
    """A single glance is not research. Without this the patterns would fire on
    any product view in the category, and every casual visit would publish a
    need."""
    for pattern_id, _concept, doc_topics, categories, terms in DOMAIN_RESEARCH_PATTERNS:
        events = qualifying(doc_topics, categories, terms, 1)
        assert pattern_id not in fired(events, policies)


def test_four_signals_reach_strong(policies):
    for pattern_id, _concept, doc_topics, categories, terms in DOMAIN_RESEARCH_PATTERNS:
        events = qualifying(doc_topics, categories, terms, 4)
        draft = fired(events, policies)[pattern_id]
        assert draft.strength == "STRONG", f"{pattern_id} stalled at {draft.strength}"


def test_domain_patterns_do_not_fire_on_each_others_vocabulary(policies):
    """Cross-contamination is the named risk of adding seven patterns at once
    (doc 14). Each domain's own signals must activate its own pattern and
    nothing else in the family."""
    family = {row[0] for row in DOMAIN_RESEARCH_PATTERNS}
    for pattern_id, _concept, doc_topics, categories, terms in DOMAIN_RESEARCH_PATTERNS:
        events = qualifying(doc_topics, categories, terms, 3)
        others = (family & set(fired(events, policies))) - {pattern_id}
        assert not others, f"{pattern_id}'s evidence also fired {sorted(others)}"


# --- The whole chain --------------------------------------------------------

def test_a_crm_journey_publishes_a_crm_need_and_ranks_a_crm_first(policies, catalog):
    """The live defect, end to end.

    The events are what the browser emits for these products: a CRM's Docs tab
    reports topic `pipeline`, its category is `crm`. Before this change the same
    journey published Workflow Automation and Identity Management.
    """
    events = [E(1, "SEARCH", query="crm"),
              E(2, "PRODUCT_VIEWED", category="crm"),
              E(3, "DOCUMENTATION_VIEWED", topic="pipeline"),
              E(4, "PRODUCT_VIEWED", category="crm"),
              E(5, "DOCUMENTATION_VIEWED", topic="crm")]
    draft = fired(events, policies)["BP-013"]
    assert draft.strength == "STRONG"

    profile = derive_requirements({"BC-019": 0.60}, BC_TO_REQ,
                                  "Technical Validation", policies)
    published = {entry["req_id"]: entry for entry in profile}
    assert "REQ-006" in published, "a CRM journey published no sales requirement"
    assert REQUIREMENTS["REQ-006"] == "Sales & Customer Management"

    ranked = rank_products(
        profile,
        candidate_ids=["Salesforce Sales Cloud", "HubSpot CRM", "Microsoft 365",
                       "ServiceNow", "Zapier"],
        product_capabilities={
            name: catalog.get(name, set()) | _canonical(name) for name in
            ["Salesforce Sales Cloud", "HubSpot CRM", "Microsoft 365",
             "ServiceNow", "Zapier"]},
        req_to_cap=REQ_TO_CAP, policies=policies)
    order = [entry["product_id"] for entry in ranked]
    assert order[0] in ("HubSpot CRM", "Salesforce Sales Cloud"), (
        f"a CRM journey ranked {order[0]} first; order was {order}")
    # The products that prompted the bug must now be *below* the CRMs, not above.
    assert order.index("Microsoft 365") > order.index("Salesforce Sales Cloud")
    assert order.index("ServiceNow") > order.index("Salesforce Sales Cloud")


def _canonical(name):
    from smartreco.domain.software_buying import CANONICAL_PRODUCTS

    for product in CANONICAL_PRODUCTS:
        if product["name"] == name:
            return set(product["capabilities"])
    return set()


def test_every_capability_in_the_catalog_can_be_covered(catalog):
    """The measurable goal of doc 14: no product may be unrecommendable.

    A product holding no capability that any requirement names cannot be scored,
    so it can never appear in a Recommendation Package however well it matches
    what the shopper wants.
    """
    reachable = set().union(*[set(caps) for caps in REQ_TO_CAP.values()])
    stranded = sorted(name for name, caps in catalog.items() if not (caps & reachable))
    assert not stranded, f"{len(stranded)} products can never be recommended: {stranded[:10]}"


def test_new_concepts_all_reach_a_requirement():
    """A concept with no mapping is a belief the platform can hold and never
    act on — the state CRM was in before this change."""
    for _pattern, concept_id, _t, _c, _s in DOMAIN_RESEARCH_PATTERNS:
        assert concept_id in BC_TO_REQ, f"{concept_id} maps to no requirement"
        primaries = [req for req, level in BC_TO_REQ[concept_id].items()
                     if level == "Primary"]
        assert len(primaries) == 1, f"{concept_id} needs exactly one Primary: {primaries}"


def test_returning_to_a_subject_next_session_makes_it_strong(policies):
    """Coming back is evidence (Decision #056).

    Two signals in a sitting is Medium; four is Strong. A shopper who does two,
    leaves, and comes back the next day to do two more used to stay at Medium —
    the v1.2 patterns were the only ones in the pack without the multi-session
    clause BP-004, BP-007 and BP-009 have carried since v1. Persistence across
    a gap is a stronger statement of intent than the same clicking in one go,
    and it is what makes a journey worth resuming rather than merely remembered.
    """
    def views(session_id, prefix):
        return [
            EventView(event_id=f"{prefix}1", event_type="SEARCH", session_id=session_id,
                      metadata={"query": "warehouse etl"}),
            EventView(event_id=f"{prefix}2", event_type="DOCUMENTATION_VIEWED",
                      session_id=session_id, metadata={"topic": "pipelines-data"}),
        ]

    one_sitting = [d for d in evaluate_patterns(views("s1", "a"), policies)
                   if d.pattern_id == "BP-018"]
    assert one_sitting and one_sitting[0].strength == "MEDIUM"

    came_back = [d for d in evaluate_patterns(views("s1", "a") + views("s2", "b"), policies)
                 if d.pattern_id == "BP-018"]
    assert came_back, "Data & Insight did not activate across two sessions"
    assert any(d.strength == "STRONG" for d in came_back), (
        f"returning the next session did not strengthen the belief: "
        f"{[(d.strength, d.explanation) for d in came_back]}")


def test_every_domain_pattern_carries_the_evaluation_stage_milestones():
    """Decision #087. Doc 02 states these are evaluation patterns and therefore
    carry the Research and Technical Validation milestones — "same behaviour,
    different domain, different ceiling: not defensible".

    The list was written as a hardcoded range, so BP-020, BP-021 and BP-022 were
    silently excluded when #077 and #081 added them: an identity, compliance or
    content shopper sat at Awareness on evidence that took a CRM shopper to
    Technical Validation, and POL-REQ-002 gates the Critical band on stage, so
    their requirements could never be Critical.
    """
    from smartreco.domain.software_buying import EVALUATION_PATTERNS, STAGE_MILESTONES

    declared = {row[0] for row in DOMAIN_RESEARCH_PATTERNS}
    assert declared <= set(EVALUATION_PATTERNS), (
        f"not evaluation patterns: {sorted(declared - set(EVALUATION_PATTERNS))}")

    for stage in ("Research", "Technical Validation"):
        milestone = next(m for m in STAGE_MILESTONES if m["stage"] == stage)
        missing = sorted(declared - set(milestone["patterns"]))
        assert not missing, (
            f"{stage} milestone omits {missing} — a journey built on them is "
            "stranded below the stage that gates the Critical band")


def test_a_subject_pattern_alone_reaches_technical_validation():
    """The behavioural half of the same claim, through the stage engine rather
    than the descriptor: one Strong subject evidence must be worth the same
    stage whichever domain it belongs to."""
    from smartreco.engines.stages import determine_stage

    reached = {}
    for pattern_id, concept_id, *_rest in DOMAIN_RESEARCH_PATTERNS:
        evidence = [{"pattern_id": pattern_id, "strength": "STRONG",
                     "concept_ids": [concept_id], "supporting_event_ids": ["e1"]}]
        reached[pattern_id] = determine_stage(evidence, {concept_id: 0.7},
                                              [], load_policies())[0]
    laggards = {p: s for p, s in reached.items() if s != "Technical Validation"}
    assert not laggards, f"these subjects cannot reach Technical Validation: {laggards}"


# --- Buying actions count toward what is being bought -------------------------

def buying_journey(categories, n_actions):
    """One product view that names the category, then `n_actions` on that product.

    This is the shape of a shopper who has stopped researching and started
    buying: the category is stated once, by the view, and every action after it
    carries only a product id (Domain Pack doc 13 — no commercial event carries
    a category).
    """
    category = sorted(categories)[0]
    events = [E(1, "PRODUCT_VIEWED", category=category, product_id="PROD-X")]
    actions = ["ADD_TO_CART", "DEMO_REQUESTED", "TRIAL_STARTED", "PRICING_VIEWED"]
    events += [E(i + 2, etype, product_id="PROD-X")
               for i, etype in enumerate(actions[:n_actions])]
    return events


def test_buying_a_product_is_evidence_about_what_is_being_bought(policies):
    """Cart, demo, trial and pricing on a product in the subject's own category.

    A shopper who adds a DevOps product to the cart, asks for a demo and starts
    a trial has made the strongest available statement about what they are
    shopping for — and until this test, none of it reached the concept that
    decides that. Those events fed only the subject-blind patterns (product
    affinity, adoption readiness), so the platform grew confident the shopper
    was ready to buy while never working out *what*.

    Observed on a live journey: 116 events, two carts and two sales contacts on
    DevOps products, and For You held at NOT_READY.
    """
    for pattern_id, concept_id, _topics, categories, _terms in DOMAIN_RESEARCH_PATTERNS:
        events = buying_journey(categories, 3)
        draft = fired(events, policies).get(pattern_id)
        assert draft is not None, (
            f"{pattern_id}: a product view plus cart, demo and trial on that product "
            "produced no evidence about the subject")
        assert draft.concept_ids == [concept_id]
        # The view plus three actions is four qualifying signals — the same
        # ladder every other route climbs (POL/pack: strong_qualifying_events).
        assert draft.strength == "STRONG", f"{pattern_id} stalled at {draft.strength}"


def test_a_buying_action_needs_the_category_established_first(policies):
    """A product id alone says nothing about the subject.

    Category is resolved from the shopper's own product views, so an action on
    a product this journey never viewed cannot be attributed. That is the
    deliberate limit of the fix: it degrades to the previous behaviour rather
    than guessing.
    """
    for pattern_id, _concept, _topics, _categories, _terms in DOMAIN_RESEARCH_PATTERNS:
        orphans = [E(i + 1, etype, product_id="PROD-UNSEEN") for i, etype in enumerate(
            ("ADD_TO_CART", "DEMO_REQUESTED", "TRIAL_STARTED", "PRICING_VIEWED"))]
        assert pattern_id not in fired(orphans, policies)


def test_a_buying_journey_publishes_the_subjects_requirement(policies):
    """The reported defect, end to end: shortlist a product, then commit to it.

    This shopper does almost no reading. They open two DevOps products, compare
    them, check pricing, book a demo and add one to the cart — which is what a
    buyer near the end of a decision actually looks like. Before Decision #092
    the two views were the only qualifying signals, the pattern stalled at
    Medium, the subject never reached POL-REQ-001's bar and its Primary
    Requirement was never published at all.

    Pinned at the requirement rather than the pattern because the pattern was
    never the complaint — an empty For You page was.
    """
    events = [E(1, "PRODUCT_VIEWED", category="devops", product_id="PROD-A"),
              E(2, "PRODUCT_VIEWED", category="devops", product_id="PROD-B"),
              E(3, "COMPARISON_STARTED", product_a="PROD-A", product_b="PROD-B"),
              E(4, "PRICING_VIEWED", product_id="PROD-A", tier="enterprise"),
              E(5, "DEMO_REQUESTED", product_id="PROD-A"),
              E(6, "ADD_TO_CART", product_id="PROD-A")]
    draft = fired(events, policies)["BP-017"]
    assert draft.strength == "STRONG"
    # All four commitments reached the subject, not just the two product views.
    assert len(draft.supporting_event_ids) == 6

    published = {e["req_id"] for e in derive_requirements(
        {"BC-023": 0.60}, BC_TO_REQ, "Technical Validation", policies)}
    assert "REQ-010" in published, "a buying journey published no engineering need"
    assert REQUIREMENTS["REQ-010"] == "Engineering Delivery"


def test_buying_actions_do_not_leak_across_subjects(policies):
    """An action on one subject's product must not qualify another's.

    The category map is keyed by product, so the same cart event reached every
    pattern if the lookup ignored which category came back.
    """
    family = {row[0] for row in DOMAIN_RESEARCH_PATTERNS}
    for pattern_id, _concept, _topics, categories, _terms in DOMAIN_RESEARCH_PATTERNS:
        events = buying_journey(categories, 3)
        others = {p for p in fired(events, policies) if p in family} - {pattern_id}
        assert not others, f"{pattern_id}'s buying actions also fired {sorted(others)}"
