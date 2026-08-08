"""Signature tests: BP-003 (AI), BP-005 (Collaboration), BP-006 (Productivity),
BP-012 (Product Discovery) — Domain 02 activation rules needed by Stories 2 and 4."""

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


# ---- BP-003 AI Evaluation ----

def test_bp003_activates_on_two_ai_signals(policies):
    events = [E(1, "DOCUMENTATION_VIEWED", topic="ai"),
              E(2, "SEARCH", query="ai meeting summaries")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-003")
    assert len(drafts) == 1
    assert drafts[0].strength == "MEDIUM"
    assert drafts[0].concept_ids == ["BC-003"]


def test_bp003_strong_at_four_qualifying(policies):
    events = [E(1, "DOCUMENTATION_VIEWED", topic="ai"),
              E(2, "SEARCH", query="ai chat assistant"),
              E(3, "PRODUCT_VIEWED", product_id="PROD-009", category="ai productivity"),
              E(4, "DOCUMENTATION_VIEWED", topic="ai")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-003")
    assert len(drafts) == 1 and drafts[0].strength == "STRONG"


def test_bp003_single_signal_does_not_activate(policies):
    events = [E(1, "DOCUMENTATION_VIEWED", topic="ai")]
    assert by_pattern(evaluate_patterns(events, policies), "BP-003") == []


# ---- BP-005 Collaboration Evaluation ----

def test_bp005_activates_and_supports_bc005(policies):
    events = [E(1, "CATEGORY_VIEWED", category="collaboration"),
              E(2, "PRODUCT_VIEWED", product_id="PROD-004", category="collaboration")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-005")
    assert len(drafts) == 1
    assert drafts[0].strength == "MEDIUM"
    assert drafts[0].concept_ids == ["BC-005"]


def test_bp005_strong_at_four_qualifying(policies):
    events = [E(1, "CATEGORY_VIEWED", category="collaboration"),
              E(2, "PRODUCT_VIEWED", product_id="PROD-004", category="collaboration"),
              E(3, "DOCUMENTATION_VIEWED", topic="co-editing"),
              E(4, "DOCUMENTATION_VIEWED", topic="meetings")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-005")
    assert len(drafts) == 1 and drafts[0].strength == "STRONG"


def test_bp005_co_supports_bc006_on_productivity_co_occurrence(policies):
    events = [E(1, "CATEGORY_VIEWED", category="collaboration"),
              E(2, "DOCUMENTATION_VIEWED", topic="co-editing"),
              E(3, "DOCUMENTATION_VIEWED", topic="productivity")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-005")
    assert drafts[0].concept_ids == ["BC-005", "BC-006"]


# ---- BP-006 Productivity Evaluation (Weak/Medium only) ----

def test_bp006_weak_at_activation_medium_at_three(policies):
    two = [E(1, "DOCUMENTATION_VIEWED", topic="templates"),
           E(2, "SEARCH", query="productivity workflows")]
    drafts = by_pattern(evaluate_patterns(two, policies), "BP-006")
    assert len(drafts) == 1 and drafts[0].strength == "WEAK"
    three = two + [E(3, "DOCUMENTATION_VIEWED", topic="tasks")]
    drafts = by_pattern(evaluate_patterns(three, policies), "BP-006")
    assert drafts[0].strength == "MEDIUM"  # no Strong level defined for BP-006


# ---- BP-012 Product Discovery ----

def test_bp012_needs_three_events_spanning_two_entities(policies):
    events = [E(1, "SEARCH", query="crm tools"),
              E(2, "PRODUCT_VIEWED", product_id="PROD-002", category="collaboration"),
              E(3, "PRODUCT_VIEWED", product_id="PROD-005", category="collaboration")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-012")
    assert len(drafts) == 1
    assert drafts[0].strength == "WEAK"
    assert drafts[0].concept_ids == ["BC-011"]


def test_bp012_medium_at_five_events(policies):
    events = [E(1, "CATEGORY_VIEWED", category="crm"),
              E(2, "PRODUCT_VIEWED", product_id="PROD-002"),
              E(3, "PRODUCT_VIEWED", product_id="PROD-005"),
              E(4, "CATEGORY_VIEWED", category="devops"),
              E(5, "PRODUCT_VIEWED", product_id="PROD-006")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-012")
    assert drafts[0].strength == "MEDIUM"


def test_bp012_silent_when_concentrated_on_one_product(policies):
    events = [E(1, "PRODUCT_VIEWED", product_id="PROD-003"),
              E(2, "PRODUCT_VIEWED", product_id="PROD-003"),
              E(3, "PRODUCT_VIEWED", product_id="PROD-003")]
    assert by_pattern(evaluate_patterns(events, policies), "BP-012") == []


def test_bp012_silent_below_three_events(policies):
    events = [E(1, "SEARCH", query="tools"),
              E(2, "PRODUCT_VIEWED", product_id="PROD-002")]
    assert by_pattern(evaluate_patterns(events, policies), "BP-012") == []
