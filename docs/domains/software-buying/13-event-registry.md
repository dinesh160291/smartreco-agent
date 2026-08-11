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
