# SmartReco Core Platform

> **Status:** ✅ Implementation Ready

---

# Overview

The **Core Platform** defines the domain-agnostic runtime architecture of the SmartReco platform.

Unlike Domain Packs, which define business knowledge for a specific industry or use case, the Core Platform defines the reusable execution framework responsible for transforming customer behavior into deterministic, explainable recommendations.

The Core Platform is independent of any business domain.

It can execute against any Domain Pack that conforms to the SmartReco Architectural Principles.

Examples include:

- Software Buying
- Healthcare
- Human Resources
- Procurement
- Finance

---

# Purpose

The purpose of the Core Platform is to define how the SmartReco platform executes.

It provides the runtime architecture for:

- Behavioral Intelligence
- Customer Memory
- Requirement Inference
- Journey Intelligence
- Recommendation Generation
- AI Explanation
- Runtime Object Management
- Platform APIs
- Decision Policies
- Observability

The Core Platform defines **how the platform executes**.

It does **not** define **what the platform knows**.

---

# Relationship to Platform Architecture

The Core Platform is governed by the platform-wide architectural standards located under:

```text
knowledge/
└── architecture/
    ├── architectural-principles.md
    └── domain-governance.md
```

These documents define:

- Platform architectural laws
- Domain governance
- Design philosophy
- Evolution guidelines

Every document within this folder should conform to those standards.

---

# High-Level Architecture

The SmartReco platform follows a layered architecture.

```text
                    Domain Packs
          (Software Buying, Healthcare, HR...)

                          │
                          ▼

         Behavioral Intelligence Platform

                          │
                          ▼

              Runtime Object Generation

                          │
                          ▼

            Recommendation Engine

                          │
                          ▼

            Recommendation Package

                          │
                          ▼

              AI Buying Advisor

                          │
                          ▼

          Applications / APIs / UI
```

The Core Platform executes domain knowledge.

Domain Packs provide domain knowledge.

---

# Repository Organization

The Core Platform is organized into modular architectural components.

| Module | Purpose |
|---------|---------|
| 00 Platform Architecture | Overall platform architecture and execution model |
| 01 Behavioral Hypotheses | Deterministic behavioral inference |
| 02 Behavioral Memory | Persistent behavioral context |
| 03 Behavioral Learning Engine | Learns customer behavior over time |
| 04 Behavioral Decay Engine | Manages behavioral aging and signal decay |
| 05 Confidence Engine | Calculates confidence for behavioral conclusions |
| 06 Requirement Engine | Produces Requirement Profiles |
| 07 Journey Stage Engine | Determines customer buying stage |
| 08 Recommendation Engine | Produces Recommendation Packages |
| 09 AI Buying Advisor | Generates explainable recommendations |
| 10 Decision Policies | Runtime decision rules |
| 11 Observability & Evaluation | Monitoring, evaluation and diagnostics |
| 12 Journey Resolution Engine | Determines journey completion |
| 13 Event Schema | Canonical runtime events |
| 14 Product Catalog | Runtime product loading and management |
| 15 LLM Contract | Contract between runtime platform and LLM |
| 16 API Contracts | External platform interfaces |
| 17 Platform Enumerations | Shared runtime enumerations |
| 18 Runtime Object Model | Canonical runtime object definitions |
| 19 Behavioral Reasoning Engine | Transforms Events into Evidence and Hypotheses |
| 20 Semantic Retrieval Engine | Product Knowledge Store, dual-write, semantic candidate generation (Tier 2 AI) |
| 21 Agent Orchestration | The agentic workflow graph composing all engines |
| 22 Event Ingestion & Tracking | Client tracking contract and batch ingestion |
| 23 Execution Triggers & Caching | When the pipeline and AI run; caching model |
| 24 Proactive Delivery | Scheduled digest generation and outbound channels |
| 99 Architectural Principles | References the platform-wide Architectural Principles |

---

# Platform Responsibilities

The Core Platform is responsible for:

- Runtime execution
- Behavioral inference
- Behavioral memory
- Requirement inference
- Journey intelligence
- Recommendation generation
- Runtime object creation
- AI orchestration
- Decision policies
- Runtime observability
- Platform APIs

The Core Platform is **not** responsible for defining business knowledge.

---

# Relationship to Domain Packs

The SmartReco platform separates **knowledge** from **execution**.

```text
                   Domain Packs

Defines

Behavioral Concepts

Business Requirements

Capabilities

Products

Mappings

────────────────────────────────

Core Platform

Executes

Behavioral Intelligence

Requirement Engine

Recommendation Engine

AI Buying Advisor
```

The Core Platform consumes Domain Packs without modifying them.

This separation allows the same platform to support multiple business domains.

---

# Design Philosophy

Every component within the Core Platform follows the SmartReco Architectural Principles.

The most important principles include:

- One Canonical Home
- Reference, Don't Duplicate
- Separation of Responsibilities
- Runtime Objects Record Outcomes
- Engines Perform Deterministic Reasoning
- AI Explains, Never Decides
- Complete Traceability
- Deterministic Before Generative

These principles ensure the platform remains deterministic, explainable, scalable, and maintainable.

---

# Runtime Execution Flow

Every customer journey follows the same deterministic execution pipeline.

```text
Customer Events

↓

Behavioral Evidence

↓

Behavioral Hypotheses

↓

Behavioral Memory

↓

Requirement Profile

↓

Recommendation Engine

↓

Recommendation Package

↓

AI Buying Advisor

↓

Applications / APIs
```

Each engine owns one responsibility.

Each Runtime Object records one deterministic outcome.

---

# Scope

The Core Platform defines:

- Runtime engines
- Runtime object models
- Platform APIs
- Runtime events
- Decision policies
- AI contracts
- Runtime execution
- Observability

The Core Platform does **not** define:

- Business Requirements
- Capabilities
- Products
- Domain mappings
- Industry-specific knowledge

Those responsibilities belong exclusively to Domain Packs.

---

# Repository Structure

The SmartReco repository is organized into four architectural layers.

```text
smartreco-agent/

knowledge/
│
└── architecture/
    │
    ├── architectural-principles.md
    └── domain-governance.md

────────────────────────────────

docs/
│
├── core/
│
└── domains/

────────────────────────────────

src/

────────────────────────────────

apps/
```

Each layer has a distinct responsibility.

| Layer | Responsibility |
|--------|----------------|
| knowledge | Platform laws, governance and architectural standards |
| docs | Platform and domain specifications |
| src | Runtime implementation |
| apps | User-facing applications |

---

# Version

Current Version: **1.0**

Status: **Implementation Ready**

The Core Platform defines the canonical runtime architecture for SmartReco. Together with the Domain Packs and the platform Architectural Principles, it provides the foundation for building deterministic, explainable, and reusable AI recommendation systems across multiple business domains.