# Reference Behavioral Journey Scenarios

**Version:** 1.0

---

# Purpose

The Reference Behavioral Journey Scenarios document demonstrates how the Software Buying Domain produces deterministic, traceable, and explainable recommendations from observed customer behavior.

This chapter introduces no new domain concepts.

It validates the concepts, relationships, and Runtime Objects defined throughout the Software Buying Domain Pack using canonical reference scenarios.

Reference Behavioral Journey Scenarios are implementation references.

They are not Runtime Objects.

They are not reference knowledge.

They do not define recommendation logic.

They do not introduce new Behavioral Concepts.

They do not introduce new Business Requirements.

They do not introduce new Capabilities.

They do not introduce new Product Capability Profiles.

Instead, they demonstrate how existing domain knowledge is traversed during runtime to produce deterministic Recommendation Packages.

---

# Guiding Principle

The Software Buying Domain is designed to produce deterministic recommendations.

Given the same:

- Observed Behavior
- Behavioral Evidence
- Behavioral Hypotheses
- Behavioral Memory
- Domain Pack
- Product Capability Profiles

the platform must always produce the same:

- Requirement Profile
- Capability Coverage Analysis
- Recommendation Package

Reference Behavioral Journey Scenarios demonstrate that deterministic behavior.

They do not define new architecture.

They validate the existing architecture.

---

# Validation Framework

Every Reference Behavioral Journey follows the same deterministic execution path.

No scenario introduces new domain knowledge.

No scenario bypasses the defined architecture.

Every recommendation must be traceable from observed customer behavior through to the final Recommendation Package.

Every Runtime Object references existing canonical objects.

Every recommendation follows the architectural principle:

Reference, don't duplicate.

---

# Master Validation Flow

Every Reference Behavioral Journey follows the same validation flow.

```text
Observed Behavior

↓

Behavioral Evidence

↓

Behavioral Hypotheses

↓

Behavioral Concepts

↓

Behavioral Concept → Business Requirement Mapping

↓

Requirement Profile

↓

Business Requirement → Capability Mapping

↓

Required Capabilities

↓

Product Capability Profiles Evaluated

↓

Capability Coverage Analysis

↓

Recommendation Package

↓

AI Buying Advisor
```

This validation flow is identical for every Reference Behavioral Journey.

Only the inputs change.

The architecture remains constant.

---

# Why This Validation Exists

The Software Buying Domain defines:

- Behavioral Concepts
- Business Requirements
- Capabilities
- Product Capability Profiles
- Canonical mappings
- Runtime contracts

This chapter demonstrates how those components work together during runtime.

It validates the integrity of the complete Software Buying Domain.

It provides implementation guidance without introducing new architectural concepts.

It serves as:

- Implementation reference
- Testing reference
- AI prompt reference
- Documentation reference

---

# Scope

This document defines:

- Canonical validation scenarios
- End-to-end behavioral journeys
- Runtime traceability
- Deterministic recommendation validation
- Recommendation traceability
- AI explanation validation

This document does not define:

- New Behavioral Concepts
- New Business Requirements
- New Capabilities
- New Product Capability Profiles
- Recommendation algorithms
- Decision Policies
- Runtime engine implementation
- AI prompting strategies
- New Runtime Objects

---

# Validation Template

Every Reference Behavioral Journey follows the same validation structure.

The validation structure is identical for every scenario.

Only the customer inputs change.

The architecture remains unchanged.

Every Reference Behavioral Journey contains the following sections.

---

## 1. Customer Context

Provides a concise description of the customer's business situation.

Customer Context establishes the starting point for the validation scenario.

It provides business background only.

It does not contain Behavioral Evidence.

Example:

```text
Organization Size

Enterprise

Industry

Financial Services

Current Environment

Multiple identity providers

Business Goal

Standardize identity management across the organization
```

---

## 2. Observed Behavior

Records observable customer actions.

Observed Behavior contains objective observations.

It never contains interpretations.

Example:

```text
Customer compares identity platforms.

Customer requests Single Sign-On capabilities.

Customer asks about Multi-Factor Authentication.

Customer evaluates centralized user provisioning.
```

---

## 3. Behavioral Evidence

Behavioral Evidence captures the observable signals extracted from customer behavior.

Behavioral Evidence is a Runtime Object.

It references Behavioral Evidence defined earlier in the Software Buying Domain.

Example:

```text
BE-001

Customer compares multiple identity platforms.

BE-004

Customer requests enterprise authentication capabilities.
```

---

## 4. Behavioral Hypotheses

Behavioral Hypotheses represent deterministic interpretations of the observed Behavioral Evidence.

Behavioral Hypotheses are Runtime Objects.

They activate one or more Behavioral Concepts.

Example:

```text
Hypothesis

Customer is evaluating enterprise identity management capabilities.
```

---

## 5. Activated Behavioral Concepts

Behavioral Concepts are activated through Behavioral Hypotheses.

Behavioral Concepts reference the Behavioral Ontology.

Example:

```text
BC-001

Security Evaluation

BC-002

Enterprise Evaluation
```

Behavioral Concept IDs resolve against the Behavioral Concept Registry (01 — Behavioral Ontology).

Behavioral Concepts remain canonical reference knowledge.

The validation scenario records only which concepts were activated.

---

## 6. Requirement Profile

The Behavioral Intelligence Platform traverses the Behavioral Concept → Business Requirement Mapping.

The resulting Requirement Profile becomes the deterministic runtime representation of customer needs.

Example:

```text
RP-20260807-000041

REQ-002

Identity Management

REQ-004

Regulatory Compliance
```

Requirement Profiles are Runtime Objects.

They reference Business Requirements.

They never redefine Business Requirements.

---

## 7. Required Capabilities

The Recommendation Engine traverses the Business Requirement → Capability Mapping.

