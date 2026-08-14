# Business Requirement Catalog

**Version:** 1.0

---

# Purpose

The Business Requirement Catalog defines the complete set of canonical Business Requirements that exist within the Software Buying Domain.

Business Requirements represent reference knowledge.

They are not Runtime Objects.

They are not user-specific.

They do not change based on individual user behavior.

Requirement Profiles reference the Business Requirements defined by this catalog.

Requirement Profiles do not redefine Business Requirements—they identify which catalog entries currently apply to an individual user.

The catalog serves as the authoritative business vocabulary for user needs throughout the Software Buying Domain.

---

# Guiding Principle

The Business Requirement Catalog defines **what users may need**.

Requirement Profiles determine **which Business Requirements currently apply to an individual user**.

The catalog defines domain knowledge.

The Behavioral Intelligence Platform performs deterministic reasoning.

Business Requirements remain static.

Requirement Profiles evolve continuously as user behavior changes.

---

# Separation of Responsibilities

Behavioral Intelligence Platform

↓

Produces Behavioral Evidence

↓

Produces Behavioral Hypotheses

↓

Maintains Behavioral Memory

↓

Produces Requirement Profiles

↓

References

↓

Business Requirement Catalog

↓

Defines

↓

Canonical Business Requirements

↓

Product Capability Profiles

↓

Recommendation Engine

---

Requirement Profiles are Runtime Objects.

Business Requirements are reference knowledge.

Requirement Profiles reference Business Requirements rather than duplicating their definitions.

This separation allows Business Requirements to evolve independently while Requirement Profiles continue to represent each user's current business needs.

---

# Why This Separation Exists

The Business Requirement Catalog defines every Business Requirement only once.

Requirement Profiles reference those Business Requirements rather than storing duplicate copies.

For example:

Business Requirement Catalog

↓

REQ-001

Secure Collaboration

↓

Description

↓

Business Purpose

↓

Supporting Capabilities

↓

Related Requirements

↓

AI Explanation Contribution

------------------------------

Requirement Profile (Runtime Object)

↓

References

↓

REQ-001

REQ-004

REQ-005

The Runtime Object stores only the Requirement IDs that currently apply to an individual user.

The Business Requirement definitions remain centralized inside the Business Requirement Catalog.

This approach provides:

- Consistent business terminology
- No duplicated business knowledge
- Simplified catalog evolution
- Consistent AI explanations
- Deterministic requirement reasoning

---

# Relationship to Runtime Objects

The Business Requirement Catalog never contains Runtime Objects.

Instead, Runtime Objects reference the catalog whenever business knowledge is required.

Behavioral Evidence

↓

Behavioral Hypotheses

↓

Behavioral Memory

↓

Requirement Profile (Runtime Object)

↓

references

↓

Business Requirement Catalog

↓

defines

↓

Business Requirements

The catalog provides the semantic meaning.

The Runtime Object provides the current user state.

---

# Relationship to Other Domain Knowledge

The Software Buying Domain contains multiple forms of reference knowledge.

Behavioral Ontology

↓

Defines behavioral concepts

↓

Business Requirement Catalog

↓

Defines business needs

↓

Product Capability Profiles

↓

Defines product capabilities

Together these documents describe **what exists** within the Software Buying Domain.

The Behavioral Intelligence Platform determines **which concepts currently apply to an individual user** by producing Runtime Objects during execution.

---

# Scope

The Business Requirement Catalog defines:

- Canonical Business Requirements
- Business Requirement categories
- Business Requirement relationships
- Typical behavioral drivers
- Typical supporting capabilities
- Typical Journey Stages
- Business explanations used by the AI Buying Advisor

The Business Requirement Catalog does not define:

- Requirement Profiles
- Runtime Objects
- User-specific requirements
- Recommendation logic
- Decision Policies
- Product rankings
- AI reasoning
- Confidence values

---

# Business Requirement Definition

Every Business Requirement represents a single, reusable business need that may exist within the Software Buying Domain.

Business Requirements are static reference knowledge.

They never represent individual users.

They never contain Runtime Objects.

Requirement Profiles reference Business Requirements as users interact with the platform.

Every Business Requirement must contain the following sections.

---

## Requirement ID

A unique identifier for the Business Requirement.

Requirement IDs are stable across Domain Pack versions.

Example:

```text
REQ-001
```

Requirement Profiles reference Requirement IDs rather than duplicating Business Requirement definitions.

---

## Requirement Name

The canonical business name of the requirement.

Examples include:

- Secure Collaboration
- Identity Management
- Workflow Automation
- Regulatory Compliance

Business Requirement names remain stable and vendor-independent.

