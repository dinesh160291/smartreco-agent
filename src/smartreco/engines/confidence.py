"""Confidence Engine — deterministic evidence → hypothesis confidence (docs/core/05).

Arithmetic is entirely policy-driven:
  POL-BEH-002 evidence older than the policy's window contributes at half weight
  POL-CONF-001 class contributions per supporting action (the flat diversity
               increment was retired in Decision #091 — see the note on noisy-OR)
  POL-CONF-002 diminishing returns, counted per *event* (Decision #091) under the
               Decision #054 identity: pattern + strength + kind of behavior
  POL-CONF-003 contradiction penalty
  POL-CONF-004 saturation cap/floor
  POL-CONF-005 retirement condition

Pure function over an ordered evidence sequence — replayable by construction.

**What is counted, and why it is the event.** Session-window patterns re-report
their whole session on every workflow run, so one finding arrives as a stream of
overlapping snapshots: one observed journey produced fourteen rows for a single
pattern citing 2, 4, 7 … 46 events, each a superset of the last. Chapter 05 damps
repeated *actions* — "viewing the same pricing page twenty times" — so the unit
has to be the action. Counting each event once per bucket makes a run that
observed nothing new worth exactly nothing, rather than merely little.

Decisions #036 and #054 both counted the *row* and differed only on which rows
were identical. That makes the running sum a geometric series whose supremum is
twice the class contribution of each distinct identity — a ceiling fixed by how
many kinds of behavior a shopper happened to produce, unrelated to any threshold
downstream. #036 rejected identity-by-pattern because it "caps a single-pattern
concept near 0.4"; #054 rejected it again for the same reason. Neither removed
the ceiling, and on the DevOps journey it landed on 0.4999… against POL-REQ-001's
0.5, so a subject evidenced by 46 events could never be published. Counting
events removes the ceiling instead of relocating it: confidence now grows with
observed behavior and saturates only at POL-CONF-004's cap.
"""

from dataclasses import dataclass

from smartreco.policies import PolicyCatalog

# Maps the EvidenceStrength enum codes (core 17) to POL-CONF-001 contribution keys.
_STRENGTH_KEY = {"WEAK": "Weak", "MEDIUM": "Medium", "STRONG": "Strong", "VERY_STRONG": "VeryStrong"}


@dataclass(frozen=True)
class EvidenceInput:
    pattern_id: str
    strength: str  # EvidenceStrength code
    supporting_events: tuple[tuple[str, str], ...]  # (event_id, event_type), report order
    relation: str = "SUPPORTING"  # SUPPORTING | CONTRADICTING
    age_days: float = 0.0  # at scoring time; POL-BEH-002


@dataclass(frozen=True)
class ConfidenceResult:
    confidence: float
    explanation: str


def compute_confidence(evidence: list[EvidenceInput], policies: PolicyCatalog) -> ConfidenceResult:
    contributions = policies.param("POL-CONF-001", "contribution")
    repeat_factor = policies.param("POL-CONF-002", "repeat_factor")
    contradiction_factor = policies.param("POL-CONF-003", "contradiction_factor")
    cap = policies.param("POL-CONF-004", "cap")
    floor = policies.param("POL-CONF-004", "floor")
    aged_after_days = policies.param("POL-BEH-002", "age_days")
    aged_weight = policies.param("POL-BEH-002", "aged_weight")

    def age_factor(item: EvidenceInput) -> float:
        return aged_weight if item.age_days > aged_after_days else 1.0

    # A bucket is the Decision #054 identity — pattern, strength, kind of
    # behavior — and holds the events already counted against it. An event
    # re-cited by a later run of the same bucket is the same action restated and
    # adds nothing; one cited at a *higher* strength opens a new bucket and pays
    # full class value, which is how a pattern escalating to Strong (including on
    # the multi-session clause, where no new event need arrive) still registers.
    counted: dict[tuple, list[str]] = {}
    buckets: dict[tuple, float] = {}
    penalty = 0.0
    steps: list[str] = []

    for item in evidence:
        class_value = contributions[_STRENGTH_KEY[item.strength]]
        for event_id, event_type in item.supporting_events:
            bucket = (item.pattern_id, item.strength, event_type, item.relation)
            seen = counted.setdefault(bucket, [])
            if event_id in seen:
                continue
            # The nth action of a kind already counted is worth repeat_factor of
            # the one before it. Damping is indexed by position rather than by
            # the previous *contribution*, so age and repetition stay independent
            # (POL-BEH-002 alongside POL-CONF-002) by construction: a month-old
            # reading is halved once for being old, never compounding into what
            # the next reading of the same kind is worth.
            delta = class_value * (repeat_factor ** len(seen)) * age_factor(item)
            seen.append(event_id)
            if item.relation == "CONTRADICTING":
                penalty += contradiction_factor * delta
            else:
                buckets[bucket] = buckets.get(bucket, 0.0) + delta

    # Buckets combine by noisy-OR, the same combination POL-REQ-003 uses for
    # requirement derivation: independent readings of one concept, none of which
    # can subtract from another, saturating toward certainty rather than summing
    # past it. Summing was what let a single kind of behavior own a fixed share
    # of the scale and cap the concept below the thresholds it feeds.
    #
    # This is also where diversity is paid, which is why POL-CONF-001 no longer
    # carries a flat increment for it (Decision #091). Chapter 05 wants diversity
    # to strengthen confidence because it "demonstrates consistent intent across
    # multiple independent behaviors" — under noisy-OR a second pattern brings
    # its own independent buckets and raises the total by construction. Adding a
    # bonus on top paid for the same diversity twice, and it was enough to lift a
    # concept that merely co-tenants another's Evidence above the concept whose
    # pattern produced it.
    combined = 1.0
    for bucket in sorted(buckets):          # key order: replay must not depend on dict order
        combined *= 1.0 - buckets[bucket]
        steps.append(f"{bucket[0]} {bucket[1]} {bucket[2]} x{len(counted[bucket])} "
                     f"{buckets[bucket]:+.4f}")
    total = (1.0 - combined) - penalty
    if penalty:
        steps.append(f"contradiction {-penalty:+.4f}")

    confidence = round(min(cap, max(floor, total)), 6)
    explanation = (
        f"Evidence contributions: {'; '.join(steps)}. "
        f"Combined {round(1.0 - combined, 6)} by noisy-OR over {len(buckets)} bucket(s), "
        f"raw {round(total, 6)}, bounded [{floor}, {cap}] -> {confidence} "
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
