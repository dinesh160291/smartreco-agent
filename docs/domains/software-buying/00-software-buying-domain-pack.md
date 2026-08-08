# Software Buying Domain Pack

**Version:** 1.0

---

# Purpose

The Software Buying Domain Pack defines all knowledge that is specific to software evaluation and purchasing.

The Behavioral Intelligence Platform is intentionally domain-independent.

This document teaches the platform how to reason about software buying without changing the core Behavioral Reasoning Engine (BRE).

The Domain Pack contains domain knowledge only.

It does not contain AI logic, database design, implementation details, or deterministic reasoning algorithms.

---

# Guiding Principle

The core platform knows **HOW to reason**.

The Domain Pack teaches the platform **WHAT to reason about**.

Changing the domain must never require changes to the Behavioral Reasoning Engine.

Only the Domain Pack changes.

---

# Responsibilities

The Software Buying Domain Pack is responsible for defining:

- Domain vocabulary
- User personas
- Software buying journey
- Domain-specific behaviors
- User requirements
- Behavioral signals
- Product knowledge model
- Recommendation objectives
- Domain rules
- Domain assumptions
- Domain examples

---

# 1. Domain Overview

The Software Buying domain models how individuals and organizations discover, evaluate, compare and adopt software products.

The objective of the platform is to reconstruct the user's software buying journey and infer evolving requirements from observable behavior.

---

# 2. Domain Vocabulary

Examples include:

- Product
- Category
- Integration
- API
- SDK
- Documentation
- Security
- Compliance
- SOC2
- SSO
- Pricing
- Free Trial
- Demo
- Workflow
- Automation
- Reporting
- Workspace
- Seat
- Enterprise
- Team
- Migration

This vocabulary is domain-specific and should not exist inside the core Behavioral Reasoning Engine.

---

# 3. Behavioral Personas

Behavioral Personas represent reusable behavioral patterns inferred from observed behavior.

Examples include:

- Startup Founder
- Engineering Manager
- Product Manager
- CTO
- Developer
- IT Administrator
- Procurement
- Operations Manager

The platform never asks users for these personas.

They are inferred through behavioral evidence.

---

# 4. Software Buying Journey

The canonical buying journey for this domain is:

Awareness

↓

Discovery

↓

Research

↓

Comparison

↓

Technical Validation

↓

Commercial Evaluation

↓

Decision

↓

Adoption

Future versions may extend or specialize this journey.

---

## 4.1 Stage Qualification Milestones

The Journey Stage Engine (core 07) determines the current stage as the **highest stage whose milestone is satisfied** by the journey's Behavioral Evidence, subject to the confidence threshold in POL-STAGE-001. Milestones are deterministic conditions over Evidence produced by the canonical patterns (02 — Behavioral Patterns):

| Stage | Milestone |
|---|---|
| Awareness | Journey has events but no evaluation Evidence yet |
| Discovery | BP-012 Product Discovery Evidence exists |
| Research | Any evaluation-pattern Evidence (BP-001…BP-008) exists, at any strength |
| Comparison | BP-009 Commercial Evidence exists, or Evidence supported by COMPARISON_STARTED events |
| Technical Validation | Any evaluation-pattern Evidence (BP-001…BP-008) at **Medium strength or stronger** |
| Commercial Evaluation | BP-009 Commercial Evidence at Medium or stronger |
| Decision | BP-010 Product Affinity Evidence at Strong, or BP-011 Adoption Readiness Evidence exists |
| Adoption | BP-011 Evidence exists **and** the journey's affinity product has onboarding/migration activity |

**Stage Confidence** = the maximum confidence among active Behavioral Hypotheses supported by the milestone-satisfying Evidence. Advancement requires the POL-STAGE-001 threshold (v1: ≥ 0.6); regression follows POL-STAGE-002.

These milestones are domain knowledge: the engine evaluates them; it never defines them.

---

# 5. Domain Behaviors

Examples include:

- Viewed API Documentation
- Viewed SDK
- Viewed GitHub Integration
- Viewed Security
- Viewed SOC2
- Viewed SSO
- Viewed Pricing
- Compared Products
- Compared Pricing
- Started Free Trial
- Requested Demo
- Contacted Sales
- Viewed Documentation
- Viewed Integrations
- Added Product Comparison
- Viewed Customer Stories
- Viewed Migration Guide
- Viewed Admin Controls
- Added Product to Cart
- Started Checkout
- Completed Purchase

These behaviors are specific to software buying and are interpreted by the core Behavioral Reasoning Engine.

---

# 6. Domain Requirements

Examples include:

- Security
- Compliance
- System Integration
- API Support
- Documentation
- Workflow Automation
- Reporting
- Analytics
- Ease of Adoption
- Pricing
- Scalability
- Migration
- Customer Support
- Enterprise Readiness

Requirements are inferred from behavioral hypotheses and are later matched against product capabilities.

---

# 7. Domain Signals

Domain signals define what behavioral observations suggest within this domain.

Examples:

Viewed GitHub Integration

→ Supports Technical Integration Requirement

Viewed Security

→ Supports Enterprise Security Requirement

Viewed Pricing

→ Supports Commercial Evaluation

Viewed Free Trial

→ Supports Adoption Readiness

These mappings are domain knowledge, not deterministic reasoning logic.

---

# 8. Product Knowledge Model

Every software product should expose a standardized capability model.

Examples:

- Features
- Integrations
- APIs
- Security
- Compliance
- Pricing
- Deployment
- Automation
- Reporting
- Customer Support
- Documentation
- Collaboration
- AI Capabilities

This enables domain-independent recommendation logic.

---

# 9. Recommendation Objectives

Recommendations should optimize for:

- Requirement Fit
- Behavioral Fit
- Buying Stage Fit
- Adoption Probability
- Confidence

Recommendations should never optimize solely for popularity.

---

# 10. Behavioral Heuristics

Examples include:

Enterprise buyers often prioritize:

- Security
- Compliance
- Integrations
- Administration
- Scalability

Individual users often prioritize:

- Ease of Use
- Pricing
- Free Trial
- Simplicity

These rules are behavioral heuristics rather than deterministic truths.

---

# 11. Domain Assumptions

Examples:

Viewing API documentation often suggests technical evaluation.

Viewing pricing multiple times often suggests commercial evaluation.

Repeated visits to the same product often indicate increasing product affinity.

Every assumption should eventually be validated using replay sessions or production data.

---

# 12. Domain Examples

Example Journey

Search

↓

Linear

↓

GitHub Integration

↓

API

↓

Security

↓

Pricing

↓

Free Trial

Possible Interpretation

- Enterprise technical evaluation
- Integration-focused buyer
- Commercial validation
- High adoption intent

Examples exist to validate and test the Behavioral Reasoning Engine.

---

# Separation of Concerns

Behavioral Intelligence Platform

↓

Determines HOW to reason

- Evidence
- Hypotheses
- Confidence
- Memory
- Narratives

Software Buying Domain Pack

↓

Defines WHAT to reason about

- Security
- Pricing
- Integrations
- Documentation
- Reporting
- Automation
- Compliance

Replacing the Domain Pack must not require modifications to the core Behavioral Reasoning Engine.

---

# Future Vision

The Software Buying Domain Pack is one implementation of the platform.

Future Domain Packs may include:

- Travel Planning
- Healthcare
- Financial Planning
- Learning
- E-commerce

Each Domain Pack supplies domain knowledge while reusing the same Behavioral Intelligence Platform.

---
