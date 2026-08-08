"""Signature test: committed demo seed integrity (data-model §Catalog Seed
Strategy). The demo catalog is data the live demo's determinism depends on:
the distractor constraint must hold so canonical winners stay canonical."""

import json
from pathlib import Path

import pytest

from smartreco.domain.software_buying import CANONICAL_PRODUCTS, REQ_TO_CAP

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


def test_distractor_constraint_holds(seed):
    """No non-canonical product may fully cover any scenario requirement's
    capability set — canonical winners must remain deterministic."""
    for product in seed["products"]:
        caps = set(product["capabilities"])
        for req_id, required in REQ_TO_CAP.items():
            assert not set(required) <= caps, (
                f"{product['product_id']} fully covers {req_id} — distractor "
                "constraint violated")


def test_narratives_are_clean(seed):
    for product in seed["products"]:
        narrative = product["business_value_narrative"]
        assert narrative and len(narrative) < 300
        for banned in ("CAP-", "REQ-", "PROD-"):
            assert banned not in narrative
