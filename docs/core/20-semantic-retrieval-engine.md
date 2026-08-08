# Semantic Retrieval Engine

**Version:** 1.0

---

# Purpose

The Semantic Retrieval Engine (SRE) grounds recommendations in the live product catalog through semantic (vector) retrieval.

It owns:

- The **Product Knowledge Store** — the dual representation of product records (relational + vector) and the dual-write contract that keeps them in sync.
- **Candidate generation** — semantic retrieval of the products most relevant to a user's behavioral context.
- **Retrieval quality evaluation and query refinement** — the bounded agentic loop that improves retrieval before deterministic matching.

The SRE produces **Candidate Sets**. It never produces final recommendations.

Final ranking, coverage analysis, and Recommendation Packages remain the exclusive responsibility of the Recommendation Engine, which consumes the Candidate Set and performs deterministic capability matching over it.

---

# Guiding Principle

Semantic retrieval proposes.

Deterministic matching disposes.

The catalog is live; the taxonomy is canonical; the truth is deterministic.

---

# The Two-Tier AI Boundary

This chapter introduces the second tier of the platform's AI boundary. The complete boundary is now:

## Tier 1 — Generative Communication

The AI Buying Advisor. Consumes approved Runtime Objects, produces AI Advisory Responses. Defined in Chapters 09 and 15. Unchanged.

## Tier 2 — Semantic Services

AI used **inside the retrieval stage only**:

- Embedding generation (products and queries)
- Retrieval quality evaluation
- Query refinement

Tier 2 services are governed by strict invariants:

- They produce and score **candidates only**.
- They never produce final rankings, match scores, or Requirement Coverage.
- They never create or modify deterministic Runtime Objects (Hypotheses, Requirement Profiles, Journey Stages, Recommendation Packages).
- They never influence Recommendation Readiness.
- Every Tier 2 call is observable, budgeted, and gated by Execution Triggers (Chapter 23).

Everything outside these two tiers remains AI-free, exactly as the Constitution requires.

**Result:** the agent decides *when and what to retrieve*; the platform decides *what is true*.

---

# AI Provider Gateway

All Tier 1 and Tier 2 calls pass through a single **AI Provider Gateway** — one OpenAI-compatible client boundary owned by the platform.

- The gateway is configured by base URL, API key, and model identifiers only — supplied entirely by deployment configuration (environment), never committed and never hardcoded.
- Swapping providers is a configuration change, never a code change. This specification names no provider; the active provider is a deployment decision.
- No platform component may construct a provider client outside the gateway.

The LLM Contract (Chapter 15) governs what flows through the gateway; this chapter governs where the gateway sits.

---

# Product Knowledge Store

The Product Knowledge Store is the runtime home of product records (see Chapter 14 — the Domain Pack owns the capability taxonomy and the Product Capability Profile *contract*; product *records* are runtime data managed by admins).

Every product record exists in two synchronized representations:

## 1. Relational Record (System of Record)

The authoritative product row: Product ID, name, vendor, description, category, price metadata, Supported Capability IDs, record version, timestamps.

## 2. Vector Record (Retrieval Index)

The embedding of the product's **Embedding Document**, stored in the vector store with the Product ID and record version as metadata.

The Embedding Document is composed deterministically from:

- Product name, vendor, category
- Product description
- Business Purpose
- Capability names and Business Value Narratives resolved from the Capability Catalog

Identical product records always produce identical Embedding Documents.

---

# Dual-Write Contract

Every product mutation (create, update, delete) follows the same transactional sequence:

1. Write the relational record with `sync_status = PENDING`.
2. Compose the Embedding Document and obtain the embedding via the AI Provider Gateway.
3. Upsert (or delete) the vector record keyed by Product ID.
4. Mark the relational record `sync_status = SYNCED`.

Failure handling:

- If step 2–3 fails, the record remains `PENDING`; a reconciliation sweep retries all `PENDING`/`FAILED` records with **exponential backoff and a bounded attempt counter** (POL-RETR-004; v1: max 5 automatic attempts). After the cap, the record stays `FAILED`, is excluded from further automatic retries, and surfaces in the admin catalog for **manual retry** (which resets the counter). The sweep never loops indefinitely on a poisoned record.
- Retrieval never returns products whose relational record is deleted; a defensive filter drops any vector hit without a live relational record.
- The relational store is always the system of record. The vector store is always derivable from it — a full re-index must always be possible.

