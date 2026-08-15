"""Measure the similarity floor for the semantic search fallback.

The gate in `docs/implementation/semantic-search-spec.md` §4: a floor may only
be set if it admits queries the catalog can answer and rejects queries it
cannot. This script is that measurement, and it is in the repository because a
number nobody can reproduce is not a measured number.

It builds a throwaway index from the CURRENT seed catalog with the configured
embedding backend, then asks two questions of every fixture query:

  1. does it miss lexically?  (only a lexical miss ever reaches the fallback)
  2. what similarity does the index give it?

Nothing touches the demo database or its index. Run from the repository root:

    python scripts/measure_search_floor.py <output-dir>

Similarity is `1 - distance`, exactly as `retrieval.retrieve_candidates`
computes it, so the numbers are directly comparable to POL-RETR-002's gate.
"""

import json
import os
import pathlib
import sys
from collections import Counter

sys.path.insert(0, "src")

import chromadb
from dotenv import load_dotenv

# find_dotenv() walks up from the *calling file*. Pointing it at the working
# directory is not a nicety: without it a run launched from elsewhere silently
# falls back to the local backend and measures the wrong embedding space, which
# is how the first run of this script produced numbers for a backend the
# deployment does not use.
if not load_dotenv(pathlib.Path.cwd() / ".env"):
    sys.exit("no .env found — run from the repository root")

from smartreco.catalog_search import normalize, search_catalog          # noqa: E402
from smartreco.domain.software_buying import CANONICAL_PRODUCTS, CAPABILITIES  # noqa: E402
from smartreco.policies import load_policies                            # noqa: E402
from smartreco.retrieval import make_embedding_backend                  # noqa: E402

CAP = {cid: (name, narrative) for cid, name, _dom, narrative in CAPABILITIES}

# Plain English, no catalog vocabulary — the whole point is queries the lexical
# path cannot serve. Each ANSWERABLE query names work the capability taxonomy
# genuinely covers; each UNANSWERABLE one names work no product in a business
# software catalog does. Labels are fixed in advance. Reclassifying one after
# seeing its score is how a measurement becomes a rationalisation.
ANSWERABLE = [
    ("stop people sharing passwords", "Identity & Access"),
    ("prove to an auditor what everyone did", "Compliance"),
    ("our designers need somewhere to put mockups", "Content & Knowledge"),
    ("we keep losing track of who is doing what this week", "Work Management"),
    ("find out why the website went down last night", "DevOps"),
    ("chase customers who have not paid us", "Finance"),
    ("make sure new starters have everything on day one", "HR"),
    ("understand which of our adverts actually worked", "Marketing"),
    ("write things down so people stop asking the same question", "Content & Knowledge"),
    ("know when someone tries to break into our systems", "Security"),
    ("keep an eye on how much the team is spending", "Finance"),
    ("stop deals going cold because nobody followed up", "CRM"),
]

UNANSWERABLE = [
    "book a meeting room",
    "order more laptops for the office",
    "best pizza near the office",
    "how many days until christmas",
    "what is the weather tomorrow",
    "my chair is broken",
    "find a plumber for the office",
    "play some music while i work",
    "renew the company car insurance",
    "translate this document into french",
]


def catalog_entries():
    seed = json.loads(pathlib.Path("seed/products.json").read_text(encoding="utf-8"))
    entries = []
    for p in list(seed["products"]) + [dict(x) for x in CANONICAL_PRODUCTS]:
        caps = list(p["capabilities"])
        entries.append({
            "product_id": p["product_id"], "name": p["name"], "vendor": p["vendor"],
            "category": p["category"], "description": p["description"],
            "business_purpose": p["business_purpose"],
            "capabilities": [CAP[c][0] for c in caps if c in CAP],
            # Same composition and field order as retrieval.embedding_document.
            "document": "\n".join(filter(None, [
                p["name"], p["vendor"], p["category"], p["description"],
                p["business_purpose"],
                *[f"{CAP[c][0]}: {CAP[c][1]}" for c in sorted(caps) if c in CAP],
            ])),
        })
    return entries


