"""Seeding — capability taxonomy + canonical product fixture.

Fixture separation (CLAUDE.md testing contract): automated tests seed ONLY the
canonical product roster supplied by the active Domain Pack. The demo
database additionally seeds the ~250-product catalog in Phase 6.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from smartreco import models
from smartreco.domain.software_buying import CANONICAL_PRODUCTS, CAPABILITIES
from smartreco.retrieval import EmbeddingBackend, save_product


def product_matches_seed(product: models.Product, stored_capability_ids: set[str],
                         entry: dict, fields: tuple[str, ...],
                         capability_ids: list[str]) -> bool:
    """Whether the stored row already says exactly what the seed entry says.

    Pure, so the seeders can skip the dual-write for products nobody edited:
    re-saving all 250 on every boot would spend an embedding call each, which
    is why the original skipped existing products outright — and why the demo
    catalog then froze at first boot (Decision #069).

    `fields` is the caller's, because the two rosters carry different ones: the
    canonical roster has no narrative, and comparing an absent field would make
    every canonical product look stale forever.
    """
    if set(capability_ids) != stored_capability_ids:
        return False
    return all((getattr(product, name) or "") == (entry.get(name) or "")
               for name in fields)


def _stored_capabilities(db: OrmSession, product_id: str) -> set[str]:
    return {
        cap_id for (cap_id,) in db.execute(
            select(models.ProductCapability.capability_id).where(
                models.ProductCapability.product_id == product_id))
    }


def seed_capabilities(db: OrmSession) -> None:
    for cap_id, name, domain, narrative in CAPABILITIES:
        if db.get(models.Capability, cap_id) is None:
            db.add(models.Capability(capability_id=cap_id, name=name, domain=domain,
                                     business_value_narrative=narrative))
    db.commit()


CANONICAL_FIELDS = ("name", "vendor", "category", "description", "business_purpose")
CATALOG_FIELDS = CANONICAL_FIELDS + ("business_value_narrative",)


def seed_canonical_products(db: OrmSession, chroma_client, backend: EmbeddingBackend) -> int:
    """Seeds the pack's canonical roster through the standard dual-write path.
    Returns the number written; unchanged products are skipped."""
    written = 0
    for entry in CANONICAL_PRODUCTS:
        product = db.get(models.Product, entry["product_id"])
        if product is not None and product.sync_status == "SYNCED" and product_matches_seed(
                product, _stored_capabilities(db, entry["product_id"]),
                entry, CANONICAL_FIELDS, entry["capabilities"]):
            continue
        product = product or models.Product(product_id=entry["product_id"])
        for name in CANONICAL_FIELDS:
            setattr(product, name, entry[name])
        save_product(db, chroma_client, backend, product, entry["capabilities"])
        written += 1
    return written


def seed_demo_catalog(db: OrmSession, chroma_client, backend: EmbeddingBackend) -> int:
    """Demo database only: loads the ~240 committed seed products
    (seed/products.json) through the standard dual-write path. Automated tests
    never call this — fixture separation."""
    import json
    from pathlib import Path

    seed_file = Path(__file__).resolve().parents[2] / "seed" / "products.json"
    if not seed_file.exists():
        return 0
    payload = json.loads(seed_file.read_text(encoding="utf-8"))
    count = 0
    for entry in payload["products"]:
        product = db.get(models.Product, entry["product_id"])
        # Skip only what already matches. Skipping every *existing* product,
        # as this did, meant an edited seed file never reached a database that
        # had booted once — the catalog audit's three passes reached the demo
        # only via hand-written scripts (Decision #069).
        if product is not None and product.sync_status == "SYNCED" and product_matches_seed(
                product, _stored_capabilities(db, entry["product_id"]),
                entry, CATALOG_FIELDS, entry["capabilities"]):
            continue
        product = product or models.Product(product_id=entry["product_id"])
        for name in CATALOG_FIELDS:
            setattr(product, name, entry[name])
        try:
            save_product(db, chroma_client, backend, product, entry["capabilities"])
            count += 1
        except Exception:
            continue  # stays PENDING/FAILED; reconciliation sweep retries
    return count
