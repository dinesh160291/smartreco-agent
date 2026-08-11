# Data Model

**Version:** 1.0

**Status:** Locked

This document defines the concrete persistence design for the SmartReco reference deployment: the relational schema (SQLite via SQLAlchemy), the vector index (Chroma), and the policy configuration file. It implements the entities defined by the architecture — the Runtime Object Model (Core 18), Event Schema (Core 13), Product Catalog (Core 14), and Product Knowledge Store (Core 20) — without redefining any of them.

Companion document: `stack-decisions.md`.

---

# Design Decisions

## D1 — Hybrid normalization

Join tables for what the platform **queries**; JSON columns for what it **snapshots**.

- Queried relationships (e.g., product ↔ capability, hypothesis ↔ evidence) are normalized rows, because engines filter on them.
- Published Runtime Objects (Requirement Profiles, Recommendation Packages, AARs, Candidate Sets) are sealed documents read back whole — their contents live in JSON columns, keeping each object atomic and its immutability trivial.

Rule of thumb: *engine filters by it → rows; sealed document → JSON.*

## D2 — Immutability by convention, enforced in the repository layer

Runtime-object tables expose **insert-only** repository helpers; no UPDATE path exists in code. Mutable state is limited to exactly the entities the architecture declares living: `users`, `products` (+ sync status), `sessions`, `journeys` (lifecycle), `behavioral_traits`. Everything else is append-only; corrections and evolution create new versions, never edits.

## D3 — Policies in versioned YAML

`config/policies.yaml` mirrors Policy Catalog v1 (Core 10). Engines consume policies through a single loader; every workflow run records the `policy_version` it used. Git versions the values. Migration to a database table is possible later without engine changes.

---

# Schema Overview

```text
        Identity & Catalog (mutable)                Behavioral Spine (append-only)
┌─────────────┐  ┌──────────────────────┐   ┌────────┐ ┌──────────┐ ┌──────────┐
│   users     │  │ capabilities (seed)  │   │ events │→│ sessions │→│ journeys │
└─────────────┘  └─────────┬────────────┘   └───┬────┘ └──────────┘ └────┬─────┘
                           │                    ▼                        │
┌─────────────┐  ┌─────────┴────────────┐   ┌──────────┐  ┌─────────────┴──┐
│  products   │──│ product_capabilities │   │ evidence │──│ hypotheses (v) │
└──────┬──────┘  └──────────────────────┘   └──────────┘  └───────┬────────┘
       │ dual-write                                               │
       ▼                                Decision Spine (immutable, versioned)
┌─────────────┐   ┌──────────────────────┐  ┌────────────────┐  ┌──────────────┐
│ Chroma index│   │ requirement_profiles │→ │ candidate_sets │→ │ rec_packages │
└─────────────┘   └──────────────────────┘  └────────────────┘  └──────┬───────┘
                  ┌────────────────┐  ┌───────────────────┐            ▼
                  │ journey_stages │  │ behavioral_traits │   ┌────────────────┐
                  └────────────────┘  └───────────────────┘   │ advisory_resp. │
                  ┌────────────────┐  ┌───────────────────┐   └────────────────┘
                  │ workflow_runs  │  │ delivery_records  │
                  └────────────────┘  └───────────────────┘
```

---

# Tables

## Identity & Catalog (mutable)

### users

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| email | TEXT UNIQUE NOT NULL | |
| password_hash | TEXT NOT NULL | bcrypt-class hash; never plaintext |
| role | TEXT | `user` \| `admin` (checked at API layer) |
| digest_opt_in | BOOLEAN default false | |
| digest_channel | TEXT nullable | `EMAIL` \| `TELEGRAM` |
| telegram_chat_id | TEXT nullable | chat reference captured when the user connects the bot (stack-decisions §Digest delivery) |
| created_at | TIMESTAMP | |

### capabilities (seeded taxonomy — read-only at runtime)

| Column | Type | Notes |
|---|---|---|
| capability_id | TEXT PK | identifier from the active Domain Pack's Capability Catalog |
| name | TEXT | |
| domain | TEXT | Capability Domain |
| business_value_narrative | TEXT | consumed by AAR generation |

Seeded from the Domain Pack at startup. Admin APIs validate product capability selections against this table; unknown IDs are rejected (Core 14).

### products

| Column | Type | Notes |
|---|---|---|
| product_id | TEXT PK | `PROD-xxx` |
| name, vendor, category | TEXT | |
| description, business_purpose | TEXT | part of the Embedding Document |
| business_value_narrative | TEXT | |
| price_note | TEXT nullable | display metadata; never used in matching |
| record_version | INTEGER | bumped on every edit; carried into vector metadata |
| sync_status | TEXT | `PENDING` \| `SYNCED` \| `FAILED` (Core 17/20) |
| deleted_at | TIMESTAMP nullable | **soft delete** — preserves traceability of historical recommendations |
| created_at, updated_at | TIMESTAMP | |

### product_capabilities (join — queried by ranking)

| Column | Type |
|---|---|
| product_id | TEXT FK → products |
| capability_id | TEXT FK → capabilities |

