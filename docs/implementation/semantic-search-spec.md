# Semantic Search Fallback — Specification

**Status: proposed, not implemented — but the shipping gate has been run.** No
code, policy or event-registry change has landed. §4's similarity floor is
**measured** (`scripts/measure_search_floor.py`, in the repository so the number
is reproducible); §5.2's vocabulary-drift eval is the one measurement still
outstanding, and it can only run once the feature exists. This document is the decision `ui-design-spec.md` §4.7a defers when
it says reusing the vector index on the search surface "would be a new use of
that seam and requires its own decision".

**Authority.** On implementation this document's rules move into their permanent
homes — §4.7a for the surface, Core 20 for the engine, Core 10 for the policies —
and this file becomes the record of why. It is not a second authority for
anything already specified elsewhere.

**Domain neutrality.** This is a platform document (Decision #040), so the rules
below name no Domain Pack identifier. Example queries are drawn from the active
pack purely to make the argument concrete; nothing in the design depends on
them, and `tests/test_domain_boundary.py` holds this file to it — it caught a
pattern ID in the first draft.

---

## 1. The problem

Catalog search is lexical and ANDed: every typed token must match a product
name, capability name, category, vendor or prose. That is deliberate, and §4.7a
gives the reasons — same query, same results, explainable without a model.

It has one failure mode, and it is the one that matters most for a buyer who
does not yet know the vocabulary. A shopper who types **"stop people sharing
passwords"** gets nothing. Every word is ordinary English; none of it appears in
the catalog. The empty state is correct — the platform refuses to guess (§6) —
but the shopper wanted identity products and the catalog has twenty of them.

The vector index already holds the answer. It is built from the Embedding
Document of every product (Core 20) and it is queried on exactly this kind of
loose, intent-shaped text. Today it is reserved for the Semantic Retrieval
Engine's behavioural Candidate Sets.

## 2. The shape

**Lexical first. Vector only on a lexical miss. Never blended.**

```
query → lexical search (unchanged)
          ├─ ≥ 1 result  → show them. No embedding, no AI, no cost. Done.
          └─ 0 results   → embed the query, query the vector index,
                           keep hits at or above the similarity floor
                             ├─ ≥ 1 hit → show them, labelled as inexact
                             └─ 0 hits  → today's empty state, unchanged
```

Three properties fall straight out of that ordering, and they are the reason for
it:

- **Every query that works today keeps working, identically.** The fallback is
  unreachable unless lexical returns nothing, so no existing result set moves.
- **Cost is bounded by how often search fails**, not by how often it is used.
- **Degradation is free.** Every failure path — gateway down, budget spent,
  index empty, backend error — lands on the empty state the shopper would have
  seen anyway. There is no error page to design and nothing to retry (Law 5).

Not blending is a decision, not an omission. Merging a lexical list with a
similarity list requires a rule for interleaving two incomparable scores, and
that rule would be neither explainable nor stable. Falling back wholesale means
the page is always showing one kind of answer, and always says which.

## 3. Honesty on the surface

A fallback result set is **not** a search result set, and the shopper must never
have to guess which they are looking at.

The result-count line (§4.7a, `role="status"`) reads:

> No exact matches for "stop people sharing passwords" — showing 6 products with
> related capabilities.

Rules:

- The wording never claims a match. "Related capabilities" is a claim the
  platform can support from the Embedding Document; "best match" is not.
- Ordering is by similarity, then by Product ID, so the list is replayable.
- Canonical IDs never appear (Law 10). Similarity scores are **not** shown to
  shoppers — they are an internal quantity with no meaning to a buyer, and
  printing them invites the reading that 0.62 is a 62% fit. They belong in the
  admin-gated Reasoning Panel.
- If nothing clears the floor, the existing empty state renders unchanged,
  suggesting a capability or a category chip. **A fallback that finds nothing
  must not degrade into a list of unrelated products** — that is the exact
  behaviour §4.7a already forbids, and the similarity floor is what enforces it.

## 4. The similarity floor — MEASURED

The floor is what separates this feature from guessing, so it is the one number
that had to be **measured before it was set**.

Method, now in `scripts/measure_search_floor.py` and reproducible: build a
throwaway index from the current seed catalog with the configured embedding
backend, then run a fixture of natural-language queries in two classes —
*answerable* (work the capability taxonomy genuinely covers) and *unanswerable*
(work no business software catalog does) — and find the floor that admits the
first class and rejects the second. Labels are fixed before the run; reclassify
a query after seeing its score and the measurement becomes a rationalisation.

### 4.1 Result: 22 queries, gateway backend, 250 products

**All 22 fixture queries miss lexically**, so all 22 would reach the fallback —
the fixture is testing the right path.

**Retrieval quality is not the problem. It is excellent.** All twelve answerable
queries returned the correct product area at rank 1, and usually the whole top
three:

| Query | Top three |
|---|---|
| stop people sharing passwords | 1Password, LastPass, FableKey |
| prove to an auditor what everyone did | OneTrust, Vanta, Drata |
| our designers need somewhere to put mockups | Figma, Canva, Notion |
| we keep losing track of who is doing what this week | Monday.com, Wrike, Todoist |
| find out why the website went down last night | NovaWatch, QuillWatch, FableWatch |
| make sure new starters have everything on day one | BrightCrew, VertexCrew, PaceCrew |

**The floor is the problem.** Unanswerable queries do not score low — they score
*plausibly*, because an embedding index has no way to say "I don't know". "Book
a meeting room" returns Calendly at **-0.386**, above ten of the twelve genuine
queries. "Play some music while I work" returns three Work Management products
at -0.518. The two classes overlap in the band **[-0.547, -0.386]**.

**The §4 gate as originally written therefore fails: there is no clean
separation.** What exists instead is a precision/recall curve:

| Floor | Answerable admitted | Unanswerable admitted |
|---|---|---|
| -0.30 | 4/12 | **0/10** |
| -0.35 | 5/12 | **0/10** |
| **-0.38** | **7/12** | **0/10** |
| -0.40 | 7/12 | 1/10 |
| -0.50 | 11/12 | 3/10 |
| -0.547 | 12/12 | 6/10 |

(Similarity is `1 - distance`, so these are negative numbers on the same scale
POL-RETR-002 already uses. Note the shape: recall is bought steeply in wrong
answers past -0.40.)

### 4.2 Verdict

**The feature ships, at a precision-first floor of -0.38, and only because its
failure mode is silence.** At that floor no unanswerable query in the fixture
produces any result at all, and seven of twelve genuine ones get help. The other
five fall back to today's empty state — not a regression, just an absence.

That is the reading the original gate was protecting: it forbade *misleading*,
not *incomplete*. A feature that helps with roughly half of the queries it sees
and misleads on none is worth having; the same feature at -0.50 would answer
"best pizza near the office" with a CRM, and that one is worse than nothing.

**-0.38 is fitted to this fixture's closest negative and has only 0.005 of
margin.** It should be re-measured whenever the catalog changes materially, and
a deployment that prefers caution should take -0.35 and lose two queries.

### 4.3 Two findings that change other parts of this spec

**The floor is backend-specific, so it is a deployment value.** The same fixture
against the local backend gives ten of twelve correct areas (it puts an
onboarding query in Customer Support and a workload query in HR) and a much
wider overlap: its precision-clean floor is about **-0.33**, admitting only four
of twelve. One number cannot serve both. The floor therefore belongs to the
deployment exactly as `EMBEDDINGS_BACKEND` does — one `min_similarity` in
policy, measured for the configured backend with the script above, and
re-measured if the backend changes. No per-backend policy structure; the
deployment already declares its backend.

**Similarity is not bit-stable.** Embedding the same query twice moved scores by
around 3×10⁻⁴ ("book a meeting room" gave -0.3861 and -0.3858 on consecutive
runs). Two consequences: never fit the floor to within a rounding error of a
sample value, and §3's tie-break on Product ID is load-bearing rather than
decorative — without it, near-equal hits could reorder between identical
searches.

## 5. What evidence a `SEARCH` event produces

**This section is why the feature needed a spec rather than an afternoon.**

### 5.1 The rule: nothing the platform retrieved is ever evidence

The `SEARCH` event continues to record **only what the shopper typed**, verbatim
and unexpanded, exactly as today. Two descriptive fields may be added —
`result_count` and `fallback_used` — and **no pattern evaluator may read
either**. They exist for the Reasoning Panel and for admin diagnostics.

The products the fallback returned are **not** evidence of anything.

The distinction is between two acts. A `PRODUCT_VIEWED` carries a category and
feeds a subject pattern because **the shopper chose that product**. A result
list is the **platform's** proposal. If a proposal became evidence, the platform
would infer intent from its own guess and then recommend against it — a
self-confirming loop, and a direct breach of Law 1, which says AI proposes
candidates and never produces requirements.

The shopper's own next act still counts, unchanged: click a fallback result and
that `PRODUCT_VIEWED` is evidence, as any click is.

### 5.2 The real risk: the box changes what people type

Evidence is not lost by the fallback. It is lost by what the fallback *teaches*.

A Domain Pack recognises a subject from a **term set** — a short keyword
vocabulary its patterns match against the typed query. Give a shopper a box that
visibly understands sentences and they will write sentences, and a sentence
rarely contains the keywords. In the active pack, the identity subject is
recognised from shorthand a buyer types when they already know the category;
"stop people sharing passwords" contains none of it. The search that finally
*works* for the shopper is the search that stops telling the platform anything.

**The platform would get better at finding and worse at understanding, at the
same time, and nothing in the current test suite would notice.**

Three responses, in order of preference:

1. **Keep the affordance keyword-shaped.** The placeholder stays "Search
   products, capabilities, categories…". The fallback is a safety net, not an
   invitation to converse.
2. **Measure the drift.** Add an eval case that runs the natural-language
   fixture from §4 through the pattern evaluator and reports which subjects go
   dark. It reads the pack's term sets through `smartreco.domain.active` rather
   than naming any of them, so it stays true when the pack changes. This is the
   check that would have caught the problem, so it ships with the feature, not
   after it.
3. **Do not "fix" it by writing the expansion into the event.** The existing
   rule — expansion is retrieval-side only, the event records what was typed —
   exists so the engines never learn vocabulary the shopper did not use.
   Overturning it is a separate decision needing its own evidence, and taking it
   quietly as a side effect of a search feature is how a platform ends up
   reasoning about words nobody said.

### 5.3 An argument, offered as an argument

A lexical miss means at least one typed token matched nothing anywhere in the
catalog. Queries containing pattern vocabulary generally do *not* miss — `sso`
expands through the alias table and matches — so the fallback should fire mostly
on queries the patterns could not read in the first place, making the evidence
delta close to nil.

That is reasoning, not measurement, and this project has been wrong twice by
reasoning where it should have measured. §5.2's eval case is what settles it.

## 6. Bounds, budget and cost (Laws 5 and 9)

| Bound | Why |
|---|---|
| Fallback fires only at **zero** lexical results | The whole cost model |
| `top_k` hits from the index | POL-RETR-001's shape, own value |
| Query truncated to `max_query_chars` before embedding | Unbounded user text must never reach the gateway |
| Identical normalized queries cached for `cache_ttl_seconds` | Determinism within the window, and a spam-typing shopper costs one call |
| **Own** daily cap per signed-in user, separate from POL-TRIG-003 | See below |
| **Per-session** cap for signed-out visitors (§12) | No account to bill, so the session is the unit |
| Cap exhausted → empty state, silently | Never an error page, never a retry storm |

**The separate cap matters.** If search embeddings drew on the Tier-2 reasoning
budget, a shopper who typed a lot of failed searches would degrade their own
recommendations — the platform's actual product — as a side effect of using the
search box. The two budgets are for different things and must not compete.

**The signed-out cap is counted per session, not per visitor**, and the
difference is worth being honest about: a session is cheap to create, so the cap
bounds the cost of one visitor's *browsing*, not of one determined attacker.
That is the right bound for the threat it is actually facing — a curious
newcomer typing questions — and it is the whole of what it claims. If the demo
is ever exposed publicly, the abuse question is answered at the edge with rate
limiting, not by this policy. On session expiry the count goes with it, by
design: the session is the budget's lifetime.

A signed-out visitor's counter therefore lives on the session record, and the
signed-in one on the user; the moment a visitor registers or logs in, the
per-user cap governs and the session count is abandoned rather than carried
across. Simpler than reconciling two ledgers, and the direction of the error
favours the shopper who has just committed to an account.

**One cost note that changes the picture.** Under `EMBEDDINGS_BACKEND=local` the
embedding is computed in-process and there is no gateway call, no network and no
budget to exhaust. The entire budget question above applies only to the gateway
backend. The feature must be correct under both, and the tests must cover both.

Law 9 ("no AI call per raw event") is respected: the embedding is not triggered
by event processing at all. It happens in the request the shopper initiated, for
the page they are waiting on, and only when the deterministic path found
nothing.

## 7. Reuse, not a new seam

`retrieval.retrieve_candidates(db, chroma, backend, query_document, policies)`
already takes a text document and returns scored candidates. The fallback passes
the shopper's normalized query as that document. No new abstraction, no second
vector path, and the dual-write contract is untouched because this is a **read**
(Law 8).

## 8. Policies to add

New IDs, mirrored into `config/policies.yaml`, with a `catalog_version` bump:

| ID | Params |
|---|---|
| `POL-SRCH-001` Catalog search fallback | `lexical_min_results`, `top_k`, `min_similarity` = **-0.38**, measured (§4), `max_query_chars` |
| `POL-SRCH-002` Search embedding budget | `searches_per_user_per_day`, `searches_per_anonymous_session`, `cache_ttl_seconds` |

Policy Catalog v1 (`docs/core/10`) is the authority and `config/policies.yaml`
mirrors it; both move in the implementing commit, or `test_policy_catalog.py`
correctly goes red.

## 9. Documents the implementing commit must amend

One commit, per the change-control rule: code, tests, and every document it
contradicts.

- `docs/implementation/ui-design-spec.md` §4.7a — replace the deferral with the
  behaviour, and add the fallback result line to the §4.7a copy rules
- `docs/core/20-…` — a second, read-only consumer of the vector index, and the
  fact that it is not the Semantic Retrieval Engine
- `docs/core/10-decision-policies.md` + `config/policies.yaml` + version bump
- `docs/domains/software-buying/13-…` event registry — `result_count` and
  `fallback_used`, both marked *not read by any evaluator*
- `docs/core/decision-log.md` — the architectural entry
- This file — status changed from proposed to shipped
- `scripts/measure_search_floor.py` already carries the fixture and method; it
  is re-run whenever the catalog or the embedding backend changes materially

## 10. Testing contract

Each test names what it pins. Against the stubbed gateway, and against both
embedding backends.

1. **A query with lexical results never embeds.** Sabotage: make the embedding
   backend raise; a normal search must still pass. This is the cost model.
2. **A zero-result query embeds once** and returns hits at or above the floor.
3. **Below-floor hits are dropped**, and an all-below-floor query renders the
   existing empty state — not a shortened list.
4. **Ordering is replayable** — same query, same order, similarity then
   Product ID.
5. **Gateway failure, budget exhaustion and an empty index each land on the
   empty state**, with a 200 and no traceback (Law 5). Three separate tests;
   they fail for different reasons.
6. **The `SEARCH` event records the typed query verbatim** — not the expansion,
   not the normalized form, not the retrieved product IDs.
7. **No pattern evaluator reads `result_count` or `fallback_used`.** A ratchet
   over the evaluator source, in the shape of the domain-boundary test.
8. **The query is truncated before it reaches the backend** — asserted at the
   backend seam, not the caller.
9. **Vocabulary rule** — no canonical IDs and no similarity scores on the
   shopper surface; both present in the admin Reasoning Panel.
10. **The drift eval** (§5.2): natural-language fixture → pattern evaluator →
    which subjects go dark. Reported, and eval-caveat rules apply — a failing
    case must fail three times to count.

## 11. Deliberately out of scope

- **Semantic ranking of successful searches.** Lexical ordering stays exactly as
  §4.7a specifies. This feature only handles the empty case.
- **Query rewriting, spell correction, "did you mean".** Each is a separate
  decision about putting words in the shopper's mouth.
- **Personalising search by journey.** The search box answers "what did this
  person ask for". Mixing in "what does their behaviour imply" is what For-You
  is for, and merging the two would make the search box's results depend on
  invisible state — unexplainable, and unreplayable by an admin.
- **Search-as-you-type.** An embedding per keystroke, with none of the bounds
  above surviving contact.

## 12. Resolved — the fallback fires for signed-out visitors

**Decided (user, 2026-08-14): yes, bounded by a per-session cap.**

The shopper who most needs help with vocabulary is the one who has not committed
to anything yet, and gating the feature behind registration would withhold it
from exactly that person. The per-user budget in §6 has no account to bill, so
the session becomes the unit: `searches_per_anonymous_session`, held in
POL-SRCH-002 alongside the signed-in cap, with the counter on the session record
and the mechanics in §6.

What this costs, stated rather than discovered later: a session is cheap to
create, so the cap bounds one visitor's browsing rather than one attacker's
persistence. That is the threat it is scoped to. A publicly exposed deployment
answers abuse at the edge with rate limiting; this policy does not pretend to.

The tests owed by this decision, added to §10:

11. **A signed-out visitor gets the fallback**, and the count lands on the
    session rather than being skipped for want of a user.
12. **The per-session cap is enforced**, and exhausting it renders the empty
    state — not an error, and not a prompt to register.
13. **Registering mid-session moves the visitor onto the per-user cap**, with
    the session count abandoned rather than carried.
