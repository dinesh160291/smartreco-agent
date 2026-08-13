"""Signature test: the ADK wrapper executes the same stage graph with the same
outcomes as the plain executor (core 21: swapping frameworks changes no engine,
contract, or Runtime Object; stack-decisions: the framework only supplies the
graph wrapper)."""

from datetime import datetime

from sqlalchemy import select

from smartreco import models
from smartreco.orchestration import adk_executor
from smartreco.pipeline import run_workflow
from smartreco.repos import insert_events_idempotent


def _seed_user_events(db, email):
    user = models.User(email=email, password_hash="x")
    db.add(user)
    db.commit()
    ts = datetime(2026, 8, 6, 9, 0)
    rows = [
        {"event_id": f"adk-{i}", "user_id": user.id, "session_id": "adk-s1",
         "journey_id": None, "event_type": et, "signal_class": "HIGH",
         "event_metadata": md, "ts": ts, "received_at": ts, "processed_at": None}
        for i, (et, md) in enumerate([
            ("SEARCH", {"query": "single sign-on"}),
            ("SECURITY_VIEWED", {"page": "a"}),
            ("SECURITY_VIEWED", {"page": "b"}),
            ("DOCUMENTATION_VIEWED", {"topic": "sso"}),
            ("DOCUMENTATION_VIEWED", {"topic": "mfa"}),
        ])
    ]
    db.add(models.Session(session_id="adk-s1", user_id=user.id,
                          started_at=ts, last_event_at=ts))
    insert_events_idempotent(db, rows)
    db.commit()
    return user, ts


def test_adk_executor_matches_plain_executor(seeded, chroma, backend, policies, fake_gateway):
    db = seeded
    user, ts = _seed_user_events(db, "adk@example.com")

    run = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                       now=ts.replace(minute=2), gateway=fake_gateway,
                       executor=adk_executor)
    assert run.status == "COMPLETED"

    # Same node trace shape as the plain executor produces
    node_names = [n["node"] for n in run.nodes]
    assert node_names[:5] == ["resolve_journey", "reason", "score_confidence",
                              "infer_requirements", "resolve_stage"]
    assert node_names[-1] in ("generate", "clarify")

    # Runtime Objects landed exactly as with the plain path
    journey = db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)).scalars().one()
    evidence = db.execute(select(models.Evidence).where(
        models.Evidence.journey_id == journey.journey_id)).scalars().all()
    assert evidence  # BP-001 fired through the ADK-run graph
    pkg = db.execute(select(models.RecommendationPackage).where(
        models.RecommendationPackage.journey_id == journey.journey_id)).scalars().first()
    assert pkg is not None


def test_adk_halts_the_graph_when_there_is_no_journey_to_reason_about(
        seeded, chroma, backend, policies, fake_gateway):
    """The halt contract, which only the happy path was covering.

    POL-TRIG-001 fires at 3 unprocessed events; POL-JRES-001 does not settle a
    session's ownership until 5. Every new session therefore passes through a
    window where a run is due and no journey exists yet — `resolve_journey`
    returns False and the graph must stop.

    The plain executor honours that return value. The ADK wrapper set
    `end_invocation` and trusted the framework to act on it, which this version
    of SequentialAgent does not: the next node ran anyway and died on
    `state["journey_id"]`, turning a routine SKIP into a FAILED run. Seen live —
    a browser session produced exactly this, 0.4s before a healthy run.
    """
    db = seeded
    # A first, settled session, so the user owns a journey: the settle guard is
    # short-circuited for a user who has none (there is no comparison to
    # protect), and it is the guard that opens the window.
    user, ts = _seed_user_events(db, "adk-halt@example.com")
    first = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                         now=ts.replace(minute=2), gateway=fake_gateway)
    assert first.status == "COMPLETED", "precondition: the user should own a journey"

    # Now a fresh session, above POL-TRIG-001's 3 and below POL-JRES-001's 5.
    later = ts.replace(minute=10)
    rows = [
        {"event_id": f"halt-{i}", "user_id": user.id, "session_id": "halt-s2",
         "journey_id": None, "event_type": "SEARCH", "signal_class": "HIGH",
         "event_metadata": {"query": f"q{i}"}, "ts": later, "received_at": later,
         "processed_at": None}
        for i in range(4)
    ]
    db.add(models.Session(session_id="halt-s2", user_id=user.id,
                          started_at=later, last_event_at=later))
    insert_events_idempotent(db, rows)
    db.commit()

    run = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                       now=later.replace(minute=12), gateway=fake_gateway,
                       executor=adk_executor)
    assert run.status == "SKIPPED", (
        "the ADK graph ran past a node that told it to stop")
    assert run.journey_id is None
