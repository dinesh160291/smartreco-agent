# Business Requirement to Capability Mapping

**Version:** 1.0

---

# Purpose

The Business Requirement to Capability Mapping document defines the canonical relationships between Business Requirements and Capabilities within the Software Buying Domain.

Business Requirement Mappings represent reference knowledge.

They are not Runtime Objects.

They are not user-specific.

They do not contain recommendation logic.

They do not perform capability matching.

They do not change based on individual user behavior.

Business Requirement Mappings reference canonical Business Requirements defined by the Business Requirement Catalog.

They reference canonical Capabilities defined by the Capability Catalog.

They do not redefine either Business Requirements or Capabilities.

This document serves as the authoritative mapping layer between business needs and solution capabilities.

---

# Guiding Principle

Business Requirements describe **what organizations need**.

Capabilities describe **what solutions provide**.

Business Requirement Mappings define the semantic relationships between Business Requirements and Capabilities.

The Recommendation Engine performs deterministic capability matching using these mappings.

The mapping document defines reference knowledge only.

It never performs capability matching.

It never performs scoring.

It never performs ranking.

It never selects products.

---

# Separation of Responsibilities

Business Requirement Catalog

↓

Defines

↓

Business Requirements (REQ)

↓

referenced by

↓

Business Requirement Mapping

↓

references

↓

Capability Catalog

↓

Capabilities (CAP)

↓

referenced by

↓

Product Capability Profiles

↓

consumed by

↓

Recommendation Engine

↓

Recommendation Package

---

Business Requirements are reference knowledge.

Capabilities are reference knowledge.

Business Requirement Mappings are reference knowledge.

Product Capability Profiles are reference knowledge.

Recommendation Packages are Runtime Objects.

The Recommendation Engine is responsible for traversing Business Requirement Mappings, evaluating Product Capability Profiles, and producing Recommendation Packages.

---

# Why This Separation Exists

Business Requirements describe business needs.

Capabilities describe solution functionality.

The Business Requirement Mapping defines the canonical relationships between them.

The Recommendation Engine traverses those relationships during runtime.

Each component owns a single responsibility.

Business Requirement Catalog

↓

Defines Business Requirements

------------------------------------

Business Requirement Mapping

↓

Defines REQ → CAP relationships

------------------------------------

Capability Catalog

↓

Defines Capabilities

------------------------------------

Recommendation Engine

↓

Traverses mappings

↓

Evaluates Product Capability Profiles

↓

Produces Recommendation Packages

No knowledge is duplicated.

Every reusable concept has one canonical home.

---

# Relationship to Runtime Objects

Business Requirement Mappings never contain Runtime Objects.

Instead, Runtime Objects consume the mapping definitions during execution.

Requirement Profile

↓

Business Requirements

↓

Business Requirement Mapping

↓

Capabilities

↓

Product Capability Profiles

↓

Recommendation Package

Runtime Objects evolve continuously.

Reference knowledge remains stable.

---

# Relationship to Other Domain Knowledge

The Software Buying Domain contains multiple layers of reference knowledge.

Behavioral Ontology

↓

Defines Behavioral Concepts

↓

Behavioral Concept Mapping

↓

Defines Behavioral Concept → Business Requirement relationships

↓

Business Requirement Catalog

↓

Defines Business Requirements

↓

Business Requirement Mapping

↓

Defines Business Requirement → Capability relationships

↓

Capability Catalog

↓

Defines Capabilities

↓

Product Capability Profiles

↓

Defines supported Capabilities

Together these documents define the complete Software Buying knowledge graph.

The Recommendation Engine consumes these reference documents while producing Recommendation Packages during execution.

---

# Scope

This document defines:

- Business Requirement identifiers
- Business Requirement to Capability relationships
- Mapping relationship types
- Mapping rationale
- Related Capabilities
- Mapping examples

This document does not define:

- Runtime Objects
- Requirement Profiles
- Recommendation logic
- Recommendation scores
- Product rankings
- Decision Policies
- Product Capability Profiles
- AI reasoning
- Confidence values

