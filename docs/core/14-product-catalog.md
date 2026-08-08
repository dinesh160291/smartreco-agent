# Product Catalog

**Version:** 1.0

---

# Purpose

The Product Catalog defines the canonical structure for products consumed by the Behavioral Intelligence Platform.

The Product Catalog represents structured product knowledge.

It never contains:

- Behavioral information
- User-specific information
- Recommendation logic
- AI-generated content

Its sole responsibility is providing deterministic product knowledge for capability matching.

---

# Contract vs. Data

Product knowledge is split into two parts with different owners and different change velocities:

## 1. The Contract and Taxonomy (knowledge — static)

- The Product Capability Profile **structure** (which fields a product must have) — owned by the Core Platform (this chapter).
- The **Capability taxonomy**, Business Requirements, and mappings — owned by the active Domain Pack.

These change only through governance review and Domain Pack versioning.

## 2. Product Records (data — runtime-managed)

The actual product entries conforming to that contract are **runtime data**, managed by administrators through the Admin Product APIs (Chapter 16):

- Admins create, update, and delete product records at any time.
- Every mutation is dual-written to the relational store and the vector store under the dual-write contract owned by the Semantic Retrieval Engine (Chapter 20).
- Product records are versioned; historical versions remain immutable for replay.
- Admins select Capability IDs from the Domain Pack taxonomy. They never invent capabilities — extending the taxonomy remains a Domain Pack governance change.

Adding a product is data entry. Adding a *capability* is knowledge evolution. This distinction keeps the catalog live for the business while the knowledge graph stays canonical.

---

# Guiding Principle

Products advertise capabilities.

Requirements consume capabilities.

The Recommendation Engine matches Requirement Profiles against Product Capability Profiles.

Products never advertise recommendations.

Recommendations are produced exclusively by the Recommendation Engine.

---

# Core Principle

Requirement Profile

↓

Recommendation Engine

↓

Product Capability Profile (PCP)

↓

Recommendation Package

The Product Catalog supplies deterministic product knowledge.

The Recommendation Engine performs deterministic capability matching.

---

# Responsibilities

The Product Catalog is responsible for:

- Defining products.
- Defining Product Capability Profiles (PCP).
- Defining product metadata.
- Defining supported capabilities.
- Supporting deterministic capability matching.
- Supporting Product Catalog versioning.

The Product Catalog never:

- Performs recommendation logic.
- Performs behavioral reasoning.
- Determines product rankings.
- Invokes AI.

---

# Product Philosophy

The Product Catalog contains objective product knowledge.

It never contains:

- User behavior
- User preferences
- Recommendation Scores
- Recommendation Readiness
- AI-generated content

The Product Catalog is deterministic.

It is versioned.

It is replayable.

---

# Product Capability Profile (PCP)

Every product exposes a Product Capability Profile (PCP).

The Product Capability Profile defines the business capabilities supported by a product.

The Recommendation Engine consumes Product Capability Profiles.

Behavioral engines never consume Product Capability Profiles.

---

# Product Capability Profile Structure

Every Product Capability Profile contains:

- Product ID
- Product Name
- Vendor
- Product Category
- Business Capabilities
- Supported Integrations
- Deployment Options
- Compliance Certifications
- Pricing Model
- Supported Platforms
- Metadata

Capability values are defined by Platform Enumerations together with the active Domain Pack.

---

# Business Capabilities

Capabilities represent vendor-neutral business concepts.

Examples include:

- Workflow Automation
- Project Planning
- Reporting
- Source Control Integration
- API Integration
- Security
- AI Assistance

Capabilities are defined by the active Domain Pack.

The Recommendation Engine matches Requirements against these capabilities.

---

# Static Product Information

Static Product Information includes:

- Product Name
- Vendor
- Logo
- Description
- Product URL

Static Product Information supports presentation.

It never participates in deterministic recommendation logic.

---

# Capability Matching

Requirement Profile

↓

Recommendation Engine

↓

Capability Matching

↓

Product Capability Profile

↓

Recommendation Package

Capability matching is deterministic.

Capability matching never invokes AI.

Business weighting is governed by Decision Policies.

---

# Product Catalog Versioning

Product Capability Profiles are versioned.

Product Catalog versions support:

- Capability evolution
- Product evolution
- Backward compatibility
- Deterministic replay

Historical Product Capability Profiles remain immutable.

Replay always uses the historical Product Capability Profile version that existed when recommendations were generated.

---

# Domain Ownership

The Product Catalog contract is owned by the Behavioral Intelligence Platform.

The active Domain Pack owns:

