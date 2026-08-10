# Decision Policies

**Version:** 1.0

---

# Purpose

The Decision Policy Framework (DPF) governs deterministic business decisions throughout the Behavioral Intelligence Platform.

Decision Policies define **when** deterministic actions are permitted.

Platform engines determine **what is true**.

Decision Policies determine **what is allowed**.

AI determines **how outcomes are communicated**.

Business policies are configuration.

They are never platform implementation.

---

# Guiding Principle

Business decisions are governed by Decision Policies.

They are never hardcoded inside platform engines.

Platform engines perform deterministic reasoning.

Decision Policies authorize deterministic actions.

Business policy evolves independently of platform implementation.

---

# Core Principle

Behavior

↓

Behavioral Evidence

↓

Behavioral Hypotheses

↓

Platform Engines determine truth

↓

Decision Policies authorize actions

↓

Recommendation Package

↓

AI Buying Advisor communicates results

The platform separates reasoning, governance, and communication into independent responsibilities.

---

# Responsibilities

The Decision Policy Framework is responsible for:

- Evaluating deterministic business policies.
- Producing Policy Evaluation Results (PER).
- Governing business thresholds.
- Governing business transitions.
- Supporting policy versioning.
- Supporting deterministic replay.
- Producing deterministic Policy Explanations.

The Decision Policy Framework never:

- Performs behavioral reasoning.
- Creates Behavioral Hypotheses.
- Creates Requirements.
- Produces recommendations.
- Invokes AI.

Its sole responsibility is governing deterministic business decisions.

---

# Inputs

The Decision Policy Framework consumes approved Runtime Objects together with versioned policy definitions.

Approved Runtime Objects may include:

- Behavioral Hypotheses
- Behavioral Memory
- Requirement Profile
- Journey Stage
- Recommendation Package
- Journey Lifecycle
- Behavioral Profile

Policy evaluation consumes Runtime Object state.

It never modifies Runtime Object state.

---

# Outputs

The Decision Policy Framework produces:

- Policy Evaluation Result (PER)

The Policy Evaluation Result is an immutable Runtime Object.

No platform runtime objects are modified.

Platform engines consume Policy Evaluation Results when executing deterministic actions.

---

# Policy Philosophy

Decision Policies determine **when** deterministic actions are permitted.

Platform engines determine **how** those actions are executed.

Examples include:

- Journey Resolution
- Journey Lifecycle Transition
- Behavioral Hypothesis Promotion
- Behavioral Trait Reinforcement
- Behavioral Trait Decay
- Journey Stage Transition
- Requirement Publication
- Recommendation Readiness
- AI Recommendation Permission

Decision Policies never implement platform logic.

They govern platform behavior.

---

# Policy Categories

## 1. Behavioral Policies

Behavioral Policies govern deterministic behavioral reasoning.

Examples include:

- Evidence Promotion
- Evidence Expiration
- Hypothesis Promotion
- Behavioral Pattern Detection
- Behavioral Conflict Resolution

Behavioral Policies support Behavioral Hypotheses.

They never create Behavioral Events.

---

## 2. Confidence Policies

Confidence Policies govern deterministic confidence behavior.

Examples include:

- Minimum Confidence
- Confidence Saturation
- Confidence Promotion
- Confidence Decay
- Evidence Diversity Rules

Confidence Policies support the Confidence Engine.

The Confidence Engine executes deterministic confidence calculations.

---

## 3. Learning Policies

Learning Policies govern long-term behavioral learning.

Examples include:

- Reinforcement Threshold
- Trait Promotion
- Trait Decay
- Reinforcement Weighting
- Trait Retirement

Learning Policies govern Behavioral Profile evolution.

The Behavioral Learning Engine and Behavioral Decay Engine execute these policies.

---

## 4. Journey Resolution Policies

Journey Resolution Policies determine whether a new Session should:

- Continue an existing Journey.
- Reactivate a Dormant Journey.
- Create a new Journey.

Journey Resolution evaluates deterministic signals including:

- Topic Similarity
- Behavioral Similarity
- Time Decay
- Journey Lifecycle
- Previous Journey Outcome

