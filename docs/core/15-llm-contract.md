# LLM Contract

**Version:** 1.0

**Status:** 🟢 Normalized

---

# Purpose

The LLM Contract defines how Large Language Models interact with the Behavioral Intelligence Platform.

The LLM Contract establishes immutable architectural boundaries between deterministic platform reasoning and AI communication.

The LLM never establishes truth.

The Behavioral Intelligence Platform establishes truth.

The LLM communicates verified deterministic platform outputs.

Its sole responsibility is producing AI Advisory Responses (AAR).

---

# Guiding Principle

The LLM answers one question:

> "Given verified deterministic Runtime Objects, how should I communicate them to the user?"

The Behavioral Intelligence Platform determines truth.

The LLM explains truth.

The LLM never performs deterministic reasoning.

---

# Core Principle

Behavior

↓

Behavioral Intelligence Platform

↓

Approved Runtime Objects

↓

LLM Contract

↓

AI Buying Advisor

↓

AI Advisory Response (AAR)

The deterministic platform owns reasoning.

The LLM owns communication.

---

# Scope: The Two AI Tiers

This contract governs every AI call the platform makes, across both tiers of the AI boundary:

- **Tier 1 — Generative Communication**: the AI Buying Advisor producing AI Advisory Responses. The primary subject of this chapter.
- **Tier 2 — Semantic Services**: embeddings, retrieval-quality evaluation, and query refinement inside the Semantic Retrieval Engine (Chapter 20). Tier 2 calls use the same gateway, versioned prompts, and safety rules, with the additional constraint that their outputs influence candidate generation only.

No AI call exists outside these two tiers.

---

# AI Provider Gateway

Every Tier 1 and Tier 2 call passes through the platform's single **AI Provider Gateway** — an OpenAI-compatible client boundary.

- Configuration: base URL, API key, and model identifiers only — supplied entirely by deployment configuration (environment variables such as `AI_GATEWAY_BASE_URL`, `AI_GATEWAY_API_KEY`, `AI_GATEWAY_MODEL`). Keys are never committed.
- Swapping providers is a configuration change, never a code change. The provider is a deployment decision, not an architectural one — this specification names no provider.
- Any OpenAI-compatible provider (or a future adapter) can back the gateway without touching platform code.
- The gateway records provider, model ID, prompt version, token usage, and latency for every call (Chapter 11).

**Per-call bounds (POL-GATE-001):** every gateway call has a hard timeout (v1: 30s) and at most 2 automatic retries with exponential backoff for transient failures. After that, the call is a **node failure** and the orchestration fallbacks apply (Chapter 21): Tier 2 → best available Candidate Set or full-catalog matching; Tier 1 → serve the deterministic Recommendation Package without a fresh AAR. No call path retries indefinitely.

**Malformed output:** an LLM response that violates its output contract is treated as follows — Tier 2: counts as evaluation-unavailable (no parse-retry loop; the pre-evaluation Candidate Set stands). Tier 1: exactly one regeneration attempt; a second violation is a node failure (package served without AAR, failure recorded).

**No tools — structural invariant:** every LLM call in this platform is pure text completion. The model is never given tool-calling, function-calling, code execution, retrieval hooks, or any actuator. The LLM cannot take actions; it can only produce text that deterministic code validates and stores.

**Prompt-data hygiene:** user-authored text (search terms) and admin-authored text (product descriptions, narratives) are always interpolated into prompts as clearly delimited quoted **data**, never as instructions. Prompt templates instruct the model to treat such content as material to describe, not directives to follow.

---

# Responsibilities

The LLM is responsible for:

- Explaining recommendations.
- Summarizing buying journeys.
- Generating executive summaries.
- Comparing alternatives.
- Explaining recommendation trade-offs.
- Asking clarifying questions.
- Producing AI Advisory Responses (AAR).

The LLM never:

- Modifies deterministic Runtime Objects.
- Determines business truth.
- Performs deterministic reasoning.
- Invokes platform engines.

---

# Approved Runtime Objects

The LLM consumes immutable Runtime Objects only.

Approved Runtime Objects include:

- Behavioral Memory
- Requirement Profile
- Journey Stage
- Recommendation Package

The LLM never consumes:

- Raw Behavioral Events
- Internal databases
- Intermediate engine state
- Decision Policy definitions

The LLM communicates exclusively from approved Runtime Objects.

---

# Prompt Composition

Every prompt follows a deterministic composition.

1. System Instructions
2. Runtime Context
3. User Request
4. Output Contract
5. Safety Rules

Prompt construction is deterministic.

Prompt execution is non-deterministic.

Deterministic platform outputs ensure grounded AI communication.

---

# Grounding Rules

Every AI response must be grounded in approved Runtime Objects.

The LLM may reference:

- Behavioral Memory
- Requirement Profile
- Journey Stage
- Recommendation Package

The LLM must never:

- Invent supporting facts.
- Infer new Requirements.
- Infer new Journey Stages.
- Modify Recommendation Rankings.

Grounding guarantees explainability.

---

# Output Contract

Every LLM response produces an AI Advisory Response (AAR).

The AI Advisory Response follows a strongly typed contract.

Every AI Advisory Response contains:

- Executive Summary
- Recommendation Communication
- Trade-off Communication
- Clarifying Questions (when applicable)
- Next Best Actions
- Required Disclaimer

The LLM never produces unsupported output structures.

---

# Recommendation Readiness

Recommendation Readiness governs AI behavior.

