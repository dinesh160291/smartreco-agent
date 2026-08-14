"""Signature tests: Recommendation Engine coverage, ranking, readiness.

Pins the Coverage Calculation Model (Domain 05/09), POL-REC-002 ranking weights
and tie-breaks, POL-REC-003 publication, POL-REC-001 readiness — exact numbers
from all four validation scenarios in docs/domains/software-buying/09."""

from datetime import timedelta

import pytest

from smartreco.domain.software_buying import CANONICAL_PRODUCTS, REQ_TO_CAP
from smartreco.engines.matching import evaluate_readiness, rank_products
from smartreco.policies import load_policies

PRODUCT_CAPS = {p["product_id"]: set(p["capabilities"]) for p in CANONICAL_PRODUCTS}


@pytest.fixture(scope="module")
def policies():
    return load_policies()


def req(req_id, confidence, priority):
    return {"req_id": req_id, "confidence": confidence, "priority": priority, "explanation": ""}


def entries_by_product(entries):
    return {e["product_id"]: e for e in entries}


def test_scenario_1_okta_m365_google(policies):
    requirements = [req("REQ-002", 0.94, "CRITICAL"), req("REQ-004", 0.56, "MEDIUM")]
    candidates = ["PROD-003", "PROD-001", "PROD-004"]
    entries = rank_products(requirements, candidates, PRODUCT_CAPS, REQ_TO_CAP, policies)
    assert [e["product_id"] for e in entries] == ["PROD-003", "PROD-001", "PROD-004"]
    by = entries_by_product(entries)
    assert by["PROD-003"]["overall_coverage"] == 83
    assert by["PROD-001"]["overall_coverage"] == 74
    assert by["PROD-004"]["overall_coverage"] == 62
    okta = by["PROD-003"]
    assert okta["per_requirement"]["REQ-002"]["coverage"] == 100
    assert okta["per_requirement"]["REQ-004"]["coverage"] == 31
    assert set(okta["missing_capability_ids"]) == {"CAP-012", "CAP-013", "CAP-014"}
    assert by["PROD-001"]["missing_capability_ids"] == ["CAP-003", "CAP-004"]


def test_scenario_2_google_notion_zoom(policies):
    requirements = [req("REQ-001", 0.83, "CRITICAL"), req("REQ-005", 0.75, "HIGH")]
    candidates = ["PROD-004", "PROD-009", "PROD-005"]
    entries = rank_products(requirements, candidates, PRODUCT_CAPS, REQ_TO_CAP, policies)
    assert [e["product_id"] for e in entries] == ["PROD-004", "PROD-009", "PROD-005"]
    by = entries_by_product(entries)
    assert by["PROD-004"]["overall_coverage"] == 97
    assert by["PROD-009"]["overall_coverage"] == 49
    assert by["PROD-005"]["overall_coverage"] == 33
    assert by["PROD-009"]["per_requirement"]["REQ-001"]["coverage"] == 21  # 1 Primary of 7


def test_scenario_3_servicenow_zapier_m365(policies):
    requirements = [req("REQ-003", 0.94, "CRITICAL")]
    candidates = ["PROD-007", "PROD-008", "PROD-001"]
    entries = rank_products(requirements, candidates, PRODUCT_CAPS, REQ_TO_CAP, policies)
    assert [e["product_id"] for e in entries] == ["PROD-007", "PROD-008", "PROD-001"]
    by = entries_by_product(entries)
    assert by["PROD-007"]["overall_coverage"] == 100
    assert by["PROD-007"]["missing_capability_ids"] == []
    assert by["PROD-008"]["overall_coverage"] == 83
    assert by["PROD-001"]["overall_coverage"] == 74


def test_scenario_4_m365_box_google(policies):
    requirements = [req("REQ-004", 0.80, "CRITICAL")]
    candidates = ["PROD-001", "PROD-010", "PROD-004"]
    entries = rank_products(requirements, candidates, PRODUCT_CAPS, REQ_TO_CAP, policies)
    assert [e["product_id"] for e in entries] == ["PROD-001", "PROD-010", "PROD-004"]
    by = entries_by_product(entries)
    assert by["PROD-001"]["overall_coverage"] == 100
    assert by["PROD-010"]["overall_coverage"] == 81
    assert by["PROD-004"]["overall_coverage"] == 50


