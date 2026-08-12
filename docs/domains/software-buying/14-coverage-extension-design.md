# Coverage Extension — Design Table (proposal, not yet adopted)

**Status: for review.** Nothing here is implemented. This document assigns every
capability in the catalog to a requirement, every requirement to a concept, and
every concept to a pattern with stated activation conditions — so the design can
be argued with before any code is written.

## The problem, measured

The catalog carries 55 capabilities. The requirement mappings reach 21 of them.

**82 of the 250 catalog products hold no capability that any requirement
names.** They are returned by search, they render a product page, they can be
added to a cart — and they can never appear in a recommendation, because
coverage scoring has nothing to score them on.

| Category | Unreachable products |
|---|---|
| DevOps | 16 |
| HR | 14 |
| Marketing | 13 |
| Data & Analytics | 12 |
| CRM | 10 |
| Finance | 9 |
| Customer Support | 3 |
| Workflow Automation | 3 |
| Work Management · Productivity | 2 |

This was a deliberate v1.1 scope boundary (doc 10 §v1.1: *"none of the v1.1
capabilities participates in requirement coverage; out-of-domain products are
the realistic noise retrieval and matching must cut through"*). The catalog was
scenery. It is now merchandise, so the boundary has to move.

---

## Design rule: the existing five requirements are frozen

New capabilities join **new** requirements only. Nothing is added to Secure
Collaboration, Identity Management, Workflow Automation, Regulatory Compliance
or AI Assistance.

This is not caution for its own sake. The four derivation scenarios in doc 09
assert exact coverage percentages — Okta 81%, Microsoft 365 70%, Google 58% —
and every one of those is a ratio whose denominator is the size of a
requirement's capability set. Adding one capability to Identity Management
moves numbers that twelve acceptance tests pin.

A capability may belong to several requirements, so this constraint costs
nothing in expressiveness.

**Consequence for verification:** all twelve acceptance stories and all four
derivation scenarios must stay green *untouched*. They will, because the
canonical ten fixture products hold none of the new capabilities and the test
fixtures emit none of the new topics — so no new pattern can fire inside them.
If one of those tests moves, something has leaked and the change is wrong.

---

## Table 1 — Requirement → Capabilities

Seven new requirements. Association levels follow doc 07's convention and feed
POL-REC-002 weighting.

| New requirement | Capabilities | Primary / Secondary |
|---|---|---|
| **REQ-006 Sales & Customer Management** | Sales Pipeline · Contact Management · Lead Scoring · Customer Support Ticketing · Live Chat | Primary: Pipeline, Contact Mgmt · Secondary: Lead Scoring, Ticketing · Supporting: Live Chat |
| **REQ-007 People Operations** | Applicant Tracking · Onboarding Workflows · Payroll Processing · Time & Attendance · Performance Reviews | Primary: Payroll, Applicant Tracking · Secondary: Onboarding, Time & Attendance · Supporting: Performance Reviews |
| **REQ-008 Financial Management** | Invoicing · Expense Management · General Ledger · Budgeting & Forecasting · Payment Processing | Primary: General Ledger, Invoicing · Secondary: Expenses, Payments · Supporting: Budgeting |
| **REQ-009 Marketing Execution** | Email Campaigns · Marketing Automation · Social Media Mgmt · SEO Analytics · A/B Testing | Primary: Marketing Automation, Email Campaigns · Secondary: Social, SEO · Supporting: A/B Testing |
| **REQ-010 Engineering Delivery** | CI/CD Pipelines · Infrastructure Monitoring · Log Management · Incident Response · Container Orchestration | Primary: CI/CD, Monitoring · Secondary: Logs, Incident Response · Supporting: Containers |
| **REQ-011 Data & Insight** | Data Visualization · ETL Pipelines · Data Warehousing | Primary: Warehousing, ETL · Secondary: Visualization |
| **REQ-012 Security Operations** | Threat Protection · Data Loss Prevention · Compliance Reporting · Identity Federation | Primary: Threat Protection, DLP · Secondary: Compliance Reporting · Supporting: Federation |

REQ-012 exists to absorb four capabilities stranded inside the *original*
domains. Housing them in a new requirement reaches them without touching the
frozen five.

### Result

| | Before | After |
|---|---|---|
| Capabilities reachable by some requirement | 21 / 55 | **53 / 55** |
| Products that can never be recommended | **82 / 250** | **0 / 250** |

Two capabilities remain unmapped: **File Sharing** and **AI Workflow
Assistance**. Both belong squarely to existing requirements' domains, so
mapping them means editing a frozen set and updating the pinned derivations.
**No product is stranded by leaving them out** — every product holding either
also holds something mapped. Recommend leaving both for a separate, deliberate
decision.

---

## Table 2 — Pattern → Concept → Requirement

Each new area needs all three links. A requirement with no concept feeding it
is inert; a concept with no pattern producing it never forms.

Activation follows the established shape: **two qualifying signals** activate,
**four** make it strong.

| New pattern | Activates on ≥2 of | Strong at | Concept | Primary requirement |
|---|---|---|---|---|
| **BP-013 CRM Evaluation** | product view in CRM / Customer Support · docs topic `pipeline` `crm` `tickets` · category browse CRM · search "crm, sales pipeline, lead, ticketing" | ≥4 | BC-019 CRM Evaluation | REQ-006 |
| **BP-014 People Ops Evaluation** | product view in HR · docs topic `payroll` `hiring` `performance` · category browse HR · search "hr, payroll, ats, onboarding" | ≥4 | BC-020 People Operations Evaluation | REQ-007 |
| **BP-015 Finance Evaluation** | product view in Finance · docs topic `accounting` `billing` `expenses` `forecasting` · category browse Finance · search "accounting, invoicing, gl, expenses" | ≥4 | BC-021 Financial Evaluation | REQ-008 |
| **BP-016 Marketing Evaluation** | product view in Marketing · docs topic `campaigns` `seo` `experiments` · category browse Marketing · search "marketing, email campaign, seo" | ≥4 | BC-022 Marketing Evaluation | REQ-009 |
| **BP-017 Engineering Delivery Evaluation** | product view in DevOps · docs topic `cicd` `monitoring` `incidents` `containers` · category browse DevOps · search "ci cd, observability, kubernetes" | ≥4 | BC-023 Engineering Delivery Evaluation | REQ-010 |
| **BP-018 Data & Insight Evaluation** | product view in Data & Analytics · docs topic `warehouse` `pipelines-data` `dashboards` · category browse · search "data warehouse, etl, bi" | ≥4 | BC-024 Data & Insight Evaluation | REQ-011 |
| **BP-019 Security Operations Evaluation** | docs topic `threat` `dlp` · security page topic `certifications` · product view in Security · search "edr, dlp, threat" | ≥4 | BC-025 Security Operations Evaluation | REQ-012 |

### Secondary associations (Table 3 — Concept → Requirement)

Cross-links keep the model honest about how these areas actually overlap. All
are Secondary or Supporting; each concept's Primary is the requirement above.

| Concept | Secondary | Supporting |
|---|---|---|
| CRM Evaluation | Marketing Execution | Workflow Automation |
| People Operations | Financial Management | Regulatory Compliance |
| Financial Evaluation | Regulatory Compliance | Workflow Automation |
| Marketing Evaluation | Data & Insight | AI Assistance |
| Engineering Delivery | Data & Insight | Workflow Automation |
| Data & Insight | AI Assistance | — |
| Security Operations | Regulatory Compliance | Identity Management |

---

## Table 4 — UI vocabulary (the link that is easiest to forget)

A pattern keyed on a topic no surface emits cannot fire from a browser. Today
**Salesforce's Docs tab reports its topic as `workflows`** and HubSpot's as
`api`, because those are the only words the product page knows.

Domain-specific capabilities must be matched **before** the generic automation
and AI entries, since first match wins and the specific term is the informative
one.

| Capability | Tab topic | Capability | Tab topic |
|---|---|---|---|
| Sales Pipeline | `pipeline` | Email Campaigns · Marketing Automation · Social | `campaigns` |
| Contact Management · Lead Scoring | `crm` | SEO Analytics | `seo` |
| Support Ticketing · Live Chat | `tickets` | A/B Testing | `experiments` |
| Payroll · Time & Attendance | `payroll` | CI/CD Pipelines | `cicd` |
| Applicant Tracking · Onboarding | `hiring` | Infra Monitoring · Log Mgmt | `monitoring` |
| Performance Reviews | `performance` | Incident Response | `incidents` |
| General Ledger | `accounting` | Container Orchestration | `containers` |
| Invoicing · Payment Processing | `billing` | ETL Pipelines | `pipelines-data` |
| Expense Management | `expenses` | Data Warehousing | `warehouse` |
| Budgeting & Forecasting | `forecasting` | Data Visualization | `dashboards` |
| Threat Protection | `threat` | Data Loss Prevention | `dlp` |

Simulated against the live catalog, this leaves **one** product falling through
to the generic `api` default, against 100+ today.

**Ordering needs one review pass.** Zendesk (Customer Support) resolves to
`pipeline` because it happens to hold Sales Pipeline; support-flavoured topics
should probably precede sales ones.

**Structural note:** this table is Domain Pack artifact 11 by contract, but it
currently lives in `apps/web/pages.py`. It should move into the pack as part of
this work rather than growing further in the wrong place.

### Buyer shorthand to add

`crm` → customer relationship management · `ats` → applicant tracking ·
`gl` → general ledger · `ap` / `ar` → accounts payable / receivable ·
`bi` → business intelligence · `etl` → data pipeline ·
`edr` → threat protection · `k8s` → container orchestration · `seo` → search optimization

---

## Table 5 — One existing pattern must be corrected first

**BP-002 Enterprise Evaluation activates on evidence that carries no meaning.**

It fires on any two of: admin/provisioning/federation docs · **enterprise
pricing tier opened** · compliance or audit page. The first and third genuinely
indicate identity and governance interest. The second does not: every product
in a marketplace has an enterprise tier, so opening one states *"I am buying for
a company"* — a fact about the buyer, not about what they need.

The concept maps **Primary** to Identity Management, on this documented
rationale (doc 06):

> Organizational adoption hinges first on centralized identity: enterprise
> evaluation behavior (admin documentation, provisioning, enterprise tiers) most
> strongly indicates an Identity Management need.

Sound when the catalog was ten identity, collaboration and automation products.
Unsound against a 250-product marketplace, and demonstrably so.

**Observed.** A shopper researching CRM (searched "crm" and "sales pipeline",
opened four CRM products, compared them, requested a demo) published an Identity
Management need at 0.55. The qualifying evidence at that run:

| Signal | Count |
|---|---|
| Enterprise plan opened | 4 |
| Admin / provisioning / federation docs | 0 |
| Compliance or audit page | 0 |

Four pricing clicks, no identity content, a Primary-strength identity need. Its
effect on the ranking was not marginal — it halved every CRM's score and lifted
Microsoft 365, which covers 0% of a CRM need, into a tie with Salesforce.

### Required change

**At least one administration signal — admin, provisioning or federation docs —
must be among the qualifying evidence.** Enterprise pricing tiers may
contribute strength, but cannot activate the pattern alone.

| Journey | Before | After |
|---|---|---|
| Identity shopper: provisioning docs + enterprise pricing | fires | fires (unchanged) |
| CRM shopper: four enterprise pricing clicks | fires → phantom identity need | does not fire |

Nothing is lost. Pricing behaviour is already read by BP-009 Commercial
Evaluation, which is the pattern that should own it — today the same click is
counted twice, once by the pattern that legitimately wants it and once by a
pattern drawing an unsupported conclusion from it.

**Every specified journey already satisfies the tightened rule.** Story 1 and
the multi-session enterprise stories supply provisioning, admin and federation
doc views; all three BP-002 unit tests include an admin or provisioning doc. The
only journeys that lose the pattern are the unspecified ones it was
misclassifying — which is the definition of a correction rather than a
regression, and the acceptance suite passing untouched is the proof.

### Why this belongs in *this* change

Twelve patterns instead of five multiplies the chances of exactly this failure.
Correcting the one live instance before adding seven more is the difference
between extending a sound model and scaling a known defect.

**Longer-term, still open:** company size is a buyer attribute, not a need. Ten
of the eighteen concepts are already marked *"deliberately unmapped: they inform
stage, constraints, ranking context, or hypothesis lifecycle — never
requirements."* Enterprise Evaluation arguably belongs in that group, with its
identity association dropped entirely rather than merely gated. That is a larger
argument and is not proposed here.

---

## What does not change

- Every engine — reasoning, confidence, requirement derivation, stage,
  matching, retrieval. They read the pack's tables; none names a capability.
- Every policy value. No threshold moves.
- The five original requirements and their capability sets.
- The canonical ten fixture products.
- The event registry — no new event types. All new signals are metadata values
  on existing types.
- The eleven other existing patterns. BP-002 is the single exception, and it
  tightens rather than broadens: every journey the specification describes still
  activates it.

---

## Known risks

**Cross-contamination gets easier, not harder.** Twelve patterns instead of five
means more ways for a stray click to manufacture a need. Table 5 corrects the
one live instance; the same discipline applies to all seven new patterns.
Activation conditions must be tight, and **mixed** journeys must be tested
deliberately, not just clean ones — a CRM shopper on HubSpot will also see
Marketing Automation capabilities, so CRM and marketing patterns will genuinely
compete.

**Ranking dilutes across published needs.** Overall coverage averages over every
published requirement. A shopper who triggers three needs will see lower
headline percentages than one who triggers a single need. Worth confirming the
displayed number still reads sensibly before this is demoed.

**Salesforce will not rank first on a CRM need, even once this is built.**
HubSpot beats it 80% to 60%, because the seed catalog gives Salesforce three of
the five CRM capabilities and HubSpot four. That is a catalog-authoring
question, not an engine one — but it should be settled deliberately rather than
discovered on stage.

---

## Delivery shape

Two commits, in this order:

1. **The BP-002 correction** (Table 5) on its own — a behaviour change to an
   existing pattern, with its own replay test and doc 02/06 amendment. Landing
   it first means the acceptance suite proves the correction in isolation,
   before seven new patterns make attribution harder.
2. **The extension** — pack code (concepts, patterns, requirements, both
   mappings, UI vocabulary), amended pack documents (01, 02, 04, 06, 07, 10,
   plus this one promoted from proposal to record), signature tests per pattern,
   at least one new derivation scenario with exact arithmetic, and a
   decision-log entry.

The proof that it is safe is that the existing twelve stories and four
derivation scenarios pass **without being edited**.
