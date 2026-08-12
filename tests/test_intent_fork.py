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

from smartreco.engines.journey_resolution import intent_diverged


def test_a_different_subject_diverges():
    # Data & Insight giving way to Engineering Delivery.
    assert intent_diverged({"BC-023"}, {"BC-024"}) is True


def test_the_same_subject_does_not_diverge():
    assert intent_diverged({"BC-024"}, {"BC-024"}) is False


def test_widening_within_a_subject_does_not_diverge():
    """Still shopping for analytics, now also touching engineering delivery.
    An overlap of one is continuity — the shopper has widened, not moved."""
    assert intent_diverged({"BC-024", "BC-023"}, {"BC-024"}) is False


def test_evidence_carrying_no_subject_never_forks():
    """Pricing, comparisons and security research say how far along a shopper
    is, not what they are shopping for. A block of them must not fork a
    journey, and must not fork it merely because the journey has a subject."""
    assert intent_diverged(set(), {"BC-024"}) is False
    assert intent_diverged({"BC-024"}, set()) is False
    assert intent_diverged(set(), set()) is False


def test_divergence_is_symmetric():
    assert intent_diverged({"BC-019"}, {"BC-021"}) == intent_diverged({"BC-021"}, {"BC-019"})


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
    ][:n]


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

    _insert(db, user.id, s, DAY + timedelta(minutes=5), _devops("b"))
    _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=7))

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

    # ...and the abandoned journey keeps its own, at the confidence it reached.
    first = {h.concept_id for h in db.execute(select(models.Hypothesis).where(
        models.Hypothesis.journey_id == journeys[0].journey_id)).scalars().all()}
    assert "BC-024" in first and "BC-023" not in first


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

    _insert(db, user.id, s, DAY + timedelta(minutes=5), _devops("f"))
    _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=7))
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

            _insert(db, user.id, s, DAY + timedelta(minutes=20), _devops("i"))
            _run(db, chroma, backend, policies, user, fake_gateway, DAY + timedelta(minutes=22))
            assert len(_journeys(db, user)) == 2, "precondition: the session should have forked"

        with TestClient(web.app) as c:
            c.post("/auth/login", json={"email": "split@example.com", "password": "pw123456"})
            html = c.get("/for-you").text

        assert "Also exploring" in html, "the abandoned journey is invisible on For-You"
        for banned in ("REQ-", "BC-", "BP-", "CAP-"):
            assert banned not in html, f"{banned} code leaked onto a shopper surface"
    finally:
        web._state.clear()
