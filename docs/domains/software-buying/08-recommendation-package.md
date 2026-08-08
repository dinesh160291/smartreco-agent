# Recommendation Package

**Version:** 1.0

---

# Purpose

The Recommendation Package defines the canonical Runtime Object produced by the Recommendation Engine within the Software Buying Domain.

Recommendation Packages represent runtime recommendation outcomes.

They are not reference knowledge.

They are generated during runtime.

They are specific to an individual buying journey.

They do not redefine Business Requirements.

They do not redefine Capabilities.

They do not redefine Product Capability Profiles.

Recommendation Packages reference canonical objects defined throughout the Software Buying Domain Pack.

They serve as the authoritative runtime contract between the Recommendation Engine and downstream consumers including the AI Buying Advisor, user interfaces, APIs, reporting, and analytics.

---

# Guiding Principle

Reference Knowledge defines what is known.

Runtime Objects define what was determined for a specific customer during execution.

The Recommendation Package represents the final deterministic recommendation produced after evaluating a customer's Requirement Profile against Product Capability Profiles.

The Recommendation Package defines runtime outcomes.

It does not define recommendation logic.

It does not define recommendation algorithms.

It does not define ranking strategies.

It does not define decision policies.

It does not define AI explanations.

The Recommendation Package contains structured facts only.

It never contains generated prose.

---

# Reference Knowledge vs Runtime Objects

The Software Buying Domain consists of two complementary layers.

Reference Knowledge

↓

Defines canonical domain knowledge

↓

Behavioral Concepts

Business Requirements

Capabilities

Product Capability Profiles

------------------------------------

Runtime Objects

↓

Represent execution results

↓

Behavioral Evidence

Behavioral Hypotheses

Behavioral Memory

Requirement Profile

Recommendation Package

Reference Knowledge remains stable across Domain Pack versions.

Runtime Objects are generated independently for every buying journey.

Reference Knowledge describes the domain.

Runtime Objects describe the outcome of deterministic reasoning within that domain.

---

# Separation of Responsibilities

Business Requirement Catalog

↓

Defines

↓

Business Requirements (REQ)

↓

Business Requirement Mapping

↓

Determines required Capabilities

↓

Capability Catalog

↓

Defines Capabilities (CAP)

↓

Product Capability Profiles

↓

Defines supported Capabilities

↓

Recommendation Engine

↓

Produces

↓

Recommendation Package

↓

Consumed by

↓

AI Buying Advisor

↓

User Interfaces

↓

APIs

↓

Reporting & Analytics

---

Business Requirements are reference knowledge.

Capabilities are reference knowledge.

Product Capability Profiles are reference knowledge.

Recommendation Packages are Runtime Objects.

The Recommendation Engine is responsible for producing Recommendation Packages.

The AI Buying Advisor is responsible for generating natural language explanations using the structured facts contained within Recommendation Packages.

---

# Relationship to Runtime Objects

Recommendation Packages are produced after a Requirement Profile has already been generated.

They do not contain Requirement Profiles.

They reference Requirement Profiles.

Requirement Profile

↓

Requirement Profile ID

↓

Recommendation Engine

↓

Recommendation Package

↓

Recommendation Entries

↓

AI Buying Advisor

This follows the architectural principle:

Reference, don't duplicate.

Every Runtime Object owns its own lifecycle.

Recommendation Packages reference Runtime Objects rather than embedding them.

This separation improves consistency, traceability, maintainability, and auditability.

---

# Scope

This document defines:

- Recommendation Package identifiers
- Recommendation Package structure
- Recommendation Entry structure
- Capability Coverage Analysis
- Runtime relationships
- Runtime invariants
- Recommendation examples

This document does not define:

- Recommendation algorithms
- Recommendation scoring formulas
- Ranking strategies
- Decision Policies
- AI-generated explanations
- Product Capability Profiles
- Business Requirement definitions
- Capability definitions
- Runtime engine implementation

---

# Recommendation Package Definition

Every Recommendation Package represents the deterministic recommendation outcome produced by the Recommendation Engine for a single Requirement Profile.

Recommendation Packages are Runtime Objects.

They are never reference knowledge.

They are deterministic.

They are user-specific.