Journey Resolution thresholds belong to Decision Policies.

The Journey Resolution Engine performs deterministic evaluation.

---

## 5. Journey Lifecycle Policies

Journey Lifecycle Policies govern operational Journey state transitions.

Examples include:

- NEW → ACTIVE
- ACTIVE → DORMANT
- DORMANT → ACTIVE
- ACTIVE → CLOSED
- CLOSED → ARCHIVED

Journey Lifecycle transitions are determined through deterministic policy evaluation.

Time alone never changes Journey Lifecycle.

Journey Lifecycle transitions are executed by the Journey Resolution Engine.

Decision Policies determine when transitions are permitted.

---

## 6. Journey Stage Policies

Journey Stage Policies define deterministic qualification criteria for entering, remaining in, or exiting a Journey Stage.

Journey Stage definitions belong to the active Domain Pack.

Decision Policies define the qualification criteria.

Examples include (**illustrative — Software Buying Domain Pack, its own 8-stage journey**; identifiers below belong to that pack, not to the platform):

- Awareness
- Discovery
- Research
- Comparison
- Technical Validation
- Commercial Evaluation
- Decision
- Adoption

The Journey Stage Engine performs deterministic classification.

Decision Policies determine when stage transitions are permitted.

---

## 7. Recommendation Policies

Recommendation Policies govern deterministic recommendation decisions.

Examples include:

- Recommendation Readiness
- Minimum Match Score
- Capability Weighting
- Tie-breaking Rules
- Blocking Constraints
- Publication Thresholds

Recommendation Policies determine whether Recommendation Packages may be published.

The Recommendation Engine executes deterministic recommendation generation.

Decision Policies authorize publication.

---

## 8. AI Communication Policies

AI Communication Policies govern how the AI Buying Advisor communicates deterministic platform outputs.

Examples include:

- AI Recommendation Allowed
- AI Clarification Required
- AI Recommendation Blocked
- Required Disclaimer
- Communication Constraints
- Required Transparency Rules

AI Communication Policies never modify deterministic runtime objects.

They govern communication only.

---

# Policy Object

Every Decision Policy follows a common deterministic structure.

Every Policy contains:

- Policy ID
- Policy Name
- Policy Version
- Policy Category
- Enabled Status
- Inputs
- Decision Rules
- Decision Outcomes
- Created Timestamp
- Effective Timestamp

Decision Policies are:

- Deterministic
- Versioned
- Immutable once published
- Independently deployable
- Fully replayable

Every policy update produces a new Policy Version.

---

# Policy Evaluation Result (PER)

Every policy evaluation produces a Policy Evaluation Result (PER).

PER is an immutable Runtime Object.

Every PER contains:

- Policy ID
- Policy Version
- Evaluation Status
- Rules Evaluated
- Rules Passed
- Rules Failed
- Deterministic Policy Explanation
- Generated Timestamp

PER provides complete auditability.

PER enables deterministic replay.

PER explains every business decision made by the platform.

---

# Runtime Object Governance

Policy Evaluation Result (PER) conforms to the Runtime Object Model (Chapter 18).

Ownership, lifecycle, shared metadata, versioning, immutability, lineage, replayability, and observability are defined by the Runtime Object Model and are not repeated in this chapter.

This chapter defines only the deterministic process responsible for producing Policy Evaluation Results.

---

# Policy Versioning

Business policy evolution must never require platform code changes.

Policy versions evolve independently of platform engines.

Platform engines consume published policy versions.

Historical policy versions remain available for replay, auditing, and historical analysis.

Policy versioning guarantees that historical platform behavior remains reproducible even after business policies evolve.

---

# Relationship to Platform Engines

Platform engines perform deterministic reasoning.

Decision Policies govern business authorization.

Examples

Behavioral Learning Engine

↓

Determines Trait Reinforcement

↓

Decision Policies

↓

Authorize Reinforcement

---

Recommendation Engine

↓

Determines Recommendation Readiness

↓

Decision Policies

↓

Authorize Recommendation Publication

---

Journey Stage Engine

↓

Determines Current Stage

↓

Decision Policies

↓

