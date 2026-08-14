"""Software Buying Domain Pack v1 — canonical reference knowledge.

One-to-one transcription of docs/domains/software-buying/:
  01 Behavioral Ontology (BC registry) · 02 Behavioral Patterns (BP-001…019)
  04 Business Requirement Catalog (REQ-001…012) · 10 Capability Catalog (55)
  06 BC→REQ mapping · 07 REQ→CAP mapping · 00 §4.1 Stage Milestones
  05 Product Capability Profiles (canonical roster PROD-001…010)

Reference knowledge is immutable during execution and never redefined by
Runtime Objects (doc 09, Principles 4-5). Pattern activation thresholds are
Domain Pack v1 values (doc 02: "the numbers are their v1 defaults").
"""

from smartreco.domain.software_buying.patterns import (
    ADOPTION_DOC_TOPICS, BP011_TRIGGERS, DOMAIN_RESEARCH_PATTERNS, INTENT_CONCEPTS,
    SUBJECTS_WITH_OWN_EVALUATOR)

DOMAIN_PACK_VERSION = "1.6"   # v1.6 adds the content & knowledge vocabulary and
                              # REQ-014 built from it (Decision #081)

# ---- Behavioral Concept Registry (doc 01) ----

BEHAVIORAL_CONCEPTS: dict[str, str] = {
    "BC-001": "Security Evaluation",
    "BC-002": "Enterprise Evaluation",
    "BC-003": "AI Evaluation",
    "BC-004": "Compliance Evaluation",
    "BC-005": "Collaboration Evaluation",
    "BC-006": "Productivity Evaluation",
    "BC-007": "Automation Evaluation",
    "BC-008": "Integration Evaluation",
    "BC-009": "Technical Evaluation",
    "BC-010": "Commercial Evaluation",
    "BC-011": "Product Discovery",
    "BC-012": "Product Affinity",
    "BC-013": "Feature Evaluation",
    "BC-014": "Pricing Sensitivity",
    "BC-015": "Adoption Readiness",
    "BC-016": "Decision Confidence",
    "BC-017": "Preference Reinforcement",
    "BC-018": "Preference Reversal",
    # v1.2 (doc 14): one concept per catalog domain that previously had no way
    # to be understood. Each answers "what is this person trying to buy", so
    # each maps Primary to a requirement — the side of the line Decision #050
    # drew.
    "BC-019": "CRM Evaluation",
    "BC-020": "People Operations Evaluation",
    "BC-021": "Financial Evaluation",
    "BC-022": "Marketing Evaluation",
    "BC-023": "Engineering Delivery Evaluation",
    "BC-024": "Data & Insight Evaluation",
    "BC-025": "Security Operations Evaluation",
    # v1.4 subjects (Decision #077). Identity and compliance products were two of
    # the ten categories a shopper could browse without the platform forming any
    # idea of what they were shopping for. Distinct from BC-001 and BC-004, which
    # are the *lenses* of the same names: checking a candidate's security posture
    # is not the same act as shopping for an identity platform, and conflating
    # them is what POL-REQ-004 exists to separate.
    "BC-026": "Identity Platform Evaluation",
    "BC-027": "Compliance Programme Evaluation",
    # v1.6 (Decision #081). Content Management, Knowledge & Docs and Design were
    # the last three categories a shopper could browse without the platform
    # forming any idea of what they wanted — 22 products between them.
    "BC-028": "Content & Knowledge Evaluation",
}

# ---- Business Requirement Catalog (doc 04) ----

REQUIREMENTS: dict[str, str] = {
    "REQ-001": "Secure Collaboration",
    "REQ-002": "Identity Management",
    "REQ-003": "Workflow Automation",
    "REQ-004": "Regulatory Compliance",
    "REQ-005": "AI Assistance",
    # v1.2 (doc 14). The catalog grew to 55 capabilities for the wide demo
    # roster, but the five requirements above reach only 21 of them — so 82 of
    # 250 products were searchable, viewable, and unrecommendable. These seven
    # cover the rest. REQ-001…005 are deliberately untouched: their capability
    # sets are the denominators of doc 09's pinned derivations.
    "REQ-006": "Sales & Customer Management",
    "REQ-007": "People Operations",
    "REQ-008": "Financial Management",
    "REQ-009": "Marketing Execution",
    "REQ-010": "Engineering Delivery",
    "REQ-011": "Data & Insight",
    "REQ-012": "Security Operations",
    # v1.5 (Decision #079). The last three capabilities that reached no
    # requirement — Task Management, Template Library, Workload Management —
    # are one coherent group, and the capability catalog already said so by
    # filing them under a "Work Management" domain of their own. This is that
    # domain's requirement.
    "REQ-013": "Work Management",
    # v1.6 (Decision #081). Documents, knowledge and design assets are one need:
    # keep what the organisation knows findable, shareable and reusable.
    "REQ-014": "Content & Knowledge",
}

# ---- Product categories (doc 05; Law 7 — closed enums) ----
#
# Category was the last free-text categorical value in the pack, and it is not a
# label: SUBJECT_CATEGORIES matches against it, so a typo silently makes a
# product off-subject for every shopper, and an invented category makes it
# off-subject permanently. Decisions #079-#081 each turned on a category being
# wrong, and none of them could have been caught by a test while the set was
# open (Decision #083).
PRODUCT_CATEGORIES: frozenset[str] = frozenset({
    "AI",
    "CRM",
    "Collaboration",
    "Compliance",
    "Content Management",
    "Customer Support",
    "Data & Analytics",
    "Design",
    "DevOps",
    "Finance",
    "HR",
    "Identity & Access Management",
    "Knowledge & Docs",
    "Marketing",
    "Productivity & Collaboration",
    "Security",
    "Work Management",
    "Workflow Automation",
})

