"""Signature tests: POL-TRIG-005 run concurrency is actually enforced.

The policy has always said "at most one in-flight workflow run per user; a
trigger arriving during a run is recorded as SKIP (already-running)". The
trigger evaluator has always implemented the decision. But nothing ever wrote
status RUNNING — the literal appeared only in the enum and in the query that
reads it — so `run_in_flight` was permanently False and the gate could never
fire. Across 153 runs in a live database: 30 COMPLETED, 123 SKIPPED, zero
RUNNING.

Found by browsing the live app. Tracking flushes a batch per page, each batch
schedules a background trigger evaluation, and two rapid flushes raced: both
passed the dead gate, both resolved sessions and created a cold-start journey,
and both inserted journey stage version 1 —

    IntegrityError: UNIQUE constraint failed:
        journey_stages.journey_id, journey_stages.version

which surfaced as a 500 and left the user with a duplicate empty journey.

These pin the state machine the policy assumed: a run announces itself, a
concurrent trigger is skipped rather than racing, and a run always releases
its claim — including when it fails, or the user is blocked forever.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from smartreco import models, repos
from smartreco.pipeline import run_workflow

NOW = datetime(2026, 8, 11, 10, 0)


def _busy_user(db, chroma, backend, policies, email="conc@example.com"):
    user = models.User(email=email, password_hash="x", role="user")
    db.add(user)
    db.commit()
    ts = NOW - timedelta(minutes=5)
    db.add(models.Session(session_id="cs1", user_id=user.id, started_at=ts, last_event_at=ts))
    repos.insert_events_idempotent(db, [
        {"event_id": f"ce{i}", "user_id": user.id, "session_id": "cs1", "journey_id": None,
         "event_type": t, "signal_class": "HIGH", "event_metadata": m,
         "ts": ts, "received_at": ts, "processed_at": None}
        for i, (t, m) in enumerate([
            ("SEARCH", {"query": "single sign-on"}),
            ("PRODUCT_VIEWED", {"product_id": "PROD-003"}),
            ("SECURITY_VIEWED", {"product_id": "PROD-003", "page": "p", "topic": "audit"}),
            ("DOCUMENTATION_VIEWED", {"product_id": "PROD-003", "topic": "sso"}),
            ("PRICING_VIEWED", {"product_id": "PROD-003", "tier": "enterprise"}),
            ("DOCUMENTATION_VIEWED", {"product_id": "PROD-003", "topic": "provisioning"}),
        ])])
    db.commit()
    return user


def test_a_run_announces_itself_while_it_executes(seeded, chroma, backend, policies,
                                                  fake_gateway):
    """The state the gate reads must exist while the work is happening —
    otherwise the check is against a value nothing ever sets."""
    db = seeded
    user = _busy_user(db, chroma, backend, policies)
    seen = {}

    def observing_executor(ctx, state):
        from smartreco.pipeline import _execute_plain
        seen["running_mid_flight"] = db.execute(
            select(models.WorkflowRun).where(
                models.WorkflowRun.user_id == ctx.user_id,
                models.WorkflowRun.status == "RUNNING")).scalars().all()
        _execute_plain(ctx, state)

    run = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                       now=NOW, gateway=fake_gateway, executor=observing_executor)
    assert run.status == "COMPLETED"
    assert seen["running_mid_flight"], (
        "no RUNNING row existed while the workflow was executing, so a "
        "concurrent trigger has nothing to detect")


def test_a_concurrent_trigger_is_skipped_as_already_running(seeded, chroma, backend,
                                                            policies, fake_gateway):
    """POL-TRIG-005 verbatim: the second trigger is recorded as a SKIP, and its
    events stay unprocessed for the next evaluation rather than being consumed
    by a half-raced run."""
    db = seeded
    user = _busy_user(db, chroma, backend, policies)
    repos.insert_workflow_run(db, models.WorkflowRun(
        run_id="WR-inflight", user_id=user.id, journey_id=None,
        trigger_type="EVENT_ACCUMULATION", gates={}, nodes=[],
        policy_version=policies.version, status="RUNNING",
        started_at=NOW, finished_at=NOW))
    db.commit()

    run = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                       now=NOW, gateway=fake_gateway)

    assert run.status == "SKIPPED", "a concurrent trigger was allowed to run"
    assert "already-running" in run.gates["decision"], run.gates
    unprocessed = db.execute(select(models.Event).where(
        models.Event.user_id == user.id,
        models.Event.processed_at.is_(None))).scalars().all()
    assert unprocessed, "the skipped trigger consumed its events anyway"


def test_a_completed_run_releases_its_claim(seeded, chroma, backend, policies,
                                            fake_gateway):
    """A claim that is never released blocks the user permanently."""
    db = seeded
    user = _busy_user(db, chroma, backend, policies)
    run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                 now=NOW, gateway=fake_gateway)
    still_running = db.execute(select(models.WorkflowRun).where(
        models.WorkflowRun.user_id == user.id,
        models.WorkflowRun.status == "RUNNING")).scalars().all()
    assert not still_running, f"run left a stuck RUNNING row: {still_running}"


def test_a_crashed_run_releases_its_claim_and_still_raises(seeded, chroma, backend,
                                                           policies, fake_gateway):
    """Fail loud, but do not fail *stuck*: the exception must propagate so the
    orchestration's degradation paths see it, and the claim must be released so
    the next trigger is not skipped forever."""
    db = seeded
    user = _busy_user(db, chroma, backend, policies)

    def exploding_executor(ctx, state):
        raise RuntimeError("node blew up")

    with pytest.raises(RuntimeError, match="node blew up"):
        run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                     now=NOW, gateway=fake_gateway, executor=exploding_executor)

    rows = db.execute(select(models.WorkflowRun).where(
        models.WorkflowRun.user_id == user.id)).scalars().all()
    assert not [r for r in rows if r.status == "RUNNING"], (
        "a crashed run left its claim held; every later trigger would be skipped")
    assert [r for r in rows if r.status == "FAILED"], (
        "the crash was not recorded as a FAILED run")


def test_only_one_journey_is_created_for_a_cold_start(seeded, chroma, backend,
                                                      policies, fake_gateway):
    """The observed symptom: two racing cold-start runs each created a journey,
    leaving an empty duplicate that later runs then targeted."""
    db = seeded
    user = _busy_user(db, chroma, backend, policies)
    run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                 now=NOW, gateway=fake_gateway)
    journeys = db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)).scalars().all()
    assert len(journeys) == 1, f"expected one journey, got {[j.journey_id for j in journeys]}"


def test_the_index_makes_the_claim_atomic(seeded, chroma, backend, policies):
    """Belt and braces: even if two evaluations both pass the gate before
    either writes, the database refuses the second claim. Without this the
    guard is advisory — a read followed by a write, with a window between."""
    from sqlalchemy.exc import IntegrityError

    db = seeded
    user = _busy_user(db, chroma, backend, policies, email="atomic@example.com")
    for run_id in ("WR-a", "WR-b"):
        repos.insert_workflow_run(db, models.WorkflowRun(
            run_id=run_id, user_id=user.id, journey_id=None,
            trigger_type="EVENT_ACCUMULATION", gates={}, nodes=[],
            policy_version=policies.version, status="RUNNING",
            started_at=NOW, finished_at=NOW))
        if run_id == "WR-a":
            db.commit()
            continue
        with pytest.raises(IntegrityError):
            db.commit()
    db.rollback()