READY

↓

- Explain recommendations.
- Compare products.
- Generate buying guidance.
- Produce AI Advisory Response.

NOT_READY

↓

- Do not recommend products.
- Explain missing information.
- Present Recommendation Constraints.
- Ask targeted clarifying questions.
- Suggest next best actions.

Recommendation Readiness is determined exclusively by the Behavioral Intelligence Platform.

The LLM never overrides Recommendation Readiness.

---

# Safety Rules

The LLM MUST NOT:

- Modify Requirements.
- Modify Recommendations.
- Modify Confidence.
- Modify Recommendation Readiness.
- Modify Journey Stage.
- Invent Behavioral Evidence.
- Invent Product Capabilities.
- Invent Recommendation Rankings.
- Override deterministic platform outputs.

All AI communication remains grounded in deterministic Runtime Objects.

---

# Prompt Versioning

Every prompt template is versioned.

Every prompt definition contains:

- Prompt ID
- Prompt Version
- Purpose
- Supported Runtime Objects
- Supported Output Schema
- Supported AI Capabilities

Prompt evolution never changes deterministic platform behavior.

Prompt evolution affects communication only.

Historical prompt versions remain available for replay and auditing.

---

# Prompt Library

The platform maintains a reusable Prompt Library.

Tier 1 templates include:

- Executive Summary
- Recommendation Explanation
- **Persuasive Narrative** (grounded persuasion — Chapter 09)
- Trade-off Communication
- Buying Narrative
- Clarifying Questions
- Alternative Comparison
- Next Best Actions
- **Digest Recap** (proactive delivery variant — Chapter 24)

Tier 2 templates include:

- Retrieval Quality Evaluation
- Query Refinement

Every prompt template has:

- A defined purpose.
- A supported runtime contract.
- A supported output schema.
- A version history.

Prompt templates remain independent of platform engines.

---

# Relationship to Decision Policies

The LLM never evaluates Decision Policies.

Decision Policies determine:

- Recommendation Readiness
- Recommendation Permissions
- AI Communication Constraints
- Required Disclaimers

The LLM consumes the outcomes of Decision Policies through approved Runtime Objects.

Business policy remains external to the AI layer.

---

# Relationship to the Platform

The Behavioral Intelligence Platform terminates with immutable Runtime Objects.

The LLM Contract defines how those Runtime Objects may be consumed.

The LLM:

- Consumes approved Runtime Objects.
- Produces AI Advisory Responses.
- Never modifies deterministic platform outputs.

The Behavioral Intelligence Platform and the AI layer remain independently evolvable.

---

# Interaction with Platform Components

Behavioral Intelligence Platform

↓

Approved Runtime Objects

↓

LLM Contract

↓

AI Buying Advisor

↓

AI Advisory Response (AAR)

↓

End User

The LLM Contract guarantees that communication remains grounded in deterministic platform outputs.

---

# LLM Contract Invariants

## Invariant 1

The LLM never owns platform state.

---

## Invariant 2

The LLM never performs deterministic reasoning.

---

## Invariant 3

The LLM communicates only approved deterministic Runtime Objects.

---

## Invariant 4

Every AI response conforms to the AI Advisory Response (AAR) schema.

---

## Invariant 5

The LLM always respects Recommendation Readiness.

---

## Invariant 6

Prompt templates are versioned.

---

## Invariant 7

The LLM never modifies deterministic Runtime Objects.

---

## Invariant 8

Prompt evolution never changes deterministic platform behavior.

---

## Invariant 9

The LLM never consumes raw Behavioral Events or internal platform state.

---

# Design Principles

The LLM Contract follows these architectural principles.

## Principle 1

The platform determines truth.

---

## Principle 2

The LLM communicates truth.

---

## Principle 3

Every AI response is grounded.

---

## Principle 4

AI communication is contract-driven.

---

## Principle 5

Prompt evolution never changes deterministic reasoning.

---

## Principle 6

The AI layer remains independent of deterministic platform implementation.

---

# Claude Implementation Contract

Claude MUST:

- Consume approved Runtime Objects.
- Respect grounding rules.
- Respect Recommendation Readiness.
- Produce valid AI Advisory Responses.
- Respect Prompt Contracts.
- Respect Output Schemas.
- Preserve communication boundaries.

Claude MUST NOT:

- Perform deterministic reasoning.
- Modify Runtime Objects.
- Consume raw Behavioral Events.
- Evaluate Decision Policies.
- Generate unsupported output structures.
- Invent facts.
- Override deterministic platform decisions.

---

# Relationship to Core Documentation

This chapter defines the contractual boundary between the deterministic Behavioral Intelligence Platform and the AI communication layer.

Related chapters include:

| Chapter | Responsibility |
|---------|----------------|
| 08 | Recommendation Engine |
| 09 | AI Buying Advisor |
| 10 | Decision Policies |
| 11 | Observability and Evaluation |
| 14 | Product Catalog |
| 16 | API Contracts |
| 17 | Platform Enumerations |
| 99 | Architecture Principles |

---

# Summary

The LLM Contract defines how Large Language Models interact with the Behavioral Intelligence Platform.

It establishes immutable boundaries between deterministic reasoning and AI communication.

The platform determines truth.

The LLM communicates truth.

The LLM consumes only approved Runtime Objects.

It never performs deterministic reasoning.

It never modifies deterministic platform outputs.

Its sole responsibility is producing grounded, explainable, contract-compliant AI Advisory Responses.

---
