"""Behavioral Learning + Decay Engines (docs/core/03, 04; POL-LEARN-001, POL-DECAY-001).

Traits are concept-derived: one trait per Behavioral Concept whose final
hypothesis confidence clears the policy threshold at journey closure — only
CLOSED journeys feed learning. Decay is pure arithmetic over inactive days
with reinforcement resistance; traits fade toward zero but are never deleted,
and decay never touches the reinforcement count.
"""

from smartreco.domain.software_buying import BEHAVIORAL_CONCEPTS
from smartreco.policies import PolicyCatalog


def derive_traits(final_hypotheses: dict[str, float], policies: PolicyCatalog) -> list[dict]:
    """POL-LEARN-001: concepts with final confidence >= threshold become traits
    (trait name = concept display name)."""
    threshold = policies.param("POL-LEARN-001", "trait_min_final_confidence")
    return [
        {"trait_name": BEHAVIORAL_CONCEPTS.get(bc_id, bc_id), "final_confidence": confidence}
        for bc_id, confidence in sorted(final_hypotheses.items())
        if confidence >= threshold
    ]


def reinforced_strength(current_strength: float | None, final_confidence: float,
                        policies: PolicyCatalog) -> float:
    """POL-LEARN-001: create at the new-trait strength; reinforce existing by
    the increment weighted by final hypothesis confidence."""
    if current_strength is None:
        return policies.param("POL-LEARN-001", "new_trait_strength")
    increment = policies.param("POL-LEARN-001", "reinforcement_increment")
    return round(min(1.0, current_strength + increment * final_confidence), 6)


def decay_trait(strength: float, reinforcement_count: int, inactive_days: float,
                policies: PolicyCatalog) -> float:
    """POL-DECAY-001: -decay_amount per step of inactive days, scaled by
    reinforcement resistance; floored at zero, never deleted."""
    step_days = policies.param("POL-DECAY-001", "inactive_days_per_step")
    amount = policies.param("POL-DECAY-001", "decay_amount")
    per_reinforcement = policies.param("POL-DECAY-001", "resistance_factor_per_reinforcement")
    cap = policies.param("POL-DECAY-001", "resistance_reinforcement_cap")

    steps = int(inactive_days // step_days)
    if steps <= 0:
        return strength
    resistance = 1.0 - per_reinforcement * min(reinforcement_count, cap)
    return round(max(0.0, strength - steps * amount * resistance), 6)
