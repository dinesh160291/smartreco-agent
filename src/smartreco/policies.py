"""Policy loader — the single access path to config/policies.yaml.

Law 4 (CLAUDE.md): no business thresholds in code. Engines never read the YAML
directly and never embed numbers; they receive a PolicyCatalog and look values up
by Policy ID. Every workflow run records catalog_version as its policy_version.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_POLICIES_PATH = Path(__file__).resolve().parents[2] / "config" / "policies.yaml"


class PolicyError(KeyError):
    """Unknown policy ID or missing parameter — always a bug, never a fallback."""


@dataclass(frozen=True)
class Policy:
    policy_id: str
    name: str
    category: str
    rule: str
    params: dict[str, Any]

    def param(self, key: str) -> Any:
        try:
            return self.params[key]
        except KeyError:
            raise PolicyError(f"{self.policy_id} has no parameter {key!r}") from None


class PolicyCatalog:
    def __init__(self, version: str, policies: dict[str, Policy]):
        self.version = version
        self._policies = policies

    def get(self, policy_id: str) -> Policy:
        try:
            return self._policies[policy_id]
        except KeyError:
            raise PolicyError(f"Unknown policy ID {policy_id!r}") from None

    def param(self, policy_id: str, key: str) -> Any:
        return self.get(policy_id).param(key)

    @property
    def policy_ids(self) -> list[str]:
        return sorted(self._policies)


def load_policies(path: Path | str = DEFAULT_POLICIES_PATH) -> PolicyCatalog:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    policies = {
        policy_id: Policy(
            policy_id=policy_id,
            name=entry["name"],
            category=entry["category"],
            rule=entry["rule"],
            params=entry.get("params", {}),
        )
        for policy_id, entry in raw["policies"].items()
    }
    return PolicyCatalog(version=str(raw["catalog_version"]), policies=policies)