# ---- Capability Catalog (doc 10 — 27 capabilities, 6 domains) ----
# (capability_id, name, domain, business_value_narrative)

CAPABILITIES: list[tuple[str, str, str, str]] = [
    ("CAP-001", "Single Sign-On", "Identity & Access",
     "Provides centralized authentication that simplifies user access while improving organizational security."),
    ("CAP-002", "Multi-Factor Authentication", "Identity & Access",
     "Materially reduces account-compromise risk by requiring proof beyond a password."),
    ("CAP-003", "SCIM Provisioning", "Identity & Access",
     "Automates identity lifecycle management, reducing manual IT effort and orphaned-account risk."),
    ("CAP-004", "Conditional Access", "Identity & Access",
     "Enforces the right level of access under the right conditions without blocking productivity."),
    ("CAP-005", "Messaging", "Collaboration",
     "Keeps team communication fast, organized, and searchable."),
    ("CAP-006", "Video Meetings", "Collaboration",
     "Enables face-to-face collaboration for distributed teams."),
    ("CAP-007", "Document Collaboration", "Collaboration",
     "Removes versioning friction by letting teams work in the same document simultaneously."),
    ("CAP-008", "Identity Federation", "Identity & Access",
     "Connects existing identity investments instead of forcing migration, easing enterprise adoption."),
    ("CAP-009", "File Sharing", "Collaboration",
     "Provides governed, permission-aware distribution of business content."),
    ("CAP-010", "Audit Logging", "Compliance",
     "Provides the traceability foundation required for governance, forensics, and regulatory audits."),
    ("CAP-011", "Encryption", "Security",
     "Protects business information even when infrastructure or transport is compromised."),
    ("CAP-012", "Information Governance", "Compliance",
     "Ensures information is handled according to its sensitivity throughout its lifecycle."),
    ("CAP-013", "Data Retention", "Compliance",
     "Keeps what regulation requires and disposes of what it doesn't — defensibly."),
    ("CAP-014", "eDiscovery", "Compliance",
     "Turns legal discovery from a scramble into a governed, repeatable process."),
    ("CAP-015", "Workflow Automation", "Automation",
     "Converts repetitive manual processes into reliable automated workflows."),
    ("CAP-016", "Integration Connectors", "Automation",
     "Connects the existing application landscape without custom integration projects."),
    ("CAP-017", "Event Triggers", "Automation",
     "Lets processes react to the business in real time instead of on a schedule."),
    ("CAP-018", "Business Rules", "Automation",
     "Encodes business policy into automation so decisions stay consistent and auditable."),
    ("CAP-019", "API Integration", "Automation",
     "Provides the extensibility surface engineering teams require for custom integration."),
    ("CAP-020", "AI Chat", "Artificial Intelligence",
     "Gives every user an assistant that answers questions in context."),
    ("CAP-021", "Content Generation", "Artificial Intelligence",
     "Accelerates content creation by turning intent into a working first draft."),
    ("CAP-022", "Intelligent Search", "Artificial Intelligence",
     "Finds what users mean, not just what they typed."),
    ("CAP-023", "Document Summarization", "Artificial Intelligence",
     "Compresses long content into decision-ready summaries."),
    ("CAP-024", "AI Workflow Assistance", "Artificial Intelligence",
     "Lowers the skill barrier for automation by letting AI help design the workflow."),
    ("CAP-025", "Threat Protection", "Security",
     "Reduces breach likelihood through active detection rather than passive defense."),
    ("CAP-026", "Data Loss Prevention", "Security",
     "Stops sensitive information from leaking through everyday collaboration channels."),
    ("CAP-027", "Compliance Reporting", "Compliance",
     "Makes compliance status visible and demonstrable to auditors and leadership."),
    # ---- v1.1 extension (append-only; new domains so wide-catalog products
    # express themselves honestly — data-model §Catalog Seed Strategy).
    #
    # v1.1 left these out of every REQ→CAP mapping deliberately: the wide catalog
    # was scenery, "realistic noise retrieval and matching must cut through". The
    # cost was 82 of 250 products that could be searched and viewed but never
    # recommended, so v1.2 (doc 14) covers them with REQ-006…012. Two remain
    # unmapped on purpose — File Sharing and AI Workflow Assistance sit inside
    # frozen requirements' domains, and no product depends on them to be
    # reachable. ----
    ("CAP-028", "Contact Management", "CRM",
     "Keeps every customer relationship and its history in one governed record."),
    ("CAP-029", "Sales Pipeline", "CRM",
     "Makes deal progress visible and forecastable across the whole team."),
    ("CAP-030", "Lead Scoring", "CRM",
     "Focuses selling time on the prospects most likely to convert."),
    ("CAP-031", "Customer Support Ticketing", "CRM",
     "Turns customer issues into tracked, accountable work."),
    ("CAP-032", "Live Chat", "CRM",
     "Meets customers in the moment questions arise."),
    ("CAP-033", "Applicant Tracking", "HR",
     "Moves candidates through hiring stages without spreadsheet chaos."),
    ("CAP-034", "Onboarding Workflows", "HR",
     "Gets new hires productive with a repeatable first-week experience."),
    ("CAP-035", "Payroll Processing", "HR",
     "Pays people correctly and on time, every cycle."),
    ("CAP-036", "Time & Attendance", "HR",
     "Captures worked time accurately for payroll and compliance."),
    ("CAP-037", "Performance Reviews", "HR",
     "Structures feedback into fair, documented growth conversations."),
    ("CAP-038", "Invoicing", "Finance",
     "Gets bills out fast and keeps receivables collectable."),
    ("CAP-039", "Expense Management", "Finance",
     "Captures and approves spend without paper or surprises."),
    ("CAP-040", "General Ledger", "Finance",
     "Keeps the books authoritative, auditable, and closeable."),
    ("CAP-041", "Budgeting & Forecasting", "Finance",
     "Turns plans into numbers the business can steer by."),
    ("CAP-042", "Payment Processing", "Finance",
     "Accepts payments reliably across channels and currencies."),
    ("CAP-043", "Email Campaigns", "Marketing",
     "Reaches audiences with targeted, measurable email programs."),
    ("CAP-044", "Marketing Automation", "Marketing",
     "Nurtures leads automatically through journey-based campaigns."),
    ("CAP-045", "Social Media Management", "Marketing",
     "Plans, publishes, and measures social presence from one place."),
    ("CAP-046", "SEO Analytics", "Marketing",
     "Shows how search visibility converts into traffic and revenue."),
    ("CAP-047", "A/B Testing", "Marketing",
     "Replaces opinions with measured winners."),
    ("CAP-048", "CI/CD Pipelines", "DevOps",
     "Ships code changes safely and continuously."),
    ("CAP-049", "Infrastructure Monitoring", "DevOps",
     "Sees outages coming before customers do."),
    ("CAP-050", "Log Management", "DevOps",
     "Makes production behavior searchable when it matters most."),
    ("CAP-051", "Incident Response", "DevOps",
     "Turns outages into coordinated, learnable events."),
    ("CAP-052", "Container Orchestration", "DevOps",
     "Runs workloads reliably at any scale."),
    ("CAP-053", "Data Visualization", "Data & Analytics",
     "Turns raw data into decisions people can see."),
    ("CAP-054", "ETL Pipelines", "Data & Analytics",
     "Moves and shapes data dependably between systems."),
    ("CAP-055", "Data Warehousing", "Data & Analytics",
     "Gives analytics one fast, governed home for enterprise data."),
    # ---- v1.3 extension (append-only). Work Management had a product category,
    # 31 products, and no capabilities of its own — so a task tool's docs tab
    # described itself with whatever generic capability it happened to hold, and
    # BP-006's productivity/templates/tasks vocabulary was unreachable from any
    # page (Decision #053). ----
    ("CAP-056", "Task Management", "Work Management",
     "Turns intent into assigned, trackable work with clear ownership and due dates."),
    ("CAP-058", "Workload Management", "Work Management",
     "Makes capacity visible so commitments match the team that has to deliver them."),
    # ---- v1.3 extension: security operations vocabulary (Decision #074) ----
    #
    # Security Operations was the only subject area described by two purpose-built
    # capabilities where People Operations and Engineering Delivery had five. The
    # cost was that the pack could not tell an endpoint-security product from a
    # password manager: CrowdStrike Falcon and SentinelOne each held exactly
    # Encryption, Threat Protection and Data Loss Prevention — identical to one
    # another and a strict subset of LastPass's eight — so a shopper researching
    # endpoint security was correctly routed to the Security category and then
    # ranked below products that merely held more of the same three.
    #
    # These four say what a security-operations product actually does, and none
    # of them is something a suite acquires by being large.
    ("CAP-059", "Endpoint Detection & Response", "Security",
     "Catches the attack already inside the estate, on the device where it lands, "
     "and gives responders somewhere to act."),
    ("CAP-060", "Threat Intelligence", "Security",
     "Turns what is known about attackers elsewhere into defenses that are already "
     "in place when they arrive here."),
    ("CAP-061", "Security Monitoring", "Security",
     "Collects and correlates security signal continuously, so detection does not "
     "depend on someone happening to look."),
    ("CAP-062", "Vulnerability Management", "Security",
     "Finds the exposures before an attacker does and puts them in an order somebody "
     "can actually work through."),
    # ---- v1.6 extension: content & knowledge vocabulary (Decision #081) ----
    #
    # Twenty-two products across Content Management, Knowledge & Docs and Design
    # could be browsed without the platform forming any idea of what was wanted,
    # and the requirement that would fix it could not be written: the Collaboration
    # domain holds four capabilities and not one of them is about content. Every
    # set built from it was fully covered by 14 to 24 products against a Candidate
    # Set of 8 — a requirement that cannot discriminate is as useless as one no
    # product satisfies.
    #
    # So this is #074's move again: give the subject area a vocabulary of its own
    # rather than borrowing one. Template Library comes with them — it arrived
    # beside Task Management and Workload Management and was filed with them, but
    # reusing a proven structure is a content idea, not a scheduling one.
    ("CAP-057", "Template Library", "Content & Knowledge",
     "Removes the blank page: proven structures are reused instead of reinvented."),
    ("CAP-063", "Knowledge Base", "Content & Knowledge",
     "Keeps what the organisation knows in one searchable place instead of in "
     "the heads of the people who happen to know it."),
    ("CAP-064", "Content Versioning", "Content & Knowledge",
     "Every change is recoverable, so people edit the current document instead of "
     "mailing copies of it."),
    ("CAP-065", "Digital Asset Management", "Content & Knowledge",
     "Finds the right image, video or design file without asking the person who "
     "made it."),
]

