"""Semantic Retrieval Engine — embedding backends, vector store, dual-write (docs/core/20).

Two-backend embedding abstraction selected by EMBEDDINGS_BACKEND (stack-decisions):
  gateway — via the AI Provider Gateway (probe-verified)
  local   — Chroma's built-in default embedding function (offline)
Tests inject their own EmbeddingBackend stub (stubbed-gateway testing contract).

Dual-write contract: relational write PENDING → embed → Chroma upsert → SYNCED.
Failures leave PENDING/FAILED for the bounded reconciliation sweep
(POL-RETR-004); the relational store remains the system of record and the index
is always re-derivable.
"""

import os
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from smartreco import models
from smartreco.domain.software_buying import CAPABILITIES
from smartreco.policies import PolicyCatalog

_CAP_BY_ID = {cap_id: (name, domain, narrative) for cap_id, name, domain, narrative in CAPABILITIES}


class EmbeddingBackend(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class LocalChromaEmbeddings:
    """Chroma default embedding function (all-MiniLM-L6-v2, bundled ONNX)."""

    def __init__(self):
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        self._fn = DefaultEmbeddingFunction()

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [list(vec) for vec in self._fn(texts)]


def make_embedding_backend(policies: PolicyCatalog) -> EmbeddingBackend:
    backend = os.environ.get("EMBEDDINGS_BACKEND", "local")
    if backend == "gateway":
        from smartreco.gateway import AIGateway

        return AIGateway(policies)
    if backend == "local":
        return LocalChromaEmbeddings()
    raise ValueError(f"Unknown EMBEDDINGS_BACKEND {backend!r} (gateway | local)")


def embedding_document(product: models.Product, capability_ids: list[str]) -> str:
    """Deterministic Embedding Document composition (Core 20)."""
    cap_lines = []
    for cap_id in sorted(capability_ids):
        name, _domain, narrative = _CAP_BY_ID.get(cap_id, (cap_id, "", ""))
        cap_lines.append(f"{name}: {narrative}")
    return "\n".join(filter(None, [
        product.name,
        product.vendor,
        product.category,
        product.description,
        product.business_purpose,
        *cap_lines,
    ]))


def get_collection(chroma_client):
    return chroma_client.get_or_create_collection(name="products")


def save_product(
    db: OrmSession,
    chroma_client,
    backend: EmbeddingBackend,
    product: models.Product,
    capability_ids: list[str],
) -> None:
    """Dual-write: relational (PENDING) → embed → Chroma upsert → SYNCED."""
    product.sync_status = "PENDING"
    db.merge(product)
    db.query(models.ProductCapability).filter(
        models.ProductCapability.product_id == product.product_id
    ).delete(synchronize_session=False)
    for cap_id in capability_ids:
        db.add(models.ProductCapability(product_id=product.product_id, capability_id=cap_id))
    db.commit()

    try:
        document = embedding_document(product, capability_ids)
        vector = backend.embed([document])[0]
        get_collection(chroma_client).upsert(
            ids=[product.product_id],
            embeddings=[vector],
            documents=[document],
            metadatas=[{"product_id": product.product_id,
                        "record_version": product.record_version}],
        )
    except Exception:
        product.sync_status = "FAILED"
        db.merge(product)
        db.commit()
        raise

    product.sync_status = "SYNCED"
    db.merge(product)
    db.commit()


def reconcile_pending(db: OrmSession, chroma_client, backend: EmbeddingBackend) -> int:
    """Startup/periodic sweep: retry PENDING/FAILED rows (POL-RETR-004 caps the
    automatic attempts at the caller's discretion; v1 sweeps once per call)."""
    rows = db.execute(
        select(models.Product).where(models.Product.sync_status.in_(("PENDING", "FAILED")),
                                     models.Product.deleted_at.is_(None))
    ).scalars().all()
    repaired = 0
    for product in rows:
        cap_ids = [pc.capability_id for pc in db.execute(
            select(models.ProductCapability).where(
                models.ProductCapability.product_id == product.product_id)
        ).scalars().all()]
        try:
            save_product(db, chroma_client, backend, product, cap_ids)
            repaired += 1
        except Exception:
            continue  # stays FAILED; bounded by the sweep cadence, sticky per POL-RETR-004
    return repaired


def retrieve_candidates(
    db: OrmSession,
    chroma_client,
    backend: EmbeddingBackend,
    query_document: str,
    policies: PolicyCatalog,
) -> list[dict]:
    """Top-K semantic retrieval (POL-RETR-001); defensively drops hits whose
    product row is soft-deleted or absent (Core 20)."""
    top_k = policies.param("POL-RETR-001", "top_k")
    collection = get_collection(chroma_client)
    if collection.count() == 0:
        return []
    vector = backend.embed([query_document])[0]
    result = collection.query(query_embeddings=[vector],
                              n_results=min(top_k, collection.count()))
    candidates = []
    for product_id, distance in zip(result["ids"][0], result["distances"][0]):
        product = db.get(models.Product, product_id)
        if product is None or product.deleted_at is not None:
            continue
        candidates.append({
            "product_id": product_id,
            "similarity": round(1.0 - distance, 6),
            "record_version": product.record_version,
        })
    return candidates