---

## Description

Defines the business need represented by the requirement.

Descriptions explain **what** the business requires rather than **how** a specific product fulfills that requirement.

---

## Business Purpose

Explains why the Business Requirement exists.

The Business Purpose provides business context independently of any product implementation.

---

## Typical Behavioral Drivers

Identifies Behavioral Concepts that commonly lead to this Business Requirement.

These mappings represent domain knowledge only.

Behavioral Intelligence Platform engines determine which Business Requirements apply to an individual user by producing Requirement Profiles.

Example:

```text
Security Evaluation

↓

Identity Management

↓

Secure Collaboration
```

Behavioral Concepts never directly recommend products.

---

## Typical Journey Stages

Identifies the Journey Stages where this Business Requirement most frequently appears.

Journey Stage determination is performed by the Journey Stage Engine.

The Business Requirement Catalog provides domain knowledge only.

Example:

```text
Evaluation

↓

Validation

↓

Purchase
```

---

## Typical Supporting Capabilities

Identifies Product Capabilities that commonly satisfy this Business Requirement.

These are capability references rather than product recommendations.

Example:

Secure Collaboration

↓

Typical Supporting Capabilities

- CAP-001 Single Sign-On
- CAP-002 Multi-Factor Authentication
- CAP-011 Encryption
- CAP-010 Audit Logging

The Capability Catalog (10) defines these capabilities canonically.

---

## Related Business Requirements

Defines Business Requirements that commonly occur together.

Example:

Secure Collaboration

↓

Related Requirements

- Identity Management
- Regulatory Compliance
- Data Protection

These relationships improve Requirement reasoning while remaining independent of Runtime Objects.

---

## AI Explanation Contribution

Provides reusable business explanation content used by the AI Buying Advisor when explaining why this Business Requirement became important for a particular user.

The catalog does not generate explanations.

Instead, it provides standardized business context that the AI Buying Advisor combines with Runtime Objects to produce user-specific explanations.

Example:

Business Requirement

↓

Secure Collaboration

↓

AI Explanation Contribution

"Secure Collaboration became a prioritized business requirement because the observed user behavior consistently emphasized protecting communication, securing organizational access, and enabling trusted collaboration across teams."

The AI Buying Advisor combines this explanation with Behavioral Evidence, Behavioral Hypotheses, and Requirement Profiles to generate personalized recommendation explanations.

---

# Requirement Categories

The Software Buying Domain currently defines six primary Business Requirement categories.

These categories organize Business Requirements.

They do not represent Runtime Objects.

---

## 1. Collaboration

Business Requirements that improve communication and teamwork.

Examples include:

- Secure Collaboration
- Team Communication
- Document Sharing
- Knowledge Sharing
- Video Meetings

---

## 2. Security

Business Requirements focused on protecting organizational identities, systems, and data.

Examples include:

- Identity Management
- Multi-Factor Authentication
- Single Sign-On
- Conditional Access
- Threat Protection

---

## 3. Compliance

Business Requirements supporting governance and regulatory obligations.

Examples include:

- Regulatory Compliance
- Audit Logging
- Data Residency
- eDiscovery
- Information Governance

---

## 4. Productivity

Business Requirements that improve operational efficiency.

Examples include:

- Workflow Automation
- AI Assistance
- Task Management
- Process Optimization
- Content Creation

---

## 5. Administration

Business Requirements supporting IT operations and centralized management.

Examples include:

- User Provisioning
- License Management
- Device Management
- Policy Management
- Central Administration

---

## 6. Analytics

Business Requirements focused on visibility, reporting, and decision support.

Examples include:

- Reporting
- Dashboards
- Adoption Analytics
- Usage Monitoring
- Business Intelligence

---

# Relationship Between Categories and Requirements

Business Requirement Categories organize Business Requirements.

Individual Business Requirements remain independent.

Example:

Security

↓

- Identity Management

- Multi-Factor Authentication

- Single Sign-On

- Conditional Access

- Threat Protection

Requirement Profiles reference individual Business Requirements rather than entire categories.

Categories exist solely to organize the Business Requirement Catalog.

---

# Canonical Business Requirements

Every Business Requirement is uniquely identified by a Requirement ID.

Requirement Profiles reference these IDs rather than duplicating the Business Requirement definition.

This ensures consistent business knowledge across all users while allowing Requirement Profiles to evolve independently as Runtime Objects.

The following examples establish the canonical structure used throughout the Software Buying Domain.

---

# REQ-001 — Secure Collaboration

## Description

Enable secure communication and collaboration between individuals, teams, and organizations while protecting business information.

---

