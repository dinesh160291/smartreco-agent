"""Signature tests: dual-write contract (docs/core/20; data-model §Vector Index).

Relational write PENDING → embed → Chroma upsert → SYNCED; failure leaves
FAILED for the reconciliation sweep; the index is always re-derivable from the
relational system of record."""

import pytest
from sqlalchemy import select

from smartreco import models
from smartreco.retrieval import get_collection, reconcile_pending, retrieve_candidates, save_product


def test_seed_reaches_synced_and_chroma_has_all_ten(seeded, chroma):
    statuses = seeded.execute(select(models.Product.sync_status)).scalars().all()
    assert len(statuses) == 10 and set(statuses) == {"SYNCED"}
    assert get_collection(chroma).count() == 10


class FailingBackend:
    def embed(self, texts):
        raise ConnectionError("embedding backend down")


def test_embed_failure_leaves_failed_then_sweep_repairs(seeded, chroma, backend):
    product = seeded.get(models.Product, "PROD-003")
    caps = [pc.capability_id for pc in seeded.execute(
        select(models.ProductCapability).where(
            models.ProductCapability.product_id == "PROD-003")).scalars().all()]

    with pytest.raises(ConnectionError):
        save_product(seeded, chroma, FailingBackend(), product, caps)
    assert seeded.get(models.Product, "PROD-003").sync_status == "FAILED"

    repaired = reconcile_pending(seeded, chroma, backend)
    assert repaired == 1
    assert seeded.get(models.Product, "PROD-003").sync_status == "SYNCED"


def test_retrieval_returns_top_k_and_drops_deleted(seeded, chroma, backend, policies):
    query = "Single Sign-On Multi-Factor Authentication SCIM identity audit"
    candidates = retrieve_candidates(seeded, chroma, backend, query, policies)
    assert len(candidates) == policies.param("POL-RETR-001", "top_k")
    ids = [c["product_id"] for c in candidates]
    assert "PROD-003" in ids  # Okta must surface for an identity query

    okta = seeded.get(models.Product, "PROD-003")
    okta.deleted_at = models.utcnow()
    seeded.commit()
    candidates = retrieve_candidates(seeded, chroma, backend, query, policies)
    assert "PROD-003" not in [c["product_id"] for c in candidates]
