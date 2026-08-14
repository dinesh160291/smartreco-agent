"""Signature test: committed demo seed integrity (data-model §Catalog Seed
Strategy). The demo catalog is data the live demo's determinism depends on:
the distractor constraint must hold so canonical winners stay canonical."""

import json
from pathlib import Path

import pytest

from smartreco.domain.software_buying import CANONICAL_PRODUCTS, REQ_TO_CAP
from smartreco.policies import load_policies

SEED = Path(__file__).resolve().parents[1] / "seed" / "products.json"


@pytest.fixture(scope="module")
def seed():
    return json.loads(SEED.read_text(encoding="utf-8"))


def test_scale_and_split(seed):
    products = seed["products"]
    real = [p for p in products if not p["fictional"]]
    fictional = [p for p in products if p["fictional"]]
    assert len(products) + len(CANONICAL_PRODUCTS) == 250
    assert len(real) + len(CANONICAL_PRODUCTS) == 125
    assert len(fictional) == 125


def test_editorial_disclaimer_present(seed):
    assert "editorial" in seed["disclaimer"].lower()
    assert "not vendor claims" in seed["disclaimer"]


def test_ids_unique_and_clear_of_canonical(seed):
    ids = [p["product_id"] for p in seed["products"]]
    assert len(ids) == len(set(ids))
    canonical = {p["product_id"] for p in CANONICAL_PRODUCTS}
    assert not canonical & set(ids)


SCENARIO_REQUIREMENTS = ("REQ-001", "REQ-002", "REQ-003", "REQ-004", "REQ-005")


def test_distractor_constraint_holds_for_scenario_requirements(seed):
    """No non-canonical product may fully cover a *scenario* requirement's
    capability set — canonical winners must remain deterministic.

    Scoped to REQ-001…005 (doc 14). Those are the requirements the demo script's
    journeys produce and the ones doc 09's derivations assert, so a distractor
    reaching 100% on them would displace the canonical winner the story names.

    The v1.2 requirements have no canonical product to protect: the canonical
    ten hold no CRM, HR, finance, marketing, DevOps or analytics capability at
    all. Forbidding full coverage there would forbid the marketplace from having
    a best-fit product for those needs, which is the whole point of adding them.
    What must hold instead is that they still discriminate — see below.
    """
    for product in seed["products"]:
        caps = set(product["capabilities"])
        for req_id in SCENARIO_REQUIREMENTS:
            assert not set(REQ_TO_CAP[req_id]) <= caps, (
                f"{product['product_id']} fully covers {req_id} — distractor "
                "constraint violated")


def test_every_requirement_discriminates(seed):
    """No requirement may be fully covered by more products than a Candidate Set
    can hold (POL-RETR-001 top_k).

    Retrieval returns at most top_k candidates. If more products tie at maximum
    coverage than that, the recommendation list can be composed entirely of
    tied products and the ranking expresses no preference — "correct and
    useless", the same failure test_fictional_products_in_a_category_are_not_clones
    exists to prevent, arriving through the requirement instead of the data.

    This caught a real design error: REQ-011 Data & Insight was first drafted
    from the three Data & Analytics capabilities alone, and 21 catalog products
    hold all three.
    """
    # `>=`, not `>`: if *exactly* top_k products cover a requirement fully, the
    # Candidate Set can still be composed entirely of them, which is the failure
    # this test exists to prevent. Corrected when the Splunk repair pushed
    # REQ-010 to exactly 8 and the guard stayed quiet (Decision #058).
    top_k = load_policies().param("POL-RETR-001", "top_k")
    saturating: dict[str, int] = {}
    for req_id, required in REQ_TO_CAP.items():
        full = sum(1 for p in seed["products"]
                   if set(required) <= set(p["capabilities"]))
        if full >= top_k:
            saturating[req_id] = full
    assert not saturating, (
        f"requirements saturated beyond a Candidate Set ({top_k}): {saturating} — "
        "the top coverage band is a tie the ranking cannot break")


WORK_MANAGEMENT_CAPS = {"CAP-056", "CAP-057", "CAP-058"}


