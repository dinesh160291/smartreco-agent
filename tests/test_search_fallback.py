"""Signature tests: the semantic search fallback (Decision #089).

Spec: docs/implementation/semantic-search-spec.md. Each test names the rule it
pins; the numbered ones map to that document's §10 testing contract.

The feature exists because a lexical AND-match cannot serve a shopper who does
not yet know the vocabulary — "stop people sharing passwords" matches no name,
capability, category, vendor or prose in the catalog, and the shopper wanted the
identity products the catalog has twenty of.

It ships with a *precision-first* floor because the measurement (§4) found no
clean separation between queries the catalog can answer and queries it cannot:
an embedding index has no way to say "I don't know", so unanswerable queries
score plausibly rather than low. The floor is what keeps the failure mode
silence rather than a wrong answer, which is why several tests below are about
what the page must NOT show.
"""

import json
import re

import pytest
from fastapi.testclient import TestClient

import apps.web.main as web
from smartreco import models
from smartreco.policies import load_policies
from smartreco.retrieval import embedding_document
from smartreco.search_fallback import QueryCache, fallback_search, select_results
from smartreco.seeding import seed_canonical_products, seed_capabilities


@pytest.fixture(scope="module")
def policies():
    return load_policies()


# --- The pure part: floor and ordering -------------------------------------

def test_the_gate_is_the_top_hit_alone(policies):
    """Decision #090. One number was doing two jobs — deciding whether the query
    has an answer *and* which products belong on the page — and the second job
    was starving the first's own page.

    The gate answers only the first question, and it asks it of the **best** hit:
    if nothing is close, the query is unanswered and the page is empty.
    """
    band = policies.param("POL-SRCH-001", "neighbour_band")
    assert select_results([("PROD-001", -0.9), ("PROD-002", -0.95)],
                          min_similarity=-0.38, neighbour_band=band, top_k=8) == []


def test_a_neighbour_below_the_gate_still_makes_the_page(policies):
    """The point of the change, and the part that looks wrong until you see why.

    -0.45 would have been discarded by the old rule. It is admitted now because
    the *query* was already judged answerable by a top hit at -0.30 — and the
    page it lands on says "products with related capabilities", which is exactly
    what it is. Precision is set by the gate; the band is about company.
    """
    # -0.44, not -0.45: the band edge is a float subtraction (-0.3 - 0.15 is
    # -0.44999999999999996), and a test sitting exactly on it would be pinning
    # the arithmetic rather than the rule.
    kept = select_results([("PROD-001", -0.30), ("PROD-002", -0.44)],
                          min_similarity=-0.38, neighbour_band=0.15, top_k=8)
    assert [pid for pid, _s in kept] == ["PROD-001", "PROD-002"]


def test_the_band_still_excludes_distant_hits():
    """A band that admits everything is not a band, and the index always returns
    something — 'best pizza' would arrive with a full page of nearest
    neighbours if the cut were only top_k."""
    kept = select_results([("PROD-001", -0.30), ("PROD-002", -0.80)],
                          min_similarity=-0.38, neighbour_band=0.15, top_k=8)
    assert [pid for pid, _s in kept] == ["PROD-001"]


def test_the_change_cannot_make_an_unanswerable_query_answerable():
    """The safety property that made this fix legitimate rather than a retune.

    Measured across the whole fixture: unanswerable pages stayed at 0/10 for
    every band from 0.05 to 0.50, because the band cannot promote a top hit
    the gate rejected. The set of queries that produce a page is *identical*
    to before Decision #090; only what is on the page changed.
    """
    for band in (0.0, 0.05, 0.15, 0.5, 5.0):
        assert select_results([("PROD-001", -0.39), ("PROD-002", -0.40)],
                              min_similarity=-0.38, neighbour_band=band,
                              top_k=8) == [], f"band {band} conjured a page"


def test_order_is_similarity_then_product_id():
    """§10.4, and it is load-bearing rather than decorative: the measurement
    found similarity is not bit-stable across calls (~3e-4), so without a total
    tie-break two identical searches could return different orders."""
    hits = [("PROD-009", -0.30), ("PROD-002", -0.30), ("PROD-005", -0.10)]
    assert [pid for pid, _s in select_results(hits, -0.38, 0.5, 8)] == [
        "PROD-005", "PROD-002", "PROD-009"]


