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
    tier1_budget = policies.param("POL-TRIG-003", "tier1_calls_per_user_per_day")
    tier2_budget = policies.param("POL-TRIG-003", "tier2_calls_per_user_per_day")

    # 1. Condition
    if trigger_type == "EVENT_ACCUMULATION":
        if ctx.unprocessed_high_medium_events < accumulation_threshold:
            return TriggerDecision(False,
                f"accumulation below threshold ({ctx.unprocessed_high_medium_events} < "
                f"{accumulation_threshold}, POL-TRIG-001)")
    elif trigger_type == "SIGNIFICANT_EVENT":
        if ctx.unprocessed_high_medium_events < 1:
            return TriggerDecision(False, "no unprocessed significant event")

    # 2. Debounce — wait for the burst to finish (SIGNIFICANT_EVENT)
    if trigger_type == "SIGNIFICANT_EVENT" and ctx.newest_event_age_seconds < debounce_seconds:
        return TriggerDecision(False,
            f"debounce: newest event {ctx.newest_event_age_seconds}s old < "
            f"{debounce_seconds}s window (POL-TRIG-002)")

    # 3. Cooldown (STAGE_TRANSITION bypasses)
    if (trigger_type not in cooldown_bypass
            and ctx.seconds_since_last_run is not None
            and ctx.seconds_since_last_run < cooldown_seconds):
        return TriggerDecision(False,
            f"cooldown: last run {ctx.seconds_since_last_run}s ago < "
            f"{cooldown_seconds}s (POL-TRIG-002)")

    # 4. Concurrency — SKIP (already-running); events stay accumulated (POL-TRIG-005)
    if ctx.run_in_flight:
        return TriggerDecision(False, "SKIP (already-running) per POL-TRIG-005")

    # 5. Budget — degrades the slow path, never blocks the deterministic run
    return TriggerDecision(
        True,
        f"{trigger_type} passed all gates",
        tier1_allowed=ctx.tier1_calls_today < tier1_budget,
        tier2_allowed=ctx.tier2_calls_today < tier2_budget,
    )
