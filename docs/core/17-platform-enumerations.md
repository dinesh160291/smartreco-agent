# Platform Enumerations

**Version:** 1.0

---

# Purpose

The Platform Enumerations document defines the canonical vocabulary used throughout the Behavioral Intelligence Platform.

Platform Enumerations provide strongly typed values for every categorical runtime field.

Enumerations improve:

- Determinism
- Validation
- Type Safety
- Replayability
- API Compatibility
- Platform Consistency

Platform Enumerations never define business logic.

They define allowed values only.

---

# Guiding Principle

Every categorical runtime field must use a strongly typed enumeration.

Free-text values are prohibited for categorical runtime fields.

Every platform component references the same canonical enumeration definitions.

---

# Core Principle

Platform Enumerations

↓

Runtime Objects

↓

Platform Engines

↓

Decision Policies

↓

API Contracts

↓

LLM Contract

↓

AI Buying Advisor

Platform Enumerations provide the canonical vocabulary shared across the entire platform.

---

# Responsibilities

Platform Enumerations are responsible for:

- Defining canonical platform vocabulary.
- Defining strongly typed categorical values.
- Supporting validation.
- Supporting deterministic replay.
- Supporting API compatibility.
- Supporting versioning.
- Supporting platform consistency.

Platform Enumerations never:

- Define business logic.
- Perform deterministic reasoning.
- Define recommendation behavior.
- Invoke AI.

Their sole responsibility is defining the canonical platform vocabulary.

---

# Enumeration Philosophy

Enumerations define the official platform vocabulary.

Every runtime object, platform engine, Decision Policy, API Contract, and LLM Contract references these definitions.

Enumerations define allowed values.

They never define behavior.

Behavior is determined by platform engines together with Decision Policies.

---

# Enumeration Ownership

Platform Enumerations are owned by the Core Platform.

Domain Enumerations are owned by Domain Packs.

The Core Platform never defines domain-specific values.

Domain Packs never redefine Platform Enumerations.

This separation preserves a domain-agnostic core platform while allowing domain-specific extension.

---

# Platform Enumerations

## JourneyLifecycle

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| NEW | New | Journey has been created but not yet processed. |
| ACTIVE | Active | Journey is currently progressing. |
| DORMANT | Dormant | Journey is temporarily inactive but may be resumed. |
| CLOSED | Closed | Journey has reached a deterministic business outcome. |
| ARCHIVED | Archived | Historical immutable Journey retained for replay, auditing, and analytics. |

**Used By**

- Journey Resolution Engine
- Behavioral Memory
- Decision Policy Framework
- API Contracts

---

## JourneyOutcome

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| PURCHASED | Purchased | Journey completed with a successful purchase. |
| ABANDONED | Abandoned | Journey ended without a purchase. |
| CANCELLED | Cancelled | Journey was intentionally cancelled. *(Reserved — no v1 closure rule produces this value.)* |
| NO_DECISION | No Decision | Journey closed without a definitive outcome. *(Reserved — no v1 closure rule produces this value.)* |

**Used By**

- Behavioral Memory
- Behavioral Learning Engine
- Journey Resolution Engine
- Observability

---

## RecommendationReadiness

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| READY | Ready | The platform has sufficient deterministic evidence to publish recommendations. |
| NOT_READY | Not Ready | Additional deterministic evidence is required before recommendations may be published. |

**Used By**

- Recommendation Engine
- AI Buying Advisor
- Decision Policy Framework

---

## ConfidenceLevel

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| VERY_LOW | Very Low | Minimal confidence. |
| LOW | Low | Weak confidence. |
| MEDIUM | Medium | Moderate confidence. |
| HIGH | High | Strong confidence. |
| VERY_HIGH | Very High | Very strong confidence. |

**Note**

ConfidenceLevel is a presentation bucket.

The platform always stores numeric confidence values.

**Used By**

- Confidence Engine
- AI Buying Advisor
- Observability

---

## EngineStatus

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| PENDING | Pending | Engine has not started. |
| RUNNING | Running | Engine is currently executing. |
| COMPLETED | Completed | Engine finished successfully. |
| FAILED | Failed | Engine execution failed. |
| SKIPPED | Skipped | Engine execution was intentionally skipped. |

**Used By**

- Observability
- Replay
- Platform Monitoring

---

## PolicyEvaluationStatus

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| PASSED | Passed | Policy conditions were satisfied. |
| FAILED | Failed | Policy conditions were not satisfied. |
| NOT_APPLICABLE | Not Applicable | Policy did not apply to the current evaluation. |

**Used By**

- Decision Policy Framework
- Observability
- Replay

---

## AIResponseStatus

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| GENERATED | Generated | AI Advisory Response successfully created. |
| BLOCKED | Blocked | AI communication was intentionally prevented. |
| CLARIFICATION_REQUIRED | Clarification Required | Additional information is required before AI communication may proceed. |