def test_tie_break_capability_count_then_product_id(policies):
    # Two products with identical coverage on REQ-003: PROD-008 (4 caps total)
    # loses to PROD-007 (7 caps); equal-everything falls back to product ID.
    requirements = [req("REQ-003", 0.94, "CRITICAL")]
    caps = {"PROD-901": {"CAP-015", "CAP-016"}, "PROD-902": {"CAP-015", "CAP-016"}}
    entries = rank_products(requirements, ["PROD-902", "PROD-901"], caps, REQ_TO_CAP, policies)
    assert [e["product_id"] for e in entries] == ["PROD-901", "PROD-902"]  # ID tie-break
    caps2 = {"PROD-901": {"CAP-015", "CAP-016"}, "PROD-902": {"CAP-015", "CAP-016", "CAP-001"}}
    entries2 = rank_products(requirements, ["PROD-901", "PROD-902"], caps2, REQ_TO_CAP, policies)
    assert [e["product_id"] for e in entries2] == ["PROD-902", "PROD-901"]  # count tie-break


def test_readiness_pol_rec_001(policies):
    ready_reqs = [req("REQ-002", 0.94, "CRITICAL")]
    assert evaluate_readiness(ready_reqs, high_signal_events=5, policies=policies) == "READY"
    assert evaluate_readiness(ready_reqs, high_signal_events=4, policies=policies) == "NOT_READY"
    low_conf = [req("REQ-004", 0.56, "MEDIUM")]
    assert evaluate_readiness(low_conf, high_signal_events=10, policies=policies) == "NOT_READY"
    assert evaluate_readiness([], high_signal_events=10, policies=policies) == "NOT_READY"


# --- The order the shopper sees is the order the engine computed (#071) ------

def test_for_you_renders_entries_in_rank_order(
        seeded, chroma, backend, policies, fake_gateway):
    """POL-REC-002 ranks deterministically and stamps each entry with its rank.
    Nothing between the engine and the page may reorder that: the panel is the
    claim "these are your best matches, best first", and a list that is merely
    *a* permutation of the right products silently breaks it.

    Asserted on the built feed rather than the package, so the assertion covers
    the persistence round-trip and the view assembly, which is where a reorder
    could actually creep in.
    """
    from apps.web.pages import _build_feed
    from tests.test_intent_fork import DAY, _run
    from tests.test_stories_6_to_9 import _insert, _user

    db = seeded
    user = _user(db, "rank-order@example.com")
    # Each batch brings a kind of signal the last lacked, so confidence
    # accumulates rather than damping (Decision #054) and the journey actually
    # reaches a ranking — a thin setup proves nothing here.
    for i, batch in enumerate([
        [("r1", "SEARCH", "HIGH", {"query": "analytics"}),
         ("r2", "SEARCH", "HIGH", {"query": "etl warehouse"}),
         ("r3", "COMPARISON_STARTED", "HIGH", {"product_a": "PROD-009"})],
        [("r4", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "pipelines-data"}),
         ("r5", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "warehouse"}),
         ("r6", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "dashboards"})],
        [("r7", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-009", "category": "data & analytics"}),
         ("r8", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-010", "category": "data & analytics"}),
         ("r9", "PRICING_VIEWED", "HIGH", {"product_id": "PROD-009"})],
        [("r10", "CATEGORY_VIEWED", "MEDIUM", {"category": "data & analytics"}),
         ("r11", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "warehouse"}),
         ("r12", "PRICING_VIEWED", "HIGH", {"product_id": "PROD-010"})],
    ]):
        _insert(db, user.id, "rank-s1", DAY + timedelta(minutes=4 * i), batch)
        _run(db, chroma, backend, policies, user, fake_gateway,
             DAY + timedelta(minutes=4 * i + 2))

    feed = _build_feed(db, user)
    assert feed and feed["entries"], "precondition: no ranking to check"

    ranks = [e["rank"] for e in feed["entries"]]
    assert ranks == sorted(ranks), f"the page reordered the ranking: {ranks}"
    assert ranks == list(range(1, len(ranks) + 1)), (
        f"ranks are not a clean 1..N sequence as rendered: {ranks}")

    coverage = [e["coverage"] for e in feed["entries"]]
    assert coverage == sorted(coverage, reverse=True), (
        f"coverage rises down the list, so rank does not mean best-first: {coverage}")
