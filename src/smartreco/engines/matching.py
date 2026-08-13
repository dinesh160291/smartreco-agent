"""Recommendation Engine — capability coverage, ranking, readiness (docs/core/08).

Coverage Calculation Model (Domain 05/09): per-requirement coverage = supported
required capabilities ÷ total required; overall = priority-weighted average with
POL-REC-002 weights. Ranking by overall coverage; ties break on total capability
count, then Product ID (POL-REC-002). Readiness per POL-REC-001. Exact rational
arithmetic (Fraction) so published percentages match the scenario derivations.
"""

from fractions import Fraction

from smartreco.policies import PolicyCatalog


def guaranteed_candidates(
    requirements: list[dict],  # published Requirement Profile entries
    product_capabilities: dict[str, set[str]],
    req_to_cap: dict[str, dict[str, str]],
    existing: list[str],
    limit: int,
) -> list[str]:
    """Products that fully cover a published Requirement and retrieval missed.

    Coverage is a set comparison over the Requirement→Capability map, exact and
    cheap for the whole catalog. Semantic retrieval answers a different and
    harder question — which products *read* like a fit — and a broad product
    loses it: one vector averaged over capabilities from two domains sits
    further from a single-domain query than a narrow product does, however
    completely it covers the requirement. GitHub covered Engineering Delivery
    5/5 and sat outside a Candidate Set of 8 for exactly that reason
    (Decision #060).

    So this does not second-guess retrieval; it supplies the answer retrieval
    was never the right instrument for, and leaves fuzzy fit to it. Only *full*
    coverage qualifies — judging partial fit is retrieval's job.

    Ordered by requirements covered, then total capabilities held, then id —
    the same tie-break POL-REC-002 ranks with, so the guarantee cannot reorder
    what the ranker would have done. Bounded by `limit`: an unbounded top-up
    would swamp the Candidate Set on a requirement many products satisfy.
    """
    published = [entry["req_id"] for entry in requirements if entry["req_id"] in req_to_cap]
    already = set(existing)
    scored: list[tuple[int, int, str]] = []
    for product_id, held in product_capabilities.items():
        if product_id in already:
            continue
        covered = sum(1 for req_id in published if set(req_to_cap[req_id]) <= held)
        if covered:
            scored.append((covered, len(held), product_id))
    scored.sort(key=lambda row: (-row[0], -row[1], row[2]))
    return [product_id for _covered, _breadth, product_id in scored[:limit]]


def rank_products(
    requirements: list[dict],  # published Requirement Profile entries
    candidate_ids: list[str],
    product_capabilities: dict[str, set[str]],
    req_to_cap: dict[str, dict[str, str]],
    policies: PolicyCatalog,
) -> list[dict]:
    weight_by_priority = {
        priority: Fraction(value).limit_denominator()
        for priority, value in policies.param("POL-REC-002", "priority_weights").items()
    }

    scored: list[tuple[Fraction, int, str, dict]] = []
    for product_id in candidate_ids:
        caps = product_capabilities[product_id]
        per_requirement: dict[str, dict] = {}
        weighted_sum = Fraction(0)
        weight_total = Fraction(0)
        satisfied, partial, unsupported = [], [], []
        missing: set[str] = set()

        for entry in requirements:
            req_id = entry["req_id"]
            required = set(req_to_cap[req_id])
            supported = required & caps
            coverage = Fraction(len(supported), len(required))
            weight = weight_by_priority[entry["priority"].capitalize()
                                        if entry["priority"].capitalize() in weight_by_priority
                                        else entry["priority"]]
            weighted_sum += weight * coverage
            weight_total += weight
            missing |= required - supported
            per_requirement[req_id] = {
                "coverage": round(coverage * 100),
                "supported_capability_ids": sorted(supported),
                "missing_capability_ids": sorted(required - supported),
            }
            if coverage == 1:
                satisfied.append(req_id)
            elif coverage > 0:
                partial.append(req_id)
            else:
                unsupported.append(req_id)

        overall = weighted_sum / weight_total if weight_total else Fraction(0)
        entry = {
            "product_id": product_id,
            "overall_coverage": round(overall * 100),
            "per_requirement": per_requirement,
            "satisfied_requirements": satisfied,
            "partially_satisfied_requirements": partial,
            "unsupported_requirements": unsupported,
            "missing_capability_ids": sorted(missing),
        }
        scored.append((overall, len(caps), product_id, entry))

    scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
    entries = []
    for rank, (_, _, _, entry) in enumerate(scored, start=1):
        entry["rank"] = rank
        entries.append(entry)
    return entries


def evaluate_readiness(requirements: list[dict], high_signal_events: int, policies: PolicyCatalog) -> str:
    min_requirements = policies.param("POL-REC-001", "min_requirements")
    min_confidence = policies.param("POL-REC-001", "min_requirement_confidence")
    min_events = policies.param("POL-REC-001", "min_high_signal_events")

    qualifying = [r for r in requirements if r["confidence"] >= min_confidence]
    if len(qualifying) >= min_requirements and high_signal_events >= min_events:
        return "READY"
    return "NOT_READY"