# ---- Buyer shorthand (doc 10 § Buyer Shorthand) ----
# Transcription of the Domain Pack's alias table — amend the doc and this map
# together. Entries exist only where the shorthand shares no usable prefix with
# the capability name; "scim" and "ediscovery" need none. Expansion is a
# retrieval convenience only: the SEARCH event always records what the shopper
# actually typed, so the BRE never sees vocabulary the user did not use.
# Consuming surface and ranking: ui-design-spec §4.7a.

SEARCH_ALIASES: dict[str, str] = {
    "sso": "single sign on",
    "mfa": "multi factor authentication",
    "2fa": "multi factor authentication",
    "saml": "identity federation",
    "oidc": "identity federation",
    "iam": "identity access management",
    "rbac": "conditional access",
    "dlp": "data loss prevention",
    # Was "audit logging" while the pack had no security-monitoring capability to
    # point at; a shopper searching SIEM was answered with compliance logging.
    "siem": "security monitoring",
    "cicd": "ci cd pipelines",
}

# ---- BC → REQ Mapping (doc 06 — association levels feed POL-REQ-003) ----
# {bc_id: {req_id: association_level}}

BC_TO_REQ: dict[str, dict[str, str]] = {
    "BC-001": {"REQ-002": "Primary", "REQ-001": "Secondary", "REQ-004": "Supporting"},
    # Enterprise Evaluation states the buyer's scale, not their need (Decision
    # #050). Its Primary link to Identity Management was removed: organizational
    # adoption does not imply identity software — an HR buyer reading a
    # provisioning page is still buying HR software. Governance obligations do
    # follow from scale, so the Secondary link to Regulatory Compliance stays,
    # and at Secondary weight it can support a requirement without ever
    # publishing one alone.
    "BC-002": {"REQ-004": "Secondary"},
    "BC-003": {"REQ-005": "Primary", "REQ-003": "Secondary", "REQ-001": "Supporting"},
    "BC-004": {"REQ-004": "Primary", "REQ-002": "Secondary", "REQ-001": "Supporting"},
    "BC-005": {"REQ-001": "Primary", "REQ-002": "Supporting"},
    # v1.5 (Decision #079). Productivity Evaluation was Primary to AI Assistance,
    # which is the mis-anchoring this phase exists to remove: BP-006 fires on
    # documentation about templates and tasks and on searches for the same, and
    # none of that is evidence that a shopper wants an AI assistant. It was a
    # proxy standing in for a requirement the pack could not express. REQ-013
    # is that requirement — Template Library and Task Management are literally
    # its capabilities — so the association moves there and the AI link goes
    # rather than being demoted, because it was never weak evidence, it was the
    # wrong evidence. The Workflow Automation link survives on its own merits.
    "BC-006": {"REQ-013": "Primary", "REQ-003": "Supporting"},
    "BC-007": {"REQ-003": "Primary", "REQ-005": "Secondary"},
    "BC-008": {"REQ-003": "Primary", "REQ-002": "Secondary"},
    # BC-009…BC-018 deliberately unmapped (doc 06): they inform stage,
    # constraints, ranking context, or hypothesis lifecycle — never requirements.
    # BC-002 joined them for its identity association in Decision #050.
    #
    # v1.2 (doc 14 Tables 2 and 3). Secondary and Supporting links express how
    # these areas genuinely overlap — a CRM buyer is often also buying
    # marketing reach; an engineering buyer often also wants the data out. They
    # are kept deliberately sparse: every extra link is another way for one
    # journey's evidence to publish another journey's need.
    "BC-019": {"REQ-006": "Primary", "REQ-009": "Secondary", "REQ-003": "Supporting"},
    "BC-020": {"REQ-007": "Primary", "REQ-008": "Secondary", "REQ-004": "Supporting"},
    "BC-021": {"REQ-008": "Primary", "REQ-004": "Secondary", "REQ-003": "Supporting"},
    "BC-022": {"REQ-009": "Primary", "REQ-011": "Secondary", "REQ-005": "Supporting"},
    "BC-023": {"REQ-010": "Primary", "REQ-011": "Secondary", "REQ-003": "Supporting"},
    "BC-024": {"REQ-011": "Primary", "REQ-005": "Secondary"},
    "BC-025": {"REQ-012": "Primary", "REQ-004": "Secondary", "REQ-002": "Supporting"},
    # v1.4 (Decision #077): the subject forms of two needs the pack could already
    # express but only ever inferred from vetting behaviour.
    # No Supporting link to Secure Collaboration: shopping for an identity
    # platform says nothing about wanting collaboration software, and inventing
    # the association published a requirement doc 09 Scenario 1 holds below the
    # publication floor.
    "BC-026": {"REQ-002": "Primary"},
    "BC-027": {"REQ-004": "Primary", "REQ-002": "Supporting"},
    # v1.6 (Decision #081). One Supporting link only, and it is the honest one:
    # documents are worked on together, so a content shopper does acquire a
    # collaboration question. No link to Regulatory Compliance, tempting as it
    # is — records retention is REQ-004's subject, and giving this requirement
    # a route into it is how one journey's evidence publishes another's need.
    "BC-028": {"REQ-014": "Primary", "REQ-001": "Supporting"},
}

