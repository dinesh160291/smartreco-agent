# Decision #001

**Title:** Rename "Behavioral Hypothesis Engine" to "Behavioral Reasoning Engine"

**Status:** Accepted

## Decision

The architecture will use **Behavioral Reasoning Engine** instead of **Behavioral Hypothesis Engine**.

## Rationale

The engine is responsible for much more than generating hypotheses. It performs deterministic reasoning over behavioral evidence, including:

- Evidence accumulation
- Hypothesis generation
- Confidence evolution
- Buying stage transitions
- Requirement inference
- Behavioral state evolution

"Hypothesis Engine" describes only one responsibility, whereas "Behavioral Reasoning Engine" accurately represents the complete scope.

## Impact

All future architecture diagrams, documentation, and implementation will use the term **Behavioral Reasoning Engine (BRE)**.


# Decision #002

## Title

Behavioral Reasoning Engine is the deterministic core of the platform.

## Status

Accepted

## Decision

The Behavioral Reasoning Engine (BRE) is responsible for all deterministic behavioral reasoning.

The BRE owns:

- Behavioral Evidence
- Behavioral Hypotheses
- Confidence Evolution
- Behavioral Memory
- Requirement Profiles
- Buying Stage
- Recommendation Triggers

The BRE does not generate recommendations or natural language.

## Rationale

Separating deterministic behavioral reasoning from LLM reasoning improves:

- Explainability
- Replayability
- Testability
- Auditability
- Maintainability

The LLM reasons over deterministic behavioral state but never owns it.

## Consequences

All future components must consume BRE outputs rather than raw behavioral events.

The Recommendation Agent is prohibited from reasoning directly over raw interaction events.

# Decision #003

## Title

Separate the Behavioral Intelligence Platform from Domain Packs

## Status

Accepted

## Decision

The platform architecture is divided into two independent layers:

1. Behavioral Intelligence Platform (Core)
2. Domain Packs

The core platform implements deterministic behavioral reasoning.

Domain Packs provide domain-specific knowledge without modifying the reasoning engine.

## Rationale

This separation enables the Behavioral Intelligence Platform to be reused across multiple domains.

Only the Domain Pack changes when moving from Software Buying to Travel, Healthcare, Finance, Learning, or other domains.

## Consequences

The core Behavioral Reasoning Engine must remain completely domain-independent.

All domain vocabulary, personas, journeys, behaviors, requirements, heuristics, and examples belong inside Domain Packs.

Future domains should require no changes to the deterministic reasoning framework.

# Decision #004

## Title

Separate Behavioral Ontology from Behavioral Hypotheses

## Status

Accepted

## Decision

The Behavioral Ontology defines static behavioral concepts.

The Behavioral Reasoning Engine creates dynamic behavioral hypotheses for individual users based on those concepts.

## Rationale

Separating static domain knowledge from runtime behavioral state improves:

- Reusability
- Explainability
- Extensibility
- Testability

The ontology represents what behaviors can exist.

Behavioral hypotheses represent what currently exists for a particular user.

## Consequences

Behavioral concepts remain domain knowledge.

Confidence, evidence, timestamps, and behavioral memory remain runtime state owned by the Behavioral Reasoning Engine.

# Decision #005

## Title

Introduce Behavioral Patterns as a separate reasoning layer

## Status

Accepted

## Decision

Behavioral Patterns are a dedicated deterministic reasoning layer positioned between Behavioral Events and Behavioral Evidence.

Patterns transform sequences of observable user interactions into reusable behavioral evidence.

## Rationale

Separating patterns from events and ontology creates a clear reasoning pipeline:

Events → Patterns → Evidence → Hypotheses → Behavioral Memory

This separation improves explainability, modularity, replayability, and testability.

## Consequences

Behavioral Patterns become the deterministic rulebook executed by the Behavioral Reasoning Engine.

The Behavioral Ontology defines concepts.

Patterns determine when evidence for those concepts should be generated.

# Decision #006

## Title

Behavioral Evidence is the deterministic bridge between Behavioral Patterns and Behavioral Hypotheses

## Status

Accepted

## Decision

Behavioral Evidence is introduced as an immutable runtime object generated deterministically by Behavioral Patterns.

Evidence supports behavioral reasoning but never performs reasoning itself.

Evidence is persisted and becomes the primary input to the Behavioral Reasoning Engine when constructing and updating Behavioral Hypotheses.

## Rationale

Separating Evidence from Events and Hypotheses provides:

- Explainability
- Replayability
- Auditability
- Traceability
- Testability

Evidence becomes the currency of reasoning.

## Consequences

Every Behavioral Hypothesis must be supported by one or more Evidence objects.

Every Evidence object must reference:

- Originating Behavioral Pattern
- Originating Behavioral Events

This creates an end-to-end deterministic reasoning chain.

# Decision #007

## Title

Behavioral Hypotheses are persistent runtime objects

## Status

Accepted

## Decision

Behavioral Hypotheses are persistent runtime objects managed by the Behavioral Reasoning Engine (BRE).

They evolve throughout the user's buying journey and maintain their own lifecycle.

Behavioral Hypotheses are not temporary calculations.

## Lifecycle

Created

↓

Strengthened

↓

Stabilized

↓

Weakened

↓

Retired

## Rationale

The platform aims to understand how user intent evolves over time.

Persistent Behavioral Hypotheses allow the system to:

- Preserve evolving beliefs
- Track changing intent
- Explain historical decisions
- Support replay
- Improve explainability

## Consequences

Behavioral Hypotheses become first-class runtime objects.

They are persisted in Behavioral Memory.

Confidence evolves over time as new Behavioral Evidence is generated.

The BRE updates existing hypotheses instead of recalculating them from scratch.

# Decision #008

## Title

Behavioral Hypotheses belong to the Core Platform

## Status

Accepted

## Decision

The Behavioral Hypothesis model is a core platform capability.

The Behavioral Reasoning Engine manages hypothesis lifecycle, confidence evolution, evidence relationships, and persistence independently of any domain.

Domain Packs define the available Behavioral Concepts from which runtime Behavioral Hypotheses are instantiated.

## Rationale

The lifecycle and management of hypotheses are identical across domains.

Only the domain-specific concepts change.

Separating the hypothesis engine from domain knowledge preserves platform reusability and prevents duplication across domains.

## Consequences

Behavioral Hypotheses will be documented under `docs/core/`.

Domain Packs will define Behavioral Concepts that the BRE can instantiate as Behavioral Hypotheses.

# Decision #009

## Title

Behavioral Hypotheses are first-class persistent runtime objects

## Status

Accepted

## Decision

Behavioral Hypotheses are modeled as first-class runtime entities managed by the Behavioral Reasoning Engine.

They persist across sessions, evolve incrementally, and maintain references to supporting Behavioral Evidence.

## Rationale

Persistent hypotheses allow the platform to model evolving user intent instead of repeatedly recalculating beliefs from raw behavioral history.

This improves explainability, replayability, auditability, and long-term behavioral understanding.

## Consequences

Behavioral Hypotheses become the central runtime reasoning object of the platform.

Behavioral Evidence supports hypotheses.

Behavioral Memory persists them.

The LLM consumes them but never owns or modifies them.

# Decision #010

## Title

Behavioral Memory is composed of Journey Memory and Behavioral Profile

## Status

Accepted

## Decision

Behavioral Memory consists of two complementary components:

- Journey Memory (short-term reasoning)
- Behavioral Profile (long-term behavioral learning)

Journey Memory captures a single buying journey.

Behavioral Profile captures durable behavioral traits accumulated across multiple journeys.

## Rationale

Separating short-term intent from long-term behavioral identity allows the platform to:

- Adapt immediately to changing user intent.
- Preserve long-term behavioral learning.
- Support contradictory buying contexts.
- Prevent historical preferences from dominating current recommendations.

Behavioral Traits evolve gradually through reinforcement and deterministic decay.

## Consequences

Current recommendations are driven by the Active Journey.

Behavioral Profile provides historical priors but never overrides current journey behavior.

Completed journeys become immutable historical records that support replay, explainability, and longitudinal behavioral analysis.

# Decision #011

## Title

Introduce the Behavioral Learning Engine (BLE)

## Status

Accepted

## Decision

The Behavioral Learning Engine is introduced as a dedicated deterministic component responsible for converting completed buying journeys into long-term behavioral learning.

The BLE updates the Behavioral Profile by reinforcing or creating Behavioral Traits based on Journey Outcome and Behavioral Hypothesis Confidence.

## Rationale

Separating learning from reasoning preserves single responsibility across the platform.

The Behavioral Reasoning Engine understands the current journey.

The Behavioral Learning Engine determines what should become long-term behavioral identity.

## Consequences

Behavioral Profile becomes the only component modified by the Behavioral Learning Engine.

Journey Memory remains immutable after completion.

Behavioral learning is deterministic, explainable, replayable, and independent of the LLM.

# Decision #012

## Title

Separate Behavioral Learning from Behavioral Decay

## Status

Accepted

## Decision

The platform introduces a dedicated Behavioral Decay Engine (BDE).

The Behavioral Learning Engine reinforces long-term Behavioral Traits.

The Behavioral Decay Engine gradually reduces confidence in Behavioral Traits when they are no longer reinforced.

Behavioral knowledge is never deleted.

Only confidence evolves.

## Rationale

Human behavior changes gradually.

Long-term identity should evolve through reinforcement and decay rather than abrupt replacement.

Separating learning and forgetting preserves explainability, replayability, and deterministic behavior.

## Consequences

Behavioral Traits maintain:

- Trait Strength
- Reinforcement Count
- Last Reinforced Timestamp

The Behavioral Decay Engine updates only the Behavioral Profile.

Journey Memory remains immutable.

# Decision #013

## Title

Introduce the Confidence Engine

## Status

Accepted

## Decision

The platform introduces a dedicated Confidence Engine responsible for updating Behavioral Hypothesis confidence using deterministic behavioral evidence.

Confidence is earned through accumulated behavioral evidence rather than predicted by an LLM.

Every confidence value must include a deterministic Confidence Explanation.

## Rationale

Separating confidence management from behavioral reasoning improves explainability, replayability, debugging, and deterministic evaluation.

Confidence reflects the platform's certainty in its current understanding of user behavior rather than the probability of a future outcome.

## Consequences

Behavioral Hypotheses maintain:

- Confidence Score
- Confidence Explanation
- Confidence Metadata

The Confidence Engine becomes the single authority responsible for confidence evolution throughout the platform.

# Decision #014

## Title

Requirements are vendor-neutral business needs

## Status

Accepted

## Decision

The Requirement Engine infers business requirements rather than vendor-specific product features.

Requirements represent business needs such as:

- Security
- Workflow Automation
- Identity Management
- Source Code Integration
- Reporting

Vendor-specific features belong to the Product Catalog.

## Rationale

Separating requirements from products allows the Behavioral Intelligence Platform to remain vendor-neutral and reusable across industries and recommendation domains.

The Recommendation Engine becomes responsible for mapping requirements to products.

# Decision #015

## Title

Requirements maintain both Confidence and Priority

## Status

Accepted

## Decision

Every Requirement maintains two independent dimensions:

- Confidence
- Priority

Confidence represents how certain the platform is that the requirement exists.

Priority represents how important that requirement appears within the user's current buying journey.

These values are independent.

## Rationale

Users may exhibit strong evidence for a requirement that is not central to their purchasing decision.

Separating Confidence from Priority improves recommendation quality, explainability, and deterministic reasoning.

## Consequences

The Recommendation Engine should optimize primarily for:

- High Priority Requirements
- High Confidence Requirements

rather than treating all inferred requirements equally.

# Decision #016

## Title

Journey Stage becomes the orchestration signal for the platform

## Status

Accepted

## Decision

The Journey Stage Engine determines the user's current decision-making stage using deterministic reasoning. 

Journey Stage acts as the orchestration signal for downstream user experiences.

Recommendations, educational content, sales engagement, and product guidance are adapted according to the user's current Journey Stage.

## Rationale

The same recommendation presented at different stages of a user's journey can have very different effectiveness.

Separating stage determination from recommendation generation improves personalization, explainability, and platform flexibility.

## Consequences

Journey Stage becomes a first-class runtime object.

Recommendation strategies become stage-aware while remaining independent of behavioral reasoning.

# Decision #017

## Title

Recommendation Engine produces an immutable Recommendation Package

## Status

Accepted

## Decision

The Recommendation Engine terminates the deterministic reasoning pipeline by producing an immutable Recommendation Package.

The Recommendation Package contains all deterministic recommendation artifacts required by downstream AI systems.

The AI Buying Advisor consumes the Recommendation Package but is never permitted to modify its contents.

## Rationale

Separating deterministic recommendation generation from AI communication preserves explainability, reproducibility, replayability, and debugging.

The Recommendation Engine owns truth.

The AI Buying Advisor owns communication.

## Consequences

Recommendation Packages become versioned runtime artifacts.

Every recommendation remains fully traceable back to behavioral evidence through the deterministic reasoning pipeline.

# Decision #018

## Title

Recommendation Readiness gates AI recommendations

## Status

Accepted

## Decision

The deterministic platform determines Recommendation Readiness before any AI interaction.

When Recommendation Readiness is:

READY

→ AI Buying Advisor generates personalized buying guidance.

NOT_READY

→ AI Buying Advisor does not recommend products.

Instead, it explains missing information and asks targeted clarifying questions.

## Rationale

The deterministic platform decides when sufficient evidence exists.

The AI decides how to communicate that decision.

This prevents premature recommendations while maintaining deterministic control over decision-making.

## Consequences

Recommendation Readiness becomes the gatekeeper between deterministic reasoning and AI advisory.

# Decision #019

## Title

Introduce the AI Buying Advisor

## Status

Accepted

## Decision

The platform introduces a dedicated AI Buying Advisor responsible for transforming deterministic recommendation artifacts into personalized buying guidance.

The AI Buying Advisor never performs deterministic reasoning.

It consumes immutable Recommendation Packages as ground truth.

## Rationale

Separating deterministic reasoning from AI communication improves explainability, governance, replayability, and user trust.

The deterministic platform determines truth.

The AI communicates truth.

## Consequences

The AI Buying Advisor becomes the only component responsible for natural language interaction with users.

All deterministic reasoning remains outside the LLM.

# Decision #020

## Title

Every user-visible statement has an owner

## Status

Accepted

## Decision

Every user-visible statement generated by the platform must have a clearly defined owner.

The Deterministic Platform owns facts.

The AI Buying Advisor owns communication.

This ownership model applies throughout the entire system.

## Rationale

Separating facts from AI-generated communication provides complete traceability, explainability, and governance.

Users and developers can always identify whether information originated from deterministic reasoning or AI synthesis.

## Consequences

All UI components should preserve ownership metadata for every section presented to users.

# Decision #021

## Title

Business decisions are governed by policies

## Status

Accepted

## Decision

All deterministic business decisions are governed by versioned policies.

Platform engines execute reasoning.

Decision Policies determine when deterministic actions are permitted.

Business thresholds must never be hardcoded inside platform engines.

## Rationale

Separating reasoning from business governance improves configurability, replayability, explainability, and long-term maintainability.

Business behavior evolves through policy changes rather than code changes.

## Consequences

Every platform engine delegates business decisions to the Decision Policy Engine.

All policy evaluations produce deterministic Policy Evaluation Results.

# Decision #022

## Title

Every deterministic decision must be observable

## Status

Accepted

## Decision

The Behavioral Intelligence Platform treats observability as a first-class architectural capability.

Every deterministic decision must support:

- Inspection
- Explainability
- Replay
- Traceability

Observability applies uniformly across all deterministic engines.

## Rationale

Production AI systems require deterministic transparency.

Complete observability simplifies debugging, evaluation, governance, and continuous improvement.

## Consequences

Every deterministic engine emits execution metadata.

Every runtime object preserves lineage.

Every recommendation can be reconstructed through deterministic replay.

# Decision #023

## Title

Journey Resolution is determined by multiple signals

## Status

Accepted

## Decision

The Journey Resolution Engine determines whether a new session belongs to an existing Journey or starts a new Journey.

Journey resolution is determined using multiple deterministic signals rather than a single heuristic.

Signals include:

- Topic Similarity
- Behavioral Similarity
- Time Decay
- Journey Status
- Previous Journey Outcome

Time influences journey resolution but never determines it.

## Rationale

Enterprise buying journeys frequently span weeks or months.

Using time alone would incorrectly split a single buying journey into multiple unrelated journeys.

A multi-signal approach better reflects real user behavior while remaining deterministic.

## Consequences

The Journey Resolution Engine evaluates a Journey Resolution Score.

If the score exceeds the configured threshold, the existing Journey is reactivated.

Otherwise, a new Journey is created.

# Decision #024

## Title

Journey Resolution determines Journey ownership

## Status

Accepted

## Decision

The platform introduces a dedicated Journey Resolution Engine responsible for assigning Journey ownership before behavioral reasoning begins.

Journey Resolution evaluates multiple deterministic signals to determine whether a Session should:

- Continue an existing Journey
- Reactivate a Dormant Journey
- Create a new Journey

Time influences Journey Resolution but never determines it.

