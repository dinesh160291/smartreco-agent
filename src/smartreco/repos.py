"""Repository layer — immutability by convention, enforced here (data-model D2).

Decision-spine tables expose insert-only helpers; no UPDATE path exists for
them anywhere in the codebase. The only sanctioned mutations are the ones the
architecture declares living: users, products (+sync), cart, sessions,
journeys (lifecycle), behavioral_traits — plus the two processing-state fields
on events (journey_id assignment, processed_at stamping).
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session as OrmSession

from smartreco import models


# ---- Events (append-only + the two sanctioned processing-state updates) ----

def insert_events_idempotent(db: OrmSession, rows: list[dict]) -> int:
    """Batch insert; duplicate client event IDs no-op (events.event_id PK)."""
    if not rows:
        return 0
    stmt = sqlite_insert(models.Event).values(rows).on_conflict_do_nothing(
        index_elements=["event_id"])
    result = db.execute(stmt)
    return result.rowcount


def assign_journey(db: OrmSession, session_id: str, journey_id: str) -> None:
    db.query(models.Event).filter(
        models.Event.session_id == session_id,
        models.Event.journey_id.is_(None),
    ).update({"journey_id": journey_id}, synchronize_session=False)


def stamp_processed(db: OrmSession, event_ids: list[str], when: datetime) -> None:
    if not event_ids:
        return
    db.query(models.Event).filter(models.Event.event_id.in_(event_ids)).update(
        {"processed_at": when}, synchronize_session=False)


# ---- Decision spine (insert-only) ----

def insert_evidence(db: OrmSession, row: models.Evidence) -> None:
    db.add(row)


def insert_hypothesis_version(db: OrmSession, row: models.Hypothesis) -> None:
    db.add(row)


def insert_requirement_profile(db: OrmSession, row: models.RequirementProfile) -> None:
    db.add(row)


def insert_journey_stage(db: OrmSession, row: models.JourneyStage) -> None:
    db.add(row)


def insert_candidate_set(db: OrmSession, row: models.CandidateSet) -> None:
    db.add(row)


def insert_recommendation_package(db: OrmSession, row: models.RecommendationPackage) -> None:
    db.add(row)


def insert_advisory_response(db: OrmSession, row: models.AdvisoryResponse) -> None:
    db.add(row)


def insert_workflow_run(db: OrmSession, row: models.WorkflowRun) -> None:
    db.add(row)


def insert_journey_transition(db: OrmSession, row: models.JourneyTransition) -> None:
    db.add(row)


# ---- Reads ----

def current_hypotheses(db: OrmSession, journey_id: str) -> dict[str, models.Hypothesis]:
    """Latest version per hypothesis_id for a journey."""
    rows = db.execute(
        select(models.Hypothesis)
        .where(models.Hypothesis.journey_id == journey_id)
        .order_by(models.Hypothesis.hypothesis_id, models.Hypothesis.version)
    ).scalars().all()
    latest: dict[str, models.Hypothesis] = {}
    for row in rows:
        latest[row.hypothesis_id] = row
    return latest


def journey_evidence(db: OrmSession, journey_id: str) -> list[models.Evidence]:
    return db.execute(
        select(models.Evidence)
        .where(models.Evidence.journey_id == journey_id)
        .order_by(models.Evidence.created_at, models.Evidence.evidence_id)
    ).scalars().all()


def journey_events(db: OrmSession, journey_id: str) -> list[models.Event]:
    return db.execute(
        select(models.Event)
        .where(models.Event.journey_id == journey_id)
        .order_by(models.Event.ts, models.Event.event_id)
    ).scalars().all()
