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


# Every Capability must reach some Requirement, or a product holding it can be
# searched and viewed but never recommended. A ratchet like
# CROSS_DOMAIN_REQUIREMENTS above: entries may be removed, never added.
#
# It exists because Decision #074 removed Identity Federation and Compliance
# Reporting from Security Operations and rehomed neither — doc 07 had said in as
# many words that Security Operations was housing them "which are otherwise
# stranded", and nothing failed when that stopped being true (Decision #075).
UNMAPPED_CAPABILITIES = {
    "CAP-009": "File Sharing — belongs to an existing requirement's domain (doc 07)",
    "CAP-024": "AI Workflow Assistance — same",
}


def test_every_capability_reaches_a_requirement():
    from smartreco.domain.software_buying import CAPABILITIES, REQ_TO_CAP

    mapped = {cap for caps in REQ_TO_CAP.values() for cap in caps}
    orphans = {cap_id for cap_id, *_rest in CAPABILITIES} - mapped - set(UNMAPPED_CAPABILITIES)
    assert not orphans, (
        "these capabilities reach no requirement, so a product holding them can "
        f"never be recommended: {sorted(orphans)}")


def test_the_unmapped_allowlist_does_not_list_mapped_capabilities():
    """The ratchet only ratchets if stale entries are removed as they are fixed."""
    from smartreco.domain.software_buying import REQ_TO_CAP

    mapped = {cap for caps in REQ_TO_CAP.values() for cap in caps}
    stale = sorted(set(UNMAPPED_CAPABILITIES) & mapped)
    assert not stale, f"now mapped — remove from UNMAPPED_CAPABILITIES: {stale}"


# --- Decision #080: the Productivity shelf ---------------------------------

def test_productivity_is_gone_from_the_catalog(seed):
    """It was never a subject anybody shopped for. Sixteen of its seventeen
    products held Workload Management because the generator stamped it on them,
    and stripping that left automation, collaboration, marketing and AI products
    with nothing in common — so the category was dissolved rather than mapped.
    """
    survivors = [p["name"] for p in seed["products"] + list(CANONICAL_PRODUCTS)
                 if p["category"] == "Productivity"]
    assert not survivors, f"Productivity is back on {survivors}"


def test_workload_management_sits_only_where_it_is_meant(seed):
    """The stamp is the reason the shelf looked coherent. A product claiming to
    manage capacity while doing nothing of the kind is not cosmetic: it covers
    REQ-013 at Secondary, so Grammarly Business ranked for a work-management
    shopper.
    """
    holders = {p["name"]: p["category"]
               for p in seed["products"] + list(CANONICAL_PRODUCTS)
               if "CAP-058" in p["capabilities"]}
    # Calendly earns it on its own terms — managing when people are available is
    # what the capability describes — and is filed under Work Management.
    stray = {n: c for n, c in holders.items() if c not in ("Work Management",)}
    assert not stray, f"Workload Management claimed outside Work Management: {stray}"
    assert len(holders) >= 5, f"only {len(holders)} products manage capacity"


# --- Decision #083: category is a closed enum, and every one needs a subject ---

# Categories that exist and have no subject concept. A ratchet: entries may be
# removed as subjects are built, never added. An entry here means every product
# in that category is off-subject for every shopper — POL-REC-002 multiplies it
# by off_subject_factor no matter what they are researching.
# Empty since Decision #088, and the sweep is what emptied it: 110 products sat
# in a subject-less category when this began. The last entry was "AI", removed
# by dissolving the category rather than by inventing a subject for it — the one
# attempt to promote BC-003 cost Story 2 its AI Assistance requirement, because
# the shopper's evidence split between "shopping for AI" and what they were
# actually shopping for and neither half cleared the bar.
CATEGORIES_WITHOUT_A_SUBJECT: dict[str, str] = {}


def test_every_product_category_is_in_the_closed_enum(seed):
    """Law 7. Category is matched against SUBJECT_CATEGORIES, so a typo does not
    look like a typo — it produces a product that is off-subject for every
    shopper, silently and permanently."""
    from smartreco.domain.software_buying import PRODUCT_CATEGORIES

    used = {p["category"] for p in seed["products"] + list(CANONICAL_PRODUCTS)}
    assert used <= PRODUCT_CATEGORIES, (
        f"categories outside the enum: {sorted(used - PRODUCT_CATEGORIES)}")


def test_the_enum_has_no_categories_nothing_uses(seed):
    """The other direction: a category no product is in is dead vocabulary, and
    Decision #080 dissolved one exactly like it."""
    from smartreco.domain.software_buying import PRODUCT_CATEGORIES

    used = {p["category"] for p in seed["products"] + list(CANONICAL_PRODUCTS)}
    assert PRODUCT_CATEGORIES <= used, (
        f"enum entries no product uses: {sorted(PRODUCT_CATEGORIES - used)}")


def test_every_category_has_a_subject_or_a_stated_reason():
    """The sweep's closing invariant. 110 of 250 products sat in a category with
    no subject when this began; a shopper browsing them declared nothing, and the
    ranking had nothing to anchor on."""
    from smartreco.domain.software_buying import PRODUCT_CATEGORIES, SUBJECT_CATEGORIES

    subject_terms = {c for cats in SUBJECT_CATEGORIES.values() for c in cats}
    uncovered = {c for c in PRODUCT_CATEGORIES
                 if not any(term in c.lower() for term in subject_terms)}
    unexplained = sorted(uncovered - set(CATEGORIES_WITHOUT_A_SUBJECT))
    assert not unexplained, (
        f"these categories have no subject and no stated reason: {unexplained} — "
        "every product in them is off-subject for every shopper")


def test_no_stale_entries_in_the_subjectless_allowlist():
    """A ratchet only ratchets if entries are removed as they are fixed."""
    from smartreco.domain.software_buying import SUBJECT_CATEGORIES

    subject_terms = {c for cats in SUBJECT_CATEGORIES.values() for c in cats}
    fixed = sorted(c for c in CATEGORIES_WITHOUT_A_SUBJECT
                   if any(term in c.lower() for term in subject_terms))
    assert not fixed, f"now has a subject — remove from the allowlist: {fixed}"


def test_no_product_sits_on_a_shelf_no_shopper_can_declare(seed):
    """Decision #088 closes the sweep: 110 products → 8 → none.

    The allowlist above is a claim about vocabulary; this is the claim about
    stock, and only the second one is felt by a shopper. A subject-less
    *category* costs nothing while it is empty. A product in one is discounted
    by off_subject_factor however well it matches, and — the half that is easier
    to miss — browsing it declares no intent at all, so the journey it belongs
    to never forms.
    """
    from smartreco.domain.software_buying import SUBJECT_CATEGORIES

    subject_terms = {c for cats in SUBJECT_CATEGORIES.values() for c in cats}
    stranded = sorted(p["name"] for p in seed["products"] + list(CANONICAL_PRODUCTS)
                      if not any(t in p["category"].lower() for t in subject_terms))
    assert not stranded, (
        f"{len(stranded)} products are permanently off-subject: {stranded}")
