"""Measure the vocabulary drift the semantic search fallback risks (spec §5.2).

The worry, written down before the feature was built: a Domain Pack recognises a
subject from a **term set** — a short keyword vocabulary its patterns match
against the typed query. A search box that visibly understands sentences teaches
shoppers to type sentences, and a sentence rarely contains the keywords. So the
search that finally *works* for the shopper could be the search that tells the
platform nothing, and the platform would get better at finding and worse at
understanding at the same time.

This is the measurement, and it is deliberately three-way rather than two,
because the two-way version would overstate the loss. A shopper who searches in
plain English and then **clicks a result** emits a PRODUCT_VIEWED, and a click
is the shopper's own act — it has always been evidence. The question is not
whether the sentence is silent; it is whether the *journey* is.

  A. keyword search only        — what a shopper who knows the vocabulary produces
  B. plain-English search only  — the same intent, no keywords
  C. plain-English + two clicks — the realistic journey through the fallback

Reads the pack's term sets through `smartreco.domain.active`, so it names no
domain identifier and stays true when the pack changes.

Run from the repository root, against the output of measure_search_floor.py:

    python scripts/eval_search_drift.py [path/to/floor.json]
"""

import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, "src")

from smartreco.domain import active as domain                    # noqa: E402
from smartreco.engines.patterns import EventView, evaluate_patterns  # noqa: E402
from smartreco.policies import load_policies                     # noqa: E402

FLOOR_JSON = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "data/floor/floor.json")


def catalog_categories() -> dict[str, str]:
    seed = json.loads(pathlib.Path("seed/products.json").read_text(encoding="utf-8"))
    by_id = {p["product_id"]: p["category"] for p in seed["products"]}
    by_id.update({p["product_id"]: p["category"] for p in domain.CANONICAL_PRODUCTS})
    return by_id


def subject_for(category: str):
    """The pack's subject pattern owning `category`, with its term set.

    Data-driven on purpose: pairing a plain-English query with a hand-written
    keyword one would measure my vocabulary rather than the pack's.
    """
    for pattern_id, concept_id, _topics, categories, terms in domain.DOMAIN_RESEARCH_PATTERNS:
        if any(c in category.lower() or category.lower() in c for c in categories):
            return pattern_id, concept_id, sorted(terms)
    return None


def searches(query: str, count: int) -> list[EventView]:
    return [EventView(event_id=f"s{i}", event_type="SEARCH", session_id="s1",
                      metadata={"query": query}) for i in range(count)]


def views(categories: list[str], offset: int) -> list[EventView]:
    return [EventView(event_id=f"v{offset + i}", event_type="PRODUCT_VIEWED",
                      session_id="s1", metadata={"category": c})
            for i, c in enumerate(categories)]


def fired(events, policies) -> dict[str, str]:
    return {d.pattern_id: d.strength for d in evaluate_patterns(events, policies)}


def main():
    if not FLOOR_JSON.exists():
        sys.exit(f"no {FLOOR_JSON} — run scripts/measure_search_floor.py first")
    policies = load_policies()
    floor = policies.param("POL-SRCH-001", "min_similarity")
    category_of = catalog_categories()
    rows = json.loads(FLOOR_JSON.read_text(encoding="utf-8"))

    print(f"floor {floor}; {len(rows)} fixture queries\n")
    print(f"{'subject':<10}{'A kw':<9}{'B plain':<10}{'C +clicks':<11}{'shown':<7}"
          f"{'clicked':<26}query")
    print("-" * 118)

    dark, restored, unreachable = [], [], []
    for row in rows:
        if not row["expected"]:
            continue                                   # unanswerable: nothing to lose
        shown = [pid for pid, sim in row["top"] if sim >= floor]
        if not shown:
            unreachable.append(row["query"])
            continue
        categories = [category_of[pid] for pid in shown]
        majority = Counter(categories).most_common(1)[0][0]
        subject = subject_for(majority)
        if subject is None:
            continue
        pattern_id, _concept, terms = subject

        # Two signals is the pack's activation ladder for a subject pattern, so
        # each arm gets two of whatever it can produce.
        a = fired(searches(" ".join(terms[:2]), 2), policies)
        b = fired(searches(row["query"], 2), policies)
        c = fired(searches(row["query"], 2) + views(categories[:2], 10), policies)

        clicked = ", ".join(categories[:2])
        print(f"{pattern_id:<10}{a.get(pattern_id, '-'):<9}{b.get(pattern_id, '-'):<10}"
              f"{c.get(pattern_id, '-'):<11}{len(shown):<7}{clicked:<26}{row['query']}")
        if pattern_id in a and pattern_id not in b:
            (restored if pattern_id in c else dark).append((pattern_id, row["query"]))

    print("-" * 96)
    print(f"\nsubjects a keyword shopper reaches that a plain-English search does NOT: "
          f"{len(dark) + len(restored)}")
    print(f"  ...restored once the shopper clicks a fallback result: {len(restored)}")
    print(f"  ...still dark after clicking: {len(dark)}")
    for pattern_id, query in dark:
        print(f"      {pattern_id}  {query!r}")
    if unreachable:
        print(f"\nqueries the floor rejects entirely (no fallback, no clicks, no evidence): "
              f"{len(unreachable)}")
        for query in unreachable:
            print(f"      {query!r}")

    print("\nVERDICT: " + (
        "drift confined to the search event — clicking restores every subject"
        if not dark else
        f"REAL DRIFT — {len(dark)} subject(s) unreachable even after clicking"))


main()
