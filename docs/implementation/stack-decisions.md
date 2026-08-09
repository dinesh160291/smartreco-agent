# Implementation Stack Decisions

**Version:** 1.0

**Status:** Locked

This document records the implementation stack for the SmartReco reference deployment, with the rationale and fallback for each choice.

The architecture specifications (`docs/core/`, `docs/domains/`) are deliberately technology-agnostic; this document is the only place implementation technologies are named. Changing any choice here must require no changes to the architecture — that property is by design, and each entry notes the seam that guarantees it.

---

# The Stack

| Layer | Choice | Fallback |
|---|---|---|
| Backend framework | FastAPI (Python) | — |
| Agent framework | Google ADK | LangGraph |
| Vector store | Chroma (embedded, persistent) | Qdrant |
| Relational database | SQLite (via SQLAlchemy, WAL mode) | PostgreSQL |
| Scheduler | APScheduler (in-process) | Celery Beat / host cron |
| Frontend | Jinja2 SSR + htmx + Pico.css + vanilla-JS tracking client | — |
| AI access | AI Provider Gateway — OpenAI-compatible client, configured entirely from environment (`AI_GATEWAY_BASE_URL`, `AI_GATEWAY_API_KEY`, `AI_GATEWAY_MODEL`) | Any OpenAI-compatible provider by config change |

---

# Rationale by Layer

## Backend — FastAPI

Async-native (fits accept-fast/process-later ingestion, Core 22), first-class Pydantic validation (fits contract-first Runtime Objects), and native ASGI. The API Contracts (Core 16) are framework-neutral; FastAPI implements them.

## Agent framework — Google ADK, LangGraph fallback

The orchestration contract (Core 21) is framework-agnostic: engines are plain Python; the framework only supplies the graph wrapper. ADK expresses the 13-node workflow via Sequential/Loop/custom agents and reaches the AI Provider Gateway through its OpenAI-compatible model support.

**Defined fallback triggers** — switch to LangGraph immediately if ADK resists any of:

1. Routing all model calls through the OpenAI-compatible gateway (base URL + key from environment).
2. Enforcing the policy-bounded evaluate→refine loop (POL-RETR-002).
3. Per-node tracing required by Core 11.

The swap cost is one wrapper module; no engine, contract, or Runtime Object changes.

## Vector store — Chroma (embedded)

- Open-source, no tiers, no account, no quotas; persistence is a local directory (`PersistentClient`).
- Supports the metadata the dual-write contract requires (Product ID, record version).
- Operationally invisible: no server process during development or demo.
- Scale ceiling (millions of vectors, single process) is orders of magnitude above the catalog size.

**Resilience:** per Core 20, the vector store is always fully re-derivable from the relational system of record. A startup reconciliation sweep re-embeds the catalog if the index is missing — ephemeral-disk hosts therefore degrade to a few seconds of startup work, never to data loss.

**Fallback:** Qdrant (self-hosted or managed) behind the same Semantic Retrieval Engine contract — a single adapter class.

## Relational database — SQLite

- Zero-setup single file; ideal for a self-contained, reviewable repository.
- WAL mode + transactional writes + append-only event store satisfy the integrity requirements (Core 22).
- All access through SQLAlchemy: upgrading to PostgreSQL is a connection-string change.

SQLite is the **system of record** — unlike the vector index it is not re-derivable, so deployment must give it a persistent disk (see Deployment Compatibility).

## Scheduler — APScheduler

In-process background scheduler satisfying the "real scheduler, never a manual action" invariant (Core 24) with no additional infrastructure (no broker, no worker fleet). Fires the SCHEDULED Execution Trigger. Fallback for multi-process deployments: Celery Beat or host-level cron hitting the same trigger endpoint — the trigger model doesn't care who fires it.

## Frontend — Jinja2 SSR + htmx + Pico.css + vanilla-JS tracker

Constraints require server-rendered templates plus a JavaScript tracking layer. Within that:

