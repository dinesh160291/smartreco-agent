"""Software Buying Domain Pack — the reference implementation of
`knowledge/architecture/domain-pack-contract.md`.

Split by contract artifact rather than by convenience:

  knowledge.py  concepts, patterns (declarative), requirements, capabilities,
                the two mappings, stage milestones, product roster, shorthand
  enums.py      event registry + journey stages (artifacts 7 and 8)
  patterns.py   pattern activation rules (artifact 2, imperative form)

Everything is re-exported here, so `from smartreco.domain.software_buying
import X` reaches any artifact without callers needing to know which file it
sits in — the split is an organising decision, not part of the interface.
"""

from smartreco.domain.software_buying.enums import (
    EVENT_TYPES,
    JOURNEY_STAGES,
    stage_index,
)
from smartreco.domain.software_buying.knowledge import (
    BC_TO_REQ,
    BEHAVIORAL_CONCEPTS,
    CANONICAL_PRODUCTS,
    CAPABILITIES,
    DOMAIN_PACK_VERSION,
    EVALUATION_LENS_CONCEPTS,
    EVALUATION_PATTERNS,
    EVENT_STAGE_CHARACTER,
    PATTERNS,
    PRODUCT_CATEGORIES,
    REQ_TO_CAP,
    REQUIREMENTS,
    SEARCH_ALIASES,
    STAGE_MILESTONES,
    SUBJECT_CATEGORIES,
    SUBJECT_REQUIREMENT,
)
from smartreco.domain.software_buying.patterns import (
    ADOPTION_MIGRATION_TOPIC,
    ADOPTION_ONBOARDING_TOPIC,
    DOMAIN_RESEARCH_PATTERNS,
    INTENT_CONCEPTS,
    DWELL_TOPICS,
    JOURNEY_EVALUATORS,
    PATTERN_TOPICS,
    SESSION_EVALUATORS,
    UI_DOC_TOPIC_DEFAULT,
    UI_DOC_TOPICS,
    UI_INTEGRATION_TOPIC_DEFAULT,
    UI_INTEGRATION_TOPICS,
    UI_SECURITY_TOPIC_DEFAULT,
    UI_SECURITY_TOPICS,
)

DOMAIN_ID = "software_buying"
DOMAIN_NAME = "Software Buying"

__all__ = [
    "ADOPTION_MIGRATION_TOPIC", "ADOPTION_ONBOARDING_TOPIC",
    "BC_TO_REQ", "BEHAVIORAL_CONCEPTS", "CANONICAL_PRODUCTS", "CAPABILITIES",
    "DOMAIN_ID", "DOMAIN_NAME", "DOMAIN_PACK_VERSION",
    "DOMAIN_RESEARCH_PATTERNS", "DWELL_TOPICS", "INTENT_CONCEPTS",
    "PRODUCT_CATEGORIES",
    "EVALUATION_LENS_CONCEPTS", "EVALUATION_PATTERNS",
    "EVENT_STAGE_CHARACTER", "EVENT_TYPES", "JOURNEY_EVALUATORS",
    "JOURNEY_STAGES", "PATTERNS", "REQ_TO_CAP", "REQUIREMENTS",
    "PATTERN_TOPICS",
    "SEARCH_ALIASES", "SESSION_EVALUATORS", "STAGE_MILESTONES", "stage_index",
    "SUBJECT_CATEGORIES", "SUBJECT_REQUIREMENT",
    "UI_DOC_TOPICS", "UI_DOC_TOPIC_DEFAULT",
    "UI_INTEGRATION_TOPICS", "UI_INTEGRATION_TOPIC_DEFAULT",
    "UI_SECURITY_TOPICS", "UI_SECURITY_TOPIC_DEFAULT",
]