PK (product_id, capability_id). Rewritten atomically with the product row inside the dual-write transaction.

### cart_items (mutable)

user_id FK · product_id FK · added_at. PK (user_id, product_id) — one cart per user, no quantities. Cleared on checkout.

### orders / order_items (append-only)

`orders`: order_id PK · user_id FK · journey_id FK · created_at. `order_items`: order_id FK · product_id FK · price_note TEXT. Checkout is a demonstration flow — card details are format-validated and **never stored**; no payment fields exist in the schema. Order creation emits PURCHASE_COMPLETED through the standard event pipeline, which closes the journey per POL-JRES-003 and feeds the Learning Engine.

---

## Behavioral Spine (append-only)

### events — the immutable behavioral system of record

| Column | Type | Notes |
|---|---|---|
| event_id | TEXT PK | **client-generated UUID → idempotency** (duplicate inserts ignored) |
| user_id | FK → users | |
| session_id | TEXT | client-generated |
| journey_id | TEXT FK nullable | null until Journey Resolution assigns it |
| event_type | TEXT | Domain Pack enumeration (Core 22 table) |
| signal_class | TEXT | `HIGH` \| `MEDIUM` \| `LOW` |
| metadata | JSON | type-specific payload (Core 13) |
| ts | TIMESTAMP | client event time — processing orders by this |
| received_at | TIMESTAMP | server arrival time |
| processed_at | TIMESTAMP nullable | set when behavioral reasoning consumed it; the event row itself is never mutated otherwise |

Batch-inserted. No UPDATE except `journey_id` assignment and `processed_at` stamping (the two processing-state fields the architecture explicitly separates from event content).

### sessions

session_id PK · user_id · journey_id · started_at · last_event_at. Closed by the session-timeout policy.

`session_id` is **not** the id the client sent: ingestion namespaces the client's value by the authenticated user (`u{user_id}:{client_session_id}`) before storing or matching it, so a single browser tab reused by two accounts produces two session rows rather than one shared one (Core 22 § Identify honestly; Decision #043). Nothing parses the key — treat it as opaque.

### journeys

journey_id PK · user_id · lifecycle (`NEW/ACTIVE/DORMANT/CLOSED/ARCHIVED`) · context · outcome nullable · created_at · closed_at nullable.

### journey_transitions (append-only log)

journey_id · from_state · to_state · reason · policy_version · ts. Makes lifecycle history replayable.

### evidence (immutable)

