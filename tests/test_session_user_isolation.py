"""Signature tests: one browser, two shoppers — sessions and journeys must not
bleed across accounts (docs/core/22 § Session Identity; Decision #043).

Found by live browsing. The tracking client keeps its session id in
`sessionStorage`, which is scoped to the tab and origin — not to the logged-in
user — so logging out and in as someone else keeps sending the same id. The
ingest endpoint looked the session up by that client-supplied id alone:

    session_row = touched_sessions.get(sid) or db.get(models.Session, sid)

and journey resolution then short-circuits on a session that already owns a
journey:

    if session_row is not None and session_row.journey_id:
        repos.assign_journey(db, session_id, session_row.journey_id)

Neither checked who the session belonged to. In the live database one session
row owned by user 8 carried 23 events from user 6, and 20 of user 6's events
were filed into user 8's journey. Worse, user 6's *workflow runs* then wrote
new Requirement Profiles and Recommendation Packages onto user 8's journey —
one shopper's browsing changed another shopper's recommendations.

Candidate scoring was never at fault: `resolve_sessions` already filters
candidate journeys by user. Both holes are identity holes, so both are closed
by identity: the stored session key is namespaced per user, and journey
assignment filters by user as well as session.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import apps.web.main as web
from smartreco import models
from smartreco.pipeline import resolve_sessions
from smartreco.seeding import seed_canonical_products, seed_capabilities

# The literal id a single browser tab reuses across a logout/login.
SHARED_CLIENT_SESSION = "s-one-browser-tab"

RESEARCH = [
    ("SEARCH", {"query": "single sign-on"}),
    ("PRODUCT_VIEWED", {"product_id": "PROD-003"}),
    ("SECURITY_VIEWED", {"product_id": "PROD-003", "page": "p", "topic": "audit"}),
    ("DOCUMENTATION_VIEWED", {"product_id": "PROD-003", "topic": "sso"}),
    ("PRICING_VIEWED", {"product_id": "PROD-003", "tier": "enterprise"}),
    ("DOCUMENTATION_VIEWED", {"product_id": "PROD-003", "topic": "provisioning"}),
]


@pytest.fixture()
def client(session_factory, chroma, backend, policies):
    web._state.clear()
    web._state.update({"policies": policies, "session_factory": session_factory,
                       "chroma": chroma, "backend": backend})
    with session_factory() as db:
        seed_capabilities(db)
        seed_canonical_products(db, chroma, backend)
    with TestClient(web.app) as test_client:
        yield test_client
    web._state.clear()


def _register(client, email):
    assert client.post("/auth/register",
                       json={"email": email, "password": "pw123456"}).status_code == 201


def _login(client, email):
    assert client.post("/auth/login",
                       json={"email": email, "password": "pw123456"}).status_code == 200


def _browse(client, who):
    """Post one shopper's research under the id the tab has been reusing."""
    events = [{"event_id": f"{who}-{i}", "session_id": SHARED_CLIENT_SESSION,
               "event_type": etype, "ts": "2026-08-01T09:00:00Z", "metadata": md}
              for i, (etype, md) in enumerate(RESEARCH)]
    assert client.post("/events/batch", json={"events": events}).status_code == 202


def _user_id(db, email):
    return db.execute(select(models.User.id).where(
        models.User.email == email)).scalars().one()


@pytest.fixture()
def two_shoppers(client, session_factory, policies):
    """First shopper researches and gets a journey; second shopper takes over
    the same tab and researches too."""
    _register(client, "first@example.com")
    _browse(client, "first")
    with session_factory() as db:
        first = _user_id(db, "first@example.com")
        resolve_sessions(db, policies, first)
        db.commit()

    _register(client, "second@example.com")   # registering logs the tab in as them
    _login(client, "second@example.com")
    _browse(client, "second")
    with session_factory() as db:
        second = _user_id(db, "second@example.com")
        resolve_sessions(db, policies, second)
        db.commit()
    return first, second


def test_a_second_shopper_does_not_inherit_the_first_ones_journey(
        two_shoppers, session_factory):
    """The live failure. The second shopper's events must never be filed into
    a journey owned by whoever used the tab before them."""
    first, second = two_shoppers
    with session_factory() as db:
        first_journeys = {j.journey_id for j in db.execute(select(models.Journey).where(
            models.Journey.user_id == first)).scalars()}
        stolen = db.execute(select(models.Event).where(
            models.Event.user_id == second,
            models.Event.journey_id.in_(first_journeys))).scalars().all()
        assert not stolen, (
            f"{len(stolen)} of the second shopper's events landed in the first "
            f"shopper's journey {first_journeys}")


