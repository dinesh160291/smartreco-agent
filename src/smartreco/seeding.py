"""Seeding — capability taxonomy + canonical product fixture.

Fixture separation (CLAUDE.md testing contract): automated tests seed ONLY the
canonical 10 products (PROD-001…010) from the Domain Pack roster. The demo
database additionally seeds the ~250-product catalog in Phase 6.
"""

from sqlalchemy.orm import Session as OrmSession

from smartreco import models
from smartreco.domain.software_buying import CANONICAL_PRODUCTS, CAPABILITIES
from smartreco.retrieval import EmbeddingBackend, save_product


def seed_capabilities(db: OrmSession) -> None:
    for cap_id, name, domain, narrative in CAPABILITIES:
        if db.get(models.Capability, cap_id) is None:
            db.add(models.Capability(capability_id=cap_id, name=name, domain=domain,
                                     business_value_narrative=narrative))
    db.commit()


def seed_canonical_products(db: OrmSession, chroma_client, backend: EmbeddingBackend) -> None:
    """Seeds PROD-001…010 through the standard dual-write path."""
    for entry in CANONICAL_PRODUCTS:
        product = db.get(models.Product, entry["product_id"]) or models.Product(
            product_id=entry["product_id"])
        product.name = entry["name"]
        product.vendor = entry["vendor"]
        product.category = entry["category"]
        product.description = entry["description"]
        product.business_purpose = entry["business_purpose"]
        save_product(db, chroma_client, backend, product, entry["capabilities"])


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
        if db.get(models.Product, entry["product_id"]) is not None:
            continue
        product = models.Product(
            product_id=entry["product_id"], name=entry["name"],
            vendor=entry["vendor"], category=entry["category"],
            description=entry["description"],
            business_purpose=entry["business_purpose"],
            business_value_narrative=entry["business_value_narrative"])
        try:
            save_product(db, chroma_client, backend, product, entry["capabilities"])
            count += 1
        except Exception:
            continue  # stays PENDING/FAILED; reconciliation sweep retries
    return count
