# Agent Orchestration

**Version:** 1.0

---

# Purpose

Agent Orchestration defines how the platform's engines are composed into a single agentic workflow — an explicit reasoning graph that analyzes behavior, decides when to retrieve, evaluates retrieval quality, refines, matches, and generates.

Orchestration composes engines.

It never implements them.

Every node in the workflow delegates to a platform engine defined elsewhere in this documentation. Orchestration owns only sequencing, branching, looping, and state passing.

---

# Guiding Principle

The graph is the agent.

The engines are the truth.

Orchestration decides *when* things run — never *what is true*.

---

# Framework Independence

This chapter defines the **orchestration contract**, not a framework.

- The workflow is expressible in any graph-based agent framework (LangGraph is the reference implementation; Google ADK or equivalents are interchangeable).
- The contract is: named nodes, typed state, explicit edges, bounded loops, per-node tracing.
- Swapping orchestration frameworks must require no changes to any engine, contract, or Runtime Object.

Framework selection is an implementation decision recorded outside this specification.

---

# The Recommendation Workflow

```text
                     ┌────────────────────┐
   Trigger fires ───►│ 1 resolve_journey  │  Journey Resolution Engine
   (Chapter 23)      └─────────┬──────────┘
                               ▼
                     ┌────────────────────┐
                     │ 2 reason           │  Behavioral Reasoning Engine
                     └─────────┬──────────┘
                               ▼
                     ┌────────────────────┐
                     │ 3 score_confidence │  Confidence Engine
                     └─────────┬──────────┘
                               ▼
                     ┌────────────────────┐
                     │ 4 infer_requirements│ Requirement Engine
                     └─────────┬──────────┘
                               ▼
                     ┌────────────────────┐
                     │ 5 resolve_stage    │  Journey Stage Engine
                     └─────────┬──────────┘
                               ▼
                     ┌────────────────────┐
                     │ 6 decide_retrieve  │  Decision Policy gate
                     └───┬──────────┬─────┘
                 skip │          │ retrieve
                      ▼          ▼
                      │  ┌────────────────────┐
                      │  │ 7 retrieve         │  Semantic Retrieval Engine
                      │  └─────────┬──────────┘
                      │            ▼
                      │  ┌────────────────────┐
                      │  │ 8 evaluate_retrieval│ Tier 2 (bounded)
                      │  └───┬──────────┬─────┘
                      │  pass│          │refine (≤ policy max)
                      │      │          ▼
                      │      │  ┌────────────────────┐
                      │      │  │ 9 refine_query     │  Tier 2 → back to 7
                      │      │  └────────────────────┘
                      │      ▼
                     ┌────────────────────┐
                     │ 10 match           │  Recommendation Engine
                     └─────────┬──────────┘
                               ▼
                     ┌────────────────────┐
                     │ 11 readiness_gate  │  Decision Policy (READY / NOT_READY)
                     └───┬──────────┬─────┘
              NOT_READY │          │ READY
                        ▼          ▼
             ┌──────────────┐  ┌────────────────────┐
             │ 12a clarify  │  │ 12b generate       │  AI Buying Advisor (Tier 1)
             └──────┬───────┘  └─────────┬──────────┘
                    ▼                    ▼
                     ┌────────────────────┐
                     │ 13 persist_deliver │  Store AAR; deliver (Chapter 24)
                     └────────────────────┘
```

---

# Node Classification

| Node | Engine | Class |
|---|---|---|
| 1 resolve_journey | Journey Resolution Engine | Deterministic |
| 2 reason | Behavioral Reasoning Engine | Deterministic |
| 3 score_confidence | Confidence Engine | Deterministic |
| 4 infer_requirements | Requirement Engine | Deterministic |
| 5 resolve_stage | Journey Stage Engine | Deterministic |
| 6 decide_retrieve | Decision Policy Framework | Deterministic |
| 7 retrieve | Semantic Retrieval Engine | Tier 2 (embeddings) |
| 8 evaluate_retrieval | Semantic Retrieval Engine | Tier 2 (LLM evaluation) |
| 9 refine_query | Semantic Retrieval Engine | Tier 2 (LLM refinement) |
| 10 match | Recommendation Engine | Deterministic |
| 11 readiness_gate | Decision Policy Framework | Deterministic |
| 12a clarify / 12b generate | AI Buying Advisor | Tier 1 (LLM generation) |
| 13 persist_deliver | Platform persistence / delivery | Deterministic |

