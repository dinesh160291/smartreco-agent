"""Signature tests for POL-REQ-004 (subject anchoring) and the two POL-REC-002
ranking corrections that landed with it — Decision #073.

The defect these pin: in all seven domain research areas, the top published
Requirement was one the shopper never expressed. A shopper researching payroll,
dashboards or endpoint security was told they needed Identity Management,
because that Requirement is fed by five Behavioral Concepts while each subject
Requirement is fed by one or two, and noisy-OR rewards feeder count.

Every test here states the shopper's subject and asserts the platform anchors on
it. None of them assert on prose.
"""

import pytest

from smartreco.domain.software_buying import knowledge as K
from smartreco.domain.software_buying.patterns import DOMAIN_RESEARCH_PATTERNS
from smartreco.engines.matching import rank_products
from smartreco.engines.requirements import derive_requirements
from smartreco.policies import load_policies


@pytest.fixture(scope="module")
def policies():
    return load_policies()


# A shopper researching one subject who also opened security and admin pages
# while doing it — the shape of every real session, and of the live trace that
# reported this bug.
def _lensed_session(subject_bc: str) -> dict[str, float]:
    return {subject_bc: 0.65, "BC-001": 0.65, "BC-002": 0.65}


SUBJECTS = [(bc, K.SUBJECT_REQUIREMENT[bc]) for _p, bc, *_r in DOMAIN_RESEARCH_PATTERNS]


@pytest.mark.parametrize("subject_bc,subject_req", SUBJECTS)
def test_declared_subject_is_the_top_requirement(subject_bc, subject_req, policies):
    """POL-REQ-004: the Requirement the shopper's subject is Primary evidence for
    outranks every Requirement derived from how they vetted candidates."""
    profile = derive_requirements(_lensed_session(subject_bc), K.BC_TO_REQ,
                                  "Comparison", policies)
    assert profile, f"{subject_bc}: nothing published"
    assert profile[0]["req_id"] == subject_req, (
        f"{subject_bc}: top requirement was {profile[0]['req_id']} "
        f"({K.REQUIREMENTS[profile[0]['req_id']]}), not the declared subject "
        f"{subject_req} ({K.REQUIREMENTS[subject_req]})")


@pytest.mark.parametrize("subject_bc,subject_req", SUBJECTS)
def test_declared_subject_is_banded_critical(subject_bc, subject_req, policies):
    """POL-REQ-004: the subject anchors ranking, so it is banded Critical whatever
    its derived confidence — a 0.65 subject must not be weighted below a 0.72
    Requirement the shopper never asked for."""
    profile = derive_requirements(_lensed_session(subject_bc), K.BC_TO_REQ,
                                  "Comparison", policies)
    entry = next(e for e in profile if e["req_id"] == subject_req)
    assert entry["priority"] == "CRITICAL"


def test_lens_concepts_still_publish_alone_when_no_subject_is_declared(policies):
    """The demotion is conditional. Scenario 1's shopper really is buying identity:
    Security Evaluation 0.80 with no subject concept active must still publish
    Identity Management at 0.80 Critical (docs/domains/software-buying/09)."""
    profile = derive_requirements({"BC-001": 0.80, "BC-002": 0.70}, K.BC_TO_REQ,
                                  "Technical Validation", policies)
    identity = next(e for e in profile if e["req_id"] == "REQ-002")
    assert identity["confidence"] == 0.80
    assert identity["priority"] == "CRITICAL"


def test_a_subject_below_the_floor_does_not_demote_the_lenses(policies):
    """POL-REQ-004 keys on subject_min_confidence. A flicker of subject evidence
    must not silently rewrite the whole mapping."""
    floor = policies.param("POL-REQ-004", "subject_min_confidence")
    # BC-023 Engineering Delivery maps nowhere near Identity Management, so any
    # movement in REQ-002 can only come from the lens being demoted.
    weak = derive_requirements({"BC-023": floor - 0.1, "BC-001": 0.80}, K.BC_TO_REQ,
                               "Technical Validation", policies)
    identity = next(e for e in weak if e["req_id"] == "REQ-002")
    assert identity["confidence"] == 0.80, "lens demoted by a sub-threshold subject"


def test_lens_demotion_lowers_what_the_lenses_derive(policies):
    """POL-REQ-004's demotion arm, pinned by value rather than by ordering.

    The live trace that reported this bug: a purely cyber-security session in
    which Identity Management was still derived at 0.72 — higher than the
    Security Operations the shopper was actually researching — because Security
    Evaluation fed it at Primary and four other concepts fed it besides. With the
    subject held, Security Evaluation contributes at Secondary and Security
    Operations at Supporting, giving 1-(1-0.6*0.65)(1-0.3*0.65) = 0.51.

    Anchoring alone would reorder the profile while leaving these numbers intact,
    so this is the assertion that fails if only the sort survives.
    """
    anchored = derive_requirements({"BC-025": 0.65, "BC-001": 0.65, "BC-002": 0.65},
                                   K.BC_TO_REQ, "Comparison", policies)
    reqs = {e["req_id"]: e for e in anchored}
    assert reqs["REQ-002"]["confidence"] == 0.51
    assert reqs["REQ-004"]["confidence"] == 0.60
    assert reqs["REQ-012"]["confidence"] == 0.65

    # The same three concepts with the subject withdrawn: no demotion applies and
    # Identity Management returns to out-deriving the rest.
    undeclared = derive_requirements({"BC-001": 0.65, "BC-002": 0.65}, K.BC_TO_REQ,
                                     "Comparison", policies)
    assert next(e for e in undeclared if e["req_id"] == "REQ-002")["confidence"] == 0.65