def test_work_management_products_describe_their_own_work(seed):
    """A task tool's documentation must be able to say it is about tasks.

    Work Management was a product category with no capabilities of its own, so
    each of these products described its docs with whatever generic capability it
    happened to carry — Asana's read as `messaging`. BP-006's
    productivity/templates/tasks vocabulary was therefore unreachable from any
    page in the catalog (Decision #053).
    """
    from smartreco.domain.software_buying import patterns

    def doc_topic(caps):
        for cap_id, topic in patterns.UI_DOC_TOPICS:
            if cap_id in caps:
                return topic
        return patterns.UI_DOC_TOPIC_DEFAULT

    work = [p for p in seed["products"] if p["category"] == "Work Management"]
    assert work, "no Work Management products in the seed"
    for product in work:
        caps = set(product["capabilities"])
        assert caps & WORK_MANAGEMENT_CAPS, (
            f"{product['name']} manages work and holds no work-management capability")
        assert doc_topic(caps) in patterns.BP006_DOC_TOPICS, (
            f"{product['name']} documents itself as {doc_topic(caps)!r}, which "
            "Productivity Evaluation does not read")


def test_fictional_products_in_a_category_are_not_clones(seed):
    """Distractors must differ from each other, not just from the canonical 10.
    The generator drew from a small per-domain pool, so all 11 fictional
    identity products came out with the identical capability set and every
    recommendation list involving them was a flat tie — the ranking was
    correct and useless. Identical profiles cannot be separated by any
    scoring rule, so the fix has to live in the data."""
    by_category: dict[str, list[tuple[str, tuple]]] = {}
    for product in seed["products"]:
        if not product["fictional"]:
            continue
        by_category.setdefault(product["category"], []).append(
            (product["product_id"], tuple(sorted(product["capabilities"]))))

    offenders = {}
    for category, entries in by_category.items():
        if len(entries) < 3:
            continue  # too few to say anything about variety
        distinct = {caps for _pid, caps in entries}
        if len(distinct) < max(2, len(entries) // 2):
            offenders[category] = f"{len(entries)} products, {len(distinct)} profile(s)"
    assert not offenders, f"fictional products are clones: {offenders}"


def test_scenario_requirement_coverage_varies_among_distractors(seed):
    """Depth against REQ-002 must vary, not just the raw capability sets:
    products can hold different capabilities and still tie on the requirement
    that actually drives ranking."""
    required = set(REQ_TO_CAP["REQ-002"])
    depths = [len(set(p["capabilities"]) & required)
              for p in seed["products"]
              if p["fictional"] and p["category"] == "Identity & Access Management"]
    assert len(set(depths)) >= 3, (
        f"identity distractors all score alike against REQ-002: {sorted(depths)}")


def test_narratives_are_clean(seed):
    for product in seed["products"]:
        narrative = product["business_value_narrative"]
        assert narrative and len(narrative) < 300
        for banned in ("CAP-", "REQ-", "PROD-"):
            assert banned not in narrative


def test_every_requirement_is_coverable(seed):
    """The other half of discrimination: a requirement no product can satisfy
    is as useless as one every product satisfies (Decision #061).

    REQ-011 spent a version at five capabilities, two of them borrowed from
    other domains to break a 21-way tie. Nothing in 250 products reached 5/5,
    so the honest winner was capped at 80% and any satisfiable requirement
    outranked it — an analytics shopper was shown a DevOps monitoring tool
    first. The tie it was solving had a different cause: the catalog assigned
    the Data & Analytics domain as a block.
    """
    products = seed["products"] + list(CANONICAL_PRODUCTS)
    uncoverable = {}
    for req_id, required in REQ_TO_CAP.items():
        need = set(required)
        best = max(len(need & set(p["capabilities"])) for p in products)
        if best < len(need):
            uncoverable[req_id] = f"best {best}/{len(need)}"
    assert not uncoverable, (
        f"no product can fully cover these requirements: {uncoverable} — "
        "their true winner is capped below 100% and loses to any satisfiable one")


# A requirement may draw on another capability domain when the *need* genuinely
# spans domains — "Secure Collaboration" is collaboration and security, and
# identity governance really does rest on audit logging. It may never do so to
# make a test pass.
#
# REQ-011 did exactly that: a 21-way tie failed the discrimination guard, so two
# capabilities were borrowed from Automation and Artificial Intelligence to
# break it. That made the requirement unsatisfiable (Decision #061) *and*
# corrupted retrieval, because capability narratives go into the Behavioral
# Query Document verbatim — an automation sentence inside an analytics query
# pulls the vector toward automation products.
#
# A ratchet, not an excuse: entries may be removed, never added. A new one means
# arguing that the need itself spans domains.
CROSS_DOMAIN_REQUIREMENTS = {
    "REQ-001": "Secure Collaboration is collaboration plus the security that makes it safe",
    "REQ-002": "identity governance rests on audit logging",
    "REQ-005": "AI Assistance includes automating what the AI drafts",
    # REQ-012 removed by the ratchet's own rule (Decision #074). It borrowed
    # Compliance Reporting and Identity Federation only because the pack had no
    # security-operations vocabulary of its own; the identity capability was also
    # how identity products out-covered endpoint-security ones on the security
    # requirement. All six of its capabilities are now Security capabilities.
}


def test_no_requirement_quietly_borrows_another_domain():
    from collections import Counter

    from smartreco.domain.software_buying import CAPABILITIES

    domain_of = {cap_id: domain for cap_id, _name, domain, _n in CAPABILITIES}
    borrowers = {}
    for req_id, caps in REQ_TO_CAP.items():
        home, _ = Counter(domain_of[c] for c in caps).most_common(1)[0]
        foreign = sorted({domain_of[c] for c in caps if domain_of[c] != home})
        if foreign and req_id not in CROSS_DOMAIN_REQUIREMENTS:
            borrowers[req_id] = foreign
    assert not borrowers, (
        f"these requirements draw on another capability domain without a stated "
        f"reason: {borrowers}. Borrowing corrupts coverage and retrieval alike — "
        "if the need genuinely spans domains, say so in CROSS_DOMAIN_REQUIREMENTS")


def test_no_stale_cross_domain_entries():
    """An entry that stops borrowing must be deleted, so the list only shrinks."""
    from collections import Counter

    from smartreco.domain.software_buying import CAPABILITIES

    domain_of = {cap_id: domain for cap_id, _name, domain, _n in CAPABILITIES}
    stale = []
    for req_id in CROSS_DOMAIN_REQUIREMENTS:
        caps = REQ_TO_CAP.get(req_id, {})
        if not caps:
            continue
        home, _ = Counter(domain_of[c] for c in caps).most_common(1)[0]
        if not any(domain_of[c] != home for c in caps):
            stale.append(req_id)
    assert not stale, f"these no longer borrow — remove them from the list: {stale}"


# --- Prose must not claim capabilities the product does not hold (#068) ------

def _named_capabilities(text: str) -> list[str]:
    """Capability display names appearing in a product's prose."""
    from smartreco.domain.software_buying import CAPABILITIES

    low = text.lower()
    return sorted({name for _cid, name, _dom, _narr in CAPABILITIES if name.lower() in low})


def test_no_product_prose_claims_a_capability_it_does_not_hold(seed):
    """The GitHub defect from Decision #060, generalised.

    Every seeded product's description is generated from its capability list,
    and that text *is* the embedded document — so prose naming a capability the
    product lacks does not merely mislead a reader, it drags the product's
    vector toward a neighbourhood it does not belong to. Decision #064 caught
    this for the fictional catalog; the real products edited by #058 and
    #061–#063 kept their pre-edit prose.
    """
    from smartreco.domain.software_buying import CAPABILITIES

    display = {cid: name for cid, name, _dom, _narr in CAPABILITIES}
    offenders = []
    for product in seed["products"]:
        held = {display[c].lower() for c in product["capabilities"]}
        prose = " ".join(filter(None, (
            product.get("description"),
            product.get("business_purpose"),
            product.get("business_value_narrative"))))
        # Two categories share a name with a capability ("Workflow Automation",
        # "Compliance"), and every product's prose states its own category. A
        # naive scan reads that as a claim, which would fail exactly the
        # products the distractor constraint deliberately keeps *off* that
        # capability (Decision #058).
        prose = prose.lower().replace(product["category"].lower(), " ")
        phantom = [n for n in _named_capabilities(prose) if n.lower() not in held]
        if phantom:
            offenders.append(f"{product['name']}: claims {', '.join(phantom)}")
    assert offenders == [], (
        f"{len(offenders)} product(s) describe capabilities they do not have:\n  "
        + "\n  ".join(offenders[:15]))
