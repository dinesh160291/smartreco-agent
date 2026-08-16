"""Signature tests: the guards a public instance needs and a laptop does not.

Four things, none of which change what the platform concludes:

  1. A global ceiling on AI spend. Per-user budgets bound one shopper; nothing
     bounded the bill.
  2. Per-IP rate limiting. Nothing capped how often a caller could arrive.
  3. A scheduled backup of the system of record, which is the only thing here
     that cannot be rebuilt.
  4. Structured logs carrying a request id, because on a deployed host stdout
     is the only observability there is.
"""

import json
import logging
import sqlite3
import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import apps.web.main as web
from smartreco import models
from smartreco.engines.triggers import TriggerContext, evaluate_trigger
from smartreco.seeding import seed_canonical_products, seed_capabilities


@pytest.fixture()
def client(session_factory, chroma, backend, policies, fake_gateway, monkeypatch):
    monkeypatch.setattr(web, "RATE_LIMIT_ENABLED", True)   # the point of this file
    web._state.clear()
    web._state.update({
        "policies": policies, "session_factory": session_factory,
        "chroma": chroma, "backend": backend, "gateway": fake_gateway,
    })
    with session_factory() as db:
        seed_capabilities(db)
        seed_canonical_products(db, chroma, backend)
        db.commit()
    web._rate_buckets.clear()
    with TestClient(web.app) as c:
        yield c
    web._state.clear()
    web._rate_buckets.clear()


def _ctx(**kw):
    base = dict(unprocessed_high_medium_events=99, newest_event_age_seconds=999,
                seconds_since_last_run=None, run_in_flight=False,
                tier1_calls_today=0, tier2_calls_today=0,
                tier1_calls_today_all_users=0, tier2_calls_today_all_users=0)
    base.update(kw)
    return TriggerContext(**base)


# --- 1. A ceiling on the bill ----------------------------------------------

def test_a_global_spend_cap_exists_beside_the_per_user_one(policies):
    """Per-user budgets bound one shopper's cost. With a thousand registered
    users those budgets multiply into a bill nothing caps. The instance needs
    its own ceiling."""
    total1 = policies.param("POL-TRIG-003", "tier1_calls_per_day_total")
    total2 = policies.param("POL-TRIG-003", "tier2_calls_per_day_total")
    per_user1 = policies.param("POL-TRIG-003", "tier1_calls_per_user_per_day")
    assert total1 > per_user1, "a global cap below one user's budget is not a cap"
    assert total2 > 0


def test_reaching_the_global_cap_stops_the_ai_not_the_reasoning(policies):
    """The budget gate degrades the slow path and never blocks the run - the
    deterministic engines need no provider. A spend cap must behave the same
    way, or running out of money would stop recommendations entirely instead
    of stopping the words."""
    total = policies.param("POL-TRIG-003", "tier1_calls_per_day_total")
    decision = evaluate_trigger("EVENT_ACCUMULATION",
                                _ctx(tier1_calls_today_all_users=total), policies)
    assert decision.run is True, "the spend cap blocked deterministic reasoning"
    assert decision.tier1_allowed is False, "the spend cap did not stop Tier 1"


def test_one_users_spending_does_not_exhaust_another_users_budget(policies):
    """The two ceilings are independent: a quiet shopper on a busy instance
    still gets their own allowance until the global cap is actually reached."""
    decision = evaluate_trigger("EVENT_ACCUMULATION",
                                _ctx(tier1_calls_today=0,
                                     tier1_calls_today_all_users=5), policies)
    assert decision.tier1_allowed is True


# --- 2. Rate limiting -------------------------------------------------------

def test_event_ingestion_is_rate_limited_per_caller(client, policies):
    """Nothing capped arrival rate. One script could exhaust the AI budget and
    the thread pool, and the events endpoint is the cheapest one to abuse
    because it is meant to be called constantly."""
    client.post("/auth/register", json={"email": "rl@example.com", "password": "pw123456"})
    client.post("/auth/login", json={"email": "rl@example.com", "password": "pw123456"})
    limit = policies.param("POL-RATE-001", "events_per_minute_per_ip")

    statuses = []
    for _ in range(limit + 15):
        r = client.post("/events/batch", json={"events": []},
                        headers={"x-forwarded-for": "203.0.113.9"})
        statuses.append(r.status_code)
    assert 429 in statuses, "no request was ever refused"
    assert statuses[0] != 429, "the very first request was refused"
    refused = statuses.count(429)
    assert refused >= 5, f"only {refused} refused out of {len(statuses)}"


def test_the_limit_is_per_caller_not_global(client, policies):
    """A shared limit would let one abusive caller lock everyone else out,
    which converts a nuisance into an outage."""
    client.post("/auth/register", json={"email": "rl2@example.com", "password": "pw123456"})
    client.post("/auth/login", json={"email": "rl2@example.com", "password": "pw123456"})
    limit = policies.param("POL-RATE-001", "events_per_minute_per_ip")
    for _ in range(limit + 10):
        client.post("/events/batch", json={"events": []},
                    headers={"x-forwarded-for": "203.0.113.1"})
    fresh = client.post("/events/batch", json={"events": []},
                        headers={"x-forwarded-for": "203.0.113.2"})
    assert fresh.status_code != 429, "a different caller was refused someone else's quota"


