"""Signature tests: POST /events/batch + minimal auth (docs/core/22; POL-TRACK-001).

202 accept-fast; idempotent by client event UUID; per-event rejection for
unknown event types (closed registry); wholesale rejection above the policy
batch maximum; endpoints require authentication."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import apps.web.main as web
from smartreco import models
from smartreco.seeding import seed_canonical_products, seed_capabilities


@pytest.fixture()
def client(session_factory, chroma, backend, policies):
    web._state.clear()
    web._state.update({
        "policies": policies,
        "session_factory": session_factory,
        "chroma": chroma,
        "backend": backend,
    })
    with session_factory() as db:
        seed_capabilities(db)
        seed_canonical_products(db, chroma, backend)
    with TestClient(web.app) as test_client:
        yield test_client
    web._state.clear()


def _register(client):
    response = client.post("/auth/register",
                           json={"email": "shopper@example.com", "password": "pw123456"})
    assert response.status_code == 201
    return response.json()


def ev(i, etype="PRODUCT_VIEWED", **metadata):
    return {"event_id": f"evt-{i}", "session_id": "s1", "event_type": etype,
            "ts": "2026-08-01T09:00:00Z", "metadata": metadata}


def test_batch_requires_auth(client):
    response = client.post("/events/batch", json={"events": [ev(1)]})
    assert response.status_code == 401


def test_batch_accepts_202_and_is_idempotent(client, session_factory):
    _register(client)
    batch = {"events": [ev(1, product_id="PROD-003"), ev(2, "SEARCH", query="sso")]}
    first = client.post("/events/batch", json=batch)
    assert first.status_code == 202
    assert first.json()["inserted"] == 2

    replay = client.post("/events/batch", json=batch)
    assert replay.status_code == 202
    assert replay.json()["inserted"] == 0  # duplicate client event IDs no-op

    with session_factory() as db:
        assert len(db.execute(select(models.Event)).scalars().all()) == 2


def test_unknown_event_type_rejected_per_event_not_batch(client, session_factory):
    _register(client)
    batch = {"events": [ev(10), {"event_id": "evt-bad", "session_id": "s1",
                                 "event_type": "NOT_A_TYPE",
                                 "ts": "2026-08-01T09:00:00Z", "metadata": {}}]}
    response = client.post("/events/batch", json=batch)
    assert response.status_code == 202
    body = response.json()
    assert body["accepted"] == 1
    assert body["rejected"][0]["event_id"] == "evt-bad"


def test_oversize_batch_rejected_wholesale(client, policies):
    _register(client)
    limit = policies.param("POL-TRACK-001", "server_max_batch")
    batch = {"events": [ev(i) for i in range(limit + 1)]}
    response = client.post("/events/batch", json=batch)
    assert response.status_code == 422


def test_login_roles(client):
    _register(client)
    ok = client.post("/auth/login", json={"email": "shopper@example.com",
                                          "password": "pw123456"})
    assert ok.status_code == 200 and ok.json()["role"] == "user"
    bad = client.post("/auth/login", json={"email": "shopper@example.com",
                                           "password": "wrong"})
    assert bad.status_code == 401
