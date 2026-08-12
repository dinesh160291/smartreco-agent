# Behavioral Patterns

**Version:** 1.0

---

# Purpose

Behavioral Patterns define how observable user interactions are transformed into deterministic Behavioral Evidence.

Patterns represent reusable deterministic reasoning rules that connect raw Behavioral Events to higher-level behavioral concepts defined by the Behavioral Ontology.

The Behavioral Intelligence Platform evaluates these patterns continuously as user behavior evolves.

Behavioral Patterns are domain-specific.

They teach the platform how software-buying behavior manifests through observable interactions.

---

# Guiding Principle

Behavioral Events describe **what happened**.

Behavioral Patterns describe **what those events mean within the Software Buying Domain**.

Patterns generate Behavioral Evidence.

Patterns never generate Behavioral Hypotheses.

Patterns never create recommendations.

The Behavioral Intelligence Platform consumes Behavioral Evidence to produce Behavioral Hypotheses.

---

# Separation of Responsibilities

Behavioral Events

↓

Immutable observable facts

↓

No interpretation

↓

----------------------------

Behavioral Patterns

↓

Deterministic interpretation rules

↓

Generate Behavioral Evidence

↓

No Runtime Objects

↓

----------------------------

Behavioral Ontology

↓

Defines behavioral concepts

↓

Static domain knowledge

↓

----------------------------

Behavioral Intelligence Platform

↓

Evaluates patterns

↓

Produces Behavioral Hypotheses

↓

Calculates Confidence

↓

Maintains Behavioral Memory

↓

Produces Requirement Profiles

↓

Determines Journey Stage

↓

Supports AI-generated explanations

---

# Pattern Definition

Every Behavioral Pattern must contain the following sections.

## Pattern Name

A unique identifier.

---

## Intent

Describes the user behavior this pattern attempts to recognize.

---

## Required Evidence

Defines the minimum Behavioral Events required for the pattern to activate.

---

## Optional Supporting Evidence

Defines additional observations that strengthen the generated Behavioral Evidence.

---

## Contradicting Evidence

Defines observable behavior that weakens the generated Behavioral Evidence.

Contradicting evidence does not directly change Behavioral Hypothesis confidence.

Confidence is determined later by the Confidence Engine.

---

## Behavioral Evidence Produced

Defines the deterministic Behavioral Evidence produced when the pattern activates.

Patterns produce Behavioral Evidence only.

They never produce Behavioral Hypotheses.

---

## Confidence Contribution

Defines how strongly the generated Behavioral Evidence may contribute toward Behavioral Hypotheses.

Patterns never assign final confidence.

The Confidence Engine determines Behavioral Hypothesis confidence.

---

## Possible User Requirements

Defines the Requirement types commonly associated with the generated Behavioral Evidence.

These mappings represent domain knowledge only.

The Requirement Engine determines which Requirements apply to an individual user.

---

## Possible Journey Stages

Defines the Journey Stages where this pattern most frequently appears.

Journey Stage determination is performed by the Journey Stage Engine.

Patterns do not determine Journey Stage.

---

## Example Journey

Illustrates a representative behavioral sequence demonstrating the pattern.

Examples are explanatory only.

They are not executable logic.

---

# Pattern Categories

The Software Buying Domain currently defines five categories of Behavioral Patterns.

## 1. Discovery Patterns

Examples include:

- Product Discovery
- Category Exploration
- Brand Exploration

---

## 2. Evaluation Patterns

Examples include:

- Technical Evaluation
- Feature Evaluation
- Security Evaluation
- Integration Evaluation
- Documentation Evaluation

---

## 3. Commercial Patterns

Examples include:

- Pricing Evaluation
- Cost Comparison
- Trial Evaluation
- ROI Evaluation

---

## 4. Decision Patterns

Examples include:

- Preference Reinforcement
- Preference Reversal
- Decision Confidence
- Purchase Readiness

---

## 5. Adoption Patterns

Examples include:

- Team Expansion
- Enterprise Rollout
- Onboarding Readiness

---

# Pattern Lifecycle

Behavioral Events

↓

Behavioral Pattern Evaluation

↓

Behavioral Evidence

↓

Behavioral Hypotheses

↓

Behavioral Memory

↓

Requirement Profile

