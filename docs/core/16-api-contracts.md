# API Contracts

**Version:** 1.0

---

# Purpose

The API Contracts define the canonical interfaces exposed by the Behavioral Intelligence Platform.

API Contracts standardize how external systems interact with the platform.

API Contracts define communication.

They never define platform behavior.

They never define business policy.

They never perform deterministic reasoning.

Their sole responsibility is exposing stable, versioned platform contracts.

---

# Guiding Principle

APIs expose platform capabilities.

Platform engines perform deterministic reasoning.

Decision Policies authorize deterministic actions.

The AI Buying Advisor communicates deterministic outcomes.

The API layer orchestrates communication.

It never performs platform reasoning.

---

# Core Principle

Client

↓

API Contract

↓

Request Validation

↓

Authorization

↓

Decision Policy Evaluation

↓

Platform Engine

↓

Response Envelope

↓

Client

API Contracts expose deterministic platform capabilities through stable interfaces.

---

# Responsibilities

The API layer is responsible for:

- Receiving requests.
- Validating requests.
- Authenticating requests.
- Authorizing requests.
- Routing requests to platform components.
- Returning standardized responses.
- Preserving API compatibility.
- Supporting API versioning.

The API layer never:

- Performs behavioral reasoning.
- Performs capability matching.
- Evaluates Recommendation Readiness.
- Performs AI communication.
- Invokes platform engines directly without validation.

Its sole responsibility is exposing stable platform interfaces.

---

# API Categories

## 1. Authentication & Account APIs

Purpose

Establish identity and role.

Examples

- POST /auth/register — email/password registration
- POST /auth/login — session establishment
- POST /auth/logout

Two roles exist: **user** (browses, is tracked, receives recommendations) and **admin** (manages the product catalog). Role checks are enforced at this layer for every admin route. Authentication is deliberately simple (email/password, server-side sessions); it verifies identity and role, nothing more.

---

## 2. Behavioral Event APIs

Purpose

Receive Behavioral Events in batches.

Examples

- POST /events/batch

The batch contract (accept-fast 202, idempotent by client Event ID, structural validation only) is defined in Chapter 22. Behavioral Events enter the platform through the Event Schema before Journey Resolution begins.

---

## 3. Admin Product APIs

Purpose

Runtime management of product records (admin role required).

Examples

- POST /admin/products — create (triggers dual-write)
- PUT /admin/products/{productId} — update (triggers dual-write)
- DELETE /admin/products/{productId} — delete (triggers dual-write removal)
- GET /admin/products — list with sync status

Every mutation follows the dual-write contract (Chapter 20). Responses include `sync_status` so admins can observe synchronization. Capability IDs are validated against the active Domain Pack taxonomy; unknown capabilities are rejected.

---

## 4. Journey APIs

Purpose

Expose Journey information.

Examples

- GET /journeys/{journeyId}
- GET /users/{userId}/journeys

Journey APIs expose immutable Journey Runtime Objects.

---

## 5. Recommendation APIs

Purpose

Serve and (via triggers) generate deterministic recommendations.

Examples

- GET /recommendations/feed — the user-facing feed: latest stored AAR + Recommendation Package for the authenticated user (serves cached artifacts; never triggers generation inline)
- POST /recommendations — explicit generation request, subject to Execution Triggers and budgets (Chapter 23)

Returns

- Recommendation Package (and associated AAR when available)

Recommendation APIs expose deterministic recommendation artifacts.

---

## 6. AI Advisory APIs

Purpose

Generate AI communication.

Examples

- POST /advisor

Returns

- AI Advisory Response (AAR)

AI Advisory APIs never modify deterministic platform outputs.

---

## 7. Replay APIs

Purpose

Replay deterministic platform reasoning.

Examples

- POST /replay

Inputs

- Journey ID
- Runtime Object Versions
- Policy Versions

Outputs

- Deterministic Replay Results

Replay uses historical runtime object versions together with historical Decision Policy versions.

---

## 8. Observability APIs

Purpose

Expose operational diagnostics.

Examples

- GET /decision-trace/{journeyId}
- GET /policy-evaluations/{journeyId}
- GET /engine-executions/{journeyId}

Observability APIs expose immutable platform diagnostics.

---

## 9. Marketplace APIs

Purpose

Cart and checkout for the marketplace surface.

Examples

- GET /cart · POST /cart/items · DELETE /cart/items/{productId}
- POST /checkout — validates card **format only**, always succeeds, records an Order; no real payment processing exists anywhere in the platform
- GET /orders

Checkout completion emits PURCHASE_COMPLETED through the standard event pipeline — commerce actions are behavioral events like any other, and journey closure follows POL-JRES-003. The checkout surface is explicitly labeled as a demonstration flow.

---

# Request Processing

Every request follows the same deterministic pipeline.

Client Request

↓

Request Validation

↓

Authentication

↓

Authorization

↓

Decision Policy Evaluation

↓

Platform Component

↓

Response Envelope

↓

Client

Requests never bypass validation.

Requests never bypass authorization.

Requests never bypass Decision Policy evaluation when applicable.