## Business Purpose

Support productive collaboration without compromising organizational security, governance, or trust.

---

## Typical Behavioral Drivers

- BC-005 Collaboration Evaluation
- BC-001 Security Evaluation
- BC-004 Compliance Evaluation

---

## Typical Journey Stages

- Research
- Technical Validation
- Decision

---

## Typical Supporting Capabilities

- CAP-001 Single Sign-On
- CAP-002 Multi-Factor Authentication
- CAP-007 Document Collaboration
- CAP-010 Audit Logging
- CAP-011 Encryption

---

## Related Business Requirements

- Identity Management
- Regulatory Compliance

---

## AI Explanation Contribution

Provide business justification explaining that secure communication and protected collaboration became important based on the user's observed behavior.

---

# REQ-002 — Identity Management

## Description

Provide centralized authentication, authorization, and identity lifecycle management for users and organizations.

---

## Business Purpose

Reduce security risk while simplifying user access across business applications.

---

## Typical Behavioral Drivers

- BC-001 Security Evaluation
- BC-002 Enterprise Evaluation
- BC-009 Technical Evaluation

---

## Typical Journey Stages

- Discovery
- Research
- Technical Validation

---

## Typical Supporting Capabilities

- CAP-001 Single Sign-On
- CAP-002 Multi-Factor Authentication
- CAP-003 SCIM Provisioning
- CAP-004 Conditional Access
- CAP-008 Identity Federation

---

## Related Business Requirements

- Secure Collaboration
- Regulatory Compliance

---

## AI Explanation Contribution

Provide business context explaining that centralized identity and secure authentication emerged as an important organizational requirement.

---

# REQ-003 — Workflow Automation

## Description

Automate repetitive business processes to improve operational efficiency and reduce manual work.

---

## Business Purpose

Increase productivity while improving consistency and scalability.

---

## Typical Behavioral Drivers

- BC-006 Productivity Evaluation
- BC-007 Automation Evaluation
- BC-008 Integration Evaluation

---

## Typical Journey Stages

- Research
- Technical Validation
- Decision

---

## Typical Supporting Capabilities

- CAP-015 Workflow Automation
- CAP-016 Integration Connectors
- CAP-017 Event Triggers
- CAP-018 Business Rules
- CAP-019 API Integration

---

## Related Business Requirements

- Process Optimization
- AI Assistance

---

## AI Explanation Contribution

Provide business context explaining that repeated evaluation of automation capabilities indicates a strong operational efficiency objective.

---

# REQ-004 — Regulatory Compliance

## Description

Support organizational compliance with legal, regulatory, and governance obligations.

---

## Business Purpose

Reduce compliance risk while satisfying internal and external governance requirements.

---

## Typical Behavioral Drivers

- BC-004 Compliance Evaluation
- BC-001 Security Evaluation
- BC-002 Enterprise Evaluation

---

## Typical Journey Stages

- Research
- Technical Validation

---

## Typical Supporting Capabilities

- CAP-010 Audit Logging
- CAP-012 Information Governance
- CAP-013 Data Retention
- CAP-014 eDiscovery
- CAP-027 Compliance Reporting

---

## Related Business Requirements

- Secure Collaboration
- Identity Management
- Data Protection

---

## AI Explanation Contribution

Provide business context explaining that governance and regulatory obligations became a significant factor during product evaluation.

---

# REQ-005 — AI Assistance

## Description

Improve user productivity through intelligent assistance, content generation, summarization, and workflow support.

---

## Business Purpose

Increase efficiency while reducing repetitive manual effort.

---

## Typical Behavioral Drivers

- BC-003 AI Evaluation
- BC-006 Productivity Evaluation
- BC-013 Feature Evaluation

---

## Typical Journey Stages

- Discovery
- Research
- Decision

---

## Typical Supporting Capabilities

- CAP-020 AI Chat
- CAP-021 Content Generation
- CAP-022 Intelligent Search
- CAP-023 Document Summarization
- CAP-024 AI Workflow Assistance

---

## Related Business Requirements

- Workflow Automation
- Knowledge Management

---

## AI Explanation Contribution

Provide business context explaining that repeated evaluation of intelligent productivity capabilities indicates interest in AI-assisted work.

---

# Catalog Evolution

New Business Requirements may be introduced through future Domain Pack versions.

Existing Requirement IDs remain stable across versions.

Requirement definitions may evolve to reflect changing business needs while preserving backward compatibility.

Requirement Profiles continue referencing Requirement IDs independently of catalog evolution.

Business Requirements remain implementation-independent.

They never reference:

- Vendors
- Products
- Pricing
- Recommendation logic
- Decision Policies
- Runtime Objects