def test_the_anchor_leads_even_when_a_lens_derives_higher(policies):
    """POL-REQ-004's ordering arm. Demotion narrows the gap but does not always
    close it: a modestly-held People Operations subject (0.50) alongside heavy
    security and compliance vetting still derives below Regulatory Compliance
    (0.66). The subject leads the profile regardless — it is the reason the
    shopper is here, not the best-evidenced guess about them.

    Without this, ordering falls back to confidence and the demotion alone
    decides, which is exactly how the profile read before Decision #073.
    """
    profile = derive_requirements({"BC-020": 0.50, "BC-001": 0.80, "BC-004": 0.80},
                                  K.BC_TO_REQ, "Comparison", policies)
    assert profile[0]["req_id"] == "REQ-007"
    assert profile[0]["confidence"] == 0.50
    assert next(e for e in profile if e["req_id"] == "REQ-004")["confidence"] == 0.66


def test_only_the_leading_subject_anchors(policies):
    """POL-REQ-004: two subjects can be held at once — a CRM buyer often also
    wants marketing reach. The weaker one bands by its own confidence, or the
    difference between why the shopper is here and what else caught their eye is
    erased (this is doc 09 Scenario 5's derivation, named)."""
    profile = derive_requirements({"BC-019": 0.80, "BC-022": 0.50}, K.BC_TO_REQ,
                                  "Technical Validation", policies)
    reqs = {e["req_id"]: e for e in profile}
    assert reqs["REQ-006"]["priority"] == "CRITICAL"     # BC-019, leading
    assert reqs["REQ-009"]["priority"] == "HIGH"         # BC-022, weaker
    assert profile[0]["req_id"] == "REQ-006"


def test_equally_held_subjects_both_anchor(policies):
    """Ties all anchor: equally held is equally the reason they are here."""
    profile = derive_requirements({"BC-019": 0.70, "BC-020": 0.70}, K.BC_TO_REQ,
                                  "Technical Validation", policies)
    reqs = {e["req_id"]: e for e in profile}
    assert reqs["REQ-006"]["priority"] == "CRITICAL"
    assert reqs["REQ-007"]["priority"] == "CRITICAL"


# ---- POL-REC-002: coverage honours the Primary/Secondary/Supporting weights ----

REQS_CRITICAL_SECOPS = [{"req_id": "REQ-012", "priority": "CRITICAL", "confidence": 0.65}]


def test_both_primary_capabilities_beat_more_optional_ones(policies):
    """Security Operations lists Threat Protection and Data Loss Prevention as
    Primary, Compliance Reporting Secondary, Identity Federation Supporting.
    Flat counting scored a product holding both Primary capabilities (2/4 = 50%)
    below one holding one Primary plus two optional (3/4 = 75%)."""
    caps = {
        "PROD-BOTH-PRIMARY": {"CAP-025", "CAP-026"},
        "PROD-OPTIONAL-HEAVY": {"CAP-026", "CAP-027", "CAP-008"},
    }
    entries = rank_products(REQS_CRITICAL_SECOPS, sorted(caps), caps, K.REQ_TO_CAP, policies)
    by_id = {e["product_id"]: e for e in entries}
    assert by_id["PROD-BOTH-PRIMARY"]["overall_coverage"] > by_id["PROD-OPTIONAL-HEAVY"]["overall_coverage"]
    assert by_id["PROD-BOTH-PRIMARY"]["rank"] == 1


def test_full_coverage_is_still_exactly_100(policies):
    """The weighting changes partial scores, never a complete one."""
    caps = {"PROD-ALL": set(K.REQ_TO_CAP["REQ-012"])}
    entry = rank_products(REQS_CRITICAL_SECOPS, ["PROD-ALL"], caps, K.REQ_TO_CAP, policies)[0]
    assert entry["overall_coverage"] == 100
    assert entry["satisfied_requirements"] == ["REQ-012"]


# ---- POL-REC-002: category affinity ----

