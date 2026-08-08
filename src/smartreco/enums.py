"""Closed platform enumerations — transcription of docs/core/17 and the
EventType registry in docs/core/22 (Law 7: never invent codes).

Codes are binding and immutable; display names are presentation only.
"""

# --- Core platform enums (docs/core/17) ---

JOURNEY_LIFECYCLE = ("NEW", "ACTIVE", "DORMANT", "CLOSED", "ARCHIVED")
JOURNEY_OUTCOME = ("PURCHASED", "ABANDONED", "CANCELLED", "NO_DECISION")
RECOMMENDATION_READINESS = ("READY", "NOT_READY")
CONFIDENCE_LEVEL = ("VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH")  # presentation bucket only
ENGINE_STATUS = ("PENDING", "RUNNING", "COMPLETED", "FAILED", "SKIPPED")
POLICY_EVALUATION_STATUS = ("PASSED", "FAILED", "NOT_APPLICABLE")
AI_RESPONSE_STATUS = ("GENERATED", "BLOCKED", "CLARIFICATION_REQUIRED")
SYNC_STATUS = ("PENDING", "SYNCED", "FAILED")
TRIGGER_TYPE = (
    "SIGNIFICANT_EVENT",
    "EVENT_ACCUMULATION",
    "SESSION_END",
    "STAGE_TRANSITION",
    "REQUIREMENT_SHIFT",
    "SCHEDULED",
    "ADMIN_CATALOG_CHANGE",
)
SIGNAL_CLASS = ("HIGH", "MEDIUM", "LOW")
DELIVERY_STATUS = ("SENT", "FAILED", "SKIPPED")
DELIVERY_CHANNEL = ("TELEGRAM", "EMAIL")
AAR_SURFACE = ("ONSITE", "DIGEST")
HYPOTHESIS_STATUS = ("CREATED", "STRENGTHENED", "STABLE", "WEAKENED", "RETIRED")
EVIDENCE_STRENGTH = ("WEAK", "MEDIUM", "STRONG", "VERY_STRONG")
REQUIREMENT_PRIORITY = ("CRITICAL", "HIGH", "MEDIUM", "LOW")

# --- Domain enumeration: EventType registry (docs/core/22, Software Buying) ---
# Closed: an event with a type outside this table fails structural validation.
# Maps event type → signal class.

EVENT_TYPES: dict[str, str] = {
    "PRODUCT_VIEWED": "HIGH",
    "SEARCH": "HIGH",
    "CATEGORY_VIEWED": "MEDIUM",
    "PRICING_VIEWED": "HIGH",
    "DOCUMENTATION_VIEWED": "HIGH",
    "SECURITY_VIEWED": "HIGH",
    "COMPARISON_STARTED": "HIGH",
    "DWELL": "LOW",
    "RECOMMENDATION_CLICKED": "HIGH",
    "TRIAL_STARTED": "HIGH",
    "DEMO_REQUESTED": "HIGH",
    "ADD_TO_CART": "HIGH",
    "CHECKOUT_STARTED": "HIGH",
    "PURCHASE_COMPLETED": "HIGH",
}

# --- Domain enumeration: Journey Stages (Domain Pack 00, canonical order) ---

JOURNEY_STAGES = (
    "Awareness",
    "Discovery",
    "Research",
    "Comparison",
    "Technical Validation",
    "Commercial Evaluation",
    "Decision",
    "Adoption",
)


def stage_index(stage: str) -> int:
    return JOURNEY_STAGES.index(stage)
