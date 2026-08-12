"""Signature tests: BP-004, BP-007, BP-008, BP-009, BP-010, BP-011 and
BP-002's contradicting rule (Domain 02 — Phase 4 pattern set)."""

import pytest

from smartreco.engines.patterns import EventView, evaluate_patterns
from smartreco.policies import load_policies


@pytest.fixture(scope="module")
def policies():
    return load_policies()


def E(i, etype, session="s1", **metadata):
    return EventView(event_id=f"e{i}", event_type=etype, session_id=session, metadata=metadata)


def by_pattern(drafts, pattern):
    return [d for d in drafts if d.pattern_id == pattern]


# ---- BP-002 contradicting: repeated individual/free-tier pricing ----

def test_bp002_contradicting_on_repeated_individual_tier_pricing(policies):
    events = [E(1, "PRICING_VIEWED", tier="individual"),
              E(2, "PRICING_VIEWED", tier="free")]
    drafts = [d for d in evaluate_patterns(events, policies)
              if d.pattern_id == "BP-002" and d.contradicts]
    assert len(drafts) == 1
    assert drafts[0].contradicts == ("BC-002",)
    assert drafts[0].concept_ids == []
    assert drafts[0].strength == "MEDIUM"


def test_bp002_single_individual_pricing_is_not_contradiction(policies):
    events = [E(1, "PRICING_VIEWED", tier="individual")]
    assert [d for d in evaluate_patterns(events, policies)
            if d.pattern_id == "BP-002" and d.contradicts] == []


# ---- BP-004 Compliance ----

