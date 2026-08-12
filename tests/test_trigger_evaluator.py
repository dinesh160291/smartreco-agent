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
    # Relative to the catalog: this pins the gate, not the tuning. The value
    # itself is pinned in test_policy_catalog, which is where a retuning has to
    # be declared (Decision #048).
    threshold = policies.param("POL-TRIG-001", "unprocessed_event_threshold")
    decision = evaluate_trigger("EVENT_ACCUMULATION", ctx(unprocessed_high_medium_events=threshold), policies)
    assert decision.run is True
    decision = evaluate_trigger("EVENT_ACCUMULATION", ctx(unprocessed_high_medium_events=threshold - 1), policies)
    assert decision.run is False and "accumulation" in decision.reason


def test_significant_event_debounce_pol_trig_002(policies):
    burst = ctx(unprocessed_high_medium_events=1, newest_event_age_seconds=5.0)
    decision = evaluate_trigger("SIGNIFICANT_EVENT", burst, policies)
    assert decision.run is False and "debounce" in decision.reason
    settled = ctx(unprocessed_high_medium_events=1, newest_event_age_seconds=61.0)
    assert evaluate_trigger("SIGNIFICANT_EVENT", settled, policies).run is True


def test_cooldown_blocks_but_stage_transition_bypasses(policies):
    cooldown = policies.param("POL-TRIG-002", "cooldown_seconds")
    threshold = policies.param("POL-TRIG-001", "unprocessed_event_threshold")
    recent = ctx(unprocessed_high_medium_events=threshold,
                 seconds_since_last_run=cooldown - 1)
    decision = evaluate_trigger("EVENT_ACCUMULATION", recent, policies)
    assert decision.run is False and "cooldown" in decision.reason
    assert evaluate_trigger("STAGE_TRANSITION", recent, policies).run is True
    cooled = ctx(unprocessed_high_medium_events=threshold,
                 seconds_since_last_run=cooldown + 1)
    assert evaluate_trigger("EVENT_ACCUMULATION", cooled, policies).run is True


def test_session_end_needs_unprocessed_activity(policies):
    """Core 23: SESSION_END fires when a session closes *with unprocessed
    high/medium activity*. A quiet session that left nothing behind is not an
    occasion to reason."""
    idle = 31 * 60.0  # past POL-TRACK-003's 30-minute window
    nothing_left = ctx(unprocessed_high_medium_events=0, newest_event_age_seconds=idle)
    decision = evaluate_trigger("SESSION_END", nothing_left, policies)
    assert decision.run is False and "unprocessed" in decision.reason


def test_session_end_waits_for_the_session_to_close(policies):
    """The shopper is still clicking: the session has not closed, so its
    boundary has not arrived (POL-TRACK-003)."""
    still_active = ctx(unprocessed_high_medium_events=3, newest_event_age_seconds=600.0)
    decision = evaluate_trigger("SESSION_END", still_active, policies)
    assert decision.run is False and "session" in decision.reason


def test_session_end_runs_below_the_accumulation_threshold(policies):
    """The defect this trigger exists to fix: a shopper who stops clicking with
    fewer than POL-TRIG-001's five events pending — a purchase, say — must still
    be reasoned about. EVENT_ACCUMULATION cannot do it; SESSION_END must."""
    threshold = policies.param("POL-TRIG-001", "unprocessed_event_threshold")
    stranded = ctx(unprocessed_high_medium_events=threshold - 1,
                   newest_event_age_seconds=31 * 60.0)
    assert evaluate_trigger("EVENT_ACCUMULATION", stranded, policies).run is False
    assert evaluate_trigger("SESSION_END", stranded, policies).run is True


def test_session_end_still_respects_cooldown(policies):
    """Only STAGE_TRANSITION bypasses cooldown (Core 23) — SESSION_END is not
    an exception to POL-TRIG-002."""
    recent = ctx(unprocessed_high_medium_events=3, newest_event_age_seconds=31 * 60.0,
                 seconds_since_last_run=policies.param("POL-TRIG-002", "cooldown_seconds") - 1)
    decision = evaluate_trigger("SESSION_END", recent, policies)
    assert decision.run is False and "cooldown" in decision.reason


def test_concurrency_skip_pol_trig_005(policies):
    busy = ctx(unprocessed_high_medium_events=5, run_in_flight=True)
    decision = evaluate_trigger("EVENT_ACCUMULATION", busy, policies)
    assert decision.run is False and "already-running" in decision.reason


def test_budget_gates_slow_path_only_pol_trig_003(policies):
    exhausted = ctx(
        unprocessed_high_medium_events=5,
        tier1_calls_today=policies.param("POL-TRIG-003", "tier1_calls_per_user_per_day"),
        tier2_calls_today=policies.param("POL-TRIG-003", "tier2_calls_per_user_per_day"))
    decision = evaluate_trigger("EVENT_ACCUMULATION", exhausted, policies)
    # Budget exhaustion never blocks the deterministic run — it degrades the slow path
    assert decision.run is True
    assert decision.tier1_allowed is False
    assert decision.tier2_allowed is False
    fresh = ctx(unprocessed_high_medium_events=5)
    open_decision = evaluate_trigger("EVENT_ACCUMULATION", fresh, policies)
    assert open_decision.tier1_allowed is True and open_decision.tier2_allowed is True
