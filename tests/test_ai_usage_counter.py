"""Signature tests: the AI-usage counter and SQLite write contention.

Both found by running the live app, and both crashed a real workflow run.

`record_ai_call` looked the counter up with `Session.get`, which consults the
identity map — and a row that has been `add`ed but not flushed is not in it.
Sessions are configured `autoflush=False`, so the second Tier-2 call of a run
(embeddings, then retrieval evaluation) saw None, added a second row for the
same key, and the flush emitted both:

    UNIQUE constraint failed: ai_usage.user_id, ai_usage.day, ai_usage.tier
        ... in do_executemany

That killed the run after it had already committed a new Requirement Profile,
leaving the journey with requirements and a stale package until the next run
recomputed it.

Separately, SQLite defaults `busy_timeout` to zero: a writer that finds the
database locked fails immediately rather than waiting. With tracking flushes
and a background trigger evaluation both writing, that surfaced as
`OperationalError: database is locked`.
"""

from datetime import datetime

from sqlalchemy import select

from smartreco import models
from smartreco.db import make_engine
from smartreco.pipeline import record_ai_call

NOW = datetime(2026, 8, 11, 12, 0)


def _user(db, email="usage@example.com"):
    row = models.User(email=email, password_hash="x", role="user")
    db.add(row)
    db.commit()
    return row


def test_two_calls_in_one_run_increment_rather_than_duplicate(seeded):
    """The exact live failure: one run records two Tier-2 calls before any
    flush. Budget accounting must count them, not raise."""
    db = seeded
    user = _user(db)

    record_ai_call(db, user.id, "tier2", NOW)
    record_ai_call(db, user.id, "tier2", NOW)
    db.commit()

    rows = db.execute(select(models.AIUsage).where(
        models.AIUsage.user_id == user.id)).scalars().all()
    assert len(rows) == 1, f"duplicate counter rows for one key: {rows}"
    assert rows[0].calls == 2, f"calls lost: {rows[0].calls}"


def test_many_calls_accumulate(seeded):
    """Budgets are 10/20 per day (POL-TRIG-003); the counter must survive a
    full day's worth of calls in a single session."""
    db = seeded
    user = _user(db, "usage2@example.com")
    for _ in range(20):
        record_ai_call(db, user.id, "tier2", NOW)
    db.commit()
    row = db.execute(select(models.AIUsage).where(
        models.AIUsage.user_id == user.id)).scalars().one()
    assert row.calls == 20


def test_tiers_and_days_stay_separate(seeded):
    """The fix must not collapse distinct keys into one counter."""
    db = seeded
    user = _user(db, "usage3@example.com")
    record_ai_call(db, user.id, "tier1", NOW)
    record_ai_call(db, user.id, "tier2", NOW)
    record_ai_call(db, user.id, "tier2", datetime(2026, 8, 12, 9, 0))
    db.commit()
    rows = db.execute(select(models.AIUsage).where(
        models.AIUsage.user_id == user.id)).scalars().all()
    assert len(rows) == 3, [(r.day, r.tier, r.calls) for r in rows]
    assert all(r.calls == 1 for r in rows)


def test_sqlite_waits_for_a_busy_database_instead_of_failing():
    """A zero busy_timeout turns ordinary write contention into an error. The
    app writes from request handlers and background trigger evaluations at the
    same time, so contention is expected, not exceptional."""
    engine = make_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        timeout_ms = conn.exec_driver_sql("PRAGMA busy_timeout").scalar()
    assert timeout_ms and timeout_ms >= 5000, (
        f"busy_timeout is {timeout_ms}ms — a concurrent writer fails instead "
        f"of waiting")


def test_recording_a_call_does_not_take_the_write_lock_early(seeded):
    """The counter must stay pending until the caller commits.

    Flushing here looked like the obvious fix for the duplicate key, and it
    made contention worse: the flush takes SQLite's write lock, and the very
    next thing a run does after recording a Tier-2 call is make a gateway
    request. Holding a write lock across network latency turned ordinary
    concurrency into "database is locked" for every other writer — which is
    exactly how a second live run died.
    """
    db = seeded
    user = _user(db, "nolock@example.com")
    record_ai_call(db, user.id, "tier2", NOW)
    assert any(isinstance(o, models.AIUsage) for o in db.new), (
        "counter was flushed instead of left pending")
    assert not db.in_nested_transaction()
