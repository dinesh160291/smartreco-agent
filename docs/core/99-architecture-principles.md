# Architecture Principles

**Version:** 1.0

**The Constitution of the Behavioral Intelligence Platform**

---

# Purpose

This document defines the fundamental architectural principles governing the Behavioral Intelligence Platform.

These principles are technology independent.

They apply regardless of:

- Programming language
- Database
- Cloud provider
- LLM provider
- Deployment model
- User interface
- Domain

Every platform component must conform to these principles.

When implementation details conflict with these principles, the principles take precedence.

If a future design violates one or more of these principles, the design must be challenged before implementation proceeds.

This document is the constitutional authority for the platform architecture.

---

# Platform Philosophy

## Principle 1

The platform establishes truth.

AI communicates truth.

---

## Principle 2

Deterministic reasoning always precedes AI.

AI never replaces deterministic reasoning.

---

## Principle 3

Behavior creates Behavioral Hypotheses.

Behavioral Hypotheses create Requirements.

Requirements drive Recommendations.

Recommendations are communicated by AI.

---

## Principle 4

The platform reasons only from observed facts.

It never reasons from assumptions.

---

## Principle 5

Platform responsibilities are separated into independent architectural layers.

- Platform Engines determine truth.
- Decision Policies authorize actions.
- AI communicates outcomes.

No platform component performs responsibilities belonging to another layer.

---

# AI Principles

## Principle 6

AI never owns platform state.

---

## Principle 7

AI never makes deterministic platform decisions.

---

## Principle 8

AI never modifies runtime objects.

---

## Principle 9

AI communicates only verified deterministic runtime objects.

---

## Principle 10

AI behavior is governed exclusively by the LLM Contract.

LLM implementations may change.

The LLM Contract remains stable.

---

## Principle 11

AI operates only within the two sanctioned tiers of the AI boundary:

**Tier 1 — Generative Communication.** The AI Buying Advisor, which begins only after deterministic reasoning has completed. AI communicates truth; it never establishes it.

**Tier 2 — Semantic Services.** Embeddings, retrieval-quality evaluation, and query refinement, permitted exclusively inside the Semantic Retrieval Engine. Tier 2 proposes candidates; it never produces final rankings, never modifies deterministic Runtime Objects, and never influences Recommendation Readiness.

Outside these two tiers, AI never participates in platform reasoning. Deterministic engines remain AI-free.