| Column | Type | Notes |
|---|---|---|
| evidence_id | TEXT PK | `BE-…` |
| journey_id | FK | |
| pattern_id | TEXT | `BP-xxx` (Domain 02) |
| strength | TEXT | Weak/Medium/Strong/Very Strong |
| supporting_event_ids | JSON | lineage to events |
| concept_ids | JSON | `BC-xxx` supported |
| contradicts_concept_ids | JSON | `BC-xxx` contradicted (patterns' Contradicting rules; drives POL-CONF-003 via the `CONTRADICTING` relation on `hypothesis_evidence`) |
| explanation | TEXT | deterministic |
| created_at | TIMESTAMP | |

### hypotheses (append-only versions)

| Column | Type | Notes |
|---|---|---|
| hypothesis_id | TEXT | stable across versions |
| version | INTEGER | PK (hypothesis_id, version); current = MAX(version) |
| journey_id | FK | |
| concept_id | TEXT | `BC-xxx` |
| status | TEXT | Created/Strengthened/Stable/Weakened/Retired |
| confidence | REAL | written only by the Confidence Engine |
| confidence_explanation | TEXT | |
| created_at | TIMESTAMP | |

### hypothesis_evidence (join — queried by confidence)

hypothesis_id · evidence_id · relation (`SUPPORTING` \| `CONTRADICTING`).

### behavioral_traits (mutable long-term profile)

user_id · trait_name · strength REAL · reinforcement_count INTEGER · last_reinforced TIMESTAMP · decay_explanation TEXT. PK (user_id, trait_name). Written only by the Learning and Decay engines.

---

## Decision Spine (immutable, versioned Runtime Objects — JSON snapshots)

### requirement_profiles

rp_id PK · journey_id · version · requirements JSON `[{req_id, confidence, priority, explanation}]` · created_at.

### journey_stages

journey_id · version (PK pair) · stage · confidence REAL · explanation · created_at.

### candidate_sets

cs_id PK · journey_id · rp_id FK · query_document TEXT · params JSON (top_k, embed_model, index_version) · candidates JSON `[{product_id, similarity, record_version}]` · refinement_history JSON · created_at.

`similarity` is `1 − distance` per Chapter 20's definition — in the reference deployment `2 × cosine − 1`, so values are in [−1, 1] and negative entries are expected for weak candidates. Ordering is unaffected.

### recommendation_packages

rpkg_id PK · journey_id · rp_id FK · cs_id FK nullable · entries JSON `[{product_id, rank, overall_coverage, per_requirement JSON, missing_capability_ids}]` · readiness (`READY/NOT_READY`) · constraints JSON · policy_version · created_at.

### advisory_responses

aar_id PK · rpkg_id FK · surface (`ONSITE` \| `DIGEST`) · prompt_version · model_id · sections JSON (executive summary, persuasive narrative, trade-offs, next actions, …) · created_at. Unique (rpkg_id, prompt_version, surface) — the AAR cache key (POL-CACHE-001) enforced by constraint.

### delivery_records

id PK · user_id · channel · aar_id FK · status (`SENT/FAILED/SKIPPED`) · reason · digest_window TEXT · created_at. Unique (user_id, digest_window) — idempotent delivery by constraint (Core 24).

### ai_usage (mutable counter — budgets)

user_id FK · day TEXT (UTC date) · tier (`tier1` \| `tier2`) · calls INTEGER. PK (user_id, day, tier). The per-user daily AI-call counters consumed by the budget gate (POL-TRIG-003). Incremented by the gateway-calling code on every Tier-classified call (including failed/malformed calls — they spent budget). A counter, not a Runtime Object: deliberately mutable, like `behavioral_traits`. Token-level usage per call is recorded on workflow-run node spans; this table exists only so the trigger evaluator's budget gate is a cheap deterministic read.

### workflow_runs (observability; powers the Reasoning Panel)

run_id PK · user_id · journey_id · trigger_type · gates JSON (debounce/cooldown/budget outcomes) · nodes JSON `[{node, class, duration_ms, cache_hit, object_refs}]` · policy_version · status · started_at · finished_at. Every run — including fast-path-only runs — writes one row. The decision *not* to run is logged by the trigger evaluator here as well (status `SKIPPED`).

A run **claims its slot** by inserting with `status = RUNNING` before any work, and releases it by finishing (`COMPLETED` / `SKIPPED` / `FAILED`) — including on failure, or the claim would outlive the run and skip every later trigger for that user. Partial unique index `uq_one_running_run_per_user` on `(user_id) WHERE status = 'RUNNING'` makes POL-TRIG-005 atomic rather than advisory: without it two concurrent evaluations both read *no run in flight* before either writes, and both proceed. A losing claim is recorded as a SKIP, which is what the policy prescribes (Decision #042).

---

# Catalog Seed Strategy

The catalog's *scale, composition and seeding rules* are Domain Pack artifact 9, not schema: how many products a demo needs, which are real and which invented, and which capability sets keep the canonical winners deterministic are all statements about a domain. A travel pack seeds itineraries, not SaaS vendors.

**Authority:** `docs/domains/software-buying/12-catalog-seed-strategy.md`.

What stays platform: products are seeded through the standard dual-write path (relational → embed → vector upsert → SYNCED), never generated at runtime, and the vector index is always re-derivable from the relational store.

---

# Vector Index (Chroma)

One collection: `products`.

| Field | Value |
|---|---|
| id | product_id |
| document | Embedding Document (deterministic composition per Core 20: name, vendor, category, description, business purpose, capability names + narratives) |
| metadata | `{product_id, record_version}` |
| embedding | via AI Provider Gateway (`AI_GATEWAY_EMBED_MODEL`) |

Dual-write order (Core 20): relational write with `sync_status=PENDING` → embed → Chroma upsert/delete → `sync_status=SYNCED`. A startup + periodic reconciliation sweep retries `PENDING`/`FAILED` rows and fully rebuilds the collection if missing. Retrieval defensively drops hits whose product row is soft-deleted or absent.

---

# Policy Configuration

`config/policies.yaml` — keys mirror Policy Catalog v1 IDs (POL-TRIG-001 …) with a top-level `policy_version`. Loaded once per process through a single loader module; hot-reload unnecessary for the reference deployment. Every `workflow_runs` and `journey_transitions` row records the version it evaluated under.

---

# Integrity Rules (enforced where)

| Rule | Enforcement |
|---|---|
| Event idempotency | `events.event_id` PK — duplicate batch replays no-op |
| Append-only Runtime Objects | Repository layer exposes insert-only helpers (D2); no UPDATE statements exist for these tables |
| AAR non-regeneration | Unique constraint (rpkg_id, prompt_version, surface) |
| Digest idempotency | Unique constraint (user_id, digest_window) |
| Capability validity | Admin API validates capability_id against `capabilities` before write |
| Referential lineage | FKs along the spine: events → journeys; evidence → journey; rpkg → rp → journey |
| Concurrency | SQLite WAL mode; single-writer process; all multi-table writes in transactions |

---

# What Is Deliberately Not a Table

- **Behavioral Memory** — a logical Runtime Object, materialized as the *view* over a journey's hypotheses, evidence, stage, and the user's traits; storing it separately would duplicate state (Reference, Don't Duplicate).
- **Policy Evaluation Results** — v1 records gate outcomes inside `workflow_runs.gates`/`journey_transitions` rather than as standalone PER rows; promotable to a table when replay tooling needs it.
- **Prompt Library** — versioned prompt templates live in code/config, keyed by `prompt_version` recorded on every AAR.

---
