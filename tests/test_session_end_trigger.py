"""Signature tests: the SESSION_END trigger (Core 23 Trigger Types; POL-TRACK-003).

Core 23 has always listed SESSION_END — "a session closes with unprocessed
high/medium-signal activity; evaluate at session boundary". Nothing ever raised
it. Only EVENT_ACCUMULATION (from event ingestion) and SCHEDULED (the daily
digest) reached the evaluator, which meant reasoning could only ever happen
while the shopper was still clicking.

Found in a live trace. A shopper researched automation, bought ServiceNow, and
closed the tab. The purchase burst was four high-signal events — one short of
POL-TRIG-001's threshold, five at the time — so no run ever started: the journey stayed open, the
purchase was never reasoned about, and the recommendation the deterministic
engines were one run away from producing never appeared. Waiting could not fix
it; without a fifth click nothing would ever wake the evaluator again.

These pin the boundary the policy assumed: the sweep reasons about what a
departing shopper left behind, ignores one who is still shopping, and does not
re-reason about work it has already done.
"""

from datetime import datetime, timedelta

from sqlalchemy import select

from smartreco import models, repos
from smartreco.pipeline import session_end_sweep

NOW = datetime(2026, 8, 11, 20, 35)
SESSION_TIMEOUT = timedelta(minutes=30)  # POL-TRACK-003


PURCHASE_BURST = [
    ("PRODUCT_VIEWED", {"product_id": "PROD-007", "category": "workflow automation"}),
    ("ADD_TO_CART", {"product_id": "PROD-007"}),
    ("CHECKOUT_STARTED", {}),
    ("PURCHASE_COMPLETED", {"product_id": "PROD-007", "order_id": "ORD-test"}),
]


def _departed_shopper(db, policies, *, last_event_at, email="stranded@example.com"):
    """Case 3 from the live traces: an automation journey that ends in a
    purchase, and a closed tab.

    The burst is sized one event *below* POL-TRIG-001's threshold rather than
    at a literal four, because the point is the relationship — a visit that
    ends short of the accumulation threshold — not the tuning of the day. The
    threshold has already moved once for demo pacing (Decision #048); the
    defect this pins is the same at any value.
    """
    threshold = policies.param("POL-TRIG-001", "unprocessed_event_threshold")
    events = PURCHASE_BURST[-(threshold - 1):]  # still ends in the purchase
    assert 0 < len(events) < threshold

    user = models.User(email=email, password_hash="x", role="user")
    db.add(user)
    db.commit()
    db.add(models.Session(session_id="se1", user_id=user.id,
                          started_at=last_event_at - timedelta(minutes=5),
                          last_event_at=last_event_at))
    repos.insert_events_idempotent(db, [
        {"event_id": f"se-{i}", "user_id": user.id, "session_id": "se1",
         "journey_id": None, "event_type": event_type, "signal_class": "HIGH",
         "event_metadata": metadata, "ts": last_event_at,
         "received_at": last_event_at, "processed_at": None}
        for i, (event_type, metadata) in enumerate(events)])
    db.commit()
    return user


def _runs_for(db, user_id):
    return db.execute(select(models.WorkflowRun).where(
        models.WorkflowRun.user_id == user_id)).scalars().all()


def test_sweep_reasons_about_what_a_departing_shopper_left_behind(
        seeded, chroma, backend, policies, fake_gateway):
    """The defect itself: the burst ends below POL-TRIG-001's threshold, so
    only a session boundary can start this run."""
    db = seeded
    user = _departed_shopper(db, policies, last_event_at=NOW - SESSION_TIMEOUT - timedelta(minutes=1))

    runs = session_end_sweep(db, chroma, backend, policies, now=NOW, gateway=fake_gateway)

    assert [r.user_id for r in runs] == [user.id]
    assert runs[0].trigger_type == "SESSION_END"
    assert runs[0].status == "COMPLETED"

    journey = db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)).scalars().one()
    assert journey.lifecycle == "CLOSED"
    assert journey.outcome == "PURCHASED"

    pending = db.execute(select(models.Event).where(
        models.Event.user_id == user.id,
        models.Event.processed_at.is_(None))).scalars().all()
    assert pending == []


def test_sweep_leaves_a_shopper_who_is_still_shopping_alone(
        seeded, chroma, backend, policies, fake_gateway):
    """Mid-session quiet is not a session boundary. Reasoning early would spend
    the cooldown on an incomplete story."""
    db = seeded
    user = _departed_shopper(db, policies, last_event_at=NOW - timedelta(minutes=5))

    runs = session_end_sweep(db, chroma, backend, policies, now=NOW, gateway=fake_gateway)

    assert runs == []
    # Not even a SKIPPED row: an active shopper is not a trigger occasion, and
    # a sweep on a few minutes' interval would otherwise bury the trigger log
    # in non-events.
    assert _runs_for(db, user.id) == []


def test_sweep_does_not_re_reason_about_a_journey_it_has_finished(
        seeded, chroma, backend, policies, fake_gateway):
    """The completed run stamps the events processed, so the next tick finds
    nothing. Without this the sweep would re-run every user, every interval,
    forever."""
    db = seeded
    user = _departed_shopper(db, policies, last_event_at=NOW - SESSION_TIMEOUT - timedelta(minutes=1))

    first = session_end_sweep(db, chroma, backend, policies, now=NOW, gateway=fake_gateway)
    second = session_end_sweep(db, chroma, backend, policies,
                               now=NOW + timedelta(minutes=5), gateway=fake_gateway)

    assert len(first) == 1 and second == []
    assert len(_runs_for(db, user.id)) == 1


def test_sweep_ignores_low_signal_leftovers(
        seeded, chroma, backend, policies, fake_gateway):
    """Dwell heartbeats are LOW signal (Core 22). A session that left only
    reading time behind has left nothing to reason about."""
    db = seeded
    idle = NOW - SESSION_TIMEOUT - timedelta(minutes=1)
    user = models.User(email="dwell-only@example.com", password_hash="x", role="user")
    db.add(user)
    db.commit()
    db.add(models.Session(session_id="se2", user_id=user.id,
                          started_at=idle, last_event_at=idle))
    repos.insert_events_idempotent(db, [
        {"event_id": f"dw-{i}", "user_id": user.id, "session_id": "se2",
         "journey_id": None, "event_type": "DWELL", "signal_class": "LOW",
         "event_metadata": {"topic": "security", "seconds": 10}, "ts": idle,
         "received_at": idle, "processed_at": None}
        for i in range(6)])
    db.commit()

    assert session_end_sweep(db, chroma, backend, policies, now=NOW,
                             gateway=fake_gateway) == []
