# SmartReco

**A behavioral AI recommendation platform.** SmartReco watches how a shopper researches software, reasons deterministically about what they need, and delivers persuasive, grounded recommendations — on the site, and proactively by daily digest.

The platform is built on one uncompromising idea: **AI writes the words, never the numbers.** Every ranking, match score, and coverage figure is computed by deterministic engines governed by versioned policies; the language model only proposes retrieval candidates and narrates outcomes. Identical inputs reproduce identical recommendations, and every recommendation traces back through Requirement → Hypothesis → Evidence → the exact clicks that earned it.

---

## What it does

- **Observes behavior, not clicks-as-counters.** A dependency-free tracking client batches page events (views, searches, documentation depth, pricing visits, dwell) and ships them non-blockingly. Breadth of clicking is not intent; depth is — fifteen shallow product views produce *no* recommendations.
- **Reasons deterministically.** Domain-defined behavioral patterns turn events into Evidence; a Confidence Engine turns Evidence into weighted Hypotheses; noisy-OR derivation turns Hypotheses into a prioritized Requirement Profile; capability coverage math ranks products. All thresholds live in a versioned policy catalog (`config/policies.yaml`) — never in engine code.
- **Retrieves semantically, decides deterministically.** A vector index over the product catalog proposes candidates (with an LLM evaluate→refine loop, bounded by policy); deterministic capability matching disposes. Semantic similarity never becomes a match score.
- **Persuades with zero hallucination risk by construction.** The advisor's narrative may use only facts present in the deterministic runtime objects — the user's own observed research, derived requirements, coverage numbers, catalog narratives. Invented social proof, scarcity, and discounts are structurally banned and tested for.
- **Learns across journeys.** Purchases close a journey; closed journeys — and only closed journeys — feed long-term traits, which decay on policy schedules and surface as priors that never override current intent.
- **Comes to you.** A real background scheduler fires a daily digest: eligibility-gated, idempotent per user per day, delivered via Telegram (primary) or email, always rendered in-app. Users with nothing new receive nothing — silence is a feature.

## Architecture at a glance

```
events ──► ingest (202, idempotent) ──► trigger evaluator (debounce · cooldown · budgets)
                                              │ named trigger only
                                              ▼
      13-node workflow (Google ADK graph; 10 nodes deterministic)
      resolve_journey → reason → confidence → requirements → stage
        → decide_retrieve → [retrieve → evaluate → refine]* → match
        → readiness gate → clarify | generate → persist/deliver
                                              │
             deterministic Recommendation Package + persuasive AAR
```

- **Two-tier AI boundary.** Tier 1 = narrative generation. Tier 2 = embeddings + retrieval evaluation/refinement, fenced inside the retrieval stage. No AI call exists outside these tiers; no model call ever gets tools. Every call flows through one environment-configured, provider-agnostic gateway.
- **Two-speed pipeline.** Deterministic nodes may run on every trigger; AI nodes run only on material change or cache miss, within per-user daily budgets. Budget exhaustion degrades gracefully — deterministic service never stops.
- **Dual-write catalog.** The relational store is the system of record; the vector index is always re-derivable (PENDING → SYNCED with bounded reconciliation). A half-synced product is never half-visible.
- **Everything observable.** Every workflow run — including every decision *not* to run — writes a trace row: trigger, gates, per-node records, policy version. The admin Reasoning Panel shows live hypotheses, requirements (including held ones), stage, traits, and the trigger log.

The core platform is domain-agnostic; all software-buying knowledge (patterns, requirements, capability taxonomy, product profiles, mappings) lives in a swappable Domain Pack.

## Feature status

| # | Distinguishing feature | Status |
|---|---|---|
| D1 | Explicit structured agent workflow (13-node graph, bounded refinement loop) | ✅ ADK-wrapped, framework-swappable |
| D2 | Scheduled proactive delivery (real scheduler, never a manual action) | ✅ Daily digest, Telegram + email + in-app |
| D3 | End-to-end workflow observability | ✅ Per-run node records, gates, budgets, skips; Reasoning Panel |
| D4 | Retrieval polish (evaluate → refine → deterministic re-rank) | ✅ Policy-bounded loop, exact-rational ranking |

All twelve mandatory platform requirements (auth/roles, relational schema, admin CRUD, dual-write, non-blocking tracking, event storage, behavioral reasoning, grounded RAG, persuasive narrative, stored/refreshed recommendations, trigger-and-cache efficiency, single gateway) are implemented — the full map is in `docs/requirements-compliance.md`.

## Setup

Requires **Python 3.11** and an OpenAI-compatible AI gateway (any provider; configured entirely by environment).

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate elsewhere)
pip install -r requirements.txt
pip install -e .

copy .env.example .env            # then fill in:
#   AI_GATEWAY_BASE_URL / AI_GATEWAY_API_KEY / AI_GATEWAY_MODEL / AI_GATEWAY_EMBED_MODEL
#   EMBEDDINGS_BACKEND=gateway|local   (run: python scripts/probe_gateway.py to decide)
#   SECRET_KEY, optional TELEGRAM_BOT_TOKEN, optional ADMIN_EMAIL/ADMIN_PASSWORD

uvicorn apps.web.main:app --port 8000
```

First startup seeds the capability taxonomy and the demo catalog (~250 products — 125 real-world and 125 fictional, all with editorial, illustrative capability profiles; not vendor claims) and starts the digest scheduler. Set `ADMIN_EMAIL`/`ADMIN_PASSWORD` to get an admin account for the catalog screens and the Reasoning Panel.

### Tests

```bash
pytest            # 139 tests: engine math, policies, stories 1–12, seed integrity
```

Automated tests run against a stubbed gateway and a fixed 10-product fixture with exact-number acceptance assertions (e.g., a security-focused journey must yield 81% / 70% / 58% coverage in that order). Time-based behavior (decay, dormancy, closure) is tested with a simulated clock. `scripts/smoke_live_aar.py` and `scripts/eval_slice.py` are the only live-gateway touchpoints.

## Repository map

| Path | Contents |
|---|---|
| `src/smartreco/` | Core platform: engines (pure functions), pipeline, orchestration, gateway, retrieval, delivery, policy loader |
| `src/smartreco/domain/` | Software Buying Domain Pack (patterns, catalogs, mappings) |
| `apps/web/` | FastAPI app: SSR pages, tracking client, admin, Reasoning Panel |
| `config/policies.yaml` | Policy Catalog — every business threshold, versioned |
| `seed/products.json` | Demo catalog (build-time generated, reviewed, committed) |
| `docs/` | The full platform specification: core chapters, Domain Pack, implementation decisions, 12 acceptance stories |
| `tests/` | Signature + acceptance tests (stubbed gateway, simulated clock) |

## Deployment

Long-running host with a persistent disk (Railway / Fly.io / Render-with-volume class). SQLite is the system of record and needs the volume; the vector index self-heals by re-indexing from it. Serverless is incompatible unchanged (persistent filesystem + in-process scheduler); the designed migration seams (managed Postgres, managed vector store, platform cron) are documented in `docs/implementation/stack-decisions.md`.
