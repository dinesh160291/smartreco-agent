"""Journey Stage Engine — milestone classification (docs/core/07; Domain 00 §4.1).

Current stage = highest stage whose milestone is satisfied with stage confidence
≥ POL-STAGE-001 threshold, where stage confidence = max confidence among
hypotheses supported by the milestone-satisfying evidence. Pure function.
"""

from smartreco.domain import active as domain
from smartreco.enums import EVIDENCE_STRENGTH
from smartreco.policies import PolicyCatalog


def _strength_at_least(strength: str, minimum: str) -> bool:
    return EVIDENCE_STRENGTH.index(strength) >= EVIDENCE_STRENGTH.index(minimum)


def _milestone_evidence(milestone: dict, evidence: list[dict], event_types: list[str]) -> list[dict] | None:
    """Return the evidence satisfying the milestone, or None if unsatisfied.
    An empty list means satisfied without evidence (event-based milestones)."""
    kind = milestone["kind"]
    if kind == "events_no_evidence":
        return [] if event_types else None
    if kind == "pattern_evidence":
        hits = [e for e in evidence if e["pattern_id"] in milestone["patterns"]]
        return hits or None
    if kind == "pattern_evidence_or_event":
        hits = [e for e in evidence if e["pattern_id"] in milestone["patterns"]]
        if hits:
            return hits
        if any(t in milestone["event_types"] for t in event_types):
            return []
        return None
    if kind == "pattern_evidence_min_strength":
        hits = [e for e in evidence
                if e["pattern_id"] in milestone["patterns"]
                and _strength_at_least(e["strength"], milestone["min_strength"])]
        return hits or None
    if kind == "decision_milestone":
        # Satisfied by a strong signal from one set, or the mere presence of
        # evidence from another. Which patterns fill those sets is the pack's.
        hits = [e for e in evidence
                if (e["pattern_id"] in milestone["strong_patterns"]
                    and _strength_at_least(e["strength"], "STRONG"))
                or e["pattern_id"] in milestone["any_patterns"]]
        return hits or None
    if kind == "adoption_milestone":
        # Pattern evidence *and* corroborating activity of a named event type.
        hits = [e for e in evidence if e["pattern_id"] in milestone["patterns"]]
        if hits and any(t in milestone["event_types"] for t in event_types):
            return hits
        return None
    raise ValueError(f"Unknown milestone kind {kind!r}")


def determine_stage(
    evidence: list[dict],  # [{evidence_id, pattern_id, strength, concept_ids}]
    hypotheses_by_concept: dict[str, float],  # active hypotheses only
    event_types: list[str],
    policies: PolicyCatalog,
) -> tuple[str, float, str]:
    """Returns (stage, stage_confidence, explanation)."""
    min_confidence = policies.param("POL-STAGE-001", "min_stage_confidence")

    for milestone in reversed(domain.STAGE_MILESTONES):  # highest stage first
        hits = _milestone_evidence(milestone, evidence, event_types)
        if hits is None:
            continue
        if not hits:
            # Event-based milestone: no supporting hypotheses required
            return milestone["stage"], 0.0, f"{milestone['stage']}: milestone satisfied by events"
        supporting = [
            hypotheses_by_concept[c]
            for e in hits for c in e["concept_ids"]
            if c in hypotheses_by_concept
        ]
        confidence = max(supporting, default=0.0)
        if confidence >= min_confidence:
            explanation = (
                f"{milestone['stage']}: milestone satisfied by "
                f"{sorted({e['pattern_id'] for e in hits})} evidence; "
                f"stage confidence {confidence} >= {min_confidence} (POL-STAGE-001)"
            )
            return milestone["stage"], confidence, explanation

    return "Awareness", 0.0, "Awareness: no milestone satisfied"


def apply_regression(current_stage: str, recent_high_signal_types: list[str],
                     policies: PolicyCatalog) -> str | None:
    """POL-STAGE-002: regress when the last N consecutive high-signal events are
    all characteristic of stages strictly earlier than the current stage.
    Returns the regressed stage (the highest stage those events characterize),
    or None when no regression applies."""
    needed = policies.param("POL-STAGE-002", "consecutive_earlier_stage_events")
    if len(recent_high_signal_types) < needed:
        return None
    window = recent_high_signal_types[-needed:]
    current_index = domain.JOURNEY_STAGES.index(current_stage)
    characters = []
    for event_type in window:
        stage = domain.EVENT_STAGE_CHARACTER.get(event_type)
        if stage is None or domain.JOURNEY_STAGES.index(stage) >= current_index:
            return None
        characters.append(domain.JOURNEY_STAGES.index(stage))
    return domain.JOURNEY_STAGES[max(characters)]