def test_a_refusal_says_when_to_come_back(client, policies):
    """429 without Retry-After tells a client to guess, and clients guess by
    retrying immediately."""
    client.post("/auth/register", json={"email": "rl3@example.com", "password": "pw123456"})
    client.post("/auth/login", json={"email": "rl3@example.com", "password": "pw123456"})
    limit = policies.param("POL-RATE-001", "events_per_minute_per_ip")
    last = None
    for _ in range(limit + 15):
        last = client.post("/events/batch", json={"events": []},
                           headers={"x-forwarded-for": "203.0.113.7"})
    assert last.status_code == 429
    assert "retry-after" in {k.lower() for k in last.headers}


def test_the_limiter_cannot_grow_without_bound(client, policies):
    """The limiter is itself a place to store attacker-controlled keys. A map
    that grows per source address is a memory leak wearing a safety hat."""
    cap = policies.param("POL-RATE-001", "max_tracked_callers")
    for i in range(cap + 50):
        client.post("/events/batch", json={"events": []},
                    headers={"x-forwarded-for": f"198.51.100.{i % 256}:{i}"})
    assert len(web._rate_buckets) <= cap, (
        f"limiter tracked {len(web._rate_buckets)} callers against a cap of {cap}")


# --- 3. The system of record has a backup -----------------------------------

def test_the_backup_captures_data_still_in_the_write_ahead_log(tmp_path):
    """The relational store is the only thing here that cannot be rebuilt - the
    vector index is re-derivable, the catalog is seeded from a file.

    A file copy is not a backup of a WAL database: the recent writes live in
    the -wal sidecar and a copy of the main file misses them. This was hit for
    real while taking a backup during this build, and the copy was silently
    short by 22 events."""
    from smartreco.backup import backup_database

    source = tmp_path / "src.db"
    conn = sqlite3.connect(source)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
    conn.executemany("INSERT INTO t (v) VALUES (?)", [(f"row{i}",) for i in range(500)])
    conn.commit()                      # committed, but sitting in the WAL

    destination = backup_database(f"sqlite:///{source}", tmp_path / "backups", keep=3)
    assert destination.exists()
    restored = sqlite3.connect(destination)
    assert restored.execute("SELECT count(*) FROM t").fetchone()[0] == 500, (
        "the backup missed rows still in the write-ahead log")
    conn.close()
    restored.close()


def test_backups_are_rotated_so_the_disk_cannot_fill(tmp_path):
    """An unbounded backup directory eventually fills the volume, which takes
    down the database it was protecting."""
    from smartreco.backup import backup_database

    source = tmp_path / "src.db"
    conn = sqlite3.connect(source)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    for i in range(6):
        backup_database(f"sqlite:///{source}", tmp_path / "backups", keep=3,
                        stamp=f"2026-08-16T{i:02d}0000")
    kept = sorted((tmp_path / "backups").glob("*.db"))
    assert len(kept) == 3, f"kept {len(kept)} backups against a retention of 3"
    # The newest must be the ones kept, not an arbitrary three.
    assert kept[-1].name.endswith("050000.db")


# --- 4. Logs you can actually read ------------------------------------------

def test_every_request_carries_an_id_the_logs_and_the_caller_share(client, caplog):
    """On a deployed host stdout is the whole of observability. A log line that
    cannot be tied to a request is a line you cannot act on, and an error the
    user reports is unfindable unless they can quote an id."""
    with caplog.at_level(logging.INFO, logger="smartreco.access"):
        response = client.get("/product/PROD-003")
    assert response.status_code == 200
    request_id = response.headers.get("x-request-id")
    assert request_id, "no request id was returned to the caller"
    assert any(request_id in record.getMessage() for record in caplog.records), (
        "the request id never reached the logs, so the two cannot be joined")


def test_logs_are_structured_enough_to_query(client, caplog):
    """Free-text logs are greppable only by luck. One JSON object per line
    survives a log shipper and a hurried human equally."""
    with caplog.at_level(logging.INFO, logger="smartreco.access"):
        client.get("/product/PROD-003")
    lines = [r.getMessage() for r in caplog.records if r.name == "smartreco.access"]
    assert lines, "no access log line was emitted"
    payload = json.loads(lines[-1])
    for field in ("request_id", "method", "path", "status", "duration_ms"):
        assert field in payload, f"access log has no {field!r}"
    assert payload["path"] == "/product/PROD-003"
    assert payload["status"] == 200


def test_the_app_does_not_print(client):
    """`print` cannot be levelled, filtered, or given a request id. Two of them
    were the whole of this app's logging before it had somewhere to run."""
    import pathlib

    offenders = []
    for path in pathlib.Path("apps").rglob("*.py"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("print(") or " print(" in stripped:
                offenders.append(f"{path}:{number}")
    assert not offenders, f"print() used instead of a logger: {offenders}"
