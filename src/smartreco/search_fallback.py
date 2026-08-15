"""Semantic fallback for the catalog search box (spec: docs/implementation/
semantic-search-spec.md; POL-SRCH-001/002).

Lexical search stays primary and unchanged. This runs only when it returns
nothing, which is what makes the cost model work: the fallback is unreachable
for any query the deterministic path can serve, so no result set that existed
before this module can move.

It is not the Semantic Retrieval Engine. That engine asks "what does this
person's behaviour imply?" and writes Candidate Sets; this reads the same index
to answer "what did this person ask for" and writes nothing. Core 20's dual-write
contract is untouched — this is a read.

Two things it deliberately does not do. It never returns a product the index
scored below the floor, because the measurement found that queries the catalog
cannot answer still score plausibly (§4) — the floor is the only thing standing
between the feature and guessing. And it never raises on a retrieval failure:
gateway down, index missing, budget spent all produce the empty result the
shopper would have seen anyway (Law 5).
"""

from collections import OrderedDict

from smartreco.gateway import GatewayUnavailable
from smartreco.policies import PolicyCatalog


class ChromaIndex:
    """Adapter: the vector store behind the seam `fallback_search` expects.

    Similarity is `1 - distance`, the same quantity Core 20 defines and
    POL-RETR-002 and POL-SRCH-001 are both expressed in. Computing it anywhere
    else would let the floor drift from the scale it was measured on.
    """

    def __init__(self, collection):
        self._collection = collection

    def query(self, vector, top_k: int) -> list[tuple[str, float]]:
        count = self._collection.count()
        if count == 0:
            return []
        result = self._collection.query(query_embeddings=[vector],
                                        n_results=min(top_k, count))
        return [(pid, round(1.0 - distance, 6))
                for pid, distance in zip(result["ids"][0], result["distances"][0])]


class QueryCache:
    """Bounded TTL cache of normalized query → hits (POL-SRCH-002).

    Two jobs, and the second is the one worth stating: it keeps the budget
    honest when a shopper retypes the same failing query, and it makes the page
    stable within the window — the measurement found similarity is not
    bit-stable, so two live embeddings of one query can order near-equal hits
    differently.

    `now` is passed in rather than read, so the expiry is testable against a
    simulated clock instead of a real wait.
    """

    def __init__(self, ttl_seconds: int, max_entries: int):
        self._ttl = ttl_seconds
        self._max = max_entries
        self._entries: OrderedDict[str, tuple[float, list]] = OrderedDict()

    def get(self, key: str, now: float):
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, value = entry
        if now - stored_at >= self._ttl:
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return value

    def put(self, key: str, value: list, now: float) -> None:
        self._entries[key] = (now, value)
        self._entries.move_to_end(key)
        while len(self._entries) > self._max:
            self._entries.popitem(last=False)   # oldest use first (Law 5: bounded)


def apply_floor(hits, min_similarity: float, top_k: int) -> list[tuple[str, float]]:
    """Discard hits below the floor; order by similarity, then Product ID.

    The tie-break is not cosmetic. Similarity is not bit-stable across embedding
    calls — the same query measured 3e-4 apart on consecutive runs — so without
    a total order two identical searches could disagree, and §3 promises the
    list is replayable.
    """
    kept = [(pid, sim) for pid, sim in hits if sim >= min_similarity]
    kept.sort(key=lambda hit: (-hit[1], hit[0]))
    return kept[:top_k]


def fallback_search(query: str, *, backend, index, policies: PolicyCatalog,
                    spend) -> list[tuple[str, float]]:
    """Embed `query`, ask `index` for neighbours, and apply POL-SRCH-001.

    `spend()` is the budget: it returns False when the caller has none left, and
    is called *before* the embedding, because a cap that still pays for the call
    is not a cap. `index.query(vector, top_k)` returns [(product_id, similarity)]
    — a seam rather than a Chroma collection, so the bounds and the degradation
    can be tested without a vector store.
    """
    if not spend():
        return []

    max_chars = policies.param("POL-SRCH-001", "max_query_chars")
    top_k = policies.param("POL-SRCH-001", "top_k")
    floor = policies.param("POL-SRCH-001", "min_similarity")

    try:
        vector = backend.embed([query[:max_chars]])[0]
        hits = index.query(vector, top_k)
    except (GatewayUnavailable, RuntimeError, ValueError, KeyError, OSError):
        # The sanctioned degradation, and it is narrow on purpose: retrieval
        # failures only. A TypeError from this module's own wiring must still
        # reach the caller, or a broken feature is indistinguishable from a
        # query the catalog cannot answer.
        return []
    return apply_floor(hits, floor, top_k)
