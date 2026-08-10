"""Domain enumerations — Software Buying (Domain Pack contract artifacts 7 and 8).

Event types and journey stages are statements about a *domain*, not about the
platform: a travel pack has neither PRICING_VIEWED nor an eight-stage software
evaluation. They lived in `smartreco.enums` beside genuinely platform-wide
enums, which meant adding a second domain required editing platform code.

Core 22 already said the active Domain Pack owns the event registry; this is
where it now lives. Platform modules reach it through `smartreco.domain.active`.
"""

# --- EventType registry (Domain Pack doc 12; Core 22 defines the mechanism) ---
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

# --- Journey Stages (Domain Pack doc 00 §4, canonical order) ---

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