# ---- Subjects and evaluation lenses (POL-REQ-004; doc 06 §Association classes) ----
#
# The four concepts below say nothing about *what* the shopper wants. Security
# posture, enterprise readiness, regulatory fit and integration fit are things a
# careful buyer checks about any candidate, in any category — an HR buyer reads
# the security page of an HR product, and that is not a request for identity
# software.
#
# Mapped at full strength they outvoted the subject in every one of the seven
# domain areas, because the requirements they feed are fed by many concepts
# (Identity Management 5, Workflow Automation 7, Regulatory Compliance 6) while
# each subject requirement is fed by one or two. Under noisy-OR, feeder count
# alone decided the top requirement, and the answer was "Identity Management"
# whether the shopper was researching payroll, dashboards or endpoint security
# (Decision #073).
#
# So the demotion is conditional, not absolute: while no subject is declared
# these concepts still derive requirements on their own — that is Scenario 1,
# where Security Evaluation genuinely *is* the subject and must keep publishing
# Identity Management at Critical.
EVALUATION_LENS_CONCEPTS = frozenset({"BC-001", "BC-002", "BC-004", "BC-008"})

# {subject concept: the Requirement it is the Primary evidence for}. Derived
# from BC_TO_REQ rather than restated, so a new subject pattern cannot acquire
# an anchor that disagrees with the mapping it was declared in.
SUBJECT_REQUIREMENT: dict[str, str] = {
    bc: next(req for req, assoc in BC_TO_REQ[bc].items() if assoc == "Primary")
    for bc in INTENT_CONCEPTS
}

