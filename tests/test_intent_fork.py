"""Signature tests: intent divergence within a session (Decision #056).

A shopper who starts on analytics and switches to DevOps inside one session was
previously filed under a single journey, because Decision #041 settles journey
ownership exactly once per session. Both intents then shared one Requirement
Profile, and the first one to accumulate dominated the ranking — Data & Insight
sat Critical at x3 weight while the DevOps need the shopper had actually moved
on to sat Medium at x1.

The test of "different subject" is the *concepts* the evidence supports, not
overlap between entity sets. Entity Jaccard was tried and rejected: over short
blocks it is dominated by product ids, so a shopper comparing five analytics
tools looks like five changes of subject.
"""

import pytest

from smartreco.engines.journey_resolution import subject_abandoned


def test_abandoning_the_journeys_subject_forks():
    """Established on analytics, recent activity is all engineering delivery."""
    assert subject_abandoned("BC-024", {"BC-023"}) is True


def test_still_doing_it_does_not_fork():
    assert subject_abandoned("BC-024", {"BC-024"}) is False


def test_a_transitional_block_does_not_fork():
    """The block where the shopper is doing both. This is the case the first
    rule got wrong: it merged here (rightly) and could never fork afterwards,
    because the journey's history then contained both subjects for good."""
    assert subject_abandoned("BC-024", {"BC-024", "BC-023"}) is False


def test_widening_and_still_returning_never_forks():
    """A shopper who keeps coming back to the original subject has widened
    their evaluation, not left it — however many other subjects they touch."""
    assert subject_abandoned("BC-024", {"BC-024", "BC-023", "BC-021"}) is False


def test_evidence_carrying_no_subject_never_forks():
    """Pricing, comparisons and security research say how far along a shopper
    is, not what they are shopping for — they must never fork a journey."""
    assert subject_abandoned("BC-024", set()) is False
    assert subject_abandoned(None, {"BC-024"}) is False
    assert subject_abandoned(None, set()) is False


# --- Integration: the session that prompted this (Decision #056) -------------

from datetime import datetime, timedelta

from sqlalchemy import select

from smartreco import models
from smartreco.pipeline import run_workflow
from tests.test_stories_6_to_9 import _insert, _user

DAY = datetime(2026, 8, 12, 9, 0)


def _analytics(prefix, n=6):
    return [
        (f"{prefix}1", "SEARCH", "HIGH", {"query": "analytics"}),
        (f"{prefix}2", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-009", "category": "data & analytics"}),
        (f"{prefix}3", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "pipelines-data"}),
        (f"{prefix}4", "SEARCH", "HIGH", {"query": "etl warehouse"}),
        (f"{prefix}5", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "warehouse"}),
        (f"{prefix}6", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "dashboards"}),
    ][:n]


def _devops(prefix, n=6):
    return [
        (f"{prefix}1", "SEARCH", "HIGH", {"query": "cicd"}),
        (f"{prefix}2", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-006", "category": "devops"}),
        (f"{prefix}3", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "cicd"}),
        (f"{prefix}4", "SEARCH", "HIGH", {"query": "monitoring observability"}),
        (f"{prefix}5", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "monitoring"}),
        (f"{prefix}6", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "incidents"}),
        (f"{prefix}7", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-002", "category": "devops"}),
        (f"{prefix}8", "SEARCH", "HIGH", {"query": "kubernetes deployment"}),
        (f"{prefix}9", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "containers"}),
        (f"{prefix}10", "CATEGORY_VIEWED", "MEDIUM", {"category": "devops"}),
        (f"{prefix}11", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "cicd"}),
        (f"{prefix}12", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-007", "category": "devops"}),
        (f"{prefix}13", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "monitoring"}),
        (f"{prefix}14", "SEARCH", "HIGH", {"query": "devops incidents"}),
        (f"{prefix}15", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "incidents"}),
        (f"{prefix}16", "CATEGORY_VIEWED", "MEDIUM", {"category": "devops"}),
    ][:n]


def _switch_to_devops(db, chroma, backend, policies, user, gw, s, prefix, at):
    """Move to DevOps and stay there.

    Deliberately more than a couple of clicks: the fork fires once the journey's
    established subject is absent from recent activity (POL-JRES-001
    recent_window_events), so it takes a shopper who has actually moved on
    rather than one who glanced sideways. Two batches, as a real session would
    deliver them.
    """
    _insert(db, user.id, s, at, _devops(prefix, 8))
    _run(db, chroma, backend, policies, user, gw, at + timedelta(minutes=2))
    _insert(db, user.id, s, at + timedelta(minutes=4), _devops(prefix + "x", 8))
    _run(db, chroma, backend, policies, user, gw, at + timedelta(minutes=6))


def _run(db, chroma, backend, policies, user, gw, at):
    return run_workflow(db, chroma, backend, policies, user.id,
                        "EVENT_ACCUMULATION", now=at, gateway=gw)


