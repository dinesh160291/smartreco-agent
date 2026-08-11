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