SyncStatus values (`PENDING`, `SYNCED`, `FAILED`) are defined in Platform Enumerations (Chapter 17).

---

# Query Construction

Retrieval queries are constructed **deterministically** — no AI required for the initial query.

The Behavioral Query Document is composed from:

- The current Requirement Profile (requirement names, priorities)
- Active Behavioral Hypotheses (concept names, from Behavioral Memory)
- Current Journey Stage
- Recent high-signal activity summary (search terms, viewed categories)

The query document template is versioned. Identical inputs produce identical query documents.

---

# Candidate Set

Retrieval produces a **Candidate Set** — a Runtime Object:

- Candidate Set ID
- Query Document (verbatim)
- Retrieval Parameters (top-K, filters, embedding model ID, index version)
- Candidates: ordered list of { Product ID, similarity score, record version }
- Refinement History (if the evaluation loop ran)
- Generated Timestamp

Candidate Sets are immutable, versioned, and replayable given the same index state. They are consumed exclusively by the Recommendation Engine.

---

# Retrieval Evaluation and Refinement (Tier 2)

After initial retrieval, the SRE may execute a bounded evaluation loop:

1. **Evaluate** — a Tier 2 call assesses whether the Candidate Set is relevant to the Query Document (verdict + missing-aspect notes).
2. **Refine** — if evaluation fails, a Tier 2 call rewrites the query document to cover the missing aspects.
3. **Re-retrieve** — retrieval runs again with the refined query.

Loop bounds are owned by Decision Policies (maximum iterations, evaluation-skip conditions, budget). The loop degrades gracefully: if budget is exhausted or evaluation is unavailable, the initial Candidate Set stands.

The evaluation verdict affects **which candidates are proposed** — never how they are finally ranked.

---

# Relationship to the Recommendation Engine

Requirement Profile

↓

Semantic Retrieval Engine

↓

Candidate Set (semantic proposal)

↓

Recommendation Engine

↓

Deterministic capability matching over candidates

↓

Recommendation Package

The Recommendation Engine treats the Candidate Set as a **scoping input**: it evaluates Product Capability Profiles of candidate products only, applies deterministic capability matching, and produces the Recommendation Package. Semantic similarity scores may appear in Recommendation Metadata for observability, but never in Match Scores.

---

# Invariants

## Invariant 1

The SRE produces Candidate Sets only. It never produces recommendations, rankings, match scores, or coverage.

## Invariant 2

Tier 2 AI never creates or modifies deterministic Runtime Objects and never influences Recommendation Readiness.

## Invariant 3

The relational store is the system of record; the vector store is always fully re-derivable from it.

## Invariant 4

Every product mutation follows the dual-write contract; sync state is always observable.

## Invariant 5

Embedding Documents and Query Documents are composed deterministically from versioned templates.

## Invariant 6

All provider calls pass through the AI Provider Gateway. Provider swap is configuration, not code.

## Invariant 7

The refinement loop is bounded by Decision Policies and degrades gracefully to the initial Candidate Set.

## Invariant 8

Candidate Sets are immutable, versioned Runtime Objects with full retrieval metadata for replay.

---

# Claude Implementation Contract

Claude MUST:

- Route every embedding and evaluation call through the AI Provider Gateway (provider resolved from deployment configuration).
- Implement the dual-write contract with sync status and reconciliation.
- Compose Embedding and Query Documents deterministically from versioned templates.
- Produce Candidate Sets conforming to the Runtime Object Model.
- Bound the refinement loop with Decision Policies.
- Filter dead vector hits against the relational store.

Claude MUST NOT:

- Let Tier 2 outputs modify deterministic Runtime Objects.
- Use similarity scores as final match scores.
- Write to the vector store outside the dual-write contract.
- Construct provider clients outside the gateway.
- Run unbounded refinement loops.

---

# Relationship to Core Documentation

| Chapter | Responsibility |
|---------|----------------|
| 06 | Requirement Engine |
| 08 | Recommendation Engine |
| 10 | Decision Policies |
| 14 | Product Catalog |
| 15 | LLM Contract |
| 17 | Platform Enumerations |
| 21 | Agent Orchestration |
| 23 | Execution Triggers & Caching |

---

# Summary

The Semantic Retrieval Engine gives the platform its grounding in the live catalog: a dual-written Product Knowledge Store, deterministic query construction, semantic candidate generation, and a bounded agentic evaluation loop — all behind a provider-agnostic gateway. It proposes; the deterministic Recommendation Engine disposes.

---
