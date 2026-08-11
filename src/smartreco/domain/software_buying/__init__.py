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
    EVALUATION_PATTERNS,
    EVENT_STAGE_CHARACTER,
    PATTERNS,
    REQ_TO_CAP,
    REQUIREMENTS,
    SEARCH_ALIASES,
    STAGE_MILESTONES,
)
from smartreco.domain.software_buying.patterns import (
    DWELL_TOPICS,
    JOURNEY_EVALUATORS,
    SESSION_EVALUATORS,
)

DOMAIN_ID = "software_buying"
DOMAIN_NAME = "Software Buying"

__all__ = [
    "BC_TO_REQ", "BEHAVIORAL_CONCEPTS", "CANONICAL_PRODUCTS", "CAPABILITIES",
    "DOMAIN_ID", "DOMAIN_NAME", "DOMAIN_PACK_VERSION", "DWELL_TOPICS",
    "EVALUATION_PATTERNS",
    "EVENT_STAGE_CHARACTER", "EVENT_TYPES", "JOURNEY_EVALUATORS",
    "JOURNEY_STAGES", "PATTERNS", "REQ_TO_CAP", "REQUIREMENTS",
    "SEARCH_ALIASES", "SESSION_EVALUATORS", "STAGE_MILESTONES", "stage_index",
]