They are generated independently for every buying journey.

Recommendation Packages reference canonical Business Requirements, Capabilities, and Product Capability Profiles defined within the Software Buying Domain.

Recommendation Packages never redefine reference knowledge.

Every Recommendation Package must contain the following sections.

---

## Recommendation Package ID

A unique identifier for the Recommendation Package.

Recommendation Package IDs are generated during runtime.

Example:

```text
REC-20260807-000123
```

Recommendation Package IDs uniquely identify a runtime recommendation.

They are not stable across executions.

---

## Generated Timestamp

The date and time when the Recommendation Package was produced.

Example:

```text
2026-08-07T14:35:12Z
```

The timestamp records when the Recommendation Engine completed the recommendation process.

---

## Requirement Profile ID

Identifies the Requirement Profile used to generate the Recommendation Package.

Recommendation Packages reference Requirement Profiles.

They never embed Requirement Profiles.

Example:

```text
RP-20260807-000041
```

This follows the architectural principle:

Reference, don't duplicate.

---

## Recommendation Entries

A Recommendation Package contains one or more Recommendation Entries.

Each Recommendation Entry represents a single recommended product.

Recommendation Entries are ordered according to the deterministic ranking produced by the Recommendation Engine.

The Recommendation Package itself does not perform ranking.

It simply records the ranking outcome.

---

# Recommendation Entry

Every Recommendation Entry represents a single recommended Product Capability Profile.

Recommendation Entries are Runtime Objects contained within a Recommendation Package.

Recommendation Entries reference Product Capability Profiles.

They never redefine Products.

Every Recommendation Entry must contain the following sections.

---

## Product ID

Identifies the recommended Product Capability Profile.

Products are referenced using Product IDs.

Example:

```text
PROD-001
```

Product definitions remain centralized within Product Capability Profiles.

---

## Recommendation Rank

Defines the relative ordering of the recommendation within the Recommendation Package.

Example:

```text
1

2

3
```

Recommendation Rank records the outcome produced by the Recommendation Engine.

It does not explain how the ranking was calculated.

---

## Capability Coverage Analysis

Summarizes how well the Product Capability Profile satisfies the required Capabilities contained within the Requirement Profile.

Capability Coverage Analysis is produced by the Recommendation Engine.

It records deterministic results.

It never performs capability matching.

Capability Coverage Analysis is discussed in detail later in this document.

---

## Recommendation Metadata

Provides runtime metadata associated with the Recommendation Entry.

Examples include:

- Recommendation generation timestamp
- Engine version
- Domain Pack version
- Recommendation execution identifier

Recommendation Metadata improves traceability and auditing.

It never contains recommendation logic.

---

# Recommendation Package Hierarchy

A Recommendation Package contains multiple Recommendation Entries.

Example:

```text
Recommendation Package

├── Recommendation Entry
│       ├── Product ID
│       ├── Recommendation Rank
│       ├── Capability Coverage Analysis
│       └── Recommendation Metadata
│
├── Recommendation Entry
│       ├── Product ID
│       ├── Recommendation Rank
│       ├── Capability Coverage Analysis
│       └── Recommendation Metadata
│
└── Recommendation Entry
        ├── Product ID
        ├── Recommendation Rank
        ├── Capability Coverage Analysis
        └── Recommendation Metadata
```

The Recommendation Package owns the overall recommendation.

Each Recommendation Entry owns the evaluation of a single product.

---

# Capability Coverage Analysis

Capability Coverage Analysis records the deterministic evaluation performed by the Recommendation Engine for a single Recommendation Entry.

Capability Coverage Analysis is a Runtime Object.

It is never reference knowledge.

It records evaluation results.

It never performs capability matching.

Capability matching is completed by the Recommendation Engine before the Recommendation Package is created.

Capability Coverage Analysis communicates those results in a structured and deterministic format.

---

## Purpose

Capability Coverage Analysis provides a transparent explanation of how well a recommended Product Capability Profile satisfies the Business Requirements contained within the Requirement Profile.

It enables:

- Explainable recommendations
- Recommendation traceability
- Product comparison
- Runtime auditing
- AI explanation generation

Capability Coverage Analysis communicates recommendation outcomes.