The Business Requirement Catalog defines **what business needs exist**.

Product Capability Profiles define **how products satisfy those needs**.

# Requirement Invariants

The following rules must always hold.

## Invariant 1

Business Requirements are static reference knowledge.

Business Requirements evolve only through new Domain Pack versions.

---

## Invariant 2

Business Requirements are never Runtime Objects.

Requirement Profiles are Runtime Objects.

Requirement Profiles reference Business Requirements.

---

## Invariant 3

Business Requirements never contain user-specific information.

Individual user needs exist only within Requirement Profiles.

---

## Invariant 4

Business Requirements never contain confidence.

Confidence belongs exclusively to Requirement Profiles.

---

## Invariant 5

Business Requirements never contain recommendation logic.

The Recommendation Engine performs capability matching.

Decision Policies authorize recommendations.

The Business Requirement Catalog defines business knowledge only.

---

## Invariant 6

Business Requirements remain implementation-independent.

Business Requirements never reference:

- Vendors
- Products
- Pricing
- Licensing
- Recommendation logic
- Decision Policies
- Runtime Objects

---

# Relationship to the Behavioral Intelligence Platform

The Behavioral Intelligence Platform produces Requirement Profiles.

Requirement Profiles reference Business Requirements.

Business Requirements provide the semantic meaning used during recommendation generation.

Behavioral Evidence

↓

Behavioral Hypotheses

↓

Behavioral Memory

↓

Requirement Profile (Runtime Object)

↓

references

↓

Business Requirement Catalog

↓

provides semantic meaning

↓

Product Capability Profiles

↓

Recommendation Engine

↓

Recommendation Package

↓

AI Buying Advisor

The Behavioral Intelligence Platform owns Runtime Objects.

The Business Requirement Catalog owns business knowledge.

Together they enable deterministic requirement reasoning while maintaining complete separation between reference knowledge and runtime state.

---

# Relationship to Other Reference Knowledge

The Software Buying Domain consists of three complementary forms of reference knowledge.

Behavioral Ontology

↓

Defines behavioral concepts

↓

Business Requirement Catalog

↓

Defines business needs

↓

Product Capability Profiles

↓

Defines product capabilities

Each document owns a distinct aspect of domain knowledge.

No document duplicates another.

The Behavioral Intelligence Platform consumes these reference documents while producing Runtime Objects during execution.

---

# Claude Implementation Contract

Claude MUST:

- Treat the Business Requirement Catalog as static reference knowledge.
- Keep Business Requirements independent from Runtime Objects.
- Allow Requirement Profiles to reference Business Requirements.
- Keep Business Requirements vendor-independent.
- Keep Business Requirements product-independent.
- Keep recommendation logic outside the Business Requirement Catalog.
- Preserve clear separation between business knowledge and runtime reasoning.
- Allow new Business Requirements to be added without modifying the Behavioral Intelligence Platform.

Claude MUST NOT:

- Store Runtime Objects.
- Store user-specific information.
- Store confidence values.
- Store recommendation logic.
- Store Decision Policies.
- Store product rankings.
- Perform deterministic reasoning.
- Modify Requirement Profiles.

---

# Future Evolution

Future Domain Pack versions may introduce additional Business Requirements.

Business Requirement definitions may evolve while preserving stable Requirement IDs.

Future Business Requirements should follow the Business Requirement Definition defined in this document.

Requirement Profiles remain independent from catalog evolution.

The Business Requirement Catalog continues defining **what business needs exist**.

The Behavioral Intelligence Platform determines **which Business Requirements currently apply to an individual user**.

Product Capability Profiles define **how products satisfy those Business Requirements**.

Recommendation Packages communicate **which products best satisfy those needs**.

---

# v1.2 Extension — REQ-006 … REQ-012

Added with doc 14. The five requirements above were authored against a
ten-product roster; the catalog then grew to 55 capabilities for the wide demo
roster, and those five reach only 21 of them. The consequence was not
theoretical: **82 of the 250 catalog products held no capability any requirement
named**, so they could be searched, viewed and added to a cart but never
recommended, because coverage scoring had nothing to score them on.

These seven complete the coverage. REQ-001 … REQ-005 are unchanged — their
capability sets are the denominators of the derivations in doc 09, so new
capabilities join new requirements only.

