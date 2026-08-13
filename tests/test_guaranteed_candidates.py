"""Signature tests: a product that fully covers a published requirement is
always considered (Decision #060).

Semantic retrieval returns the products whose Embedding Document sits nearest
the query. That is the right tool for fuzzy fit, and the wrong one for a
question we can answer exactly: coverage is a set comparison over the
Requirement→Capability map, computable for the whole catalog in microseconds.

Observed live: GitHub covers Engineering Delivery 5/5 and sat around rank 13,
outside a Candidate Set of 8, because its own Embedding Document spans nine
capabilities across two domains and its vector is the average of both. No
amount of query tuning reaches it — the dilution is on the product side.
"""

import pytest

from smartreco.engines.matching import guaranteed_candidates

REQ_TO_CAP = {
    "REQ-010": {"CAP-048": "Primary", "CAP-049": "Primary", "CAP-050": "Primary"},
    "REQ-011": {"CAP-053": "Primary", "CAP-054": "Primary"},
}
CAPS = {
    "PROD-GH": {"CAP-048", "CAP-049", "CAP-050", "CAP-016", "CAP-019"},  # covers 010, broad
    "PROD-CI": {"CAP-048", "CAP-049", "CAP-050"},                        # covers 010, focused
    "PROD-DD": {"CAP-048", "CAP-049"},                                   # partial
    "PROD-BQ": {"CAP-053", "CAP-054"},                                   # covers 011
    "PROD-XX": {"CAP-001"},                                              # irrelevant
}
REQS = [{"req_id": "REQ-010", "priority": "CRITICAL"}]


def test_a_full_coverage_product_missed_by_retrieval_is_added():
    added = guaranteed_candidates(REQS, CAPS, REQ_TO_CAP, existing=["PROD-CI", "PROD-XX"], limit=4)
    assert added == ["PROD-GH"]


def test_products_already_retrieved_are_not_duplicated():
    added = guaranteed_candidates(REQS, CAPS, REQ_TO_CAP,
                                  existing=["PROD-GH", "PROD-CI"], limit=4)
    assert added == []


def test_partial_coverage_is_never_guaranteed():
    """Only *full* coverage earns a guaranteed slot. Judging partial fit is
    what retrieval is for; this is the exact answer, not a better guess."""
    added = guaranteed_candidates(REQS, CAPS, REQ_TO_CAP, existing=[], limit=4)
    assert "PROD-DD" not in added


def test_only_published_requirements_count():
    added = guaranteed_candidates(REQS, CAPS, REQ_TO_CAP, existing=[], limit=4)
    assert "PROD-BQ" not in added  # covers REQ-011, which this journey never published


def test_the_addition_is_bounded_and_deterministic():
    """Bounded because an unbounded top-up would swamp the Candidate Set on a
    requirement many products satisfy; deterministic because two identical
    journeys must produce identical Candidate Sets (core 20)."""
    reqs = [{"req_id": "REQ-010", "priority": "CRITICAL"},
            {"req_id": "REQ-011", "priority": "HIGH"}]
    a = guaranteed_candidates(reqs, CAPS, REQ_TO_CAP, existing=[], limit=1)
    b = guaranteed_candidates(reqs, CAPS, REQ_TO_CAP, existing=[], limit=1)
    assert a == b and len(a) == 1


def test_breadth_breaks_the_tie_among_equal_covers():
    """Two products fully cover it; the one holding more capabilities overall
    is the richer product, and is the same tie-break POL-REC-002 ranks with."""
    added = guaranteed_candidates(REQS, CAPS, REQ_TO_CAP, existing=[], limit=2)
    assert added == ["PROD-GH", "PROD-CI"]