**Used By**

- AI Buying Advisor
- LLM Contract

---

## SyncStatus

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| PENDING | Pending | Relational record written; vector synchronization not yet completed. |
| SYNCED | Synced | Relational and vector representations are consistent. |
| FAILED | Failed | Vector synchronization failed; eligible for reconciliation retry. |

**Used By**

- Semantic Retrieval Engine (dual-write contract)
- Admin Product APIs
- Observability

---

## TriggerType

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| SIGNIFICANT_EVENT | Significant Event | A high-signal Behavioral Event arrived. |
| EVENT_ACCUMULATION | Event Accumulation | Unprocessed event count crossed the policy threshold. |
| SESSION_END | Session End | A session closed with meaningful unprocessed activity. |
| STAGE_TRANSITION | Stage Transition | The Journey Stage changed. |
| REQUIREMENT_SHIFT | Requirement Shift | A materially new Requirement Profile version was published. |
| SCHEDULED | Scheduled | A background schedule fired (e.g., daily digest). |
| ADMIN_CATALOG_CHANGE | Admin Catalog Change | Product mutations invalidated dependent cached artifacts. |

**Used By**

- Execution Triggers & Caching
- Agent Orchestration
- Observability

---

## SignalClass

**Version:** 1.0

**Owner:** Core Platform (values assigned to Event Types by the active Domain Pack)

| Code | Display Name | Description |
|------|--------------|-------------|
| HIGH | High Signal | Strong behavioral meaning; protected from overflow loss; may fire triggers. |
| MEDIUM | Medium Signal | Moderate behavioral meaning; contributes to accumulation. |
| LOW | Low Signal | Weak individual meaning (e.g., dwell heartbeats); droppable under pressure. |

**Used By**

- Event Ingestion & Tracking
- Execution Triggers & Caching

---

## DeliveryStatus

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| SENT | Sent | Delivery completed successfully. |
| FAILED | Failed | Delivery attempted and failed. |
| SKIPPED | Skipped | User ineligible this window (recorded with reason). |

**Used By**

- Proactive Delivery
- Observability

---

## DeliveryChannel

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| TELEGRAM | Telegram | Telegram bot delivery (primary reference adapter). |
| EMAIL | Email | SMTP email delivery (optional adapter). |

**Used By**

- Proactive Delivery
- Authentication & Account APIs (digest preferences)

---

## AARSurface

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| ONSITE | On-site | AAR generated for the recommendations page. |
| DIGEST | Digest | AAR generated for proactive delivery. |

**Used By**

- AI Buying Advisor
- Proactive Delivery
- Caching (AAR cache key component)

---

## HypothesisStatus

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| CREATED | Created | Hypothesis newly instantiated from Evidence. |
| STRENGTHENED | Strengthened | Confidence rising on recent updates. |
| STABLE | Stable | Confidence steady across recent updates. |
| WEAKENED | Weakened | Confidence declining (contradiction or decay). |
| RETIRED | Retired | Below retirement threshold; preserved in history, contributes nothing downstream. |

**Used By**

- Behavioral Reasoning Engine
- Confidence Engine
- Requirement Engine (retired hypotheses excluded)

---

## EvidenceStrength

**Version:** 1.0

**Owner:** Core Platform (levels assigned by Domain Pack patterns)

| Code | Display Name | Description |
|------|--------------|-------------|
| WEAK | Weak | Minimal deterministic signal. |
| MEDIUM | Medium | Moderate signal; qualifies evaluation-stage milestones. |
| STRONG | Strong | Strong signal. |
| VERY_STRONG | Very Strong | Decisive signal (e.g., checkout events). |

**Used By**

- Behavioral Patterns (production)
- Confidence Engine (POL-CONF-001 contributions)
- Journey Stage Engine (milestones)

---

## RequirementPriority

**Version:** 1.0

**Owner:** Core Platform

| Code | Display Name | Description |
|------|--------------|-------------|
| CRITICAL | Critical | Band per POL-REQ-002; ranking weight ×3. |
| HIGH | High | Ranking weight ×2. |
| MEDIUM | Medium | Ranking weight ×1. |
| LOW | Low | Ranking weight ×0.5. |

**Used By**

- Requirement Engine
- Recommendation Engine (POL-REC-002 weighting)
- AI Buying Advisor (presentation)

---

# Domain Enumerations

The Core Platform defines only platform-wide enumerations.

Domain-specific enumerations are owned by the active Domain Pack.

Examples include:

- EventType
- ProductCategory
- Capability
- SearchIntent
- BehavioralPatternType
- EvidenceType
- JourneyStage

Each Domain Pack:

- Defines its own enumeration values.
- Versions its own enumerations.
- Owns its own vocabulary.
- Extends the platform without modifying Core Platform enumerations.

This separation preserves a stable, domain-agnostic platform while enabling domain-specific customization.

---

# Enumeration Versioning

Every enumeration includes:

- Enumeration Name
- Version
- Owner
- Allowed Values

Versioning Rules:

- Enumeration codes are immutable.
- Existing codes are never renamed.
- Existing codes are never repurposed.
- New values require a version update.
- Deprecated values remain available until formally removed.

Replay always uses the historical enumeration version that existed when runtime objects were created.

Enumeration versioning guarantees deterministic replay and long-term platform stability.

---

# Relationship to Decision Policies

Decision Policies consume Platform Enumerations.

Platform Enumerations never define policy behavior.

Examples include:

- RecommendationReadiness
- JourneyLifecycle
- PolicyEvaluationStatus
- AIResponseStatus

Decision Policies determine how enumeration values influence business decisions.

Platform Enumerations define only the allowed values.

---

# Relationship to Domain Packs

The Core Platform owns platform-wide enumerations.

Domain Packs own domain-specific enumerations.

The Core Platform defines:

- Structure
- Ownership
- Versioning
- Validation Rules

Domain Packs define:

- Domain vocabulary
- Business capabilities
- Product categories
- Event types
- Journey stages

Neither layer modifies the other.

This separation allows new domains to be added without changing the Core Platform.

---

# Relationship to the Platform

Platform Enumerations provide the canonical vocabulary shared across the Behavioral Intelligence Platform.

Every platform component references Platform Enumerations for categorical runtime fields.

Components include:

- Runtime Objects
- Platform Engines
- Decision Policy Framework
- API Contracts
- LLM Contract
- AI Buying Advisor
- Observability
- Replay

Platform Enumerations are the single source of truth for categorical values.

---

# Interaction with Platform Components

Platform Enumerations

↓

Runtime Objects

↓

Platform Engines

↓

Decision Policies

↓

API Contracts

↓

LLM Contract

↓

AI Buying Advisor

Every categorical runtime value originates from Platform Enumerations or the active Domain Pack.

---

# Enumeration Invariants

## Invariant 1

Every categorical runtime field uses a strongly typed enumeration.

---

## Invariant 2

Platform Enumerations are owned by the Core Platform.

---

## Invariant 3

Domain Enumerations are owned by Domain Packs.

---

## Invariant 4

Enumeration codes are immutable.

---

## Invariant 5

Enumerations are versioned.

---

## Invariant 6

Free-text values are prohibited for categorical runtime fields.

---

## Invariant 7

API Contracts exchange enumeration codes, never display labels.

---

## Invariant 8

Historical enumeration versions remain available for deterministic replay.

---

## Invariant 9

Platform Enumerations never define business logic.

---

# Design Principles

The Platform Enumerations follow these architectural principles.

## Principle 1

Every categorical runtime value is strongly typed.

---

## Principle 2

Platform vocabulary has a single authoritative owner.

---

## Principle 3

Platform Enumerations remain domain-agnostic.

---

## Principle 4

Domain Packs extend platform vocabulary without modifying it.

---

## Principle 5

Enumeration versioning supports deterministic replay.

---

## Principle 6

Business logic remains external to Platform Enumerations.

---

# Claude Implementation Contract

Claude MUST:

- Respect Platform Enumerations.
- Validate enumeration values.
- Reject unsupported values.
- Respect enumeration versions.
- Respect Domain Pack enumerations.
- Preserve replayability.

Claude MUST NOT:

- Invent enumeration values.
- Rename enumeration codes.
- Generate free-text categorical values.
- Modify historical enumeration definitions.
- Override Platform Enumeration ownership.

---

# Relationship to Core Documentation

This chapter defines the canonical vocabulary shared across the Behavioral Intelligence Platform.

Related chapters include:

| Chapter | Responsibility |
|---------|----------------|
| 06 | Requirement Engine |
| 07 | Journey Stage Engine |
| 08 | Recommendation Engine |
| 10 | Decision Policies |
| 11 | Observability and Evaluation |
| 12 | Journey Resolution Engine |
| 13 | Event Schema |
| 14 | Product Catalog |
| 15 | LLM Contract |
| 16 | API Contracts |
| 99 | Architecture Principles |

---

# Summary

Platform Enumerations define the canonical vocabulary for the Behavioral Intelligence Platform.

They provide strongly typed, versioned, deterministic categorical values shared across runtime objects, platform engines, Decision Policies, API Contracts, the LLM Contract, and the AI Buying Advisor.

They never define business logic.

They never perform deterministic reasoning.

They serve as the single source of truth for categorical values while enabling deterministic validation, replay, interoperability, and long-term platform stability.

---
