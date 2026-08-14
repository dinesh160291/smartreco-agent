"""Signature tests: the Decision #078 entry shape as it reaches the page — both
the new one, served over the real route, and the one already on disk.

Recommendation Packages are insert-only Runtime Objects (Law 6), so every row a
running deployment has already written stays on disk with the entry shape it had
when it was written — `overall_coverage` and no `match_score`/`on_subject`. The
code that reads them changed; the rows did not. A missing key resolves to
Undefined in Jinja, which is falsy, so the failure mode is not a crash but the
"ranked lower" caveat printed against *every* product in the list.
"""

from datetime import datetime

import pytest

from smartreco import models
from smartreco.seeding import seed_canonical_products, seed_capabilities

PRE_078_ENTRIES = [
    {"product_id": "PROD-003", "rank": 1, "overall_coverage": 82,
     "per_requirement": {"REQ-002": {"coverage": 100, "supported_capability_ids": ["CAP-001"],
                                     "missing_capability_ids": []}},
     "satisfied_requirements": ["REQ-002"], "partially_satisfied_requirements": [],
     "unsupported_requirements": [], "missing_capability_ids": []},
    {"product_id": "PROD-001", "rank": 2, "overall_coverage": 78,
     "per_requirement": {"REQ-002": {"coverage": 78, "supported_capability_ids": ["CAP-001"],
                                     "missing_capability_ids": ["CAP-003"]}},
     "satisfied_requirements": [], "partially_satisfied_requirements": ["REQ-002"],
     "unsupported_requirements": [], "missing_capability_ids": ["CAP-003"]},
]


@pytest.fixture
def legacy_package(seeded, chroma, backend):
    db = seeded
    seed_capabilities(db)
    seed_canonical_products(db, chroma, backend)
    user = models.User(email="legacy@example.com", password_hash="x")
    db.add(user)
    db.commit()
    now = datetime(2026, 8, 1, 9, 0)
    db.add(models.Journey(journey_id="J-legacy", user_id=user.id,
                          lifecycle="ACTIVE", created_at=now))
    db.add(models.Session(session_id="lg-s1", user_id=user.id,
                          started_at=now, last_event_at=now))
    db.flush()
    db.add(models.Event(event_id="lg1", user_id=user.id, session_id="lg-s1",
                        journey_id="J-legacy", event_type="PRODUCT_VIEWED",
                        signal_class="HIGH", event_metadata={}, ts=now,
                        received_at=now, processed_at=now))
    db.add(models.RequirementProfile(
        rp_id="RP-legacy", journey_id="J-legacy", version=1,
        requirements=[{"req_id": "REQ-002", "confidence": 0.8,
                       "priority": "CRITICAL", "explanation": ""}],
        created_at=now))
    db.flush()   # the package references the profile
    db.add(models.RecommendationPackage(
        rpkg_id="RPKG-legacy", journey_id="J-legacy", rp_id="RP-legacy", cs_id=None,
        entries=PRE_078_ENTRIES, readiness="READY", constraints={},
        policy_version="1.9", created_at=now))
    db.commit()
    return db, user


def test_a_pre_078_package_renders_without_caveating_every_product(legacy_package):
    """The failure this forecloses is silent: no exception, just every entry
    labelled as the wrong kind of product because the key is absent."""
    from apps.web.pages import _build_feed, templates

    db, user = legacy_package
    feed = _build_feed(db, user)
    assert feed is not None and feed["entries"], "a stored package stopped rendering"
    assert all(e["on_subject"] is True for e in feed["entries"]), (
        "entries written before the field defaulted to off-subject")

    html = templates.get_template("_feed.html").render(feed=feed)
    assert "Ranked lower" not in html
    assert "82%" in html and "78%" in html      # the stored figures, unchanged


# ---- the new shape, over the real HTTP route ----

POST_078_ENTRIES = [
    {"product_id": "PROD-005", "rank": 1, "overall_coverage": 33, "match_score": 33,
     "on_subject": True,
     "per_requirement": {"REQ-001": {"coverage": 33, "supported_capability_ids": ["CAP-005"],
                                     "missing_capability_ids": ["CAP-001"]}},
     "satisfied_requirements": [], "partially_satisfied_requirements": ["REQ-001"],
     "unsupported_requirements": [], "missing_capability_ids": ["CAP-001"]},
    {"product_id": "PROD-009", "rank": 2, "overall_coverage": 49, "match_score": 29,
     "on_subject": False,
     "per_requirement": {"REQ-001": {"coverage": 49, "supported_capability_ids": ["CAP-007"],
                                     "missing_capability_ids": ["CAP-001"]}},
     "satisfied_requirements": [], "partially_satisfied_requirements": ["REQ-001"],
     "unsupported_requirements": [], "missing_capability_ids": ["CAP-001"]},
]


def test_for_you_serves_the_off_subject_reason_over_the_real_route(
        session_factory, chroma, backend, policies, fake_gateway):
    """The whole chain on one request: stored package -> _build_feed -> template
    -> HTTP response. The unit tests either build the view dict themselves or
    render the partial directly, so neither of them would notice the route
    wiring dropping the field on the way past.
    """
    import apps.web.main as web
    from fastapi.testclient import TestClient

    web._state.clear()
    web._state.update({"policies": policies, "session_factory": session_factory,
                       "chroma": chroma, "backend": backend, "gateway": fake_gateway})
    try:
        now = datetime(2026, 8, 4, 9, 0)
        with session_factory() as db:
            seed_capabilities(db)
            seed_canonical_products(db, chroma, backend)
            db.add(models.User(email="offsubject@example.com",
                               password_hash=web._hash_password("pw123456"), role="user"))
            db.commit()
            user = db.query(models.User).filter(
                models.User.email == "offsubject@example.com").one()
            db.add(models.Journey(journey_id="J-off", user_id=user.id,
                                  lifecycle="ACTIVE", created_at=now))
            db.add(models.Session(session_id="off-s1", user_id=user.id,
                                  started_at=now, last_event_at=now))
            db.flush()
            db.add(models.Event(event_id="off1", user_id=user.id, session_id="off-s1",
                                journey_id="J-off", event_type="PRODUCT_VIEWED",
                                signal_class="HIGH", event_metadata={}, ts=now,
                                received_at=now, processed_at=now))
            db.add(models.RequirementProfile(
                rp_id="RP-off", journey_id="J-off", version=1,
                requirements=[{"req_id": "REQ-001", "confidence": 0.83,
                               "priority": "CRITICAL", "explanation": ""}],
                created_at=now))
            db.flush()
            db.add(models.RecommendationPackage(
                rpkg_id="RPKG-off", journey_id="J-off", rp_id="RP-off", cs_id=None,
                entries=POST_078_ENTRIES, readiness="READY", constraints={},
                policy_version="1.10", created_at=now))
            db.commit()

        with TestClient(web.app) as client:
            client.post("/auth/login", json={"email": "offsubject@example.com",
                                             "password": "pw123456"})
            html = client.get("/for-you").text

        assert "49%" in html, "the off-subject product's true coverage never reached the page"
        assert "33%" in html
        assert html.count("Ranked lower") == 1, (
            "exactly the off-subject entry should carry the reason")
        # Law 10: canonical IDs never reach a shopper surface.
        for banned in ("CAP-", "REQ-", "BC-", "BP-"):
            assert banned not in html
    finally:
        web._state.clear()