The resulting Capabilities represent the deterministic capability requirements for the customer's Requirement Profile.

Example:

```text
CAP-001

Single Sign-On

CAP-002

Multi-Factor Authentication

CAP-010

Audit Logging
```

Required Capabilities reference the Capability Catalog.

They never redefine Capabilities.

---

## 8. Product Capability Profiles Evaluated

The Recommendation Engine evaluates Product Capability Profiles against the required Capabilities.

Every evaluated Product Capability Profile references canonical Capability IDs.

Example:

```text
PROD-001

Microsoft 365

PROD-003

Okta

PROD-004

Google Workspace
```

Product IDs resolve against the Product Roster (05 — Product Capability Profiles).

Product Capability Profiles remain reference knowledge.

The validation scenario records only which products were evaluated.

---

## 9. Capability Coverage Analysis

Capability Coverage Analysis records the deterministic evaluation produced by the Recommendation Engine.

Coverage Analysis records:

- Coverage Percentage
- Satisfied Business Requirements
- Partially Satisfied Business Requirements
- Unsupported Business Requirements
- Satisfied Capabilities
- Missing Capabilities

Capability Coverage Analysis records deterministic outcomes.

It never performs deterministic reasoning.

---

## 10. Recommendation Package

The Recommendation Engine produces a Recommendation Package.

The Recommendation Package references the Requirement Profile.

It contains one or more Recommendation Entries.

Each Recommendation Entry records the evaluation of a recommended Product Capability Profile.

Recommendation Packages remain Runtime Objects.

They never redefine reference knowledge.

---

## 11. AI Buying Advisor

The AI Buying Advisor consumes the Recommendation Package.

It generates natural language explanations using the structured facts contained within the Recommendation Package.

The AI Buying Advisor never performs deterministic reasoning.

It never modifies the Recommendation Package.

---

## 12. Traceability Summary

Every validation scenario concludes with a complete traceability summary.

The traceability summary demonstrates that every recommendation can be traced back to observed customer behavior.

Example:

```text
Observed Behavior

↓

Behavioral Evidence

↓

Behavioral Concepts

↓

Business Requirements

↓

Required Capabilities

↓

Product Capability Profiles

↓

Capability Coverage Analysis

↓

Recommendation Package
```

This traceability chain must remain complete for every validation scenario.

It provides deterministic evidence supporting every recommendation.

---

# How Scenario Numbers Are Computed

Every number in these scenarios is derivable — nothing is illustrative.