def _journeys(db, user):
    return db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)
        .order_by(models.Journey.created_at)).scalars().all()


def test_changing_subject_midsession_opens_a_second_journey(
        seeded, chroma, backend, policies, fake_gateway):
    """The reported behaviour: intent A then intent B inside one session.

    Both intents used to share one Requirement Profile, so the earlier one kept
    the higher priority band and the ranking answered a question the shopper
    had stopped asking.
    """
    db = seeded
    user = _user(db, "switcher@example.com")
    s = "fork-s1"

    _insert(db, user.id, s, DAY, _analytics("a"))
    _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=2))
    assert len(_journeys(db, user)) == 1

    _switch_to_devops(db, chroma, backend, policies, user, fake_gateway, s, "b",
                      DAY + timedelta(minutes=5))

    journeys = _journeys(db, user)
    assert len(journeys) == 2, (
        "the shopper changed subject inside one session and it stayed on one journey")

    # The new journey holds only the DevOps evidence — nothing bled across.
    second = journeys[1].journey_id
    concepts = {h.concept_id for h in db.execute(select(models.Hypothesis).where(
        models.Hypothesis.journey_id == second)).scalars().all()}
    assert "BC-023" in concepts, f"second journey has no engineering-delivery belief: {concepts}"
    assert "BC-024" not in concepts, (
        f"analytics belief followed the shopper into the new journey: {concepts}")

    # ...and the abandoned journey keeps its own belief, at the confidence it
    # reached. It may also hold some engineering-delivery evidence from the
    # transitional block — the stretch where the shopper was doing both stays
    # with the journey that was running, by design (Decision #057). What must
    # hold is that analytics is still what that journey is *about*.
    first_id = journeys[0].journey_id
    first = {h.concept_id: h.confidence for h in db.execute(select(models.Hypothesis).where(
        models.Hypothesis.journey_id == first_id)).scalars().all()}
    assert "BC-024" in first, f"the abandoned journey lost its own subject: {first}"
    assert first["BC-024"] >= first.get("BC-023", 0.0), (
        f"engineering delivery took over the analytics journey: {first}")


def test_staying_on_one_subject_does_not_fork(
        seeded, chroma, backend, policies, fake_gateway):
    """The control. Breadth inside a subject — different products, different
    searches — is not a change of subject, and entity overlap alone could not
    tell the two apart."""
    db = seeded
    user = _user(db, "steady@example.com")
    s = "fork-s2"
    _insert(db, user.id, s, DAY, _analytics("c"))
    _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=2))
    _insert(db, user.id, s, DAY + timedelta(minutes=5), [
        ("d1", "SEARCH", "HIGH", {"query": "bi dashboards"}),
        ("d2", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-010", "category": "data & analytics"}),
        ("d3", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "warehouse"}),
        ("d4", "PRICING_VIEWED", "HIGH", {"product_id": "PROD-010", "tier": "enterprise"}),
        ("d5", "COMPARISON_STARTED", "HIGH", {"product_a": "PROD-010", "product_b": "PROD-009"}),
        ("d6", "SEARCH", "HIGH", {"query": "analytics pricing"}),
    ])
    _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=7))
    assert len(_journeys(db, user)) == 1, "widening within one subject forked the journey"


def test_returning_to_the_first_subject_resumes_that_journey(
        seeded, chroma, backend, policies, fake_gateway):
    """A -> B -> A opens two journeys, not three, and the analytics beliefs
    resume where they were rather than starting over."""
    db = seeded
    user = _user(db, "returner2@example.com")
    s = "fork-s3"

    _insert(db, user.id, s, DAY, _analytics("e"))
    _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=2))
    first = _journeys(db, user)[0].journey_id
    before = {h.concept_id: h.confidence for h in db.execute(select(models.Hypothesis).where(
        models.Hypothesis.journey_id == first)).scalars().all()}

    _switch_to_devops(db, chroma, backend, policies, user, fake_gateway, s, "f",
                      DAY + timedelta(minutes=5))
    assert len(_journeys(db, user)) == 2

    _insert(db, user.id, s, DAY + timedelta(minutes=10), [
        ("g1", "SEARCH", "HIGH", {"query": "warehouse analytics"}),
        ("g2", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-009", "category": "data & analytics"}),
        ("g3", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "dashboards"}),
        ("g4", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "pipelines-data"}),
        ("g5", "SEARCH", "HIGH", {"query": "bi"}),
        ("g6", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "warehouse"}),
    ])
    _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=12))

    assert len(_journeys(db, user)) == 2, "returning to the first subject opened a third journey"
    after = {h.concept_id: h.confidence for h in db.execute(select(models.Hypothesis).where(
        models.Hypothesis.journey_id == first)).scalars().all()}
    assert after["BC-024"] >= before["BC-024"], (
        "resumed journey lost ground instead of continuing from where it was")