Ten of thirteen nodes are deterministic. AI appears exactly where the two-tier boundary permits it — and nowhere else.

---

# Orchestration State

The workflow state carries **references to Runtime Objects, never copies**:

- Journey ID, Session ID, Correlation ID
- Latest Behavioral Memory version reference
- Latest Requirement Profile version reference
- Journey Stage reference
- Candidate Set reference (after node 7)
- Recommendation Package reference (after node 10)
- Refinement iteration counter
- Trigger metadata (what fired this run — Chapter 23)

State is serializable, so any framework's checkpointing works and every run is resumable and traceable.

---

# Loop and Branch Rules

- The only loop is 7 → 8 → 9 → 7, bounded by the Decision Policy `retrieval.max_refinements`.
- `decide_retrieve` may skip retrieval **only into a valid cached Candidate Set** (cache key: user, Requirement Profile version, catalog index version). If no valid cached set exists, the skip branch does not exist — retrieval runs.
- If retrieval cannot run (budget exhausted, gateway failure) **and** no valid cached Candidate Set exists, the match node degrades to **full-catalog matching**: deterministic capability matching over all SYNCED, non-deleted products. The resulting Recommendation Package records a null Candidate Set reference, keeping the degradation observable. Retrieval is an efficiency-and-grounding optimization — never a correctness dependency of the deterministic matcher.
- `readiness_gate` branches exclusively on deterministic Recommendation Readiness. Tier 1 nodes never override it: NOT_READY always routes to clarify, never to generate.
- Node failures degrade gracefully: a Tier 2 failure falls through to the best available Candidate Set; a Tier 1 failure persists the deterministic Recommendation Package without an AAR and records the failure.

---

# Observability

Every node emits:

- Node name, engine, class (Deterministic / Tier 1 / Tier 2)
- Input and output Runtime Object references
- Duration, success status, failure reason
- For AI nodes: prompt version, model ID, token usage

The full graph run is traceable end to end (LangSmith-class tracing in the reference implementation). Deterministic replay re-executes deterministic nodes exactly; AI nodes are regenerated per the Runtime Object Model's replay rules.

---

# Invariants

## Invariant 1

Orchestration never implements engine logic. Every node delegates.

## Invariant 2

Node classification is fixed: AI never appears in a node classified Deterministic.

## Invariant 3

All loops are bounded by Decision Policies.

## Invariant 4

Workflow runs start only from Execution Triggers (Chapter 23) — never per raw event.

## Invariant 5

State carries Runtime Object references, never mutable copies.

## Invariant 6

The readiness gate is deterministic and cannot be overridden downstream.

## Invariant 7

The orchestration framework is replaceable without touching engines, contracts, or Runtime Objects.

---

# Claude Implementation Contract

Claude MUST:

- Implement the workflow as an explicit graph with the nodes and edges defined here.
- Delegate every node to its owning engine.
- Bound the refinement loop by policy.
- Emit per-node observability metadata.
- Route all AI nodes through the AI Provider Gateway.
- Degrade gracefully on AI-node failure.

Claude MUST NOT:

- Inline engine logic into orchestration code.
- Add AI calls to deterministic nodes.
- Let generation proceed when readiness is NOT_READY.
- Trigger workflow runs per raw event.
- Couple engines to a specific orchestration framework.

---

# Relationship to Core Documentation

| Chapter | Responsibility |
|---------|----------------|
| 05–08 | Deterministic engines composed by nodes 3–10 |
| 09 | AI Buying Advisor (nodes 12a/12b) |
| 10 | Decision Policies (nodes 6, 11, loop bounds) |
| 12 | Journey Resolution Engine (node 1) |
| 19 | Behavioral Reasoning Engine (node 2) |
| 20 | Semantic Retrieval Engine (nodes 7–9) |
| 23 | Execution Triggers & Caching (workflow entry) |
| 24 | Proactive Delivery (scheduled workflow entry) |

---

# Summary

Agent Orchestration turns the platform's engines into one explicit, observable, framework-agnostic reasoning graph: deterministic through and through, with AI appearing only at the two sanctioned tiers — semantic services inside retrieval, generative communication at the end. The graph is the agent; the engines are the truth.

---