## Rationale

Separating Journey Resolution from Behavioral Reasoning eliminates hidden assumptions regarding Journey ownership.

It enables long-running enterprise buying journeys while remaining deterministic and replayable.

## Consequences

Behavioral Events receive a Journey ID only after Journey Resolution completes.

All downstream platform engines operate on resolved Journeys.

# Decision #025

## Title

Behavioral Events are immutable facts

## Status

Accepted

## Decision

The Behavioral Intelligence Platform treats Behavioral Events as immutable factual records.

Behavioral Events capture objective observations only.

Behavioral interpretation is performed exclusively by downstream deterministic reasoning engines.

Behavioral Events support schema versioning to evolve the event contract while preserving historical compatibility.

## Rationale

Separating facts from interpretation preserves replayability, explainability, and future reasoning improvements.

Historical events remain valid even as reasoning algorithms evolve.

## Consequences

Behavioral Events become the canonical input contract for the platform.

Schema evolution is managed through Schema Version rather than modifying historical events.

# Decision #026

## Title

Separate Product Catalog contracts from Product Catalog data

## Status

Accepted

## Decision

The Behavioral Intelligence Platform defines the Product Catalog contract.

Domain Packs provide the actual Product Catalog data.

The Product Catalog contract defines the structure of Product Capability Profiles.

Product definitions, capabilities, and taxonomies are owned by individual Domain Packs.

## Rationale

Separating contracts from domain data keeps the core platform reusable across multiple domains while allowing each Domain Pack to define its own products and capability taxonomy.

## Consequences

The Recommendation Engine consumes Product Capability Profiles using a common contract.

Adding a new domain requires only a new Domain Pack.

The core platform remains unchanged.

# Decision #027

## Title

LLMs interact with the platform through a formal contract

## Status

Accepted

## Decision

The Behavioral Intelligence Platform defines a formal LLM Contract.

The contract specifies:

- Approved runtime inputs
- Prompt composition
- Grounding rules
- Output contracts
- Safety rules

The contract is independent of any specific LLM provider.

## Rationale

Treating the LLM as a platform component rather than an implementation detail improves portability, governance, testing, and maintainability.

Future LLM providers can be adopted without changing platform architecture.

## Consequences

The platform depends on the LLM Contract rather than any individual model implementation.

Prompt evolution is managed independently from deterministic reasoning.

# Decision #028

## Title

All external communication occurs through versioned API Contracts

## Status

Accepted

## Decision

The Behavioral Intelligence Platform exposes all functionality through standardized API Contracts.

APIs define communication boundaries between external clients and platform engines.

Every API follows a canonical request and response structure.

## Rationale

Standardized API Contracts improve interoperability, maintainability, client compatibility, and long-term platform evolution.

Separating communication from business logic preserves the integrity of the deterministic reasoning platform.

## Consequences

All platform functionality is accessed through versioned APIs.

Clients interact only with API Contracts and never directly with internal platform engines.

# Decision #029

## Title

Normalize the Behavioral Intelligence Platform into a Contract-First Architecture

## Status

Accepted

## Decision

The Behavioral Intelligence Platform is formally established as a contract-first deterministic architecture.

The platform consists of independently owned deterministic components that communicate exclusively through immutable Runtime Objects.

Platform responsibilities are separated into distinct architectural layers:

- Behavioral Intelligence Platform (determines truth)
- Decision Policy Framework (authorizes business actions)
- AI Buying Advisor (communicates deterministic outcomes)

The Runtime Object Model becomes the canonical communication model for the platform.

All platform contracts, runtime artifacts, and platform vocabulary are standardized and versioned.

## Rationale

As the architecture evolved, deterministic reasoning expanded beyond a single Behavioral Reasoning Engine into a collection of specialized platform engines.

This evolution revealed that the architecture is fundamentally organized around stable contracts rather than individual implementations.

Adopting a contract-first architecture improves:

- Separation of responsibilities
- Explainability
- Replayability
- Traceability
- Versioning
- Independent evolution
- Long-term maintainability

## Consequences

The Behavioral Intelligence Platform becomes the canonical architectural boundary.

Platform engines communicate exclusively through Runtime Objects.

Business behavior is governed by the Decision Policy Framework.

AI communicates deterministic platform outputs but never establishes platform truth.

The Runtime Object Model becomes the canonical specification for Runtime Objects.

Platform Enumerations become the canonical vocabulary shared across the platform.

Future architectural evolution should extend contracts rather than modify existing responsibilities.

# Decision #030

## Title

Product knowledge is split into contract (knowledge) and records (data)

## Status

Accepted

## Decision

The Domain Pack owns the Product Capability Profile contract, the Capability taxonomy, and reference profiles. Product records are runtime data managed by administrators through the Admin Product APIs, dual-written to the relational store (system of record) and the vector store under the Semantic Retrieval Engine's dual-write contract.

## Rationale

A live platform requires admin-managed catalogs; a reusable platform requires canonical taxonomies. Splitting contract from data provides both: admins add products at any time, while capability vocabulary evolves only through governed Domain Pack versions. This also satisfies the requirement that products be dual-written to SQL and a vector database and kept in sync.

## Consequences

Governance Law 4 was clarified: it governs contracts and taxonomies, never data entered under them. Chapter 14 defines the split; Chapter 20 owns the dual-write contract; Chapter 16 defines the Admin Product APIs.

# Decision #031

## Title

The AI boundary becomes two-tiered

## Status

Accepted

## Decision

AI operates in exactly two tiers. Tier 1 — Generative Communication (the AI Buying Advisor, unchanged). Tier 2 — Semantic Services (embeddings, retrieval-quality evaluation, query refinement), permitted exclusively inside the Semantic Retrieval Engine. Tier 2 proposes candidates only: never final rankings, never Runtime Object mutation, never Recommendation Readiness influence.

## Rationale

Grounded recommendations over a live catalog require semantic retrieval, and an agentic workflow requires AI-assisted retrieval evaluation. A single post-reasoning AI boundary made both illegal. The two-tier boundary admits them in a fenced yard while deterministic engines remain AI-free — agentic retrieval, deterministic truth.

## Consequences

Principle 11 was amended. Chapter 20 defines Tier 2 and the Candidate Set Runtime Object. The Recommendation Engine consumes Candidate Sets as scoping input; final ranking remains deterministic capability matching.

# Decision #032

## Title

Grounded persuasion is an explicit AI Buying Advisor responsibility

## Status

Accepted

## Decision

The AI Advisory Response includes a Persuasive Buying Narrative governed by the Grounded Persuasion Mandate: compelling, action-oriented copy built exclusively from facts present in approved Runtime Objects. Invented social proof, scarcity, discounts, or capabilities are prohibited.

## Rationale

Recommendations exist to motivate action. Persuasion that changes how the truth is told — never what the truth is — delivers motivating copy with zero hallucination risk by construction.

## Consequences

Chapter 09 gained the mandate and the renamed AAR section; the Prompt Library gained Persuasive Narrative and Digest Recap templates.

# Decision #033

## Title

The execution surface becomes explicit: reasoning ownership, orchestration, ingestion, triggers, delivery

## Status

Accepted

## Decision

Five execution gaps were closed as core chapters: the Behavioral Reasoning Engine (Chapter 19) canonically owns Events → Evidence → Hypotheses, superseding the names "Behavioral Hypothesis Engine" and earlier uses of "Behavioral Reasoning Engine"; Agent Orchestration (Chapter 21) defines the framework-agnostic workflow graph; Event Ingestion & Tracking (Chapter 22) defines the batched, non-blocking tracking contract; Execution Triggers & Caching (Chapter 23) defines when the pipeline and AI run; Proactive Delivery (Chapter 24) defines the scheduled digest as a delivery surface reusing the standard workflow.

## Rationale

The architecture specified what every engine does but never who owns the first reasoning step, when anything runs, how events arrive, or how results leave the platform. Execution semantics belong in the architecture, not in implementation folklore.

## Consequences

The Runtime Object Model registers Candidate Set and Delivery Record and names the BRE as owner of Evidence and Hypotheses. Chapter 10 gained Policy Catalog v1 — the initial published values for every threshold the engines consume.

# Decision #034

## Title

All AI calls pass through one provider-agnostic AI Provider Gateway

## Status

Accepted

## Decision

Tier 1 and Tier 2 calls route through a single OpenAI-compatible gateway configured by base URL, key, and model IDs, supplied entirely by deployment configuration. Swapping providers is configuration, never code. The specification names no provider; keys live in the environment and are never committed.

## Rationale

Deployments may be bound to a specific gateway provider by their environment's requirements while the platform itself stays portable to any OpenAI-compatible provider. One boundary gives both, plus a single place for budgets, tracing, and usage accounting.

## Consequences

Chapters 15 and 20 define the gateway; Chapter 23's budgets and Chapter 11's AI-call observability attach to it.
# Decision #035

## Title

REQ-004 capability set fixed at four capabilities; CAP-001 Supporting association removed

## Status

Accepted

## Decision

The Business Requirement → Capability Mapping (Domain 07) listed CAP-001 Single Sign-On as a Supporting association of REQ-004 Regulatory Compliance, while every derivation in the Reference Behavioral Journey Scenarios (Domain 09) — and the platform's binding acceptance numbers (Okta 81% / Microsoft 365 70% / Google Workspace 58% in Scenario 1; the Scenario 4 coverage set) — computes REQ-004 coverage over exactly four capabilities (CAP-010, CAP-012, CAP-013, CAP-014). The two documents contradicted each other. The scenario derivations are the acceptance contract, so Domain 07 was amended: REQ-004 carries no Supporting association.

## Rationale

Scenario numbers are exact, executable acceptance criteria ("an implementation that seeds these profiles and replays these behaviors must reproduce these exact numbers" — Domain 09). A five-capability REQ-004 would change Okta's Scenario 1 overall coverage from 81% to 85% and break Scenario 4. Identity's reinforcement of compliance is already expressed at the BC → REQ layer (BC-004 → REQ-002 Secondary); duplicating it at the capability layer double-counted the relationship.

## Consequences

Domain 07 REQ-004 Supporting Association is now empty. The REQ→CAP fixture and coverage engine derive from the four-capability set. No scenario numbers change.

# Decision #036

## Title

POL-CONF-002 identity of "repeated identical Evidence" defined as (pattern, strength, event-type composition)

## Status

Accepted

## Decision

POL-CONF-002 ("Repeated identical Evidence contributes at 50% of prior contribution") did not define "identical". The Behavioral Reasoning Engine already deduplicates identical pattern activations over the same supporting events, so identity-by-event-set would make the policy unreachable; identity-by-pattern-alone would cap single-pattern hypothesis confidence near 0.4 (a geometric series of one class contribution), making the Domain 09 scenario confidences (0.80 / 0.70 / 0.50) underivable — no v1 concept is supported by more than one pattern, so the diversity increment cannot close the gap. "Identical" is now defined as: same pattern, same strength, and same supporting event-type composition (the multiset of event types backing the Evidence). Evidence of the same pattern with a different strength or a different event-type composition contributes at full class value.

## Rationale

This preserves the policy's anti-gaming intent — viewing the same pricing page twenty times produces evidence of identical composition and diminishes — while diverse research (security pages, then security + documentation, then documentation + search) accumulates at full value, which is exactly the diversity philosophy of the Confidence Engine chapter ("confidence grows through evidence quality"). It is deterministic, replayable, and unit-testable, and it makes the stated scenario hypothesis confidences reachable from honest clickstreams.

## Consequences

Chapter 10's POL-CONF-002 row and config/policies.yaml carry the identity definition. The Confidence Engine's unit tests pin both behaviors: identical-composition repeats halve; changed-composition evidence contributes fully. Policy Catalog stays at version 1.0 — this resolves an ambiguity rather than changing a published value.

# Decision #037

## Title

Story 2 outcome binds exact scenario coverages and relative order, not absolute ranks

## Status

Accepted

## Decision

Story 2 asserted Google Workspace at absolute rank 1 (92%). Over the canonical ten-product fixture, Microsoft 365's capability profile fully covers both derived requirements (REQ-001 7/7, REQ-005 5/5 → 100% weighted coverage), so the deterministic ranker places it above Google Workspace whenever it is a candidate — and with top_K = 8 over ten products it always is. The Scenario 2 derivation evaluated only Google Workspace, Notion, and Zoom, and never claimed Microsoft 365 was absent. Story 2's outcome is amended to bind: the three scenario products' exact coverages (92 / 41 / 33), their relative order, and the absence of workflow-automation products from the top three.

## Rationale

The alternatives were worse: trimming Microsoft 365's capability profile to force the old assertion would violate the fixture-integrity rule (never adjust seed data to make an exact assertion pass), and suppressing a full-coverage candidate in the ranker would corrupt the deterministic matching contract. The derivation math — the part the platform actually proves — is preserved exactly.

## Consequences

user-journey-stories.md Story 2 amended. The acceptance test asserts exact coverages, relative order, and automation-product absence. Scenario 2 in Domain 09 is unchanged.

# Decision #038

## Title

Policy Catalog v1.1 — trigger pacing retuned for live demonstration

## Status

Accepted

## Decision

POL-TRIG-002 changes from debounce 60s / cooldown 10min to debounce 30s / cooldown 3min, publishing Policy Catalog v1.1. No other policy value changes. Historical workflow runs recorded policy_version 1.0 and remain replayable under it.

## Rationale

The v1 values were correct efficiency defaults but made the live demonstration arc (browse → recommendations building over successive runs) take tens of minutes of wall-clock waiting. The catalog is explicitly configuration ("values are deliberately demo-friendly and are expected to be tuned; every change produces a new policy version" — Chapter 10). A 3-minute cooldown preserves the burst-coalescing and anti-churn guarantees at demo timescales.

## Consequences

config/policies.yaml carries catalog_version 1.1; the Chapter 10 table records both values; engines are untouched (they read the loader). Tests pin the new values; acceptance-story fixtures already space runs beyond both cooldown values.

# Decision #039

## Title

Candidate Set similarity score — definition pinned; POL-RETR-002's skip gate documented as inert

## Status

Accepted

## Decision

The Candidate Set similarity score is defined as `1 − distance` for the vector index's configured space (Chapter 20, "Similarity Score — Definition"). In the reference deployment the space is squared L2 over unit-normalized vectors, so the recorded score equals `2 × cosine − 1`, ranges over [−1, 1], and may be negative. POL-RETR-002's 0.85 skip threshold is expressed in this quantity and is documented as not firing in practice: Tier 2 evaluation runs on every retrieval. No code, policy value, or index changes; catalog_version remains 1.1.

## Rationale

The specification named a "similarity score" and set a threshold against it without ever defining the metric. Validation against the 250-product demo index measured the gap: a Behavioral Query Document scores 0.29–0.34 against its best real candidate (cosine ≈ 0.65), while the 0.85 gate requires cosine ≥ 0.925. The gate was therefore unreachable, and the recorded number was uninterpretable to anyone reading a Candidate Set — negative entries look like a fault.

Defining the quantity rather than changing it was chosen deliberately. Always evaluating is the conservative direction: evaluation is a quality gate, and skipping it is an optimization the platform does not need at demonstration scale (one Tier 2 call per retrieval against a 20/user/day budget). Converting the score to true cosine is a monotonic transform that changes no ranking, so it would have bought interpretability at the cost of a behavior change to a spec-mandated seam, and would still not have made the gate fire. Retuning the threshold to a value fitted from observed data was rejected as deriving a policy number from measurement rather than from the specification.

## Consequences

Chapter 20 gains a "Similarity Score — Definition" section; the Chapter 10 POL-RETR-002 row cites it and a note records the inert gate and its Tier 2 cost; `config/policies.yaml` mirrors the amended rule text (rule prose only — every parameter value is unchanged, so no new catalog version); `data-model.md` candidate_sets notes the range. Engines, tests, and the index are untouched; 139 tests remain green. Retuning the threshold for a backend with closer query/document vectors remains available as a policy-version change.

# Decision #040

## Title

Platform/domain boundary made structural — domain knowledge relocated out of the engines, core chapters and implementation docs

## Status

Accepted

## Decision

Domain knowledge is removed from every platform surface and consolidated in the Domain Pack, reached through a single indirection.

**Code.** The Software Buying pack becomes a package (`domain/software_buying/`) split by contract artifact: `knowledge.py` (declarative reference knowledge), `enums.py` (event registry, journey stages — artifacts 7 and 8, moved out of `smartreco.enums`), `patterns.py` (BP-001…012 activation rules, moved out of `engines/patterns.py`). `engines/evidence.py` holds `EventView` and `EvidenceDraft` so the pack and the engine share shapes without importing each other. `engines/patterns.py` keeps only the mechanism — session windowing, evaluator dispatch, ordering. Stage milestones name their own pattern ids in the pack's `STAGE_MILESTONES` rather than inside the engine's dispatcher.

**Selection.** `smartreco.domain.active` resolves the configured pack from `DOMAIN_PACK` (default `software_buying`). Platform modules import `active`, never a pack by name.