- Capability Taxonomies
- Product Categories
- Domain-specific Product Metadata contracts
- Reference Product Capability Profiles (seed/reference knowledge, e.g. the Product Roster)

Runtime product records are owned by the **Product Knowledge Store** (Chapter 20) and managed by administrators through the Admin Product APIs.

The core platform remains completely domain-agnostic.

The Product Catalog defines **how** products are represented.

Domain Packs define **which capabilities can exist**.

Administrators define **which products currently exist**.

---

# Relationship to Decision Policies

The Product Catalog never contains business policy.

Business rules governing recommendation behavior are defined exclusively by the Decision Policy Framework.

Examples include:

- Capability weighting
- Recommendation publication thresholds
- Tie-breaking rules
- Recommendation Readiness thresholds

The Product Catalog supplies deterministic product knowledge.

Decision Policies govern how that knowledge is evaluated.

---

# Relationship to the Platform

The Product Catalog is the authoritative source of product knowledge for the Behavioral Intelligence Platform.

Platform components consume the Product Catalog as follows:

- Recommendation Engine consumes Product Capability Profiles.
- AI Buying Advisor consumes Product information through the Recommendation Package.
- Behavioral engines never consume Product Capability Profiles.
- Journey Resolution never consumes Product Catalog information.

The Product Catalog never consumes Behavioral Runtime Objects.

Product knowledge and behavioral knowledge remain completely independent.

---

# Interaction with Platform Components

Requirement Profile

↓

Recommendation Engine

↓

Product Capability Profile

↓

Capability Matching

↓

Recommendation Package

↓

AI Buying Advisor

↓

AI Advisory Response

The Product Catalog provides deterministic product knowledge.

It never performs deterministic reasoning.

---

# Product Catalog Invariants

## Invariant 1

Products advertise capabilities.

They never advertise recommendations.

---

## Invariant 2

Capabilities are vendor-neutral.

---

## Invariant 3

The Product Catalog contains no user-specific information.

---

## Invariant 4

The Product Catalog is deterministic.

---

## Invariant 5

Product Capability Profiles are versioned.

Historical versions remain immutable.

---

## Invariant 6

Domain Packs own the capability taxonomy and the Product Capability Profile contract.

Administrators own runtime product records, mutated only through the Admin Product APIs and the dual-write contract (Chapter 20).

Product records never introduce capability values outside the Domain Pack taxonomy.

---

## Invariant 7

Behavioral engines never consume Product Capability Profiles.

---

## Invariant 8

The Product Catalog never performs recommendation logic.

---

## Invariant 9

The Product Catalog never invokes AI.

---

# Design Principles

The Product Catalog follows these architectural principles.

## Principle 1

Products advertise capabilities.

---

## Principle 2

Capabilities are vendor-neutral.

---

## Principle 3

Behavioral knowledge and product knowledge remain independent.

---

## Principle 4

The Product Catalog is deterministic.

---

## Principle 5

Product knowledge is versioned and replayable.

---

## Principle 6

Business policy remains external through the Decision Policy Framework.

---

# Claude Implementation Contract

Claude MUST:

- Consume Product Capability Profiles.
- Respect Product Capability Profile versions.
- Respect Product Catalog versions.
- Support deterministic capability matching.
- Preserve replayability.
- Respect Decision Policies.

Claude MUST NOT:

- Mutate product records outside the Admin Product APIs and dual-write contract.
- Generate Product Capability Profiles with AI.
- Infer missing capabilities.
- Accept capability values outside the Domain Pack taxonomy.
- Invoke AI for capability matching.
- Override Decision Policies.

---

# Relationship to Core Documentation

This chapter defines the canonical product knowledge contract consumed by the Behavioral Intelligence Platform.

Related chapters include:

| Chapter | Responsibility |
|---------|----------------|
| 06 | Requirement Engine |
| 08 | Recommendation Engine |
| 10 | Decision Policies |
| 11 | Observability and Evaluation |
| 13 | Event Schema |
| 15 | LLM Contract |
| 16 | API Contracts |
| 17 | Platform Enumerations |
| 20 | Semantic Retrieval Engine |
| 99 | Architecture Principles |

---

# Summary

The Product Catalog defines the canonical structure for deterministic product knowledge within the Behavioral Intelligence Platform.

It provides Product Capability Profiles that enable deterministic capability matching.

It contains objective, versioned, vendor-neutral product information.

It never performs behavioral reasoning.

It never performs recommendation logic.

It never invokes AI.

Its sole responsibility is supplying trusted product knowledge to the Recommendation Engine.

---