| ID | Requirement | Business meaning | Capabilities (doc 07) |
|---|---|---|---|
| REQ-006 | **Sales & Customer Management** | Keep customer relationships and deal progress in one governed system of record | Sales Pipeline · Contact Management *(Primary)* · Lead Scoring · Support Ticketing *(Secondary)* · Live Chat *(Supporting)* |
| REQ-007 | **People Operations** | Run the employee lifecycle — hiring, onboarding, pay and performance | Payroll · Applicant Tracking *(Primary)* · Onboarding · Time & Attendance *(Secondary)* · Performance Reviews *(Supporting)* |
| REQ-008 | **Financial Management** | Keep the books, bill customers and control spend | General Ledger · Invoicing *(Primary)* · Expenses · Payments *(Secondary)* · Budgeting *(Supporting)* |
| REQ-009 | **Marketing Execution** | Reach an audience and measure whether the reach worked | Marketing Automation · Email Campaigns *(Primary)* · Social · SEO *(Secondary)* · A/B Testing *(Supporting)* |
| REQ-010 | **Engineering Delivery** | Ship software and keep it running | CI/CD · Infrastructure Monitoring *(Primary)* · Logs · Incident Response *(Secondary)* · Containers *(Supporting)* |
| REQ-011 | **Data & Insight** | Consolidate data and get answers out of it | Data Warehousing · ETL *(Primary)* · Visualization · Intelligent Search *(Secondary)* · API Integration *(Supporting)* |
| REQ-012 | **Security Operations** | Detect threats and stop information leaving | Threat Protection · Data Loss Prevention *(Primary)* · Compliance Reporting *(Secondary)* · Identity Federation *(Supporting)* |

---

# v1.5 Extension — REQ-013

| ID | Requirement | What the buyer is trying to do | Capabilities |
|---|---|---|---|
| REQ-013 | **Work Management** | Plan, assign and track a team's work, and see who has capacity for more | Task Management *(Primary)* · Workload Management *(Secondary)* · Template Library *(Supporting)* |

**Why REQ-013 exists.** Task Management, Workload Management and Template
Library were the last three capabilities in the catalog that reached no
requirement at all, so a product holding only them could be searched, viewed and
added to a cart but never recommended. They are not three strays from three
different domains — the Capability Catalog already files them together under a
**Work Management** domain of its own, which is the whole argument for one
requirement rather than three rehomings (Decision #079).

**Why there is no Productivity requirement beside it.** The obvious second
candidate was Productivity, since the catalog carries a Productivity category of
17 products. It is not a subject anybody shops for: 16 of those 17 hold Workload
Management, and they hold it because the seed generator stamped it on them
indiscriminately. Strip that one capability and the shelf is automation,
collaboration, marketing and AI products with nothing in common. A requirement
built on it would answer a question no shopper asks.

**Decision #080 went further and dissolved the category**, redistributing all
seventeen by what they hold: eight to a new AI category, four to Workflow
Automation, two to Collaboration, one to Marketing, and Calendly and Todoist to
Work Management. Leaving the shelf in place would have been worse than leaving
it unmapped, because BC-006 claimed it: browsing Grammarly Business declared a
work-management intent its shopper never had.

**Why REQ-012 exists.** Four capabilities were stranded inside the *original*
domains — Threat Protection, Data Loss Prevention, Compliance Reporting and
Identity Federation belong to Security, Compliance and Identity, but no
requirement named them. Housing them in a new requirement reaches them without
editing a frozen capability set.

**Why REQ-011 carries two capabilities from outside its domain.** Data &
Analytics holds only three capabilities, and 21 catalog products hold all three
— a requirement built from them alone produced a 21-way tie at 100%, a ranking
that is correct and useless. Intelligent Search and API Integration are
genuinely part of getting insight out of data, and they discriminate.
`test_seed_catalog` now pins the general rule: no requirement may be fully
covered by more products than a Candidate Set can hold.

**Still unmapped:** File Sharing and AI Workflow Assistance. Both belong to
existing requirements' domains, so mapping them would edit a frozen set and move
the pinned derivations. No product is stranded by leaving them out — every
product holding either also holds something mapped — so this is deliberately
left as a separate decision.

---

# Summary

The Business Requirement Catalog provides the canonical business vocabulary used throughout the Software Buying Domain.

Business Requirements represent shared business knowledge.

Requirement Profiles represent user-specific Runtime Objects.

Requirement Profiles reference Business Requirements rather than redefining them.

This separation ensures:

- Consistent business terminology
- Reusable business knowledge
- Deterministic requirement reasoning
- Independent catalog evolution
- Consistent AI explanations
- Clear separation between reference knowledge and runtime state

The Business Requirement Catalog serves as the bridge between behavioral understanding and product capability matching, enabling the Behavioral Intelligence Platform to transform observed user behavior into meaningful business needs while remaining completely independent of vendors, products, and recommendation logic.

---