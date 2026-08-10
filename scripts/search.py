"""Manual retrieval bench — type a query, see the top-K candidates (read-only).

Two modes, matching the two things that can be searched with:

  1. Plain text — "what if a shopper meant this?"
       python scripts/search.py "single sign-on for contractors"

  2. A real Behavioral Query Document, composed from requirements exactly the
     way the pipeline's retrieval node composes it (this is what actually runs
     in production; plain text is a convenience for exploring the index):
       python scripts/search.py --req REQ-002:Critical,REQ-004:Medium

Prints each candidate's similarity, category, and how many of the requested
requirements' capabilities it actually holds — the last column is what the
Recommendation Engine goes on to rank by, and it is often not in similarity
order. That divergence is the point.

Costs one embedding call per run. Writes nothing.

Run:  .venv\\Scripts\\python scripts\\search.py "your query here"
"""

import os
import sys

import chromadb
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session as OrmSession

from smartreco import models
from smartreco.domain.software_buying import REQUIREMENTS, REQ_TO_CAP
from smartreco.policies import load_policies
from smartreco.retrieval import (
    compose_query_document,
    make_embedding_backend,
    retrieve_candidates,
)

USAGE = __doc__


def _parse_requirements(spec: str) -> list[dict]:
    """'REQ-002:Critical,REQ-004' -> requirement entries (default priority Medium)."""
    entries = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        req_id, _, priority = chunk.partition(":")
        req_id = req_id.strip().upper()
        if req_id not in REQUIREMENTS:
            raise SystemExit(f"unknown requirement {req_id!r}; known: "
                             f"{', '.join(sorted(REQUIREMENTS))}")
        entries.append({"req_id": req_id, "priority": (priority or "Medium").strip()})
    if not entries:
        raise SystemExit("no requirements given")
    return entries


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(USAGE)
        return 0

    load_dotenv()
    policies = load_policies()

    if argv[0] == "--req":
        if len(argv) < 2:
            raise SystemExit("--req needs a value, e.g. --req REQ-002:Critical")
        requirements = _parse_requirements(argv[1])
        wanted_caps = {cap for entry in requirements
                       for cap in REQ_TO_CAP[entry["req_id"]]}
        query = compose_query_document(
            requirements,
            concept_names=[],
            stage="Evaluation",
            recent_terms=[],
            requirement_names=REQUIREMENTS)
        print("Behavioral Query Document (qd-v1):\n")
        for line in query.splitlines():
            print(f"    {line[:96]}")
    else:
        query = " ".join(argv)
        wanted_caps = set()
        print(f'Plain-text query: "{query}"')

    engine = create_engine(os.environ.get("DATABASE_URL",
                                          "sqlite:///./data/smartreco.db"))
    chroma = chromadb.PersistentClient(
        path=os.environ.get("CHROMA_PATH", "./data/chroma"))
    backend = make_embedding_backend(policies)
    top_k = policies.param("POL-RETR-001", "top_k")

    with OrmSession(engine) as db:
        candidates = retrieve_candidates(db, chroma, backend, query, policies)
        if not candidates:
            print("\nno candidates — is the catalog seeded?")
            return 1

        header = f"\ntop {len(candidates)} of {top_k} requested"
        print(f"{header}   (similarity: ~0.3 strong, ~0.1 loose, <=0 weak)\n")
        print(f"    {'sim':>8}  {'product':<26} {'category':<26} caps")
        print(f"    {'-' * 8}  {'-' * 26} {'-' * 26} ----")
        for c in candidates:
            product = db.get(models.Product, c["product_id"])
            caps = set(db.execute(
                select(models.ProductCapability.capability_id).where(
                    models.ProductCapability.product_id == c["product_id"])
            ).scalars().all())
            held = f"{len(caps & wanted_caps)}/{len(wanted_caps)}" if wanted_caps else "-"
            print(f"    {c['similarity']: 8.4f}  {product.name[:26]:<26} "
                  f"{product.category[:26]:<26} {held}")

        if wanted_caps:
            print("\n    caps = required capabilities the product actually holds.")
            print("    Ranking in the app comes from that column, not from similarity.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
