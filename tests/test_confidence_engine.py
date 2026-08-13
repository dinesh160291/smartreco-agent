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


def ev(pattern, strength, composition, relation="SUPPORTING", age_days=0.0):
    return EvidenceInput(
        pattern_id=pattern,
        strength=strength,
        event_type_composition=tuple(sorted(composition)),
        relation=relation,
        age_days=age_days,
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


def test_more_of_the_same_kind_damps_decision_054(policies):
    """More events of kinds already counted is the same finding restated.

    This sequence used to reach 0.80 under the Decision #036 multiset identity:
    the composition grew each time, so nothing was ever recognised as a repeat.
    It is the shape every session-window pattern produces, because each run
    re-reports the whole session.
    """
    seq = [
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "DOCUMENTATION_VIEWED", "DWELL"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED", "DOCUMENTATION_VIEWED", "DWELL"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED", "DOCUMENTATION_VIEWED",
                                "DOCUMENTATION_VIEWED", "DWELL"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED", "SECURITY_VIEWED",
                                "DOCUMENTATION_VIEWED", "DOCUMENTATION_VIEWED", "DWELL"]),
    ]
    # 0.20 + 0.10 + 0.05 + 0.025
    assert compute_confidence(seq, policies).confidence == 0.375


def test_a_new_kind_of_behavior_contributes_full_value_decision_054(policies):
    """A behavior kind not seen before for this pattern is a new finding.

    This is what keeps the damping from collapsing to identity-by-pattern,
    which Decision #036 rejected for capping single-pattern concepts near 0.4.
    Reading time appearing alongside pages already read is genuinely new
    information about the shopper; a fifth page view is not.
    """
    seq = [
        ev("BP-001", "STRONG", ["SECURITY_VIEWED"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "DOCUMENTATION_VIEWED"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "DOCUMENTATION_VIEWED", "DWELL"]),
    ]
    assert compute_confidence(seq, policies).confidence == 0.60


def test_a_change_of_strength_contributes_full_value(policies):
    """Escalation is a new finding even over the same behavior kinds."""
    seq = [
        ev("BP-002", "MEDIUM", ["DOCUMENTATION_VIEWED", "SECURITY_VIEWED"]),
        ev("BP-002", "STRONG", ["DOCUMENTATION_VIEWED", "SECURITY_VIEWED"]),
    ]
    assert compute_confidence(seq, policies).confidence == 0.30


def test_story1_hypothesis_confidences_are_derivable(policies):
    """Story 1 must still reach BC-001 0.80 / BC-002 0.70 (Domain 09 Scenario 1).

    Under Decision #054 those numbers are earned by evidence that changes in
    kind or strength, not by repetition. Mirrors the re-derived clickstream in
    test_story1_acceptance — if these two diverge, the scenario is no longer
    the thing the acceptance test replays.
    """
    bc001 = [
        ev("BP-001", "MEDIUM", ["SECURITY_VIEWED", "DOCUMENTATION_VIEWED"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "DOCUMENTATION_VIEWED", "DWELL"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "DOCUMENTATION_VIEWED"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "DOCUMENTATION_VIEWED"]),
    ]
    assert compute_confidence(bc001, policies).confidence == 0.80

    bc002 = [
        ev("BP-002", "MEDIUM", ["DOCUMENTATION_VIEWED"]),
        ev("BP-002", "MEDIUM", ["DOCUMENTATION_VIEWED", "SECURITY_VIEWED"]),
        ev("BP-002", "STRONG", ["DOCUMENTATION_VIEWED", "SECURITY_VIEWED"]),
        ev("BP-002", "STRONG", ["DOCUMENTATION_VIEWED", "SECURITY_VIEWED", "PRICING_VIEWED"]),
        ev("BP-002", "STRONG", ["DOCUMENTATION_VIEWED", "SECURITY_VIEWED", "PRICING_VIEWED"]),
    ]
    assert compute_confidence(bc002, policies).confidence == 0.70