# {subject concept: product categories that subject is shopped in} — the same
# categories the pattern activates on, so "what the shopper researched" and
# "what counts as on-subject when ranking" cannot drift apart.
SUBJECT_CATEGORIES: dict[str, frozenset[str]] = {
    **{bc: frozenset(categories)
       for _pattern, bc, _topics, categories, _terms in DOMAIN_RESEARCH_PATTERNS},
    **SUBJECTS_WITH_OWN_EVALUATOR,
}

# ---- REQ → CAP Mapping (doc 07 — all associations are "required") ----
# {req_id: {cap_id: association_level}}
# Note: REQ-004 carries exactly 4 capabilities — the CAP-001 Supporting row was
# removed from doc 07 (Decision #035) to match the binding derivations in doc 09.

REQ_TO_CAP: dict[str, dict[str, str]] = {
    "REQ-001": {
        "CAP-001": "Primary", "CAP-002": "Primary", "CAP-007": "Primary",
        "CAP-005": "Secondary", "CAP-006": "Secondary",
        "CAP-010": "Supporting", "CAP-011": "Supporting",
    },
    "REQ-002": {
        "CAP-001": "Primary", "CAP-002": "Primary",
        "CAP-003": "Secondary", "CAP-004": "Secondary",
        # Rehomed from Security Operations, where it never belonged and where its
        # presence let identity products out-cover endpoint-security ones
        # (Decisions #074, #075). Federation is an identity mechanism; this is
        # the requirement it has always described.
        "CAP-008": "Secondary",
        "CAP-010": "Supporting",
    },
    "REQ-003": {
        "CAP-015": "Primary", "CAP-016": "Primary",
        "CAP-017": "Secondary", "CAP-018": "Secondary",
        "CAP-019": "Supporting",
    },
    "REQ-004": {
        "CAP-010": "Primary", "CAP-012": "Primary",
        "CAP-013": "Secondary", "CAP-014": "Secondary",
        # Rehomed from Security Operations (Decisions #074, #075). Decision #074's
        # own amendment said "Compliance Reporting is what REQ-004 is for" and
        # then did not put it there; demonstrating compliance status to auditors
        # is this requirement's entire subject.
        "CAP-027": "Secondary",
    },
    # v1.2 (doc 14 Table 1). Additive only: nothing above changes, because those
    # set sizes are the denominators the pinned derivations assert.
    "REQ-006": {
        "CAP-029": "Primary", "CAP-028": "Primary",
        "CAP-030": "Secondary", "CAP-031": "Secondary",
        "CAP-032": "Supporting",
    },
    "REQ-007": {
        "CAP-035": "Primary", "CAP-033": "Primary",
        "CAP-034": "Secondary", "CAP-036": "Secondary",
        "CAP-037": "Supporting",
    },
    "REQ-008": {
        "CAP-040": "Primary", "CAP-038": "Primary",
        "CAP-039": "Secondary", "CAP-042": "Secondary",
        "CAP-041": "Supporting",
    },
    "REQ-009": {
        "CAP-044": "Primary", "CAP-043": "Primary",
        "CAP-045": "Secondary", "CAP-046": "Secondary",
        "CAP-047": "Supporting",
    },
    "REQ-010": {
        "CAP-048": "Primary", "CAP-049": "Primary",
        "CAP-050": "Secondary", "CAP-051": "Secondary",
        "CAP-052": "Supporting",
    },
    # v1.5 (Decision #079). Task Management is what a shopper means by work
    # management; Workload Management is the capacity view a team reaches for
    # once the tasks exist; Template Library is how repeated work stops being
    # retyped. All three are the capability catalog's own "Work Management"
    # domain, and all three previously reached no requirement at all.
    "REQ-013": {
        "CAP-056": "Primary",
        "CAP-058": "Secondary",
    },
    # v1.6 (Decision #081). Working on a document together and getting it to the
    # people who need it are what the whole family shares — 13 and 12 of the 24
    # products hold them. Template Library is reuse, which is the difference
    # between a document store and a knowledge base.
    #
    # Information Governance and Data Retention were the obvious additions, and
    # are deliberately absent: they are REQ-004's subject, and requirements that
    # borrow capabilities from another domain are how REQ-011 ended up ranking a
    # DevOps monitoring tool first (Decision #061).
    "REQ-014": {
        "CAP-063": "Primary", "CAP-064": "Primary",
        "CAP-057": "Secondary",
        "CAP-065": "Supporting",
    },
    # Move the data, store it, show it — the three things a shopper means by
    # "data and insight", and nothing borrowed from another domain.
    #
    # It was briefly five, with Intelligent Search and API Integration added to
    # break a 21-way tie at 100%. That fixed the tie and made the requirement
    # *unsatisfiable*: no product in 250 could reach 5/5, so the true winner was
    # capped at 80% while anything satisfiable beat it (Decision #061).
    #
    # The tie was never really about the requirement. All 21 products held all
    # three capabilities because the catalog assigned the Data & Analytics
    # domain as a block — it said Tableau, Fivetran and BigQuery were the same
    # product. With each restated as what it is, three capabilities discriminate
    # perfectly well and only the end-to-end platforms cover all of them.
    "REQ-011": {
        "CAP-054": "Primary", "CAP-055": "Primary",
        "CAP-053": "Secondary",
    },
    # v1.2 housed four capabilities stranded inside the *original* domains here,
    # to reach them without editing a frozen set. Two of those four described the
    # wrong thing: Compliance Reporting is what REQ-004 is for, and Identity
    # Federation is an identity capability whose presence let identity products
    # out-cover endpoint-security ones on the security requirement. Both are gone,
    # replaced by the v1.3 vocabulary that says what detecting and responding to
    # threats actually requires (Decision #074).
    "REQ-012": {
        "CAP-059": "Primary", "CAP-025": "Primary",
        "CAP-060": "Secondary", "CAP-061": "Secondary",
        "CAP-062": "Supporting", "CAP-026": "Supporting",
    },
    "REQ-005": {
        "CAP-020": "Primary", "CAP-021": "Primary",
        "CAP-022": "Secondary", "CAP-023": "Secondary",
        "CAP-015": "Supporting",
    },
}

