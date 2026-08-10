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
