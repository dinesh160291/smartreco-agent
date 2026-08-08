# Behavioral Reasoning Engine

**Version:** 1.0

---

# Purpose

The Behavioral Reasoning Engine (BRE) is the deterministic engine that transforms validated Behavioral Events into Behavioral Evidence and Behavioral Hypotheses.

It is the authoritative owner of the reasoning step at the front of the behavioral pipeline:

Behavioral Events

↓

Behavioral Pattern Evaluation

↓

Behavioral Evidence

↓

Behavioral Hypothesis Lifecycle

↓

Behavioral Memory

Prior documents referred to this engine inconsistently ("Behavioral Hypothesis Engine" in the Runtime Object Model, "Behavioral Reasoning Engine" in the Decision Log). This chapter is the canonical definition. The name **Behavioral Reasoning Engine (BRE)** supersedes all prior names.

---

# Guiding Principle

The BRE answers one question:

> "Given the user's observed behavior, what does the platform now believe about their intent?"

Patterns are domain knowledge. Reasoning is platform execution.

The BRE executes patterns; it never defines them.

---

# Responsibilities

The BRE is responsible for:

- Evaluating Behavioral Patterns (defined by the active Domain Pack) against incoming Behavioral Events.
- Producing Behavioral Evidence when patterns activate.
- Creating Behavioral Hypotheses from Behavioral Evidence, instantiated from Behavioral Concepts in the Domain Pack ontology.
- Linking supporting and contradicting Behavioral Evidence to existing Behavioral Hypotheses.
- Managing the Behavioral Hypothesis lifecycle (Created → Strengthened → Stable → Weakened → Retired), as authorized by Decision Policies.
- Updating Journey Memory with new Evidence and Hypothesis references.

The BRE never:

- Calculates confidence (Confidence Engine).
- Infers Requirements (Requirement Engine).
- Determines Journey Stage (Journey Stage Engine).
- Produces recommendations (Recommendation Engine).
- Modifies the Behavioral Profile (Behavioral Learning / Decay Engines).
- Invokes AI.

---

# Inputs

- Validated Behavioral Events (post Journey Resolution — every event already owns a Journey ID)
- Behavioral Patterns (active Domain Pack)
- Behavioral Ontology / Behavioral Concept Registry (active Domain Pack)
- Current Behavioral Memory (Journey Memory + Behavioral Profile as read-only priors)
- Decision Policies (hypothesis promotion, evidence expiration, conflict resolution)

---

# Outputs

- Behavioral Evidence (immutable Runtime Objects)
- Behavioral Hypothesis versions (new hypotheses, or new versions linking additional evidence / lifecycle transitions)
- Updated Journey Memory references

Confidence fields on Behavioral Hypotheses are populated exclusively by the Confidence Engine, which executes immediately after the BRE within the pipeline.

---

# Pattern Evaluation

Pattern evaluation is deterministic and replayable.

For each incoming batch of Behavioral Events, the BRE:

1. Loads the active Domain Pack's Behavioral Patterns.
2. Evaluates each pattern's Required Evidence conditions against the event window defined by the pattern.
3. On activation, produces a Behavioral Evidence Runtime Object referencing the producing pattern (BP-xxx) and the supporting events.
4. Applies Evidence deduplication: identical pattern activation over the same supporting events never produces duplicate Evidence.

Identical events evaluated by identical pattern versions always produce identical Evidence.

---

# Hypothesis Management

For each new Behavioral Evidence object, the BRE:

1. Resolves the Behavioral Concepts the Evidence supports (from the pattern definition).
2. If an active Behavioral Hypothesis exists for the concept within the Journey — links the Evidence (supporting or contradicting).
3. If none exists and Decision Policy promotion criteria are met — creates a new Behavioral Hypothesis referencing the Behavioral Concept ID.
4. Requests lifecycle transitions (e.g., Weakened, Retired) only when authorized by Decision Policy evaluation.

Hypotheses evolve incrementally. They are never recalculated from scratch.

---

# Relationship to Other Engines

| Engine | Relationship |
|---|---|
| Journey Resolution Engine | Executes before the BRE; supplies Journey ownership |
| Confidence Engine | Executes after the BRE; owns all confidence values |
| Requirement Engine | Consumes BRE-produced Hypotheses via Behavioral Memory |
| Behavioral Learning / Decay Engines | Operate on the Behavioral Profile only; never on BRE outputs |

---

# Invariants

## Invariant 1

The BRE is the exclusive producer of Behavioral Evidence and Behavioral Hypotheses.

## Invariant 2

Pattern evaluation is deterministic and replayable.

## Invariant 3

The BRE never assigns or modifies confidence.

## Invariant 4

Every Behavioral Evidence object references its producing Behavioral Pattern and supporting Behavioral Events.

## Invariant 5

Every Behavioral Hypothesis references a Behavioral Concept defined in the active Domain Pack's registry. The BRE never invents concepts.

## Invariant 6

The BRE never invokes an LLM.

## Invariant 7

The BRE hardcodes no thresholds. Promotion, expiration, and lifecycle rules come from Decision Policies.

---

# Claude Implementation Contract

Claude MUST:

- Implement pattern evaluation as pure deterministic logic over event windows.
- Produce Evidence and Hypotheses conforming to the Runtime Object Model.
- Reference Behavioral Concept IDs from the Domain Pack registry.
- Preserve lineage: Event → Pattern → Evidence → Hypothesis.
- Delegate confidence to the Confidence Engine.
- Respect Decision Policies for promotion and lifecycle transitions.

Claude MUST NOT:

- Generate Evidence or Hypotheses with AI.
- Duplicate Evidence for identical pattern activations.
- Recalculate Hypotheses from scratch.
- Modify the Behavioral Profile.
- Hardcode business thresholds.

---

# Relationship to Core Documentation

| Chapter | Responsibility |
|---------|----------------|
| 01 | Behavioral Hypotheses (object semantics) |
| 02 | Behavioral Memory |
| 05 | Confidence Engine |
| 10 | Decision Policies |
| 12 | Journey Resolution Engine |
| 13 | Event Schema |
| 18 | Runtime Object Model |
| 21 | Agent Orchestration |

---

# Summary

The Behavioral Reasoning Engine is the deterministic entry point of behavioral understanding: it executes Domain Pack patterns against immutable events, produces Evidence, and maintains the Hypothesis lifecycle. It owns the step every downstream engine depends on — and nothing else.

---