# ---- Stage Qualification Milestones (doc 00 §4.1) ----
# Declarative descriptors consumed by the Journey Stage Engine.
#
# Evaluation patterns are the ones that mean "this person is researching a kind
# of software": BP-001…008 in v1, plus the seven v1.2 domain patterns. They
# carry the Research and Technical Validation milestones, so leaving the new
# ones out would strand a CRM or payroll journey at Awareness forever — and
# because stage gates the Critical priority band (POL-REQ-002), a need those
# journeys produced could never reach Critical while an identity journey's
# could. Same behavior, different domain, different ceiling: not defensible.

EVALUATION_PATTERNS = (tuple(f"BP-{i:03d}" for i in range(1, 9))
                       + tuple(f"BP-{i:03d}" for i in range(13, 20)))

STAGE_MILESTONES: list[dict] = [
    {"stage": "Awareness", "kind": "events_no_evidence"},
    {"stage": "Discovery", "kind": "pattern_evidence", "patterns": ["BP-012"]},
    {"stage": "Research", "kind": "pattern_evidence", "patterns": list(EVALUATION_PATTERNS)},
    {"stage": "Comparison", "kind": "pattern_evidence_or_event",
     "patterns": ["BP-009"], "event_types": ["COMPARISON_STARTED"]},
    {"stage": "Technical Validation", "kind": "pattern_evidence_min_strength",
     "patterns": list(EVALUATION_PATTERNS), "min_strength": "MEDIUM"},
    {"stage": "Commercial Evaluation", "kind": "pattern_evidence_min_strength",
     "patterns": ["BP-009"], "min_strength": "MEDIUM"},
    # Which patterns satisfy these two is domain knowledge, so the ids are
    # named here rather than inside the engine's dispatcher: the kind says how
    # to evaluate, the lists say what to evaluate against.
    {"stage": "Decision", "kind": "decision_milestone",
     "strong_patterns": ["BP-010"], "any_patterns": ["BP-011"]},
    # Doc 00 §4.1: BP-011 evidence *and the journey's affinity product has
    # onboarding/migration activity*. Both qualifiers are load-bearing — the
    # topic, and the product it belongs to. `product_event_types` names the
    # triggers that identify which product is being adopted, imported from the
    # pattern that defines them so the two cannot drift apart.
    {"stage": "Adoption", "kind": "adoption_milestone",
     "patterns": ["BP-011"], "event_types": ["DOCUMENTATION_VIEWED"],
     "topics": sorted(ADOPTION_DOC_TOPICS),
     "product_event_types": sorted(BP011_TRIGGERS)},
]

# ---- Event stage character (POL-STAGE-002 support) ----
# The HIGHEST journey stage an event type is characteristic of, derived from the
# patterns' "Possible Journey Stages" (doc 02). An event counts as
# "characteristic of an earlier stage" only when this stage sits below the
# journey's current stage — research-depth events never regress an evaluation
# stage they themselves qualify.

EVENT_STAGE_CHARACTER: dict[str, str] = {
    "SEARCH": "Discovery",
    "CATEGORY_VIEWED": "Discovery",
    "PRODUCT_VIEWED": "Discovery",
    "RECOMMENDATION_CLICKED": "Discovery",
    "DOCUMENTATION_VIEWED": "Technical Validation",
    "SECURITY_VIEWED": "Technical Validation",
    "PRICING_VIEWED": "Commercial Evaluation",
    "COMPARISON_STARTED": "Commercial Evaluation",
    "TRIAL_STARTED": "Adoption",
    "DEMO_REQUESTED": "Adoption",
    "ADD_TO_CART": "Adoption",
    "CHECKOUT_STARTED": "Adoption",
    "PURCHASE_COMPLETED": "Adoption",
}

# ---- Behavioral Patterns BP-001…BP-012 (doc 02, declarative) ----
# Activation is evaluated by the BRE over the pattern's window (session-scoped
# unless journey_scope). Thresholds are Domain Pack v1 defaults (doc 02).
# Strength ladder: WEAK → MEDIUM → STRONG → VERY_STRONG.

