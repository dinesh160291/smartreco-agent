"""Signature tests: journey ownership waits for a session to say enough
(docs/core/12 § Session Settlement, POL-JRES-001 min_session_events).

Found in a live trace. A shopper browsed analytics products, paused three
minutes, and resumed in the same category. Resolution ran while the resumed
session was two events old, scored 0.438 against the existing journey, and
forked. Seven events later the same session scored 0.653 — a clear CONTINUE.
Ownership is decided exactly once per session (Core 12), so the premature call
was permanent and the rest of the session landed in an empty journey.

The cost was not cosmetic: the stranded events carried the second piece of
evidence for a concept that already had one, which is what POL-BEH-001 needs
to promote a hypothesis. Split across two journeys, neither half reached the
bar, and the shopper saw no recommendations.

The scoring was never wrong — it was asked too early. These pin *when* the
question may be asked.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from smartreco import models, repos
from smartreco.pipeline import resolve_sessions

BASE = datetime(2026, 8, 10, 19, 0)


def _events(db, user_id, session_id, specs, start):
    """Insert events and their session row; specs = [(type, metadata), …]."""
    if db.get(models.Session, session_id) is None:
        db.add(models.Session(session_id=session_id, user_id=user_id,
                              started_at=start, last_event_at=start))
    rows = []
    for i, (event_type, metadata) in enumerate(specs):
        ts = start + timedelta(seconds=10 * i)
        rows.append({"event_id": f"{session_id}-{i}", "user_id": user_id,
                     "session_id": session_id, "journey_id": None,
                     "event_type": event_type, "signal_class": "HIGH",
                     "event_metadata": metadata, "ts": ts, "received_at": ts,
                     "processed_at": None})
    repos.insert_events_idempotent(db, rows)
    db.commit()
    return start + timedelta(seconds=10 * len(specs))


ANALYTICS_FIRST_SESSION = [
    ("SEARCH", {"query": "analytics"}),
    ("PRODUCT_VIEWED", {"product_id": "PROD-156", "category": "data & analytics"}),
    ("DOCUMENTATION_VIEWED", {"product_id": "PROD-156", "topic": "api"}),
    ("PRODUCT_VIEWED", {"product_id": "PROD-158", "category": "data & analytics"}),
    ("DOCUMENTATION_VIEWED", {"product_id": "PROD-158", "topic": "integrations"}),
    ("PRICING_VIEWED", {"product_id": "PROD-158", "tier": "enterprise"}),
]
# The resumed session, in the order the shopper produced it. The first two
# events look like almost nothing; the rest make the continuation obvious.
RESUMED_SESSION = [
    ("CATEGORY_VIEWED", {"category": "Data & Analytics"}),
    ("PRODUCT_VIEWED", {"product_id": "PROD-149", "category": "data & analytics"}),
    ("DOCUMENTATION_VIEWED", {"product_id": "PROD-149", "topic": "integrations"}),
    ("DOCUMENTATION_VIEWED", {"product_id": "PROD-149", "topic": "api"}),
    ("PRICING_VIEWED", {"product_id": "PROD-149", "tier": "enterprise"}),
]


@pytest.fixture()
def user(seeded):
    row = models.User(email="settle@example.com", password_hash="x", role="user")
    seeded.add(row)
    seeded.commit()
    return row


def _journeys(db, user_id):
    return db.execute(select(models.Journey).where(
        models.Journey.user_id == user_id)).scalars().all()


def test_a_barely_started_session_does_not_get_its_own_journey(seeded, policies, user):
    """The regression. Two events is not enough to conclude 'different mission',
    and the conclusion cannot be revised later."""
    db = seeded
    resolve_sessions(db, policies, user.id, now=BASE + timedelta(minutes=2))
    _events(db, user.id, "s1", ANALYTICS_FIRST_SESSION, BASE)
    resolve_sessions(db, policies, user.id, now=BASE + timedelta(minutes=2))
    assert len(_journeys(db, user.id)) == 1

    # resumed three minutes later; resolution runs when only two events exist
    resume = BASE + timedelta(minutes=8)
    _events(db, user.id, "s2", RESUMED_SESSION[:2], resume)
    resolve_sessions(db, policies, user.id, now=resume + timedelta(seconds=30))

    assert len(_journeys(db, user.id)) == 1, (
        "a two-event session was given its own journey; ownership is decided "
        "once, so this cannot be undone when the session fills out")


def test_once_the_session_has_spoken_it_continues_the_same_journey(seeded, policies, user):
    """And the deferral must actually resolve — deferring forever would strand
    the events instead of misfiling them, which is no better."""
    db = seeded
    _events(db, user.id, "s1", ANALYTICS_FIRST_SESSION, BASE)
    resolve_sessions(db, policies, user.id, now=BASE + timedelta(minutes=2))
    first = _journeys(db, user.id)[0].journey_id

    resume = BASE + timedelta(minutes=8)
    _events(db, user.id, "s2", RESUMED_SESSION, resume)
    resolve_sessions(db, policies, user.id, now=resume + timedelta(minutes=2))

    journeys = _journeys(db, user.id)
    assert len(journeys) == 1, f"session forked despite continuing the mission: {journeys}"
    assigned = db.execute(select(models.Event.journey_id).where(
        models.Event.session_id == "s2")).scalars().all()
    assert set(assigned) == {first}, "resumed events did not join the original journey"


def test_a_short_session_still_resolves_once_it_is_over(seeded, policies, user):
    """Deferral is bounded. A shopper who views two pages and leaves must still
    have those events owned by a journey — silence must not mean limbo."""
    db = seeded
    _events(db, user.id, "s1", ANALYTICS_FIRST_SESSION, BASE)
    resolve_sessions(db, policies, user.id, now=BASE + timedelta(minutes=2))

    resume = BASE + timedelta(minutes=8)
    _events(db, user.id, "s2", RESUMED_SESSION[:2], resume)
    # long enough after the last event that the session has timed out
    resolve_sessions(db, policies, user.id, now=resume + timedelta(hours=2))

    unassigned = db.execute(select(models.Event).where(
        models.Event.session_id == "s2",
        models.Event.journey_id.is_(None))).scalars().all()
    assert not unassigned, "a finished session was left permanently unresolved"


def test_a_superseded_session_resolves_even_while_small(seeded, policies, user):
    """A newer session proves the older one is finished, so its size no longer
    matters — waiting for events that will never arrive is limbo again."""
    db = seeded
    _events(db, user.id, "s1", ANALYTICS_FIRST_SESSION, BASE)
    resolve_sessions(db, policies, user.id, now=BASE + timedelta(minutes=2))

    short = BASE + timedelta(minutes=8)
    _events(db, user.id, "s2", RESUMED_SESSION[:2], short)
    _events(db, user.id, "s3", RESUMED_SESSION, short + timedelta(minutes=5))
    resolve_sessions(db, policies, user.id, now=short + timedelta(minutes=7))

    unassigned = db.execute(select(models.Event).where(
        models.Event.session_id == "s2",
        models.Event.journey_id.is_(None))).scalars().all()
    assert not unassigned, "superseded session left unresolved"