Authorize Stage Transition

Platform engines never hardcode business thresholds.

Business policy remains external to platform implementation.

---

# Relationship to the Platform

The Decision Policy Framework provides the governance layer for the Behavioral Intelligence Platform.

The platform is composed of three independent responsibilities:

Behavioral Intelligence Platform

↓

Platform Engines determine truth.

↓

Decision Policies authorize actions.

↓

AI communicates outcomes.

Each responsibility is independent.

No platform component performs more than one responsibility.

---

# Interaction with Platform Components

Behavioral Evidence

↓

Platform Engines

↓

Runtime Objects

↓

Decision Policy Framework

↓

Policy Evaluation Result (PER)

↓

Platform Engine Action

↓

Recommendation Package

↓

AI Buying Advisor

Decision Policies never replace deterministic reasoning.

They govern whether deterministic actions are permitted.

---

# Policy Invariants

## Invariant 1

Decision Policies are deterministic.

---

## Invariant 2

Decision Policies are versioned.

---

## Invariant 3

Decision Policies are immutable once published.

Every policy update creates a new Policy Version.

---

## Invariant 4

Policy evaluation produces deterministic Policy Explanations.

---

## Invariant 5

Decision Policies never invoke AI.

AI outputs never influence policy evaluation.

---

## Invariant 6

Policy evaluation is fully replayable.

---

## Invariant 7

Business thresholds never appear inside platform engines.

All business thresholds are owned by Decision Policies.

---

## Invariant 8

Decision Policies never modify runtime objects.

Platform engines execute deterministic actions after policy authorization.

---

## Invariant 9

Policy Evaluation Results are immutable Runtime Objects.

---

# Design Principles

The Decision Policy Framework follows these architectural principles.

## Principle 1

Platform engines determine truth.

---

## Principle 2

Decision Policies authorize actions.

---

## Principle 3

AI communicates outcomes.

---

## Principle 4

Business policy remains external to platform implementation.

---

## Principle 5

Business rules evolve without changing platform code.

---

## Principle 6

Policy evaluation is deterministic, versioned, explainable, and replayable.

---

# Claude Implementation Contract

Claude MUST:

- Evaluate Decision Policies deterministically.
- Produce Policy Evaluation Results (PER) that conform to the Runtime Object Model.
- Respect Policy Versions.
- Produce deterministic Policy Explanations.
- Respect Runtime Object ownership.
- Respect Runtime Object immutability.
- Respect Runtime Object versioning.
- Preserve Runtime Object lineage.
- Preserve replayability.
- Preserve observability.

Claude MUST NOT:

- Hardcode business thresholds.
- Modify Policy Definitions.
- Modify Runtime Objects.
- Override published Decision Policies.
- Invoke AI during policy evaluation.
- Allow AI outputs to influence policy evaluation.

---

# Policy Catalog v1 — Initial Values

The following are the platform's initial published policy values. They are configuration, not engine code: every value is versioned, replayable, and changeable without touching any engine. Values are deliberately demo-friendly (behavior visibly changes within a short session) and are expected to be tuned; every change produces a new policy version.

## Behavioral & Confidence Policies

