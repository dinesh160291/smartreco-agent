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
    """Build Evidence from a composition of event *kinds*.

    The nth occurrence of a kind is always the same synthetic event id, so a row
    listing more of a kind than the row before it re-cites those earlier events
    and introduces only the extra ones — which is exactly how a session-window
    pattern re-reports its session.
    """
    seen: dict[str, int] = {}
    events = []
    for event_type in composition:
        seen[event_type] = seen.get(event_type, 0) + 1
        events.append((f"{event_type}-{seen[event_type]}", event_type))
    return EvidenceInput(
        pattern_id=pattern,
        strength=strength,
        supporting_events=tuple(events),
        relation=relation,
        age_days=age_days,
    )


def test_single_contributions_match_pol_conf_001(policies):
    assert compute_confidence([ev("BP-001", "WEAK", ["SEARCH"])], policies).confidence == 0.05
    assert compute_confidence([ev("BP-001", "MEDIUM", ["SEARCH"])], policies).confidence == 0.10
    assert compute_confidence([ev("BP-001", "STRONG", ["SEARCH"])], policies).confidence == 0.20
    assert compute_confidence([ev("BP-011", "VERY_STRONG", ["ADD_TO_CART"])], policies).confidence == 0.30


def test_identical_composition_repeats_halve_pol_conf_002(policies):
    """Two security views, reported three times: 0.20 + 0.10 for the two actions.

    The second and third rows re-cite the same two events and are worth nothing
    at all (Decision #091) — the damping is spent on the second *action*, not on
    the second *report*.
    """
    seq = [
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED"]),
        ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED"]),
    ]
    assert compute_confidence(seq, policies).confidence == 0.30


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
    # Six distinct actions: security x3 (0.20+0.10+0.05), documentation x2
    # (0.20+0.10), dwell x1 (0.20), combined by noisy-OR.
    assert compute_confidence(seq, policies).confidence == 0.636
    # Well under the 0.80 the multiset identity used to award, and the per-kind
    # damping is visible: three security views are worth 0.35, not 0.60.


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
    # Three kinds, one action each, none of them a repeat: 1 - 0.8^3.
    assert compute_confidence(seq, policies).confidence == 0.488


def test_a_change_of_strength_contributes_full_value(policies):
    """Escalation is a new finding even over the same behavior kinds.

    The same two actions re-read at Strong open their own buckets, so a pattern
    that escalates still pays — including on the multi-session clause, where the
    escalation arrives with no new event attached.
    """
    seq = [
        ev("BP-002", "MEDIUM", ["DOCUMENTATION_VIEWED", "SECURITY_VIEWED"]),
        ev("BP-002", "STRONG", ["DOCUMENTATION_VIEWED", "SECURITY_VIEWED"]),
    ]
    # 1 - (0.9 x 0.9 x 0.8 x 0.8): two Medium buckets, then two Strong ones.
    assert compute_confidence(seq, policies).confidence == 0.4816
    assert (compute_confidence(seq, policies).confidence
            > compute_confidence(seq[:1], policies).confidence)


def cited(pattern, strength, pairs, relation="SUPPORTING", age_days=0.0):
    """Evidence citing named events — the shape the pipeline actually passes."""
    return EvidenceInput(pattern_id=pattern, strength=strength,
                         supporting_events=tuple(pairs), relation=relation,
                         age_days=age_days)


# The BP-001 and BP-002 Evidence rows written by the Story 1 clickstream, read
# back from the acceptance replay. Naming the events is the point: under
# Decision #091 confidence depends on *which* actions a row cites, so a fixture
# that lists only kinds cannot mirror the run. These are the same e-numbers the
# acceptance test inserts.
_SEC, _DOC, _DWELL, _PRICE = (
    "SECURITY_VIEWED", "DOCUMENTATION_VIEWED", "DWELL", "PRICING_VIEWED")

STORY1_BC001 = [
    ("MEDIUM", [("e03", _SEC), ("e04", _DOC)]),
    ("STRONG", [("e03", _SEC), ("e04", _DOC), ("e10", _DWELL), ("e11", _DWELL),
                ("e12", _DWELL), ("e13", _DWELL), ("e14", _DWELL), ("e15", _DWELL),
                ("e16", _SEC), ("e17", _DOC)]),
    ("STRONG", [("e30", _SEC), ("e31", _SEC), ("e32", _SEC), ("e33", _SEC)]),
    ("STRONG", [("e30", _SEC), ("e31", _SEC), ("e32", _SEC), ("e33", _SEC),
                ("e40", _SEC), ("e41", _DOC), ("e42", _DOC)]),
    ("STRONG", [("e30", _SEC), ("e31", _SEC), ("e32", _SEC), ("e33", _SEC),
                ("e40", _SEC), ("e41", _DOC), ("e42", _DOC), ("e50", _SEC),
                ("e52", _DOC)]),
]

