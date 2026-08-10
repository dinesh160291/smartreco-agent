"""Domain Packs — canonical reference knowledge, strictly separated from the core platform.

`active` is the pack the platform reasons with. Platform modules import it
rather than naming a pack directly:

    from smartreco.domain import active as domain
    domain.EVENT_TYPES, domain.JOURNEY_STAGES, domain.SESSION_EVALUATORS

That indirection is the point of the separation. Without it, swapping domains
means editing every platform module that mentions one by name; with it, the
swap is configuration and the engines are untouched — which is the claim
`knowledge/architecture/domain-pack-contract.md` makes.

Selected by `DOMAIN_PACK`, defaulting to the reference domain. The pack must
supply every artifact in the contract; the boundary test checks that it does.
"""

import importlib
import os

DEFAULT_DOMAIN_PACK = "software_buying"

ACTIVE_DOMAIN_PACK = os.environ.get("DOMAIN_PACK") or DEFAULT_DOMAIN_PACK

active = importlib.import_module(f"smartreco.domain.{ACTIVE_DOMAIN_PACK}")

__all__ = ["ACTIVE_DOMAIN_PACK", "DEFAULT_DOMAIN_PACK", "active"]
