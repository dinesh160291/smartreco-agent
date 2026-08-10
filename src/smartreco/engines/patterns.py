"""Behavioral Reasoning Engine — pattern evaluation mechanism (docs/core/19).

Pure deterministic function over the journey's event history: identical events
always produce identical Evidence drafts. The caller persists drafts whose
dedup key is new (Core 19 dedup rule).

The engine owns the *mechanism* — grouping events into sessions, running each
evaluator, ordering session-scoped work before journey-scoped work. It owns no
pattern. The activation rules are Domain Pack artifact 2 and live in the active
pack (`domain-pack-contract.md`), so a second domain supplies its own
predicates without this file changing.

`EventView` and `EvidenceDraft` are re-exported for callers that import them
from here.
"""

from smartreco.engines.evidence import EventView, EvidenceDraft
from smartreco.policies import PolicyCatalog

__all__ = ["EventView", "EvidenceDraft", "evaluate_patterns"]


def evaluate_patterns(
    events: list[EventView],
    policies: PolicyCatalog,
    session_evaluators=None,
    journey_evaluators=None,
) -> list[EvidenceDraft]:
    """Run the active domain's pattern evaluators over one journey's events.

    Evaluators default to the active Domain Pack's. They are injectable so a
    test can exercise the mechanism against a fixed set without standing up a
    whole pack. Imported lazily: the pack's evaluators depend on the evidence
    types, and a module-level import here would close that loop.
    """
    if session_evaluators is None or journey_evaluators is None:
        from smartreco.domain import active as domain

        session_evaluators = session_evaluators or domain.SESSION_EVALUATORS
        journey_evaluators = journey_evaluators or domain.JOURNEY_EVALUATORS

    drafts: list[EvidenceDraft] = []
    sessions: dict[str, list[EventView]] = {}
    for event in events:
        sessions.setdefault(event.session_id, []).append(event)

    for session_events in sessions.values():
        for evaluator in session_evaluators:
            result = evaluator(session_events, events)
            if isinstance(result, EvidenceDraft):
                drafts.append(result)
            elif result:
                drafts.extend(result)

    for evaluator in journey_evaluators:
        drafts.extend(evaluator(events))
    return drafts
