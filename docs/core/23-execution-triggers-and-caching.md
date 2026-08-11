# Execution Triggers & Caching

**Version:** 1.0

---

# Purpose

This chapter defines **when** the platform runs — and, critically, when it does not.

Behavioral events arrive continuously. Deterministic reasoning is cheap; AI calls are not. The Execution Trigger model decides when accumulated behavior justifies running the recommendation workflow (Chapter 21), and the caching model prevents redundant work when nothing meaningful has changed.

An LLM call per user action is an architectural defect, not an implementation detail.

---

# Guiding Principle

React to meaning, not to motion.

Events are motion. Significance is meaning. The pipeline runs on meaning.

---

# Trigger Types

All trigger conditions are Decision Policy values. The trigger evaluator is deterministic.

| Trigger | Fires when | Typical policy |
|---|---|---|
| SIGNIFICANT_EVENT | A high-signal event arrives (signal classes per Domain Pack, Chapter 22) | Immediate evaluation, debounced |
| EVENT_ACCUMULATION | N processed events since the last workflow run for this user | `triggers.event_count_threshold` |
| SESSION_END | A session closes with unprocessed high/medium-signal activity | Evaluate at session boundary |
| STAGE_TRANSITION | Journey Stage Engine publishes a new stage | Always evaluate |
| REQUIREMENT_SHIFT | A new Requirement Profile version differs materially from the last one used for recommendations | Material-change policy |
| SCHEDULED | Proactive delivery schedule fires (Chapter 24) | Daily digest window |
| ADMIN_CATALOG_CHANGE | Product mutations invalidate cached recommendations referencing them | Invalidation sweep |

## A declared trigger must have something that raises it

A trigger nothing emits is not implemented, however complete the evaluator looks: its gates are unreachable, and the behaviour the table promises never happens. This is the trigger-layer form of the reachability rule the Domain Pack's event registry states for event types.

**How each is raised in the reference implementation:**

| Trigger | Raised by |
|---|---|
| EVENT_ACCUMULATION | the ingestion endpoint, as a background task per accepted batch |
| SESSION_END | a background sweep every `POL-TRACK-003.end_sweep_interval_minutes`, over shoppers whose newest unprocessed high/medium event predates that policy's inactivity window (Decision #047) |
| SCHEDULED | the daily digest window (Chapter 24) |
| SIGNIFICANT_EVENT · STAGE_TRANSITION · REQUIREMENT_SHIFT · ADMIN_CATALOG_CHANGE | **not raised in v1** — declared and evaluable, with no caller |

SESSION_END exists because EVENT_ACCUMULATION cannot reach a shopper who has stopped. Its threshold is met by events that arrive, so a visit ending below the threshold — the ordinary case, and the certain case after a purchase — leaves work no later event will ever collect. Session closure is the boundary at which that work must be picked up, and inactivity is how closure is observed: a client-sent "session over" signal is missing in exactly the cases that matter (closed tab, closed laptop, crashed browser).

---

# Debounce and Cooldown

Triggers gate entry to the workflow; debounce and cooldown gate the triggers:

- **Debounce** — a SIGNIFICANT_EVENT trigger waits `triggers.debounce_window` for the burst to finish; one workflow run covers the whole burst.
- **Cooldown** — after a workflow run, no new run for the same user before `triggers.cooldown_window`, except STAGE_TRANSITION, which bypasses cooldown.
- **Concurrency** — at most **one in-flight workflow run per user** (POL-TRIG-005). A trigger arriving mid-run is recorded as SKIP (already-running); its events stay accumulated and are covered by the next evaluation. Racing triggers can never produce parallel runs or duplicate Recommendation Packages.
- **Budget** — per-user daily AI-call budget (`budget.tier1_daily`, `budget.tier2_daily`). Budget exhaustion degrades gracefully: deterministic nodes still run; Tier 2 falls back to the cached Candidate Set — or, when none exists, the match node falls back to full-catalog matching over all SYNCED products (Chapter 21, branch rules); Tier 1 falls back to serving the last stored AAR alongside the fresh deterministic Recommendation Package.

