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


# --- Activation --------------------------------------------------------------

def test_every_domain_pattern_activates_on_two_signals(policies):
    """One ladder for all seven, matching BP-003 and BP-007: two qualifying
    signals activate at Medium. Shopping for payroll must be no harder to
    recognise than shopping for AI."""
    for pattern_id, concept_id, doc_topics, categories, _terms in DOMAIN_RESEARCH_PATTERNS:
        events = [E(1, "DOCUMENTATION_VIEWED", topic=sorted(doc_topics)[0]),
                  E(2, "PRODUCT_VIEWED", category=sorted(categories)[0])]
        draft = fired(events, policies).get(pattern_id)
        assert draft is not None, f"{pattern_id} did not activate on two signals"
        assert draft.strength == "MEDIUM"
        assert draft.concept_ids == [concept_id]


def test_one_signal_is_never_enough(policies):
    """A single glance is not research. Without this the patterns would fire on
    any product view in the category, and every casual visit would publish a
    need."""
    for pattern_id, _concept, doc_topics, _categories, _terms in DOMAIN_RESEARCH_PATTERNS:
        events = [E(1, "DOCUMENTATION_VIEWED", topic=sorted(doc_topics)[0])]
        assert pattern_id not in fired(events, policies)


def test_four_signals_reach_strong(policies):
    for pattern_id, _concept, doc_topics, categories, terms in DOMAIN_RESEARCH_PATTERNS:
        topics = sorted(doc_topics)
        events = [E(1, "SEARCH", query=sorted(terms)[0]),
                  E(2, "PRODUCT_VIEWED", category=sorted(categories)[0]),
                  E(3, "CATEGORY_VIEWED", category=sorted(categories)[0]),
                  E(4, "DOCUMENTATION_VIEWED", topic=topics[0])]
        draft = fired(events, policies)[pattern_id]
        assert draft.strength == "STRONG", f"{pattern_id} stalled at {draft.strength}"


def test_domain_patterns_do_not_fire_on_each_others_vocabulary(policies):
    """Cross-contamination is the named risk of adding seven patterns at once
    (doc 14). Each domain's own signals must activate its own pattern and
    nothing else in the family."""
    family = {row[0] for row in DOMAIN_RESEARCH_PATTERNS}
    for pattern_id, _concept, doc_topics, categories, _terms in DOMAIN_RESEARCH_PATTERNS:
        events = [E(1, "DOCUMENTATION_VIEWED", topic=sorted(doc_topics)[0]),
                  E(2, "PRODUCT_VIEWED", category=sorted(categories)[0]),
                  E(3, "DOCUMENTATION_VIEWED", topic=sorted(doc_topics)[-1])]
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