**Docs.** Acceptance stories → `docs/domains/software-buying/11-user-journey-stories.md`. Catalog seed strategy → `12-catalog-seed-strategy.md`. EventType registry → `13-event-registry.md`. Core 22 and `data-model.md` keep their mechanisms and point at the pack. Illustrative identifiers in Core 10 and `stack-decisions.md` are reworded to neutral language.

**Enforcement.** `tests/test_domain_boundary.py` fails if any platform module or reusable document hardcodes a `BP/BC/CAP/REQ/PROD` identifier, if the pack stops supplying a contracted artifact, or if the import seam disappears. The one permanent exception is this decision log, whose historical entries legitimately name domain content.

## Rationale

The reuse claim — engines identical across domains, only the pack changes — was asserted in the architecture and contradicted by the code. `engines/patterns.py` held 442 lines of software-buying logic; `enums.py` held an event registry Core 22 explicitly said belonged to the active pack; the stage engine named BP-010 and BP-011 directly. A second domain could not have been added without editing engines, which is the failure the separation exists to prevent.

Nothing here changes behaviour. The evaluator bodies moved verbatim; the milestone change replaces two inline literals with the same two ids read from the pack. This was deliberate: mixing relocation with redesign would have made a refactor bug indistinguishable from an intended change, and the acceptance suite is the only thing proving the move was faithful.

The `DOMAIN_PACK` indirection was added rather than leaving direct imports, because a seam that every platform module bypasses is not a seam. Without it, swapping domains means editing each importer — the cost the boundary was meant to remove.

## Consequences

165 pre-existing tests unchanged and green (177 total including the boundary suite); live retrieval validation and catalog search verified unchanged against the demo database. `.env.example` gains `DOMAIN_PACK`. `knowledge/architecture/domain-pack-contract.md` moves from "known deviations" to "conformance". A second Domain Pack is now a directory plus a config value.

One defect was found and fixed in the boundary test itself while landing this: its identifier pattern matched `REQ-003` inside `POL-REQ-003`, flagging policy lookups as domain leakage. Acting on that false positive rewrote live `policies.param` calls and broke 25 tests before revert; the pattern now excludes the `POL-` prefix and the reason is recorded in the test.

# Decision #041

## Title

Session settlement — journey ownership is deferred until a session can be judged

## Status

Accepted

## Decision

A session's journey ownership is resolved only once the session has **settled**: it has at least `min_session_events` events (new POL-JRES-001 parameter, value 5), or a newer session proves it finished, or its last event predates the POL-TRACK-003 inactivity window. Sessions that have not settled are skipped and reconsidered on the next resolution pass.

Cold start is exempt: when the user has no candidate journey, resolution returns *create* regardless of session size, so deferring would only deny a first-time visitor a journey.

Policy Catalog published as v1.2. Chapter 12 gains a "Session Settlement" section.

## Rationale

Found in a live trace, not in review. A shopper browsed analytics products, paused three minutes, and resumed in the same category. Resolution ran while the resumed session was two events old, scored **0.438** against the existing journey, and forked. Seven events later the same session scored **0.653** — comfortably a continuation. Because Chapter 12 decides ownership exactly once per session, the premature call was permanent.

The cost was not bookkeeping. The stranded session carried a second `integrations`/`api` documentation view — the second piece of evidence for a concept that already had one, which is exactly what POL-BEH-001 requires to promote a hypothesis. Split across two journeys, neither half reached the bar, no requirement was derived, and the shopper saw no recommendations at all. Replaying the same event stream against the fix produces one journey instead of two.

The scoring was never wrong. Chapter 12 specified *how* to decide and left *when* unspecified, so the platform decided at the first workflow run after a session began, on whatever fragment existed at that instant. This closes that gap rather than touching the signals or their thresholds.

The bounded-deferral conditions are deliberate: an unbounded "wait for more events" rule would strand the events of anyone who views two pages and leaves, which reasons about nothing and is no better than misfiling them.

## Consequences

`config/policies.yaml` carries catalog_version 1.2 and the new parameter; Chapter 12 documents settlement; the policy signature test pins the value. Four new signature tests in `tests/test_session_settlement.py` cover the regression, the continuation, the timed-out session and the superseded session; 184 tests green.

Story 3 (cold-start browser) failed on the first implementation, which deferred every small session including a first visitor's. That failure produced the cold-start exemption — the acceptance suite catching an over-general rule is the mechanism working, and the exemption is principled rather than a carve-out: with no candidate journey there is no fork decision to protect.

# Decision #042

## Title

Workflow run lifecycle — POL-TRIG-005 concurrency enforced instead of merely specified

## Status

Accepted

## Decision

A workflow run claims its slot by inserting a `workflow_runs` row with `status = RUNNING` before executing any node, and releases it by finishing — `COMPLETED`, `SKIPPED`, or `FAILED`. Failure marks the row `FAILED` and re-raises. A partial unique index `uq_one_running_run_per_user` on `(user_id) WHERE status = 'RUNNING'` makes the constraint atomic; a losing claim is recorded as a SKIP with the policy's own wording.

## Rationale

Found by browsing the live application, not in review. The status literal `RUNNING` appeared in exactly two places in the codebase: the `ENGINE_STATUS` enum, and the query that counted rows holding it. **Nothing ever wrote it.** `run_in_flight` was therefore permanently false and POL-TRIG-005's gate — specified since v1, implemented in the trigger evaluator — could never fire. A live database of 153 runs contained 30 COMPLETED, 123 SKIPPED, and zero RUNNING.

The consequence was not theoretical. The tracking client flushes a batch per page and each batch schedules a background trigger evaluation; two rapid flushes raced. Both passed the dead gate, both resolved sessions and created a cold-start journey, and both inserted journey stage version 1:

    IntegrityError: UNIQUE constraint failed: journey_stages.journey_id, journey_stages.version

which surfaced as a 500 and left the user holding a duplicate empty journey. Because the pipeline targets the most recent journey, later runs then reasoned about the empty one.

Committing the claim before execution closes the practical window, but a read-then-write remains a race in principle, so the index closes it in fact. Catching the resulting `IntegrityError` narrowly and recording a SKIP is not error-swallowing: losing that race *is* the policy's "a trigger arriving during a run", and the SKIP is the prescribed outcome.

Releasing the claim on failure is equally load-bearing. Fail loud is the rule, but a run that fails while holding its claim fails *stuck* — every subsequent trigger for that user would be skipped forever. The exception still propagates so the orchestration's degradation paths see it.

## Consequences

`workflow_runs` gains the partial index (`data-model.md` amended); existing databases need it created once, which is idempotent. Six signature tests in `tests/test_run_concurrency.py` cover the announcement, the concurrent skip, release on success, release on crash with the exception still raised, single-journey cold start, and the index's atomicity. 189 tests green.

Historical runs recorded no RUNNING state; the Reasoning Panel's trigger log gains a genuinely reachable third status.

---

# Decision #043

## Title

Session identity is decided by the server — one browser tab, two shoppers, two journeys

## Status

Accepted

## Decision

The Session ID a client sends is a suggestion, never an identity claim. Ingestion namespaces it by the authenticated user (`u{user_id}:{client_session_id}`) before the session row is created or matched, so a stored session can never span two accounts. `repos.assign_journey` filters on `user_id` as well as `session_id`. The tracking client additionally starts a new session when the logged-in user changes.

## Rationale

Found by live browsing, and it is the most serious defect the live scenarios have surfaced. The tracking client keeps its session id in `sessionStorage`, which is scoped to the tab and origin — not to the person using it. Logging out of one account and into another in the same tab keeps sending the previous shopper's id. Ingestion resolved the session by that id alone:

    session_row = touched_sessions.get(sid) or db.get(models.Session, sid)

and journey resolution short-circuits on a session that already owns a journey:

    if session_row is not None and session_row.journey_id:
        repos.assign_journey(db, session_id, session_row.journey_id)

Neither checked ownership. In the live database one session row owned by user 8 carried 23 events from user 6, and 20 of user 6's events were filed into user 8's journey. The damage did not stop at misfiled rows: user 6's **workflow runs** then wrote Requirement Profile versions 4 and 5 and two Recommendation Packages onto user 8's journey. User 8's top recommendation changed from ServiceNow to Microsoft 365 — a product surfaced by a different person's browsing. Meanwhile user 6 never got a journey of their own, so their own reasoning silently produced nothing.

Candidate scoring was never implicated: `resolve_sessions` already restricts candidate journeys to `user_id`. Both holes were identity holes, so both are closed by identity rather than by scoring.

Namespacing was chosen over rejecting foreign-session events. Rejection is the other honest option and the endpoint already has a per-event `rejected` channel, but it discards a shopper's browsing until the client happens to rotate its id, and it makes correctness depend on client cooperation. Namespacing loses nothing, needs no cooperation, and puts the decision where identity is actually known.

The client-side change is defence in depth and is *not* what enforces isolation — the tracking client fails silently by design (Core 22), so it can never be the guarantee. It earns its place on its own terms: a session is one person's sitting, and continuing someone else's across a login makes the behavioural window a fiction.

## Consequences

Stored `session_id` values are no longer the client's literal string; nothing parses them, and `data-model.md` records the format as opaque. Core 22 gains the server-authority paragraph under *Identify honestly* and a new Invariant 8: no Session and no Journey ever holds more than one user's events. `repos.assign_journey` takes `user_id` — both call sites are in `pipeline.resolve_sessions`, where it is already in scope.

Six signature tests in `tests/test_session_user_isolation.py` reproduce the live failure through the real endpoint and pin the repository-level filter directly, plus one in `test_ui_tracking_contract.py` for the client. 202 tests green. All three locks were sabotage-verified; the client test passed for the wrong reason on the first attempt — asserting on the whole function matched `cfg.user` in the record being written even with the guard deleted — and was tightened to assert on the new-session condition itself.

Pre-existing data cannot be repaired by migration: Runtime Objects are insert-only, so contaminated Requirement Profile and Recommendation Package versions stay in history. Affected databases must be reseeded.

---

# Decision #044

## Title

The UI states intent instead of assuming it — pricing tiers, sales contact, and dwell topics

## Status

Accepted

## Decision

Opening the pricing surface emits `PRICING_VIEWED` with `product_id` only; a `tier` appears solely when the shopper opens a specific plan (`personal` or `enterprise`). The Enterprise plan carries a "Contact sales" control emitting `DEMO_REQUESTED`, which collects no personal data. Recommendation entries emit `RECOMMENDATION_CLICKED`. Each tab accrues dwell against the topic it actually documents. Every event type in the Domain Pack registry must be reachable from a surface or recorded as server-emitted, enforced as a ratchet.

## Rationale

Three of the fourteen registered event types could not be produced by the running product. Nothing emitted `DEMO_REQUESTED`, so a shopper asking to talk to sales — which BP-011 treats as a **Strong** adoption trigger — was indistinguishable from one reading a page. Nothing emitted `RECOMMENDATION_CLICKED`, so acting on a recommendation looked identical to finding the product by browsing, and the platform could not observe whether its own advice was taken. And every pane except Security set `data-dwell-topic=""`, which *clears* the topic, so BP-003's `dwell >= 60s` branch could never fire and time spent reading anything but the security pane counted for nothing.

The pricing tab was worse than missing: it was wrong. Every view emitted `tier: "enterprise"`, so glancing at pricing was recorded as evaluating an enterprise purchase. BP-002 keys on exactly that value, so the pattern was fed a fact the shopper never stated — and its contradiction branch, which reads `individual` / `free` / `personal`, had no surface that could ever produce those values. Half the pattern was unreachable and the other half was manufactured.

This is the same defect class as `2cb6134`, one level up. There the vocabulary inside an event was dead; here whole event types were. Both share a cause: the templates were written against what a page should *look* like, not against what the reasoning engine reads. The fix in each case is a ratchet that fails in CI rather than in a demo.

Two tiers rather than three: Personal versus Enterprise is the discriminating axis, and a middle "Team" tier blurs the very signal the surface exists to capture. Capabilities are deliberately **not** gated by tier — capability profiles are the substrate of coverage ranking, so tier-gating would make requirement satisfaction depend on which plan was opened and would reopen the pinned acceptance numbers.