It never determines recommendation outcomes.

---

## Coverage Components

Every Capability Coverage Analysis contains the following sections.

---

### Coverage Percentage

Represents the overall percentage of required Capabilities satisfied by the Product Capability Profile.

Coverage Percentage is produced by the Recommendation Engine.

The Recommendation Package records the result.

It never calculates the value.

Example:

```text
92%
```

---

### Satisfied Business Requirements

Identifies the Business Requirements that are fully satisfied by the recommended product.

Business Requirements are referenced using Requirement IDs.

Example:

```text
REQ-001

REQ-002

REQ-005
```

Recommendation Packages reference Business Requirements.

They never duplicate Business Requirement definitions.

---

### Partially Satisfied Business Requirements

Identifies Business Requirements that are only partially satisfied.

Example:

```text
REQ-004
```

Partially satisfied Business Requirements indicate that some required Capabilities are supported while others are missing.

---

### Unsupported Business Requirements

Identifies Business Requirements that are not satisfied by the recommended product.

Example:

```text
REQ-003
```

Unsupported Business Requirements improve recommendation transparency.

They do not prevent products from being recommended.

---

### Satisfied Capabilities

Identifies the required Capabilities supported by the Product Capability Profile.

Capabilities are referenced using Capability IDs.

Example:

```text
CAP-001

CAP-002

CAP-010
```

Capability definitions remain centralized within the Capability Catalog.

---

### Missing Capabilities

Identifies required Capabilities that are not supported by the Product Capability Profile.

Example:

```text
CAP-015

CAP-017
```

Missing Capabilities improve recommendation explainability.

They provide deterministic evidence supporting the recommendation outcome.

---

# Capability Coverage Hierarchy

Capability Coverage Analysis summarizes the relationship between the customer's Requirement Profile and the evaluated Product Capability Profile.

Example:

```text
Requirement Profile

↓

Business Requirements

↓

Required Capabilities

↓

Product Capability Profile

↓

Supported Capabilities

↓

Capability Coverage Analysis

├── Coverage Percentage
├── Satisfied Business Requirements
├── Partially Satisfied Business Requirements
├── Unsupported Business Requirements
├── Satisfied Capabilities
└── Missing Capabilities
```

Capability Coverage Analysis records evaluation outcomes.

It never performs evaluation.

---

# Why Capability Coverage Exists

Capability Coverage Analysis improves recommendation transparency.

It provides deterministic evidence supporting every recommendation.

Coverage Analysis enables downstream components to understand:

- Why a product was recommended
- Which Business Requirements were satisfied
- Which Capabilities were supported
- Which Capabilities were missing

Coverage Analysis provides structured facts.

It never generates explanations.

The AI Buying Advisor uses these structured facts to produce natural language explanations.

---

# Reference Relationships

Capability Coverage Analysis references canonical objects defined elsewhere within the Software Buying Domain Pack.

Requirement Profile

↓

Business Requirement IDs

↓

Capability IDs

↓

Product Capability Profile IDs

↓

Capability Coverage Analysis

This follows the architectural principle:

Reference, don't duplicate.

Capability Coverage Analysis never redefines Business Requirements.

Capability Coverage Analysis never redefines Capabilities.

Capability Coverage Analysis never redefines Products.

---

# Runtime Invariants

The following rules must always hold.

## Invariant 1

Recommendation Packages are Runtime Objects.

They are generated during runtime.

They are never reference knowledge.

---

## Invariant 2

Recommendation Packages are immutable.

Once generated, Recommendation Packages are never modified.

If recommendation results change, the Recommendation Engine produces a new Recommendation Package.

---

## Invariant 3

Recommendation Packages reference existing Runtime Objects.

They reference Requirement Profiles.

They never embed Requirement Profiles.

This follows the architectural principle:

Reference, don't duplicate.

---

## Invariant 4

Recommendation Packages reference canonical reference knowledge.

They reference:

- Business Requirements
- Capabilities
- Product Capability Profiles

They never redefine reference knowledge.

---

## Invariant 5

Recommendation Packages never contain recommendation logic.

Recommendation logic belongs exclusively to the Recommendation Engine.

Recommendation Packages communicate recommendation outcomes.

