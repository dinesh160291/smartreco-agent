"""Acceptance: Story 1 — The Security Evaluator (Gate G1).

docs/domains/software-buying/11-user-journey-stories.md Story 1 + Domain 09 Scenario 1:
replay a two-session clickstream → BP-001/BP-002 evidence → BC-001 0.80,
BC-002 0.70 → REQ-002 0.94 CRITICAL, REQ-004 0.56 MEDIUM, REQ-001 held at
0.48 → stage Technical Validation → Okta 81 / Microsoft 365 70 / Google
Workspace 58 → READY.

The clickstream extends the story's skeleton with additional same-character
events (more security/enterprise research across the two sessions) so the
published POL-CONF-001/002 arithmetic honestly produces the scenario's stated
hypothesis confidences — the derivation constraint the handoff records and
Decision #036 formalizes. Simulated clock throughout; no real waits; stubbed
embedding backend (no gateway calls).
"""

from datetime import datetime

import pytest
from sqlalchemy import select

from smartreco import models
from smartreco.pipeline import run_workflow
from smartreco.repos import insert_events_idempotent


def _batch(db, user_id, session_id, ts, specs):
    rows = []
    for i, (event_id, event_type, signal, metadata) in enumerate(specs):
        rows.append({
            "event_id": event_id, "user_id": user_id, "session_id": session_id,
            "journey_id": None, "event_type": event_type, "signal_class": signal,
            "event_metadata": metadata, "ts": ts, "received_at": ts,
            "processed_at": None,
        })
    session_row = db.get(models.Session, session_id)
    if session_row is None:
        db.add(models.Session(session_id=session_id, user_id=user_id,
                              started_at=ts, last_event_at=ts))
    else:
        session_row.last_event_at = ts
    insert_events_idempotent(db, rows)
    db.commit()


@pytest.fixture()
def user(seeded):
    row = models.User(email="evaluator@example.com", password_hash="x", role="user")
    seeded.add(row)
    seeded.commit()
    return row


def replay_story1(db, chroma, backend, policies, user, gw):
    """Replays the Story 1 clickstream (5 batches, 2 sessions, 5 runs).
    Returns the list of completed runs. Reused by Story 9 (the Buyer)."""
    s1, s2 = "story1-s1", "story1-s2"
    day1 = datetime(2026, 8, 1)
    day2 = datetime(2026, 8, 2)

    # --- Session 1: search → Okta → security & compliance tab → SSO/SCIM docs → compare
    _batch(db, user.id, s1, day1.replace(hour=9, minute=0), [
        ("e01", "SEARCH", "HIGH", {"query": "single sign-on okta"}),
        ("e02", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-003"}),
        ("e03", "SECURITY_VIEWED", "HIGH", {"page": "security-overview", "topic": "compliance"}),
        ("e04", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"}),
        ("e05", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "provisioning"}),
    ])
    r1 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION", gateway=gw,
                      now=day1.replace(hour=9, minute=2))
    assert r1.status == "COMPLETED"

    dwell = [(f"e{n:02d}", "DWELL", "LOW", {"topic": "security", "seconds": 10})
             for n in range(6, 12)]
    _batch(db, user.id, s1, day1.replace(hour=9, minute=15), dwell + [
        ("e12", "SECURITY_VIEWED", "HIGH", {"page": "security-certifications", "topic": "audit"}),
        ("e13", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "mfa"}),
        ("e14", "COMPARISON_STARTED", "HIGH", {"product_a": "PROD-003", "product_b": "PROD-001"}),
        ("e15", "SEARCH", "HIGH", {"query": "okta scim provisioning"}),
        ("e16", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "admin"}),
    ])
    r2 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION", gateway=gw,
                      now=day1.replace(hour=9, minute=17))
    assert r2.status == "COMPLETED"

    _batch(db, user.id, s1, day1.replace(hour=9, minute=30), [
        ("e17", "DWELL", "LOW", {"topic": "security", "seconds": 10}),
        ("e18", "DWELL", "LOW", {"topic": "security", "seconds": 10}),
        ("e19", "DWELL", "LOW", {"topic": "security", "seconds": 10}),
        ("e20", "SECURITY_VIEWED", "HIGH", {"page": "security-encryption"}),
        ("e21", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "federation"}),
        ("e22", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-003"}),
        ("e23", "SEARCH", "HIGH", {"query": "single sign on audit logging"}),
        ("e24", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"}),
    ])
    r3 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION", gateway=gw,
                      now=day1.replace(hour=9, minute=32))
    assert r3.status == "COMPLETED"

    # --- Session 2 (next day): enterprise pricing, admin docs, more security research
    _batch(db, user.id, s2, day2.replace(hour=10, minute=0), [
        ("e30", "PRICING_VIEWED", "HIGH", {"product_id": "PROD-003", "tier": "enterprise"}),
        ("e31", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "admin"}),
        ("e32", "SECURITY_VIEWED", "HIGH", {"page": "deployment-security"}),
        ("e33", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "mfa"}),
        ("e34", "SEARCH", "HIGH", {"query": "single sign-on scim provisioning okta"}),
        ("e35", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"}),
    ])
    r4 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION", gateway=gw,
                      now=day2.replace(hour=10, minute=2))
    assert r4.status == "COMPLETED"

    _batch(db, user.id, s2, day2.replace(hour=10, minute=15), [
        ("e40", "SECURITY_VIEWED", "HIGH", {"page": "security-overview-v2"}),
        ("e41", "PRICING_VIEWED", "HIGH", {"product_id": "PROD-003", "tier": "enterprise"}),
        ("e42", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "provisioning"}),
        ("e43", "SEARCH", "HIGH", {"query": "okta sso audit logging"}),
        ("e44", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "admin"}),
    ])
    r5 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION", gateway=gw,
                      now=day2.replace(hour=10, minute=17))
    return [r1, r2, r3, r4, r5]