---

# Business Requirement to Capability Mapping Definition

Every Business Requirement to Capability Mapping represents a canonical relationship between a Business Requirement and one or more Capabilities within the Software Buying Domain.

Business Requirement Mappings are static reference knowledge.

They are never Runtime Objects.

They are deterministic.

They are domain-specific.

They do not perform capability matching.

They define semantic relationships that are traversed by the Recommendation Engine during runtime.

Business Requirement Mappings reference:

- Business Requirements defined by the Business Requirement Catalog
- Capabilities defined by the Capability Catalog

Business Requirement Mappings never redefine either object.

Every Business Requirement Mapping must contain the following sections.

---

## Business Requirement ID

A unique identifier for the Business Requirement.

Business Requirement IDs remain stable across Domain Pack versions.

Example:

```text
REQ-001
```

Business Requirement Mappings reference Requirement IDs rather than duplicating Business Requirement definitions.

---

## Business Requirement Name

The canonical name of the Business Requirement.

Examples include:

- Secure Collaboration
- Identity Management
- Workflow Automation
- Regulatory Compliance
- AI Assistance

Business Requirement names remain stable across Domain Pack versions.

---

## Mapped Capability IDs

Defines the Capabilities associated with the Business Requirement.

Capabilities are referenced using Capability IDs.

Example:

```text
CAP-001

CAP-002

CAP-007

CAP-010
```

Capability definitions remain centralized within the Capability Catalog.

---

## Mapping Relationships

Defines how strongly each Capability contributes to satisfying the Business Requirement.

Relationship Types:

- Primary Association
- Secondary Association
- Supporting Association

These relationship types represent domain knowledge.

They are not probabilities.

They are not confidence values.

They are not runtime scores.

The Recommendation Engine interprets these relationships during deterministic capability matching.

---

## Mapping Rationale

Explains why each Capability is associated with the Business Requirement.

Mapping Rationales are authored by domain experts.

They provide business context for the relationship.

Example:

```text
Organizations requiring Identity Management
must first establish secure authentication
before implementing broader identity
governance capabilities.
```

---

## Related Capabilities

Defines Capabilities that frequently complement one another.

These relationships improve explainability while remaining independent of recommendation logic.

Example:

Single Sign-On

↓

Related Capabilities

- Multi-Factor Authentication
- SCIM Provisioning
- Conditional Access

---

## Mapping Notes

Provides additional implementation guidance or business context.

Mapping Notes never contain:

- Recommendation logic
- Runtime capability matching
- Decision Policies
- Confidence values

They exist solely to improve understanding of the mapping.

---

# Mapping Relationships

Business Requirement Mappings define one of three semantic relationship types.

These relationship types describe how Capabilities contribute to satisfying Business Requirements.

They are reference relationships.

They are not runtime priorities.

They are not probabilities.

---

## Primary Association

A Primary Association represents a Capability that is fundamental to satisfying the Business Requirement.

Every Business Requirement must have at least one Primary Association.

Primary Associations provide the strongest business justification for capability matching.

Example:

```text
REQ-002

Identity Management

↓

Primary Association

↓

CAP-001

Single Sign-On
```

---

## Secondary Association

A Secondary Association represents a Capability that meaningfully enhances the Business Requirement but is typically complemented by Primary Capabilities.

Example:

```text
REQ-002

Identity Management

↓

Secondary Association

↓

CAP-003

SCIM Provisioning
```

---

## Supporting Association

A Supporting Association represents a Capability that reinforces the Business Requirement but is rarely sufficient on its own.

Supporting Associations improve completeness and explainability.

Example:

```text
REQ-002

Identity Management

↓

Supporting Association

↓

CAP-010

Audit Logging
```

---

# Relationship Hierarchy

A single Business Requirement may map to multiple Capabilities.

Each relationship represents a different semantic association.

Example:

```text
REQ-002

Identity Management

        │
        │ Primary Association
        ▼
CAP-001
Single Sign-On

        │
        │ Primary Association
        ▼
CAP-002
Multi-Factor Authentication

        │
        │ Secondary Association
        ▼
CAP-003
SCIM Provisioning

        │
        │ Supporting Association
        ▼
CAP-010
Audit Logging
```

The Business Requirement remains unchanged.

The Capabilities remain unchanged.

Only the semantic relationships differ.

---

# Why Relationship Types Exist

Relationship Types improve deterministic capability matching while remaining independent of runtime implementation.

They provide:

- Explainability
- Traceability
- Consistent domain knowledge
- Deterministic capability relationships

Relationship Types do not determine whether a product is recommended.

The Recommendation Engine determines that during runtime by evaluating Product Capability Profiles against the required Capabilities.

The Mapping document simply defines how Business Requirements are semantically related to Capabilities.

---

# Canonical Business Requirement Mappings

The following examples establish the canonical mapping structure used throughout the Software Buying Domain.

Business Requirement Mappings define semantic relationships between Business Requirements and Capabilities.

They do not perform capability matching.

They provide the reference knowledge consumed by the Recommendation Engine.

---

# REQ-001 — Secure Collaboration

## Business Requirement

Secure Collaboration

---

## Mapped Capability IDs

### Primary Association

```text
CAP-001   Single Sign-On

CAP-002   Multi-Factor Authentication

CAP-007   Document Collaboration
```

### Secondary Association

```text
CAP-005   Messaging

CAP-006   Video Meetings
```

### Supporting Association

```text
CAP-010   Audit Logging

CAP-011   Encryption
```

---

## Mapping Rationale

Organizations requiring Secure Collaboration must first establish trusted identity and secure access.

Document Collaboration forms the core capability required for collaborative work.

Messaging and Video Meetings enhance collaboration, while Audit Logging and Encryption strengthen governance and protection.

---

## Related Capabilities

- Single Sign-On
- Multi-Factor Authentication
- Document Collaboration
- Encryption

---

## Mapping Notes

Secure Collaboration requires both collaboration capabilities and foundational security capabilities to deliver a complete business solution.

---

# REQ-002 — Identity Management

## Business Requirement

Identity Management

---

## Mapped Capability IDs

### Primary Association

```text
CAP-001   Single Sign-On

CAP-002   Multi-Factor Authentication
```

### Secondary Association

```text
CAP-003   SCIM Provisioning

CAP-004   Conditional Access
```

### Supporting Association

```text
CAP-010   Audit Logging
```

---

## Mapping Rationale

Identity Management begins with secure authentication.

Identity lifecycle management and access governance expand those foundational capabilities.

Audit Logging reinforces operational governance and security visibility.

---

## Related Capabilities

- Single Sign-On
- Multi-Factor Authentication
- Conditional Access

---

## Mapping Notes

Identity Management focuses on secure access, authentication, authorization, and identity lifecycle management.

---

# REQ-003 — Workflow Automation

## Business Requirement

Workflow Automation

---

## Mapped Capability IDs

### Primary Association

```text
CAP-015   Workflow Automation

CAP-016   Integration Connectors
```

### Secondary Association

```text
CAP-017   Event Triggers

CAP-018   Business Rules
```

### Supporting Association

```text
CAP-019   API Integration
```

---

## Mapping Rationale

Workflow Automation requires the ability to orchestrate business processes.

Integration Connectors enable communication between systems.

Event Triggers and Business Rules expand automation flexibility.

API Integration provides extensibility across enterprise platforms.

---

## Related Capabilities

- Workflow Automation
- Integration Connectors
- Event Triggers

---

## Mapping Notes

Workflow Automation emphasizes operational efficiency through deterministic process execution.

---

# REQ-004 — Regulatory Compliance

## Business Requirement

Regulatory Compliance

---

## Mapped Capability IDs

### Primary Association

```text
CAP-010   Audit Logging

CAP-012   Information Governance
```