def test_no_journey_ever_holds_two_shoppers_events(two_shoppers, session_factory):
    """Stated from the journey's side, because this is what corrupts the
    decision spine: evidence, requirements and packages are derived from a
    journey's events, so one foreign event is enough to change someone else's
    recommendations."""
    _first, _second = two_shoppers
    with session_factory() as db:
        for journey in db.execute(select(models.Journey)).scalars():
            owners = set(db.execute(select(models.Event.user_id).where(
                models.Event.journey_id == journey.journey_id)).scalars().all())
            assert len(owners) <= 1, (
                f"journey {journey.journey_id} (owner {journey.user_id}) holds "
                f"events from users {sorted(owners)}")


def test_no_session_row_ever_holds_two_shoppers_events(two_shoppers, session_factory):
    """The root cause, pinned directly: the server must not let a
    client-supplied session id join two accounts, whatever the client sends."""
    _first, _second = two_shoppers
    with session_factory() as db:
        for row in db.execute(select(models.Session)).scalars():
            owners = set(db.execute(select(models.Event.user_id).where(
                models.Event.session_id == row.session_id)).scalars().all())
            assert len(owners) <= 1, (
                f"session {row.session_id} (owner {row.user_id}) carries events "
                f"from users {sorted(owners)}")


def test_each_shopper_still_gets_their_own_journey(two_shoppers, session_factory):
    """Isolation must not be achieved by dropping the newcomer's events —
    silently discarding them would pass every assertion above."""
    first, second = two_shoppers
    with session_factory() as db:
        for user_id in (first, second):
            events = db.execute(select(models.Event).where(
                models.Event.user_id == user_id)).scalars().all()
            assert len(events) == len(RESEARCH), (
                f"user {user_id} kept {len(events)} of {len(RESEARCH)} events")
            assert all(e.journey_id for e in events), (
                f"user {user_id} has events no journey owns")
            journeys = {e.journey_id for e in events}
            assert len(journeys) == 1, f"user {user_id} was split across {journeys}"


def test_journey_assignment_filters_on_the_user_not_just_the_session(seeded, policies):
    """The second lock, pinned where the endpoint's namespacing cannot reach it.

    Namespaced keys mean two users can no longer share a session id *through the
    endpoint*, so this constructs the collision directly. `assign_journey` is the
    write that puts events on the decision spine; it must not move a row it does
    not own, whatever session id it is handed.
    """
    from smartreco import repos

    db = seeded
    owner = models.User(email="owner@example.com", password_hash="x", role="user")
    other = models.User(email="other@example.com", password_hash="x", role="user")
    db.add_all([owner, other])
    db.commit()

    ts = models.utcnow()
    db.add(models.Session(session_id="collision", user_id=owner.id,
                          started_at=ts, last_event_at=ts))
    repos.insert_events_idempotent(db, [
        {"event_id": f"iso-{who.id}", "user_id": who.id, "session_id": "collision",
         "journey_id": None, "event_type": "PRODUCT_VIEWED", "signal_class": "HIGH",
         "event_metadata": {"product_id": "PROD-003"}, "ts": ts, "received_at": ts,
         "processed_at": None}
        for who in (owner, other)])
    db.add(models.Journey(journey_id="J-owner", user_id=owner.id,
                          lifecycle="ACTIVE", created_at=ts))
    db.commit()

    repos.assign_journey(db, "collision", "J-owner", owner.id)
    db.commit()

    assert db.get(models.Event, f"iso-{owner.id}").journey_id == "J-owner"
    assert db.get(models.Event, f"iso-{other.id}").journey_id is None, (
        "assignment moved an event belonging to another user")


def test_the_two_shoppers_journeys_are_distinct(two_shoppers, session_factory):
    """And they are two journeys, not one shared row that happens to pass the
    per-user checks."""
    first, second = two_shoppers
    with session_factory() as db:
        def journey_of(user_id):
            return db.execute(select(models.Event.journey_id).where(
                models.Event.user_id == user_id)).scalars().first()
        assert journey_of(first) != journey_of(second)
