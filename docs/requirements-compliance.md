# Reference Deployment — Requirements Compliance Matrix

**Version:** 1.0

This document maps every requirement of the SmartReco reference deployment to the architecture component that satisfies it. It is the bridge between the requirements and the specification — and the backbone of the implementation README.

Column key: **Core** = `docs/core/`, **Domain** = `docs/domains/software-buying/`.

---

## Mandatory Requirements

| # | Requirement | Satisfied by | Where |
|---|---|---|---|
| M1 | Web platform with email/password auth and two roles (user, admin) | Authentication & Account APIs; role enforcement at the API layer | Core 16 |
| M2 | Clean relational schema: users, products, activity events, stored recommendations | Runtime Object Model + Event Schema + Product Knowledge Store define the entities; implementation derives tables from them | Core 13, 14, 18 |
| M3 | Admin product CRUD | Admin Product APIs; contract-vs-data split (taxonomy governed, records runtime-managed) | Core 14, 16 · Decision #030 |
| M4 | Dual-write to relational DB **and** vector DB, kept in sync | Dual-write contract: relational system of record, vector index, SyncStatus, reconciliation sweep | Core 20, 17 |
| M5 | Efficient, non-blocking behavioral event tracking (batching, throttling) | Client tracking contract: buffer/flush/beacon, throttled heartbeats, silent failure; `POST /events/batch` accept-fast ingestion | Core 22 |
| M6 | Sensible event storage (who/what/when, batched) | Event Schema (envelope, IDs, relationships) + append-only batch-insert store | Core 13, 22 |
| M7 | Agent consumes tracked activity and reasons about interests | Behavioral Reasoning Engine → Confidence → Requirement Engine pipeline over Domain Pack patterns | Core 19, 05, 06 · Domain 02 |
| M8 | Recommendations via semantic retrieval / RAG, grounded in the real catalog | Semantic Retrieval Engine: Candidate Set proposal + deterministic capability matching ("semantic retrieval proposes, deterministic matching disposes") | Core 20, 08 |
| M9 | Personalized, persuasive recommendation narrative | Grounded Persuasion Mandate; Persuasive Buying Narrative section of the AAR | Core 09, 15 · Decision #032 |
| M10 | Recommendations stored and refreshed as behavior changes | Immutable versioned Recommendation Packages + AARs; refresh driven by triggers on material change | Core 18, 23 |
| M11 | No AI call per user action; meaningful triggers and caching | Execution Triggers & Caching: two-speed pipeline, debounce/cooldown/budgets, version-keyed caches | Core 23 |
| M12 | All AI calls through the environment-mandated gateway | AI Provider Gateway: single OpenAI-compatible boundary, configured entirely from deployment environment | Core 15, 20 · Decision #034 |

---

## Distinguishing Features

| # | Feature | Satisfied by | Where |
|---|---|---|---|
| D1 | Explicit structured agent workflow (analyze → decide-retrieve → evaluate → refine → generate) | Agent Orchestration: 13-node graph, framework-agnostic contract, bounded refinement loop | Core 21 |
| D2 | Scheduled proactive delivery (digest via real background scheduler, not a manual action) | Proactive Delivery: SCHEDULED trigger, eligibility policy, channel adapters, idempotent Delivery Records | Core 24 |
| D3 | End-to-end workflow observability / tracing | Agent Workflow Tracing (per-node spans, AI-call metadata) atop platform-wide observability | Core 11 |
| D4 | Retrieval polish (evaluation, refinement, deterministic re-ranking over candidates) | Tier 2 evaluate→refine loop; priority-weighted deterministic ranking as the re-rank stage | Core 20, 08, 10 |

---

## Architecture Guarantees Beyond the Requirements

These are not required by the reference deployment; they are the platform's own standards, and they differentiate it:

| Guarantee | Where |
|---|---|
| Deterministic, replayable reasoning — identical inputs reproduce identical recommendations | Core 18, 11 · Domain 09 |
| Complete traceability: every recommendation traces Event → Evidence → Hypothesis → Requirement → Capability → Product | Domain 09 · Core 11 |
| Two-tier AI boundary: AI proposes candidates and narrates outcomes; it never establishes truth | Core 99 (Principle 11) · Decision #031 |
| Business thresholds live in versioned Decision Policies (Policy Catalog v1), never in engine code | Core 10 |
| Domain-agnostic core: a new domain (events, travel, books, …) is a new Domain Pack, zero core changes | knowledge/architecture · Core 00 |
| Persuasion with zero hallucination risk by construction — every persuasive claim traceable to a Runtime Object | Core 09 |

---

## Stack Constraints (implementation-time)

The specification is technology-agnostic; the reference deployment constrains implementation choices as follows. Final selections are recorded at implementation time, not in the architecture.

| Constraint | Specification stance |
|---|---|
| Python web framework (FastAPI/Flask class) | API Contracts (Core 16) are framework-neutral |
| Server-rendered templates + JS tracking client | Tracking contract (Core 22) is transport-level, template-engine-neutral |
| Relational DB: SQLite/PostgreSQL class | System of record per Core 20; schema derived from Core 13/14/18 |
| Vector DB: any | Vector index contract per Core 20; store is swappable |
| AI access via configured gateway, key in environment, never committed | Core 15/20; env vars only |
| Agent framework: any graph-based framework | Core 21 orchestration contract is framework-independent |
| Scheduler: any real background scheduler | Core 24 scheduler contract |

---

## Deployment Checklist (repository-level)

Implementation-time obligations, tracked here so they are not lost:

- [ ] Public repository with all source code
- [ ] README: what was built, architecture summary, setup/run instructions, feature list (D1–D4 status)
- [ ] `requirements.txt` (or equivalent) declaring the web framework and the AI client library
- [ ] `.gitignore` includes `.env`; no secrets ever committed
- [ ] Repository secrets configured per the deployment environment's instructions (gateway key, deployment token)
- [ ] CI workflow file installed at the path the deployment environment specifies; checks green
- [ ] Optional: demo video and deployed URL

---

## Reading Order for Reviewers

1. `docs/core/README.md` — platform overview
2. `docs/core/21-agent-orchestration.md` — the agent at a glance (13 nodes, 10 deterministic)
3. `docs/core/20-semantic-retrieval-engine.md` — RAG grounding and dual-write
4. `docs/core/23-execution-triggers-and-caching.md` — efficiency model
5. `docs/domains/software-buying/09-reference-behavioral-journey-scenarios.md` — end-to-end worked examples with computed numbers

---