def build_index(entries, backend, out_dir):
    client = chromadb.PersistentClient(path=str(out_dir / "chroma"))
    try:
        client.delete_collection("products")
    except Exception:                      # first run — nothing to delete
        pass
    collection = client.create_collection(name="products")
    for i in range(0, len(entries), 64):
        chunk = entries[i:i + 64]
        vectors = [[float(x) for x in v]
                   for v in backend.embed([e["document"] for e in chunk])]
        collection.add(ids=[e["product_id"] for e in chunk], embeddings=vectors,
                       documents=[e["document"] for e in chunk])
        print(f"  indexed {min(i + 64, len(entries))}/{len(entries)}", flush=True)
    return collection


def main():
    out_dir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "./data/floor")
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = catalog_entries()
    backend_name = os.environ.get("EMBEDDINGS_BACKEND", "local")
    print(f"catalog: {len(entries)} products, backend={backend_name}")

    backend = make_embedding_backend(load_policies())
    collection = build_index(entries, backend, out_dir)
    by_id = {e["product_id"]: e for e in entries}

    rows = []
    for query, expected in ([(q, e) for q, e in ANSWERABLE]
                            + [(q, None) for q in UNANSWERABLE]):
        vector = [float(x) for x in backend.embed([normalize(query)])[0]]
        result = collection.query(query_embeddings=[vector], n_results=5)
        rows.append({
            "query": query, "expected": expected,
            "lexical": len(search_catalog(entries, query)),
            "top": [(pid, round(1.0 - dist, 4))
                    for pid, dist in zip(result["ids"][0], result["distances"][0])],
        })

    print("\n" + "=" * 96)
    for row in rows:
        kind = "ANSWERABLE" if row["expected"] else "UNANSWERABLE"
        cats = [by_id[pid]["category"] for pid, _s in row["top"][:3]]
        agree = Counter(cats).most_common(1)[0]
        print(f"{kind:<13} lex={row['lexical']:<3} sim={row['top'][0][1]:<9}"
              f"top3={agree[0] if agree[1] >= 2 else 'no majority':<20} {row['query']}")
        for pid, sim in row["top"][:3]:
            print(f"{'':<18}{sim:<9} {by_id[pid]['name']}  [{by_id[pid]['category']}]")
        if row["expected"]:
            print(f"{'':<18}expected area: {row['expected']}")
    print("=" * 96)

    answerable = [r for r in rows if r["expected"] and r["lexical"] == 0]
    unanswerable = [r for r in rows if not r["expected"] and r["lexical"] == 0]
    print(f"\nlexical misses: {len(answerable)}/{len(ANSWERABLE)} answerable, "
          f"{len(unanswerable)}/{len(UNANSWERABLE)} unanswerable "
          "(a query that hits lexically never reaches the fallback)")

    lowest = min(r["top"][0][1] for r in answerable)
    highest = max(r["top"][0][1] for r in unanswerable)
    print(f"lowest answerable top-1   : {lowest}")
    print(f"highest unanswerable top-1: {highest}")
    if lowest > highest:
        print(f"CLEAN SEPARATION — any floor in ({highest}, {lowest}) passes the §4 gate")
    else:
        print(f"NO CLEAN SEPARATION — overlap band [{lowest}, {highest}]")
        print("\nprecision/recall at candidate floors:")
        for floor in sorted({round(highest + 0.005, 4), -0.30, -0.35, -0.40,
                             -0.45, -0.50, round(lowest, 4)}, reverse=True):
            admits = sum(1 for r in answerable if r["top"][0][1] >= floor)
            wrong = sum(1 for r in unanswerable if r["top"][0][1] >= floor)
            print(f"  floor {floor:>8}: {admits:2}/{len(answerable)} answerable, "
                  f"{wrong:2}/{len(unanswerable)} unanswerable")

    (out_dir / "floor.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"\nwrote {out_dir / 'floor.json'}")


main()
