# Journey Resolution Engine

**Version:** 1.0

---

# Purpose

The Journey Resolution Engine (JRE) is responsible for determining which Journey a new Session belongs to.

The Journey Resolution Engine establishes Journey ownership before deterministic behavioral reasoning begins.

Journey Resolution is the first deterministic decision performed for every new Session.

The Journey Resolution Engine never performs behavioral reasoning.

It never determines user intent.

It never invokes AI.

Its sole responsibility is resolving Journey ownership.

---

# Guiding Principle

The Journey Resolution Engine answers one question:

> "Does this Session continue an existing Journey or begin a new Journey?"

Journey Resolution is deterministic.

Journey Resolution evaluates multiple deterministic signals.

Journey Resolution never relies on a single heuristic.

---

# Core Principle

User

↓

Session

↓

Journey Resolution Engine

↓

Journey ID

↓

Behavioral Intelligence Platform

↓

Recommendation Package

Journey ownership is established before any deterministic reasoning begins.

All downstream Runtime Objects belong to exactly one Journey.

---

# Responsibilities

The Journey Resolution Engine is responsible for:

- Creating new Journeys.
- Assigning Journey IDs.
- Reusing existing Journeys.
- Reactivating Dormant Journeys.
- Managing Journey Lifecycle transitions.
- Producing Journey Resolution Results.

The Journey Resolution Engine never:

- Performs behavioral reasoning.
- Creates Behavioral Hypotheses.
- Creates Requirements.
- Produces recommendations.
- Invokes AI.

---

# Inputs

The Journey Resolution Engine consumes:

- User ID
- Session ID
- Session Behavioral Events
- Existing Active Journeys
- Existing Dormant Journeys
- Journey Lifecycle
- Decision Policies

Behavioral Events are consumed only for Journey ownership determination.

Behavioral reasoning begins after Journey Resolution has completed.

---

# Outputs

The Journey Resolution Engine produces:

- Journey ID
- Journey Resolution Result (JRR)
- Journey Lifecycle Update

Journey Resolution Result is an immutable runtime object.

No other Runtime Objects are modified.

---

# Journey Resolution Philosophy

Journey Resolution evaluates multiple deterministic signals.

No individual signal determines Journey ownership.

Examples include:

- Topic Similarity
- Behavioral Similarity
- Time Decay
- Journey Lifecycle
- Previous Journey Outcome

Decision Policies determine how these signals are evaluated.

The Journey Resolution Engine executes deterministic Journey Resolution.

---

# Journey Resolution Signals

The Journey Resolution Engine evaluates:

- Topic Similarity
- Behavioral Similarity
- Time Decay
- Journey Lifecycle State
- Previous Journey Outcome

Signals are evaluated together.

Time alone never creates a new Journey.

Time alone never reactivates a Journey.

Time alone never closes a Journey.

---

# Signal Computation