---

# Request Validation

Every request validates:

- API Version
- Request Schema
- Required Fields
- Authentication
- Authorization
- Supported Enumerations

Validation verifies structural correctness.

Validation never performs behavioral reasoning.

Invalid requests are rejected before reaching platform components.

---

# Response Envelope

Every API returns a canonical Response Envelope.

Every Response Envelope contains:

- Request ID
- Correlation ID
- API Version
- Timestamp
- Status
- Payload
- Errors
- Warnings
- Metadata

Responses are strongly typed.

Response schemas are versioned.

The Payload contains immutable Runtime Objects or immutable platform artifacts.

---

# Error Handling

API errors are deterministic.

Errors communicate validation failures, authorization failures, or deterministic platform outcomes.

Examples include:

- INVALID_EVENT_SCHEMA
- INVALID_REQUEST
- INVALID_POLICY
- JOURNEY_NOT_FOUND
- RECOMMENDATION_NOT_READY
- INVALID_CAPABILITY
- POLICY_EVALUATION_FAILED

Error codes are defined through Platform Enumerations.

Errors are strongly typed.

Errors are versioned.

---

# API Versioning

Every API Contract is independently versioned.

API versioning supports:

- Backward compatibility
- Platform evolution
- Client compatibility
- Contract stability

API versions are independent of:

- Runtime Object Versions
- Decision Policy Versions
- Prompt Versions
- Platform Releases

Historical API versions remain available according to the platform's compatibility strategy.

---

# Authentication & Authorization

API Contracts define authentication and authorization requirements.

Implementation details remain outside the scope of this specification.

Examples include:

- Authentication
- Authorization
- Tenant Isolation
- Role-Based Access Control (RBAC)
- Service-to-Service Authentication

Authentication verifies identity.

Authorization verifies permissions.

Neither performs deterministic platform reasoning.

---

# Relationship to Decision Policies

The API layer never evaluates Decision Policies.

When a request requires policy evaluation, the API layer routes the request to the appropriate platform component.

Platform components evaluate Decision Policies.

The API layer returns the resulting deterministic platform artifact.

Business policy remains external to the API layer.

---

# Relationship to the Platform

The API layer is the external interface to the Behavioral Intelligence Platform.

The API layer:

- Receives requests.
- Validates requests.
- Routes requests.
- Returns standardized responses.

The API layer never:

- Performs behavioral reasoning.
- Performs recommendation logic.
- Modifies Runtime Objects.
- Invokes AI directly.

Platform engines remain isolated from client applications.

Clients communicate exclusively through API Contracts.

---

# Interaction with Platform Components

Client

↓

API Contract

↓

Validation

↓

Platform Component

↓

Immutable Runtime Object

↓

Response Envelope

↓

Client

The API layer exposes platform capabilities.

It never exposes platform implementation.

---

# API Invariants

## Invariant 1

APIs expose contracts.

They never expose platform internals.

---

## Invariant 2

All requests are validated.

---

## Invariant 3

All responses use the canonical Response Envelope.

---

## Invariant 4

API Contracts are versioned.

---

## Invariant 5

APIs exchange strongly typed contracts.

---

## Invariant 6

APIs never expose mutable Runtime Objects.

---

## Invariant 7

The API layer never performs deterministic reasoning.

---

## Invariant 8

The API layer never modifies platform state.

---

## Invariant 9

API Contracts remain independent of platform implementation.

---

# Design Principles

The API Contracts follow these architectural principles.

## Principle 1

API Contracts expose platform capabilities.

---

## Principle 2

Platform implementation remains internal.

---

## Principle 3

API Contracts are stable and versioned.

---

## Principle 4

Requests are validated before platform execution.

---

## Principle 5

The API layer orchestrates communication.

It never performs deterministic reasoning.

---

## Principle 6

Platform components remain independently evolvable behind stable contracts.

---

# Claude Implementation Contract

Claude MUST:

- Respect API Contracts.
- Respect request schemas.
- Respect response schemas.
- Respect API versions.
- Respect Response Envelopes.
- Preserve contract compatibility.

Claude MUST NOT:

- Invent request fields.
- Invent response fields.
- Bypass validation.
- Modify Runtime Objects.
- Expose internal platform implementation.
- Override API Contracts.

---

# Relationship to Core Documentation

This chapter defines the external communication contracts for the Behavioral Intelligence Platform.

Related chapters include:

| Chapter | Responsibility |
|---------|----------------|
| 11 | Observability and Evaluation |
| 12 | Journey Resolution Engine |
| 13 | Event Schema |
| 15 | LLM Contract |
| 17 | Platform Enumerations |
| 99 | Architecture Principles |

---

# Summary

API Contracts define the canonical interfaces exposed by the Behavioral Intelligence Platform.

They provide stable, versioned, strongly typed contracts for external systems.

The API layer validates requests, routes them to the appropriate platform components, and returns standardized responses.

It never performs behavioral reasoning.

It never evaluates business policy.

It never modifies platform state.

Its sole responsibility is exposing deterministic platform capabilities through stable external interfaces.

---
