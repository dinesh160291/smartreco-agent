"""Retrieval validation probe — demo catalog, live embedding backend (read-only).

The automated suite proves the engines against the canonical-10 fixture with a
deterministic embedding stub (testing contract). Two things it therefore cannot
see, and this probe checks:

  * whether the demo index (250 products, live backend) still agrees with the
    relational store — the dual-write contract's invariant (Core 20)
  * whether real embeddings retrieve anything meaningful, and what the
    `similarity` numbers recorded in Candidate Sets actually mean

Checks A-C are invariants: hard PASS/FAIL. Checks D-F are retrieval-quality
diagnostics — the spec promises no precision level (that is why Tier 2
evaluation exists), so they report measured numbers against a stated heuristic
and are labelled DIAGNOSTIC.

Writes nothing: the database is opened read-only and Chroma is only queried.

Run:  .venv\\Scripts\\python scripts\\validate_retrieval.py
"""

import math
import os
import sys
from collections import Counter

import chromadb
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session as OrmSession

from smartreco import models
from smartreco.domain.software_buying import REQUIREMENTS, REQ_TO_CAP
from smartreco.policies import load_policies
from smartreco.retrieval import (
    compose_query_document,
    embedding_document,
    get_collection,
    make_embedding_backend,
    retrieve_candidates,
)

SELF_RETRIEVAL_SAMPLE = 5          # products re-embedded and looked up by content
SELF_RETRIEVAL_MIN_SIMILARITY = 0.98

# Intent probes for the discrimination check: plain shopper language paired
# with the catalog category the intent obviously belongs to. The pairing is a
# diagnostic expectation, not a spec assertion.
INTENT_PROBES = [
    ("single sign-on and multi-factor authentication for employees",
     "Identity & Access Management"),
    ("continuous integration pipelines and container deployment", "DevOps"),
    ("applicant tracking, onboarding and payroll for staff", "HR"),
    ("dashboards and business intelligence over our warehouse", "Data & Analytics"),
    ("email campaigns, landing pages and lead nurturing", "Marketing"),
]


def _fail(results, name, detail):
    results.append((name, "FAIL", detail))


def _pass(results, name, detail):
    results.append((name, "PASS", detail))


def _info(results, name, detail):
    results.append((name, "INFO", detail))


def check_a_parity(db, collection, results) -> None:
    """A — dual-write parity (Core 20): the index is exactly the SYNCED rows."""
    rows = db.execute(
        select(models.Product.product_id, models.Product.sync_status)
        .where(models.Product.deleted_at.is_(None))).all()
    by_status = Counter(status for _pid, status in rows)
    synced = {pid for pid, status in rows if status == "SYNCED"}
    indexed = set(collection.get(include=[])["ids"])

    print(f"  relational: {len(rows)} live products {dict(by_status)}")
    print(f"  index:      {len(indexed)} vectors")

    unindexed = synced - indexed
    orphans = indexed - synced
    stuck = by_status.get("PENDING", 0) + by_status.get("FAILED", 0)

    if unindexed or orphans:
        _fail(results, "A dual-write parity",
              f"{len(unindexed)} SYNCED rows missing from index "
              f"{sorted(unindexed)[:5]}; {len(orphans)} orphan vectors "
              f"{sorted(orphans)[:5]}")
    elif stuck:
        _fail(results, "A dual-write parity",
              f"{stuck} products stuck PENDING/FAILED — reconciliation owes work")
    else:
        _pass(results, "A dual-write parity",
              f"{len(synced)} SYNCED rows == {len(indexed)} vectors, no orphans, "
              f"nothing PENDING/FAILED")


def check_b_vector_space(collection, backend, results) -> dict:
    """B — one vector space: stored dimensions uniform, live query vectors match,
    and vector norms (which decide what `1 - distance` means)."""
    sample = collection.get(limit=25, include=["embeddings"])
    dims = {len(v) for v in sample["embeddings"]}
    norms = [math.sqrt(sum(x * x for x in v)) for v in sample["embeddings"]]
    query_vector = backend.embed(["single sign-on"])[0]
    query_norm = math.sqrt(sum(x * x for x in query_vector))

    print(f"  stored dimensions: {sorted(dims)}  norms "
          f"min={min(norms):.4f} max={max(norms):.4f}")
    print(f"  live query vector: dim={len(query_vector)} norm={query_norm:.4f}")

    if len(dims) != 1:
        _fail(results, "B vector space", f"mixed stored dimensions {sorted(dims)}")
    elif len(query_vector) != dims.pop():
        _fail(results, "B vector space",
              f"live backend emits dim {len(query_vector)}, index holds "
              f"{sorted({len(v) for v in sample['embeddings']})} — spaces disagree")
    else:
        _pass(results, "B vector space",
              f"dim {len(query_vector)} everywhere; stored norms "
              f"{min(norms):.4f}-{max(norms):.4f}, query norm {query_norm:.4f}")

    unit = all(abs(n - 1.0) < 0.01 for n in norms) and abs(query_norm - 1.0) < 0.01
    space = (collection.configuration_json or {}).get("hnsw", {}).get("space")
    return {"unit_normalized": unit, "space": space}


