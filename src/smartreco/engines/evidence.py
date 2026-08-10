"""Evidence types — the contract between the platform and a Domain Pack's
pattern evaluators (docs/core/19, Core 03).

Kept in their own module so the pack's evaluators can depend on the shapes
without importing the engine that runs them, and the engine can load the
pack's evaluators without importing back. Neither side needs the other's
implementation — only these two structures.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EventView:
    """One tracked event, reduced to what pattern evaluation may look at."""

    event_id: str
    event_type: str
    session_id: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceDraft:
    """A pattern's activation, before the caller persists it as Evidence.

    `dedup_key` is the platform's identity rule (Core 19): the same pattern
    over the same supporting events is the same observation, however many
    times evaluation runs.
    """

    pattern_id: str
    strength: str
    concept_ids: list[str]
    supporting_event_ids: list[str]
    explanation: str
    contradicts: tuple[str, ...] = ()  # concepts contradicted (pattern Contradicting rules)

    @property
    def dedup_key(self) -> tuple:
        return (self.pattern_id, tuple(sorted(self.supporting_event_ids)), self.contradicts)
