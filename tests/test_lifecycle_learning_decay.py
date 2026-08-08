"""Signature tests: journey lifecycle, Learning Engine, Decay Engine.

Pins POL-JRES-002 (dormancy), POL-JRES-003 (closure rules incl. trial-adoption
fallback), POL-LEARN-001 (concept-derived traits on CLOSED journeys only),
POL-DECAY-001 (decay + reinforcement resistance) — all with a simulated clock,
never real waits (testing contract; stories doc §Deliberate Non-Story Coverage).
"""

from datetime import datetime, timedelta

import pytest

from smartreco.engines.learning import decay_trait, derive_traits, reinforced_strength
from smartreco.engines.lifecycle import evaluate_closure, should_go_dormant
from smartreco.policies import load_policies


@pytest.fixture(scope="module")
def policies():
    return load_policies()


NOW = datetime(2026, 8, 10, 12, 0)


# ---- POL-JRES-002: dormancy ----

def test_dormancy_after_seven_inactive_days(policies):
    assert should_go_dormant(NOW - timedelta(days=8), NOW, policies) is True
    assert should_go_dormant(NOW - timedelta(days=6), NOW, policies) is False
    assert should_go_dormant(NOW - timedelta(days=7), NOW, policies) is True


# ---- POL-JRES-003: closure ----

def test_purchase_completed_closes_immediately(policies):
    outcome, reason = evaluate_closure(
        lifecycle="ACTIVE", has_purchase=True, last_trial_ts=None,
        last_activity_ts=NOW, dormant_since=None, now=NOW, policies=policies)
    assert outcome == "PURCHASED" and "PURCHASE_COMPLETED" in reason


def test_trial_adoption_fallback_after_seven_quiet_days(policies):
    trial_ts = NOW - timedelta(days=8)
    outcome, _ = evaluate_closure(
        lifecycle="ACTIVE", has_purchase=False, last_trial_ts=trial_ts,
        last_activity_ts=trial_ts, dormant_since=None, now=NOW, policies=policies)
    assert outcome == "PURCHASED"  # trial-adoption fallback

    # Further journey activity after the trial resets the quiet window
    outcome, _ = evaluate_closure(
        lifecycle="ACTIVE", has_purchase=False, last_trial_ts=trial_ts,
        last_activity_ts=NOW - timedelta(days=2), dormant_since=None,
        now=NOW, policies=policies)
    assert outcome is None


def test_dormant_over_thirty_days_closes_abandoned(policies):
    outcome, _ = evaluate_closure(
        lifecycle="DORMANT", has_purchase=False, last_trial_ts=None,
        last_activity_ts=NOW - timedelta(days=40),
        dormant_since=NOW - timedelta(days=31), now=NOW, policies=policies)
    assert outcome == "ABANDONED"
    outcome, _ = evaluate_closure(
        lifecycle="DORMANT", has_purchase=False, last_trial_ts=None,
        last_activity_ts=NOW - timedelta(days=20),
        dormant_since=NOW - timedelta(days=20), now=NOW, policies=policies)
    assert outcome is None  # time alone below the policy bound never closes


# ---- POL-LEARN-001: concept-derived traits ----

def test_traits_derive_only_from_confident_concepts(policies):
    traits = derive_traits({"BC-001": 0.8, "BC-002": 0.59, "BC-011": 0.3}, policies)
    assert traits == [{"trait_name": "Security Evaluation", "final_confidence": 0.8}]


def test_new_trait_strength_and_reinforcement(policies):
    assert reinforced_strength(None, 0.8, policies) == 0.3  # create at 0.3
    # Existing trait: +0.1 weighted by final confidence
    assert reinforced_strength(0.3, 0.8, policies) == pytest.approx(0.38)
    assert reinforced_strength(0.3, 1.0, policies) == pytest.approx(0.4)


# ---- POL-DECAY-001: decay with reinforcement resistance ----

def test_decay_steps_and_resistance(policies):
    # 14 idle days, no reinforcements: −0.05 × (1 − 0) = −0.05
    assert decay_trait(0.5, reinforcement_count=0, inactive_days=14,
                       policies=policies) == pytest.approx(0.45)
    # 28 idle days: two steps
    assert decay_trait(0.5, 0, 28, policies) == pytest.approx(0.40)
    # 56 idle days: four steps
    assert decay_trait(0.5, 0, 56, policies) == pytest.approx(0.30)
    # Higher reinforcement count slows decay: rc=10 → ×(1 − 0.5) = 0.025/step
    assert decay_trait(0.5, 10, 14, policies) == pytest.approx(0.475)
    # Resistance caps at rc=10
    assert decay_trait(0.5, 25, 14, policies) == decay_trait(0.5, 10, 14, policies)
    # Below one full step: no decay
    assert decay_trait(0.5, 0, 13, policies) == 0.5
    # Never below zero — traits are never deleted, they fade
    assert decay_trait(0.05, 0, 56, policies) == 0.0
