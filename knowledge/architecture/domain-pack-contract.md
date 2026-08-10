# Domain Pack Contract

**Status:** Binding — this is the interface between the platform and any domain.

---

# Purpose

`domain-governance.md` defines *how* domain knowledge evolves — lifecycle, review, versioning. This document defines *what a domain must supply* to run on the platform, in a form an implementing agent can work through directly.

The platform is domain-agnostic by design: the engines, orchestration, retrieval mechanism, tracking, triggers, caching and delivery are identical whether the marketplace sells software, travel experiences, or event tickets. **Only the Domain Pack changes.** This contract is the list of what changes.

If you are standing up a new domain, every artifact below is required unless marked optional. If you are extending the existing one, this is the map of what you are allowed to touch.

---

# Guiding Principle

> The platform knows **how to reason**. The Domain Pack knows **what the reasoning is about**.

A capability, a behavioral pattern, a journey stage and an event type are all statements about a *domain*. Confidence arithmetic, noisy-OR derivation, coverage ranking, debounce and cooldown are statements about a *platform*. When those get mixed, a second domain cannot be added without editing the engine — which is the failure this contract exists to prevent.

---

# The Required Artifacts

Each row is one thing a Domain Pack must provide. "Consumed by" names the platform component that reads it, so a change can be traced forward.

| # | Artifact | Shape | Consumed by |
|---|---|---|---|
| 1 | **Behavioral Concepts** | `{concept_id: display_name}` — what a user might be trying to do | Behavioral Reasoning Engine (Core 19) |
| 2 | **Behavioral Patterns** | activation conditions → strength → concepts supported/contradicted | BRE (Core 19); evidence per Core 03 |
| 3 | **Business Requirements** | `{req_id: display_name}` — what a user needs | Requirement Engine (Core 06) |
| 4 | **Capabilities** | `(id, name, domain, business-value narrative)` | Recommendation Engine (Core 08), Retrieval (Core 20) |
| 5 | **Concept → Requirement mapping** | `{concept: {requirement: Primary\|Secondary\|Supporting}}` | POL-REQ-003 noisy-OR derivation |
| 6 | **Requirement → Capability mapping** | `{requirement: [capability, …]}` | Coverage and ranking (POL-REC-002) |
| 7 | **Event Types** | `{event_type: HIGH\|MEDIUM\|LOW}` — a **closed** registry | Ingestion (Core 22), trigger evaluator (Core 23) |
| 8 | **Journey Stages** | ordered stage names + qualification milestones | Stage Engine (Core 07), POL-STAGE-001/002 |
| 9 | **Product roster** | canonical fixture products with capability profiles | Acceptance tests; the derivation scenarios |
| 10 | **Buyer shorthand** *(optional)* | `{acronym: expansion}` | Catalog search (ui-design-spec §4.7a) |
| 11 | **UI vocabulary** | product-detail tab set, per-tab tracked topics, display copy | Reference deployment templates |
| 12 | **Derivation scenarios** | worked arithmetic with exact expected numbers | Acceptance tests — the platform's proof of determinism |
| 13 | **Acceptance stories** | end-to-end journeys with expected outcomes | Acceptance tests |

**Artifacts 12 and 13 are not optional and not documentation.** They are how anyone knows the port succeeded. A domain without exact expected numbers cannot demonstrate that its reasoning is deterministic, which is the platform's central claim.

---

# What the Domain Pack May **Not** Contain

- **Thresholds.** Every number lives in `config/policies.yaml` mirroring Policy Catalog v1 (Core 10). A Domain Pack that hardcodes `0.6` has taken a decision that belongs to the operator.
- **Runtime logic.** Reference knowledge only — no orchestration, no I/O, no calls.
- **Platform enumerations.** Lifecycle states, sync statuses, evidence strengths, trigger types and readiness values are Core 17's, identical across domains.
- **AI prompts.** Prompt versions belong to the Prompt Library (Core 15). A domain supplies facts; it does not supply persuasion.

---

# What the Platform Guarantees in Return

Supply the thirteen artifacts and the following work unchanged, with no engine edits:

Journey resolution · behavioral reasoning · confidence scoring · requirement derivation · stage progression and regression · semantic retrieval with the bounded evaluate/refine loop · deterministic coverage and ranking · the readiness gate · grounded AI narrative · triggers, debounce, cooldown, budgets and caching · dual-write and reconciliation · tracking and batching · proactive digest delivery · the Reasoning Panel.

---

# Porting Checklist

1. Copy the pack structure; keep the numbered file convention so cross-references stay stable.
2. Define concepts (1), then patterns (2) — patterns reference concepts, not the reverse.
3. Define requirements (3) and capabilities (4), then the two mappings (5, 6). Governance Law 3: relationships live in mappings, never inside the objects they relate.
4. Declare the closed event registry (7) and the stage model (8). Both are domain-shaped: a travel journey is not an eight-stage software evaluation.
5. Author the product roster (9) and, if the vocabulary needs it, shorthand (10).
6. Supply UI vocabulary (11) — the reference deployment renders a product page, but *which tabs* and *what each one documents* is yours.
7. Write the derivation scenarios (12) **before** implementing, and the acceptance stories (13) alongside. They are the specification of correct behaviour, not a report on it.
8. Point `policies.yaml` at your thresholds and record `policy_version`.
9. Run the boundary test (`tests/test_domain_boundary.py`) — it fails if domain identifiers have leaked into platform code.

---

# Tracing a Change

Because every artifact names its consumer, a domain change can be followed forward: adding a capability touches (4), the requirement mapping (6), the product roster (9), and the expected numbers in (12). Adding an event type touches (7) and any pattern in (2) that keys on it.

If a change appears to require editing an engine, that is the signal that either the change belongs in the Domain Pack in a different shape, or the platform has a genuine gap — the latter is a Core change with a decision-log entry, never a quiet edit.

---

# Conformance

The reference implementation satisfies this contract. `tests/test_domain_boundary.py` enforces it: no platform module or reusable document may hardcode a Domain Pack identifier, the pack must supply every contracted artifact, and the import seam must still exist.

One permanent exception is recorded there — `docs/core/decision-log.md` names domain identifiers in historical entries. Rewriting past decisions to satisfy a later rule would falsify the record, so those stay.

The test is a ratchet: an entry that stops leaking must be removed, so the exception list can only shrink.
