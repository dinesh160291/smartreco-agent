"""Signature tests: trigger evaluator (docs/core/23; POL-TRIG-001/002/003/005).

Deterministic gate sequence: condition → debounce → cooldown → concurrency →
budget. Every decision — including SKIP — is explainable. Times are supplied by
the caller (simulated clock; no real waits)."""

import pytest

from smartreco.engines.triggers import TriggerContext, evaluate_trigger
from smartreco.policies import load_policies


@pytest.fixture(scope="module")
def policies():
    return load_policies()


def ctx(**overrides):
    base = dict(
        unprocessed_high_medium_events=0,
        newest_event_age_seconds=120.0,   # burst is over (debounce window passed)
        seconds_since_last_run=None,      # no prior run
        run_in_flight=False,
        tier1_calls_today=0,
        tier2_calls_today=0,
    )
    base.update(overrides)
    return TriggerContext(**base)


def test_accumulation_threshold_pol_trig_001(policies):
    decision = evaluate_trigger("EVENT_ACCUMULATION", ctx(unprocessed_high_medium_events=5), policies)
    assert decision.run is True
    decision = evaluate_trigger("EVENT_ACCUMULATION", ctx(unprocessed_high_medium_events=4), policies)
    assert decision.run is False and "accumulation" in decision.reason


def test_significant_event_debounce_pol_trig_002(policies):
    burst = ctx(unprocessed_high_medium_events=1, newest_event_age_seconds=5.0)
    decision = evaluate_trigger("SIGNIFICANT_EVENT", burst, policies)
    assert decision.run is False and "debounce" in decision.reason
    settled = ctx(unprocessed_high_medium_events=1, newest_event_age_seconds=61.0)
    assert evaluate_trigger("SIGNIFICANT_EVENT", settled, policies).run is True


def test_cooldown_blocks_but_stage_transition_bypasses(policies):
    recent = ctx(unprocessed_high_medium_events=5, seconds_since_last_run=120.0)
    decision = evaluate_trigger("EVENT_ACCUMULATION", recent, policies)
    assert decision.run is False and "cooldown" in decision.reason
    assert evaluate_trigger("STAGE_TRANSITION", recent, policies).run is True
    cooled = ctx(unprocessed_high_medium_events=5, seconds_since_last_run=601.0)
    assert evaluate_trigger("EVENT_ACCUMULATION", cooled, policies).run is True


def test_concurrency_skip_pol_trig_005(policies):
    busy = ctx(unprocessed_high_medium_events=5, run_in_flight=True)
    decision = evaluate_trigger("EVENT_ACCUMULATION", busy, policies)
    assert decision.run is False and "already-running" in decision.reason


def test_budget_gates_slow_path_only_pol_trig_003(policies):
    exhausted = ctx(unprocessed_high_medium_events=5, tier1_calls_today=10, tier2_calls_today=20)
    decision = evaluate_trigger("EVENT_ACCUMULATION", exhausted, policies)
    # Budget exhaustion never blocks the deterministic run — it degrades the slow path
    assert decision.run is True
    assert decision.tier1_allowed is False
    assert decision.tier2_allowed is False
    fresh = ctx(unprocessed_high_medium_events=5)
    open_decision = evaluate_trigger("EVENT_ACCUMULATION", fresh, policies)
    assert open_decision.tier1_allowed is True and open_decision.tier2_allowed is True
