"""Signature tests: the three things that break a deployed instance.

None of these are reasoning defects. They are the operational properties a
long-running host depends on, and each was found by asking what happens when
this runs somewhere other than a developer's laptop:

  1. A health check that answers "ok" while the process cannot serve a page
     tells a load balancer to send traffic to an instance that will time out.
  2. A background job that holds the single write lock for the length of its
     run makes every concurrent write fail, because SQLite has one writer.
  3. Background reasoning that can consume the whole thread pool means a slow
     provider stalls page rendering for everyone.
"""

import threading
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import apps.web.main as web
from smartreco import models
from smartreco.delivery import run_digest_cycle
from smartreco.seeding import seed_canonical_products, seed_capabilities


@pytest.fixture()
def client(session_factory, chroma, backend, policies, fake_gateway):
    web._state.clear()
    web._state.update({
        "policies": policies, "session_factory": session_factory,
        "chroma": chroma, "backend": backend, "gateway": fake_gateway,
    })
    with session_factory() as db:
        seed_capabilities(db)
        seed_canonical_products(db, chroma, backend)
        db.commit()
    with TestClient(web.app) as c:
        yield c
    web._state.clear()


# --- 1. Liveness and readiness are different questions ----------------------

def test_liveness_answers_immediately(client):
    """Liveness means the process is alive. It must never do work, or it
    becomes a way to fail a healthy instance under load."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_is_a_separate_endpoint_that_reports_the_real_state(client):
    """Readiness means the app can actually serve a request: settings loaded,
    catalog queryable, vector index populated.

    Measured on a cold start with an empty data directory, the first page
    request took 3m29s while `/health` had been answering "ok" the whole time.
    A platform health check pointed at liveness routes live traffic into that
    window."""
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["catalog"] > 0, "readiness did not verify the catalog"
    assert body["index"] > 0, "readiness did not verify the vector index"


def test_readiness_refuses_while_the_app_is_still_warming(client):
    """The failure this exists to prevent: 200 before the app can serve."""
    saved = dict(web._state)
    web._readiness.update(ready=False, detail="warming up")
    try:
        response = client.get("/ready")
        assert response.status_code == 503, "a warming instance advertised itself as ready"
        assert response.json()["ready"] is False
        # Liveness must still pass, or the platform restarts a healthy process
        assert client.get("/health").status_code == 200
    finally:
        web._readiness.update(ready=True, detail="ready")
        web._state.update(saved)


# --- 2. The digest must not hold the write lock for its whole run -----------

def test_the_digest_commits_per_user_not_once_at_the_end(session_factory, chroma,
                                                         backend, policies,
                                                         fake_gateway):
    """A ratchet on a property the cycle already has, not a fix.

    SQLite allows one writer. A cycle over 1000 users inside a *single*
    transaction would hold that writer for the length of the run, so every
    concurrent event ingest would fail once the 5-second busy timeout expired
    - the whole site down, not just the digest. Reading the code, the only
    visible `commit` is a trailing one, which is what that failure looks like.

    Measured, it is not: the per-user lifecycle sweep commits on every
    iteration, so the lock is released each time round. That is load-bearing
    and invisible - it lives in a function called for its own reasons, and
    someone could reasonably move it. This test fails if that happens.
    """
    from unittest.mock import patch

    from smartreco.models import utcnow

    users = 5
    with session_factory() as db:
        seed_capabilities(db)
        for i in range(users):
            db.add(models.User(email=f"d{i}@example.com", password_hash="x",
                               digest_opt_in=True, digest_channel="TELEGRAM",
                               telegram_chat_id=str(i)))
        db.commit()

    with session_factory() as db:
        with patch.object(db, "commit", wraps=db.commit) as spy:
            run_digest_cycle(db, chroma, backend, fake_gateway, policies, utcnow())
        assert spy.call_count >= users, (
            f"{users} users produced only {spy.call_count} commit(s) - the cycle "
            f"is one long transaction, so it holds the single write lock for its "
            f"whole duration and every concurrent write fails")

    # And the work is durable, which is what makes an interrupted cycle resumable.
    with session_factory() as db:
        assert len(db.execute(select(models.DeliveryRecord)).scalars().all()) == users


def test_rerunning_the_cycle_resumes_rather_than_repeats(session_factory, chroma,
                                                         backend, policies,
                                                         fake_gateway):
    """Bounded transactions are only safe because the window is idempotent:
    a user already recorded for today is skipped, so a second run continues
    where the first stopped instead of double-sending."""
    from smartreco.models import utcnow
    now = utcnow()
    with session_factory() as db:
        seed_capabilities(db)
        db.add(models.User(email="resume@example.com", password_hash="x",
                           digest_opt_in=True, digest_channel="TELEGRAM",
                           telegram_chat_id="1"))
        db.commit()

    with session_factory() as db:
        run_digest_cycle(db, chroma, backend, fake_gateway, policies, now)
    with session_factory() as db:
        first = db.execute(select(models.DeliveryRecord)).scalars().all()
        run_digest_cycle(db, chroma, backend, fake_gateway, policies, now)
    with session_factory() as db:
        second = db.execute(select(models.DeliveryRecord)).scalars().all()
    assert len(second) == len(first), "a second run in the same window duplicated work"


# --- 3. Background reasoning must not consume the whole thread pool ---------

def test_reasoning_runs_are_capped_so_a_slow_provider_cannot_stall_the_site(client):
    """Every event flush schedules a background trigger evaluation, and each
    one can hold a thread for up to the gateway timeout times its retries.
    The server's thread pool is 40; without a cap, a provider slowdown turns
    every page request into a queue.

    The cap sheds rather than queues: a skipped evaluation costs nothing,
    because the next flush raises the trigger again."""
    state = web._state
    cap = state["policies"].param("POL-TRIG-005", "max_concurrent_runs")
    assert cap >= 1

    slots = web._run_slots(state)
    held = [slots.acquire(blocking=False) for _ in range(cap)]
    assert all(held), "the limiter refused a slot below its own cap"
    try:
        assert slots.acquire(blocking=False) is False, (
            "the limiter handed out more slots than the cap allows")
    finally:
        for _ in held:
            slots.release()


def test_a_shed_evaluation_leaves_no_wreckage(client):
    """Shedding must be a no-op, not a half-run: no workflow row, no partial
    journey. The trigger will be raised again by the next flush."""
    state = web._state
    slots = web._run_slots(state)
    cap = state["policies"].param("POL-TRIG-005", "max_concurrent_runs")
    with state["session_factory"]() as db:
        user = models.User(email="shed@example.com", password_hash="x")
        db.add(user)
        db.commit()
        user_id = user.id
        before = len(db.execute(select(models.WorkflowRun)).scalars().all())

    held = [slots.acquire(blocking=False) for _ in range(cap)]
    try:
        web._evaluate_triggers_async(user_id)      # every slot taken
    finally:
        for _ in held:
            slots.release()

    with state["session_factory"]() as db:
        after = len(db.execute(select(models.WorkflowRun)).scalars().all())
    assert after == before, "a shed evaluation still wrote a workflow run"


# --- 4. A cold boot must actually complete ---------------------------------

def test_building_state_from_cold_does_not_deadlock(tmp_path, monkeypatch):
    """Every other test injects state, so nothing in the suite had ever run the
    constructor - and the constructor is what a deployed instance runs.

    Found by inspection while adding the readiness warm-up: construction holds
    the state lock and then calls the limiter accessor, which takes the same
    lock. With a non-reentrant lock that is a deadlock on first boot, invisible
    to a green suite and fatal on the host.
    """
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'boot.db'}")
    monkeypatch.setenv("CHROMA_PATH", str(tmp_path / "chroma"))
    monkeypatch.setenv("EMBEDDINGS_BACKEND", "local")
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)

    web._state.clear()
    web._readiness.update(ready=False, detail="warming up")
    done = threading.Event()
    error = []

    def boot():
        try:
            web._init_state()
        except Exception as exc:                  # a failure is a result; a hang is not
            error.append(exc)
        finally:
            done.set()

    thread = threading.Thread(target=boot, daemon=True)
    thread.start()
    finished = done.wait(timeout=180)
    try:
        assert finished, ("building state from cold never returned - the "
                          "constructor is deadlocked against its own lock")
        assert not error, f"cold boot raised {error[0]!r}"
        assert web._state.get("run_slots") is not None
    finally:
        scheduler = web._state.get("scheduler")
        if scheduler is not None:
            scheduler.shutdown(wait=False)
        web._state.clear()