### Secondary Association

```text
CAP-013   Data Retention

CAP-014   eDiscovery
```

### Supporting Association

```text
CAP-001   Single Sign-On
```

---

## Mapping Rationale

Compliance initiatives require governance, traceability, and information management.

Identity capabilities reinforce compliance by ensuring controlled access to regulated resources.

---

## Related Capabilities

- Audit Logging
- Information Governance
- Data Retention

---

## Mapping Notes

Compliance capabilities primarily address governance and regulatory obligations rather than collaboration or productivity.

---

# REQ-005 — AI Assistance

## Business Requirement

AI Assistance

---

## Mapped Capability IDs

### Primary Association

```text
CAP-020   AI Chat

CAP-021   Content Generation
```

### Secondary Association

```text
CAP-022   Intelligent Search

CAP-023   Document Summarization
```

### Supporting Association

```text
CAP-015   Workflow Automation
```

---

## Mapping Rationale

AI Assistance focuses on improving productivity through intelligent interaction and content generation.

Search and summarization enhance user efficiency.

Workflow Automation extends AI capabilities into operational business processes.

---

## Related Capabilities

- AI Chat
- Intelligent Search
- Workflow Automation

---

## Mapping Notes

AI Assistance represents intelligent productivity rather than business process automation alone.

---

# Canonical Mapping Principles

Every Business Requirement may map to multiple Capabilities.

Every Capability may support multiple Business Requirements.

Each relationship represents a semantic association defined by domain experts.

Example:

```text
REQ-002

Identity Management

        │
        │ Primary Association
        ▼
CAP-001
Single Sign-On

        │
        │ Primary Association
        ▼
CAP-002
Multi-Factor Authentication

        │
        │ Secondary Association
        ▼
CAP-003
SCIM Provisioning

        │
        │ Supporting Association
        ▼
CAP-010
Audit Logging
```

Business Requirement Mappings define the available semantic relationships.

The Recommendation Engine determines which Product Capability Profiles best satisfy those Capabilities during runtime.

Business Requirement Mappings remain static reference knowledge.

Recommendation Packages remain Runtime Objects.

---

# Mapping Invariants

The following rules must always hold.

## Invariant 1

Business Requirement Mappings are static reference knowledge.

Business Requirement Mappings evolve only through new Domain Pack versions.

Business Requirement IDs remain stable across versions.

Capability IDs remain stable across versions.

---

## Invariant 2

Business Requirement Mappings are never Runtime Objects.

Business Requirement Mappings define semantic relationships.

They never perform runtime capability matching.

---

## Invariant 3

Business Requirement Mappings never contain user-specific information.

They describe canonical relationships.

They never describe individual users.

---

## Invariant 4

Business Requirement Mappings never contain recommendation scores.

Coverage percentages, ranking scores, and recommendation scores belong exclusively to the Recommendation Engine.

---

## Invariant 5

Business Requirement Mappings never contain recommendation logic.

Recommendation logic belongs exclusively to the Recommendation Engine.

---

## Invariant 6

Business Requirement Mappings never perform deterministic capability matching.

They define semantic relationships.

The Recommendation Engine traverses those relationships during runtime.

---

## Invariant 7

Every Business Requirement must map to at least one Primary Association.

Every Capability may satisfy multiple Business Requirements.

Business Requirements never map directly to Products.

Business Requirements map only to Capabilities.

Product Capability Profiles reference Capabilities.

The Recommendation Engine performs all runtime capability matching.

---

## Invariant 8

Every reusable Business Requirement has one canonical definition.

Business Requirement Mappings reference Business Requirement IDs.

Business Requirement definitions remain centralized within the Business Requirement Catalog.

---

## Invariant 9

Every reusable Capability has one canonical definition.

Business Requirement Mappings reference Capability IDs.

Capability definitions remain centralized within the Capability Catalog.

---

# Relationship to the Recommendation Engine