STORY1_BC002 = [
    ("MEDIUM", [("e05", _DOC), ("e06", _DOC)]),
    ("MEDIUM", [("e05", _DOC), ("e06", _DOC), ("e16", _SEC)]),
    ("STRONG", [("e05", _DOC), ("e06", _DOC), ("e16", _SEC), ("e34", _DOC), ("e35", _DOC)]),
    ("STRONG", [("e05", _DOC), ("e06", _DOC), ("e16", _SEC), ("e34", _DOC), ("e35", _DOC),
                ("e43", _PRICE)]),
    ("STRONG", [("e05", _DOC), ("e06", _DOC), ("e16", _SEC), ("e34", _DOC), ("e35", _DOC),
                ("e43", _PRICE), ("e51", _PRICE), ("e53", _DOC)]),
]


def test_story1_hypothesis_confidences_are_derivable(policies):
    """Story 1 must reach BC-001 0.819065 / BC-002 0.737605 (Domain 09 Scenario 1).

    Re-derived under Decision #091, which counts each action once instead of
    each Evidence row. Mirrors the clickstream in test_story1_acceptance — if
    these two diverge, the scenario is no longer the thing the acceptance test
    replays, so both must move together or neither.
    """
    assert compute_confidence(
        [cited("BP-001", s, p) for s, p in STORY1_BC001], policies).confidence == 0.819065
    assert compute_confidence(
        [cited("BP-002", s, p) for s, p in STORY1_BC002], policies).confidence == 0.737605


def test_the_story1_mirror_cites_the_events_the_acceptance_run_cites(policies):
    """The mirror is only evidence if it fails when the clickstream changes.

    Dropping the second session's security reading has to move BC-001 — if it
    does not, the fixture is no longer coupled to the run it claims to mirror.
    """
    trimmed = [cited("BP-001", s, p) for s, p in STORY1_BC001[:2]]
    assert compute_confidence(trimmed, policies).confidence < 0.819065


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


# Cumulative per-kind counts of the fourteen BP-017 Evidence rows written by
# journey J-11-569f23cc, read back from the running demo database. Every row is
# a strict superset of the one before it — the session-window pattern re-reports
# the whole session on every run — so the shopper's 46 distinct qualifying
# events arrive as fourteen overlapping snapshots.
JOURNEY_DEVOPS_EVIDENCE = [
    # (strength, searches, product views, documentation views) — cumulative
    ("MEDIUM", 1, 1, 0),
    ("STRONG", 2, 1, 1),
    ("STRONG", 3, 2, 2),
    ("STRONG", 3, 3, 3),
    ("STRONG", 5, 5, 4),
    ("STRONG", 8, 7, 4),
    ("STRONG", 8, 7, 5),
    ("STRONG", 8, 8, 5),
    ("STRONG", 9, 9, 5),
    ("STRONG", 11, 10, 5),
    ("STRONG", 12, 11, 5),
    ("STRONG", 17, 15, 6),
    ("STRONG", 18, 17, 7),
    ("STRONG", 20, 18, 8),
]


def devops_subject_evidence():
    """The J-11-569f23cc BP-017 sequence, built the way the pipeline builds it."""
    return [
        ev("BP-017", strength,
           ["SEARCH"] * s + ["PRODUCT_VIEWED"] * p + ["DOCUMENTATION_VIEWED"] * d)
        for strength, s, p, d in JOURNEY_DEVOPS_EVIDENCE
    ]


def test_a_declared_subject_is_publishable_before_the_shopper_gives_up(policies):
    """46 qualifying events on one subject must clear POL-REQ-001's 0.5 bar.

    The shopper of J-11-569f23cc searched DevOps terms twenty times, opened
    eighteen DevOps products and read eight DevOps documentation pages across
    eighteen minutes — then added two of those products to the cart and asked
    sales to contact them twice. Engineering Delivery Evaluation is the subject
    the Domain Pack has for exactly this, and it is BC-023's only feeder, so its
    confidence *is* whether the platform knows what the journey is about.

    It reached 0.499951 and stopped. POL-CONF-002 damped by multiplying the
    previous *increment*, so the running sum is a geometric series whose
    supremum is twice the class contribution of each distinct identity — here
    0.10 + (2 x 0.20) = 0.50 exactly, approached from below and never reached.
    The Primary Requirement of the subject was therefore never published, no
    subject was ever anchored (POL-REQ-004), every candidate ranked off-subject,
    and For You held at NOT_READY no matter how much the shopper clicked.

    The bar is the assertion, not the number: a subject this heavily evidenced
    must be publishable. Decisions #036 and #054 both moved this ceiling by
    redefining which Evidence counts as identical; neither removed it.
    """
    confidence = compute_confidence(devops_subject_evidence(), policies).confidence
    publication_bar = policies.param("POL-REQ-001", "min_confidence")
    assert confidence >= publication_bar, (
        f"BC-023 reached {confidence} on 46 qualifying events — below the {publication_bar} "
        "publication bar, so the shopper's declared subject can never be recommended")