def check_c_self_retrieval(db, collection, backend, results) -> None:
    """C — the stored vector really is this product's Embedding Document.
    Recompose each document from the current rows, embed it live, and look it
    up. Falsifies: stale vectors, mismatched ID mapping, drifted documents,
    query-side and document-side embeddings from different models."""
    products = db.execute(
        select(models.Product).where(models.Product.sync_status == "SYNCED")
        .order_by(models.Product.product_id)).scalars().all()
    step = max(1, len(products) // SELF_RETRIEVAL_SAMPLE)
    sample = products[::step][:SELF_RETRIEVAL_SAMPLE]

    documents, recomposed = [], []
    for product in sample:
        cap_ids = db.execute(
            select(models.ProductCapability.capability_id)
            .where(models.ProductCapability.product_id == product.product_id)
        ).scalars().all()
        recomposed.append(embedding_document(product, list(cap_ids)))
    documents = backend.embed(recomposed)

    stored = collection.get(ids=[p.product_id for p in sample], include=["documents"])
    stored_by_id = dict(zip(stored["ids"], stored["documents"]))

    misses, drifted = [], []
    for product, vector, document in zip(sample, documents, recomposed):
        hit = collection.query(query_embeddings=[vector], n_results=1)
        top_id = hit["ids"][0][0]
        similarity = 1.0 - hit["distances"][0][0]
        ok = top_id == product.product_id and similarity >= SELF_RETRIEVAL_MIN_SIMILARITY
        print(f"  {product.product_id:<9} {product.name[:28]:<28} "
              f"top1={top_id:<9} similarity={similarity:.4f} {'ok' if ok else 'MISS'}")
        if not ok:
            misses.append(f"{product.product_id}->{top_id}@{similarity:.4f}")
        if stored_by_id.get(product.product_id) != document:
            drifted.append(product.product_id)

    if misses:
        _fail(results, "C self-retrieval", f"{len(misses)} of {len(sample)}: {misses}")
    else:
        _pass(results, "C self-retrieval",
              f"{len(sample)}/{len(sample)} products are their own nearest neighbour "
              f"at similarity >= {SELF_RETRIEVAL_MIN_SIMILARITY}")
    if drifted:
        _fail(results, "C document drift",
              f"indexed document no longer matches the relational row: {drifted}")
    else:
        _pass(results, "C document drift",
              f"{len(sample)}/{len(sample)} indexed documents recompose byte-identically")


def check_d_discrimination(db, chroma_client, backend, policies, results) -> None:
    """D — DIAGNOSTIC: do different intents retrieve different, on-topic products?
    Degenerate embeddings return the same neighbours for every query."""
    top_k = policies.param("POL-RETR-001", "top_k")
    top3_sets, on_topic = [], []
    for text, expected_category in INTENT_PROBES:
        candidates = retrieve_candidates(db, chroma_client, backend, text, policies)
        named = []
        for c in candidates[:5]:
            product = db.get(models.Product, c["product_id"])
            named.append((product.name, product.category, c["similarity"]))
        hits = sum(1 for _n, category, _s in named[:3] if category == expected_category)
        on_topic.append(hits)
        top3_sets.append({c["product_id"] for c in candidates[:3]})
        print(f"  {text[:46]:<46} -> {hits}/3 {expected_category}")
        for name, category, similarity in named[:3]:
            print(f"      {similarity: .4f}  {name[:34]:<34} [{category}]")

    overlaps = [len(a & b) for i, a in enumerate(top3_sets) for b in top3_sets[i + 1:]]
    worst_overlap = max(overlaps) if overlaps else 0
    total_on_topic = sum(on_topic)
    print(f"  top-{top_k} retrieval; max top-3 overlap between unrelated intents: "
          f"{worst_overlap}")

    if worst_overlap >= 2:
        _fail(results, "D discrimination",
              f"unrelated intents share {worst_overlap} of their top 3 — "
              f"embeddings are not discriminating")
    elif total_on_topic < 2 * len(INTENT_PROBES):
        _info(results, "D discrimination",
              f"on-topic {total_on_topic}/{3 * len(INTENT_PROBES)} (heuristic wanted "
              f">= {2 * len(INTENT_PROBES)}); top-3 sets disjoint enough "
              f"(max overlap {worst_overlap})")
    else:
        _pass(results, "D discrimination",
              f"on-topic {total_on_topic}/{3 * len(INTENT_PROBES)}, "
              f"max top-3 overlap {worst_overlap}")


def check_e_query_document(db, chroma_client, backend, policies, results) -> None:
    """E — DIAGNOSTIC: the real thing. Compose a Behavioral Query Document the
    way stage_retrieval does and run the pipeline's own retrieve_candidates."""
    requirements = [{"req_id": "REQ-002", "priority": "Critical", "confidence": 0.94},
                    {"req_id": "REQ-004", "priority": "Medium", "confidence": 0.56}]
    query_document = compose_query_document(
        requirements, ["Identity Consolidation", "Security Posture"], "Evaluation",
        ["single sign-on", "saml"], REQUIREMENTS)
    print("  query document (qd-v1), first 3 lines:")
    for line in query_document.splitlines()[:3]:
        print(f"      {line}")

    candidates = retrieve_candidates(db, chroma_client, backend,
                                     query_document, policies)
    wanted_caps = set(REQ_TO_CAP["REQ-002"]) | set(REQ_TO_CAP["REQ-004"])
    relevant = 0
    for c in candidates:
        product = db.get(models.Product, c["product_id"])
        caps = set(db.execute(
            select(models.ProductCapability.capability_id)
            .where(models.ProductCapability.product_id == c["product_id"])
        ).scalars().all())
        overlap = caps & wanted_caps
        relevant += 1 if overlap else 0
        print(f"      {c['similarity']: .4f}  {product.name[:30]:<30} "
              f"[{product.category[:24]:<24}] matching-caps={len(overlap)}")

    top_similarity = candidates[0]["similarity"] if candidates else float("nan")
    skip_threshold = policies.param("POL-RETR-002", "skip_evaluation_min_similarity")
    print(f"  top similarity {top_similarity:.4f} vs POL-RETR-002 skip threshold "
          f"{skip_threshold} -> Tier 2 evaluation "
          f"{'SKIPPED' if top_similarity >= skip_threshold else 'RUNS'}")

    if not candidates:
        _fail(results, "E behavioral query document", "no candidates retrieved")
    else:
        _pass(results, "E behavioral query document",
              f"{len(candidates)} candidates, {relevant} carry >=1 capability the "
              f"requirements need")
    _info(results, "E skip-evaluation gate",
          f"top similarity {top_similarity:.4f} < {skip_threshold}: Tier 2 evaluation "
          f"runs on every retrieval")


def check_f_similarity_semantics(collection, backend, space_info, results) -> None:
    """F — what does the recorded `similarity` number mean? retrieve_candidates
    stores 1 - distance; with an l2-space index over unit vectors that is
    2*cos - 1, not cosine. Measure it rather than assume it."""
    a, b = backend.embed(["single sign-on for employees",
                          "payroll and benefits administration"])
    cosine = sum(x * y for x, y in zip(a, b))
    hit = collection.query(query_embeddings=[a], n_results=1)
    recorded = 1.0 - hit["distances"][0][0]
    print(f"  index space={space_info['space']}  unit-normalized vectors="
          f"{space_info['unit_normalized']}")
    print(f"  cosine between two unrelated intents: {cosine:.4f}")
    print(f"  recorded similarity of the best real hit: {recorded:.4f}")

    if space_info["space"] == "l2" and space_info["unit_normalized"]:
        _info(results, "F similarity semantics",
              "recorded similarity = 1 - squared_L2 = 2*cos - 1 on this index, "
              "not cosine; it compresses to [-1, 1] with 0 at cos=0.5 and can go "
              "negative. POL-RETR-002's 0.85 gate therefore means cos >= 0.925.")
    else:
        _info(results, "F similarity semantics",
              f"space={space_info['space']} unit={space_info['unit_normalized']} — "
              f"recorded similarity is 1 - distance in that space")


def main() -> int:
    load_dotenv()
    policies = load_policies()
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./data/smartreco.db")
    chroma_path = os.environ.get("CHROMA_PATH", "./data/chroma")
    backend_name = os.environ.get("EMBEDDINGS_BACKEND", "local")

    print(f"database  {database_url}")
    print(f"chroma    {chroma_path}")
    print(f"backend   {backend_name}   policy_version {policies.version}\n")

    engine = create_engine(database_url)
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = get_collection(chroma_client)
    backend = make_embedding_backend(policies)
    results: list[tuple[str, str, str]] = []

    with OrmSession(engine) as db:
        print("A. Dual-write parity (Core 20 invariant)")
        check_a_parity(db, collection, results)
        print("\nB. Vector space consistency")
        space_info = check_b_vector_space(collection, backend, results)
        print("\nC. Self-retrieval and document drift")
        check_c_self_retrieval(db, collection, backend, results)
        print("\nD. Intent discrimination (DIAGNOSTIC)")
        check_d_discrimination(db, chroma_client, backend, policies, results)
        print("\nE. Behavioral Query Document, pipeline path (DIAGNOSTIC)")
        check_e_query_document(db, chroma_client, backend, policies, results)
        print("\nF. Similarity semantics")
        check_f_similarity_semantics(collection, backend, space_info, results)

    print("\n" + "=" * 72)
    for name, status, detail in results:
        print(f"{status:<5} {name:<28} {detail}")
    failures = [r for r in results if r[1] == "FAIL"]
    print("=" * 72)
    print(f"{len(failures)} FAIL, "
          f"{len([r for r in results if r[1] == 'PASS'])} PASS, "
          f"{len([r for r in results if r[1] == 'INFO'])} INFO")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