def test_cumulative_restatement_does_not_ratchet_decision_054(policies):
    """A session-window pattern re-reporting the same finding must not compound.

    Replays the defect from journey J-3 (Decision #054): BP-008 fired eight
    times in one session on nothing but Integrations-tab clicks. Every run it
    re-reported the whole session, so under the Decision #036 multiset identity
    the composition grew by one event and the POL-CONF-002 damping never
    engaged — eight Medium readings paid full value and Integration Evaluation
    reached 0.80, minting a Critical Workflow Automation requirement.

    Same pattern, same strength, same *kinds* of behavior = the same finding
    restated. It must converge on the geometric series, not climb to the cap.
    """
    seq = [ev("BP-008", "MEDIUM", ["DOCUMENTATION_VIEWED"] * n) for n in range(2, 12)]
    confidence = compute_confidence(seq, policies).confidence
    assert confidence < 0.25, (
        f"eight restatements of one Medium finding reached {confidence} — "
        "POL-CONF-002 did not engage")
    # 0.10 + 0.05 + 0.025 + ... — bounded by twice the class contribution.
    assert confidence == pytest.approx(0.199, abs=0.001)


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
    # Reaching the cap now takes genuinely varied evidence: five patterns at
    # Strong contribute 5×0.20 plus four diversity increments = 1.40.
    strong = [
        ev(f"BP-00{n}", "STRONG", ["SECURITY_VIEWED", "DOCUMENTATION_VIEWED"])
        for n in range(1, 6)
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


# --- POL-BEH-002: evidence older than 30 days contributes at half weight -----
# (Decision #067 — the policy was published and unread)

def test_aged_evidence_contributes_at_half_weight(policies):
    """A Strong finding is +0.20 fresh; the same finding a month later is worth
    half that. Journeys survive dormancy for weeks, so without this a belief
    formed in July still counted in full in September."""
    fresh = compute_confidence(
        [ev("BP-001", "STRONG", ["SECURITY_VIEWED"])], policies)
    aged = compute_confidence(
        [ev("BP-001", "STRONG", ["SECURITY_VIEWED"], age_days=31)], policies)
    assert fresh.confidence == 0.20
    assert aged.confidence == 0.10


def test_the_age_boundary_is_the_policy_value_not_a_guess(policies):
    """30 days exactly is not yet "older than 30 days"."""
    at = compute_confidence(
        [ev("BP-001", "STRONG", ["SECURITY_VIEWED"], age_days=30)], policies)
    past = compute_confidence(
        [ev("BP-001", "STRONG", ["SECURITY_VIEWED"], age_days=30.5)], policies)
    assert at.confidence == 0.20
    assert past.confidence == 0.10


def test_age_and_diminishing_returns_do_not_compound_each_other(policies):
    """POL-CONF-002 damps repetition, POL-BEH-002 damps age. A repeat of aged
    evidence damps from what the finding was worth, not from what age had
    already taken off it — otherwise the second reading of a month-old finding
    would be quartered by a rule about saying the same thing twice."""
    seq = [ev("BP-001", "STRONG", ["SECURITY_VIEWED"], age_days=31),
           ev("BP-001", "STRONG", ["SECURITY_VIEWED"], age_days=31)]
    # 0.20 -> aged 0.10; repeat damps 0.20 to 0.10 -> aged 0.05
    assert compute_confidence(seq, policies).confidence == 0.15


def test_contradicting_evidence_also_ages(policies):
    """A month-old objection is no more binding than a month-old endorsement."""
    seq = [ev("BP-001", "STRONG", ["SECURITY_VIEWED"]),
           ev("BP-002", "MEDIUM", ["PRICING_VIEWED"], relation="CONTRADICTING",
              age_days=31)]
    fresh_objection = [ev("BP-001", "STRONG", ["SECURITY_VIEWED"]),
                       ev("BP-002", "MEDIUM", ["PRICING_VIEWED"], relation="CONTRADICTING")]
    assert (compute_confidence(seq, policies).confidence
            > compute_confidence(fresh_objection, policies).confidence)


def test_the_pipeline_measures_evidence_age_at_scoring_time(
        seeded, policies):
    """The wiring, not the arithmetic: `_update_hypotheses` must hand the engine
    a real age. Sabotaging it to a constant 0.0 left every other test green,
    which is the whole reason this one exists.

    Scoring the same journey twice — once the day its evidence was written, once
    two months later — must yield a lower confidence the second time, with no
    new evidence in between.
    """
    from datetime import datetime, timedelta

    from smartreco import models
    from smartreco.pipeline import _update_hypotheses
    from tests.test_stories_6_to_9 import _user

    db = seeded
    user = _user(db, "aging@example.com")
    written = datetime(2026, 6, 1, 9, 0)
    db.add(models.Journey(journey_id="J-age", user_id=user.id, lifecycle="ACTIVE",
                          created_at=written))
    db.commit()
    for i, strength in enumerate(("STRONG", "MEDIUM")):
        db.add(models.Evidence(
            evidence_id=f"BE-age-{i}", journey_id="J-age", pattern_id=f"BP-00{i + 1}",
            strength=strength, concept_ids=["BC-001"], contradicts_concept_ids=[],
            supporting_event_ids=[], explanation="fixture", created_at=written))
    db.commit()

    same_day = _update_hypotheses(db, policies, "J-age", written + timedelta(hours=1))
    two_months = _update_hypotheses(db, policies, "J-age", written + timedelta(days=60))
    assert same_day["BC-001"] > two_months["BC-001"], (
        f"month-old evidence scored the same as fresh: {same_day} vs {two_months}")