def test_top_k_bounds_the_result(policies):
    """Law 5. The index will always return something; the bound is ours."""
    hits = [(f"PROD-{i:03d}", -0.1) for i in range(20)]
    assert len(select_results(hits, -0.38, 0.5, top_k=3)) == 3
    assert policies.param("POL-SRCH-001", "top_k") == 8


# --- The wiring: bounds, budget, degradation --------------------------------

class FakeBackend:
    """Counts embed calls, because the cost model is 'only on a lexical miss'
    and a test that cannot see the call cannot pin it."""

    def __init__(self, vector=None, raises=None):
        self.calls: list[str] = []
        self._vector = vector or [0.1, 0.2, 0.3]
        self._raises = raises

    def embed(self, texts):
        self.calls.extend(texts)
        if self._raises:
            raise self._raises
        return [self._vector for _ in texts]


class FakeIndex:
    def __init__(self, hits=(), raises=None):
        self._hits = list(hits)
        self._raises = raises
        self.queries = 0

    def query(self, vector, top_k):
        self.queries += 1
        if self._raises:
            raise self._raises
        return self._hits[:top_k]


def test_the_query_is_truncated_before_it_reaches_the_backend(policies):
    """§10.8, asserted at the backend seam rather than the caller — unbounded
    user text must never reach the gateway (Law 5), and a caller-side assertion
    would pass while the bound was applied to the wrong string."""
    backend = FakeBackend()
    index = FakeIndex([("PROD-001", -0.1)])
    fallback_search("x" * 5000, backend=backend, index=index, policies=policies,
                    spend=lambda: True)
    limit = policies.param("POL-SRCH-001", "max_query_chars")
    assert len(backend.calls[0]) == limit


def test_a_refused_budget_never_embeds(policies):
    """§6. Exhaustion must cost nothing — a cap that still pays for the call is
    not a cap."""
    backend = FakeBackend()
    index = FakeIndex([("PROD-001", -0.1)])
    result = fallback_search("anything", backend=backend, index=index,
                             policies=policies, spend=lambda: False)
    assert result == []
    assert backend.calls == [], "budget was refused and the embedding ran anyway"
    assert index.queries == 0


def test_a_gateway_failure_degrades_to_the_empty_state(policies):
    """§10.5. Never an error page (Law 5). This is the one place the codebase
    sanctions swallowing an exception, and it is narrow: the caller gets the
    same empty list it would have got from a genuinely unanswerable query."""
    from smartreco.gateway import GatewayUnavailable

    backend = FakeBackend(raises=GatewayUnavailable("down"))
    index = FakeIndex([("PROD-001", -0.1)])
    assert fallback_search("anything", backend=backend, index=index,
                           policies=policies, spend=lambda: True) == []


def test_an_index_failure_degrades_to_the_empty_state(policies):
    """The other half of §10.5, and it fails for a different reason: the
    embedding succeeded and the vector store is what broke."""
    backend = FakeBackend()
    index = FakeIndex(raises=RuntimeError("collection missing"))
    assert fallback_search("anything", backend=backend, index=index,
                           policies=policies, spend=lambda: True) == []


def test_the_cache_expires_on_a_simulated_clock():
    """POL-SRCH-002's TTL, tested without a real wait (CLAUDE.md). The cache is
    what keeps a shopper retyping one failing query from spending the budget
    twice, so an expiry that never fires and one that always fires are both
    bugs — this pins the boundary in each direction."""
    cache = QueryCache(ttl_seconds=3600, max_entries=8)
    cache.put("sso", ["hit"], now=1000.0)
    assert cache.get("sso", now=1000.0 + 3599) == ["hit"]
    assert cache.get("sso", now=1000.0 + 3600) is None, "TTL boundary is exclusive"


def test_the_cache_is_bounded():
    """Law 5. An unbounded cache on a public surface is a memory leak with a
    query box attached."""
    cache = QueryCache(ttl_seconds=3600, max_entries=2)
    for i in range(5):
        cache.put(f"q{i}", [i], now=1000.0)
    assert cache.get("q0", now=1000.0) is None      # evicted
    assert cache.get("q4", now=1000.0) == [4]