They never determine recommendation outcomes.

---

## Invariant 6

Recommendation Packages never perform capability matching.

Capability matching belongs exclusively to the Recommendation Engine.

Capability Coverage Analysis records the results of capability matching.

It never performs capability matching.

---

## Invariant 7

Recommendation Packages never contain generated prose.

Recommendation Packages contain structured facts only.

Natural language explanations belong exclusively to the AI Buying Advisor.

---

## Invariant 8

Recommendation Packages remain deterministic.

Given the same Requirement Profile, Product Capability Profiles, Recommendation Engine version, Decision Policies, and Domain Pack version, the Recommendation Package must be reproducible.

---

## Invariant 9

Recommendation Packages are traceable.

Every recommendation must be traceable back to:

- Requirement Profile
- Business Requirements
- Required Capabilities
- Product Capability Profiles
- Capability Coverage Analysis

Recommendation Packages must never contain unsupported conclusions.

---

# Relationship to Other Components

Recommendation Packages represent the final Runtime Object produced by the Recommendation Engine.

Behavioral Intelligence Platform

↓

Requirement Profile

↓

Business Requirement → Capability Mapping

↓

Required Capabilities

↓

Product Capability Profiles

↓

Recommendation Engine

↓

Recommendation Package

↓

AI Buying Advisor

↓

User Interfaces

↓

APIs

↓

Reporting & Analytics

The Recommendation Engine owns recommendation generation.

The Recommendation Package owns recommendation outcomes.

The AI Buying Advisor owns recommendation explanations.

Each component owns one unique responsibility.

---

# Claude Implementation Contract

Claude MUST:

- Treat Recommendation Packages as Runtime Objects.
- Treat Recommendation Packages as immutable.
- Reference Requirement Profiles using Requirement Profile IDs.
- Reference Products using Product IDs.
- Reference Business Requirements using Requirement IDs.
- Reference Capabilities using Capability IDs.
- Preserve deterministic recommendation outcomes.
- Preserve the distinction between Runtime Objects and reference knowledge.
- Generate explanations using the structured facts contained within Recommendation Packages.

Claude MUST NOT:

- Modify Recommendation Packages.
- Modify Requirement Profiles.
- Modify Product Capability Profiles.
- Modify Business Requirements.
- Modify Capabilities.
- Perform recommendation logic while interpreting Recommendation Packages.
- Generate deterministic recommendation outcomes.
- Replace structured facts with assumptions.

---

# Future Evolution

Future versions of the Software Buying Domain may introduce:

- Additional Recommendation Entry attributes
- Enhanced Capability Coverage Analysis
- Additional recommendation metadata
- New explainability references

Future versions of the Recommendation Engine may introduce:

- Improved recommendation algorithms
- Enhanced ranking strategies
- New decision policies
- Improved capability matching

These implementation improvements must never require changes to the canonical Recommendation Package structure.

The Recommendation Package remains the stable runtime contract between the Recommendation Engine and downstream consumers.

---

# Summary

The Recommendation Package defines the canonical Runtime Object produced by the Recommendation Engine within the Software Buying Domain.

Recommendation Packages communicate deterministic recommendation outcomes.

They never perform recommendation logic.

They never redefine reference knowledge.

They contain structured facts only.

Each Recommendation Package references a Requirement Profile and contains one or more Recommendation Entries.

Each Recommendation Entry records the deterministic evaluation of a single Product Capability Profile, including Capability Coverage Analysis and recommendation metadata.

The Recommendation Package serves as the authoritative runtime contract consumed by the AI Buying Advisor, user interfaces, APIs, reporting, and analytics.

This separation ensures:

- Deterministic recommendation outcomes
- Complete runtime traceability
- Clear separation of responsibilities
- Explainable recommendations
- Stable runtime contracts
- Consistent reference reuse
- Independent evolution of the Recommendation Engine and the Software Buying Domain Pack

Together with the Behavioral Ontology, Business Requirement Catalog, Capability Catalog, Product Capability Profiles, Behavioral Concept Mapping, and Business Requirement to Capability Mapping, the Recommendation Package completes the Software Buying Domain by defining the canonical runtime representation of recommendation outcomes.

---
