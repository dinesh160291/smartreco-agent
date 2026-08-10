"""Deterministic catalog search for the Explore surface (ui-design-spec §Catalog Search).

Not a decision engine and not the Semantic Retrieval Engine: this is the
shopper's own text query against the catalog, and it is deliberately
deterministic — same query, same results, explainable without a model. The
vector index stays reserved for the Semantic Retrieval Engine's behavioral
Candidate Sets (Core 20), which answer a different question ("what does this
person's behaviour imply?") from the one a search box asks.

Matching: normalize away punctuation and case, split the query into tokens,
require every token to match somewhere (AND), and let a token match as a
prefix so "provision" finds "SCIM Provisioning". Ranking is by which field
matched — a name hit outranks a description hit — so the ordering is
explainable rather than merely stable.

Capability names are searched, which is the point: a product's capabilities
are what it *does*, and searching only prose meant the canonical SSO product
could not be found by searching for single sign-on.
"""

import re

from smartreco.domain.software_buying import CAPABILITIES, SEARCH_ALIASES

# Capability name → taxonomy domain, and how many capabilities each domain has.
# Ranking needs the domain of whatever the query matched, so it can ask how
# completely a product covers *that* area rather than how large it is overall.
_DOMAIN_OF = {name: domain for _cid, name, domain, _n in CAPABILITIES}
_DOMAIN_SIZE: dict[str, int] = {}
for _cid, _name, _domain, _n in CAPABILITIES:
    _DOMAIN_SIZE[_domain] = _DOMAIN_SIZE.get(_domain, 0) + 1

# Field weights: where a token matched decides rank. Values are ordinal, not
# tuned — only their order carries meaning.
WEIGHT_NAME = 100
WEIGHT_CAPABILITY = 60
WEIGHT_CATEGORY = 40
WEIGHT_VENDOR = 30
WEIGHT_PROSE = 10

_NON_WORD = re.compile(r"[^a-z0-9]+")


def normalize(text: str) -> str:
    """Case-fold and reduce every run of punctuation/whitespace to one space,
    so 'Single Sign-On!', 'single sign on' and 'single  sign--on' are one
    string. Hyphenation must never decide whether a product is findable."""
    return _NON_WORD.sub(" ", (text or "").lower()).strip()


def _tokens(text: str) -> list[str]:
    return [t for t in normalize(text).split(" ") if t]


def expand_query(query: str) -> list[str]:
    """Query tokens with domain acronyms resolved (sso → single sign on).

    Expansion is a retrieval convenience only. The SEARCH event records what
    the shopper actually typed — rewriting it would teach the reasoning
    engines vocabulary the user never used.
    """
    out: list[str] = []
    for token in _tokens(query):
        out.extend(_tokens(SEARCH_ALIASES[token]) if token in SEARCH_ALIASES else [token])
    return out


MIN_PREFIX_LEN = 3


def _matches(token: str, words: set[str]) -> bool:
    """Prefix match, except for very short tokens which must match a whole word.

    Without the length floor, the "on" in "single sign-on" prefix-matches
    OneLogin's *name* at full name weight, so every single-sign-on search
    returned OneLogin first on the strength of a two-letter fragment.
    """
    if len(token) < MIN_PREFIX_LEN:
        return token in words
    return any(word.startswith(token) for word in words)


def _field_score(token: str, haystack_tokens: set[str], weight: int) -> int:
    return weight if _matches(token, haystack_tokens) else 0


def score_entry(entry: dict, query_tokens: list[str]) -> int | None:
    """Total score, or None when any token fails to match anywhere (AND)."""
    fields = (
        (_tokens(entry.get("name", "")), WEIGHT_NAME),
        ({t for cap in entry.get("capabilities", ()) for t in _tokens(cap)},
         WEIGHT_CAPABILITY),
        (_tokens(entry.get("category", "")), WEIGHT_CATEGORY),
        (_tokens(entry.get("vendor", "")), WEIGHT_VENDOR),
        (_tokens(f"{entry.get('description', '')} {entry.get('business_purpose', '')}"),
         WEIGHT_PROSE),
    )
    prepared = [(set(words), weight) for words, weight in fields]

    total = 0
    for token in query_tokens:
        best = max(_field_score(token, words, weight) for words, weight in prepared)
        if best == 0:
            return None  # AND: one unmatched token disqualifies the product
        total += best
    return total


def domain_completeness(entry: dict, query_tokens: list[str]) -> float:
    """How completely the product covers the taxonomy domain the query hit.

    A capability query matches every product holding that capability at the
    same weight — twenty identity products score identically for "single sign
    on" — so a tiebreak decides the order, and which one is chosen decides
    whether specialists or suites surface.

    The choice is really about what to divide by, and each option has a bias:
    dividing by nothing ranks on raw capability count and puts the broadest
    suite on top; dividing by the *product's* own count rewards being thin, so
    three-capability distractors win. Dividing by the *searched domain's* size
    does neither — a product cannot inflate it by being large or by being
    small, only by genuinely covering the area asked about.

    This is not popularity or editorial prominence: it is computed from the
    capability taxonomy. The platform refuses popularity-based ranking on its
    recommendation surface, and the search box must not reinstate it.
    """
    capabilities = entry.get("capabilities") or ()
    matched_domains = {
        _DOMAIN_OF[cap] for cap in capabilities
        if cap in _DOMAIN_OF and any(_matches(token, set(_tokens(cap)))
                                     for token in query_tokens)
    }
    if not matched_domains:
        return 0.0
    held = sum(1 for cap in capabilities if _DOMAIN_OF.get(cap) in matched_domains)
    available = sum(_DOMAIN_SIZE[domain] for domain in matched_domains)
    return held / available if available else 0.0


def search_catalog(entries: list[dict], query: str) -> list[dict]:
    """Filter and rank `entries` by `query`. An empty query filters nothing.

    Order: field-weight score → domain completeness → capability count → name.
    Total and replayable: the same query always returns the same order.
    """
    query_tokens = expand_query(query)
    if not query_tokens:
        return list(entries)

    scored = []
    for entry in entries:
        score = score_entry(entry, query_tokens)
        if score is not None:
            scored.append((score, domain_completeness(entry, query_tokens),
                           len(entry.get("capabilities") or ()), entry))
    scored.sort(key=lambda t: (-t[0], -t[1], -t[2], t[3].get("name", "")))
    return [entry for _score, _complete, _count, entry in scored]
