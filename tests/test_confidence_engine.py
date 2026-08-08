"""Signature tests: Confidence Engine arithmetic.

Pins POL-CONF-001 (class contributions + diversity), POL-CONF-002 (diminishing
returns under the Decision #036 identity), POL-CONF-003 (contradiction penalty),
POL-CONF-004 (saturation), POL-CONF-005 (retirement) — docs/core/05 + 10.
Also pins the Story 1 hypothesis confidences (0.80 / 0.70) that the Scenario 1
requirement derivation depends on (docs/domains/software-buying/09).
"""

import pytest

from smartreco.engines.confidence import EvidenceInput, compute_confidence, should_retire
from smartreco.policies import load_policies


@pytest.fixture(scope="module")
def policies():
    return load_policies()


def ev(pattern, strength, composition, relation="SUPPORTING"):
    return EvidenceInput(
        pattern_id=pattern,
        strength=strength,
        event_type_composition=tuple(sorted(composition)),
        relation=relation,
    )


def test_single_contributions_match_pol_conf_001(policies):
    assert compute_confidence([ev("BP-001", "WEAK", ["SEARCH"])], policies).confidence == 0.05
    assert compute_confidence([ev("BP-001", "MEDIUM", ["SEARCH"])], policies).confidence == 0.10
    assert compute_confidence([ev("BP-001", "STRONG", ["SEARCH"])], policies).confidence == 0.20
    assert compute_confidence([ev("BP-011", "VERY_STRONG", ["ADD_TO_CART"])], policies).confidence == 0.30


def test_identical_composition_repeats_halve_pol_conf_002(policies):
    # Same pattern, same strength, same composition: 0.20 + 0.10 + 0.05
    seq = [
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED"]),
    ]
    assert compute_confidence(seq, policies).confidence == 0.35


def test_changed_composition_contributes_full_value_decision_036(policies):
    # Same pattern+strength but growing event-type composition: full value each
    seq = [
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "DOCUMENTATION_VIEWED", "DWELL"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED", "DOCUMENTATION_VIEWED", "DWELL"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED", "DOCUMENTATION_VIEWED",
                                "DOCUMENTATION_VIEWED", "DWELL"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED", "SECURITY_VIEWED",
                                "DOCUMENTATION_VIEWED", "DOCUMENTATION_VIEWED", "DWELL"]),
    ]
    assert compute_confidence(seq, policies).confidence == 0.80  # Story 1: BC-001


def test_story1_bc002_reaches_070(policies):
    seq = [
        ev("BP-002", "MEDIUM", ["PRICING_VIEWED", "DOCUMENTATION_VIEWED"]),
        ev("BP-002", "STRONG", ["PRICING_VIEWED", "DOCUMENTATION_VIEWED", "SECURITY_VIEWED"]),
        ev("BP-002", "STRONG", ["PRICING_VIEWED", "DOCUMENTATION_VIEWED", "DOCUMENTATION_VIEWED",
                                "SECURITY_VIEWED"]),
        ev("BP-002", "STRONG", ["PRICING_VIEWED", "PRICING_VIEWED", "DOCUMENTATION_VIEWED",
                                "DOCUMENTATION_VIEWED", "SECURITY_VIEWED"]),
    ]
    assert compute_confidence(seq, policies).confidence == 0.70  # Story 1: BC-002


def test_diversity_increment_per_distinct_pattern_beyond_first(policies):
    # Two distinct patterns supporting one hypothesis: +0.10 diversity bonus
    seq = [
        ev("BP-005", "MEDIUM", ["PRODUCT_VIEWED", "CATEGORY_VIEWED"]),
        ev("BP-006", "WEAK", ["SEARCH", "DOCUMENTATION_VIEWED"]),
    ]
    # 0.10 + 0.05 + 0.10 (diversity)
    assert compute_confidence(seq, policies).confidence == 0.25


def test_contradiction_subtracts_75pct_of_class_pol_conf_003(policies):
    seq = [
        ev("BP-002", "STRONG", ["PRICING_VIEWED", "DOCUMENTATION_VIEWED"]),
        ev("BP-002", "MEDIUM", ["PRICING_VIEWED"], relation="CONTRADICTING"),
    ]
    # 0.20 − 0.75×0.10 = 0.125
    assert compute_confidence(seq, policies).confidence == 0.125


def test_saturation_cap_and_floor_pol_conf_004(policies):
    strong = [
        ev("BP-001", "STRONG", ["SECURITY_VIEWED"] * n + ["DOCUMENTATION_VIEWED"])
        for n in range(1, 8)
    ]
    assert compute_confidence(strong, policies).confidence == 0.95  # capped, not 1.40
    contradicted = [
        ev("BP-001", "MEDIUM", ["SEARCH"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED"], relation="CONTRADICTING"),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "DWELL"], relation="CONTRADICTING"),
    ]
    assert compute_confidence(contradicted, policies).confidence == 0.05  # floored


def test_retirement_needs_two_consecutive_low_updates_pol_conf_005(policies):
    assert should_retire([0.10, 0.10], policies) is True
    assert should_retire([0.10, 0.20], policies) is False
    assert should_retire([0.20, 0.10], policies) is False
    assert should_retire([0.14], policies) is False  # one update is not enough
    assert should_retire([0.15, 0.15], policies) is False  # < 0.15 strictly


def test_explanation_is_deterministic_and_references_evidence(policies):
    seq = [ev("BP-001", "STRONG", ["SECURITY_VIEWED", "DOCUMENTATION_VIEWED"])]
    r1 = compute_confidence(seq, policies)
    r2 = compute_confidence(seq, policies)
    assert r1.explanation == r2.explanation
    assert "BP-001" in r1.explanation
