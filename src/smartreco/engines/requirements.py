"""Requirement Engine — hypotheses → Requirement Profile (docs/core/06).

POL-REQ-003: each active hypothesis contributes (association weight × confidence)
to its mapped requirements; contributions combine via noisy-OR.
POL-REQ-004: once the shopper has declared a subject, evaluation-lens concepts
are demoted one association band and the subject's own requirement is banded
Critical.
POL-REQ-001: publish at derived confidence ≥ threshold.
POL-REQ-002: priority bands (Critical additionally requires stage ≥ Technical
Validation). Pure function; retired hypotheses are simply absent from the input.
"""

from smartreco.domain import active as domain
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

    stage_allows_critical = domain.stage_index(current_stage) >= _critical_stage_index(critical_stage)

    subject_min = policies.param("POL-REQ-004", "subject_min_confidence")
    demotion = policies.param("POL-REQ-004", "lens_demotion")
    subject_priority = policies.param("POL-REQ-004", "subject_priority")

    # POL-REQ-004. A held subject says what the shopper is shopping for; the
    # evaluation lenses say how they are vetting it. While both feed requirements
    # at full strength the lenses win on feeder count alone — they are mapped
    # into the requirements many concepts share, and noisy-OR rewards that.
    subjects = {bc: confidence for bc, confidence in active_hypotheses.items()
                if bc in domain.SUBJECT_REQUIREMENT and confidence >= subject_min}
    # Only the *leading* subject anchors. A shopper can hold two subjects at
    # once — a CRM buyer often also wants marketing reach — and banding a
    # just-past-the-floor second interest Critical alongside a 0.80 primary one
    # erases the difference between why they are here and what else caught their
    # eye (doc 09 Scenario 5). Ties all anchor: equally held is equally the reason.
    leading = max(subjects.values(), default=0.0)
    anchored = {domain.SUBJECT_REQUIREMENT[bc]
                for bc, confidence in subjects.items() if confidence == leading}

    # Collect weighted contributions per requirement
    contributions: dict[str, list[tuple[str, str, float, float]]] = {}
    for bc_id, confidence in active_hypotheses.items():
        for req_id, association in bc_to_req.get(bc_id, {}).items():
            # Demote a lens only where it feeds a requirement *other* than the
            # anchor. The rule exists to stop lenses manufacturing a competing
            # subject; weakening their contribution to the declared subject is
            # self-defeating. Integration Evaluation feeds Workflow Automation at
            # Primary, so an automation shopper who checks integrations is
            # evidencing the thing they are shopping for, not a rival need
            # (doc 09 Scenario 3, Decision #077).
            if (subjects and bc_id in domain.EVALUATION_LENS_CONCEPTS
                    and req_id not in anchored):
                association = demotion[association]
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
        if req_id in anchored:
            # The shopper told us why they are here. That is not a confidence
            # estimate to be out-banded by a requirement they never expressed.
            priority = subject_priority
        elif raw >= critical_min and stage_allows_critical:
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

    # Anchors lead (POL-REQ-004); the rest by confidence, then id, as before.
    profile.sort(key=lambda entry: (entry["req_id"] not in anchored,
                                    -entry["confidence"], entry["req_id"]))
    return profile


def _critical_stage_index(policy_stage: str) -> int:

    normalized = _normalize_stage(policy_stage)
    for i, stage in enumerate(domain.JOURNEY_STAGES):
        if _normalize_stage(stage) == normalized:
            return i
    raise ValueError(f"Unknown stage in POL-REQ-002: {policy_stage!r}")
