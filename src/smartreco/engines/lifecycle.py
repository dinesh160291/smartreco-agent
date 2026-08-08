"""Journey lifecycle policies — dormancy and closure (docs/core/12; POL-JRES-002/003).

Pure functions over caller-supplied timestamps (simulated-clock testable).
Time alone never closes a journey — closure is authorized exclusively by the
policy rules below; the Journey Resolution Engine executes the transitions.
"""

from datetime import datetime

from smartreco.policies import PolicyCatalog


def should_go_dormant(last_activity_ts: datetime, now: datetime,
                      policies: PolicyCatalog) -> bool:
    """POL-JRES-002: ACTIVE → DORMANT after N days of inactivity."""
    days = policies.param("POL-JRES-002", "dormancy_inactive_days")
    return (now - last_activity_ts).total_seconds() >= days * 86400


def evaluate_closure(
    lifecycle: str,
    has_purchase: bool,
    last_trial_ts: datetime | None,
    last_activity_ts: datetime,
    dormant_since: datetime | None,
    now: datetime,
    policies: PolicyCatalog,
) -> tuple[str | None, str]:
    """POL-JRES-003. Returns (outcome, reason) — outcome None = stays open."""
    if has_purchase:
        return "PURCHASED", "PURCHASE_COMPLETED -> immediate closure (POL-JRES-003)"

    trial_days = policies.param("POL-JRES-003", "trial_adoption_inactive_days")
    if (last_trial_ts is not None
            and last_activity_ts <= last_trial_ts
            and (now - last_trial_ts).total_seconds() >= trial_days * 86400):
        return "PURCHASED", (
            f"TRIAL_STARTED followed by >= {trial_days} days without further journey "
            "activity -> trial-adoption fallback (POL-JRES-003)")

    dormant_days = policies.param("POL-JRES-003", "dormant_closure_days")
    if (lifecycle == "DORMANT" and dormant_since is not None
            and (now - dormant_since).total_seconds() > dormant_days * 86400):
        return "ABANDONED", f"DORMANT > {dormant_days} days (POL-JRES-003)"

    return None, "no closure rule satisfied"