- **htmx** (single script tag) provides live-feeling updates — recommendation feed refresh, admin sync-status badges — via server-rendered partials. No build tooling, no npm.
- **Pico.css** (single stylesheet) provides polished defaults; a small custom stylesheet adds the elements that carry the product: coverage bars, confidence meters, sync-status badges.
- **The tracking client is hand-written vanilla JS** (~80 lines) implementing Core 22 exactly: buffered batches, throttled dwell heartbeats, `sendBeacon` flush on page exit, client UUID event IDs for idempotency, silent failure. It stays dependency-free deliberately — its non-blocking guarantees must not hinge on third-party code.
- **Information architecture is part of the data design:** the product detail page is tabbed (Overview / Pricing / Security & Compliance / Docs & API / Integrations) so that navigation emits the distinct event types the Behavioral Patterns (Domain 02) activate on. The frontend is the signal generator.

Pages: login/register · home (categories + search) · search results · tabbed product detail · comparison view · **cart** · **checkout** (demonstration flow — card format-validated only, never stored, always succeeds; emits PURCHASE_COMPLETED and closes the journey) · order confirmation · recommendations (rendered AAR) · account/digest preferences · admin product list (sync badges) · admin product form · **Reasoning Panel** (live Hypotheses, Requirements, Journey Stage, trigger log — the platform's explainability made visible; **admin-gated with a user selector**, never shown to shoppers, whose explanation surface is the plain-language "why this" on the recommendations page).

Visual details: product identity via **generated monogram tiles** (square, initials on a deterministic per-vendor hue — no logo assets, works for admin-created products); **light/dark theme** with an in-app toggle (CSS custom-property tokens, `data-theme` attribute, defaults to OS preference); product cards use a **header-row layout** (tile + name/vendor line, description full-width below with clear separation).

**Vocabulary rule:** canonical platform IDs (CAP-xxx, REQ-xxx, PROD-xxx, BC/BP codes) never appear on shopper-facing surfaces — users see display names only ("Single Sign-On", never "CAP-001"). IDs appear exclusively on admin screens and the Reasoning Panel, which are deliberately internal-facing.

## Digest delivery channel — Telegram primary, Email optional

The proactive digest (Core 24) ships with the **Telegram adapter as the primary channel**: free bot API, one HTTP POST per delivery, instant and visible — no SMTP setup or deliverability risk. The **Email adapter** is implemented against SMTP environment variables and self-reports unavailable when they are absent. Every delivery additionally renders in-app (Delivery Record + digest AAR view) as observability, guaranteeing the feature is demonstrable independent of external channels. Recipients connect Telegram once via the bot to capture their chat ID (`users.digest_channel` + chat reference).

New environment variables: `TELEGRAM_BOT_TOKEN` (required for the channel), `SMTP_HOST/PORT/USER/PASSWORD` (optional).

## AI access — Provider Gateway

Per Core 15/20 and Decision #034: one OpenAI-compatible client boundary, configured entirely from environment variables, keys never committed. The deployment environment supplies the provider; the codebase names none.

---

# Deployment Compatibility

The stack assumes a **persistent process with a persistent disk**. That assumption determines where it runs unchanged.

| Host class | Examples | Verdict |
|---|---|---|
| Long-running server + volume | Railway, Fly.io, Render (with disk), any VM | ✅ Works unchanged — recommended |
| Long-running server, ephemeral disk | Some free tiers | ⚠️ Chroma self-heals via re-index; **SQLite does not** — attach a volume or switch to managed Postgres |
| Serverless / edge | Vercel, Netlify, AWS Lambda | ❌ Not compatible unchanged — see below |

**Serverless incompatibilities (e.g., Vercel):** SQLite and embedded Chroma require a persistent filesystem (serverless filesystems are ephemeral); APScheduler requires a continuously running process (serverless functions terminate after each request); deferred background processing may be killed after the response.

**Serverless migration path (if ever required)** — every incompatibility swaps at a designed seam, with zero architecture changes:

1. SQLite → managed PostgreSQL (connection-string change via SQLAlchemy)
2. Chroma → managed Qdrant (adapter behind the Core 20 contract)
3. APScheduler → platform cron invoking the SCHEDULED trigger endpoint

**Recommended deployment:** a long-running host with a mounted volume (Railway / Fly.io / Render-with-disk). Local execution remains the primary demonstration environment.

## Moving a Seeded Data Directory Between Machines

The default path needs no data transfer: deploy the code, let the host seed itself on first request, and the catalog is rebuilt from `seed/` through the normal dual-write contract. Transfer is only an optimization — it avoids re-spending embedding calls on the ~250-product catalog.

If the data directory is transferred, **do not copy `smartreco.db` or `chroma/chroma.sqlite3` as files.** Both run in WAL mode, so recent writes live in a `-wal` sidecar that a naive copy either misses or invalidates (a copied `-shm` can cause the WAL to be reset rather than replayed). The failure is silent: the copy is a valid SQLite file that opens with no rows, so the destination looks like a fresh install rather than a corrupt one.

Use one of these instead, with no writer running:

- SQLite's online backup API — `sqlite3.connect(src).backup(sqlite3.connect(dst))` — which is WAL-aware and produces a consistent snapshot; or
- `VACUUM INTO 'destination.db'`; or
- `PRAGMA wal_checkpoint(TRUNCATE)` on the source first, then copy the `.db` alone (never the `-wal`/`-shm`).

The vector store needs both halves: snapshot `chroma/chroma.sqlite3` by the same method **and** copy the HNSW segment directory beside it. If the two disagree, discard the index — it is re-derivable from the relational store by design (Core 20), and a full re-index is the sanctioned repair.

`scripts/validate_retrieval.py` verifies the result on the destination: it fails loudly when the index and the relational store disagree.

---

# Model Configuration

| Purpose | Variable | Default |
|---|---|---|
| Tier 1 generation | `AI_GATEWAY_MODEL` | `openai/gpt-4o-mini` (upgradeable by config) |
| Tier 2 evaluation / refinement | `AI_GATEWAY_MODEL` (shared) | `openai/gpt-4o-mini` |
| Embeddings | `AI_GATEWAY_EMBED_MODEL` | `openai/text-embedding-3-small` (gateway backend) |

## Embeddings Contingency

Gateways focused on chat completions may not serve an embeddings endpoint. The embedding layer is therefore a two-backend abstraction selected by `EMBEDDINGS_BACKEND`:

- **`gateway`** — embeddings via the AI Provider Gateway. Verified by a probe call at setup; preferred when available.
- **`local`** — `all-MiniLM-L6-v2` via Chroma's built-in default embedding function (bundled ONNX runtime): offline, free, no budget impact, retrieval quality equivalent at catalog scale. Makes no external AI call, so the gateway mandate is not bypassed — generation and retrieval-evaluation calls continue to flow through the gateway in either mode.

Backends produce different vector dimensions (1536 vs 384); the collection records its embedding model and index version, and a backend switch triggers the standard full re-index from the relational store (seconds at catalog scale).

---

# Environment Variables

| Variable | Purpose |
|---|---|
| `AI_GATEWAY_BASE_URL` | OpenAI-compatible provider base URL |
| `AI_GATEWAY_API_KEY` | Provider key (mapped from the deployment environment's secret) |
| `AI_GATEWAY_MODEL` | Generation model identifier |
| `AI_GATEWAY_EMBED_MODEL` | Embedding model identifier (gateway backend) |
| `EMBEDDINGS_BACKEND` | `gateway` \| `local` (see Embeddings Contingency) |
| `DATABASE_URL` | SQLAlchemy connection string (default: local SQLite file) |
| `CHROMA_PATH` | Vector store directory (default: `./data/chroma`) |
| `SECRET_KEY` | Session signing |

All secrets live in `.env` (gitignored) locally and in the host's secret store when deployed. Nothing secret is ever committed.

---

# Decision Provenance

| Decision | Made | Basis |
|---|---|---|
| ADK first, LangGraph fallback | 2026-08-07 | Owner preference; protected by the framework-agnostic orchestration contract (Core 21) |
| Chroma | 2026-08-07 | Persistence requirement + zero-ops + re-index guarantee (Core 20) |
| SQLite, APScheduler | 2026-08-07 | Minimal-infrastructure principle for a self-contained reference deployment |
| Frontend stack | 2026-08-07 | SSR constraint + polish/integrity/stability requirements; delegated to engineering |

---
