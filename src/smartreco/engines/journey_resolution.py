"""Journey Resolution Engine — signal computation + decision (docs/core/12).

Pure set/distribution arithmetic over event metadata; no AI, no embeddings
(Tier 2 is fenced to the Semantic Retrieval Engine, Decision #031). Thresholds
and weights come from POL-JRES-001; the engine hardcodes none.
"""

import math
from dataclasses import dataclass

from smartreco.policies import PolicyCatalog


@dataclass(frozen=True)
class ResolutionDecision:
    action: str  # CONTINUE | REACTIVATE | CREATE
    journey_id: str | None
    score: float
    explanation: str


def topic_similarity(session_entities: set[str], journey_entities: set[str]) -> float:
    """Jaccard overlap of entity sets (product IDs, categories, doc topics,
    normalized search tokens)."""
    union = session_entities | journey_entities
    if not union:
        return 0.0
    return len(session_entities & journey_entities) / len(union)


def behavioral_similarity(session_histogram: dict[str, int], journey_histogram: dict[str, int]) -> float:
    """Cosine similarity between event-type count histograms."""
    keys = set(session_histogram) | set(journey_histogram)
    dot = sum(session_histogram.get(k, 0) * journey_histogram.get(k, 0) for k in keys)
    norm_s = math.sqrt(sum(v * v for v in session_histogram.values()))
    norm_j = math.sqrt(sum(v * v for v in journey_histogram.values()))
    if norm_s == 0 or norm_j == 0:
        return 0.0
    return dot / (norm_s * norm_j)


def time_decay(days_inactive: float, half_life_days: float) -> float:
    return max(0.0, 0.5 ** (days_inactive / half_life_days))


def subject_abandoned(established: str | None, recent_subjects: set[str]) -> bool:
    """Has the shopper stopped doing what this journey was about? (core 12)

    True when the journey has an established subject, recent activity names a
    subject, and the established one is not among them. The two are sampled
    from **disjoint** slices — `established` is the dominant subject of
    everything *before* a trailing window, `recent_subjects` is what appears
    *in* it. Both are supplied by the caller, so the engine knows no concept
    ids. Overlapping the samples defeats the rule: a new subject pursued long
    enough becomes the dominant one, and then there is nothing left to
    abandon.

    **Why abandonment rather than divergence.** The first rule compared a block
    of new events against everything the journey had ever contained and forked
    when they shared nothing. It could not survive contact with real behavior:
    a switch of subject always passes through a transitional block where the
    shopper is doing both, that block overlaps and merges, and from then on the
    journey's history contains both subjects so nothing can ever diverge from it
    again. It fired only when a workflow run happened to land exactly on the
    pivot — luck, not a rule (Decision #057).

    Abandonment reads the other way round and survives the transition: the
    mixed block continues, and the fork happens on the first block after the
    shopper has genuinely stopped. Two consequences are deliberate — a shopper
    who keeps returning to the original subject never forks however much they
    widen, and evidence naming no subject at all never forks, because progress
    signals like pricing and comparisons say nothing about what is being bought.
    """
    return established is not None and bool(recent_subjects) and established not in recent_subjects


def resolution_score(topic: float, behavioral: float, decay: float, policies: PolicyCatalog) -> float:
    weights = policies.param("POL-JRES-001", "signal_weights")
    return weights["topic"] * topic + weights["behavioral"] * behavioral + weights["time_decay"] * decay


def resolve(
    session_entities: set[str],
    session_histogram: dict[str, int],
    candidates: list[dict],  # [{journey_id, lifecycle, entities, histogram, days_inactive}]
    policies: PolicyCatalog,
) -> ResolutionDecision:
    reuse_min = policies.param("POL-JRES-001", "reuse_active_min_score")
    reactivate_min = policies.param("POL-JRES-001", "reactivate_dormant_min_score")
    half_life = policies.param("POL-JRES-001", "time_decay_half_life_days")

    # Lifecycle gates candidacy: CLOSED and ARCHIVED are never candidates (core 12)
    eligible = [c for c in candidates if c["lifecycle"] in ("NEW", "ACTIVE", "DORMANT")]

    best: tuple[float, dict] | None = None
    for candidate in eligible:
        score = resolution_score(
            topic_similarity(session_entities, candidate["entities"]),
            behavioral_similarity(session_histogram, candidate["histogram"]),
            time_decay(candidate["days_inactive"], half_life),
            policies,
        )
        if best is None or score > best[0]:
            best = (score, candidate)

    if best is None:
        return ResolutionDecision("CREATE", None, 0.0,
                                  "No candidate journeys (cold start) -> create (core 12)")

    score, candidate = best
    threshold = reactivate_min if candidate["lifecycle"] == "DORMANT" else reuse_min
    if score >= threshold:
        action = "REACTIVATE" if candidate["lifecycle"] == "DORMANT" else "CONTINUE"
        return ResolutionDecision(action, candidate["journey_id"], round(score, 4),
                                  f"{action} {candidate['journey_id']}: score {round(score, 4)} >= "
                                  f"{threshold} (POL-JRES-001)")
    return ResolutionDecision("CREATE", None, round(score, 4),
                              f"Best candidate {candidate['journey_id']} score {round(score, 4)} < "
                              f"{threshold} -> create (POL-JRES-001)")
