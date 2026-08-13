"""Confidence Engine — deterministic evidence → hypothesis confidence (docs/core/05).

Arithmetic is entirely policy-driven:
  POL-BEH-002 evidence older than the policy's window contributes at half weight
  POL-CONF-001 class contributions + diversity increment
  POL-CONF-002 diminishing returns (identity per Decision #054:
               pattern + strength + the *set* of supporting event types)
  POL-CONF-003 contradiction penalty
  POL-CONF-004 saturation cap/floor
  POL-CONF-005 retirement condition

Pure function over an ordered evidence sequence — replayable by construction.
"""

from dataclasses import dataclass

from smartreco.policies import PolicyCatalog

# Maps the EvidenceStrength enum codes (core 17) to POL-CONF-001 contribution keys.
_STRENGTH_KEY = {"WEAK": "Weak", "MEDIUM": "Medium", "STRONG": "Strong", "VERY_STRONG": "VeryStrong"}


@dataclass(frozen=True)
class EvidenceInput:
    pattern_id: str
    strength: str  # EvidenceStrength code
    event_type_composition: tuple[str, ...]  # sorted multiset of supporting event types
    relation: str = "SUPPORTING"  # SUPPORTING | CONTRADICTING
    age_days: float = 0.0  # at scoring time; POL-BEH-002


@dataclass(frozen=True)
class ConfidenceResult:
    confidence: float
    explanation: str


def compute_confidence(evidence: list[EvidenceInput], policies: PolicyCatalog) -> ConfidenceResult:
    contributions = policies.param("POL-CONF-001", "contribution")
    diversity_increment = policies.param("POL-CONF-001", "diversity_increment")
    repeat_factor = policies.param("POL-CONF-002", "repeat_factor")
    contradiction_factor = policies.param("POL-CONF-003", "contradiction_factor")
    cap = policies.param("POL-CONF-004", "cap")
    floor = policies.param("POL-CONF-004", "floor")
    aged_after_days = policies.param("POL-BEH-002", "age_days")
    aged_weight = policies.param("POL-BEH-002", "aged_weight")

    def age_factor(item: EvidenceInput) -> float:
        return aged_weight if item.age_days > aged_after_days else 1.0

    total = 0.0
    last_contribution: dict[tuple, float] = {}  # identity key → prior contribution
    supporting_patterns: list[str] = []
    steps: list[str] = []

    for item in evidence:
        class_value = contributions[_STRENGTH_KEY[item.strength]]
        if item.relation == "CONTRADICTING":
            delta = -contradiction_factor * class_value * age_factor(item)
            total += delta
            steps.append(f"{item.pattern_id} {item.strength} contradicting {delta:+.4f}")
            continue

        # Identity is the *set* of event kinds, not how many of each (Decision
        # #054). Session-window patterns re-report their whole session on every
        # run, so a multiset identity grew by one event each time and the
        # damping below never engaged — confidence tracked how many times the
        # workflow happened to run, not how much evidence there was.
        identity = (item.pattern_id, item.strength, frozenset(item.event_type_composition))
        if identity in last_contribution:
            delta = last_contribution[identity] * repeat_factor
        else:
            delta = class_value
        # The damping chain records what the *finding* was worth, so age and
        # repetition stay independent (POL-BEH-002 alongside POL-CONF-002): the
        # second reading of a month-old finding is halved once for being said
        # twice and once for being a month old, never quartered by either rule
        # standing in for the other.
        last_contribution[identity] = delta
        delta *= age_factor(item)
        total += delta
        steps.append(f"{item.pattern_id} {item.strength} {delta:+.4f}")

        if item.pattern_id not in supporting_patterns:
            supporting_patterns.append(item.pattern_id)
            if len(supporting_patterns) > 1:
                total += diversity_increment
                steps.append(f"diversity({item.pattern_id}) {diversity_increment:+.4f}")

    confidence = round(min(cap, max(floor, total)), 6)
    explanation = (
        f"Evidence contributions: {'; '.join(steps)}. "
        f"Raw {round(total, 6)}, bounded [{floor}, {cap}] -> {confidence} "
        f"(POL-CONF-001/002/003/004)."
    )
    return ConfidenceResult(confidence=confidence, explanation=explanation)


def should_retire(confidence_history: list[float], policies: PolicyCatalog) -> bool:
    """POL-CONF-005: retire when confidence < threshold for N consecutive updates."""
    threshold = policies.param("POL-CONF-005", "retirement_confidence")
    consecutive = policies.param("POL-CONF-005", "consecutive_updates")
    if len(confidence_history) < consecutive:
        return False
    return all(value < threshold for value in confidence_history[-consecutive:])