Each signal is computed deterministically, bounded to [0, 1], and combined using the weights defined by Decision Policy POL-JRES-001. The Journey Resolution Engine never uses AI or embeddings — Tier 2 semantic services are fenced to the Semantic Retrieval Engine (Decision #031); resolution signals are pure set and distribution arithmetic over event metadata, computable before behavioral reasoning begins.

## Topic Similarity

Jaccard overlap between the new Session's **entity set** and each candidate Journey's entity set:

```text
topic_similarity = |S ∩ J| ÷ |S ∪ J|
```

An entity set is the deterministic union, extracted from Behavioral Event metadata, of:

- Product IDs touched
- Categories viewed
- Documentation topics
- Normalized search-term tokens

The Journey's entity set accumulates over all its Sessions.

## Behavioral Similarity

Overlap of the two **event-type distributions** — cosine similarity between the Session's and the Journey's event-type histograms (counts per Event Type, normalized). Two periods of activity are behaviorally similar when they are composed of the same kinds of actions, regardless of the specific entities involved.

## Time Decay

Exponential decay on inactivity of the candidate Journey:

```text
time_decay = 0.5 ^ (days_since_last_journey_activity ÷ half_life_days)
```

with the half-life owned by Decision Policy (v1: 7 days), floored at 0.

## Combination and Edge Cases

```text
resolution_score = w_topic × topic_similarity
                 + w_behavioral × behavioral_similarity
                 + w_time × time_decay
```

- Weights and thresholds are POL-JRES-001 values; the engine hardcodes none.
- No candidate Journey exists (cold start) → score is undefined ≡ 0 → create a new Journey.
- Journey Lifecycle and Previous Journey Outcome act as deterministic gates on which Journeys are candidates (e.g., CLOSED and ARCHIVED Journeys are never candidates), not as score terms.

---

# Journey Resolution Result (JRR)

Every Journey Resolution produces a Journey Resolution Result.

Journey Resolution Result contains:

- Journey ID
- Resolution Decision
- Supporting Signals
- Decision Policy Version
- Deterministic Explanation
- Generated Timestamp

Journey Resolution Results are immutable.

They support replay, auditing, and explainability.

---

# Runtime Object Governance

Journey Resolution Result (JRR) conforms to the Runtime Object Model (Chapter 18).

Ownership, lifecycle, shared metadata, versioning, immutability, lineage, replayability, and observability are defined by the Runtime Object Model and are not repeated in this chapter.

This chapter defines only the deterministic process responsible for producing Journey Resolution Results.

---

# Journey Lifecycle

Journey Lifecycle represents the operational state of a Journey.

Journey Lifecycle is independent of Journey Stage.

Journey Lifecycle answers:

> "What is the operational status of this Journey?"

Journey Stage answers:

> "Where is the user within this Journey?"

These concepts are independent.

---

# Journey Lifecycle States

## NEW

Journey has been created but has not yet begun deterministic reasoning.

---

## ACTIVE

The user is actively progressing through the Journey.

Behavioral reasoning continues.

Requirements evolve.

Journey Stage may change.

---

## DORMANT

The Journey is temporarily inactive.

Behavioral Memory is preserved.

The Journey may later be reactivated.

Dormant Journeys are never considered complete.

---

## CLOSED

The Journey has reached a deterministic business outcome.

Examples include:

- PURCHASED
- ABANDONED
- CANCELLED
- NO_DECISION

Closed Journeys are immutable.

Only Closed Journeys contribute finalized learning signals to the Behavioral Learning Engine.

---

## ARCHIVED

Archived Journeys are retained for:

- Replay
- Auditing
- Analytics
- Long-term learning

Archived Journeys remain immutable.

Archived Journeys are never reactivated.

---

# Journey Lifecycle

NEW

↓

ACTIVE

↕︎

DORMANT

↓

ACTIVE

↓

CLOSED

↓

ARCHIVED

A Journey may transition between **ACTIVE** and **DORMANT** multiple times during its lifetime.

Once a Journey reaches **CLOSED**, it may no longer return to ACTIVE.

Once a Journey reaches **ARCHIVED**, it becomes permanently immutable.

---

# Journey Lifecycle Principles

## Principle 1

A Journey may transition between ACTIVE and DORMANT multiple times.

---

## Principle 2

Time alone never closes a Journey.

Journey closure is authorized exclusively by Decision Policies.

---

## Principle 3

The Journey Resolution Engine determines whether a Dormant Journey should be reactivated or whether a new Journey should be created.

---

## Principle 4

Only CLOSED Journeys contribute finalized learning signals to the Behavioral Learning Engine.

ACTIVE and DORMANT Journeys continue to evolve.

---

## Principle 5

Archived Journeys are immutable.

Archived Journeys support replay, auditing, analytics, and long-term behavioral understanding.

---

# Journey Ownership

The Journey Resolution Engine exclusively owns:

- Journey Creation
- Journey Assignment
- Journey Reactivation
- Journey Lifecycle Transitions
- Journey Resolution Results

No other platform component may modify Journey ownership.

Behavioral engines consume Journey ownership.

They never change it.

---

# Relationship to Decision Policies

The Journey Resolution Engine executes deterministic Journey Resolution.

Decision Policies determine:

- Journey reuse thresholds.
- Dormant Journey reactivation criteria.
- New Journey creation criteria.
- Journey Lifecycle transition rules.
- Journey closure rules.

The Journey Resolution Engine consumes Decision Policies.

It never defines them.

Business policy evolves independently of engine implementation.

---

# Relationship to the Platform

The Journey Resolution Engine is the entry point to the deterministic behavioral reasoning pipeline.

Every new Session begins with Journey Resolution.

Only after Journey ownership has been established may downstream platform engines execute.

The Journey Resolution Engine:

- Produces Journey IDs.
- Produces Journey Resolution Results.
- Updates Journey Lifecycle.
- Preserves replayability.

The Journey Resolution Engine never:

- Performs behavioral reasoning.
- Determines Requirements.
- Determines Journey Stage.
- Produces recommendations.
- Invokes AI.

---

# Interaction with Platform Components

User

↓

Session

↓

Journey Resolution Engine

↓

Journey ID

↓

Behavioral Memory

↓

Behavioral Hypotheses

↓

Requirement Profile

↓

Journey Stage

↓

Recommendation Package

↓

AI Buying Advisor

Every downstream runtime object belongs to exactly one Journey.

Journey ownership never changes after Session assignment.

---

# Journey Invariants

## Invariant 1

Every Session belongs to exactly one Journey.

---

## Invariant 2

Every Journey belongs to exactly one User.

---

## Invariant 3

A Journey may contain multiple Sessions.

---

## Invariant 4

Journey Resolution is deterministic.

---

## Invariant 5

Journey Resolution never invokes AI.

---

## Invariant 6

Journey Resolution decisions are replayable.

---

## Invariant 7

Journey Resolution Results are immutable.

---

## Invariant 8

Journey Lifecycle is independent of Journey Stage.

---

## Invariant 9

Journey ownership is determined exactly once for each Session.

---

# Design Principles

The Journey Resolution Engine follows these architectural principles.

## Principle 1

Journey ownership is deterministic.

---

## Principle 2

Journey ownership precedes behavioral reasoning.

---

## Principle 3

Journey Lifecycle and Journey Stage are independent concepts.

---

## Principle 4

Business policy remains external through Decision Policies.

---

## Principle 5

Journey Resolution Results are explainable and replayable.

---

## Principle 6

Journey ownership is immutable after Session assignment.

---

# Claude Implementation Contract

Claude MUST:

- Evaluate Journey Resolution deterministically.
- Produce Journey Resolution Results (JRR) that conform to the Runtime Object Model.
- Respect Decision Policies.
- Assign Journey IDs.
- Reactivate Dormant Journeys when authorized.
- Create new Journeys when required.
- Preserve Runtime Object lineage.
- Preserve replayability.
- Preserve explainability.

Claude MUST NOT:

- Hardcode Journey Resolution thresholds.
- Modify Journey ownership after Session assignment.
- Override Decision Policies.
- Invoke AI.
- Modify historical Runtime Objects.

---

# Relationship to Core Documentation

This chapter defines how Sessions are assigned to Journeys before deterministic behavioral reasoning begins.

Related chapters include:

| Chapter | Responsibility |
|---------|----------------|
| 02 | Behavioral Memory |
| 03 | Behavioral Learning Engine |
| 04 | Behavioral Decay Engine |
| 07 | Journey Stage Engine |
| 10 | Decision Policies |
| 11 | Observability and Evaluation |
| 13 | Event Schema |
| 17 | Platform Enumerations |
| 18 | Runtime Object Model |
| 99 | Architecture Principles |

---

# Summary

The Journey Resolution Engine establishes Journey ownership before any deterministic behavioral reasoning begins.

It evaluates deterministic signals together with Decision Policies to determine whether a Session continues an existing Journey, reactivates a Dormant Journey, or begins a new Journey.

The Journey Resolution Engine owns Journey IDs, Journey Lifecycle, and Journey Resolution Results.

It never performs behavioral reasoning.

It never produces recommendations.

It never invokes AI.

Its sole responsibility is ensuring that every Session is deterministically assigned to the correct Journey before the remainder of the Behavioral Intelligence Platform executes.

---