def test_an_unexpected_error_is_not_swallowed(policies):
    """The limit of the rule above. Fail loud (CLAUDE.md): the degradation path
    catches retrieval failures, not every bug that happens to occur inside it.
    A TypeError here means the code is wrong, and hiding it behind an empty
    search result is how a broken feature looks like an unanswerable query."""
    backend = FakeBackend()
    backend.embed = lambda texts: (_ for _ in ()).throw(TypeError("bug"))
    with pytest.raises(TypeError):
        fallback_search("anything", backend=backend, index=FakeIndex(),
                        policies=policies, spend=lambda: True)


# --- Through the route: the behaviour a shopper actually gets ---------------

# "sharing" prefix-matches File Sharing, "passwords" matches nothing anywhere,
# and the lexical path ANDs — so this is a genuine miss, which is the only way
# to reach the fallback. Exactly the shopper the feature exists for: they want
# the identity products and do not know the word "SSO".
MISS = "stop people sharing passwords"
HIT = "single sign-on"


class SpyBackend:
    """Counts embed calls and can point one query at a known product's document.

    The count is the point: "only on a lexical miss" is a claim about calls, and
    a test that cannot see the call cannot pin it. The alias exists because the
    stub embedding is token-hashed — a query that misses lexically also shares
    no vocabulary with any document, so without it no fixture query could ever
    clear the floor.
    """

    def __init__(self, inner, alias=None):
        self.inner, self.alias, self.calls = inner, alias or {}, []

    def embed(self, texts):
        self.calls.extend(texts)
        return self.inner.embed([self.alias.get(t, t) for t in texts])


@pytest.fixture()
def client(session_factory, chroma, backend, policies, fake_gateway):
    web._state.clear()
    web._state.update({"policies": policies, "session_factory": session_factory,
                       "chroma": chroma, "backend": backend, "gateway": fake_gateway})
    with session_factory() as db:
        seed_capabilities(db)
        seed_canonical_products(db, chroma, backend)
        product = db.get(models.Product, "PROD-003")
        caps = [row.capability_id for row in db.query(models.ProductCapability)
                .filter_by(product_id="PROD-003").all()]
        document = embedding_document(product, caps)
    # The miss query embeds exactly like PROD-003's document, so it lands at the
    # top of the index at similarity 1.0 — well clear of the floor.
    web._state["backend"] = SpyBackend(backend, {MISS: document})
    with TestClient(web.app) as c:
        yield c
    web._state.clear()


def spy():
    return web._state["backend"]


def page_events(html):
    match = re.search(r'id="sr-page-events">(.*?)</script>', html, re.S)
    return json.loads(match.group(1)) if match else []


def test_a_query_with_lexical_results_never_embeds(client):
    """§10.1 — the cost model, and the reason the fallback is safe to ship: it
    is unreachable for any query the deterministic path can serve, so no result
    set that existed before this feature can move, and no ordinary search pays
    for an embedding."""
    response = client.get("/?q=single+sign-on")
    assert response.status_code == 200
    assert "Okta" in response.text
    assert spy().calls == [], "a lexical hit reached the embedding backend"
    assert "No exact matches" not in response.text


def test_a_zero_result_query_falls_back_and_says_so(client):
    """§10.2 and §3. The shopper gets products *and* is told these are not exact
    matches — a fallback result set presented as a search result set would be
    the platform quietly overstating what it knows."""
    response = client.get("/?q=stop+people+sharing+passwords")
    assert response.status_code == 200
    assert len(spy().calls) == 1, "expected exactly one embedding"
    assert "No exact matches for" in response.text
    assert "products with related capabilities" in response.text
    assert "Okta" in response.text          # PROD-003, the aliased document


def test_a_query_the_catalog_cannot_answer_still_gets_the_empty_state(client):
    """§10.3 at the route, and the safety property the whole feature rests on.

    The index always returns *something* — it has no way to say "I don't know",
    which is exactly what the measurement found: unanswerable queries score
    plausibly rather than low. So the fallback runs, spends its embedding, and
    must still render the empty state rather than dressing up its nearest
    neighbours as an answer. "Helps sometimes" is the deal; "answers wrongly"
    is not.
    """
    response = client.get("/?q=best+pizza+near+the+office")
    assert response.status_code == 200
    assert len(spy().calls) == 1, "the fallback should have run"
    assert "No products match that search" in response.text
    assert "No exact matches for" not in response.text
    assert "products with related capabilities" not in response.text


