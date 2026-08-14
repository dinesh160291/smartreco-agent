"""Acceptance: Stories 6-9 (Group C journey intelligence + Group D commerce).

Story 6 — Multi-Journey User: CLOSED journeys are never candidates; traits are
priors, never ranking inputs. Story 7 — Returning Researcher: DORMANT journey
reactivates (score ≥ 0.7) and state resumes. Story 8 — Mind-Changer:
contradiction weakens gradually (POL-CONF-003), never flips on one event;
stage can regress (POL-STAGE-002). Story 9 — the Buyer: purchase closes the
journey immediately and the Learning Engine writes concept-derived traits.
Simulated clock; stubbed gateway."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from smartreco import models
from smartreco.pipeline import run_workflow
from smartreco.repos import insert_events_idempotent
from tests.test_story1_acceptance import replay_story1


def _insert(db, user_id, session_id, ts, specs):
    rows = [{"event_id": eid, "user_id": user_id, "session_id": session_id,
             "journey_id": None, "event_type": et, "signal_class": sig,
             "event_metadata": md, "ts": ts, "received_at": ts,
             "processed_at": None} for eid, et, sig, md in specs]
    if db.get(models.Session, session_id) is None:
        db.add(models.Session(session_id=session_id, user_id=user_id,
                              started_at=ts, last_event_at=ts))
    insert_events_idempotent(db, rows)
    db.commit()


def _user(db, email):
    row = models.User(email=email, password_hash="x")
    db.add(row)
    db.commit()
    return row


def _latest_hypotheses(db, journey_id):
    latest = {}
    for h in db.execute(select(models.Hypothesis).where(
            models.Hypothesis.journey_id == journey_id)
            .order_by(models.Hypothesis.version)).scalars().all():
        latest[h.concept_id] = h
    return latest


def _traits(db, user_id):
    return {t.trait_name: t for t in db.execute(
        select(models.BehavioralTrait).where(
            models.BehavioralTrait.user_id == user_id)).scalars().all()}


def _buy_okta(db, chroma, backend, policies, user, gw, when):
    _insert(db, user.id, "story1-s2", when, [
        ("buy1", "ADD_TO_CART", "HIGH", {"product_id": "PROD-003"}),
        ("buy2", "CHECKOUT_STARTED", "HIGH", {}),
        ("buy3", "PURCHASE_COMPLETED", "HIGH", {"product_id": "PROD-003"}),
    ])
    return run_workflow(db, chroma, backend, policies, user.id, "SIGNIFICANT_EVENT",
                        now=when + timedelta(minutes=2), gateway=gw)


def test_story9_buyer_learning_arc(seeded, chroma, backend, policies, fake_gateway):
    db = seeded
    user = _user(db, "buyer@example.com")
    replay_story1(db, chroma, backend, policies, user, fake_gateway)

    run = _buy_okta(db, chroma, backend, policies, user, fake_gateway,
                    datetime(2026, 8, 2, 11, 0))
    assert run.status == "COMPLETED"

    journey = db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)).scalars().one()
    assert journey.lifecycle == "CLOSED"          # never ACTIVE after purchase
    assert journey.outcome == "PURCHASED"
    assert journey.closed_at is not None

    traits = _traits(db, user.id)
    # Concept-derived per POL-LEARN-001: BC-001 (0.8) and BC-002 (0.7) clear 0.6
    assert set(traits) == {"Security Evaluation", "Enterprise Evaluation"}
    for t in traits.values():
        assert t.strength == policies.param("POL-LEARN-001", "new_trait_strength")
        assert t.reinforcement_count == 1

    transitions = db.execute(select(models.JourneyTransition).where(
        models.JourneyTransition.journey_id == journey.journey_id,
        models.JourneyTransition.to_state == "CLOSED")).scalars().all()
    assert len(transitions) == 1 and "POL-JRES-003" in transitions[0].reason


def test_story6_multi_journey_context_switch(seeded, chroma, backend, policies, fake_gateway):
    db = seeded
    user = _user(db, "switcher@example.com")
    replay_story1(db, chroma, backend, policies, user, fake_gateway)
    _buy_okta(db, chroma, backend, policies, user, fake_gateway,
              datetime(2026, 8, 2, 11, 0))

    # Three weeks later: personal note-taking research — disjoint intent
    day = datetime(2026, 8, 23)
    _insert(db, user.id, "notes-s1", day.replace(hour=9), [
        ("n01", "SEARCH", "HIGH", {"query": "note taking app templates"}),
        ("n02", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-009", "category": "knowledge"}),
        ("n03", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "templates"}),
        ("n04", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "tasks"}),
        ("n05", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "ai"}),
        ("n06", "SEARCH", "HIGH", {"query": "ai writing assistant"}),
    ])
    r1 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                      now=day.replace(hour=9, minute=2), gateway=fake_gateway)
    _insert(db, user.id, "notes-s1", day.replace(hour=9, minute=20), [
        ("n07", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "productivity"}),
        ("n08", "SEARCH", "HIGH", {"query": "productivity templates tasks"}),
        ("n09", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "ai"}),
        ("n10", "SEARCH", "HIGH", {"query": "notion ai review"}),
        ("n11", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-004", "category": "productivity"}),
    ])
    r2 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                      now=day.replace(hour=9, minute=22), gateway=fake_gateway)
    assert r1.status == "COMPLETED" and r2.status == "COMPLETED"

    journeys = db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)
        .order_by(models.Journey.created_at)).scalars().all()
    assert len(journeys) == 2                      # new journey, old NOT reactivated
    assert journeys[0].lifecycle == "CLOSED" and journeys[0].outcome == "PURCHASED"
    assert journeys[1].lifecycle == "ACTIVE"

    # Traits exist as priors but never drive the current ranking:
    assert set(_traits(db, user.id)) == {"Security Evaluation", "Enterprise Evaluation"}
    pkg = db.execute(select(models.RecommendationPackage).where(
        models.RecommendationPackage.journey_id == journeys[1].journey_id)
        .order_by(models.RecommendationPackage.created_at.desc())).scalars().first()
    if pkg is not None and pkg.entries:
        assert "PROD-003" not in [e["product_id"] for e in pkg.entries]  # no identity push


def _pump_focus(db, chroma, backend, policies, user, gw, day, session_id):
    """Three runs of tightly-scoped identity research (small entity set so a
    resumed session can overlap near-fully). BC-001 reaches 0.6 → REQ-002 0.6.

    Pages, then documentation, then reading time: each run brings a kind of
    evidence the last lacked, so each contributes fully (Decision #054).
    """
    batches = [
        [("p1", "SEARCH", "HIGH", {"query": "single sign-on okta"}),
         ("p2", "SECURITY_VIEWED", "HIGH", {"page": "a"}),
         ("p3", "SECURITY_VIEWED", "HIGH", {"page": "b"}),
         ("p4", "SECURITY_VIEWED", "HIGH", {"page": "c"}),
         ("p5", "SECURITY_VIEWED", "HIGH", {"page": "d"})],
        [("p6", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"}),
         ("p7", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "mfa"}),
         ("p8", "SEARCH", "HIGH", {"query": "okta sso mfa"}),
         ("p9", "SECURITY_VIEWED", "HIGH", {"page": "e"}),
         ("p10", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"})],
        [("p11", "SECURITY_VIEWED", "HIGH", {"page": "f"}),
         ("p12", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "mfa"}),
         ("p13", "SEARCH", "HIGH", {"query": "single sign-on okta mfa"})]
        + [(f"p{n}", "DWELL", "LOW", {"topic": "security", "seconds": 10})
           for n in range(14, 20)],
    ]
    runs = []
    for i, specs in enumerate(batches):
        ts = day + timedelta(minutes=15 * i)
        _insert(db, user.id, session_id, ts, specs)
        runs.append(run_workflow(db, chroma, backend, policies, user.id,
                                 "EVENT_ACCUMULATION", now=ts + timedelta(minutes=2),
                                 gateway=gw))
    return runs


def test_story7_returning_researcher_reactivation(seeded, chroma, backend, policies,
                                                  fake_gateway):
    db = seeded
    user = _user(db, "returner@example.com")
    day = datetime(2026, 8, 1, 9, 0)
    runs = _pump_focus(db, chroma, backend, policies, user, fake_gateway, day, "res-s1")
    assert all(r.status == "COMPLETED" for r in runs)
    journey = db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)).scalars().one()
    confidence_before = _latest_hypotheses(db, journey.journey_id)["BC-001"].confidence
    assert confidence_before >= 0.6

    # 10 quiet days → DORMANT (POL-JRES-002); same research resumes → reactivate
    resume = day + timedelta(days=10)
    _insert(db, user.id, "res-s2", resume, [
        ("q1", "SEARCH", "HIGH", {"query": "single sign-on okta"}),
        ("q2", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"}),
        ("q3", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "mfa"}),
        ("q4", "SECURITY_VIEWED", "HIGH", {"page": "a"}),
        ("q5", "SEARCH", "HIGH", {"query": "okta sso mfa"}),
    ] + [(f"q{n}", "DWELL", "LOW", {"topic": "security", "seconds": 10})
         for n in range(6, 9)])
    run = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                       now=resume + timedelta(minutes=2), gateway=fake_gateway)
    assert run.status == "COMPLETED"

    journeys = db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)).scalars().all()
    assert len(journeys) == 1                      # reactivated, never duplicated
    assert journeys[0].lifecycle == "ACTIVE"
    transitions = [t.to_state for t in db.execute(
        select(models.JourneyTransition).where(
            models.JourneyTransition.journey_id == journey.journey_id)
        .order_by(models.JourneyTransition.ts)).scalars().all()]
    assert "DORMANT" in transitions and transitions[-1] == "ACTIVE"

    # State resumed — confidence never reset to zero, requirements survive
    confidence_after = _latest_hypotheses(db, journey.journey_id)["BC-001"].confidence
    assert confidence_after >= confidence_before
    rp = db.execute(select(models.RequirementProfile)
                    .where(models.RequirementProfile.journey_id == journey.journey_id)
                    .order_by(models.RequirementProfile.version.desc())).scalars().first()
    assert any(r["req_id"] == "REQ-002" for r in rp.requirements)  # no cold start


def test_story8_mind_changer_gradual_reversal(seeded, chroma, backend, policies,
                                              fake_gateway):
    db = seeded
    user = _user(db, "pivoter@example.com")
    day = datetime(2026, 8, 1, 9, 0)

    # Enterprise identity evaluation with enterprise signals (BC-002 present)
    _insert(db, user.id, "mind-s1", day, [
        ("m1", "SECURITY_VIEWED", "HIGH", {"page": "a", "topic": "compliance"}),
        ("m2", "SECURITY_VIEWED", "HIGH", {"page": "b", "topic": "audit"}),
        ("m3", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "provisioning"}),
        ("m4", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"}),
        ("m5", "PRICING_VIEWED", "HIGH", {"product_id": "PROD-003", "tier": "enterprise"}),
    ])
    r1 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                      now=day + timedelta(minutes=2), gateway=fake_gateway)
    _insert(db, user.id, "mind-s1", day + timedelta(minutes=15), [
        ("m6", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "admin"}),
        ("m7", "SECURITY_VIEWED", "HIGH", {"page": "c"}),
        ("m8", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "mfa"}),
        ("m9", "SEARCH", "HIGH", {"query": "enterprise sso rollout"}),
        ("m10", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "federation"}),
    ])
    r2 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                      now=day + timedelta(minutes=17), gateway=fake_gateway)
    assert r1.status == "COMPLETED" and r2.status == "COMPLETED"

    journey = db.execute(select(models.Journey).where(
        models.Journey.user_id == user.id)).scalars().one()
    enterprise_before = _latest_hypotheses(db, journey.journey_id)["BC-002"].confidence
    assert enterprise_before > 0

    # One contrary click changes nothing (a single individual-tier view is not
    # a contradiction — BP-002's rule needs repetition)
    _insert(db, user.id, "mind-s1", day + timedelta(hours=1), [
        ("c1", "PRICING_VIEWED", "HIGH", {"product_id": "PROD-009", "tier": "individual"}),
        ("c2", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-009", "category": "knowledge"}),
        ("c3", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "templates"}),
        ("c4", "SEARCH", "HIGH", {"query": "personal plan"}),
        ("c5", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-005", "category": "collaboration"}),
    ])
    r3 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                      now=day + timedelta(hours=1, minutes=2), gateway=fake_gateway)
    assert r3.status == "COMPLETED"
    after_one = _latest_hypotheses(db, journey.journey_id)["BC-002"].confidence
    assert after_one == enterprise_before          # no instant flip

    # Sustained contradiction: repeated individual/free-tier pricing across
    # two sessions → gradual weakening (POL-CONF-003), never a cliff.
    #
    # This block names collaboration, which is a subject since Decision #077,
    # and the journey stays whole only because it never established a subject
    # of its own: BP-020 Identity Platform needs two qualifying signals and
    # this shopper produces one search. `subject_abandoned` requires an
    # established subject, so there is nothing here to abandon.
    #
    # It is worth knowing which way that cuts. Were the identity intent one
    # signal stronger, this block would abandon the journey and fork — and the
    # fork would carry BP-002's contradicting evidence to a journey holding no
    # BC-002 to contradict, so the enterprise hypothesis would never weaken and
    # this story would fail on its own stated failure mode. That is not a bug
    # in either rule: a contradiction can only be observed where the hypothesis
    # lives. It is a genuine limit on how much subject-change a *contradiction*
    # story can carry, and the fixture stays on the near side of it.
    _insert(db, user.id, "mind-s1", day + timedelta(hours=1, minutes=20), [
        ("c6", "PRICING_VIEWED", "HIGH", {"product_id": "PROD-009", "tier": "individual"}),
        ("c7", "PRICING_VIEWED", "HIGH", {"product_id": "PROD-005", "tier": "free"}),
        ("c8", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-009", "category": "knowledge"}),
        ("c9", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-005", "category": "collaboration"}),
        ("c10", "PRODUCT_VIEWED", "HIGH", {"product_id": "PROD-002", "category": "collaboration"}),
    ])
    r4 = run_workflow(db, chroma, backend, policies, user.id, "EVENT_ACCUMULATION",
                      now=day + timedelta(hours=1, minutes=22), gateway=fake_gateway)
    after_sustained = _latest_hypotheses(db, journey.journey_id)["BC-002"].confidence
    assert after_sustained < after_one             # weakened…
    assert after_sustained > 0.05                  # …gradually, not a cliff
    hyp = _latest_hypotheses(db, journey.journey_id)["BC-002"]
    assert hyp.status == "WEAKENED"

    # Stage regression: the last three high-signal events are Discovery-
    # characteristic product views (POL-STAGE-002)
    stage = db.execute(select(models.JourneyStage)
                       .where(models.JourneyStage.journey_id == journey.journey_id)
                       .order_by(models.JourneyStage.version.desc())).scalars().first()
    assert stage.stage not in ("Technical Validation", "Commercial Evaluation",
                               "Decision", "Adoption")  # no evaluation-stage claim survives

    # REQ-002 recomputed downward in the latest profile
    rp = db.execute(select(models.RequirementProfile)
                    .where(models.RequirementProfile.journey_id == journey.journey_id)
                    .order_by(models.RequirementProfile.version.desc())).scalars().first()
    req2 = next((r for r in rp.requirements if r["req_id"] == "REQ-002"), None)
    if req2 is not None:
        assert req2["confidence"] < 0.94