(Amended by Decision #031 — the two-tier AI boundary.)

---

# Runtime Object Principles

## Principle 12

Runtime Objects are immutable after publication.

---

## Principle 13

Runtime Objects are versioned.

---

## Principle 14

Every Runtime Object has exactly one authoritative owner.

Ownership is explicit.

Ownership is never shared.

---

## Principle 15

Runtime Objects communicate through well-defined contracts.

---

## Principle 16

Runtime Objects preserve deterministic replay.

---

## Principle 17

Runtime Objects never contain AI-generated information.

---

## Principle 18

Every major platform artifact is:

- Immutable after publication.
- Versioned.
- Replayable.
- Explainable.
- Independently evolvable.

Examples include:

- Behavioral Events
- Behavioral Memory
- Behavioral Hypotheses
- Requirement Profiles
- Journey Resolution Results
- Recommendation Packages
- Policy Evaluation Results
- Platform Enumerations
- API Contracts
- Prompt Contracts

---

# Engine Principles

## Principle 19

Every platform engine has exactly one responsibility.

---

## Principle 20

Platform engines communicate exclusively through strongly typed runtime objects.

---

## Principle 21

Platform engines never modify upstream runtime objects.

---

## Principle 22

Platform engines are deterministic.

---

## Principle 23

Every platform engine is independently testable.

---

## Principle 24

Platform engines determine truth.

They never authorize business policy.

They never communicate directly with users.

---

# Decision Policy Principles

## Principle 25

Business rules belong exclusively in the Decision Policy Framework.

Platform engines determine truth.

Decision Policies authorize actions.

---

## Principle 26

Business rules and thresholds are defined in Decision Policies.

They never appear inside platform engines.

---

## Principle 27

Every deterministic business decision is explainable.

Every decision references supporting runtime objects and Decision Policy evaluations.

---

## Principle 28

Every deterministic business decision is observable.

Every decision emits observable metadata.

---

## Principle 29

Every deterministic business decision is replayable.

Replay always uses:

- Historical Runtime Object Versions
- Historical Decision Policy Versions
- Historical Enumeration Versions

---

## Principle 30

Decision Policies evolve independently of platform engines.

Business evolution never requires deterministic engine implementation changes.

---

# Data Principles

## Principle 31

Behavioral Events are immutable facts.

---

## Principle 32

Capture facts.

Infer meaning later.

Behavioral meaning is never stored inside Behavioral Events.

---

## Principle 33

Every categorical runtime field uses a strongly typed enumeration.

Free-text values are prohibited for categorical runtime fields.

---

## Principle 34

Platform vocabulary is defined once through Platform Enumerations.

Every platform component references the same canonical vocabulary.

---

## Principle 35

Every platform contract is versioned.

Examples include:

- Runtime Objects
- Event Schemas
- Platform Enumerations
- API Contracts
- Prompt Contracts
- Product Capability Profiles

Versioning guarantees deterministic replay and long-term compatibility.

---

## Principle 36

Historical platform artifacts are never modified.

New versions extend the platform.

They never rewrite history.

---

# Contract Principles

## Principle 37

Platform components communicate through contracts.

They never communicate through implementation details.

---

## Principle 38

Contracts define interaction.

Implementation remains replaceable.

---

## Principle 39

Contracts are stable.

Implementations evolve.

---

## Principle 40

Every platform contract has exactly one authoritative owner.

Ownership is explicit.

Ownership is never shared.

---

## Principle 41

The platform is contract-first.

Contracts define the architecture.

Implementations fulfill those contracts.

---

# Domain Principles

## Principle 42

The Core Platform defines infrastructure and contracts.

---

## Principle 43

Domain Packs define business knowledge.

Examples include:

- Event Types
- Journey Stages
- Product Categories
- Business Capabilities
- The Product Capability Profile contract and reference profiles

Runtime product **records** are data, not knowledge: they are managed by administrators through platform APIs and the dual-write contract, always conforming to the Domain Pack's taxonomy. (Amended by Decision #030 — contract vs. data.)

---

## Principle 44

The Core Platform never owns domain knowledge.

---

## Principle 45

Domain Packs never redefine Core Platform contracts.

They extend the platform through approved extension points.

---

## Principle 46

New business domains integrate through Domain Packs.

The Core Platform remains domain-agnostic.

---

# Engineering Principles

## Principle 47

No platform engine guesses.

Every deterministic decision is supported by observable evidence.

---

## Principle 48

No hidden assumptions.

Every business rule, threshold, and transition is explicitly defined.

---

## Principle 49

No circular dependencies.

Platform dependencies always flow in one direction.

---

## Principle 50

Every platform component has exactly one responsibility.

Responsibilities are never duplicated.

Responsibilities are never shared.

---

## Principle 51

Every platform component has exactly one authoritative owner.

Ownership is explicit.

Ownership is never shared.

---

## Principle 52

Design for replacement, not permanence.

Implementations evolve.

Contracts remain stable.

---

## Principle 53

Prefer composition over coupling.

Platform components communicate through contracts.

Platform components never depend on internal implementation details.

---

# Cross-Cutting Capability Principles

## Principle 54

Observability is a platform capability.

It is not owned by a single engine.

Every platform component participates in observability.

---

## Principle 55

Replay is a platform capability.

Every deterministic decision supports deterministic replay.

---

## Principle 56

Explainability is a platform capability.

Every deterministic decision can be explained using supporting runtime objects.

AI may communicate explanations.

AI never creates deterministic explanations.

---

## Principle 57

Traceability is a platform capability.

Every runtime object maintains complete lineage.

Every deterministic decision is traceable from Behavioral Event to AI Advisory Response.

---

## Principle 58

Versioning is a platform capability.

Every major platform artifact is versioned.

Versioning enables replay, compatibility, auditing, and long-term evolution.

---

## Principle 59

Validation is a platform capability.

Every platform contract validates structure before deterministic reasoning begins.

Validation never performs behavioral reasoning.

---

# Future Evolution Principles

## Principle 60

The platform evolves by extending contracts.

Existing contracts remain stable whenever possible.

---

## Principle 61

New domains integrate through Domain Packs.

The Core Platform remains domain-agnostic.

---

## Principle 62

New AI models integrate through the LLM Contract.

Platform architecture remains independent of LLM implementation.

---

## Principle 63

Business evolution occurs through Decision Policies.

Platform engines remain stable.

---

## Principle 64

Platform evolution preserves backward compatibility.

Historical artifacts remain replayable.

---

## Principle 65

Platform architecture outlives individual implementations.

Technologies may change.

The architecture remains stable.

---

## Principle 66

The architecture is contract-first.

Contracts define behavior.

Implementations fulfill contracts.

---

# The Constitution

The Behavioral Intelligence Platform is founded on the following constitutional principles.

The platform establishes truth.

AI communicates truth.

Deterministic reasoning always precedes AI.

Behavior creates Behavioral Hypotheses.

Behavioral Hypotheses create Requirements.

Requirements drive Recommendations.

Recommendations are communicated by AI.

Platform Engines determine truth.

Decision Policies authorize actions.

AI communicates outcomes.

Capture facts.

Infer meaning later.

Behavioral Events are immutable.

Runtime Objects are immutable after publication.

Every Runtime Object has exactly one authoritative owner.

Every platform component has exactly one responsibility.

Every deterministic decision is explainable.

Every deterministic decision is observable.

Every deterministic decision is replayable.

Business rules belong exclusively in the Decision Policy Framework.

Platform components communicate through contracts.

Implementation details remain replaceable.

Contracts remain stable.

The platform is contract-first.

The Core Platform defines infrastructure and contracts.

Domain Packs define knowledge.

Platform Enumerations define canonical vocabulary.

Every categorical runtime value is strongly typed.

Version everything.

Observe everything.

Replay everything.

Explain everything.

No platform engine guesses.

No hidden assumptions.

No circular dependencies.

Design for replacement, not permanence.

Architecture outlives implementation.

Technology evolves.

Contracts evolve carefully.

Architecture endures.

---

# Final Architectural Statement

The Behavioral Intelligence Platform is a deterministic, explainable, replayable, contract-first architecture.

Its purpose is to transform observed behavior into trustworthy business intelligence through deterministic reasoning, governed business policies, and responsible AI communication.

Every architectural decision should reinforce:

- Determinism
- Explainability
- Replayability
- Traceability
- Versioning
- Clear ownership
- Stable contracts
- Separation of responsibilities

When implementation choices conflict with these principles, the principles prevail.

The Constitution is the highest architectural authority of the Behavioral Intelligence Platform.

---