def test_an_off_subject_product_is_discounted(policies):
    """Coverage says a product *can* do the job. A shopper who has only opened
    Security products is not shopping for a productivity suite, however much of
    the requirement that suite happens to cover.

    The discount lands on `match_score` since Decision #078; it used to be
    applied to `overall_coverage`. Same factor, same ordering — a different
    field, because coverage has an arithmetic definition it has to keep.
    """
    caps = {"PROD-SUITE": set(K.REQ_TO_CAP["REQ-012"]), "PROD-SEC": set(K.REQ_TO_CAP["REQ-012"])}
    cats = {"PROD-SUITE": "Productivity & Collaboration", "PROD-SEC": "Security"}
    entries = rank_products(REQS_CRITICAL_SECOPS, sorted(caps), caps, K.REQ_TO_CAP, policies,
                            product_categories=cats, subject_categories={"security"})
    by_id = {e["product_id"]: e for e in entries}
    assert by_id["PROD-SEC"]["rank"] == 1
    factor = policies.param("POL-REC-002", "off_subject_factor")
    assert by_id["PROD-SUITE"]["match_score"] == round(100 * factor)


def test_off_subject_discounts_the_match_score_and_leaves_coverage_alone(policies):
    """Coverage is capability arithmetic; being the wrong kind of product is not
    a capability the product lacks (Decision #078).

    The factor used to multiply `overall_coverage` itself, and that number is
    not private to the ranker: it is the meter and percentage on For-you, it is
    handed to the Tier-1 narrative beside the list of capabilities the product
    *does* hold, and it goes out in the digest. Notion was published at 29%
    alongside four of the five AI capabilities the shopper asked for — a figure
    that contradicted the facts printed next to it, in the one place Law 11 says
    the narrative may use nothing but Runtime Object facts.
    """
    caps = {"PROD-SUITE": set(K.REQ_TO_CAP["REQ-012"]), "PROD-SEC": set(K.REQ_TO_CAP["REQ-012"])}
    cats = {"PROD-SUITE": "Productivity & Collaboration", "PROD-SEC": "Security"}
    entries = rank_products(REQS_CRITICAL_SECOPS, sorted(caps), caps, K.REQ_TO_CAP, policies,
                            product_categories=cats, subject_categories={"security"})
    by_id = {e["product_id"]: e for e in entries}

    # The off-subject suite covers the requirement completely, and says so —
    # in the figure, in the parts, and in the satisfied list, all three of which
    # the narrative and the Reasoning Panel read.
    assert by_id["PROD-SUITE"]["overall_coverage"] == 100
    assert by_id["PROD-SUITE"]["per_requirement"]["REQ-012"]["coverage"] == 100
    assert by_id["PROD-SUITE"]["satisfied_requirements"] == ["REQ-012"]
    assert by_id["PROD-SUITE"]["on_subject"] is False
    assert by_id["PROD-SEC"]["on_subject"] is True


def test_published_coverage_reconciles_with_its_own_parts(policies):
    """Doc 09 defines Overall Coverage as the priority-weighted average of the
    per-Requirement coverages. Anyone — a shopper, an admin in the Reasoning
    Panel, a test — can do that arithmetic from the entry itself, and it must
    come out to the published figure whether or not the product is on subject.
    """
    requirements = [{"req_id": "REQ-001", "priority": "CRITICAL", "confidence": 0.83},
                    {"req_id": "REQ-005", "priority": "HIGH", "confidence": 0.75}]
    caps = {p["product_id"]: set(p["capabilities"]) for p in K.CANONICAL_PRODUCTS}
    cats = {p["product_id"]: p["category"] for p in K.CANONICAL_PRODUCTS}
    entries = rank_products(requirements, ["PROD-004", "PROD-009", "PROD-005"], caps,
                            K.REQ_TO_CAP, policies, product_categories=cats,
                            subject_categories={"collaboration"})
    weights = policies.param("POL-REC-002", "priority_weights")
    for entry in entries:
        recomputed = sum(
            weights[r["priority"].capitalize()] * entry["per_requirement"][r["req_id"]]["coverage"]
            for r in requirements) / sum(weights[r["priority"].capitalize()] for r in requirements)
        # One point of slack, and one only: the engine averages exact fractions
        # and rounds once, while this recomputes from the parts as stored, which
        # are already rounded. Nothing else may separate the two — the defect
        # this pins put Notion 20 points below its own figures.
        assert abs(entry["overall_coverage"] - recomputed) <= 1, (
            f"{entry['product_id']} publishes {entry['overall_coverage']}% but its own "
            f"per-requirement figures average {recomputed:.1f}%")


def test_no_declared_subject_means_no_category_discount(policies):
    """With no subject declared there is no such thing as off-subject, and
    ranking must be exactly what it was before category affinity existed."""
    caps = {"PROD-SUITE": set(K.REQ_TO_CAP["REQ-012"])}
    cats = {"PROD-SUITE": "Productivity & Collaboration"}
    entries = rank_products(REQS_CRITICAL_SECOPS, ["PROD-SUITE"], caps, K.REQ_TO_CAP, policies,
                            product_categories=cats, subject_categories=set())
    assert entries[0]["overall_coverage"] == 100


def test_subject_categories_are_declared_by_the_pack_not_the_platform():
    """Domain boundary: which categories a subject is shopped in is pack
    knowledge, and must agree with the categories its pattern activates on."""
    for _p, bc, _t, categories, _s in DOMAIN_RESEARCH_PATTERNS:
        assert K.SUBJECT_CATEGORIES[bc] == frozenset(categories)