def test_for_you_shows_the_abandoned_journey_without_ranking_it(
        session_factory, chroma, backend, policies, fake_gateway):
    """Both journeys visible, only one ranking (Decision #056).

    The point of splitting is that the subject a shopper moved away from stops
    competing in the ranking. Showing it on the page is what stops that from
    reading as amnesia — and it must be named in shopper vocabulary, never by
    requirement code.
    """
    import apps.web.main as web
    from fastapi.testclient import TestClient
    from smartreco.seeding import seed_canonical_products, seed_capabilities

    web._state.clear()
    web._state.update({"policies": policies, "session_factory": session_factory,
                       "chroma": chroma, "backend": backend, "gateway": fake_gateway})
    try:
        with session_factory() as db:
            seed_capabilities(db)
            seed_canonical_products(db, chroma, backend)
            db.add(models.User(email="split@example.com",
                               password_hash=web._hash_password("pw123456"), role="user"))
            db.commit()
            user = db.query(models.User).filter(
                models.User.email == "split@example.com").one()
            s = "ui-fork-s1"
            # Analytics, built up until it publishes a requirement — each batch
            # brings a kind of signal the last lacked, so it accumulates rather
            # than damping (Decision #054). A journey with no ranking has
            # nothing to show on the strip, which is why the thin version of
            # this setup proved nothing.
            for i, batch in enumerate([
                [("h1", "SEARCH", "HIGH", {"query": "analytics"}),
                 ("h2", "SEARCH", "HIGH", {"query": "etl warehouse"}),
                 ("h3", "COMPARISON_STARTED", "HIGH", {"product_a": "PROD-009"})],
                [("h4", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "pipelines-data"}),
                 ("h5", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "warehouse"}),
                 ("h6", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "dashboards"})],
                [("h7", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-009", "category": "data & analytics"}),
                 ("h8", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-010", "category": "data & analytics"}),
                 ("h9", "PRICING_VIEWED", "HIGH", {"product_id": "PROD-009"})],
                [("h10", "CATEGORY_VIEWED", "MEDIUM", {"category": "data & analytics"}),
                 ("h11", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "warehouse"}),
                 ("h12", "PRICING_VIEWED", "HIGH", {"product_id": "PROD-010"})],
            ]):
                _insert(db, user.id, s, DAY + timedelta(minutes=3 * i), batch)
                _run(db, chroma, backend, policies, user, fake_gateway,
                     DAY + timedelta(minutes=3 * i + 2))
            first = _journeys(db, user)[0].journey_id
            pkg = db.execute(select(models.RecommendationPackage).where(
                models.RecommendationPackage.journey_id == first)
                .order_by(models.RecommendationPackage.created_at.desc())).scalars().first()
            assert pkg is not None and pkg.entries, (
                "precondition: the analytics journey never produced a ranking")

            _switch_to_devops(db, chroma, backend, policies, user, fake_gateway, s, "i",
                              DAY + timedelta(minutes=20))
            assert len(_journeys(db, user)) == 2, "precondition: the session should have forked"

        with TestClient(web.app) as c:
            c.post("/auth/login", json={"email": "split@example.com", "password": "pw123456"})
            html = c.get("/for-you").text

        assert "Also exploring" in html, "the abandoned journey is invisible on For-You"
        for banned in ("REQ-", "BC-", "BP-", "CAP-"):
            assert banned not in html, f"{banned} code leaked onto a shopper surface"
    finally:
        web._state.clear()


# --- A dwell heartbeat must not decide which journey a run reasons about ------
# (Decision #066; found while auditing the 95 events stuck at processed_at NULL)

def test_low_signal_events_are_stamped_processed_once_consumed(
        seeded, chroma, backend, policies, fake_gateway):
    """`data-model.md`: processed_at is "set when behavioral reasoning consumed
    it". Dwell is consumed — BP-001 sums security dwell to reach Strong — but
    only the high/medium slice was ever stamped, so every dwell heartbeat a
    shopper ever emitted stayed pending for the life of the database.
    """
    db = seeded
    user = _user(db, "dwell-stamp@example.com")
    _insert(db, user.id, "dwell-s1", DAY, _analytics("j") + [
        ("j7", "DWELL", "LOW", {"topic": "security", "seconds": 45})])
    run = _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=2))
    assert run.status == "COMPLETED"

    pending = db.execute(select(models.Event).where(
        models.Event.user_id == user.id,
        models.Event.processed_at.is_(None))).scalars().all()
    assert pending == [], (
        f"{len(pending)} event(s) still pending after a completed run: "
        f"{[e.event_type for e in pending]}")