def test_bp004_activates_on_compliance_docs(policies):
    events = [E(1, "DOCUMENTATION_VIEWED", topic="retention"),
              E(2, "SECURITY_VIEWED", topic="certifications", page="soc2")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-004")
    assert len(drafts) == 1 and drafts[0].strength == "MEDIUM"
    assert drafts[0].concept_ids == ["BC-004"]


def test_bp004_strong_across_two_sessions(policies):
    events = [E(1, "DOCUMENTATION_VIEWED", session="s1", topic="compliance"),
              E(2, "DOCUMENTATION_VIEWED", session="s1", topic="audit"),
              E(3, "DOCUMENTATION_VIEWED", session="s2", topic="ediscovery"),
              E(4, "DOCUMENTATION_VIEWED", session="s2", topic="retention")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-004")
    assert drafts and all(d.strength == "STRONG" for d in drafts)


# ---- BP-007 Automation ----

def test_bp007_activation_and_strong(policies):
    two = [E(1, "DOCUMENTATION_VIEWED", topic="workflows"),
           E(2, "SEARCH", query="automate approvals")]
    drafts = by_pattern(evaluate_patterns(two, policies), "BP-007")
    assert len(drafts) == 1 and drafts[0].strength == "MEDIUM"
    four = two + [E(3, "PRODUCT_VIEWED", product_id="PROD-008", category="workflow automation"),
                  E(4, "DOCUMENTATION_VIEWED", topic="triggers")]
    drafts = by_pattern(evaluate_patterns(four, policies), "BP-007")
    assert drafts[0].strength == "STRONG"


# ---- BP-008 Integration ----

def test_bp008_two_integration_docs_medium(policies):
    # Two connector pages — breadth on one kind of integration research, so
    # Medium. The generic `integrations` topic no longer qualifies at all
    # (Decision #055); it was the fallback for products with no connective
    # capability, which is not integration research.
    events = [E(1, "DOCUMENTATION_VIEWED", topic="connectors"),
              E(2, "DOCUMENTATION_VIEWED", topic="connectors")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-008")
    assert len(drafts) == 1 and drafts[0].strength == "MEDIUM"
    assert drafts[0].concept_ids == ["BC-008", "BC-009"]  # co-supports Technical Evaluation


def test_bp008_ignores_the_generic_integrations_topic(policies):
    """Decision #055: the word that used to be every product's fallback."""
    events = [E(1, "DOCUMENTATION_VIEWED", topic="integrations"),
              E(2, "DOCUMENTATION_VIEWED", topic="integrations"),
              E(3, "DOCUMENTATION_VIEWED", topic="integrations")]
    assert not by_pattern(evaluate_patterns(events, policies), "BP-008")


def test_bp008_strong_when_api_and_connector_both_appear(policies):
    events = [E(1, "DOCUMENTATION_VIEWED", topic="api"),
              E(2, "DOCUMENTATION_VIEWED", topic="connectors")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-008")
    assert drafts[0].strength == "STRONG"


# ---- BP-009 Commercial ----

def test_bp009_pricing_plus_comparison(policies):
    events = [E(1, "PRICING_VIEWED", tier="enterprise", product_id="PROD-003"),
              E(2, "COMPARISON_STARTED", product_a="PROD-003", product_b="PROD-001")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-009")
    assert len(drafts) == 1 and drafts[0].strength == "MEDIUM"
    assert drafts[0].concept_ids == ["BC-010"]


def test_bp009_strong_with_pricing_across_sessions(policies):
    events = [E(1, "PRICING_VIEWED", session="s1", product_id="PROD-003"),
              E(2, "PRICING_VIEWED", session="s1", product_id="PROD-001"),
              E(3, "PRICING_VIEWED", session="s2", product_id="PROD-003"),
              E(4, "PRICING_VIEWED", session="s2", product_id="PROD-004")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-009")
    assert drafts and all(d.strength == "STRONG" for d in drafts)


# ---- BP-010 Product Affinity (journey-scoped, product-scoped) ----

def test_bp010_three_views_across_two_sessions(policies):
    events = [E(1, "PRODUCT_VIEWED", session="s1", product_id="PROD-003"),
              E(2, "PRODUCT_VIEWED", session="s1", product_id="PROD-003"),
              E(3, "PRODUCT_VIEWED", session="s2", product_id="PROD-003")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-010")
    assert len(drafts) == 1 and drafts[0].strength == "MEDIUM"
    assert drafts[0].concept_ids == ["BC-012"]


def test_bp010_two_views_plus_same_product_pricing(policies):
    events = [E(1, "PRODUCT_VIEWED", product_id="PROD-003"),
              E(2, "PRODUCT_VIEWED", product_id="PROD-003"),
              E(3, "PRICING_VIEWED", product_id="PROD-003", tier="enterprise")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-010")
    assert len(drafts) == 1


def test_bp010_silent_within_single_session_without_pricing(policies):
    events = [E(1, "PRODUCT_VIEWED", product_id="PROD-003"),
              E(2, "PRODUCT_VIEWED", product_id="PROD-003"),
              E(3, "PRODUCT_VIEWED", product_id="PROD-003")]
    assert by_pattern(evaluate_patterns(events, policies), "BP-010") == []


def test_bp010_contradicting_comparison_after_affinity(policies):
    events = [E(1, "PRODUCT_VIEWED", session="s1", product_id="PROD-003"),
              E(2, "PRODUCT_VIEWED", session="s1", product_id="PROD-003"),
              E(3, "PRODUCT_VIEWED", session="s2", product_id="PROD-003"),
              E(4, "COMPARISON_STARTED", session="s2",
                product_a="PROD-003", product_b="PROD-009")]
    contradictions = [d for d in evaluate_patterns(events, policies)
                      if d.pattern_id == "BP-010" and d.contradicts]
    assert contradictions and contradictions[0].contradicts == ("BC-012",)


# ---- BP-011 Adoption Readiness ----

def test_bp011_cart_is_strong_checkout_is_very_strong(policies):
    cart = [E(1, "ADD_TO_CART", product_id="PROD-003")]
    drafts = by_pattern(evaluate_patterns(cart, policies), "BP-011")
    assert drafts[0].strength == "STRONG"
    assert drafts[0].concept_ids == ["BC-015", "BC-016"]  # co-supports Decision Confidence

    purchase = cart + [E(2, "PURCHASE_COMPLETED", product_id="PROD-003")]
    drafts = by_pattern(evaluate_patterns(purchase, policies), "BP-011")
    assert drafts[0].strength == "VERY_STRONG"


def test_sustained_affinity_co_supports_decision_confidence(policies):
    """Doc 02: 'BC-012 Product Affinity; sustained affinity co-supports BC-016
    Decision Confidence.' The co-support was never implemented (Decision #046).

    Sustained is the pattern's own Strong bar — five qualifying events on one
    product. Below it the shopper is still looking; at it they have converged,
    which is what Decision Confidence describes. Adoption Readiness already
    co-supports the same concept, so this pattern was the only route to it for
    a shopper who converges without yet trialling or buying.
    """
    events = [E(1, "PRODUCT_VIEWED", session="s1", product_id="PROD-003"),
              E(2, "PRODUCT_VIEWED", session="s1", product_id="PROD-003"),
              E(3, "PRODUCT_VIEWED", session="s2", product_id="PROD-003"),
              E(4, "PRODUCT_VIEWED", session="s2", product_id="PROD-003"),
              E(5, "PRICING_VIEWED", session="s2", product_id="PROD-003",
                tier="enterprise")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-010")
    assert len(drafts) == 1 and drafts[0].strength == "STRONG"
    assert drafts[0].concept_ids == ["BC-012", "BC-016"], (
        f"sustained affinity did not co-support Decision Confidence: "
        f"{drafts[0].concept_ids}")