↓

Journey Stage

↓

Recommendation Package

Patterns never modify Runtime Objects directly.

Patterns never modify Behavioral Memory.

Patterns only produce Behavioral Evidence.

The Behavioral Intelligence Platform owns all Runtime Objects and behavioral state.

---

# Pattern Invariants

The following rules must always hold.

## Invariant 1

Behavioral Patterns are deterministic.

Identical Behavioral Events must always produce identical Behavioral Evidence.

---

## Invariant 2

Behavioral Patterns never invoke AI or an LLM.

All pattern evaluation is deterministic.

---

## Invariant 3

Behavioral Patterns produce Behavioral Evidence only.

They never produce:

- Behavioral Hypotheses
- Requirement Profiles
- Journey Stages
- Recommendation Packages

Those Runtime Objects are produced by the Behavioral Intelligence Platform.

---

## Invariant 4

Behavioral Patterns never own user state.

They never store:

- Behavioral Memory
- Confidence
- Session state
- Journey state
- Runtime Objects

---

## Invariant 5

Behavioral Patterns are reusable across all users, sessions, and journeys.

They represent domain knowledge only.

---

## Invariant 6

Behavioral Patterns may evolve through new Domain Pack versions without requiring architectural changes to the Behavioral Intelligence Platform.

---

# Claude Implementation Contract

Claude MUST:

- Implement every Behavioral Pattern as deterministic logic.
- Ensure identical Behavioral Events always produce identical Behavioral Evidence.
- Keep Behavioral Pattern execution independent from AI reasoning.
- Keep Behavioral Patterns independent from Runtime Objects.
- Support deterministic replay of historical Behavioral Events.
- Preserve clear separation between domain knowledge and runtime reasoning.

Claude MUST NOT:

- Store Runtime Objects inside Behavioral Patterns.
- Store Behavioral Memory.
- Store confidence values.
- Invoke AI during Behavioral Pattern evaluation.
- Generate Behavioral Hypotheses.
- Generate Requirement Profiles.
- Generate Journey Stages.
- Generate Recommendation Packages.
- Modify historical Behavioral Events.
- Modify Decision Policies.

---

# Canonical Behavioral Patterns

The following patterns are the canonical v1 pattern set of the Software Buying Domain.

Conventions:

- Event Types and their metadata are defined by the Event Schema (core 13) and the tracking contract (core 22). Topic metadata (e.g., a documentation page's topic) is carried in Event Metadata.
- Unless stated otherwise, activation windows are **session-scoped**; window sizes and counts are Decision Policy values and the numbers below are their v1 defaults.
- Patterns whose conditions span sessions (e.g., "across ≥ 2 sessions") evaluate over the **active Journey's full event history** — journey-scoped lookback, never across journeys. Evidence recency weighting per POL-BEH-002 applies within that scope.
- Every pattern names the Behavioral Concept(s) its Evidence supports, by registry ID (01 — Behavioral Ontology).
- Evidence Strength stated per activation level; the Confidence Engine converts strength into Hypothesis confidence per POL-CONF-001.

---

## BP-001 — Security Evaluation

**Intent:** The user is validating security posture.

**Required Evidence:** ≥ 2 SECURITY_VIEWED events on distinct pages, or 1 SECURITY_VIEWED + 1 DOCUMENTATION_VIEWED with topic = security/SSO/MFA, within a session.

**Optional Supporting:** DWELL ≥ 60s on security pages; SEARCH with security terms.

**Contradicting:** Sustained activity exclusively on non-security content in subsequent sessions.

**Produces:** Evidence type *Security Evaluation* — Strength Medium (minimum activation), Strong (≥ 4 qualifying events or supporting dwell).

**Supports Concepts:** BC-001 Security Evaluation.

**Possible Requirements:** REQ-002 Identity Management, REQ-001 Secure Collaboration, REQ-004 Regulatory Compliance.

**Possible Journey Stages:** Research, Technical Validation.

**Example:** Search "SSO project management" → product page → security page → SSO docs (90s dwell).

---

## BP-002 — Enterprise Evaluation

**Intent:** The user is evaluating for organizational (not personal) adoption.

**Required Evidence:** ≥ 2 events among: DOCUMENTATION_VIEWED topic = admin/provisioning/federation, PRICING_VIEWED on enterprise tier, SECURITY_VIEWED topic = compliance/audit, within a session — **at least one of which must be an administration page** (topic = admin/provisioning/federation).

**Why the administration signal is required (Decision #049):** this pattern maps Primary to REQ-002 Identity Management, on doc 06's rationale that *"organizational adoption hinges first on centralized identity"*. Only the administration evidence carries that meaning. Every product in the catalog has an enterprise tier and a compliance posture page, so those two signals alone state that the buyer is a company — not what the company needs. Without this clause a shopper comparing four CRM products on their Enterprise plans published an Identity Management need at 0.55, which halved every CRM's coverage and promoted a product scoring 0% on the actual need. Pricing behaviour is read by BP-009 Commercial Evaluation, which is where it belongs.

**Optional Supporting:** COMPARISON_STARTED between enterprise products; DEMO_REQUESTED.

**Contradicting:** Repeated PRICING_VIEWED on individual/free tiers.

**Produces:** *Enterprise Evaluation* — Strength Medium; Strong with ≥ 3 qualifying events across ≥ 2 sessions.

**Supports Concepts:** BC-002 Enterprise Evaluation.

**Possible Requirements:** REQ-004 Regulatory Compliance (Secondary), and only in combination with other evidence. This pattern publishes no requirement on its own — see doc 06 and Decision #050: it establishes that the buyer is an organization, which informs stage and framing rather than naming a need.

**Possible Journey Stages:** Research, Technical Validation, Commercial Evaluation.

**Example:** Enterprise pricing → admin docs → SCIM provisioning docs.

**Counter-example (does not activate):** Enterprise pricing on four different CRM products. Four qualifying events, no administration page — company size, not an identity need.

---

## BP-003 — AI Evaluation

**Intent:** The user is exploring AI-assisted capabilities.

**Required Evidence:** ≥ 2 events among: DOCUMENTATION_VIEWED topic = AI, PRODUCT_VIEWED where the product's category is AI-focused, SEARCH containing AI terms, within a session.

**Optional Supporting:** DWELL ≥ 60s on AI feature pages; COMPARISON_STARTED filtered to AI capabilities.

**Contradicting:** None specific; absence weakens via decay only.

**Produces:** *AI Evaluation* — Strength Medium; Strong with ≥ 4 qualifying events.

**Supports Concepts:** BC-003 AI Evaluation.

**Possible Requirements:** REQ-005 AI Assistance, REQ-003 Workflow Automation.

**Possible Journey Stages:** Discovery, Research.

**Example:** Search "AI meeting summaries" → AI feature page → AI docs.

---

## BP-004 — Compliance Evaluation

**Intent:** The user is validating governance and regulatory fit.

**Required Evidence:** ≥ 2 events among: DOCUMENTATION_VIEWED topic = compliance/audit/retention/eDiscovery, SECURITY_VIEWED topic = certifications (SOC2, ISO), within a session.

**Optional Supporting:** SEARCH with compliance terms; DWELL ≥ 60s on compliance pages.

**Contradicting:** None specific.

**Produces:** *Compliance Evaluation* — Strength Medium; Strong with qualifying events across ≥ 2 sessions.

**Supports Concepts:** BC-004 Compliance Evaluation.

**Possible Requirements:** REQ-004, REQ-002.

**Possible Journey Stages:** Research, Technical Validation.

**Example:** SOC2 page → audit logging docs → data retention docs.

---

## BP-005 — Collaboration Evaluation

**Intent:** The user is evaluating team communication and co-work capability.

**Required Evidence:** ≥ 2 events among: PRODUCT_VIEWED in a collaboration category, DOCUMENTATION_VIEWED topic = messaging/meetings/co-editing, CATEGORY_VIEWED = collaboration, within a session.

**Optional Supporting:** COMPARISON_STARTED between collaboration products.

**Contradicting:** None specific.

**Produces:** *Collaboration Evaluation* — Strength Medium; Strong with ≥ 4 qualifying events.

**Supports Concepts:** BC-005 Collaboration Evaluation; co-supports BC-006 Productivity Evaluation when productivity topics co-occur.

**Possible Requirements:** REQ-001 Secure Collaboration.

**Possible Journey Stages:** Discovery, Research, Comparison.

**Example:** Collaboration category → two product pages → co-editing docs.

---

## BP-006 — Productivity Evaluation

**Intent:** The user seeks efficiency and output improvements.

**Required Evidence:** ≥ 2 events among: DOCUMENTATION_VIEWED topic = productivity/templates/tasks, SEARCH with productivity terms, PRODUCT_VIEWED in productivity categories, within a session.

**Optional Supporting:** AI-topic co-occurrence (strengthens BP-003 concurrently).

**Contradicting:** None specific.

**Produces:** *Productivity Evaluation* — Strength Weak (minimum), Medium (≥ 3 events).

**Supports Concepts:** BC-006 Productivity Evaluation.

**Possible Requirements:** REQ-005, REQ-003.

**Possible Journey Stages:** Discovery, Research.

**Example:** Search "team task automation" → productivity suite page → templates docs.

---

## BP-007 — Automation Evaluation

**Intent:** The user is evaluating workflow/process automation.

**Required Evidence:** ≥ 2 events among: DOCUMENTATION_VIEWED topic = workflows/automation/triggers, PRODUCT_VIEWED in an automation category, SEARCH with automation terms, within a session.

**Optional Supporting:** DWELL ≥ 60s on workflow-builder pages; DOCUMENTATION_VIEWED topic = business rules.

**Contradicting:** None specific.

**Produces:** *Automation Evaluation* — Strength Medium; Strong with ≥ 4 qualifying events or multi-session recurrence.

**Supports Concepts:** BC-007 Automation Evaluation.

**Possible Requirements:** REQ-003 Workflow Automation.

**Possible Journey Stages:** Research, Technical Validation.

**Example:** Search "automate approvals" → automation product → event-trigger docs.

---

## BP-008 — Integration Evaluation

**Intent:** The user is validating fit with an existing stack.

**Required Evidence:** ≥ 2 DOCUMENTATION_VIEWED events with topic = integrations/API/connectors, within a session.

**Optional Supporting:** SEARCH naming a specific system ("Salesforce integration"); DWELL ≥ 60s on API reference.

**Contradicting:** None specific.

**Produces:** *Integration Evaluation* — Strength Medium; Strong when API reference and connector pages both appear.

**Supports Concepts:** BC-008 Integration Evaluation; co-supports BC-009 Technical Evaluation.

**Possible Requirements:** REQ-003, REQ-002.

**Possible Journey Stages:** Technical Validation.

**Example:** Integrations directory → API reference (long dwell) → webhook docs.

---

## BP-009 — Commercial Evaluation

**Intent:** The user is evaluating cost and commercial viability.

**Required Evidence:** ≥ 2 PRICING_VIEWED events (any products), or 1 PRICING_VIEWED + 1 COMPARISON_STARTED, within a session.

**Optional Supporting:** Repeat PRICING_VIEWED on the same product across sessions (also feeds BP-010); SEARCH with pricing terms.

**Contradicting:** None specific.

**Produces:** *Commercial Evaluation* — Strength Medium; Strong with pricing views across ≥ 2 sessions.

**Supports Concepts:** BC-010 Commercial Evaluation; repeated same-tier focus co-supports BC-014 Pricing Sensitivity.

**Possible Requirements:** Priced-plan fit (informs Recommendation Constraints: Budget Unknown when absent).

**Possible Journey Stages:** Comparison, Commercial Evaluation.

**Example:** Product A pricing → Product B pricing → comparison view.

---

## BP-010 — Product Affinity

**Intent:** The user is converging on a specific product.

**Required Evidence:** ≥ 3 PRODUCT_VIEWED events for the same product across ≥ 2 sessions, or ≥ 2 same-product views + 1 same-product PRICING_VIEWED.

**Optional Supporting:** DWELL ≥ 120s cumulative on the product; RECOMMENDATION_CLICKED for the product.

**Contradicting:** COMPARISON_STARTED introducing new alternatives after affinity formed; sustained views of a competitor (feeds BC-018 Preference Reversal in a future pattern version).

**Produces:** *Product Affinity* (product-scoped) — Strength Medium; Strong at ≥ 5 qualifying events.

**Supports Concepts:** BC-012 Product Affinity; sustained affinity co-supports BC-016 Decision Confidence.

**Possible Requirements:** None directly — affinity informs ranking context, never requirements.

**Possible Journey Stages:** Comparison, Decision.

**Example:** Product page (3 visits, 2 days) → pricing → docs, all same product.

---

## BP-011 — Adoption Readiness

**Intent:** The user is preparing to act.

**Required Evidence:** 1 of: TRIAL_STARTED, DEMO_REQUESTED, ADD_TO_CART, CHECKOUT_STARTED, PURCHASE_COMPLETED.

**Optional Supporting:** DOCUMENTATION_VIEWED topic = onboarding/migration within the same session.

**Contradicting:** No product activity for a sustained period after trial start; cart abandoned across ≥ 2 sessions.

**Produces:** *Adoption Readiness* (product-scoped) — Strength Strong (trial/demo/cart), Very Strong (CHECKOUT_STARTED or PURCHASE_COMPLETED). PURCHASE_COMPLETED additionally triggers journey closure per POL-JRES-003.

**Supports Concepts:** BC-015 Adoption Readiness; co-supports BC-016 Decision Confidence.

**Possible Requirements:** None new — signals stage progression.

**Possible Journey Stages:** Decision, Adoption.

**Example:** Pricing → Start free trial → onboarding guide.

---

## BP-012 — Product Discovery

**Intent:** The user is exploring the space without a formed target.

**Required Evidence:** ≥ 3 events among CATEGORY_VIEWED, SEARCH, PRODUCT_VIEWED spanning ≥ 2 distinct products or categories, within a session, with no single product exceeding 2 views.

**Optional Supporting:** Broad, short dwells.

**Contradicting:** Concentration on one product (BP-010 takes over).

**Produces:** *Product Discovery* — Strength Weak; Medium at ≥ 5 qualifying events.

**Supports Concepts:** BC-011 Product Discovery.

**Possible Requirements:** None yet — discovery precedes requirement formation.

**Possible Journey Stages:** Awareness, Discovery.

**Example:** Search "project tools" → category page → three different product pages.

---

## Clauses not implemented in v1

Every **Required Evidence** and **Produces** rule above is implemented and tested. Five clauses are not, and are listed here so a reader can tell a deliberate omission from a defect — the distinction this section exists to make. Adding any of them is a normal change; discovering by accident that the pack promised something the platform never did is not.

**Contradicting evidence — 2 of 4 implemented.** Enterprise Evaluation (repeated individual/free-tier pricing views) and Product Affinity (a comparison introducing alternatives after affinity formed) subtract confidence per POL-CONF-003. Two are not implemented:

| Pattern | Unimplemented clause | Why deferred |
|---|---|---|
| BP-001 Security Evaluation | *Sustained activity exclusively on non-security content in subsequent sessions* | Needs a definition of "sustained" and a journey-wide absence check; absence is already handled generally by decay (POL-DECAY-001), so the marginal value is small. |
| BP-011 Adoption Readiness | *No product activity after trial start; cart abandoned across ≥ 2 sessions* | Overlaps journey dormancy and the trial-adoption fallback (POL-JRES-002/003), which already act on the same silence. Implementing both risks penalising one shopper twice for one behaviour. |

**Optional Supporting dwell — 1 of 4 implemented.** `DWELL ≥ 60s` is read only by Security Evaluation, where it also promotes strength. BP-003, BP-004, BP-007 and BP-008 list it as supporting evidence, which is lineage rather than confidence: supporting events appear in an Evidence object's trail and change no score. None of those surfaces runs a dwell heartbeat (Decision #045), so the events do not exist to attach.

Reading time promotes strength in **exactly one pattern**, and that asymmetry is deliberate — see Decision #045. Security interest can only be shown on a product's single security page, so four qualifying events means visiting four products, and reading one closely deserves an alternative route. Patterns qualifying on several event kinds reach four without help.

---

## Pattern Set Evolution

Patterns for BC-013 Feature Evaluation, BC-009 Technical Evaluation (standalone), BC-014 Pricing Sensitivity (standalone), BC-016 Decision Confidence (standalone), BC-017 Preference Reinforcement, and BC-018 Preference Reversal are planned for Domain Pack v1.1, following this same template. Their concepts are already co-supported by the v1 patterns noted above.

---