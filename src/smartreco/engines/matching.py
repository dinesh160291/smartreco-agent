"""Recommendation Engine — capability coverage, ranking, readiness (docs/core/08).

Coverage Calculation Model (Domain 05/09): per-requirement coverage = supported
required capabilities ÷ total required; overall = priority-weighted average with
POL-REC-002 weights. Ranking is by `match_score` — coverage with the off-subject
category term applied — while `overall_coverage` stays the pure capability
arithmetic the scenarios derive (Decision #078); ties break on total capability
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
    product_categories: dict[str, str] | None = None,
    subject_categories: set[str] | None = None,
) -> list[dict]:
    """`subject_categories` empty or omitted means no subject has been declared,
    and there is correspondingly no such thing as an off-subject candidate — the
    category term drops out entirely rather than defaulting to a preference
    nobody expressed (POL-REC-002, Decision #073).
    """
    weight_by_priority = {
        priority: Fraction(value).limit_denominator()
        for priority, value in policies.param("POL-REC-002", "priority_weights").items()
    }
    # Association weights, not one-per-capability. The Requirement→Capability map
    # has always said which capabilities are Primary; ranking used to discard
    # that, so a product holding every Primary capability of a Requirement could
    # score below one holding none of them and more optional extras.
    weight_by_association = {
        association: Fraction(value).limit_denominator()
        for association, value in policies.param("POL-REC-002", "capability_weights").items()
    }
    off_subject = Fraction(policies.param("POL-REC-002", "off_subject_factor")).limit_denominator()
    subject_categories = {c.lower() for c in (subject_categories or set())}
    product_categories = product_categories or {}

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
            associations = req_to_cap[req_id]
            required = set(associations)
            supported = required & caps
            required_weight = sum((weight_by_association[a] for a in associations.values()),
                                  Fraction(0))
            supported_weight = sum((weight_by_association[associations[cap]] for cap in supported),
                                   Fraction(0))
            coverage = supported_weight / required_weight if required_weight else Fraction(0)
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
        # Coverage answers "can this product do the job", never "is this the kind
        # of product I am shopping for". A shopper who has only opened Security
        # products is not shopping for a productivity suite, however much of the
        # requirement that suite covers.
        #
        # So the category term scores the *match*, and leaves coverage alone
        # (Decision #078). It used to multiply `overall_coverage` itself, and
        # that field is not the ranker's private working: it is the meter and
        # the percentage on For-you, it is handed to the Tier-1 narrative beside
        # the list of capabilities the product holds, and it goes out in the
        # digest. A product was published at 29% next to four of the five
        # capabilities the shopper asked for, and its own per-requirement
        # figures averaged 49% — the number disagreed with the facts printed
        # next to it. Being the wrong kind of product is not a capability the
        # product lacks, and coverage is the only thing that reconciles.
        on_subject = True
        if subject_categories:
            category = product_categories.get(product_id, "").lower()
            on_subject = any(subject in category for subject in subject_categories)
        match = overall if on_subject else overall * off_subject
        entry = {
            "product_id": product_id,
            "overall_coverage": round(overall * 100),
            "match_score": round(match * 100),
            "on_subject": on_subject,
            "per_requirement": per_requirement,
            "satisfied_requirements": satisfied,
            "partially_satisfied_requirements": partial,
            "unsupported_requirements": unsupported,
            "missing_capability_ids": sorted(missing),
        }
        scored.append((match, len(caps), product_id, entry))

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