PATTERNS: dict[str, dict] = {
    "BP-001": {
        "name": "Security Evaluation",
        "concepts": ["BC-001"],
        "window": "session",
        # ≥2 SECURITY_VIEWED on distinct pages, OR 1 SECURITY_VIEWED +
        # 1 DOCUMENTATION_VIEWED topic in security/sso/mfa
        "base_strength": "MEDIUM",
        "strong_qualifying_events": 4,   # or supporting dwell ≥ 60s
        "dwell_seconds": 60,
    },
    "BP-002": {
        "name": "Enterprise Evaluation",
        "concepts": ["BC-002"],
        "window": "session",
        # ≥2 among: DOCUMENTATION_VIEWED topic admin/provisioning/federation;
        # PRICING_VIEWED enterprise tier; SECURITY_VIEWED topic compliance/audit
        "base_strength": "MEDIUM",
        "strong_qualifying_events": 3,   # across ≥ 2 sessions
        "strong_requires_multi_session": True,
    },
    "BP-003": {
        "name": "AI Evaluation",
        "concepts": ["BC-003"],
        "window": "session",
        "base_strength": "MEDIUM",
        "strong_qualifying_events": 4,
        "dwell_seconds": 60,
    },
    "BP-004": {
        "name": "Compliance Evaluation",
        "concepts": ["BC-004"],
        "window": "session",
        "base_strength": "MEDIUM",
        "strong_requires_multi_session": True,
        "dwell_seconds": 60,
    },
    "BP-005": {
        "name": "Collaboration Evaluation",
        "concepts": ["BC-005"],           # co-supports BC-006 on productivity co-occurrence
        "co_supports": ["BC-006"],
        "window": "session",
        "base_strength": "MEDIUM",
        "strong_qualifying_events": 4,
    },
    "BP-006": {
        "name": "Productivity Evaluation",
        "concepts": ["BC-006"],
        "window": "session",
        "base_strength": "WEAK",
        "medium_qualifying_events": 3,    # no Strong level defined
    },
    "BP-007": {
        "name": "Automation Evaluation",
        "concepts": ["BC-007"],
        "window": "session",
        "base_strength": "MEDIUM",
        "strong_qualifying_events": 4,    # or multi-session recurrence
        "dwell_seconds": 60,
    },
    "BP-008": {
        "name": "Integration Evaluation",
        "concepts": ["BC-008"],
        "co_supports": ["BC-009"],
        "window": "session",
        "base_strength": "MEDIUM",
        # Strong when API reference and connector pages both appear
    },
    "BP-009": {
        "name": "Commercial Evaluation",
        "concepts": ["BC-010"],
        "co_supports": ["BC-014"],
        "window": "session",
        "base_strength": "MEDIUM",
        "strong_requires_multi_session": True,
    },
    "BP-010": {
        "name": "Product Affinity",
        "concepts": ["BC-012"],
        "co_supports": ["BC-016"],
        "window": "journey",              # journey-scoped, product-scoped evidence
        "base_strength": "MEDIUM",
        "strong_qualifying_events": 5,
        "cumulative_dwell_seconds": 120,
    },
    "BP-011": {
        "name": "Adoption Readiness",
        "concepts": ["BC-015"],
        "co_supports": ["BC-016"],
        "window": "session",
        # 1 of: TRIAL_STARTED, DEMO_REQUESTED, ADD_TO_CART → STRONG;
        # CHECKOUT_STARTED, PURCHASE_COMPLETED → VERY_STRONG
        "base_strength": "STRONG",
        "very_strong_events": ["CHECKOUT_STARTED", "PURCHASE_COMPLETED"],
        "trigger_events": ["TRIAL_STARTED", "DEMO_REQUESTED", "ADD_TO_CART",
                           "CHECKOUT_STARTED", "PURCHASE_COMPLETED"],
    },
    "BP-012": {
        "name": "Product Discovery",
        "concepts": ["BC-011"],
        "window": "session",
        # ≥3 among CATEGORY_VIEWED/SEARCH/PRODUCT_VIEWED spanning ≥2 distinct
        # products or categories, no single product > 2 views
        "base_strength": "WEAK",
        "medium_qualifying_events": 5,    # no Strong level defined
        "min_qualifying_events": 3,
        "min_distinct_entities": 2,
        "max_views_per_product": 2,
    },
}

# v1.2 domain research patterns (doc 14 Table 2). Registry entries are generated
# from the same table the evaluators are built from, so a pattern can never be
# described here and absent there — the divergence that produced Decisions #044,
# #045 and #046. The vocabulary itself lives in `patterns.py` beside the rule
# that reads it.
PATTERNS.update({
    pattern_id: {
        "name": BEHAVIORAL_CONCEPTS[concept_id],
        "concepts": [concept_id],
        "window": "session",
        # ≥2 among: DOCUMENTATION_VIEWED on a topic of this domain;
        # PRODUCT_VIEWED / CATEGORY_VIEWED in one of its categories;
        # SEARCH containing one of its terms
        "base_strength": "MEDIUM",
        "strong_qualifying_events": 4,
        "doc_topics": sorted(doc_topics),
        "categories": sorted(categories),
        "search_terms": sorted(search_terms),
    }
    for pattern_id, concept_id, doc_topics, categories, search_terms
    in DOMAIN_RESEARCH_PATTERNS
})

# ---- Canonical Product Roster PROD-001…010 (doc 05 — test fixture) ----
# (product_id, name, vendor, category, description, business_purpose, capability_ids)