def test_restating_a_finding_cannot_move_confidence_at_all(policies):
    """Re-reporting with nothing new must be worth nothing, not merely little.

    POL-CONF-002 exists because session-window patterns re-report the whole
    session every run (Decision #054). Damping shrinks that inflation; it does
    not remove it, and what leaks through is indistinguishable from evidence.
    Chapter 05 damps repeated *actions* — twenty views of one page — so a run
    that observed no new action must not move the number.
    """
    seq = devops_subject_evidence()
    settled = compute_confidence(seq, policies).confidence
    # Five more runs, each re-reporting the identical 46 events.
    restated = compute_confidence(seq + [seq[-1]] * 5, policies).confidence
    assert restated == settled, (
        f"five restatements of the same 46 events moved confidence {settled} -> {restated}")

    # The 46-event sequence alone cannot police this: by then every bucket is so
    # deep that an undamped leak lands below the sixth decimal and rounds away.
    # A two-event finding is where a leak is still visible, so this is the case
    # that fails if the counting stops being per-action.
    small = [ev("BP-004", "STRONG", ["SECURITY_VIEWED", "DOCUMENTATION_VIEWED"])]
    assert compute_confidence(small * 6, policies).confidence == \
        compute_confidence(small, policies).confidence


def test_diversity_pays_through_the_combination_not_a_bonus(policies):
    """Chapter 05 wants diversity to strengthen confidence. Decision #091 pays it
    where it is earned rather than as POL-CONF-001's flat increment.

    A second pattern brings its own independent buckets, so noisy-OR raises the
    total by construction. The retired increment paid for that same diversity a
    second time, which was enough to lift a concept that merely shares another's
    Evidence above the concept whose pattern produced it.
    """
    first = [ev("BP-005", "MEDIUM", ["PRODUCT_VIEWED", "CATEGORY_VIEWED"])]
    second = [ev("BP-006", "WEAK", ["SEARCH", "DOCUMENTATION_VIEWED"])]
    both = compute_confidence(first + second, policies).confidence
    assert both > compute_confidence(first, policies).confidence
    assert both > compute_confidence(second, policies).confidence
    # 1 - (0.9 x 0.9 x 0.95 x 0.95) — two Medium buckets and two Weak ones.
    assert both == 0.268975


def test_contradiction_subtracts_75pct_of_class_pol_conf_003(policies):
    seq = [
        ev("BP-002", "STRONG", ["PRICING_VIEWED", "DOCUMENTATION_VIEWED"]),
        ev("BP-002", "MEDIUM", ["PRICING_VIEWED"], relation="CONTRADICTING"),
    ]
    # Support 1 - 0.8^2 = 0.36; one contradicting action costs 0.75 x 0.10.
    assert compute_confidence(seq, policies).confidence == 0.285


def test_saturation_cap_and_floor_pol_conf_004(policies):
    # Reaching the cap takes genuinely varied evidence: seven patterns, each
    # reading two kinds of behavior, is fourteen independent buckets at Strong —
    # 1 - 0.8^14 = 0.956, which the cap holds at 0.95.
    strong = [
        ev(f"BP-{n:03d}", "STRONG", ["SECURITY_VIEWED", "DOCUMENTATION_VIEWED"])
        for n in range(1, 8)
    ]
    assert compute_confidence(strong, policies).confidence == 0.95
    # Six of those patterns must *not* reach it, or the cap is doing no work.
    assert compute_confidence(strong[:6], policies).confidence < 0.95
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
    # A second security view, a month old like the first — the repeat has to be
    # a second *action*, since a re-report of the first is worth nothing now.
    seq = [ev("BP-001", "STRONG", ["SECURITY_VIEWED"], age_days=31),
           ev("BP-001", "STRONG", ["SECURITY_VIEWED", "SECURITY_VIEWED"], age_days=31)]
    # 0.20 -> aged 0.10; second action damps 0.20 to 0.10 -> aged 0.05
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
    db.commit()                      # events reference the journey by foreign key
    # Evidence has to cite real events: confidence is computed over the actions a
    # row names (Decision #091), so a row citing none is worth nothing and would
    # make this test pass for the wrong reason. No Evidence row in the running
    # system cites an empty set.
    db.add(models.Session(session_id="s-age", user_id=user.id,
                          started_at=written, last_event_at=written))
    events = [("a1", "SECURITY_VIEWED"), ("a2", "DOCUMENTATION_VIEWED")]
    for eid, etype in events:
        db.add(models.Event(
            event_id=eid, user_id=user.id, session_id="s-age", journey_id="J-age",
            event_type=etype, signal_class="HIGH", event_metadata={},
            ts=written, received_at=written))
    db.commit()
    for i, strength in enumerate(("STRONG", "MEDIUM")):
        db.add(models.Evidence(
            evidence_id=f"BE-age-{i}", journey_id="J-age", pattern_id=f"BP-00{i + 1}",
            strength=strength, concept_ids=["BC-001"], contradicts_concept_ids=[],
            supporting_event_ids=[eid for eid, _ in events],
            explanation="fixture", created_at=written))
    db.commit()

    same_day = _update_hypotheses(db, policies, "J-age", written + timedelta(hours=1))
    two_months = _update_hypotheses(db, policies, "J-age", written + timedelta(days=60))
    assert same_day["BC-001"] > two_months["BC-001"], (
        f"month-old evidence scored the same as fresh: {same_day} vs {two_months}")