| Policy ID | Policy | v1 Value |
|---|---|---|
| POL-BEH-001 | Hypothesis promotion | Create a Hypothesis at 2 supporting Evidence objects, or 1 with Strength ≥ Strong |
| POL-BEH-002 | Evidence expiration | Evidence older than 30 days contributes at 50% weight |
| POL-CONF-001 | Confidence contribution | Weak +0.05, Medium +0.10, Strong +0.20, Very Strong +0.30 per Evidence; diversity increment +0.10 per distinct pattern beyond the first |
| POL-CONF-002 | Diminishing returns | Repeated identical Evidence contributes at 50% of prior contribution. Identical = same pattern, same strength, same supporting event-type composition; a different strength or composition contributes at full class value (Decision #036) |
| POL-CONF-003 | Contradiction penalty | Contradicting Evidence subtracts at 75% of its class contribution |
| POL-CONF-004 | Confidence saturation | Cap 0.95; floor 0.05 |
| POL-CONF-005 | Hypothesis retirement | Retire when confidence < 0.15 for 2 consecutive updates |

## Requirement & Stage Policies

| Policy ID | Policy | v1 Value |
|---|---|---|
| POL-REQ-001 | Requirement publication | Include a Requirement when derived confidence ≥ 0.5 |
| POL-REQ-002 | Priority bands | Critical ≥ 0.8 with stage ≥ Technical Validation; High ≥ 0.65; Medium ≥ 0.5; else Low |
| POL-REQ-003 | Requirement confidence derivation | Each active Hypothesis contributes (association weight × hypothesis confidence) to its mapped Requirements — weights: Primary 1.0, Secondary 0.6, Supporting 0.3. Contributions combine via noisy-OR: confidence = 1 − ∏(1 − wᵢ·cᵢ). Retired hypotheses contribute nothing |
| POL-STAGE-001 | Stage advancement | Current stage = highest stage whose Domain Pack milestone is satisfied (Software Buying: 00 — §4.1 Stage Qualification Milestones) with stage confidence ≥ 0.6, where stage confidence = max confidence among hypotheses supported by the milestone-satisfying Evidence |
| POL-STAGE-002 | Stage regression | Regress on 3 consecutive high-signal events characteristic of an earlier stage |

## Recommendation & Readiness Policies

| Policy ID | Policy | v1 Value |
|---|---|---|
| POL-REC-001 | Recommendation Readiness | READY when ≥ 1 Requirement at confidence ≥ 0.6 AND journey has ≥ 5 high-signal events |
| POL-REC-002 | Ranking | Rank by weighted coverage: Critical ×3, High ×2, Medium ×1, Low ×0.5; tie-break on total capability count, then Product ID |
| POL-REC-003 | Publication | Publish top 3 entries; include up to 2 alternatives |
| POL-REC-004 | Constraint derivation | Budget Unknown when the journey contains no PRICING_VIEWED events; additional constraint rules (deployment preference, team size, data residency) deferred to v1.1 |

## Retrieval Policies (Tier 2)

| Policy ID | Policy | v1 Value |
|---|---|---|
| POL-RETR-001 | Retrieval parameters | top_K = 8 candidates |
| POL-RETR-002 | Refinement loop | max_refinements = 2; skip evaluation when top similarity ≥ 0.85 (similarity as defined in Chapter 20 — `1 − distance`, i.e. `2 × cosine − 1` in the reference deployment; see note below) |
| POL-RETR-003 | Candidate cache TTL | 1 hour |
| POL-RETR-004 | Dual-write reconciliation | Sweep retries PENDING/FAILED with exponential backoff, max 5 automatic attempts; then sticky FAILED, admin manual retry resets the counter |
| POL-GATE-001 | Gateway call bounds | Per-call timeout 30s; max 2 automatic retries with exponential backoff; then node failure → orchestration fallbacks (Chapter 21) |

**Note on POL-RETR-002's skip threshold.** The 0.85 threshold is expressed in the Chapter 20 similarity quantity, so it corresponds to cosine ≥ 0.925. Measured against the reference deployment's embedding backend, a Behavioral Query Document scores 0.29–0.34 (cosine ≈ 0.65) against its best real candidate, so the skip branch does not fire in practice and **Tier 2 evaluation runs on every retrieval**. This is the conservative direction — evaluation is a quality gate, not an optimization — and it costs one Tier 2 call per retrieval against the POL-TRIG-003 budget. The threshold is retained as the documented escape hatch for backends whose query/document vectors sit closer together; retuning it is a policy-version change, not a code change.

## Trigger, Budget & Caching Policies

| Policy ID | Policy | v1 Value |
|---|---|---|
| POL-TRIG-001 | Event accumulation | Run workflow after 5 unprocessed high/medium-signal events |
| POL-TRIG-002 | Debounce / cooldown | v1.1: Debounce 30s; cooldown 3min (STAGE_TRANSITION bypasses cooldown). v1 was 60s / 10min — retuned for demo pacing (Decision #038); historical runs recorded policy_version 1.0 |
| POL-TRIG-003 | AI budgets | Tier 1: 10 calls/user/day; Tier 2: 20 calls/user/day |
| POL-TRIG-004 | Material change | New/removed Requirement, priority band change, stage change, or top-candidate change |
| POL-TRIG-005 | Run concurrency | At most one in-flight workflow run per user; a trigger arriving during a run is recorded as SKIP (already-running) and its events remain accumulated for the next evaluation |
| POL-CACHE-001 | AAR cache | One AAR per (Recommendation Package, prompt version, surface) |

## Tracking & Session Policies

| Policy ID | Policy | v1 Value |
|---|---|---|
| POL-TRACK-001 | Client batching | batch_size = 10 events; flush_interval = 15s; failed flushes retry max 3 times with exponential backoff, then drop (low-signal first); server rejects batches > 50 events |
| POL-TRACK-002 | Dwell heartbeat | 10s cadence, visible pages only |
| POL-TRACK-003 | Session timeout | 30 minutes of inactivity |

## Learning, Decay & Journey Policies

| Policy ID | Policy | v1 Value |
|---|---|---|
| POL-LEARN-001 | Trait reinforcement | Traits are **concept-derived**: one trait per Behavioral Concept whose final hypothesis confidence ≥ 0.6 at journey closure (trait name = concept name, as the active Domain Pack defines it). On CLOSED journey: reinforce existing matching traits +0.1 (weighted by final hypothesis confidence); create new trait at strength 0.3 |
| POL-DECAY-001 | Trait decay | −0.05 per 14 inactive days; resistance ×(1 − 0.05 × min(Reinforcement Count, 10)) |
| POL-JRES-001 | Journey resolution | Reuse ACTIVE journey when resolution score ≥ 0.6 (weights: topic 0.4, behavioral 0.3, time-decay 0.3); reactivate DORMANT ≥ 0.7; else create new. Signal functions defined in Chapter 12 — Signal Computation (topic = Jaccard over entity sets; behavioral = cosine over event-type histograms; time-decay half-life 7 days). **min_session_events = 5** — ownership is deferred until a session has settled (Chapter 12 § Session Settlement, Decision #041); cold start exempt |
| POL-JRES-002 | Journey dormancy | ACTIVE → DORMANT after 7 days of inactivity (evaluated with other signals, never time alone at closure) |
| POL-JRES-003 | Journey closure | PURCHASE_COMPLETED → immediate CLOSED (Outcome: PURCHASED). TRIAL_STARTED followed by ≥ 7 days without further journey activity → CLOSED (Outcome: PURCHASED — trial-adoption fallback). DORMANT > 30 days → CLOSED (Outcome: ABANDONED). Only CLOSED journeys feed the Learning Engine |

## Delivery Policies

| Policy ID | Policy | v1 Value |
|---|---|---|
| POL-DELIV-001 | Digest eligibility | ≥ 3 high-signal events since last digest; opted-in channel |
| POL-DELIV-002 | Digest schedule & cap | Daily 17:00 platform-local; max 1 digest/user/day |

---

# Relationship to Core Documentation

This chapter defines the governance layer that separates deterministic reasoning from business policy.

Related chapters include:

| Chapter | Responsibility |
|---------|----------------|
| 03 | Behavioral Learning Engine |
| 04 | Behavioral Decay Engine |
| 05 | Confidence Engine |
| 06 | Requirement Engine |
| 07 | Journey Stage Engine |
| 08 | Recommendation Engine |
| 09 | AI Buying Advisor |
| 12 | Journey Resolution Engine |
| 13 | Event Schema |
| 17 | Platform Enumerations |
| 99 | Architecture Principles |

---

# Summary

The Decision Policy Framework governs deterministic business decisions throughout the Behavioral Intelligence Platform.

Platform engines determine truth.

Decision Policies authorize actions.

The AI Buying Advisor communicates outcomes.

This separation ensures that behavioral reasoning, business governance, and AI communication evolve independently while remaining deterministic, explainable, versioned, and fully replayable.

Decision Policies never perform behavioral reasoning.

They never invoke AI.

They never modify runtime objects.

Their sole responsibility is governing deterministic business decisions.

---
