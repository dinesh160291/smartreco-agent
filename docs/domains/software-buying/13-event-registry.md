# Event Registry — Software Buying

**Domain Pack artifact 7** (`knowledge/architecture/domain-pack-contract.md`); the Domain Enumeration referenced by Core 17.

Moved here from Core 22, which already stated that the active Domain Pack owns this vocabulary while hosting the table itself. Core 22 keeps the ingestion mechanism — buffering, batching, idempotency, the client tracking contract — and points here.

**Closed registry.** An event with a type outside this table fails structural validation. New types are added only through a Domain Pack version. Signal class is domain knowledge consumed by Execution Triggers (Core 23): it decides which events can trigger reasoning (HIGH/MEDIUM) and which only enrich it (LOW).

Transcribed in the reference implementation as `EVENT_TYPES` in the pack's `enums.py` — amend the table and the transcription together.

---

| Interaction | Event Type | Signal class |
|---|---|---|
| Page / product detail view | PRODUCT_VIEWED | High |
| Search submitted | SEARCH | High |
| Category browsed | CATEGORY_VIEWED | Medium |
| Pricing page viewed | PRICING_VIEWED | High |
| Documentation / security page viewed | DOCUMENTATION_VIEWED / SECURITY_VIEWED | High |
| Product comparison | COMPARISON_STARTED | High |
| Time on page (heartbeat) | DWELL | Low |
| Click on recommendation | RECOMMENDATION_CLICKED | High |
| Trial / demo actions | TRIAL_STARTED / DEMO_REQUESTED | High |
| Product added to cart | ADD_TO_CART | High |
| Checkout begun | CHECKOUT_STARTED | High |
| Purchase completed | PURCHASE_COMPLETED | High |

Raw scroll and hover activity is not tracked as discrete events; dwell is sampled via heartbeat (Core 22, POL-TRACK-002).

## Every type must be reachable

A type in this table is a promise that the platform can observe that behaviour. Three of the fourteen were unobservable in the reference implementation until Decision #044 — nothing emitted `DEMO_REQUESTED` or `RECOMMENDATION_CLICKED`, and every pane but Security cleared its dwell topic, so BP-011's demo trigger and BP-003's dwell branch could not fire from a browser at all. Adding a row therefore costs a surface that emits it, or an explicit note here that it is server-emitted. `tests/test_ui_tracking_contract.py` enforces it as a ratchet.

Server-emitted, with no clickable surface by design:

| Event Type | Emitted by |
|---|---|
| PURCHASE_COMPLETED | the checkout route, after an order is written |
| DWELL | the tracking client's heartbeat, not a click (POL-TRACK-002) |

## `PRICING_VIEWED.tier` — stated, never assumed

`tier` carries the shopper's own statement of intent and is **absent** when they have not made one. Opening the pricing surface emits the event with no `tier`: pricing was read, which is true. A `tier` appears only when the shopper opens a specific plan — `personal` or `enterprise` in the reference deployment's two-tier layout.

This matters because both branches of BP-002 key on it: `tier == "enterprise"` is enterprise-evaluation evidence, while repeated `individual` / `free` / `personal` views are *contradicting* evidence. A surface that stamped every pricing view as `enterprise` would manufacture the first and make the second unreachable. Tier-less events still count toward BP-009 Commercial Evaluation, which cares that pricing was consulted at all.

## `SEARCH.result_count` and `.fallback_used` — descriptive, never evidence

`SEARCH` carries `query` — what the shopper typed, verbatim and unexpanded. That has not changed and must not: buyer-shorthand expansion (`sso` → `single sign on`) is retrieval-side only, so the reasoning engines never learn vocabulary the shopper did not use.

Decision #089 added two fields beside it. `result_count` is how many products the page showed; `fallback_used` says whether the answer came from the semantic fallback rather than the lexical path.

**No pattern evaluator may read either.** They exist for the Reasoning Panel and for admin diagnostics, and the prohibition is the point rather than an implementation detail. A `PRODUCT_VIEWED` carries a category and feeds a subject pattern because *the shopper chose that product*; a result list is the **platform's own proposal**. If a proposal became evidence, the platform would infer intent from its own guess and then recommend against it — a self-confirming loop, and a breach of the law that says AI proposes candidates and never produces requirements. The shopper's next act still counts as it always did: click a fallback result and that `PRODUCT_VIEWED` is evidence, like any click.

`tests/test_search_fallback.py` holds this as a ratchet over both the platform and Domain Pack evaluators, because a rule of this kind is only worth something if a later evaluator cannot quietly reach for a field that happens to be sitting there.

**A second-order effect worth watching.** Pattern term sets are keyword vocabularies. A search box that visibly understands sentences teaches shoppers to type sentences, and a sentence rarely contains the keywords — so the search that finally *works* for the shopper can be the search that tells the platform nothing. The platform would get better at finding and worse at understanding at the same time. The placeholder is deliberately kept keyword-shaped, and the drift is to be measured rather than assumed (semantic-search-spec §5.2).