The Recommendation Engine evaluates Business Requirements against Product Capability Profiles using the semantic relationships defined by this document.

Requirement Profile

↓

Business Requirements (REQ)

↓

Business Requirement Mapping

↓

Capabilities (CAP)

↓

Product Capability Profiles (PROD)

↓

Capability Coverage

↓

Coverage Analysis

↓

Recommendation Engine

↓

Recommendation Package

↓

AI Buying Advisor

The Recommendation Engine owns runtime capability matching.

The Business Requirement Catalog owns Business Requirements.

The Capability Catalog owns Capability definitions.

The Business Requirement Mapping owns the semantic relationships between Business Requirements and Capabilities.

The Recommendation Engine traverses those relationships to produce Recommendation Packages.

---

# Relationship to Other Reference Knowledge

The Software Buying Domain consists of six complementary forms of reference knowledge.

Behavioral Ontology

↓

Defines Behavioral Concepts

↓

Behavioral Concept Mapping

↓

Defines Behavioral Concept → Business Requirement relationships

↓

Business Requirement Catalog

↓

Defines Business Requirements

↓

Business Requirement Mapping

↓

Defines Business Requirement → Capability relationships

↓

Capability Catalog

↓

Defines Capabilities

↓

Product Capability Profiles

↓

Compose Capabilities into complete product representations

Each document owns one unique responsibility.

No document duplicates another.

Every reusable concept has one canonical home.

Together these documents form the Software Buying Domain Knowledge Graph.

---

# Claude Implementation Contract

Claude MUST:

- Treat Business Requirement Mappings as static reference knowledge.
- Treat Business Requirements as canonical objects defined by the Business Requirement Catalog.
- Treat Capabilities as canonical objects defined by the Capability Catalog.
- Reference Business Requirements using Requirement IDs.
- Reference Capabilities using Capability IDs.
- Preserve the distinction between reference knowledge and Runtime Objects.
- Allow Business Requirement Mappings to evolve independently of runtime implementation.
- Preserve deterministic semantic relationships.
- Allow new Business Requirements and Capabilities to be introduced without modifying the Recommendation Engine.

Claude MUST NOT:

- Store Runtime Objects.
- Store user-specific information.
- Store recommendation scores.
- Store recommendation rankings.
- Perform runtime capability matching.
- Perform recommendation logic.
- Modify Recommendation Packages.
- Modify Decision Policies.

---

# Future Evolution

Future Domain Pack versions may introduce:

- New Business Requirements
- New Capabilities
- New Business Requirement Mappings
- Additional semantic relationships

Business Requirement IDs remain stable across versions.

Capability IDs remain stable across versions.

Business Requirement Mappings remain independent of Runtime Objects.

The Business Requirement Catalog continues defining **what business needs exist**.

The Business Requirement Mapping continues defining **how Business Requirements are semantically related to Capabilities**.

The Capability Catalog continues defining **what solution capabilities exist**.

The Recommendation Engine continues determining **which Product Capability Profiles best satisfy those Business Requirements**.

Recommendation Packages continue representing the runtime recommendation results.

---

# Summary

The Business Requirement to Capability Mapping document defines the semantic relationships connecting business needs to solution capabilities.

Business Requirements represent canonical business knowledge.

Capabilities represent canonical solution knowledge.

Business Requirement Mappings define the deterministic relationships between those two knowledge models.

The Recommendation Engine consumes these mappings while producing Recommendation Packages during runtime.

This separation ensures:

- Consistent Business Requirement relationships
- Reusable Capability definitions
- Deterministic capability matching
- Explainable recommendations
- Independent mapping evolution
- Clear separation between reference knowledge and runtime behavior

The Business Requirement to Capability Mapping document completes the bridge between business needs and solution capabilities.

Together with the Behavioral Ontology, Behavioral Concept Mapping, Business Requirement Catalog, Capability Catalog, and Product Capability Profiles, it provides the complete knowledge foundation required for deterministic recommendation generation within the Recommendation Engine.

---