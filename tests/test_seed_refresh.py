"""Signature tests: a seeded catalog edit must reach an existing database.

Decision #069. `seed_demo_catalog` skipped every product that already existed
and startup only seeded at all when the products table was empty, so the demo
catalog froze at first boot: three passes of catalog audit changed
`seed/products.json` and reached the running demo only because each was
followed by a hand-written re-embed script.

The predicate is pure and tested here; the seeders own the loop around it.
Automated tests never call `seed_demo_catalog` itself — fixture separation
(CLAUDE.md testing contract) reserves the 240-product catalog for the demo
database.
"""

from smartreco import models
from smartreco.seeding import product_matches_seed


def _product(**overrides):
    fields = {"product_id": "PROD-900", "name": "Tableau", "vendor": "Salesforce",
              "category": "Data & Analytics", "description": "a description",
              "business_purpose": "a purpose", "business_value_narrative": "a narrative"}
    fields.update(overrides)
    return models.Product(**fields)


def _entry(**overrides):
    entry = {"name": "Tableau", "vendor": "Salesforce", "category": "Data & Analytics",
             "description": "a description", "business_purpose": "a purpose",
             "business_value_narrative": "a narrative"}
    entry.update(overrides)
    return entry


FIELDS = ("name", "vendor", "category", "description", "business_purpose",
          "business_value_narrative")


def test_unchanged_entry_needs_no_write():
    """The common case, and the reason the skip existed: re-embedding 240
    products on every boot would spend a gateway call each."""
    assert product_matches_seed(
        _product(), {"CAP-019"}, _entry(), FIELDS, ["CAP-019"]) is True


def test_a_changed_description_is_not_current():
    """The replay: prose regenerated in the seed file never reached the demo
    database, so the page kept describing the pre-audit product."""
    assert product_matches_seed(
        _product(), {"CAP-019"}, _entry(description="rewritten"), FIELDS,
        ["CAP-019"]) is False


def test_changed_capabilities_are_not_current():
    """Three audit passes moved capabilities; none of them reached the demo
    database on their own."""
    assert product_matches_seed(
        _product(), {"CAP-019"}, _entry(), FIELDS, ["CAP-019", "CAP-053"]) is False
    assert product_matches_seed(
        _product(), {"CAP-019", "CAP-053"}, _entry(), FIELDS, ["CAP-019"]) is False


def test_capability_order_is_not_a_change():
    """Capability lists are sets; a reordered list must not trigger a re-embed."""
    assert product_matches_seed(
        _product(), {"CAP-019", "CAP-053"}, _entry(), FIELDS,
        ["CAP-053", "CAP-019"]) is True


def test_a_field_the_caller_does_not_own_is_not_compared():
    """The canonical roster carries no narrative, so comparing one would make
    every canonical product look stale on every boot."""
    canonical_fields = ("name", "vendor", "category", "description", "business_purpose")
    assert product_matches_seed(
        _product(business_value_narrative="stored"), {"CAP-019"},
        _entry(business_value_narrative="different"), canonical_fields,
        ["CAP-019"]) is True


def test_missing_and_empty_are_the_same_thing():
    """A stored NULL and an absent seed key both mean "nothing here" — they must
    not read as a difference and re-embed the catalog every boot."""
    assert product_matches_seed(
        _product(business_value_narrative=None), {"CAP-019"},
        _entry(business_value_narrative=""), FIELDS, ["CAP-019"]) is True
