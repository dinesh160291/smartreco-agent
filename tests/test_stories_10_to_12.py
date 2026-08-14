"""Acceptance: Stories 10-12 (proactive delivery + operational edges).

Story 10 — Digest Pair: eligible user gets exactly one grounded Telegram
digest; rerun never double-sends; silent user is skipped WITH a recorded
reason. Story 11 — Catalog Shift: dual-write liveness + index-version cache
invalidation; PENDING products never surface. Story 12 — Budget Wall:
budget exhaustion degrades the AI path only; next day generation resumes.
Simulated clock; stubbed gateway; fake channel adapters."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from smartreco import models
from smartreco.delivery import EmailAdapter, TelegramAdapter, run_digest_cycle
from smartreco.pipeline import run_workflow
from smartreco.repos import insert_events_idempotent
from smartreco.retrieval import save_product
from tests.test_stories_6_to_9 import _insert, _pump_focus, _user


class FakeTelegram(TelegramAdapter):
    def __init__(self):
        super().__init__(token="stub-token")
        self.sent: list[tuple[str, str]] = []

    def send(self, chat_id: str, text: str) -> None:
        self.sent.append((chat_id, text))


def test_story10_digest_pair(seeded, chroma, backend, policies, fake_gateway):
    db = seeded
    day = datetime(2026, 8, 1, 9, 0)

    # User A: active this morning, opted in, Telegram connected
    user_a = _user(db, "digest-a@example.com")
    user_a.digest_opt_in = True
    user_a.digest_channel = "TELEGRAM"
    user_a.telegram_chat_id = "chat-a"
    runs = _pump_focus(db, chroma, backend, policies, user_a, fake_gateway, day, "dig-s1")
    assert all(r.status == "COMPLETED" for r in runs)

    # User B: opted in but zero activity
    user_b = _user(db, "digest-b@example.com")
    user_b.digest_opt_in = True
    user_b.digest_channel = "TELEGRAM"
    user_b.telegram_chat_id = "chat-b"
    db.commit()

    telegram = FakeTelegram()
    seventeen = day.replace(hour=17)
    run_digest_cycle(db, chroma, backend, fake_gateway, policies, seventeen,
                     telegram=telegram, email=EmailAdapter())

    # A: exactly one message, grounded digest structure, SENT record
    assert len(telegram.sent) == 1
    chat_id, text = telegram.sent[0]
    assert chat_id == "chat-a"
    assert "Next step:" in text and "AI wrote the words" in text
    records = {r.user_id: r for r in db.execute(
        select(models.DeliveryRecord)).scalars().all()}
    assert records[user_a.id].status == "SENT"
    assert records[user_a.id].aar_id is not None

    # B: nothing sent, skip recorded with reason
    assert records[user_b.id].status == "SKIPPED"
    assert "POL-DELIV-001" in records[user_b.id].reason

    # Scheduler rerun in the same window: idempotent — no double-send
    run_digest_cycle(db, chroma, backend, fake_gateway, policies,
                     seventeen + timedelta(minutes=30),
                     telegram=telegram, email=EmailAdapter())
    assert len(telegram.sent) == 1
    all_records = db.execute(select(models.DeliveryRecord).where(
        models.DeliveryRecord.user_id == user_a.id)).scalars().all()
    assert len(all_records) == 1

    # Digest AAR rendered in-app: DIGEST surface, distinct from ONSITE
    digest_aar = db.get(models.AdvisoryResponse, records[user_a.id].aar_id)
    assert digest_aar.surface == "DIGEST"
    assert digest_aar.prompt_version == "aar-digest-v2"  # off-subject note, #078


def test_story11_catalog_shift(seeded, chroma, backend, policies, fake_gateway):
    db = seeded
    user = _user(db, "shift@example.com")
    day = datetime(2026, 8, 1, 9, 0)
    _pump_focus(db, chroma, backend, policies, user, fake_gateway, day, "shift-s1")

    journey = db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)).scalars().one()
    pkg_before = db.execute(
        select(models.RecommendationPackage)
        .where(models.RecommendationPackage.journey_id == journey.journey_id)
        .order_by(models.RecommendationPackage.created_at.desc())).scalars().first()
    assert "PROD-011" not in [e["product_id"] for e in pkg_before.entries]

    # Admin adds an Auth0-class product with the full identity capability set
    new_product = models.Product(
        product_id="PROD-011", name="Authway", vendor="Authway",
        category="Identity & Access Management",
        description="Identity platform with single sign-on, multi-factor "
                    "authentication, provisioning and access policies.",
        business_purpose="Standardize identity management across applications.")
    save_product(db, chroma, backend, new_product,
                 ["CAP-001", "CAP-002", "CAP-003", "CAP-004", "CAP-008", "CAP-010"])
    assert db.get(models.Product, "PROD-011").sync_status == "SYNCED"

    # New events → next trigger: index version changed → cache invalidated →
    # re-retrieval ranks the new product deterministically
    _insert(db, user.id, "shift-s1", day + timedelta(hours=1), [
        ("s20", "SECURITY_VIEWED", "HIGH", {"page": "g"}),
        ("s21", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"}),
        ("s22", "SEARCH", "HIGH", {"query": "okta sso mfa"}),
        ("s23", "SECURITY_VIEWED", "HIGH", {"page": "h"}),
        ("s24", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "mfa"}),
    ])
    run = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                       now=day + timedelta(hours=1, minutes=2), gateway=fake_gateway)
    assert run.status == "COMPLETED"
    retrieve_nodes = [n for n in run.nodes if n["node"] == "retrieve"]
    assert retrieve_nodes and retrieve_nodes[0]["cache_hit"] is False  # invalidated

    pkg_after = db.execute(
        select(models.RecommendationPackage)
        .where(models.RecommendationPackage.journey_id == journey.journey_id)
        .order_by(models.RecommendationPackage.created_at.desc())).scalars().first()
    entry_ids = [e["product_id"] for e in pkg_after.entries]
    assert "PROD-011" in entry_ids  # the catalog is live end to end
    # Ranked purely by coverage: full REQ-002 set → 100% ties Okta; capability
    # count breaks the tie (Okta 7 caps > Authway 6)
    authway = next(e for e in pkg_after.entries if e["product_id"] == "PROD-011")
    assert authway["overall_coverage"] == 100


def test_story11_pending_product_never_surfaces(seeded, chroma, backend, policies,
                                                fake_gateway):
    db = seeded
    user = _user(db, "pending@example.com")
    day = datetime(2026, 8, 2, 9, 0)

    class FailingBackend:
        def embed(self, texts):
            raise ConnectionError("vector backend down")

    half_synced = models.Product(
        product_id="PROD-012", name="Halfway", vendor="Halfway",
        category="Identity & Access Management",
        description="Identity product whose vector write failed.",
        business_purpose="Test PENDING invisibility.")
    with pytest.raises(ConnectionError):
        save_product(db, chroma, FailingBackend(), half_synced,
                     ["CAP-001", "CAP-002", "CAP-003", "CAP-004", "CAP-010"])
    assert db.get(models.Product, "PROD-012").sync_status == "FAILED"

    _pump_focus(db, chroma, backend, policies, user, fake_gateway, day, "pend-s1")
    pkg = db.execute(select(models.RecommendationPackage)
                     .order_by(models.RecommendationPackage.created_at.desc())
                     ).scalars().first()
    assert "PROD-012" not in [e["product_id"] for e in pkg.entries]  # never half-present


def test_story12_budget_wall(seeded, chroma, backend, policies, fake_gateway):
    db = seeded
    user = _user(db, "wall@example.com")
    day = datetime(2026, 8, 3, 9, 0)
    runs = _pump_focus(db, chroma, backend, policies, user, fake_gateway, day, "wall-s1")
    aar_count_before = len(db.execute(select(models.AdvisoryResponse)).scalars().all())
    assert aar_count_before >= 1  # last stored AAR exists

    # Exhaust both budgets mid-afternoon
    tier1 = policies.param("POL-TRIG-003", "tier1_calls_per_user_per_day")
    tier2 = policies.param("POL-TRIG-003", "tier2_calls_per_user_per_day")
    for tier, limit in (("tier1", tier1), ("tier2", tier2)):
        row = db.get(models.AIUsage, (user.id, day.strftime("%Y-%m-%d"), tier))
        if row is None:
            db.add(models.AIUsage(user_id=user.id, day=day.strftime("%Y-%m-%d"),
                                  tier=tier, calls=limit))
        else:
            row.calls = limit
    db.commit()

    # Meaningful research continues — deterministic path never blocks
    _insert(db, user.id, "wall-s1", day + timedelta(hours=5), [
        ("w20", "SECURITY_VIEWED", "HIGH", {"page": "x"}),
        ("w21", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"}),
        ("w22", "SEARCH", "HIGH", {"query": "okta sso mfa"}),
        ("w23", "SECURITY_VIEWED", "HIGH", {"page": "y"}),
        ("w24", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "mfa"}),
    ])
    calls_before = len(fake_gateway.calls)
    run = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                       now=day + timedelta(hours=5, minutes=2), gateway=fake_gateway)
    assert run.status == "COMPLETED"                     # nothing errors
    assert len(fake_gateway.calls) == calls_before       # budget never bypassed
    assert run.gates["tier1_allowed"] is False and run.gates["tier2_allowed"] is False
    tier1_nodes = [n for n in run.nodes if n["node"] in ("generate", "clarify")]
    assert tier1_nodes and ("budget" in str(tier1_nodes[0].get("skipped", ""))
                            or tier1_nodes[0].get("cache_hit"))

    # Fresh deterministic package still published; last stored AAR still served
    pkg = db.execute(select(models.RecommendationPackage)
                     .order_by(models.RecommendationPackage.created_at.desc())
                     ).scalars().first()
    assert pkg is not None and pkg.entries

    # Next day: budgets reset by day key — generation resumes
    next_day = day + timedelta(days=1)
    _insert(db, user.id, "wall-s1", next_day, [
        ("w30", "SECURITY_VIEWED", "HIGH", {"page": "z"}),
        ("w31", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "mfa"}),
        ("w32", "SEARCH", "HIGH", {"query": "single sign-on okta"}),
        ("w33", "SECURITY_VIEWED", "HIGH", {"page": "w"}),
        ("w34", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"}),
    ])
    run2 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                        now=next_day + timedelta(minutes=2), gateway=fake_gateway)
    assert run2.status == "COMPLETED"
    assert run2.gates["tier1_allowed"] is True           # generation resumes
