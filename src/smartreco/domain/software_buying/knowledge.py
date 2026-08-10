"""Software Buying Domain Pack v1 — canonical reference knowledge.

One-to-one transcription of docs/domains/software-buying/:
  01 Behavioral Ontology (BC registry) · 02 Behavioral Patterns (BP-001…012)
  04 Business Requirement Catalog · 10 Capability Catalog (27)
  06 BC→REQ mapping · 07 REQ→CAP mapping · 00 §4.1 Stage Milestones
  05 Product Capability Profiles (canonical roster PROD-001…010)

Reference knowledge is immutable during execution and never redefined by
Runtime Objects (doc 09, Principles 4-5). Pattern activation thresholds are
Domain Pack v1 values (doc 02: "the numbers are their v1 defaults").
"""

DOMAIN_PACK_VERSION = "1.0"

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
}

# ---- Business Requirement Catalog (doc 04) ----

REQUIREMENTS: dict[str, str] = {
    "REQ-001": "Secure Collaboration",
    "REQ-002": "Identity Management",
    "REQ-003": "Workflow Automation",
    "REQ-004": "Regulatory Compliance",
    "REQ-005": "AI Assistance",
}

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
    # express themselves honestly — data-model §Catalog Seed Strategy). The five
    # REQ→CAP mappings are unchanged: these capabilities are realistic noise
    # retrieval and matching must cut through. ----
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
    "siem": "audit logging",
    "cicd": "ci cd pipelines",
}

# ---- BC → REQ Mapping (doc 06 — association levels feed POL-REQ-003) ----
# {bc_id: {req_id: association_level}}

BC_TO_REQ: dict[str, dict[str, str]] = {
    "BC-001": {"REQ-002": "Primary", "REQ-001": "Secondary", "REQ-004": "Supporting"},
    "BC-002": {"REQ-002": "Primary", "REQ-004": "Secondary"},
    "BC-003": {"REQ-005": "Primary", "REQ-003": "Secondary", "REQ-001": "Supporting"},
    "BC-004": {"REQ-004": "Primary", "REQ-002": "Secondary", "REQ-001": "Supporting"},
    "BC-005": {"REQ-001": "Primary", "REQ-002": "Supporting"},
    "BC-006": {"REQ-005": "Primary", "REQ-003": "Supporting"},
    "BC-007": {"REQ-003": "Primary", "REQ-005": "Secondary"},
    "BC-008": {"REQ-003": "Primary", "REQ-002": "Secondary"},
    # BC-009…BC-018 deliberately unmapped in v1 (doc 06): they inform stage,
    # constraints, ranking context, or hypothesis lifecycle — never requirements.
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
    },
    "REQ-005": {
        "CAP-020": "Primary", "CAP-021": "Primary",
        "CAP-022": "Secondary", "CAP-023": "Secondary",
        "CAP-015": "Supporting",
    },
}

# ---- Stage Qualification Milestones (doc 00 §4.1) ----
# Declarative descriptors consumed by the Journey Stage Engine. Evaluation-
# pattern range for Research/Technical Validation milestones is BP-001…BP-008.

EVALUATION_PATTERNS = tuple(f"BP-{i:03d}" for i in range(1, 9))

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
    {"stage": "Adoption", "kind": "adoption_milestone",
     "patterns": ["BP-011"], "event_types": ["DOCUMENTATION_VIEWED"]},
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
        "capabilities": ["CAP-016", "CAP-017", "CAP-019", "CAP-022"],
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
                          "CAP-023"],
    },
    {
        "product_id": "PROD-010", "name": "Box", "vendor": "Box",
        "category": "Content Management",
        "description": "Governed cloud content management: secure file storage, sharing, and collaboration with enterprise-grade governance controls.",
        "business_purpose": "Provide a single, secure, compliant home for organizational content.",
        "capabilities": ["CAP-007", "CAP-009", "CAP-010", "CAP-011", "CAP-012", "CAP-013",
                          "CAP-026"],
    },
]
