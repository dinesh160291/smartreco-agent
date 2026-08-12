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
    top_k = load_policies().param("POL-RETR-001", "top_k")
    saturating: dict[str, int] = {}
    for req_id, required in REQ_TO_CAP.items():
        full = sum(1 for p in seed["products"]
                   if set(required) <= set(p["capabilities"]))
        if full > top_k:
            saturating[req_id] = full
    assert not saturating, (
        f"requirements saturated beyond a Candidate Set ({top_k}): {saturating} — "
        "the top coverage band is a tie the ranking cannot break")


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
