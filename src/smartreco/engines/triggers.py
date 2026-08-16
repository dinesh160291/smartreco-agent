"""Trigger evaluator — deterministic gate sequence (docs/core/23).

condition → debounce → cooldown → concurrency → budget. Budget exhaustion never
blocks the deterministic run; it only degrades the slow path (Invariant 4).
All times are caller-supplied — testable with a simulated clock.
"""

from dataclasses import dataclass

from smartreco.policies import PolicyCatalog


@dataclass(frozen=True)
class TriggerContext:
    unprocessed_high_medium_events: int
    newest_event_age_seconds: float
    seconds_since_last_run: float | None  # None = never ran
    run_in_flight: bool
    tier1_calls_today: int
    tier2_calls_today: int
    # The deployment's spend for the day, beside this user's. Two ceilings,
    # because they answer different questions: "has this shopper had their
    # share" and "has this deployment spent its money" (Decision #100). Default
    # zero so a caller that does not care about the instance bill — the tests
    # of the other gates — need not supply it.
    tier1_calls_today_all_users: int = 0
    tier2_calls_today_all_users: int = 0
    # An unprocessed event that closes the journey under POL-JRES-003. Neither
    # waiting gate has anything to wait for once one arrives: debounce waits for
    # a burst to finish and a purchase ends the journey, cooldown protects AI
    # spend and closure is deterministic (Decision #085).
    closing_event_pending: bool = False


@dataclass(frozen=True)
class TriggerDecision:
    run: bool
    reason: str
    tier1_allowed: bool = True
    tier2_allowed: bool = True


def evaluate_trigger(trigger_type: str, ctx: TriggerContext, policies: PolicyCatalog) -> TriggerDecision:
    accumulation_threshold = policies.param("POL-TRIG-001", "unprocessed_event_threshold")
    debounce_seconds = policies.param("POL-TRIG-002", "debounce_seconds")
    cooldown_seconds = policies.param("POL-TRIG-002", "cooldown_seconds")
    cooldown_bypass = policies.param("POL-TRIG-002", "cooldown_bypass_triggers")
    closing_bypass = policies.param(
        "POL-TRIG-002", "closing_events_bypass_debounce_and_cooldown")
    bypass_waits = closing_bypass and ctx.closing_event_pending
    tier1_budget = policies.param("POL-TRIG-003", "tier1_calls_per_user_per_day")
    tier2_budget = policies.param("POL-TRIG-003", "tier2_calls_per_user_per_day")
    tier1_total = policies.param("POL-TRIG-003", "tier1_calls_per_day_total")
    tier2_total = policies.param("POL-TRIG-003", "tier2_calls_per_day_total")

    # 1. Condition
    if trigger_type == "EVENT_ACCUMULATION":
        if ctx.unprocessed_high_medium_events < accumulation_threshold:
            return TriggerDecision(False,
                f"accumulation below threshold ({ctx.unprocessed_high_medium_events} < "
                f"{accumulation_threshold}, POL-TRIG-001)")
    elif trigger_type == "SIGNIFICANT_EVENT":
        if ctx.unprocessed_high_medium_events < 1:
            return TriggerDecision(False, "no unprocessed significant event")
    elif trigger_type == "SESSION_END":
        # "A session closes with unprocessed high/medium-signal activity"
        # (Core 23). Both halves are conditions: something must be left over,
        # and the session must actually be over. Closure is inactivity —
        # POL-TRACK-003's window, the same one the tracking client and journey
        # resolution already treat as the session boundary.
        if ctx.unprocessed_high_medium_events < 1:
            return TriggerDecision(False, "no unprocessed activity at session close")
        session_timeout = policies.param("POL-TRACK-003", "inactivity_minutes") * 60
        if ctx.newest_event_age_seconds < session_timeout:
            return TriggerDecision(False,
                f"session still open: newest event {ctx.newest_event_age_seconds}s old < "
                f"{session_timeout}s (POL-TRACK-003)")

    # 2. Debounce — wait for the burst to finish (SIGNIFICANT_EVENT)
    if (trigger_type == "SIGNIFICANT_EVENT" and not bypass_waits
            and ctx.newest_event_age_seconds < debounce_seconds):
        return TriggerDecision(False,
            f"debounce: newest event {ctx.newest_event_age_seconds}s old < "
            f"{debounce_seconds}s window (POL-TRIG-002)")

    # 3. Cooldown (STAGE_TRANSITION bypasses)
    if (trigger_type not in cooldown_bypass and not bypass_waits
            and ctx.seconds_since_last_run is not None
            and ctx.seconds_since_last_run < cooldown_seconds):
        return TriggerDecision(False,
            f"cooldown: last run {ctx.seconds_since_last_run}s ago < "
            f"{cooldown_seconds}s (POL-TRIG-002)")

    # 4. Concurrency — SKIP (already-running); events stay accumulated (POL-TRIG-005)
    if ctx.run_in_flight:
        return TriggerDecision(False, "SKIP (already-running) per POL-TRIG-005")

    # 5. Budget — degrades the slow path, never blocks the deterministic run.
    #    Both ceilings apply: a shopper must be inside their own allowance *and*
    #    the deployment inside its daily spend. Exhausting either stops the
    #    words and not the answer, which is the whole point of the split.
    return TriggerDecision(
        True,
        f"{trigger_type} passed all gates",
        tier1_allowed=(ctx.tier1_calls_today < tier1_budget
                       and ctx.tier1_calls_today_all_users < tier1_total),
        tier2_allowed=(ctx.tier2_calls_today < tier2_budget
                       and ctx.tier2_calls_today_all_users < tier2_total),
    )