def test_a_stale_dwell_does_not_route_a_run_to_an_abandoned_journey(
        seeded, chroma, backend, policies, fake_gateway):
    """The consequence, and the reason this is not bookkeeping.

    Journey ownership for a run is the journey of the newest *unprocessed*
    event. With dwell never stamped, the only pending events are dwell
    heartbeats — so a trigger that carries no condition of its own (SCHEDULED,
    the daily digest) reasons about whichever journey last had a heartbeat.
    For a shopper who has forked, that is the subject they walked away from.
    """
    db = seeded
    user = _user(db, "dwell-route@example.com")
    s = "dwell-s2"

    _insert(db, user.id, s, DAY, _analytics("k") + [
        ("k7", "DWELL", "LOW", {"topic": "security", "seconds": 30})])
    _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=2))
    abandoned = _journeys(db, user)[0].journey_id

    _switch_to_devops(db, chroma, backend, policies, user, fake_gateway, s, "l",
                      DAY + timedelta(minutes=5))
    assert len(_journeys(db, user)) == 2, "precondition: the session should have forked"

    scheduled = run_workflow(db, chroma, backend, policies, user.id, "SCHEDULED",
                             now=DAY + timedelta(minutes=30), gateway=fake_gateway)
    assert scheduled.journey_id != abandoned, (
        "a dwell heartbeat from before the fork pulled the run back onto the "
        "journey the shopper left")


def test_dwell_heartbeats_alone_never_trigger_a_run(
        seeded, chroma, backend, policies, fake_gateway):
    """POL-TRIG-001 counts unprocessed *high/medium*-signal events, and Law 9
    forbids an AI call per raw event. Dwell is sampled by heartbeat, so if it
    counted toward the accumulation threshold a shopper sitting still on one
    page would trigger runs indefinitely.

    This is the guard on the distinction Decision #066 introduced: the stamp
    covers every pending event, the trigger gate still sees only high/medium.
    """
    db = seeded
    user = _user(db, "dwell-trigger@example.com")
    _insert(db, user.id, "dwell-s3", DAY, [
        (f"m{i}", "DWELL", "LOW", {"topic": "security", "seconds": 20})
        for i in range(6)])   # twice POL-TRIG-001's threshold

    run = _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=2))
    assert run.status == "SKIPPED", f"dwell heartbeats triggered a run: {run.gates}"


# --- For-You must follow the shopper, not the clock (#071) -------------------

def test_for_you_leads_with_the_journey_the_shopper_is_actually_in(
        seeded, chroma, backend, policies, fake_gateway):
    """A shopper who forks and then returns is back on the first journey — the
    workflow says so, because it routes the run there. The page picked the
    newest journey by `created_at` instead, so it kept leading with the subject
    the shopper had left, showing its stale not-ready panel while the journey
    they were actively researching sat under "Also exploring".

    Seen live: a Decision-stage journey with 83 events relegated beneath an
    Awareness stub that had not been touched in three hours.
    """
    from apps.web.pages import _build_feed

    db = seeded
    user = _user(db, "leads-with@example.com")
    s = "lead-s1"

    _insert(db, user.id, s, DAY, _analytics("n"))
    _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=2))
    analytics = _journeys(db, user)[0].journey_id

    _switch_to_devops(db, chroma, backend, policies, user, fake_gateway, s, "o",
                      DAY + timedelta(minutes=5))
    assert len(_journeys(db, user)) == 2, "precondition: the session should have forked"

    # …and later, in a *new* session, back to analytics. A new session is
    # scored against every candidate journey, so this is the path that resumes
    # an older one — and the path the live account took.
    _insert(db, user.id, "lead-s2", DAY + timedelta(hours=2), _analytics("p"))
    resumed = _run(db, chroma, backend, policies, user, fake_gateway,
                   DAY + timedelta(hours=2, minutes=2))
    assert resumed.journey_id == analytics, (
        "precondition: the run should have resumed the analytics journey")

    feed = _build_feed(db, user)
    assert feed is not None
    assert feed["journey_id"] == analytics, (
        f"For-You led with {feed['journey_id']}, not the journey the run just used "
        f"({analytics}). Both journeys label as 'Just started', so the label alone "
        f"cannot tell them apart — the id is what discriminates.")


def test_for_you_reports_the_run_that_produced_what_it_is_showing(
        seeded, chroma, backend, policies, fake_gateway):
    """The panel's "trigger:" line described the user's most recent completed
    run whatever journey it belonged to, so a package from one journey was
    stamped with another journey's trigger — the header disagreed with the
    body it sat above.
    """
    from apps.web.pages import _build_feed, _journey_label

    db = seeded
    user = _user(db, "trigger-line@example.com")
    _insert(db, user.id, "trig-s1", DAY, _analytics("q"))
    run = _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=2))

    feed = _build_feed(db, user)
    assert feed["trigger"] == run.trigger_type
    assert run.journey_id is not None