No contact form. Events are append-only and immutable (Law 6), so personal data placed in event metadata could never be deleted; a deletion request would be impossible to honour without breaking the immutability the decision spine rests on. The account already holds an email, so the control records the *behaviour* — which is all the platform reasons about — and confirms that the team will follow up there. A future form would need its own mutable table, never the spine, and only fields that do work (team size, timeline feed POL-REC-004's deferred constraint derivation).

## Consequences

`PRICING_VIEWED.tier` becomes optional; consumers must treat its absence as "no intent stated" rather than defaulting. BP-009 is unaffected — it filters out tier-less events when checking same-tier focus, and still counts them as pricing consultation. BP-002's contradiction branch is reachable from a browser for the first time.

`ui-design-spec` §4.6a specifies the tier cards: the pricing pane opts out of the 68ch prose measure and centres a 720px row of two `flex: 1 1 0` cards, so they stay equal whatever their copy. Domain Pack 13 gains the reachability rule and the `tier` semantics. Four signature tests in `test_ui_tracking_contract.py` pin the registry ratchet, the tier-less tab hook, both tiers as vocabulary the patterns read, and per-pane dwell topics. 206 tests green, all sabotage-verified.

An earlier claim in this session that dwell "never fires" was too strong and is corrected here: BP-001's dwell path was wired correctly all along via the Security tab. What was broken is that no other pane carried a topic, and heartbeats are visible-only by design (POL-TRACK-002), so an automated window that is minimised produces none.

---

# Decision #045

## Title

Reading time substitutes for activity in exactly one pattern — remove the unspecified dwell path

## Status

Accepted

## Decision

Only Security Evaluation promotes evidence to Strong on dwell. The dwell clause the code carried in AI Evaluation is removed, matching Domain Pack doc 02. The dwell vocabulary is named in the pack (`DWELL_TOPICS`, now a single topic) and surfaces run a heartbeat only for topics in that set, so the Security pane is the only one with a stopwatch.

## Rationale

Doc 02 gives Security Evaluation the clause explicitly — *"Strong (≥ 4 qualifying events or supporting dwell)"* — and gives AI Evaluation *"Strong with ≥ 4 qualifying events"*, full stop. The code promoted on dwell in both. The divergence was invisible because **no test covered the AI path**; every dwell test in the suite exercised the security pattern.

The pack's asymmetry is deliberate, not an omission, and that is what decided the direction of the fix. Security interest can only be shown on a product's security page, and a product has exactly one, so reaching four qualifying events means visiting four separate products — reading a single product closely deserves an alternative route. AI Evaluation qualifies on documentation views, product views **and** searches, so four accumulate inside one product plus a couple of searches. It never needed an escape hatch, and giving it one made Strong cheaper there than anywhere else for no stated reason.

The alternative — amending doc 02 so the spec matched the code — was rejected. It would have been the easier edit, and the code had already shipped and been demonstrated, but changing a spec to match its implementation can rationalise any bug. It should require a positive argument, and here the argument ran the other way.

Doc 02 also lists `DWELL ≥ 60s` as *Optional Supporting* evidence for compliance, automation and integration research. That is lineage, not strength: supporting events appear in an evidence object's trail and change no confidence value. It remains unimplemented, knowingly.

## Consequences

Behaviour change: a shopper who reads an AI product's documentation for two minutes without other AI activity now produces Medium rather than Strong evidence, which is what the pack always specified. Nothing else moves — every click is unchanged, and the Security dwell path is untouched.

The Docs pane no longer needs a dwell topic, so `doc_dwell_topic` resolves to empty for every product and **Security is the only pane running a heartbeat** — simpler than the per-product conditional it replaces. `ui-design-spec` §4.6b records the rule.

Two signature tests in `tests/test_patterns_bre.py` pin both directions: reading time alone does not reach Strong, and four qualifying events still do. Sabotage-verified by reinstating the removed clause. 295 tests green.

This is the second defect this session found by reading the Domain Pack against the code rather than trusting the code (the first was the pricing tab asserting enterprise intent, Decision #044). Both had the same shape: the implementation was treated as the description of behaviour, and it was wrong.

---

# Decision #046

## Title

The Stage Engine reads event metadata — Adoption means onboarding *this* product

## Status

Accepted

## Decision

`determine_stage` takes journey events as `{event_type, metadata}` rather than a list of bare type names. The Adoption milestone now requires the corroborating documentation to be on an onboarding or migration topic **and** to concern a product the journey is actually adopting. Product Affinity co-supports Decision Confidence at Strong, as doc 02 specifies.

## Rationale

Found by auditing all twelve patterns against Domain Pack doc 02 after Decision #045 — the exercise that decision's rationale recommended. Activation and strength rules were eleven-of-twelve correct. The gaps were elsewhere.

**Adoption was reachable on the wrong evidence.** Doc 00 §4.1 defines the milestone as *"BP-011 Evidence exists and the journey's affinity product has onboarding/migration activity"*. The engine checked that BP-011 evidence existed and that the journey contained **any** `DOCUMENTATION_VIEWED` at all — no topic, no product. A shopper who started a trial and had once opened any product's docs tab reached the highest stage in the model.

That is not cosmetic. Stage gates the Critical priority band (POL-REQ-002 requires stage ≥ Technical Validation), and Critical carries triple weight in coverage ranking (POL-REC-002). An inflated stage can inflate a requirement's priority and reorder the recommendations a shopper sees.

The cause was visible in the seam: the engine received `event_types` as a list of strings, so it *could not* ask what a view was about. The weak check was the strongest expressible against that input. Widening the parameter is the fix; the milestone conditions then state themselves. The pattern that produces the adoption evidence already collects onboarding/migration views into its supporting events, so the vocabulary existed — only the milestone ignored it.

Product scoping falls back to topic alone when no product is identifiable. Some adoption triggers name no product — a checkout covers the whole cart — and demanding a match there would make Adoption unreachable for anyone who buys rather than trials.

**Product Affinity's co-support was simply missing.** Doc 02: *"BC-012 Product Affinity; sustained affinity co-supports BC-016 Decision Confidence."* Sustained is read as the pattern's own Strong bar — five qualifying events on one product. Adoption Readiness already co-supports that concept, so this was the only route to it for a shopper who converges without yet trialling or buying.

## Consequences

`determine_stage`'s signature changes; the single production caller in `pipeline` now passes metadata, and the stage tests were migrated mechanically. Behaviour was verified unchanged by that refactor before any milestone logic moved.

No acceptance story shifted stage: all twelve stories and the four derivation scenarios pass untouched, which is the evidence that this tightening corrects an over-eager path rather than breaking a working one. Journeys in existing databases may compute a *lower* Adoption stage on their next run, which is the point.

`STAGE_MILESTONES` gains `topics` and `product_event_types`; the latter is imported from the pattern that defines the triggers so the two cannot drift. Four signature tests in `test_stage_engine.py` and one in `test_patterns_bre_phase4.py`, all sabotage-verified. 301 tests green.

Three defects this session came from the same habit — describing behaviour by reading the implementation instead of the pack (Decisions #044, #045, and this one). The audit that found these two was itself the corrective, and it is worth repeating whenever the pack changes.

---

# Decision #047

## Title

Raise SESSION_END — reasoning must not depend on the shopper still clicking

## Status

Accepted

## Decision

The platform raises the `SESSION_END` trigger that Chapter 23 has always listed. A background sweep, running every `POL-TRACK-003.end_sweep_interval_minutes` (5), finds shoppers whose newest unprocessed high/medium event is older than that policy's inactivity window and runs the workflow for each with trigger type `SESSION_END`. The trigger evaluator gains the matching condition: unprocessed activity must exist **and** the session must be closed. `SESSION_END` does not bypass cooldown — only `STAGE_TRANSITION` does.

## Rationale

Chapter 23 names seven trigger types. Two were ever raised: `EVENT_ACCUMULATION`, from event ingestion, and `SCHEDULED`, from the digest. The other five existed in the enum and in the evaluator's gate sequence, reachable by nothing.

That made event ingestion the only thing that could wake the evaluator, and `EVENT_ACCUMULATION` needs POL-TRIG-001's five pending events. A shopper who stops below the threshold leaves work that nothing will ever collect — because the only thing that would collect it is another event from a shopper who has left. It is not a delay; it is permanent.

Found in a live trace. A shopper researched automation across four products, bought ServiceNow, and closed the tab. The purchase burst was four high-signal events. Four is not five, so no run started: the journey stayed ACTIVE, the purchase was never reasoned about, no trait was considered, and the shopper saw "not ready" on a journey the deterministic engines were one run from resolving. Replayed on a copy of that database, a single further run published the requirement at 0.60, flipped readiness to READY with ServiceNow at 100% coverage, and closed the journey as PURCHASED. Nothing was wrong with the reasoning. It never got its last run.

The same gap degrades journeys that do not end in a purchase. Confidence accumulates per run, not per event, so the number of runs a visit produces is a real input to the outcome. Two accounts performed the same research minutes apart in the same live session; the one that clicked more slowly produced three runs and reached READY, while the more thorough one produced two, stalled at 0.30 against the 0.50 publication bar, and left eleven events — including a trial start and a demo request — unprocessed forever. The thorough shopper got the worse answer.

**Why inactivity, not a client signal.** A `pagehide` beacon reports the boundary directly, but it is exactly the report that fails when it matters: a closed laptop, a killed tab, a crashed browser. The tracking client is silent by design (Core 22), so a beacon that never arrives is indistinguishable from a session that never ended. Inactivity is observed server-side from data already recorded, and POL-TRACK-003's window is already the session boundary for both the tracking client and journey resolution. Reusing it adds no new notion of "over".

**Why a sweep over users rather than session rows.** Once every session of a shopper's is past the inactivity window, they have no open session, and the workflow's unit is the shopper. Tracking closure per session row would need a schema column and its own bookkeeping to avoid re-firing; the user-level query needs neither, because a completed run stamps its events processed and the next sweep finds nothing. Candidates are pre-filtered in SQL rather than left to the evaluator, so a five-minute sweep does not write a SKIPPED row per idle shopper per tick — the trigger log stays a record of occasions, not of ticks. The evaluator re-checks both halves of the condition and remains the authority.

## Consequences

Journeys now resolve after the shopper leaves, which is when most journeys actually end. Purchases close their journeys without needing four more clicks; the Learning Engine sees closures it was previously never offered.

Existing databases self-heal: any journey sitting on unprocessed events is swept within five minutes of the next start-up, including the stranded case-3 journey that prompted this.

`POL-TRACK-003` gains a parameter, mirrored in the Chapter 10 catalog. `session_end_sweep` in `pipeline`, the condition in `engines/triggers`, and one APScheduler interval job — the same scheduler the digest already uses, which is why the deployment target remains a long-running host with a persistent disk.

Eight signature tests: four on the evaluator condition (`test_trigger_evaluator`), four on the sweep (`test_session_end_trigger`), all with a simulated clock and no real waits. Sabotage-verified: relaxing the inactivity cutoff reddens the still-shopping case, dropping the signal-class filter reddens the dwell-only case. 309 tests green.

The remaining four declared-but-unraised triggers — `SIGNIFICANT_EVENT`, `STAGE_TRANSITION`, `REQUIREMENT_SHIFT`, `ADMIN_CATALOG_CHANGE` — are unchanged and still unreachable. Each is a latent version of this same defect: a policy that cannot fire is a policy that is not implemented, however complete the evaluator looks. Scoped deliberately: this decision fixes the one that strands shoppers.

---

# Decision #048

## Title

Catalog v1.3 — retune pacing for demonstration, and pin the judgment values against drift

## Status

Accepted

## Decision

Catalog version 1.3. Four pacing values change:

| Policy | v1.2 | v1.3 |
|---|---|---|
| POL-TRIG-001 accumulation threshold | 5 events | **3** |
| POL-TRIG-002 cooldown | 180s | **45s** |
| POL-TRIG-003 daily AI budget | 10 / 20 | **30 / 40** |
| POL-TRACK-003 sweep interval | 5 min | **2 min** |

Debounce stays at 30s, the session-inactivity window stays at 30 minutes, and no confidence, publication, promotion, or readiness threshold moves.

## Rationale

Reaching a recommendation takes three or four workflow runs, because confidence accumulates per run rather than per event. At a 180-second cooldown that put a floor of roughly nine minutes under any demonstration, no matter how purposefully the shopper clicked — and the floor was invisible, so it read as the platform being unsure rather than the platform being rate-limited. The live traces made the cost concrete: two accounts performed the same research minutes apart, and the more thorough one produced fewer runs and the worse answer.

**The distinction this decision turns on** is between values that govern *how often the platform reasons* and values that govern *what it is willing to conclude*. Cooldown, accumulation threshold, sweep interval, and AI budget are the first kind: moving them changes latency and cost, and nothing else — every number the shopper sees is derived the same way and means the same thing. Publication at 0.5, readiness at 0.6, the confidence contributions, and hypothesis promotion are the second kind: moving them would make the platform assert confidence it has not earned, which is the one claim the whole design exists to support.

Precedent: Decision #038 already retuned this same cooldown for the same reason. This decision extends that and, more usefully, writes the distinction down.

**Budgets are raised because cadence consumes them.** The per-shopper daily AI budget is a fixed count, so quadrupling the run rate quadruples the draw on it. At 10 Tier-1 calls a rehearsed demonstration on one account would exhaust the budget mid-journey and silently degrade to the last stored narrative — correct behaviour under POL-TRIG-003, and indistinguishable on stage from the narrative having frozen. The AAR cache absorbs some of this (repeat runs over an unchanged package hit it), so 30/40 is headroom rather than a proportional increase.

**Two values deliberately left alone.** The 30-second debounce gates only SIGNIFICANT_EVENT, which nothing raises (Decision #047) — changing it would be theatre. The 30-minute inactivity window is not only the SESSION_END boundary: it is also what the tracking client uses to mint a new session id, and several patterns are session-scoped, with two reaching Strong only across multiple sessions. Shortening it to make the walk-away path demonstrable would risk manufacturing Strong evidence out of a clock, which is precisely the kind of number this decision refuses to move.

## Consequences

Roughly three minutes of steady clicking to a recommendation, against nine-plus. More runs land on NOT_READY before the picture forms, so the clarify path is seen more often — which is the honest shape of the system and arguably the better demonstration.

All twelve acceptance stories and the four derivation scenarios pass unchanged, which is the evidence that this retuning is pacing and not judgment: the derivations assert exact confidences and coverages, and none of them moved.

`test_policy_catalog` gains `test_judgment_thresholds_are_untouched_by_demo_pacing`, pinning publication, readiness, promotion, and the inactivity window, so a future pacing change cannot drift across the line this decision draws. Sabotage-verified: lowering publication to 0.4 fails it and seven acceptance tests with it.

The gate tests in `test_trigger_evaluator` and the burst in `test_session_end_trigger` now derive their inputs from the catalog rather than restating tuned numbers. They pin the rule — *below the threshold skips, at it runs* — while the values themselves are pinned in one place, the catalog test, where a retuning has to be declared. 310 tests green.

Runs recorded before this change carry policy_version 1.2 and are not comparable on timing; the decision spine is versioned precisely so that stays visible.

---

# Decision #049

## Title

Enterprise Evaluation requires an administration signal — company size is not a need

## Status

Accepted

## Decision

BP-002 Enterprise Evaluation activates only when at least one of its qualifying
events is an administration page (`DOCUMENTATION_VIEWED` topic admin,
provisioning or federation). Enterprise pricing tiers and compliance posture
pages still qualify and still contribute strength, but cannot activate the
pattern between them.

## Rationale

The pattern fired on any two of three signals: administration pages, enterprise
pricing tiers, compliance or audit pages. It maps **Primary** to REQ-002
Identity Management on doc 06's rationale that *"organizational adoption hinges
first on centralized identity"*.

Only one of those three signals supports that rationale. Administration pages
are about running identities at organizational scale. **Every product in the
catalog has an enterprise tier and a compliance posture page** — those two are
read by shoppers in every domain, and on their own they say the buyer is a
company, not what the company needs. Company size is a buyer attribute; the
mapping treated it as a product requirement.

The rule was sound when it was written, against a ten-product roster of
identity, collaboration and automation software, where enterprise-tier interest
genuinely was identity interest. It does not survive a 250-product marketplace.

**Observed.** A shopper searched "crm" and "sales pipeline", opened four CRM
products, compared them, priced them and requested a demo. At the run that
published the requirement profile, BP-002's qualifying evidence was four
enterprise-tier pricing views, zero administration pages, zero compliance pages.
It published Identity Management at 0.55.

The consequence was not cosmetic. Overall coverage averages across published
requirements, so an irrelevant need halves the score of every product that fits
the real one and lifts products that do not:

| | CRM need only | With the phantom identity need |
|---|---|---|
| HubSpot | 80% | 40% |
| Salesforce | 60% | 30% |
| Microsoft 365 | **0%** | **30%** |

Microsoft 365 covers none of a CRM need and was promoted into a tie with
Salesforce by a need the shopper never expressed.

**Nothing is lost by the tightening.** Pricing behaviour is already read by
BP-009 Commercial Evaluation. The same click was being counted twice — once by
the pattern that legitimately wants it, and once by a pattern drawing an
unsupported conclusion from it.

## Consequences

Every journey the specification describes still activates the pattern: Story 1
and the multi-session enterprise stories supply provisioning, admin and
federation views, and all three pre-existing unit tests include an
administration page. The twelve acceptance stories and four derivation
scenarios pass **untouched**, which is what distinguishes this from a
regression — the only journeys that lose the pattern are the unspecified ones it
was misclassifying.

Re-evaluated against the live CRM journey's 31 real events, BP-002 no longer
activates; the pricing views are read by BP-009 alone, as intended.

Doc 02 gains the clause and a counter-example; doc 06 records why the Primary
association depends on the administration half of the evidence. Three signature
tests in `test_patterns_bre.py`, two of them a replay of the live journey, both
watched red before the fix.

Landed ahead of the coverage extension (doc 14) deliberately. That change adds
seven patterns, and cross-contamination is its main risk; correcting the one
live instance first means the acceptance suite proves the correction in
isolation, before attribution gets harder.

**Left open.** Company size arguably should not map to a requirement at all —
ten of the eighteen concepts are already marked as informing stage, constraints
or ranking context without ever producing a requirement, and Enterprise
Evaluation may belong among them. Gating the evidence fixes the observed defect;
whether the association should exist at all is a larger argument, deliberately
not settled here.

---

# Decision #050

## Title

Enterprise Evaluation states the buyer's scale, not their need — the identity association is removed

## Status

Accepted

## Decision

BC-002 Enterprise Evaluation no longer maps Primary to REQ-002 Identity
Management. Its Secondary association to REQ-004 Regulatory Compliance is
retained. The concept joins those that inform stage, framing and ranking
context without ever publishing a requirement of its own.

## Rationale

Decision #049 required an administration page before the pattern could
activate, which stopped four enterprise-tier pricing clicks on four CRM
products from publishing an identity need. That narrowed the defect without
closing it.

**The hole it left, measured:** four HR products in the catalog — Rippling
among them — carry provisioning capabilities, so their integrations page
reports topic `provisioning`. An HR buyer reading it activates the pattern
*legitimately*, satisfies the new administration clause, and is still told they
need Identity Management. Narrower than before — four products instead of every
product with an enterprise tier — but the same wrong answer.

Which locates the defect properly. It was never in the evidence; it was in the
association. "This person is buying for an organization" answers *what kind of
buyer is this*, and it had been wired into the socket for *what do they want to
buy*. Ten of the eighteen concepts already sit on the correct side of that line,
marked as informing stage, constraints or ranking lifecycle without producing
requirements. This one belongs with them.

Nothing is lost: identity interest is carried by BC-001 Security Evaluation,
which reads the behavior that actually means it.

**Why the governance link stays.** Buying at organizational scale genuinely does
imply governance exposure, in a way it does not imply identity software. At
Secondary weight it can strengthen a compliance requirement that other evidence
supports while never publishing one alone — a lone Enterprise Evaluation
hypothesis at 0.70 derives 0.42, below POL-REQ-001's 0.5 bar. The test pins that.

**Why the partial demotion rather than the full one.** Removing both
associations was the purer reading and was rejected on evidence. It would have
dropped Regulatory Compliance out of Scenario 1's requirement profile entirely
(0.24, unpublished), collapsing the reference derivation from two requirements
to one and its coverage spread from 81/70/58 to 100/60/60 — a tie for second.
The flagship scenario exists to demonstrate multi-requirement derivation with
differentiated ranking; the purer change would have cost that to fix nothing the
partial change does not.

## Consequences

**One number moves in the entire specification.** Scenario 1's REQ-002 goes from
0.94 to 0.80 — same Critical band, same requirement set, same stage, same
coverage percentages (Okta 81%, Microsoft 365 70%, Google Workspace 58%), same
READY. That invariance is the evidence the change was surgical rather than
disruptive, and it is why the amendment to doc 09 is three lines rather than a
rewrite.

313 of 314 tests passed unchanged on the first run; the single failure was
Story 1's requirement confidence, which is exactly the number this decision
changes and nothing else. Two new signature tests: the amended Scenario 1
derivation, and one pinning that an enterprise buyer with no other evidence
publishes nothing at all.

Docs 02, 06 and 09 amended. Doc 06 retains the superseded rationale verbatim
rather than deleting it — it was correct for the ten-product roster it was
written against, and the way it failed as the catalog grew is the more useful
record.

This closes the item left open by Decision #049. It also settles the question
before the coverage extension (doc 14) adds seven more concepts: the line
between *what the buyer is* and *what the buyer needs* is now drawn explicitly,
and every new concept has to be placed on one side of it.

---

# Decision #051

## Title

Domain Pack v1.2 — every product in the catalog can be recommended

## Status

Accepted

## Decision

Seven new Business Requirements (REQ-006…012), seven Behavioral Concepts
(BC-019…025), seven patterns (BP-013…019), both mappings, and the per-tab topic
vocabulary that lets the patterns fire from a browser. The five original
requirements and their capability sets are unchanged. Implements doc 14.

## Rationale

The Capability Catalog extended to 55 capabilities in v1.1 so wide-catalog
products could describe themselves honestly, and deliberately left them out of
requirement coverage: the demo catalog was scenery, "realistic noise retrieval
and matching must cut through" (doc 10). That boundary stopped being defensible
once the catalog was presented as a marketplace.

**Measured against the seeded roster: 21 of 55 capabilities were named by any
requirement, and 82 of 250 products held none of them.** Those products were
searchable, viewable and addable to a cart, and could never appear in a
recommendation — coverage scoring had nothing to score them on. DevOps 16, HR
14, Marketing 13, Analytics 12, CRM 10, Finance 9.

**Observed.** A shopper searched "crm" and "sales pipeline", opened four CRM
products, compared them, priced them, requested a demo and started a trial. The
platform recommended Microsoft 365, ServiceNow and Zapier, with Salesforce
fifth. Retrieval understood the journey perfectly — Salesforce was in the
candidate set. The failure was downstream: with no CRM concept, no CRM
requirement and no CRM capability in any mapping, the CRM pages' integration and
automation vocabulary was the only thing the model could read, so it answered
the nearest question it had.

**Why all four links, together.** A requirement with no concept feeding it is
inert; a concept with no pattern producing it never forms; a pattern keyed on a
topic no surface emits cannot fire from a browser. Each new area needed the
whole chain, which is why this is a large change rather than a mapping edit.

**Why the original five are frozen.** Their capability-set sizes are the
denominators of every coverage percentage doc 09 asserts. A capability may
belong to several requirements, so new capabilities joining new requirements
costs nothing — and it makes the acceptance suite the safety proof: the twelve
stories and four derivation scenarios pass **untouched**, because the canonical
ten hold none of the new capabilities and the fixtures emit none of the new
topics.

## Consequences

53 of 55 capabilities reachable; **0 of 250 products unrecommendable**. File
Sharing and AI Workflow Assistance remain unmapped by choice: both sit inside
frozen requirements' domains, and no product depends on them for reachability.

**Two design errors were caught by tests rather than review, and both changed
the design:**

*REQ-011 Data & Insight* was drafted from the three Data & Analytics
capabilities alone. 21 catalog products hold all three, so the requirement
produced a 21-way tie at 100% — a ranking that is correct and useless. Fixed by
adding Intelligent Search and API Integration, and generalised into a new
invariant: **no requirement may be fully covered by more products than a
Candidate Set can hold** (POL-RETR-001 top_k). That threshold is not arbitrary —
past it, the whole recommendation list can be tied products.

*The distractor constraint* — "no non-canonical product may fully cover any
requirement" — was written when every requirement had a canonical winner to
protect. The new requirements have none: the canonical ten hold no CRM, HR,
finance, marketing, DevOps or analytics capability. Forbidding full coverage
there would forbid the marketplace from having a best-fit product, which is the
point of the change. Scoped to REQ-001…005; the discrimination invariant above
replaces it for the rest.

**The tab vocabulary moved into the pack**, where the contract has always placed
it (artifact 11) and where the web layer had been holding it. Salesforce's Docs
tab now reports `pipeline` rather than `workflows` — the mistranslation that
made a CRM journey read as automation research. `PATTERN_TOPICS` is assembled
from the same constants the evaluators read, so the reachability ratchet now
checks the code rather than a list restated in a test.

**The new patterns are evaluation patterns** and carry the Research and
Technical Validation milestones. Without that a CRM journey would sit at
Awareness forever, and since stage gates the Critical band, its needs could
never reach Critical while an identity journey's could.

Doc 09 gains Validation Scenario 5 with exact arithmetic — the regression case
for the observed journey, and the first scenario that exercises weighted
coverage across two requirements of different priority. It also records a
catalog-authoring observation rather than hiding it: Salesforce ranks last of
eight, because its editorial profile carries three CRM capabilities and no
marketing capability while HubSpot carries four and four. The ranking follows
the profile, and the profile is editable.

**Left open.** Four topics are read by patterns and emitted by nothing —
`admin`, `productivity`, `templates`, `tasks`, plus `automation`. Same class of
defect as Decision #044, predating this change and deliberately not folded into
it. The reachability ratchet only checks that emitted topics are read; the
reverse direction is still unguarded.

---

# Decision #052

## Title

A rule must be reachable to be a rule — the reverse vocabulary check, and the Adoption stage it unblocked

## Status

Accepted

## Decision

`test_ui_tracking_contract` gains the reverse-direction check: **every topic a
pattern reads must be emittable by some surface.** Three of the seven topics
that failed it are fixed, three are recorded as a shrinking ratchet, and one
was removed as a redundant synonym.

| Topic | Resolution |
|---|---|
| `onboarding` · `migration` | An owned product's Docs tab reports `onboarding`, its Integrations tab `migration` |
| `admin` | Conditional Access reports `admin` on the Docs tab, ordered after single sign-on |
| `automation` | Removed from BP-007 — a synonym for `workflows`/`triggers`, both emitted |
| `productivity` · `templates` · `tasks` | Ratchet entry: no capability in the catalog means task or template management |

## Rationale

Decision #044 established that an event type nothing emits is not implemented,
and added a ratchet: every topic a page emits must be read by some pattern. The
ratchet only ever ran in one direction. It could not see the opposite failure —
a pattern listening for a word no page says. Such a clause is documented,
unit-tested against synthetic events, and dead in production.

Seven topics were in that state. Five were harmless: spare synonyms beside words
that are emitted.

**Two were not.** Decision #046 tightened the Adoption stage milestone to require
a documentation view on `onboarding` or `migration`. No surface emitted either,
so **the highest stage in the model became unreachable from a browser** — the
tightening did not narrow Adoption, it closed it. Whether dead vocabulary is
cosmetic depends entirely on who is listening, and here a stage engine was.

**The fix for those two is a surface, not a deletion.** Reading a product's docs
means something different once you own it: it is no longer evaluation, it is
onboarding. So an owned product's Docs tab reports `onboarding` and its
Integrations tab `migration`. The words were always right; nothing had ever said
them.

**The acceptance suite corrected a wrong first attempt, which is the more useful
part of this entry.** The initial fix deleted BP-006's document vocabulary as
unreachable — and Story 2, a binding acceptance journey, feeds `templates`,
`tasks` and `productivity` views directly. Deleting the clause broke it. Editing
Story 2 to avoid the vocabulary would have been adjusting a fixture to make an
assertion pass, which is the one forbidden move. The vocabulary is specified
behavior; the defect is the missing surface. So it stays, recorded as a ratchet
entry with what it actually needs: a capability meaning task or template
management, which is a catalog change and deliberately out of scope.

## Consequences

Adoption is reachable, proved behaviorally rather than by vocabulary
bookkeeping: a test buys a product and asserts the same two panes change what
they document. Sabotage-verified — forcing the ownership check to False reddens
it, and adding a topic no surface emits reddens the reverse check.

`ADOPTION_DOC_TOPICS` is named in the pack and consumed by three places that
previously each restated the words: the pattern, the stage milestone, and now
the surface. `BP007_DOC_TOPICS` loses `automation`; no test fed it, and nothing
observable changed.

The deviation list is a ratchet in the same shape as the domain-boundary one:
nothing may be added, and `test_no_stale_topic_deviations` fails if an entry
becomes emittable, so it can only shrink.

327 tests green. Doc 02 records the two-directional rule, the resolutions, and
the remaining entry.

**What this says about the earlier decisions.** #044, #045, #046 and #049 were
each a rule that described behavior the implementation did not produce. This one
is the inverse: a rule the implementation could not produce because no surface
spoke its vocabulary. The class is the same — a specification that agrees with
itself and not with the running system — and the general defense is a check in
both directions, which now exists for topics and does not yet exist for anything
else.

---

# Decision #053

## Title

Work Management gains capabilities of its own — closing the last unemittable topics

## Status

Accepted

## Decision

Three capabilities, append-only, in a new Work Management Capability Domain:
CAP-056 Task Management, CAP-057 Template Library, CAP-058 Workload Management.
Assigned to 31 catalog products, and mapped to the document topics BP-006
Productivity Evaluation reads. They participate in no Business Requirement.

## Rationale

Decision #052's reverse vocabulary check left three entries on its deviation
list: `productivity`, `templates`, `tasks`. All three belonged to BP-006, and all
three failed for one reason — **Work Management was a product category with 31
products and no capabilities of its own.**

The topic a tab reports is derived from the product's capabilities. Asana's
capability list was Messaging, File Sharing, Document Collaboration, Integration
Connectors, API Integration, so its documentation described itself as
`messaging`. A task tool could not say it was about tasks, because the catalog
had no word for that. BP-006 was listening for three words the marketplace was
structurally unable to speak.

That is the same defect as Decision #044, arriving through the capability catalog
rather than through a template: a rule that reads correct in the specification
and cannot fire in the product. It stayed invisible until the vocabulary check
ran in both directions, which is the argument for that check.

**Why three rather than one.** They are one coherent product space and they fail
together. Adding only Task Management would have left two entries on a list whose
whole purpose is to shrink to nothing.

**Why they participate in no requirement — the interesting constraint.** The
concept that would naturally feed one is BC-006 Productivity Evaluation, and it
maps Primary to REQ-005. Giving it a second Primary publishes a new requirement
inside Validation Scenario 2, whose published set (`{REQ-001, REQ-005}`) is
pinned — a shopper in that scenario would acquire a need the scenario does not
assert. Every product holding these capabilities is already reachable through
others, so the v1.1 failure of 82 unrecommendable products does not recur.
Wiring them into coverage means moving Scenario 2 deliberately, which is a
separate decision.

## Consequences

The deviation list is **empty**, and the ratchet keeps it there: a topic no
surface can emit fails the build, and an entry that becomes emittable must be
deleted.

Emitted now: `tasks` by 11 products, `templates` by 4, `productivity` by 16.
Asana, Todoist and Linear report `tasks`; Confluence reports `templates`;
Calendly reports `productivity`. A new seed test pins the general rule — every
Work Management product must hold a work-management capability and must document
itself in a word BP-006 reads — sabotage-verified by unassigning Asana's.

The canonical ten are untouched, so no acceptance number moves. 328 tests green.

**Operational note:** capability rows are added on start-up, but existing
databases keep their old product→capability assignments. The demo database needs
reseeding for these 31 products to gain the new capabilities; the automated tests
seed the canonical ten only and are unaffected.

**Still unmapped to any requirement:** CAP-009 File Sharing, CAP-024 AI Workflow
Assistance, and now these three. The first two sit inside frozen requirements'
domains; these three are blocked by Scenario 2. Four decisions have now been
constrained by pinned scenarios (#050, #051, #052, this one), which is the
mechanism working as designed — but it is worth noticing that the pins are
starting to shape the model, and a deliberate re-derivation of Scenario 2 would
unblock several of them at once.

---

# Decision #054

## Title

POL-CONF-002 identity is the *set* of supporting event types, not the multiset — superseding Decision #036

## Status

Accepted (supersedes Decision #036)

## Decision

"Repeated identical Evidence" is now identified by **pattern + strength + the
set of supporting event types**. A different strength, or a kind of event not
yet seen for that pattern, contributes at full class value. More events of kinds
already counted is the same finding restated and damps at `repeat_factor`.

Policy Catalog v1.4. This is the first change to how a published policy
*behaves* rather than to one of its numbers, so the version bump is what keeps
historical runs interpretable — every run records the `policy_version` it ran
under.

## Rationale

Found by reading the trace of a real journey (J-3, 12 minutes, 82 events) whose
shopper searched for analytics and DevOps tooling and was recommended
ServiceNow, a workflow-automation product they never opened. The product they
had put in their cart did not appear at all.

**The mechanism.** Session-window patterns re-report their *whole session* on
every workflow run. Under #036's multiset identity, each run's composition grew
by one event, so the identity key changed, so the damping never engaged.
Integration Evaluation fired eight times on nothing but Integrations-tab clicks
— Medium every time, never escalating — and climbed +0.10 per run to 0.80:

| Run | Events cited | Confidence |
|---|---|---|
| 1 | 2 | 0.10 |
| … | … | … |
| 8 | 11 | 0.80 |

That published Workflow Automation as a Critical requirement, and ServiceNow is
the one product in 250 that covers it completely. It won on 36% overall while
scoring zero on Engineering Delivery, the need the shopper actually had.

Across the whole journey, **1 of 41 evidence rows hit the damping rule.** A
policy that never fires is not a policy. Confidence was measuring how many times
the workflow happened to run, not how much evidence existed.

**Chapter 05 already said this.** Its Diminishing Returns section reads:
"Viewing the same pricing page twenty times should not increase confidence as
much as observing: Pricing, Documentation, API Reference, Security,
Integrations." That is set-of-kinds semantics stated in the constitution.
Decision #036 implemented the opposite, and no test caught it because the tests
were written from #036. Same family as Decisions #044, #045, #046, #049 and
#052 — a specification that agrees with itself but not with the running system —
and the most expensive instance so far, because this one lived in the core
arithmetic every hypothesis passes through.

**Why not identity-by-pattern-alone.** Still rejected, for exactly the reason
#036 gave: it caps a single-pattern concept near 0.4 (a geometric series of one
class contribution) and makes the Domain 09 confidences underivable. The set of
event *kinds* sits between the two failures — reachable, so the policy fires;
discriminating, so genuine escalation still pays.

## Consequences

**Every hypothesis confidence in the system moves.** On the journey that
prompted this, Integration Evaluation falls 0.80 → 0.20, which drops Workflow
Automation and Identity Management below the publication threshold and leaves
exactly the two requirements the shopper's behavior supports. Ranked over the
full catalog, the top two become Splunk and Datadog — the products they had in
their cart and on their comparison screen.

**Validation Scenario 1 was re-derived, deliberately.** Its pinned 0.80 / 0.70
were themselves produced by the ratchet: two of the five evidence rows behind
Security Evaluation were "same pattern, same strength, same kinds, just more of
them". Under the corrected rule the old clickstream yields 0.65, which drops
Identity Management out of Critical and pushes Regulatory Compliance below
publication — Okta / Microsoft 365 / Google Workspace would become 100 / 60 / 60,
a tie for second.

Rather than accept that, the scenario's **observed behavior** was rewritten so
the same confidences are earned by evidence that changes in kind: security pages,
then reading time, then a cross-product comparison sweep, then the product
documentation. Both concepts land exactly on 0.80 and 0.70, and every downstream
number — REQ-002 Critical, REQ-004 Medium, REQ-001 held at 0.48, Okta 81 /
Microsoft 365 70 / Google Workspace 58, READY — is unchanged.

This is recorded plainly because it deserves scrutiny: **reshaping a fixture to
preserve a number is adjacent to the one move this project forbids.** Three
things distinguish it. The scenario's *conclusions* were held fixed while its
*inputs* were re-derived, not the other way round. The replacement behavior is
more realistic than what it replaced, not less — a security buyer comparing four
platforms' security pages is ordinary, and the old clickstream's fifth repeat of
the same page was filler that existed to reach a number. And the constraint was
surfaced and decided explicitly rather than absorbed. The alternative — moving
81/70/58 — was offered and declined.

Validation Scenario 2 needed the same treatment for the same reason and got it:
its two sessions now take different routes through the evidence lattice, and
BC-005 0.80 / BC-006 0.50 / BC-003 0.50 are unchanged.

**Fixtures that reached a threshold by repetition no longer do**, which is the
policy working. Three platform fixtures (`_pump_requirements`, `_pump_focus`,
and Story 7's resumed session) were rebuilt to add a kind of evidence per run
instead of more of the same.

**Not addressed here.** The Integrations tab still emits a word that wakes
Integration Evaluation on 225 of 250 products; that is a Domain Pack vocabulary
defect and lands separately. Either fix alone corrects the journey above — this
one was chosen first because the other leaves the ratchet in place for the next
over-broad pattern.

---

# Decision #055

## Title

A pane with nothing to declare declares nothing — the Integrations tab stops asserting a capability the product lacks

## Status

Accepted

## Decision

The Integrations tab's tracked topic is derived from the product's own
capabilities with **no generic fallback**:

| Capability held | Topic emitted |
|---|---|
| CAP-016 Integration Connectors | `connectors` |
| CAP-019 API Integration | `api` *(new)* |
| CAP-003 SCIM Provisioning | `provisioning` |
| CAP-008 Identity Federation | `federation` |
| none of the above | **no topic** — the pane emits `DOCUMENTATION_VIEWED` carrying only the product |

`integrations` is removed from BP-008's vocabulary, leaving `{api, connectors}`
— the two words its own Strong clause is written around.

## Rationale

Second of the two defects behind the ServiceNow misrecommendation (Decision
#054 was the first). Either fix alone corrects that journey; this one removes
the false input rather than damping it.

**The tab was lying.** The topic a pane reports is derived from the product's
capabilities. When the derivation had no input it fell back to the word
`integrations` — which **153 of 250 products** hit, because they hold no
connective capability at all. Two clicks on that tab, the most ordinary thing a
shopper does, activated Integration Evaluation, which is Primary to Workflow
Automation and Secondary to Identity Management. One generic affordance minted
two requirements.

The prose on the very same pane already said the opposite: for these products
it reads "none of which are specifically connective — integration here will
mean a generic API or an intermediary rather than a purpose-built connector."
The page told the truth in words and the wrong thing in metadata.

This is Decision #053 inverted. There, a task tool could not say it was about
tasks because the catalog had no word for it. Here, a product with nothing to
integrate was made to claim integration, because a fallback existed. Both are
the topic derivation disagreeing with the product.

**Why not gate the evidence instead** (the Decision #049 move — require a
specific signal alongside the generic one). It would have worked, and it is
less code. It leaves the false claim in place: 153 product pages would still
report integration research to anything else that ever reads that stream. The
defect is in what the page says about the product, so that is where it is
fixed.

**Why not demote the mapping** (the Decision #050 move — BC-008 stops being
Primary to REQ-003). The concept is not wrong. In Validation Scenario 3 a
shopper reading API and connector documentation of automation products
genuinely is evaluating integration, and that scenario pins BC-008 Primary at
1.0×0.70. The evidence was wrong, not the meaning, and Scenario 3 is untouched.

**`api` becomes emittable for the first time.** 25 products hold API Integration
and no other connective capability; they previously fell through to the generic
word. The reverse vocabulary check (Decision #052) had not caught this because
`api` was structurally emittable as the Docs tab default — no product happened
to reach it. Structural reachability is weaker than actual reachability, which
is worth remembering the next time that check reports clean.

## Consequences

Verified against the journey that prompted it. Of the ten products that shopper
opened the Integrations tab on, nine now declare nothing and only GitHub — which
genuinely holds Integration Connectors — emits a signal. One signal; the pattern
needs two. Integration Evaluation never activates, so Workflow Automation and
Identity Management are never derived and ServiceNow is never ranked.

Declaring no topic is a deliberate narrowing of what the event *asserts*, not
of what is recorded: the read still fires a `DOCUMENTATION_VIEWED` carrying the
product, so it counts toward accumulation and stays available to any future
clause keyed on something other than topic. It simply makes no claim about
subject matter. `SECURITY_VIEWED` has always behaved this way — a security view
with no topic cannot contribute to Enterprise Evaluation — so this is an
existing convention applied, not a new one invented. Both vocabulary guards
were adjusted to treat a `None` default as "declares nothing" rather than as an
unread word.

### Amendment — emit without a topic, rather than not at all

As first written this decision dropped the event entirely for those 153
products. That was wrong in three ways, and the correction landed immediately
after: a shopper genuinely comparing integration fit across generic products
would have produced *no* signal at all (a false signal replaced by no signal is
not obviously better); those clicks are High-signal events that count toward
POL-TRIG-001, so reasoning would have fired less often on exactly those
journeys; and it would have left 61% of the catalog with no telemetry on that
tab for anything later.

Downstream was checked before the change: every consumer of `topic` already
guards — the pattern predicates via `.get()` (where `None in SET` is simply
False), `_entities` and the behavior summary via truthiness tests so no `None`
leaks into an entity set, and `track.js` via `JSON.parse(… || "{}")`. Ingest
validates the event type against the closed registry and does not check
metadata shape. The metadata convention in `patterns.py` was amended from
`DOCUMENTATION_VIEWED: {topic}` to `{product_id, topic?}` to match.

The catalog now splits 97 products that make a specific, true integration claim
against 153 that make none. `test_a_product_with_nothing_to_integrate_claims_no_integration_research`
and `test_browsing_two_unconnected_products_does_not_infer_an_integration_need`
pin both halves — the vocabulary and the pattern behaviour it drives.

---

# Decision #056

## Title

A session can carry more than one buying effort — intra-session intent forking

## Status

Accepted (amends Decision #041)

## Decision

Three changes, one behaviour:

1. **Journey ownership is decided once per settled block of events, not once
   per session.** A block below `fork_min_events` (5) inherits, exactly as a
   too-small session used to defer.
2. **Divergence is tested on subject-bearing concepts**, exported by the Domain
   Pack as `INTENT_CONCEPTS`. Two blocks belong to different efforts when both
   name a subject and share none. Returning to an earlier subject continues
   *that* journey — reactivating it if dormant — rather than opening a third.
3. **The v1.2 domain research patterns gain the multi-session clause** BP-004,
   BP-007 and BP-009 have carried since v1: recurrence across two sessions
   reaches Strong.

For You leads with the active journey and lists the others under "Also
exploring", named by requirement display names.

## Rationale

Reported from a live session: analytics and ETL research for six minutes, then
a deliberate switch to DevOps and CI/CD in the same session. The shopper
expected the recommendations to follow them. They did not.

**Data & Insight froze at 0.775 and never moved again** across five subsequent
runs of pure DevOps behavior. Nothing in the model represents "stopped caring":
confidence only rises, and browsing DevOps does not *contradict* analytics.
Evidence ageing is 30 days and hypothesis retirement needs confidence under
0.15 — both unreachable inside a fourteen-minute session.

The final profile put Data & Insight at Critical 0.85 (weight ×3) and
Engineering Delivery at Medium 0.57 (×1): **the abandoned intent outweighed the
current one three to one.** Worse, it was *promoted by* the new one — BC-023
maps Secondary to REQ-011, so the DevOps browsing pushed the analytics
requirement from 0.775 past the 0.8 Critical threshold. Switching subject made
the abandoned subject Critical.

The output followed: rank 1 Datadog, an overlap product; GitHub, which the
shopper had put in their cart and which covers Engineering Delivery completely,
scored 40% and was never retrieved.

**Why forking rather than decaying confidence.** Recency-weighted evidence and
a rolling pattern window were both considered. Both change the arithmetic every
pinned scenario depends on, and Decision #054 had just spent a full re-derivation
of Validation Scenarios 1 and 2 on exactly that. Forking touches no scenario —
none of them changes subject — and it reuses machinery that already exists.
It is also the more honest model: two subjects *are* two buying efforts, and
merging their Requirement Profiles was the actual error.

**Why concepts rather than entity similarity — measured, not assumed.** Entity
Jaccard was implemented and tested against two real sessions first. The
composite resolution score could not separate them: a genuine switch scored
0.470 and ordinary drift *inside* one subject scored 0.563, both under the 0.6
reuse threshold. Behavioural cosine is near-constant within a session (same
site, same event kinds) and time decay is 1.0, so 60% of the composite was
noise. Topic alone was tried at several window sizes; over short blocks it is
dominated by product ids, so a shopper comparing five analytics tools produced
false splits at every threshold that caught the real one. Concept divergence
separated both sessions cleanly with no threshold at all:

| Session | Fork point | Transition |
|---|---|---|
| Deliberate switch | the `cicd` search | Data & Insight → Engineering Delivery |
| Gradual drift | mid-session | Data & Insight → Engineering Delivery |

The concepts were already being computed for another purpose. Using a tuned
proxy for something the system knows exactly was the wrong instinct.

## Consequences

**Memory is kept, and kept out of the ranking.** The contamination was never
that the platform remembered analytics — it was that analytics memory sat
inside the DevOps ranking math at triple weight. Two journeys means two
Requirement Profiles and two rankings; nothing is forgotten and nothing blends.

**Returning resumes rather than restarts**, and now escalates: the multi-session
clause means coming back to a subject is itself evidence. Under Decision #054
alone, returning and re-reading the same material would have damped to nearly
nothing.

**A freshly forked journey has no ranking yet.** `_build_feed` returned nothing
in that state, which blanked For You at precisely the moment the shopper
changed subject — losing sight of the effort they had just left as well as the
one they started. It now renders the not-ready state alongside the other
journeys. Found by the acceptance test, not by review.

**Decision #041 is amended, not overturned.** Its finding stands: a two-event
session scores 0.438 against its own journey and forks wrongly. The error was
concluding that once-per-session was the only remedy; the remedy is not judging
a block too small to judge, which `fork_min_events` preserves.

**Not addressed.** POL-BEH-002 (evidence older than 30 days contributes at 50%)
still has no consumer in the code — a published policy nothing reads, and the
mechanism one would expect to handle long-run memory fade. Retrieval dilution
(the Finding 4 of this review series) is also untouched: journey B's ranking is
still capped by what retrieval returns for it.

---

# Decision #057

## Title

The intent fork tests abandonment, not divergence — Decision #056 could not fire on real behavior

## Status

Accepted (corrects Decision #056)

## Decision

A journey forks when its **established subject is absent from recent
activity**, sampled from disjoint slices: `established` is the dominant subject
of everything before a trailing window of `recent_window_events` (15), and
`recent` is whatever appears inside it.

This replaces #056's rule, which forked when a block of new events shared no
subject with the journey's whole history.

## Rationale

Reported, not reviewed: the shopper ran the switch test twice more after #056
shipped and saw one journey both times. The first report turned out to be a
stale server process; this one was a real defect, and the trace named it
exactly.

```
20:08:34  new=[Data & Insight, Engineering Delivery]  journey=[Data & Insight]         continue
20:11:31  new=[Engineering Delivery]  journey=[Data & Insight, Engineering Delivery]   continue
20:12:27  new=[Engineering Delivery]  journey=[Data & Insight, Engineering Delivery]   continue
```

**A change of subject always passes through a transitional block.** At 20:08
the shopper was still on analytics and starting on DevOps. #056's rule says an
overlap of one is continuity, so that block merged — correctly. But it merged
into a journey whose signature then held *both* subjects permanently, and every
later block of pure DevOps overlapped it. The fork became unreachable.

#056 passed its tests and one live session for the same wrong reason: both had
a clean pivot with no transitional block, so the workflow run happened to land
exactly on the switch. **It fired on luck, not on a rule.** The synthetic
clickstream was clean because it was written clean.

Two corrections, both found by measurement against three replayed sessions:

**Abandonment rather than divergence.** Asking "has the shopper stopped doing
what this journey was about" survives the transition; asking "does this block
share anything with the journey's history" cannot, because the history only
accumulates. This is the same failure shape as the cumulative comparison window
in Decision #054, and as the entity-Jaccard-against-all-prior measurement
rejected during #056 — the third instance in one working session of a growing
baseline destroying a signal.

**Disjoint slices.** The first attempt at the corrected rule still computed
dominance over the whole journey *including* the recent window. That fails
differently: pursue the new subject long enough and it becomes the dominant
one, so there is nothing left to abandon. Caught by an acceptance test whose
first phase was short — the fixture that was unrealistically small is the one
that exposed it.

## Consequences

All three replayed sessions now fork exactly once, at the right moment:

| Session | Fork | Transition |
|---|---|---|
| testcase0300 | 20:11:31 | Data & Insight → Engineering Delivery |
| testcase0126 | 18:37:56 | Data & Insight → Engineering Delivery |
| earlier analytics/DevOps | 16:46:01 | Data & Insight → Engineering Delivery |

Stable for `recent_window_events` anywhere between 10 and 20, which is the
evidence it reads a real signal rather than a tuned one.

**The transitional stretch stays with the original journey.** That is the right
place for it — the shopper genuinely was doing both — and it means the
abandoned journey holds a little evidence for the new subject. The acceptance
test asserts what actually matters instead of absence: the new journey carries
no trace of the old subject, and the old journey is still dominated by its own.

**Acceptance fixtures now use realistic volumes.** The fork needs a shopper who
has moved on, not one who glanced sideways, so a six-event switch no longer
triggers it — correctly. The earlier fixtures were small enough to pass under a
rule that could not work in production, which is the lesson of this entry: a
synthetic clickstream validates the code against itself; only a replayed one
validates it against the world.

---

# Decision #058

## Title

Catalog capability profiles must describe the product — and the discrimination guard was off by one

## Status

Accepted

## Decision

Three seed corrections and one guard correction:

| Product | Change | Why |
|---|---|---|
| Splunk | **+ Log Management** | it is a log management product |
| Linear | **− the five infrastructure capabilities** | an issue tracker runs no infrastructure |
| n8n | **− the five infrastructure capabilities** | a workflow tool runs no infrastructure |

`test_every_requirement_discriminates` now fails at `full >= top_k` rather than
`full > top_k`.

## Rationale

Noticed from a live ranking, not from review. A shopper on a DevOps journey got
CircleCI, New Relic and PagerDuty at 100% while Splunk sat at 80% — because the
catalog said Splunk has no Log Management. Splunk is the log management
product; the profile was simply wrong.

Correcting it exposed the same defect running the other way. **Linear and n8n
both fully covered Engineering Delivery**, claiming CI/CD Pipelines,
Infrastructure Monitoring, Log Management, Incident Response and Container
Orchestration. An issue tracker and a workflow automation tool run no
infrastructure between them. That is how a project-management product could
have out-ranked Datadog on a DevOps recommendation.

**The guard was off by one, and the Splunk fix walked straight into the gap.**
`test_every_requirement_discriminates` exists because a requirement covered
fully by more products than a Candidate Set can hold produces a list that is
entirely ties — "correct and useless". It compared `full > top_k`. Adding
Splunk took REQ-010 to exactly 8 against a Candidate Set of 8, where every
retrieved candidate can be a perfect-coverage tie: precisely the failure the
test names, and it stayed quiet. The boundary is `>=`.

With Linear and n8n corrected, REQ-010 is fully covered by 6 — GitHub,
CircleCI, New Relic, Splunk, PagerDuty, Docker Hub, all of them genuinely
DevOps products — which leaves the ranking something to discriminate on.

## Consequences

The demo database was updated through `save_product`, the sanctioned dual-write
path, so the vector index was re-embedded alongside the relational rows rather
than drifting from them (Core 20). All 250 products remain SYNCED.

**n8n now holds no Workflow Automation capability**, which is its own absurdity
and is left alone deliberately. Adding CAP-015 would give it all five of
REQ-003's capabilities, and `test_distractor_constraint_holds_for_scenario_requirements`
forbids a non-canonical product from fully covering a scenario requirement —
that rule protects ServiceNow as the canonical Workflow Automation winner in
Validation Scenario 3. The catalog cannot describe n8n honestly without moving
that scenario, so the tension is recorded rather than resolved.

**This is the second finding of the same kind** (Decision #053 added Work
Management capabilities so a task tool could say it was about tasks). The
generator drew capability sets from per-domain pools without checking them
against the product, so plausibility is not guaranteed anywhere in the catalog.
Three profiles are now known-correct; the rest have been checked only where a
ranking made them visible. A systematic pass is worth doing before the catalog
is treated as ground truth.

---

# Decision #059

## Title

The Behavioral Query Document describes the need, not the shopper — Finding 4, first half

## Status

Accepted

## Decision

Removed from the embedded query document: the `interest:` lines naming active
behavioral concepts, the `journey stage:` line, and the `query-template`
version marker. What remains is requirements with their capabilities, and the
shopper's recent search terms.

The template version moves to the Candidate Set's `params`, where it already
keyed the cache. Bumped to `qd-v2`, and the pipeline now references the
constant instead of repeating the literal.

## Rationale

Finding 4 of the trace review: a requirement at Critical 0.90 with seven
products covering it completely, and retrieval returned none of them. The
assumed cause was cross-requirement dilution — one embedding averaging five
requirements. Measurement said otherwise.

A journey that published a **single** requirement still retrieved badly:
distances across the whole 250-product catalog spanned 0.937 to 1.167, near
orthogonal to everything, with a Marketing product covering 0% ranking above
two products covering 100%. With one requirement there is nothing to dilute
across, so the dilution had to be *within* the document.

It was. The document carried eight `interest:` lines — Pricing Sensitivity,
Product Affinity, Decision Confidence, Adoption Readiness and so on — plus a
journey stage and a version marker. **A product Embedding Document contains
nothing any of those can match against.** They were pure noise competing with
the five capability lines that carried the meaning.

Measured on the live index, one requirement, same shopper:

| Query | Mean coverage | Perfect | Useless (0%) |
|---|---|---|---|
| As shipped | 60.0% | 3 | 2 |
| Without concepts + stage | 87.5% | 5 | 0 |
| Also without the version marker | 87.5% | 5 | 0 |

The marker deserves its own line in that story: reintroducing it alone dropped
the same query back to 67.5% with three perfect and one useless. **One line of
bookkeeping inside the embedded text cost twenty points of mean coverage.**

Keeping only the *subject-bearing* concepts was tested and made no difference —
the requirement they produced is already in the document, so they are a
restatement. The simpler document wins.

Recent activity stays: removing it was measured as slightly worse. It is the
shopper's own words about what they are looking for, which is exactly the kind
of thing product prose contains.

## Consequences

Both of the reported journeys now retrieve entirely on-category:

| Journey | Before | After |
|---|---|---|
| Engineering Delivery | 60.0% mean, 2 useless, a Marketing product at rank 5 | **87.5% mean, 5 perfect, 0 useless, all 8 DevOps** |
| Data & Insight | 42.5% mean, 1 useless | **47.5% mean, 0 useless, all 8 Data & Analytics** |

Data & Insight looks weak only because its ceiling is 60% — no product in the
catalog covers it (Finding 5, still open). It now returns five products *at*
that ceiling instead of Marketing and Productivity tools.

**The second half of Finding 4 is deliberately not built.** Per-requirement
retrieval — one query per requirement, merged — was measured and would lift
Engineering Delivery from 80% to 100% and Identity Management from 60% to 100%
on the old five-requirement journey. It costs one embedding call per
requirement instead of one per retrieval, a Candidate Set of 15 against a
policy that says 8, and a change to the POL-RETR-001 contract.

It is not built because **intent forking has largely dissolved the case for
it.** Since Decisions #056 and #057, journeys carry one subject and therefore
one or two requirements — both reported journeys published exactly one. The
five-requirement blend that motivated the idea was itself a symptom of merging
two buying efforts into one journey, and that is fixed at the source. Recorded
here so the measurement is not lost if multi-requirement journeys become common.

**GitHub is still not retrieved** despite covering Engineering Delivery
completely; it sits around rank 13. Its own Embedding Document spans nine
capabilities across DevOps and collaboration, so the dilution is now on the
*product* side rather than the query side. That is a different problem from
this one and is left open.

---

# Decision #060

## Title

Full coverage is computed, not retrieved — guaranteed candidates (POL-RETR-005)

## Status

Accepted

## Decision

After the bounded evaluate/refine loop, any product whose capabilities **fully
cover a published Requirement** is added to the Candidate Set if semantic
retrieval did not return it. At most `max_guaranteed` (4) per retrieval,
ordered by requirements covered, then capability count, then Product ID.

Guaranteed members carry `similarity: null` and `source: "guaranteed"`, and the
addition is recorded in the Candidate Set's refinement history as an explicit
`guarantee` action.

## Rationale

The product-side half of Finding 4. GitHub covers Engineering Delivery 5/5 and
sat around rank 13, outside a Candidate Set of 8, so it could not be
recommended however well it fit.

The cause is structural, not textual. GitHub's Embedding Document spans nine
capabilities across DevOps and Workflow Automation; its single vector is the
average of both, and averages sit further from a single-domain query than a
narrow product's vector does. Three document compositions were measured —
current, prose removed, capabilities only — and GitHub held rank 9 of 13 in all
three. Rewriting the document cannot fix it.

**The insight that settled the design is that we never needed retrieval for
this.** Coverage is a set comparison over the Requirement→Capability map: exact,
total over the catalog, and computable in microseconds. Semantic retrieval
answers a different and much harder question — which products *read* like a fit
— and it is the right instrument for that. Asking an embedding to rediscover
something already known exactly is strictly worse than looking it up.

So this is not a correction applied to retrieval's output, and not a fallback.
It supplies the answer retrieval was never the right instrument for, and leaves
fuzzy fit entirely to it. Only *full* coverage qualifies: judging partial fit is
retrieval's job and this does not encroach on it.

**Facet indexing was measured and rejected for now.** Indexing each product once
per capability domain lifts GitHub from rank 9 to 5 and separates off-domain
products cleanly (0.37–0.48 versus 0.67+). It is the better general answer and
remains the right eventual fix. It also changes Core 20's contract from one
Embedding Document per product to one per product-domain and requires
re-embedding the whole catalog — roughly 430 provider calls — which is not a
change to make late in a project when a smaller one is available. The
measurement is recorded so the option is not lost.

## Consequences

Verified against the live catalog. Engineering Delivery retrieves eight DevOps
products and GitHub is added, completing the set of six products that fully
cover it. Data & Insight adds nothing, correctly: no product covers it at all
(Finding 5, still open), so there is nothing to guarantee.

**It respects the dual-write contract, and did not at first.** The initial
implementation read capability rows straight from the relational store and
surfaced a product whose vector write had FAILED —
`test_story11_pending_product_never_surfaces` caught it. Reading the relational
store is what makes the guarantee exact, but it must not become a side door
around Core 20: the query now filters to SYNCED and undeleted products, the same
visibility `retrieve_candidates` enforces. Worth recording because the failure
mode is generic — any deterministic shortcut past the vector store inherits that
obligation.

**Guaranteed members are marked rather than disguised.** Giving them a
fabricated similarity would have misreported how they reached the Candidate Set,
and the Candidate Set is a Runtime Object that has to explain itself.

**The Candidate Set can now exceed POL-RETR-001's top_k**, by up to
`max_guaranteed`. That is a deliberate widening of what the Candidate Set is: a
top_k drawn by similarity, plus a bounded set drawn by exact coverage. Ranking
is unchanged and still decides the order.

---

# Decision #061

## Title

A requirement nothing can cover is as broken as one everything covers — Data & Insight restored to three capabilities

## Status

Accepted

## Decision

REQ-011 Data & Insight returns to the three Data & Analytics capabilities:
ETL Pipelines and Data Warehousing Primary, Data Visualization Secondary.
Intelligent Search and API Integration are removed.

The three capabilities are no longer assigned as a block. Twenty-one products
held all three; each is now restated as what it actually is, and connective and
AI capabilities they genuinely have were added in the same pass.

`test_every_requirement_is_coverable` pins the missing half of the invariant.

## Rationale

Finding 5 of the trace review. No product in 250 could cover Data & Insight —
the best was 4 of 5 — so the honest winner was capped at 80% and any
satisfiable requirement beat it. An analytics shopper's top recommendation was
Datadog, a DevOps monitoring tool, at 60%.

Self-inflicted, and recently. The requirement was drafted from the three
Data & Analytics capabilities, `test_every_requirement_discriminates` caught a
21-way tie at 100%, and two capabilities from other domains were added to break
it. The tie went away and a worse fault arrived in its place: **the guard
checked that a requirement was not too easy to cover and never checked that it
could be covered at all.**

**The tie was never about the requirement.** All 21 products held all three
capabilities because the catalog assigned the Data & Analytics domain as a
block. It said Tableau, Fivetran and BigQuery were the same product — eleven
products had that identical three-capability profile and nothing else. Adding
capabilities to the requirement was treating the symptom; the disease was that
the catalog could not tell a visualization tool from a pipeline tool.

Restated by what each product actually does:

| | |
|---|---|
| End-to-end platforms | Databricks, Snowflake — move it, store it, show it |
| Warehouse-first | BigQuery |
| Movement and transformation | Fivetran, Airbyte, Segment, dbt Cloud |
| Presentation | Tableau, Power BI, Looker Studio, Mode, Amplitude, Mixpanel |
| Dashboards only | Grafana, Datadog, Splunk |
| Not data platforms at all | Airtable, Smartsheet, Klaviyo, Semrush |

The last row matters most: a spreadsheet and an SEO tool were *fully covering*
"Data & Insight". That is the same defect as Decision #058's Linear and n8n
covering Engineering Delivery.

**Removing alone would have been worse.** The first pass stripped what products
did not do and left Tableau and Fivetran holding one capability each — accurate
and useless. The change only works because each product also gained the
connective and AI capabilities it genuinely has: connectors for the pipeline
tools, natural-language query for Tableau and Power BI, API integration
throughout.

## Consequences

Data & Insight is covered by exactly two products, Databricks and Snowflake,
against a Candidate Set of eight — satisfiable and discriminating. An analytics
journey now ranks Databricks, Snowflake, BigQuery, which is the answer a person
would give.

**The invariant gained its second half.** `test_every_requirement_discriminates`
forbids a requirement covered by more products than a Candidate Set can hold;
`test_every_requirement_is_coverable` now forbids one covered by none. Verified
by restoring the five-capability definition and watching it fail.

**Intelligent Search is no longer stranded.** It was borrowed into REQ-011
because no analytics product held it; Tableau and Power BI now do, on the
strength of Ask Data and Q&A, so the capability describes something real
instead of being a tie-breaker.

**Twenty-one products were re-embedded** through `save_product`, so the vector
index moved with the relational rows. All 250 remain SYNCED.

This is the third catalog-plausibility finding (#053 Work Management, #058
Splunk/Linear/n8n, this one). All three were found because a ranking made them
visible, never by inspection. The systematic audit is still outstanding and is
now clearly the highest-value remaining work on the catalog.

---

# Decision #062

## Title

Catalog audit, first pass: the DevOps domain, and a ratchet on cross-domain requirements

## Status

Accepted (audit continuing — see Consequences)

## Decision

Every DevOps capability assignment is restated by what the product actually is.
Seventeen products changed. `Shortcut` moves to Work Management capabilities,
`JumpCloud` and `Retool` stop claiming delivery infrastructure.

`test_no_requirement_quietly_borrows_another_domain` is added as a ratchet:
a requirement may draw on another capability domain only with a stated reason
in `CROSS_DOMAIN_REQUIREMENTS`. Entries may be removed, never added.

## Rationale

The audit began by looking for signatures rather than reading 250 products.
Two found every previous defect: capabilities from a domain unrelated to the
product's category, and identical profiles across products that are not alike.

**No capability domain is assigned as a block any more** — the worst remaining
is Security at 41%, and Data & Analytics fell to 6% after Decision #061. That
was the systemic fault and it is gone.

**Identical profiles are what remains.** Six clusters of real products share
byte-identical capability sets. The most damaging was in DevOps:

> CircleCI, Docker Hub, New Relic, PagerDuty — identical, all 5/5.

A CI service, a container registry, an observability platform and an on-call
tool, indistinguishable. Meanwhile **GitLab, the one product that genuinely is
an end-to-end DevOps platform, had no CI/CD at all**, JumpCloud (identity)
claimed CI/CD and monitoring, and Opsgenie (alerting) claimed CI/CD but not
Incident Response. The assignments were not merely optimistic; they were
unrelated to the products.

Restated: GitLab covers all five. Source-and-build tools hold CI/CD, runtimes
hold Container Orchestration, observability tools hold monitoring and logs,
on-call tools hold Incident Response. Each also keeps the connective surface it
genuinely ships — Jenkins' plugin ecosystem and CircleCI's orbs are real
integration marketplaces, and PagerDuty is event-driven by definition.

**Removing alone is not the fix, twice over.** The first pass here left
CircleCI, PagerDuty and Docker Hub holding one capability each — the same
mistake made in Decision #061 and repeated within an hour. Worse,
`test_every_capability_in_the_catalog_can_be_covered` then caught that Shortcut
had become unrecommendable: stripping its false DevOps claims left it with
nothing any requirement reaches. Accuracy that impoverishes the catalog is not
accuracy.

**The ratchet exists because the user identified a failure mode I had not
named.** Borrowing a capability from another domain to break a tie corrupts
retrieval as well as coverage: capability narratives enter the Behavioral Query
Document verbatim, so an automation sentence inside an analytics query pulls the
vector toward automation products. That is why a Marketing product once ranked
fifth in an analytics Candidate Set. Measured on REQ-012, whose borrowing is
principled, the effect is still visible — 4 of 8 retrieved products are
off-domain versus 2 with the Security capabilities alone — but its borrowing is
load-bearing and mild, so it is recorded rather than removed.

## Consequences

A DevOps journey now ranks GitLab 100%, Datadog 60%, New Relic 40%, PagerDuty
20% — differentiated, and in the order a person would give. Before, four
products tied at 100% and the winner was decided by Product ID.

**The coverage guarantee earned its place again.** Retrieval missed GitLab, and
POL-RETR-005 supplied it. Without Decision #060 this correction would have made
the catalog more honest and the recommendation no better.

**Five identical-profile clusters remain**, all lower-impact than DevOps:

| Cluster | Why it is wrong |
|---|---|
| Figma, Miro, GoTo Meeting, Webex | whiteboards and video conferencing are not the same product |
| Help Scout, Zendesk, Pipedrive | two support desks and a sales CRM |
| Brex, FreshBooks, QuickBooks Online | spend management and accounting |
| Make, n8n, PandaDoc | two automation platforms and a document-signature tool |
| Amplitude, Mixpanel, Looker Studio, Mode | product analytics and BI — mildest of the five |

Bitbucket, CircleCI and Jenkins now share a profile too, and that one is
allowed to stand: three hosted CI services with a public API and an integration
ecosystem genuinely are alike.

The audit is a pass per domain, not a single change. This entry covers DevOps;
the clusters above are the remaining work, in roughly that order of impact.

---

# Decision #063

## Title

Catalog audit, second pass: the remaining identical-profile clusters, and finance

## Status

Accepted (audit complete for real products)

## Decision

The five remaining identical-profile clusters are restated by what each product
is: whiteboards separated from video conferencing, a sales CRM from support
desks, spend management from accounting, an e-signature tool from automation
platforms, product analytics from BI. Twenty-four products changed in total.

The Finance and HR boundary is corrected in the same pass.

## Rationale

Each cluster was a capability domain copied wholesale onto every product in it.
Figma, Miro, GoTo Meeting and Webex all held Messaging, Video Meetings,
Document Collaboration and File Sharing — a design tool and a
video-conferencing product, indistinguishable. Zendesk, Help Scout and
Pipedrive all held the full CRM set, so a support desk claimed a sales
pipeline. Brex, QuickBooks and FreshBooks all held the full finance set.

**Two faults were found by the invariants, not by inspection**, which is the
whole argument for having them:

*Splitting CRM left REQ-006 with no coverer.* No product held all five CRM
capabilities once support and sales were separated.
`test_every_requirement_is_coverable` failed immediately. The honest fix was in
the catalog, not the requirement: HubSpot CRM lacked **Contact Management**,
which for a product that is fundamentally a contact database is a plain error.
Restoring it gives REQ-006 exactly one coverer, and it is the right one.

*Financial Management was won by a payroll product.* Gusto held all five
finance capabilities — invoicing, general ledger, budgeting — while NetSuite, a
full ERP, and QuickBooks Online, an accounting package, each fell one short.
Payroll runs payments and reimburses expenses; it does not keep your ledger.
NetSuite and QuickBooks now cover the requirement, and Gusto, Deel and Workday
hold the two finance capabilities payroll genuinely has.

**Removing without adding was avoided this time.** After two rounds of the same
mistake (#061 and #062), each product's adjacent capabilities were restored in
the same pass, and a check for products left under two capabilities now runs
before the change is accepted. Expensify briefly fell to one and was given back
reimbursement payments and its public API.

## Consequences

Every requirement is coverable and none is saturated. The winners are all
plausible: Okta for identity, ServiceNow for workflow automation, HubSpot for
CRM, NetSuite and QuickBooks for finance, GitLab for engineering delivery,
Snowflake and Databricks for data.

**Two identical profiles remain and are allowed to stand.** Bitbucket, CircleCI
and Jenkins really are three hosted CI services with a public API and an
integration ecosystem. Tableau, Power BI and Mode really are three BI tools with
natural-language query. Products that are genuinely alike should look alike; the
defect was never similarity, it was similarity between things that differ.

**Eleven pairs still share a profile**, which is left alone for the same reason
— at that scale it is indistinguishable from honest similarity, and forcing
difference would be inventing capabilities, which is the fault this audit
exists to remove.

**The fictional products were not audited.** They hold generated three-capability
sets by design and nobody can say they are wrong. If the catalog is ever cut to
real products only, that decision stands on its own merits and is recorded in
the session history rather than here.

---

# Decision #064

## Title

Catalog audit, third pass: fictional products in the wrong domain, at unchanged depth

## Status

Accepted (catalog audit complete)

## Decision

Forty-four fictional products held no capability from their own category's
domain and are re-drawn from it — at the **same depth**, and never taking a
domain's complete set. Their descriptions are regenerated from the new
capability list. Twelve further fictional products had descriptions that had
drifted from their capabilities since Decision #053; those are regenerated too.

## Rationale

A third of the fictional catalog was mislabelled rather than shallow. A
"Data & Analytics platform" whose capabilities were Intelligent Search,
Document Summarization and AI Workflow Assistance. A "CRM" with no CRM
capability. Six DevOps products that did nothing related to delivery. After the
real-product audit, exactly one real product had that fault; forty-four
fictional ones did.

**Depth was deliberately not changed.** The alternative considered was
reshaping the fictional set to match the real distribution — average 3.2
capabilities against 5.6, and no fictional product above six. It was rejected
on three grounds:

- **Coverage ranking rewards breadth, and the tie-break is total capability
  count.** A broadened distractor would tie a real product at 100% and then win
  the tie. "QuillWatch" above Datadog is a worse outcome than any realism gain.
- **Saturation.** Engineering Delivery has one full coverer and Data & Insight
  two; broadening 125 products would push several requirements past what a
  Candidate Set can hold, and the only remedy would be trimming them again.
- Doc 12 already says distractors get "deliberately partial capability sets so
  canonical winners remain deterministic". Shallow is the design.

The narrow fix raises plausibility without touching any of that: a three-
capability distractor still loses to Databricks, it simply stops claiming to be
something it is not.

**The saturation risk was not hypothetical.** The first attempt drew each
product a full-depth set from its own domain, which for the three-capability
domains meant the complete set — seven fictional analytics products then
covered Data & Insight completely and
`test_every_requirement_discriminates` failed at nine coverers. The rule that
fixes it is doc 12's own distractor constraint, generalised: **a fictional
product never holds a domain's complete capability set.**

**Descriptions had to move with the capabilities.** Fictional prose is
templated from the capability list — "X is a devops platform offering A, B, C."
Leaving it would have reproduced the GitHub defect from Decision #060, where a
description naming a subset of what a product holds pulls its embedding toward
the wrong half. Regenerating found twelve more products whose prose had drifted
when Decision #053 added Workload Management without regenerating them: a
pre-existing fault, found only because this pass compared the two.

## Consequences

No fictional product is in the wrong domain. Ninety-six distinct capability
profiles across 125 products, so they remain distractors rather than clones.
Every requirement is still coverable and none saturated.

Fifty-six products were re-embedded — the forty-four re-drawn, the twelve with
stale prose — so the vector index carries the corrected documents. All 250
SYNCED.

**The catalog audit is complete.** Real products across every domain (#062,
#063), and fictional products for domain placement (this entry). What remains
untouched by design: fictional capability *depth*, for the reasons above, and
the eleven real-product pairs that share a profile, where forcing difference
would mean inventing capabilities — the fault the audit existed to remove.

---

# Decision #065

## Title

Stage flapping: an evidence-free milestone arm, and a floor under regression

## Status

Accepted

## Decision

Two independent fixes to the Journey Stage Engine, both found by replaying one
live journey:

1. A milestone that offers an evidence-free arm is satisfied by that arm when
   its Evidence arm fails the POL-STAGE-001 threshold. Acquiring Evidence can
   no longer lower a stage.
2. A POL-STAGE-002 regression may only lower the journey's **recorded** stage.
   Where the regressed stage is not strictly earlier than the recorded one, no
   regression applies.

## Rationale

Journey `J-3` wrote eight stage versions in twelve minutes and moved backwards
in five of them. Its evidence only ever grew.

**The first fault is non-monotone by construction.** The Comparison milestone is
satisfied by a comparison-started event *or* by comparison-pattern evidence.
`_milestone_evidence` returned the pattern evidence whenever any existed, and
`determine_stage` then held that evidence to the ≥ 0.6 stage-confidence gate and
skipped the milestone when it failed — never reaching the event arm that had
been satisfying it a minute earlier. The journey fell from Comparison to
Awareness, five stages, *because it had learned something*. The two arms are not
alternatives and the engine was treating them as one.

**The second fault is a sliding window with no anchor.** POL-STAGE-002 reads the
journey's last three high-signal events. The milestone stage is recomputed from
cumulative evidence on every run, so a journey settled at Decision was regressed
afresh each time — and because the window slides, the target moved with it:
three documentation views regressed it to Technical Validation, three pricing
views to Commercial Evaluation, and it ping-ponged between the two four times in
nine minutes while its evidence never changed. Neither move was a shopper
backing off; documentation and pricing are what Decision-stage shoppers read.

The floor states what "regress" already means: you can only go back from
somewhere you have been. Recovery is unaffected — on the first run where the
trailing window is not uniformly earlier-stage, POL-STAGE-001 records the
milestone stage, which is exactly how `J-3` reached Decision at version 8.

**This was not cosmetic.** Stage gates the Critical priority band (POL-REQ-002),
which carries triple weight in coverage ranking (POL-REC-002), so the
requirement profile and the product order churned on every flap.

## Consequences

`J-3`'s history becomes four monotone records instead of eight with five
backwards moves. Genuine regression is untouched and still pinned by Story 8:
three consecutive Discovery-characteristic events after an evaluation stage
regress the journey, and `test_regression_still_fires_on_a_genuine_step_back`
exists so the fix cannot degrade into "regression never fires".

`apply_regression` takes the recorded stage as a second argument — the engine
stays pure, and the orchestration reads the stored stage before deciding rather
than after.

---

# Decision #066

## Title

Low-signal events are stamped processed; signal class gates triggering, not consumption

## Status

Accepted

## Decision

A completed workflow run stamps `processed_at` on **every** event it consumed,
not only the high/medium-signal slice. The trigger gates continue to count
high/medium events alone.

## Rationale

Ninety-five events in the demo database sat at `processed_at IS NULL`, every one
of them a dwell heartbeat, going back to the first session ever recorded. One
query built the trigger-gate count *and* the stamp list, and it filtered to
`signal_class IN ('HIGH','MEDIUM')` — correct for the gate, wrong for the stamp.
`data-model.md` defines the field as "set when behavioral reasoning consumed
it", and dwell is consumed: BP-001 sums security dwell to reach Strong.

**The leak is not bookkeeping.** Journey ownership for a run is the journey of
the newest *unprocessed* event. Once every high/medium event is stamped, the
only pending events are heartbeats — so any trigger carrying no condition of its
own resolves the run to whichever journey last had a dwell. SCHEDULED, the daily
digest, is exactly such a trigger. For a shopper who has forked (#057), that is
the subject they walked away from: two of the six live demo users were in that
state, one of them with three journeys, pointing at the wrong one.

**The two uses of signal class are genuinely different**, which is why they now
read from different lists rather than one filtered query. Core 22: "signal class
is domain knowledge consumed by Execution Triggers." It says what may *start* a
run — Law 9's no-AI-call-per-raw-event, and heartbeats must never count toward
POL-TRIG-001 or a shopper sitting still would trigger runs forever. It says
nothing about what reasoning read. Conflating the two is what produced a
distinction the code could not hold.

## Consequences

No event survives a completed run unprocessed, and the pending set is bounded by
what has arrived since the last run rather than by the age of the database.

A SCHEDULED run for a user with no new activity now resolves no journey and is
SKIPPED, where before it silently reasoned about a heartbeat's journey. The
digest is unaffected: it reads the latest Recommendation Package for the user's
newest journey, which the accumulation runs already keep current.

`test_dwell_heartbeats_alone_never_trigger_a_run` pins the half of the
distinction nothing was guarding — six heartbeats, twice POL-TRIG-001's
threshold, must not start a run. It was written because sabotaging the gate to
count every pending event left all 363 tests green.

---

# Decision #067

## Title

POL-BEH-002 acquires a consumer: evidence ages out of full weight

## Status

Accepted

## Decision

The Confidence Engine applies POL-BEH-002 — evidence older than the policy's
window contributes at half weight. `EvidenceInput` carries `age_days`, measured
by the orchestration at scoring time against `evidence.created_at`.

## Rationale

POL-BEH-002 has been in the Policy Catalog and in `config/policies.yaml` since
v1 with both its numbers, and nothing read either of them. A published policy
that no code consumes is worse than an absent one: it is a promise the system
does not keep, and Law 4 exists to make the catalog the single place a
behavioural number lives — which only holds if the engines actually read it.

The behaviour it was written for is real here. Journeys survive dormancy for
weeks (POL-JRES-002), and a returning shopper resumes the journey they left
rather than starting a new one (#057). Without ageing, a belief formed in one
session counts at full strength however long ago that session was, so a
requirement derived from a month-old security evaluation outranks one derived
from yesterday's.

**Age and repetition are kept independent.** POL-CONF-002 damps a finding
restated; POL-BEH-002 damps a finding grown old. The damping chain records what
the finding was worth before ageing, so the second reading of a month-old
finding is halved once for each rule rather than quartered by either standing in
for the other.

**Measured at scoring time, not at insert.** Ageing is a property of the
question "what is this worth now", so a dormant journey is re-scored on its
evidence's present value every time it runs. Stamping a weight at insert would
freeze it at the moment the evidence was written, which is the one moment the
policy is never asking about.

## Consequences

Nothing changes for a journey scored within the window — the acceptance
derivations in `docs/domains/software-buying/09` all sit inside one session, and
Story 1's 0.80 / 0.70 are untouched.

The wiring is pinned separately from the arithmetic. Sabotaging the orchestration
to hand the engine a constant age left all 368 tests green, so
`test_the_pipeline_measures_evidence_age_at_scoring_time` scores one journey at
two clock positions and requires the later one to be lower.

**One knob is still unread**: `cumulative_dwell_seconds` on the Product Affinity
pattern. Unlike POL-BEH-002 it is Domain Pack data rather than a platform
policy, and the pattern's Strong bar is written in qualifying events; it is
recorded here rather than fixed silently.

---

# Decision #068

## Title

Real-product prose that still described the pre-audit product

## Status

Accepted

## Decision

Fifty-one real products whose `description`, `business_purpose` or
`business_value_narrative` named a capability the product does not hold have
that prose regenerated from their actual capability list.
`test_no_product_prose_claims_a_capability_it_does_not_hold` becomes a ratchet
over the whole catalog.

## Rationale

Found by opening the catalog page in a browser. The cards were self-refuting:
"CircleCI is a devops platform offering CI/CD Pipelines, Infrastructure
Monitoring, Log Management, Incident Response, Container Orchestration"
directly above "3 capabilities". CircleCI holds Integration Connectors, API
Integration and CI/CD Pipelines. Four of the five named were false.

**This is the GitHub defect of Decision #060, fifty-one times over.**
Decisions #058 and #061–#063 restated capability assignments across the real
catalog and never regenerated the prose that is generated *from* them.
Decision #064 caught it for the fictional half — and the entry even says the
prose "is templated from the capability list" and that leaving it "would have
reproduced the GitHub defect" — while the real half, which the same three
decisions had just rewritten, went unchecked. The audit verified the data it had
changed and not the text describing it.

**It reaches retrieval, not just the reader.** `embedding_document` composes
name, vendor, category, description and business_purpose, then one narrative
line per capability held. A description naming a capability the product lacks
therefore injects that capability's language with no capability line behind it:
pure signal for a claim nothing supports. That is why three DevOps products that
hold one relevant capability each were crowding a Candidate Set.

**And it reaches the words.** The narrative is passed to Tier 1 as the
product's grounding, so a false claim there is Law 11 — persuasive copy built on
a capability the product does not have.

**Only false claims are fixed, not omissions.** Fourteen untouched products
name *fewer* capabilities than they hold, because #063 restored capabilities
without extending the prose. Omission is survivable: every held capability
reaches the vector through its own narrative line regardless of the description.
An invented one has no such line. The generator was first required to reproduce
untouched prose byte-for-byte and could not — the original wording follows no
ordering this repository can regenerate — so the pass was narrowed to products
whose prose is actually false rather than rewriting prose that is merely
partial.

## Consequences

Engineering Delivery retrieval now returns GitLab at 5/5 coverage in second
place, with the three products that had been claiming the whole delivery surface
sitting at 1/5. All 250 products re-embedded through `save_product`, all SYNCED.

The ratchet scans all three prose fields case-insensitively and subtracts the
product's own category first: two categories share a name with a capability
("Workflow Automation", "Compliance"), and every description states its
category, so a naive scan fails exactly the automation products that the
distractor constraint deliberately keeps off that capability (#058).

**The lesson is about the shape of the check, not the data.** Three audit
passes verified capability assignments against each other and never once asked
whether the sentences describing them still held. A catalog invariant that reads
only structured fields cannot see prose drift, and prose is half of what the
index is built from.

---

# Decision #069

## Title

Seeding is convergent and runs every startup; the catalog no longer freezes at first boot

## Status

Accepted

## Decision

`seed_canonical_products` and `seed_demo_catalog` compare each seed entry with
its stored row and write only what differs. Startup calls both unconditionally
rather than only when the products table is empty.

## Rationale

`seed_demo_catalog` began each product with `if db.get(...) is not None:
continue`, and startup ran it only `if db.query(models.Product).count() == 0`.
Together those meant **a demo database that had booted once never took another
catalog edit** — not on restart, not ever.

Demonstrated rather than deduced: writing a sentinel description into
`seed/products.json` and running the seeder against the live demo database
reported "inserted: 0" and left the stored description untouched.

This is why three passes of catalog audit — #062, #063, #064 — each needed a
hand-written re-embed script to reach the running demo, and why Decision #068's
prose fix needed a fourth. Four ad-hoc scripts is not four accidents; it is the
seeding path telling us it did not work, four times, and being answered with a
workaround each time. The catalog audit's whole premise was that
`seed/products.json` is the source of truth, and for a booted database it was
not.

**The skip existed for a real reason and is kept.** Re-saving 250 products on
every boot spends one embedding call each against the configured provider. The
fix is to skip on *equality* rather than on *existence*: `product_matches_seed`
compares the caller's fields and the capability set, so an unchanged catalog
still costs nothing. Measured on the live database: a one-product edit wrote
exactly one product, and a second pass wrote none.

**Fields are the caller's, not the function's.** The canonical roster carries no
`business_value_narrative`; comparing a field the caller does not supply would
make all ten canonical products look stale on every boot and re-embed them
forever. A stored NULL and an absent key both read as "nothing here" for the
same reason.

**Unsynced rows are never skipped**, whatever their fields say: a product whose
vector write failed is PENDING or FAILED and must be re-attempted, which is what
`reconcile_pending` is for and what an equality check alone would defeat.

## Consequences

Editing `seed/products.json` and restarting is now sufficient to move the demo
catalog. No re-embed script is needed, and the four written so far are
superseded.

The predicate is pure and tested directly, so the 240-product catalog stays out
of the automated tests as fixture separation requires.

**What this says about the previous four decisions.** Their *data* was correct —
the store and index were verified against the seed file each time. What was
wrong is that verification depended on remembering to run a script, and a
correctness property that depends on remembering is not a property. The audit
kept finding drift because the mechanism that was supposed to prevent it had
been switched off since the first boot.

---

# Decision #070

## Title

The ADK wrapper enforces the halt itself instead of asking the framework to

## Status

Accepted

## Decision

`StageAgent` records a halt in the workflow state it owns and checks that state
before running any node. `ctx.end_invocation` is still set, as the
framework-native signal, but nothing depends on it.

## Rationale

Found by watching a live browser session: a `FAILED` workflow run 0.4 seconds
before a healthy one, with `KeyError: 'journey_id'` at the node *after*
`resolve_journey`.

`resolve_journey` returns False when there is no journey to reason about, and
the graph must stop. The plain executor obeys the return value. The ADK wrapper
set `ctx.end_invocation = True` and trusted `SequentialAgent` to act on it —
which this version does not do between sub-agents, so the next node ran anyway
and dereferenced the journey id it had just been told did not exist.

**The state it fails in is routine, not rare.** POL-TRIG-001 fires a run at 3
unprocessed events; POL-JRES-001 does not settle a session's ownership until 5.
Every new session of a shopper who already owns a journey passes through that
window. What should be an ordinary SKIP was a FAILED run each time.

**This is the framework seam failing at the one thing it exists to guarantee.**
Core 21 and `stack-decisions.md` both say the wrapper only supplies sequencing —
swapping ADK for LangGraph changes no engine, contract, or Runtime Object. A
wrapper that can only *request* a halt does not bind the graph contract; it
delegates it to a third party whose behaviour is a version detail. Enforcing it
in state we own makes the contract ours again, and the same three lines will
carry to LangGraph unchanged.

## Consequences

`test_adk_halts_the_graph_when_there_is_no_journey_to_reason_about` reproduces
the live failure exactly — the same KeyError, at the same node — and now passes
as a SKIP.

**The existing ADK test only ever walked the happy path**, which is why a
framework divergence survived: it asserted that a *completed* run through ADK
matches the plain executor and never asked what an incomplete one does. Where
two implementations must agree, the cases worth pinning are the ones where one
of them stops early.

The deprecation warning already visible in the suite — `SequentialAgent is
deprecated in favor of Workflow` — is the same version drift seen from the other
side, and is now recorded rather than merely printed.

---

# Decision #071

## Title

For-You follows the shopper, and reports the run that produced what it shows

## Status

Accepted

## Decision

The default journey on For-You is the one owning the shopper's most recent
event, not the most recently created journey. The panel's `trigger` line is
scoped to the journey being displayed. `_build_feed` returns the journey it
chose.

## Rationale

Seen live: a Decision-stage journey with 83 events and a READY ranking sat under
"Also exploring" while an Awareness stub, untouched for three hours, held the
main panel and asked the shopper clarifying questions about a subject they had
left.

The page ordered journeys by `created_at`. That agrees with the workflow on a
fresh fork — the journey the shopper moved to is the newest — and disagrees the
moment a **new session resumes an older journey**, which is exactly what
POL-JRES-001's candidate scoring is for. The workflow filed the events there and
reasoned about it; the page kept leading with the newest one. Two components
answering "which journey is the shopper in?" with different rules is the defect;
using the events' own answer makes them agree by construction.

The `trigger` line took the user's most recent completed run *regardless of
journey*, so a package from one journey was labelled with another journey's
trigger — the header contradicting the body directly beneath it.

## Consequences

**The first version of the test passed vacuously.** It asserted on the journey
*label*, and both journeys in the fixture label as "Just started" — the
assertion could not fail. `_build_feed` now returns `journey_id` and the test
asserts on that, which is also the honest thing for the function to expose.

Product order is pinned separately: `test_for_you_renders_entries_in_rank_order`
asserts on the *built feed* rather than the stored package, so it covers the
persistence round-trip and the view assembly — the two places a reorder could
creep in between POL-REC-002 and the shopper. Ranks must render as a clean 1..N
and coverage must not rise down the list. Verified against the live account:
both journeys' packages render in rank order with coverage non-increasing.

**A stale package is not a stale ranking.** The engineering journey still shows
a pre-audit ordering because Recommendation Packages are insert-only Runtime
Objects and that journey has not run since the catalog was corrected. The
arithmetic was right over the data it had; the data is what changed. It will
re-rank on that journey's next run — and against the corrected catalog the same
requirement now returns GitLab at 5/5 where those three sit at 1/5.