- **Requirement confidence** derives from activated Behavioral Hypotheses via the BC → REQ mappings (06) under POL-REQ-003: noisy-OR of (association weight × hypothesis confidence), weights Primary 1.0 / Secondary 0.6 / Supporting 0.3. Requirements publish at ≥ 0.5 (POL-REQ-001); priorities follow POL-REQ-002 bands. Each scenario shows this derivation explicitly.
- **Required Capabilities per Requirement** come from 07 — Business Requirement to Capability Mapping (all associations: Primary + Secondary + Supporting).
- **Per-Requirement Coverage** = supported association weight ÷ total association weight × 100 (Coverage Calculation Model, 05 — Product Capability Profiles), using each product's Supported Capability IDs. Each required Capability counts for its association weight — Primary 1.0, Secondary 0.6, Supporting 0.3 (POL-REC-002 `capability_weights`) — not one apiece. Counting them equally let a product holding every Primary Capability of a Requirement score below one holding none of them and more optional extras (Decision #073). Full coverage is still exactly 100% and zero coverage exactly 0%, so every ranking below is unchanged in order and winner; the partial percentages rose.
- **Overall Coverage** = priority-weighted average of per-Requirement coverage, using POL-REC-002 weights (Critical ×3, High ×2, Medium ×1, Low ×0.5).
- **Match Score** = Overall Coverage × POL-REC-002's `off_subject_factor` for a candidate outside every category the shopper has been researching, and equal to Overall Coverage otherwise. It is a separate figure because coverage has an arithmetic definition to keep: being the wrong *kind* of product is not a capability the product lacks (Decision #078).
- **Subject categories** for the Match Score are those of every subject held above POL-REC-002's `subject_category_min_confidence` (0.2), not POL-REQ-004's anchoring bar (0.5). Scenario 1 holds Identity Platform Evaluation at 0.20: too weak to anchor the profile, strong enough to say what kind of product that shopper has been opening (Decision #082).
- **Ranking** follows Match Score; ties break per POL-REC-002. A ranked list is therefore not always ordered by the coverage figure beside it — an off-subject product can cover more and still rank lower, and the surfaces say so rather than leaving the order unexplained.

These scenarios therefore double as executable acceptance tests: an implementation that seeds these profiles and replays these behaviors must reproduce these exact numbers.

---

# Validation Scenario 1 — Security & Identity

## Customer Context

```text
Organization Size

Enterprise

Industry

Financial Services

Current Environment

Multiple identity providers

Business Goal

Standardize enterprise identity management while improving authentication security and centralized access governance.
```

---

## Observed Behavior

```text
Day 1 — Customer finds an identity platform, opens its security page, and
reads the Single Sign-On and administration documentation.

Day 1 — Customer returns to the audit page and the Multi-Factor Authentication
documentation, spending over a minute on the security material.

Day 2 — Customer compares the security posture of four identity platforms in
one sitting, alongside their identity lifecycle documentation.

Day 2 — Customer narrows back to one platform: Single Sign-On and
Multi-Factor Authentication documentation, and the enterprise pricing tier.

Day 2 — Customer makes a final pass over the same material.
```

---

## Behavioral Evidence

```text
BE-001

Customer compares multiple identity platforms.

Produced by BP-001 Security Evaluation

BE-004

Customer requests enterprise authentication capabilities.

Produced by BP-002 Enterprise Evaluation

BE-009

Customer evaluates identity governance features.

Produced by BP-002 Enterprise Evaluation

BE-011

Customer searches for identity platforms by name and capability.

Produced by BP-020 Identity Platform Evaluation
```

---

## Behavioral Hypotheses

```text
The customer is prioritizing enterprise identity management.

The customer is reducing authentication risk.

The customer is seeking centralized identity governance.
```

---

## Activated Behavioral Concepts

```text
BC-001

Security Evaluation — hypothesis confidence 0.80

BC-002

Enterprise Evaluation — hypothesis confidence 0.70

BC-026

Identity Platform Evaluation — hypothesis confidence 0.20
```

Journey Stage: Technical Validation

## How those confidences are reached (POL-CONF-001/002)

Each run contributes at full class value only when it differs from what came
before in **strength** or in the **kind** of behavior backing it; more of a kind
already counted damps to half (POL-CONF-002, Decision #054). The five
observations above therefore produce:

| Run | BC-001 Security Evaluation | BC-002 Enterprise Evaluation |
|---|---|---|
| 1 | Medium · security page + docs · **+0.10** | Medium · admin docs · **+0.10** |
| 2 | Strong · + reading time · **+0.20** | Medium · + audit page · **+0.10** |
| 3 | Strong · security pages alone · **+0.20** | Strong (2 sessions) · **+0.20** |
| 4 | Strong · pages + docs · **+0.20** | Strong · + enterprise tier · **+0.20** |
| 5 | Strong · repeat · **+0.10** | Strong · repeat · **+0.10** |
| | **0.80** | **0.70** |

This derivation is why the observed behavior is written as five distinct
episodes rather than one summary: under POL-CONF-002 the *shape* of the
research, not merely its volume, is what produces the confidences. A shopper
who performed the fifth episode ten more times would still reach 0.80.

**BC-026 Identity Platform Evaluation — 0.20** (added in v1.4, Decision #077).
This shopper is not only vetting candidates on security grounds; they are
shopping for an identity platform, and now the pack has a concept that says so.
BP-020 reaches Strong across two sessions on three searches —
`okta scim provisioning`, `single sign-on scim provisioning okta` and
`okta sso audit logging` — contributing **+0.20** once.

It draws on **nothing else in the clickstream**, and that restraint is the
substance of the entry rather than a detail of it. The SSO and MFA
documentation pages this shopper read are BP-001's evidence, and BC-001 is
already Primary to REQ-002; letting BP-020 read them too would put one page
into two Primary contributions of the same Requirement. Measured before the
overlap was removed: five of BP-020's eight supporting events were BP-001's,
and REQ-002 derived 0.88 instead of 0.84 on no new evidence.

---

## Requirement Derivation (POL-REQ-003)

```text
REQ-002:  BC-001 Primary (1.0×0.80) + BC-026 Primary (1.0×0.20)
          = 1 − (0.20)(0.80) = 0.84
          → publish, Critical (≥0.8, stage ≥ Technical Validation)

REQ-004:  BC-001 Supporting (0.3×0.80=0.24) + BC-002 Secondary (0.6×0.70=0.42)
          = 1 − (0.76)(0.58) = 0.56  → publish, Medium

REQ-001:  BC-001 Secondary (0.6×0.80=0.48)
          = 0.48  → below 0.5, not published
```

**Why BC-002 does not appear in REQ-002 (Decision #050).** Enterprise Evaluation
was Primary to Identity Management until this scenario was amended, which put
REQ-002 at 0.94. The association was removed: organizational scale is a fact
about the buyer, not a statement of what they need — an HR buyer reading a
provisioning page is still buying HR software. The Secondary link to REQ-004
survives, because governance obligations genuinely do follow from
organizational adoption. Nothing downstream moves: the same two requirements
publish, in the same priority bands, producing the same coverage percentages
below. That invariance is the evidence the change was surgical.

**And why BC-026 does (Decision #077).** The distinction #050 drew is precisely
the one BC-026 sits on the other side of. Enterprise Evaluation is an attribute
of the buyer; Identity Platform Evaluation is a statement of what they are
buying, which is what a Primary association is for. REQ-002 accordingly moves
0.80 → 0.84 — the only number in this scenario that does. Priority band,
requirement set, stage and every coverage percentage below are unchanged.

---

## Requirement Profile

```text
RP-20260807-000001

REQ-002

Identity Management — Priority: Critical

REQ-004

Regulatory Compliance — Priority: Medium
```

---

## Required Capabilities

```text
From REQ-002 (07 — mapping):

CAP-001   Single Sign-On
CAP-002   Multi-Factor Authentication
CAP-003   SCIM Provisioning
CAP-004   Conditional Access
CAP-010   Audit Logging

From REQ-004 (07 — mapping):

CAP-010   Audit Logging
CAP-012   Information Governance
CAP-013   Data Retention
CAP-014   eDiscovery
```

---

## Product Capability Profiles Evaluated

```text
PROD-003   Okta

PROD-001   Microsoft 365

PROD-004   Google Workspace
```

---

## Capability Coverage Analysis

```text
PROD-003  (Okta)

REQ-002 coverage: 4.1/4.1 = 100%
REQ-004 coverage: 1.0/3.8 = 26%   (has CAP-010)

Overall (3×1.00 + 1×0.263) ÷ 4 = 82%

Satisfied Requirements

REQ-002

Partially Satisfied Requirements

REQ-004

Missing Capabilities

CAP-012, CAP-013, CAP-014
```

```text
PROD-001  (Microsoft 365)

REQ-002 coverage: 2.9/4.1 = 71%   (missing CAP-003, CAP-004)
REQ-004 coverage: 4/4 = 100%

Overall (3×0.707 + 1×1.00) ÷ 4 = 78%

Satisfied Requirements

REQ-004

Partially Satisfied Requirements

REQ-002

Missing Capabilities

CAP-003, CAP-004
```

```text
PROD-004  (Google Workspace)

REQ-002 coverage: 2.3/4.1 = 56%   (missing CAP-003, CAP-004, CAP-008)
REQ-004 coverage: 1.6/3.8 = 42%   (missing CAP-012, CAP-014, CAP-027)

Overall (3×0.561 + 1×0.421) ÷ 4 = 53%

Partially Satisfied Requirements

REQ-002

REQ-004

Missing Capabilities

CAP-003, CAP-004, CAP-012, CAP-014
```

---

## Recommendation Package

```text
REC-20260807-000001

Requirement Profile

RP-20260807-000001

Recommendation Entries

Rank 1

PROD-003

Rank 2

PROD-001

Rank 3

PROD-004
```

---

## AI Buying Advisor

The AI Buying Advisor consumes the Recommendation Package.

Using the structured facts contained within the Recommendation Package, it generates a natural language explanation describing why PROD-003 best satisfies the customer's Business Requirements.

The AI Buying Advisor does not modify the Recommendation Package.

It explains the deterministic recommendation outcome.

---

## Traceability Summary

```text
Observed Behavior

↓

Behavioral Evidence (BP-001, BP-002, BP-020)

↓

BC-001

BC-002

BC-026

↓

REQ-002 (Critical)

REQ-004 (Medium)

↓

CAP-001  CAP-002  CAP-003  CAP-004  CAP-010

CAP-012  CAP-013  CAP-014

↓

PROD-003

↓

REC-20260807-000001
```

This scenario demonstrates deterministic recommendation generation for enterprise identity management.

---

# Validation Scenario 2 — Collaboration & Productivity

## Customer Context

```text
Organization Size

Global Enterprise

Industry

Professional Services

Current Environment

Multiple collaboration platforms

Business Goal

Consolidate collaboration capabilities while improving employee productivity.
```

---

## Observed Behavior

```text
Customer browses the collaboration category and its platforms, and searches
for AI meeting summaries.

Customer widens to more collaboration platforms and AI feature pages.

Customer opens a second line of research on the same platforms, and reads
productivity, template and task documentation.

Customer requests integrated communication capabilities — meetings
documentation and AI assistant research.

Customer returns to the collaboration category, and to template and task
documentation.
```

The two lines of research reach the concept differently — one through the
category and its products, the other through the products and then their
documentation — which is what earns BC-005 0.80 under POL-CONF-002
(Decision #054) rather than repetition of a single route.

---

## Behavioral Evidence

```text
BE-002

Customer evaluates collaboration capabilities.

Produced by BP-005 Collaboration Evaluation
(co-supports BC-006 Productivity Evaluation)

BE-006

Customer requests AI productivity features.

Produced by BP-003 AI Evaluation
```

---

## Behavioral Hypotheses

```text
The customer is modernizing enterprise collaboration.

The customer is improving workforce productivity.

The customer is seeking integrated collaboration capabilities.
```

---

## Activated Behavioral Concepts

```text
BC-005

Collaboration Evaluation — hypothesis confidence 0.80

BC-006

Productivity Evaluation — hypothesis confidence 0.50

BC-003

AI Evaluation — hypothesis confidence 0.50
```

Journey Stage: Technical Validation

---

## Requirement Derivation (POL-REQ-003)

```text
REQ-001:  BC-005 Primary (1.0×0.80) + BC-003 Supporting (0.3×0.50=0.15)
          = 1 − (0.20)(0.85) = 0.83  → publish, Critical

REQ-013:  BC-006 Primary (1.0×0.50)
          = 0.50  → publish, Medium

REQ-005:  BC-003 Primary (1.0×0.50)
          = 0.50  → publish, Medium

REQ-003:  BC-006 Supporting (0.3×0.50=0.15) + BC-003 Secondary (0.6×0.50=0.30)
          = 1 − (0.85)(0.70) = 0.41  → below 0.5, not published

REQ-002:  BC-005 Supporting (0.3×0.80=0.24)
          = 0.24  → not published
```

**Why AI Assistance fell from High to Medium, and why a third requirement
appeared** (Decision #079). Both are the same amendment. Productivity Evaluation
used to be Primary to AI Assistance, so this shopper's reading about templates
and tasks was counted as evidence that they wanted an AI assistant — it carried
REQ-005 to 0.75 High. It was a proxy for a requirement the pack could not
express. REQ-013 Work Management is that requirement, so the evidence goes
there, and REQ-005 now rests on this shopper's actual AI research alone.

The published percentages below all fall as a result, and the arithmetic is
worth stating plainly: three requirements now share the priority-weighted
average where two did (Critical ×3 + Medium ×1 + Medium ×1 = 5, the same total
weight as Critical ×3 + High ×2), and none of the three products originally
evaluated here holds a work-management capability. Google Workspace is not
thought less of than it was; it answers two of three stated needs instead of
two of two.

---

## Requirement Profile

```text
RP-20260807-000002

REQ-001

Secure Collaboration — Priority: Critical

REQ-013

Work Management — Priority: Medium

REQ-005

AI Assistance — Priority: Medium
```

---

## Required Capabilities

```text
From REQ-001 (07 — mapping):

CAP-001   Single Sign-On
CAP-002   Multi-Factor Authentication
CAP-007   Document Collaboration
CAP-005   Messaging
CAP-006   Video Meetings
CAP-010   Audit Logging
CAP-011   Encryption

From REQ-005 (07 — mapping):

CAP-020   AI Chat
CAP-021   Content Generation
CAP-022   Intelligent Search
CAP-023   Document Summarization
CAP-015   Workflow Automation

From REQ-013 (07 — mapping):

CAP-056   Task Management
CAP-058   Workload Management
CAP-057   Template Library
```

---

## Product Capability Profiles Evaluated

```text
PROD-004   Google Workspace

PROD-009   Notion

PROD-005   Zoom Workplace
```

---

## Capability Coverage Analysis

```text
PROD-004  (Google Workspace)

REQ-001 coverage: 7/7 = 100%
REQ-005 coverage: 3.2/3.5 = 91%   (missing CAP-015)
REQ-013 coverage: 0/1.9 = 0%      (missing CAP-056, CAP-057, CAP-058)

Overall (3×1.00 + 1×0.914 + 1×0.00) ÷ 5 = 78%
Match score: on subject (Collaboration), so 78%

Satisfied Requirements

REQ-001

Partially Satisfied Requirements

REQ-005

Missing Capabilities

CAP-015
```

```text
PROD-009  (Notion)

REQ-001 coverage: 1.0/4.8 = 21%   (has CAP-007 only)
REQ-005 coverage: 3.2/3.5 = 91%   (missing CAP-015)
REQ-013 coverage: 0/1.9 = 0%      (missing CAP-056, CAP-057, CAP-058)

Overall (3×0.208 + 1×0.914 + 1×0.00) ÷ 5 = 31%
Match score: off subject (Knowledge & Docs, not Collaboration) 31% × 0.6 = 18%
             — below the publication cut once Jira enters; see below

Partially Satisfied Requirements

REQ-001

REQ-005

Missing Capabilities

CAP-001, CAP-002, CAP-005, CAP-006, CAP-010, CAP-011, CAP-015
```

```text
PROD-005  (Zoom Workplace)

REQ-001 coverage: 1.2/4.8 = 25%   (has CAP-005, CAP-006)
REQ-005 coverage: 1.6/3.5 = 46%   (has CAP-020, CAP-023)
REQ-013 coverage: 0/1.9 = 0%      (missing CAP-056, CAP-057, CAP-058)

Overall (3×0.25 + 1×0.457 + 1×0.00) ÷ 5 = 24%
Match score: on subject (Collaboration), so 24%

Partially Satisfied Requirements

REQ-001

REQ-005

Missing Capabilities

CAP-001, CAP-002, CAP-007, CAP-010, CAP-011, CAP-015, CAP-021, CAP-022
```

**The off-subject term, and why it reorders this scenario (Decision #077).**
Collaboration became a declared subject in v1.4, so POL-REC-002's
`off_subject_factor` — dormant here until now, because this journey held no
subject the platform could name — applies to any candidate outside the category
being shopped. Notion is catalogued under Knowledge & Docs, so its **match
score** is 29% against Zoom Workplace's 33%, and it ranks below it.

**Its coverage is still 49%, and that is the number the shopper is shown**
(Decision #078). The two were one field until the discount was found in the
figure printed beside the capability list, in the digest, and in the facts block
handed to the narrative — Notion published at 29% next to four of the five AI
capabilities this shopper asked for. Coverage answers what a product covers;
being the wrong kind of product is not a capability it lacks.

So this scenario's list is deliberately not ordered by the percentage beside it:
Zoom at 33% sits above Notion at 49%. That is the intended reading — Notion's
49% is carried almost entirely by REQ-005 AI Assistance at 91%, while on
REQ-001 Secure Collaboration, the Critical requirement its behaviour anchored,
it holds one capability of seven. A shopper consolidating collaboration tools is
shown collaboration tools first, and told plainly why the one covering more is
not at the top.

**The known limitation, recorded rather than papered over.** The factor keys on
the candidate's catalog category alone, so it cannot tell a product the
retrieval surfaced from one the shopper studied. This shopper opened Notion
repeatedly and searched for it by name, and it still ranks last. The rule as
specified in POL-REC-002 says *outside every category the shopper has been
researching*, and Notion's category is outside it; changing that reading is a
policy change and is deliberately not made here. What #078 removes is the part
that was indefensible either way — the shopper being told a coverage figure that
disagreed with its own components.

---

## Recommendation Package

```text
REC-20260807-000002

Requirement Profile

RP-20260807-000002

Recommendation Entries

Rank 1

PROD-004

Rank 2

PROD-005

Rank 3

PROD-006
```

**Atlassian Jira replaces Notion in the published list, and that is the cost of
Decision #079 rather than a detail of it.** Jira enters because it covers the
new requirement in full, which makes it a guaranteed candidate (Decision #060),
and it is on subject because BC-006 is held at 0.50 so Work Management joins
Collaboration in this shopper's subject categories. Its overall coverage is 23%.

Notion's is 31% — higher — and this shopper searched for it by name. It is
absent because Knowledge & Docs is a category with no subject, so the
off-subject factor takes it to a match of 18 and Jira's arrival pushes it past
the top-three-plus-two publication cut.

This is Decision #078's recorded limitation reaching its sharpest form: the
factor keys on the candidate's catalog category alone and cannot tell a product
the shopper studied from one retrieval dragged in. Two things would each
resolve it, and both are outstanding — a Content & Knowledge requirement, which
would give Notion's category a subject, and a lower confidence floor for
POL-REC-002's category set than POL-REQ-004 uses for anchoring.

---

## AI Buying Advisor

The AI Buying Advisor generates a natural language explanation using the structured facts contained within the Recommendation Package.

The explanation reflects the deterministic recommendation outcome.

---

## Traceability Summary

```text
Observed Behavior

↓

Behavioral Evidence (BP-005, BP-003)

↓

BC-005

BC-006

BC-003

↓

REQ-001 (Critical)

REQ-005 (High)

↓

CAP-001  CAP-002  CAP-005  CAP-006  CAP-007  CAP-010  CAP-011

CAP-015  CAP-020  CAP-021  CAP-022  CAP-023

↓

PROD-004

↓

REC-20260807-000002
```

This scenario demonstrates deterministic recommendation generation for enterprise collaboration and AI-assisted productivity.

---

# Validation Scenario 3 — Process Automation

## Customer Context

```text
Organization Size

Large Enterprise

Industry

Manufacturing

Current Environment

Multiple disconnected business systems

Business Goal

Automate business processes while improving integration across enterprise applications.
```

---

## Observed Behavior

```text
Customer evaluates workflow automation platforms.

Customer requests low-code automation capabilities.

Customer asks about enterprise integrations.

Customer evaluates event-driven automation.

Customer requests API integration capabilities.
```

---

## Behavioral Evidence

```text
BE-003

Customer evaluates workflow automation.

Produced by BP-007 Automation Evaluation

BE-007

Customer requests enterprise integrations.

Produced by BP-008 Integration Evaluation

BE-010

Customer evaluates business process automation.

Produced by BP-007 Automation Evaluation
```

---

## Behavioral Hypotheses

```text
The customer is modernizing operational processes.

The customer is reducing manual work.

The customer is seeking enterprise-wide automation.
```

---

## Activated Behavioral Concepts

```text
BC-007

Automation Evaluation — hypothesis confidence 0.80

BC-008

Integration Evaluation — hypothesis confidence 0.70
```

Journey Stage: Technical Validation

---

## Requirement Derivation (POL-REQ-003)

```text
REQ-003:  BC-007 Primary (1.0×0.80) + BC-008 Primary (1.0×0.70)
          = 1 − (0.20)(0.30) = 0.94  → publish, Critical, anchored

REQ-005:  BC-007 Secondary (0.6×0.80=0.48)
          = 0.48  → below 0.5, not published

REQ-002:  BC-008 Supporting (0.3×0.70=0.21), demoted from Secondary
          = 0.21  → not published
```

**Automation Evaluation is the subject here** (BC-007, held at 0.80), so
POL-REQ-004 anchors REQ-003 and demotes the lens BC-008 Integration Evaluation
one band — but **only where it feeds something other than the anchor**. On
REQ-002 it drops Secondary → Supporting, 0.42 → 0.21. On REQ-003 it keeps its
Primary association, because an automation shopper checking integrations is
evidencing the very thing they are shopping for. Demoting it there took REQ-003
below its own Critical band, which is how the exception was found (Decision
#077).

---

## Requirement Profile

```text
RP-20260807-000003

REQ-003

Workflow Automation — Priority: Critical
```

---

## Required Capabilities

```text
From REQ-003 (07 — mapping):

CAP-015   Workflow Automation

CAP-016   Integration Connectors

CAP-017   Event Triggers

CAP-018   Business Rules

CAP-019   API Integration
```

---

## Product Capability Profiles Evaluated

```text
PROD-007   ServiceNow

PROD-008   Zapier

PROD-001   Microsoft 365
```

---

## Capability Coverage Analysis

```text
PROD-007  (ServiceNow)

REQ-003 coverage: 5/5 = 100%

Overall (3×1.00) ÷ 3 = 100%

Satisfied Requirements

REQ-003

Missing Capabilities

None
```

```text
PROD-008  (Zapier)

REQ-003 coverage: 2.9/3.5 = 83%   (missing CAP-018)

Overall (3×0.829) ÷ 3 = 83%

Partially Satisfied Requirements

REQ-003

Missing Capabilities

CAP-018
```

```text
PROD-001  (Microsoft 365)

REQ-003 coverage: 2.6/3.5 = 74%   (missing CAP-018, CAP-019)

Overall (3×0.743) ÷ 3 = 74%

Partially Satisfied Requirements

REQ-003

Missing Capabilities

CAP-018, CAP-019
```

---

## Recommendation Package

```text
REC-20260807-000003

Requirement Profile

RP-20260807-000003

Recommendation Entries

Rank 1

PROD-007

Rank 2

PROD-008

Rank 3

PROD-001
```

---

## AI Buying Advisor

The AI Buying Advisor generates a natural language explanation using the structured facts contained within the Recommendation Package.

The explanation reflects the deterministic recommendation outcome.

---

## Traceability Summary

```text
Observed Behavior

↓

Behavioral Evidence (BP-007, BP-008)

↓

BC-007

BC-008

↓

REQ-003 (Critical)

↓

CAP-015  CAP-016  CAP-017  CAP-018  CAP-019

↓

PROD-007

↓

REC-20260807-000003
```

This scenario demonstrates deterministic recommendation generation for workflow automation and enterprise integration.

---

# Validation Scenario 4 — Governance & Compliance

## Customer Context

```text
Organization Size

Global Enterprise

Industry

Healthcare

Current Environment

Distributed information governance

Business Goal

Strengthen governance, auditing, and regulatory compliance across enterprise information systems.
```

---

## Observed Behavior

```text
Customer evaluates compliance capabilities.

Customer requests audit reporting.

Customer evaluates information governance.

Customer requests data retention capabilities.

Customer evaluates eDiscovery functionality.
```

---

## Behavioral Evidence

```text
BE-005

Customer evaluates governance capabilities.

Produced by BP-004 Compliance Evaluation

BE-008

Customer requests regulatory compliance support.

Produced by BP-004 Compliance Evaluation

BE-011

Customer evaluates enterprise auditing.

Produced by BP-004 Compliance Evaluation
```

---

## Behavioral Hypotheses

```text
The customer is strengthening enterprise governance.

The customer is improving regulatory compliance.

The customer is increasing audit readiness.
```

---

## Activated Behavioral Concepts

```text
BC-004

Compliance Evaluation — hypothesis confidence 0.80
```

Journey Stage: Technical Validation

---

## Requirement Derivation (POL-REQ-003)

```text
REQ-004:  BC-004 Primary (1.0×0.80)
          = 0.80  → publish, Critical (≥0.8, stage ≥ Technical Validation)

REQ-002:  BC-004 Secondary (0.6×0.80=0.48)
          = 0.48  → below 0.5, not published

REQ-001:  BC-004 Supporting (0.3×0.80=0.24)
          = 0.24  → not published
```

---

## Requirement Profile

```text
RP-20260807-000004

REQ-004

Regulatory Compliance — Priority: Critical
```

---

## Required Capabilities

```text
From REQ-004 (07 — mapping):

CAP-010   Audit Logging

CAP-012   Information Governance

CAP-013   Data Retention

CAP-014   eDiscovery
```

---

## Product Capability Profiles Evaluated

```text
PROD-001   Microsoft 365

PROD-010   Box

PROD-004   Google Workspace
```

---

## Capability Coverage Analysis

```text
PROD-001  (Microsoft 365)

REQ-004 coverage: 4/4 = 100%

Overall (3×1.00) ÷ 3 = 100%

Satisfied Requirements

REQ-004

Missing Capabilities

None
```

```text
PROD-010  (Box)

REQ-004 coverage: 2.6/3.8 = 68%   (missing CAP-014, CAP-027)

Overall (3×0.684) ÷ 3 = 68%

Partially Satisfied Requirements

REQ-004

Missing Capabilities

CAP-014
```

```text
PROD-004  (Google Workspace)

REQ-004 coverage: 1.6/3.8 = 42%   (missing CAP-012, CAP-014, CAP-027)

Overall (3×0.50) ÷ 3 = 50%

Partially Satisfied Requirements

REQ-004

Missing Capabilities

CAP-012, CAP-014
```

---

## Recommendation Package

```text
REC-20260807-000004

Requirement Profile

RP-20260807-000004

Recommendation Entries

Rank 1

PROD-001

Rank 2

PROD-010

Rank 3

PROD-004
```

---

## AI Buying Advisor

The AI Buying Advisor generates a natural language explanation using the structured facts contained within the Recommendation Package.

The explanation reflects the deterministic recommendation outcome.

---

## Traceability Summary

```text
Observed Behavior

↓

Behavioral Evidence (BP-004)

↓

BC-004

↓

REQ-004 (Critical)

↓

CAP-010  CAP-012  CAP-013  CAP-014

↓

PROD-001

↓

REC-20260807-000004
```

This scenario demonstrates deterministic recommendation generation for governance, auditing, and regulatory compliance.

---

# Validation Scenario 5 — Sales & Customer Management

Added with the v1.2 coverage extension (doc 14). The first four scenarios all
resolve inside the original five requirements; this one exercises the seven
added for the wide catalog, and exists because a real journey through them was
answered wrongly.

## Customer Context

```text
Organization Size

Mid-market

Industry

B2B services

Current Environment

Spreadsheet pipeline tracking, no shared customer record

Business Goal

Adopt a system of record for customer relationships, with campaign reach for the same audience.
```

---

## Observed Behavior

```text
SEARCH                "crm"
PRODUCT_VIEWED        category crm
DOCUMENTATION_VIEWED  topic pipeline
COMPARISON_STARTED    two CRM products
PRODUCT_VIEWED        category crm
DOCUMENTATION_VIEWED  topic crm
SEARCH                "marketing campaign"
DOCUMENTATION_VIEWED  topic campaigns
```

---

## Activated Behavioral Concepts

```text
BC-019

CRM Evaluation — hypothesis confidence 0.80

BC-022

Marketing Evaluation — hypothesis confidence 0.50
```

Journey Stage: Technical Validation

---

## Requirement Derivation (POL-REQ-003)

```text
REQ-006:  BC-019 Primary (1.0x0.80)
          = 0.80  -> publish, Critical (>= 0.8, stage >= Technical Validation)

REQ-009:  BC-019 Secondary (0.6x0.80=0.48) + BC-022 Primary (1.0x0.50)
          = 1 - (0.52)(0.50) = 0.74  -> publish, High

REQ-003:  BC-019 Supporting (0.3x0.80=0.24)
          = 0.24  -> below 0.5, not published

REQ-011:  BC-022 Secondary (0.6x0.50=0.30)
          = 0.30  -> below 0.5, not published

REQ-005:  BC-022 Supporting (0.3x0.50=0.15)
          = 0.15  -> below 0.5, not published
```

---

## Requirement Profile

```text
REQ-006

Sales & Customer Management — Priority: Critical

REQ-009

Marketing Execution — Priority: High
```

---

## Coverage & Ranking (POL-REC-002 — Critical x3, High x2)

Against the demo catalog:

| Rank | Product | Sales & Customer Mgmt | Marketing Execution | Overall |
|---|---|---|---|---|
| 1 | HubSpot CRM | 80% | 80% | **80%** |
| 2 | Zoho CRM | 60% | 60% | 60% |
| 3 | Pipedrive | 100% | 0% | 60% |
| 4 | Zendesk | 100% | 0% | 60% |
| 5 | Freshsales | 80% | 0% | 48% |
| 6 | Braze | 0% | 100% | 40% |
| 7 | Mailchimp | 0% | 100% | 40% |
| 8 | Salesforce Sales Cloud | 60% | 0% | 36% |

Readiness: **READY** (one requirement >= 0.6, >= 5 high-signal events).

### What this scenario is for

**It is the regression case for the defect that motivated doc 14.** Run before
the extension, this journey published Workflow Automation and Identity
Management, and ranked Microsoft 365 first with Salesforce fifth — the platform
had no way to represent wanting a CRM, so it answered the nearest question it
could.

**It demonstrates weighted coverage doing real work.** Pipedrive covers the
Critical requirement completely and scores below HubSpot, which covers both
partially. Ranks 2 and 3 tie at 60% by different routes and are separated by
the documented tie-break. A single-requirement scenario cannot show either.

**It records a catalog-authoring observation, not an engine one.** Salesforce
Sales Cloud ranks last of the eight. Its editorial profile carries three CRM
capabilities and no marketing capability, while HubSpot carries four and four.
That is a statement about the seed data, which is illustrative rather than a
vendor claim (doc 12) — but anyone expecting the best-known name to rank first
should know the ranking follows the profile, and that the profile is editable.

---

# Validation Principles

Every implementation of the Software Buying Domain should produce deterministic, traceable, and explainable recommendation outcomes.

The following principles define the expected behavior of every valid implementation.

---

## Principle 1

Every recommendation must be deterministic.

Given the same:

- Observed Behavior
- Behavioral Evidence
- Behavioral Hypotheses
- Behavioral Memory
- Domain Pack version
- Product Capability Profiles
- Recommendation Engine version

the implementation must produce the same:

- Requirement Profile
- Capability Coverage Analysis
- Recommendation Package

---

## Principle 2

Every recommendation must be completely traceable.

Every Recommendation Package must be traceable back to:

Observed Behavior

↓

Behavioral Evidence

↓

Behavioral Hypotheses

↓

Behavioral Concepts

↓

Business Requirements

↓

Capabilities

↓

Product Capability Profiles

↓

Capability Coverage Analysis

↓

Recommendation Package

No recommendation should exist without a complete traceability chain.

---

## Principle 3

Every recommendation must remain explainable.

The Recommendation Package contains structured facts.

The AI Buying Advisor generates natural language explanations using those structured facts.

Natural language explanations must remain consistent with the Recommendation Package.

The AI Buying Advisor never performs deterministic reasoning.

---

## Principle 4

Reference Knowledge remains immutable during execution.

Behavioral Concepts

Business Requirements

Capabilities

Product Capability Profiles

Behavioral Concept Mappings

Business Requirement Mappings

must never be modified during runtime.

---

## Principle 5

Runtime Objects never redefine Reference Knowledge.

Runtime Objects reference canonical identifiers.

They never duplicate or redefine:

- Behavioral Concepts
- Business Requirements
- Capabilities
- Product Capability Profiles

This follows the architectural principle:

Reference, don't duplicate.

---

## Principle 6

Recommendation Packages communicate recommendation outcomes.

They never perform:

- recommendation logic
- capability matching
- ranking algorithms
- decision policies

Those responsibilities belong exclusively to the Recommendation Engine.

---

## Principle 7

Behavioral Intelligence Platform and Recommendation Engine have independent responsibilities.

Behavioral Intelligence Platform produces:

- Behavioral Evidence
- Behavioral Hypotheses
- Behavioral Memory
- Requirement Profile

Recommendation Engine produces:

- Capability Coverage Analysis
- Recommendation Package

Neither engine assumes responsibilities belonging to the other.

---

## Principle 8

Every Runtime Object has one canonical responsibility.

Behavioral Evidence captures observations.

Behavioral Hypotheses capture interpretations.

Behavioral Memory captures behavioral context.

Requirement Profiles capture customer requirements.

Recommendation Packages capture recommendation outcomes.

Runtime Objects never overlap responsibilities.

---

## Principle 9

The Software Buying Domain remains the single source of truth for domain knowledge.

Every implementation references the Domain Pack.

Implementations never redefine:

- Business Requirements
- Capabilities
- Product Capability Profiles
- Canonical mappings

The Domain Pack remains the authoritative knowledge source.

---

## Principle 10

Reference Behavioral Journey Scenarios validate the architecture.

They introduce no new:

- Behavioral Concepts
- Business Requirements
- Capabilities
- Product Capability Profiles
- Runtime Objects

They exist solely to validate that the Software Buying Domain behaves consistently during runtime.

---

# Claude Implementation Contract

Claude MUST:

- Treat every Reference Behavioral Journey as a validation scenario.
- Preserve deterministic execution paths.
- Preserve complete traceability.
- Reference canonical identifiers.
- Preserve the distinction between Reference Knowledge and Runtime Objects.
- Explain recommendations using Recommendation Packages.
- Never invent missing domain knowledge.
- Never bypass the canonical mappings.

Claude MUST NOT:

- Introduce new domain concepts.
- Modify canonical Business Requirements.
- Modify canonical Capabilities.
- Modify Product Capability Profiles.
- Modify Runtime Objects.
- Replace deterministic reasoning with AI-generated assumptions.
- Skip validation steps.
- Produce recommendations that cannot be traced back to observed behavior.

---

# Summary

The Reference Behavioral Journey Scenarios document validates the complete Software Buying Domain using deterministic, end-to-end behavioral journeys.

This chapter introduces no new domain concepts.

Instead, it demonstrates how the existing architecture behaves during runtime by traversing:

Observed Behavior

↓

Behavioral Evidence

↓

Behavioral Hypotheses

↓

Behavioral Concepts

↓

Behavioral Concept → Business Requirement Mapping

↓

Requirement Profile

↓

Business Requirement → Capability Mapping

↓

Required Capabilities

↓

Product Capability Profiles

↓

Capability Coverage Analysis

↓

Recommendation Package

↓

AI Buying Advisor

Each Reference Behavioral Journey validates:

- Deterministic reasoning
- Complete traceability
- Reference reuse
- Runtime consistency
- Explainable recommendations
- Separation of responsibilities

Together, the Behavioral Ontology, Business Requirement Catalog, Capability Catalog, Product Capability Profiles, Mapping Documents, Runtime Objects, and Reference Behavioral Journey Scenarios form the complete Software Buying Domain Pack.

The Software Buying Domain Pack now provides:

- Canonical Reference Knowledge
- Canonical Relationships
- Canonical Runtime Contracts
- Canonical Validation

This completes the Software Buying Domain Pack and establishes an implementation-ready foundation for the Behavioral Intelligence Platform, Recommendation Engine, and AI Buying Advisor.

---