def test_story1_security_evaluator(seeded, chroma, backend, policies, user, fake_gateway):
    db = seeded
    runs = replay_story1(db, chroma, backend, policies, user, fake_gateway)
    assert all(r.status == "COMPLETED" for r in runs)

    # --- Both sessions resolved into ONE journey ---
    journeys = db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)).scalars().all()
    assert len(journeys) == 1
    journey_id = journeys[0].journey_id

    # --- Hypotheses: BC-001 0.80, BC-002 0.70 (Scenario 1 stated confidences) ---
    latest: dict[str, models.Hypothesis] = {}
    for h in db.execute(select(models.Hypothesis).where(
            models.Hypothesis.journey_id == journey_id)
            .order_by(models.Hypothesis.version)).scalars().all():
        latest[h.concept_id] = h
    assert latest["BC-001"].confidence == 0.80
    assert latest["BC-002"].confidence == 0.70

    # --- Requirement Profile: REQ-002 0.94 Critical / REQ-004 0.56 Medium / REQ-001 held ---
    rp = db.execute(select(models.RequirementProfile)
                    .where(models.RequirementProfile.journey_id == journey_id)
                    .order_by(models.RequirementProfile.version.desc())).scalars().first()
    reqs = {entry["req_id"]: entry for entry in rp.requirements}
    assert set(reqs) == {"REQ-002", "REQ-004"}          # REQ-001 held below 0.5
    # 0.80, not 0.94: Enterprise Evaluation no longer contributes to Identity
    # Management (Decision #050) — this shopper's identity need rests on their
    # security research alone. Everything downstream is unchanged, which is the
    # evidence the demotion was surgical: same requirement set, same priority
    # bands, same coverage percentages asserted below.
    assert reqs["REQ-002"]["confidence"] == 0.80
    assert reqs["REQ-002"]["priority"] == "CRITICAL"
    assert reqs["REQ-004"]["confidence"] == 0.56
    assert reqs["REQ-004"]["priority"] == "MEDIUM"

    # --- Stage: Technical Validation ---
    stage = db.execute(select(models.JourneyStage)
                       .where(models.JourneyStage.journey_id == journey_id)
                       .order_by(models.JourneyStage.version.desc())).scalars().first()
    assert stage.stage == "Technical Validation"

    # --- Recommendation Package: Okta 81 / M365 70 / Google 58, READY ---
    pkg = db.execute(select(models.RecommendationPackage)
                     .where(models.RecommendationPackage.journey_id == journey_id)
                     .order_by(models.RecommendationPackage.created_at.desc())
                     ).scalars().first()
    assert pkg.readiness == "READY"
    top3 = [(e["product_id"], e["overall_coverage"]) for e in pkg.entries[:3]]
    assert top3 == [("PROD-003", 81), ("PROD-001", 70), ("PROD-004", 58)]

    # --- Stubbed AAR persisted for the package (unique per surface/prompt) ---
    aar = db.execute(select(models.AdvisoryResponse).where(
        models.AdvisoryResponse.rpkg_id == pkg.rpkg_id)).scalars().first()
    assert aar is not None and aar.surface == "ONSITE"

    # --- Observability: every run recorded with its trigger and policy version ---
    runs = db.execute(select(models.WorkflowRun).where(
        models.WorkflowRun.user_id == user.id,
        models.WorkflowRun.status == "COMPLETED")).scalars().all()
    assert len(runs) == 5
    assert all(r.policy_version == policies.version for r in runs)