CANONICAL_PRODUCTS: list[dict] = [
    {
        "product_id": "PROD-001", "name": "Microsoft 365", "vendor": "Microsoft",
        "category": "Productivity & Collaboration",
        "description": "Enterprise productivity and collaboration platform supporting communication, document management, security, compliance, automation, and AI-assisted productivity.",
        "business_purpose": "Enable secure collaboration and organizational productivity through an integrated cloud platform.",
        "capabilities": ["CAP-001", "CAP-002", "CAP-005", "CAP-006", "CAP-007", "CAP-008",
                          "CAP-009", "CAP-010", "CAP-011", "CAP-012", "CAP-013", "CAP-014",
                          "CAP-015", "CAP-016", "CAP-017", "CAP-020", "CAP-021", "CAP-022",
                          "CAP-023", "CAP-025", "CAP-026", "CAP-027"],
    },
    {
        "product_id": "PROD-002", "name": "Slack", "vendor": "Salesforce",
        "category": "Collaboration",
        "description": "Enterprise collaboration platform focused on team communication, knowledge sharing, workflow integration, and productivity.",
        "business_purpose": "Improve organizational communication while connecting teams, applications, and workflows.",
        "capabilities": ["CAP-005", "CAP-006", "CAP-007", "CAP-009", "CAP-015", "CAP-016",
                          "CAP-019", "CAP-024"],
    },
    {
        "product_id": "PROD-003", "name": "Okta", "vendor": "Okta",
        "category": "Identity & Access Management",
        "description": "Independent identity and access management platform providing centralized authentication, identity lifecycle management, and access governance across an organization's application portfolio.",
        "business_purpose": "Standardize identity across every application while reducing authentication risk and manual identity administration.",
        "capabilities": ["CAP-001", "CAP-002", "CAP-003", "CAP-004", "CAP-008", "CAP-010",
                          "CAP-016"],
    },
    {
        "product_id": "PROD-004", "name": "Google Workspace", "vendor": "Google",
        "category": "Productivity & Collaboration",
        "description": "Cloud productivity and collaboration suite combining mail, documents, meetings, storage, and AI-assisted work.",
        "business_purpose": "Enable fast, browser-first collaboration and AI-assisted productivity with minimal administration.",
        "capabilities": ["CAP-001", "CAP-002", "CAP-005", "CAP-006", "CAP-007", "CAP-009",
                          "CAP-010", "CAP-011", "CAP-013", "CAP-020", "CAP-021", "CAP-022",
                          "CAP-023"],
    },
    {
        "product_id": "PROD-005", "name": "Zoom Workplace", "vendor": "Zoom",
        "category": "Collaboration",
        "description": "Video-first collaboration platform with meetings, team chat, and AI meeting assistance.",
        "business_purpose": "Make distributed meetings effortless and their outcomes durable through AI summaries.",
        "capabilities": ["CAP-005", "CAP-006", "CAP-020", "CAP-023"],
    },
    {
        "product_id": "PROD-006", "name": "Atlassian Jira", "vendor": "Atlassian",
        "category": "Work Management",
        "description": "Work and project management platform for planning, tracking, and shipping team work.",
        "business_purpose": "Give teams a structured, integrated system of record for work execution.",
        # v1.5 (Decision #079). The canonical Work Management product held no
        # work-management capability: its profile described the integration
        # platform underneath while its own description said "planning,
        # tracking, and shipping team work". The three capabilities were added
        # to the catalog for the wide demo roster and this roster was never
        # revisited, so REQ-013 had no product that could cover it and the
        # coverability ratchet said so the moment the requirement existed.
        "capabilities": ["CAP-016", "CAP-017", "CAP-019", "CAP-022",
                         "CAP-056", "CAP-057", "CAP-058"],
    },
    {
        "product_id": "PROD-007", "name": "ServiceNow", "vendor": "ServiceNow",
        "category": "Workflow Automation",
        "description": "Enterprise workflow platform automating business processes across IT, HR, and operations with rules-driven orchestration.",
        "business_purpose": "Digitize and automate enterprise processes end to end with governed, auditable workflows.",
        "capabilities": ["CAP-010", "CAP-015", "CAP-016", "CAP-017", "CAP-018", "CAP-019",
                          "CAP-027"],
    },
    {
        "product_id": "PROD-008", "name": "Zapier", "vendor": "Zapier",
        "category": "Workflow Automation",
        "description": "No-code automation platform connecting business applications through prebuilt integrations and event-driven workflows.",
        "business_purpose": "Let any team automate cross-application work without engineering effort.",
        "capabilities": ["CAP-015", "CAP-016", "CAP-017", "CAP-019"],
    },
    {
        "product_id": "PROD-009", "name": "Notion", "vendor": "Notion Labs",
        "category": "Knowledge & Docs",
        "description": "Connected workspace for documents, knowledge, and lightweight project management with integrated AI.",
        "business_purpose": "Consolidate team knowledge and docs into one flexible, AI-assisted workspace.",
        "capabilities": ["CAP-007", "CAP-009", "CAP-019", "CAP-020", "CAP-021", "CAP-022",
                          "CAP-023", "CAP-057", "CAP-063", "CAP-064"],
    },
    {
        "product_id": "PROD-010", "name": "Box", "vendor": "Box",
        "category": "Content Management",
        "description": "Governed cloud content management: secure file storage, sharing, and collaboration with enterprise-grade governance controls.",
        "business_purpose": "Provide a single, secure, compliant home for organizational content.",
        "capabilities": ["CAP-007", "CAP-009", "CAP-010", "CAP-011", "CAP-012", "CAP-013",
                          "CAP-026", "CAP-064", "CAP-065"],
    },
]