---

# The Two-Speed Pipeline

The workflow has two cost classes, gated independently:

## Fast path (deterministic, cheap — may run often)

Nodes 1–6 and 10–11 of the workflow: reasoning, confidence, requirements, stage, matching, readiness. These may run on every trigger.

## Slow path (AI, budgeted — runs on meaning)

Nodes 7–9 (Tier 2 retrieval loop) and 12 (Tier 1 generation). These run only when:

- The fast path produced a materially new Requirement Profile or Journey Stage, **or**
- No valid cached Candidate Set / AAR exists for the current state.

The fast path decides whether the slow path is worth paying for.

---

# Caching Model

## Candidate Set cache

- **Key:** (User ID, Requirement Profile version, catalog index version)
- **Invalidation:** new Requirement Profile version with material change; catalog index version change (dual-write bumps it); TTL `cache.candidate_ttl`.

## Recommendation Package cache

Recommendation Packages are immutable Runtime Objects; the "cache" is simply serving the latest package while its inputs are unchanged. A new package is produced only when a trigger fires **and** inputs (Requirement Profile version, Candidate Set, catalog versions, policy versions) differ from the last run's.

## AAR cache

- **Key:** (Recommendation Package ID, prompt version, delivery surface)
- The same package never generates twice for the same surface. Digest and on-site surfaces may hold distinct AARs for one package.

## Material change

"Materially new" is a Decision Policy: e.g., a requirement added/removed, a priority crossing a band, stage change, or top-candidate change — not any float wiggle. This single policy is the platform's main defense against LLM churn.

---

# Trigger Evaluation Flow

```text
Event batch processed (Chapter 22)
        ↓
Trigger Evaluator (deterministic, per user)
        ↓
condition met? ──no──► do nothing (events remain accumulated)
        ↓ yes
debounce / cooldown / budget gates
        ↓ pass
Workflow run (Chapter 21)
        ↓
Fast path always; slow path only on material change or cache miss
        ↓
Record run metadata (trigger type, gates evaluated, cache hits)
```

Every trigger decision — including the decision *not* to run — is observable.

---

# Invariants

## Invariant 1

No AI call is ever made in direct response to a single raw event.

## Invariant 2

Every workflow run is caused by a named trigger; the cause is recorded.

## Invariant 3

All thresholds, windows, and budgets are Decision Policy values.

## Invariant 4

Budget exhaustion degrades gracefully — deterministic outputs are always available.

## Invariant 5

Cache keys include the versions of every input that could change the output; stale serving is impossible by construction.

## Invariant 6

The material-change policy gates all slow-path execution.

## Invariant 7

Trigger evaluation is deterministic and replayable.

---

# Claude Implementation Contract

Claude MUST:

- Implement the trigger evaluator as deterministic policy evaluation over accumulated events.
- Gate slow-path (AI) nodes behind material change and cache state.
- Key caches by input versions; invalidate on catalog mutation via dual-write version bumps.
- Enforce debounce, cooldown, and per-user budgets.
- Record every trigger decision, including no-ops.

Claude MUST NOT:

- Call any AI per raw event.
- Regenerate an AAR for an unchanged Recommendation Package and surface.
- Hardcode thresholds.
- Fail the user experience when budgets are exhausted.
- Run the workflow without a named trigger.

---

# Relationship to Core Documentation

| Chapter | Responsibility |
|---------|----------------|
| 10 | Decision Policies (all trigger/cache/budget values) |
| 20 | Semantic Retrieval Engine (Candidate Set cache) |
| 21 | Agent Orchestration (the workflow being gated) |
| 22 | Event Ingestion & Tracking (signal classes, accumulation) |
| 24 | Proactive Delivery (SCHEDULED trigger) |

---

# Summary

Execution Triggers & Caching is the platform's efficiency contract: deterministic reasoning runs freely, AI runs only when accumulated behavior *means* something new, and every output is cached against the exact versions of its inputs. React to meaning, not to motion.

---