def test_the_fallback_page_shows_no_ids_and_no_similarity_scores(client):
    """§10.9. Law 10 for the IDs; the scores are excluded because they are an
    internal quantity — printing -0.38 invites reading it as a percentage fit,
    and it is negative on this scale anyway."""
    html = client.get("/?q=stop+people+sharing+passwords").text
    body = re.sub(r"<script[\s\S]*?</script>", "", html)
    text_only = re.sub(r"<[^>]+>", "", body)
    assert not re.search(r"\b(CAP|REQ|PROD|BC|BP)-\d", text_only)
    assert "similarity" not in text_only.lower()


def test_the_search_event_records_the_typed_query_not_the_retrieval(client):
    """§10.6 and §5.1 — the load-bearing one.

    The event records what the shopper typed, verbatim. The two new fields are
    descriptive. What must NOT appear is any trace of what the platform
    retrieved: a result list is the platform's own proposal, and if a proposal
    became evidence the platform would infer intent from its own guess and then
    recommend against it.
    """
    html = client.get("/?q=stop+people+sharing+passwords").text
    search = next(e for e in page_events(html) if e["type"] == "SEARCH")
    assert search["metadata"]["query"] == MISS            # verbatim, unexpanded
    assert search["metadata"]["fallback_used"] is True
    assert search["metadata"]["result_count"] >= 1
    blob = json.dumps(search)
    assert "PROD-" not in blob, "the retrieved products leaked into the event"
    assert "similarity" not in blob


def test_no_pattern_evaluator_reads_the_new_metadata():
    """§10.7. A ratchet in the shape of the domain-boundary test: the rule is
    only worth anything if it cannot be quietly undone later by an evaluator
    reaching for a field that happens to be sitting there."""
    import inspect

    from smartreco.domain.software_buying import patterns as pack
    from smartreco.engines import patterns as engine

    for module in (engine, pack):
        source = inspect.getsource(module)
        for field in ("result_count", "fallback_used"):
            assert field not in source, (
                f"{module.__name__} reads {field} — the platform's own retrieval "
                "output has become evidence (spec §5.1)")


def test_a_signed_out_visitor_gets_the_fallback(client):
    """§10.11. The shopper who most needs help with vocabulary is the one who
    has not committed to an account yet; gating the feature behind registration
    would withhold it from exactly that person."""
    response = client.get("/?q=stop+people+sharing+passwords")
    assert "No exact matches for" in response.text
    assert len(spy().calls) == 1


def test_the_anonymous_session_cap_is_enforced(client, policies):
    """§10.12. Exhaustion renders the empty state — not an error, and not a
    prompt to register. The cap bounds cost; it is not a conversion funnel."""
    cap = policies.param("POL-SRCH-002", "searches_per_anonymous_session")
    for i in range(cap):
        client.get(f"/?q=unmatchable+xyzzy{i}+quux")
    assert len(spy().calls) == cap

    response = client.get("/?q=stop+people+sharing+passwords")
    assert response.status_code == 200
    assert len(spy().calls) == cap, "spent an embedding past the cap"
    assert "No products match that search" in response.text
    assert "No exact matches for" not in response.text


def test_registering_moves_the_visitor_onto_the_per_user_cap(client, policies):
    """§10.13. The session count is abandoned rather than carried — simpler than
    reconciling two ledgers, and the direction of the error favours the shopper
    who has just committed to an account."""
    cap = policies.param("POL-SRCH-002", "searches_per_anonymous_session")
    for i in range(cap):
        client.get(f"/?q=unmatchable+xyzzy{i}+quux")
    assert len(spy().calls) == cap

    assert client.post("/auth/register", json={"email": "s@example.com",
                                               "password": "pw123456"}).status_code == 201
    response = client.get("/?q=stop+people+sharing+passwords")
    assert "No exact matches for" in response.text
    assert len(spy().calls) == cap + 1, (
        "the exhausted anonymous count followed the shopper into their account")
