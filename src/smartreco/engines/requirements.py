"""Requirement Engine — hypotheses → Requirement Profile (docs/core/06).

POL-REQ-003: each active hypothesis contributes (association weight × confidence)
to its mapped requirements; contributions combine via noisy-OR.
POL-REQ-001: publish at derived confidence ≥ threshold.
POL-REQ-002: priority bands (Critical additionally requires stage ≥ Technical
Validation). Pure function; retired hypotheses are simply absent from the input.
"""

from smartreco.enums import stage_index
from smartreco.policies import PolicyCatalog


def _normalize_stage(stage: str) -> str:
    return stage.replace(" ", "")


def derive_requirements(
    active_hypotheses: dict[str, float],  # {bc_id: confidence} — retired excluded
    bc_to_req: dict[str, dict[str, str]],
    current_stage: str,
    policies: PolicyCatalog,
) -> list[dict]:
    weights = policies.param("POL-REQ-003", "association_weights")
    publish_min = policies.param("POL-REQ-001", "min_confidence")
    critical_min = policies.param("POL-REQ-002", "critical_min_confidence")
    critical_stage = policies.param("POL-REQ-002", "critical_min_stage")
    high_min = policies.param("POL-REQ-002", "high_min_confidence")
    medium_min = policies.param("POL-REQ-002", "medium_min_confidence")

    stage_allows_critical = stage_index(current_stage) >= _critical_stage_index(critical_stage)

    # Collect weighted contributions per requirement
    contributions: dict[str, list[tuple[str, str, float, float]]] = {}
    for bc_id, confidence in active_hypotheses.items():
        for req_id, association in bc_to_req.get(bc_id, {}).items():
            weight = weights[association]
            contributions.setdefault(req_id, []).append((bc_id, association, weight, confidence))

    profile: list[dict] = []
    for req_id, parts in contributions.items():
        survival = 1.0
        for _, _, weight, confidence in parts:
            survival *= 1.0 - weight * confidence
        raw = 1.0 - survival
        if raw < publish_min:
            continue
        if raw >= critical_min and stage_allows_critical:
            priority = "CRITICAL"
        elif raw >= high_min:
            priority = "HIGH"
        elif raw >= medium_min:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        terms = "; ".join(
            f"{bc_id} {association} {weight}x{confidence:.2f}" for bc_id, association, weight, confidence in parts
        )
        profile.append({
            "req_id": req_id,
            "confidence": round(raw, 2),
            "priority": priority,
            "explanation": f"{terms} combined via noisy-OR (POL-REQ-003) = {round(raw, 4)}",
        })

    profile.sort(key=lambda entry: (-entry["confidence"], entry["req_id"]))
    return profile


def _critical_stage_index(policy_stage: str) -> int:
    from smartreco.enums import JOURNEY_STAGES

    normalized = _normalize_stage(policy_stage)
    for i, stage in enumerate(JOURNEY_STAGES):
        if _normalize_stage(stage) == normalized:
            return i
    raise ValueError(f"Unknown stage in POL-REQ-002: {policy_stage!r}")
