"""Acceptance: Stories 2-5 (docs/domains/software-buying/11-user-journey-stories.md).

Story 2 — Collaboration Modernizer (happy path; Scenario 2 derivations,
amended outcome per Decision #037).
Story 3 — Cold-Start Browser (readiness gate; zero Tier 2, one cached clarify).
Story 4 — Time-Waster (noise rejection; discovery maps to no requirement).
Story 5 — Frenzy (burst debounce → 1 run; idempotency; evidence dedup).

Simulated clock throughout; stubbed gateway (FakeGateway)."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from smartreco import models
from smartreco.pipeline import run_workflow
from smartreco.repos import insert_events_idempotent


def _insert(db, user_id, session_id, ts, specs):
    rows = [{"event_id": eid, "user_id": user_id, "session_id": session_id,
             "journey_id": None, "event_type": et, "signal_class": sig,
             "event_metadata": md, "ts": ts, "received_at": ts,
             "processed_at": None} for eid, et, sig, md in specs]
    if db.get(models.Session, session_id) is None:
        db.add(models.Session(session_id=session_id, user_id=user_id,
                              started_at=ts, last_event_at=ts))
    inserted = insert_events_idempotent(db, rows)
    db.commit()
    return inserted


def _user(db, email):
    row = models.User(email=email, password_hash="x")
    db.add(row)
    db.commit()
    return row


def _tier_calls(db, user_id, tier):
    rows = db.execute(select(models.AIUsage).where(
        models.AIUsage.user_id == user_id, models.AIUsage.tier == tier)).scalars().all()
    return sum(r.calls for r in rows)


def test_story2_collaboration_modernizer(seeded, chroma, backend, policies, fake_gateway):
    db = seeded
    user = _user(db, "modernizer@example.com")
    day = datetime(2026, 8, 4)
    sA, sB = "story2-sA", "story2-sB"

    _insert(db, user.id, sA, day.replace(hour=9, minute=0), [
        ("a01", "CATEGORY_VIEWED", "MEDIUM", {"category": "collaboration"}),
        ("a02", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-004", "category": "collaboration"}),
        ("a03", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "ai"}),
        ("a04", "SEARCH", "HIGH", {"query": "ai meeting summaries"}),
        ("a05", "SEARCH", "HIGH", {"query": "google workspace collaboration"}),
    ])
    r1 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                      now=day.replace(hour=9, minute=2), gateway=fake_gateway)
    assert r1.status == "COMPLETED"

    _insert(db, user.id, sA, day.replace(hour=9, minute=15), [
        ("a06", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-005", "category": "collaboration"}),
        ("a07", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-009", "category": "ai"}),
        ("a08", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "ai"}),
        ("a09", "SEARCH", "HIGH", {"query": "notion ai writing"}),
        ("a11", "CATEGORY_VIEWED", "MEDIUM", {"category": "collaboration"}),
    ])
    r2 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                      now=day.replace(hour=9, minute=17), gateway=fake_gateway)
    assert r2.status == "COMPLETED"

    _insert(db, user.id, sB, day.replace(hour=9, minute=30), [
        ("b01", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-005", "category": "collaboration"}),
        ("b02", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-009", "category": "collaboration"}),
        ("b03", "SEARCH", "HIGH", {"query": "google workspace notion collaboration"}),
        ("b04", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-004", "category": "collaboration"}),
    ])
    _insert(db, user.id, sA, day.replace(hour=9, minute=31), [
        ("a13", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "templates"}),
        ("a14", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "tasks"}),
        ("a15", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "productivity"}),
    ])
    r3 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                      now=day.replace(hour=9, minute=33), gateway=fake_gateway)
    assert r3.status == "COMPLETED"

    _insert(db, user.id, sB, day.replace(hour=9, minute=45), [
        ("b05", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "ai"}),
        ("b06", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "ai"}),
        ("b07", "SEARCH", "HIGH", {"query": "ai assistant tools"}),
        ("b08", "SEARCH", "HIGH", {"query": "copilot ai"}),
        ("b09", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "meetings"}),
    ])
    r4 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                      now=day.replace(hour=9, minute=47), gateway=fake_gateway)
    assert r4.status == "COMPLETED"

    _insert(db, user.id, sB, day.replace(hour=10, minute=0), [
        ("b10", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "templates"}),
        ("b11", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "tasks"}),
        ("b12", "SEARCH", "HIGH", {"query": "productivity templates"}),
        ("b13", "CATEGORY_VIEWED", "MEDIUM", {"category": "collaboration"}),
        ("b14", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-004", "category": "collaboration"}),
    ])
    r5 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                      now=day.replace(hour=10, minute=2), gateway=fake_gateway)
    assert r5.status == "COMPLETED"

    journeys = db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)).scalars().all()
    assert len(journeys) == 1
    journey_id = journeys[0].journey_id

    latest: dict[str, models.Hypothesis] = {}
    for h in db.execute(select(models.Hypothesis).where(
            models.Hypothesis.journey_id == journey_id)
            .order_by(models.Hypothesis.version)).scalars().all():
        latest[h.concept_id] = h
    assert latest["BC-005"].confidence == 0.80
    assert latest["BC-006"].confidence == 0.50
    assert latest["BC-003"].confidence == 0.50

    rp = db.execute(select(models.RequirementProfile)
                    .where(models.RequirementProfile.journey_id == journey_id)
                    .order_by(models.RequirementProfile.version.desc())).scalars().first()
    reqs = {e["req_id"]: e for e in rp.requirements}
    assert set(reqs) == {"REQ-001", "REQ-005"}  # REQ-003 (0.41) and REQ-002 held
    assert reqs["REQ-001"]["confidence"] == 0.83
    assert reqs["REQ-001"]["priority"] == "CRITICAL"
    assert reqs["REQ-005"]["confidence"] == 0.75
    assert reqs["REQ-005"]["priority"] == "HIGH"

    pkg = db.execute(select(models.RecommendationPackage)
                     .where(models.RecommendationPackage.journey_id == journey_id)
                     .order_by(models.RecommendationPackage.created_at.desc())
                     ).scalars().first()
    assert pkg.readiness == "READY"
    coverage = {e["product_id"]: e["overall_coverage"] for e in pkg.entries}
    match = {e["product_id"]: e["match_score"] for e in pkg.entries}
    rank = {e["product_id"]: e["rank"] for e in pkg.entries}
    # Scenario 2 exact coverages (Decision #037: exact numbers + relative order;
    # full-coverage products may rank above).
    #
    # Notion covers 49% and is ranked last of the three. Both halves matter and
    # they are now different fields (Decision #078): coverage is what its
    # capabilities earn, and the ranking is on match_score, where Collaboration
    # being a declared subject (Decision #077) puts Notion — catalogued under
    # Knowledge & Docs — at 49 × 0.6 = 29. So it ranks below Zoom, which covers
    # less but is the kind of product being shopped for, while still telling the
    # shopper honestly how much of their requirement it covers.
    assert coverage["PROD-004"] == 97
    assert coverage["PROD-009"] == 49
    assert coverage["PROD-005"] == 33
    assert match["PROD-009"] == 29
    assert match["PROD-005"] == 33
    assert rank["PROD-004"] < rank["PROD-005"] < rank["PROD-009"]
    top3 = [e["product_id"] for e in pkg.entries[:3]]
    assert "PROD-007" not in top3 and "PROD-008" not in top3  # automation absent


def test_story3_cold_start_browser(seeded, chroma, backend, policies, fake_gateway):
    db = seeded
    user = _user(db, "coldstart@example.com")
    ts = datetime(2026, 8, 5, 9, 0)
    _insert(db, user.id, "cold-s1", ts, [
        ("c01", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-002"}),
    ])
    # Accumulation below threshold → SKIP, recorded
    skip = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                        now=ts + timedelta(seconds=90), gateway=fake_gateway)
    assert skip.status == "SKIPPED" and "accumulation" in skip.gates["decision"]

    # Significant event (debounce passed) → fast path only
    run = run_workflow(db, chroma, backend, policies, user.id, "SIGNIFICANT_EVENT",
                       now=ts + timedelta(seconds=120), gateway=fake_gateway)
    assert run.status == "COMPLETED"

    pkg = db.execute(select(models.RecommendationPackage)).scalars().first()
    assert pkg is not None
    assert pkg.readiness == "NOT_READY"
    assert pkg.entries == []  # no ranked list, no popularity fallback

    aar = db.execute(select(models.AdvisoryResponse).where(
        models.AdvisoryResponse.rpkg_id == pkg.rpkg_id)).scalars().first()
    assert aar is not None
    assert aar.sections["clarifying_questions"]  # sourced from constraints
    assert aar.sections["recommended_products"] == []

    assert _tier_calls(db, user.id, "tier2") == 0  # zero Tier-2 calls
    assert _tier_calls(db, user.id, "tier1") == 1  # exactly one clarify call

    # Unchanged state revisited → clarify served from cache, no new call
    _insert(db, user.id, "cold-s1", ts + timedelta(minutes=30), [
        ("c02", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-002"}),
    ])
    again = run_workflow(db, chroma, backend, policies, user.id, "SIGNIFICANT_EVENT",
                         now=ts + timedelta(minutes=32), gateway=fake_gateway)
    assert again.status == "COMPLETED"
    assert _tier_calls(db, user.id, "tier1") == 1  # cached — still one


def test_story4_time_waster_noise_rejection(seeded, chroma, backend, policies, fake_gateway):
    db = seeded
    user = _user(db, "timewaster@example.com")
    start = datetime(2026, 8, 5, 14, 0)
    categories = ["crm", "hr", "devops", "analytics", "support", "marketing"]
    run_times = []
    eid = 0
    # 15 product views across 6 categories in ~12 minutes + category views + short dwells
    for wave in range(3):
        specs = []
        for i in range(5):
            eid += 1
            product = f"PROD-{(eid % 10) + 1:03d}"
            specs.append((f"t{eid:03d}", "PRODUCT_VIEWED", "HIGH",
                          {"product_id": product, "category": categories[(eid) % 6]}))
        eid += 1
        specs.append((f"t{eid:03d}", "CATEGORY_VIEWED", "MEDIUM",
                      {"category": categories[wave]}))
        eid += 1
        specs.append((f"t{eid:03d}", "DWELL", "LOW", {"seconds": 10}))
        ts = start + timedelta(minutes=4 * wave)
        _insert(db, user.id, "waste-s1", ts, specs)
        run_times.append(ts + timedelta(minutes=1))

    runs = [run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                         now=t + timedelta(minutes=11 * i), gateway=fake_gateway)
            for i, t in enumerate(run_times)]
    completed = [r for r in runs if r.status == "COMPLETED"]
    assert completed  # accumulation triggers do fire — fast path only

    journey = db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)).scalars().first()
    hypotheses = db.execute(select(models.Hypothesis).where(
        models.Hypothesis.journey_id == journey.journey_id)).scalars().all()
    concepts = {h.concept_id for h in hypotheses}
    assert concepts <= {"BC-011"}  # only Product Discovery, which maps to no requirement
    for h in hypotheses:
        assert h.confidence <= 0.35  # breadth is not intent; confidence saturates low

    rp = db.execute(select(models.RequirementProfile)
                    .order_by(models.RequirementProfile.version.desc())).scalars().first()
    assert rp.requirements == []

    pkg = db.execute(select(models.RecommendationPackage)
                     .order_by(models.RecommendationPackage.created_at.desc())
                     ).scalars().first()
    assert pkg.readiness == "NOT_READY" and pkg.entries == []

    stage = db.execute(select(models.JourneyStage)
                       .order_by(models.JourneyStage.version.desc())).scalars().first()
    assert stage.stage in ("Awareness", "Discovery")  # never an evaluation stage

    assert _tier_calls(db, user.id, "tier2") == 0
    assert _tier_calls(db, user.id, "tier1") <= 1  # one cached clarify at most
    assert db.execute(select(models.CandidateSet)).scalars().all() == []


def test_story5_frenzy_burst_and_duplicates(seeded, chroma, backend, policies, fake_gateway):
    db = seeded
    user = _user(db, "frenzy@example.com")
    t0 = datetime(2026, 8, 5, 16, 0)

    # 30 near-identical events in 60 seconds; only 10 unique client UUIDs —
    # the rest are client retries replaying the same IDs
    specs = [(f"f{i % 10:02d}", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-003"})
             for i in range(30)]
    inserted = 0
    for wave in range(3):
        inserted += _insert(db, user.id, "frenzy-s1",
                            t0 + timedelta(seconds=20 * wave), specs[wave * 10:(wave + 1) * 10])
    assert inserted == 10  # duplicate UUIDs no-op (server dedupe)

    # Trigger storm during the burst: debounced → SKIP rows. Probe times sit
    # inside the policy's debounce window (duplicate UUIDs no-op, so the newest
    # unprocessed event is from the first wave at t0).
    debounce = policies.param("POL-TRIG-002", "debounce_seconds")
    s1 = run_workflow(db, chroma, backend, policies, user.id, "SIGNIFICANT_EVENT",
                      now=t0 + timedelta(seconds=debounce - 10), gateway=fake_gateway)
    s2 = run_workflow(db, chroma, backend, policies, user.id, "SIGNIFICANT_EVENT",
                      now=t0 + timedelta(seconds=debounce - 2), gateway=fake_gateway)
    assert s1.status == "SKIPPED" and "debounce" in s1.gates["decision"]
    assert s2.status == "SKIPPED" and "debounce" in s2.gates["decision"]

    # Burst over → exactly one run covers it
    run = run_workflow(db, chroma, backend, policies, user.id, "SIGNIFICANT_EVENT",
                       now=t0 + timedelta(seconds=debounce + 80), gateway=fake_gateway)
    assert run.status == "COMPLETED"

    runs = db.execute(select(models.WorkflowRun).where(
        models.WorkflowRun.user_id == user.id)).scalars().all()
    assert sum(1 for r in runs if r.status == "COMPLETED") == 1  # never 30 runs
    assert sum(1 for r in runs if r.status == "SKIPPED") == 2

    # Rage-refreshing one product produces no duplicated evidence and no
    # runaway confidence (BP-012 needs breadth; BP-010 needs multi-session)
    evidence = db.execute(select(models.Evidence)).scalars().all()
    keys = [(e.pattern_id, tuple(sorted(e.supporting_event_ids))) for e in evidence]
    assert len(keys) == len(set(keys))  # no duplicated evidence rows
    for h in db.execute(select(models.Hypothesis)).scalars().all():
        assert h.confidence < 0.95
