"""Signature tests: Tier 1 + Tier 2 contracts and their fallback paths
(core 15 §Malformed output, core 20 §evaluate/refine loop, core 21 fallbacks,
core 23 budgets/caching). Stubbed gateway throughout — including the malformed
responses the fallback paths need."""

from datetime import datetime

import pytest
from sqlalchemy import select

from tests.conftest import FakeGateway
from smartreco import models
from smartreco.advisor import (
    MalformedResponse,
    build_clarify_prompt,
    build_generate_prompt,
    generate_sections,
)
from smartreco.gateway import GatewayUnavailable
from smartreco.pipeline import run_workflow
from smartreco.repos import insert_events_idempotent
from smartreco.retrieval import compose_query_document, retrieve_with_refinement

FACTS = {
    "products": [{"name": "Okta", "vendor": "Okta", "coverage": 81,
                  "covered": ["Single Sign-On"], "missing": ["eDiscovery"],
                  "narrative": "Standardize identity across every application."}],
    "requirements": [{"name": "Identity Management", "priority": "Critical",
                      "confidence": 0.94}],
    "stage": "Technical Validation",
    "behavior_summary": "searched for: single sign-on",
    "alternatives": ["Box"],
    "constraints": {},
}


# ---- Tier 1: prompt hygiene + malformed handling ----

def test_generate_prompt_uses_display_names_and_delimited_data():
    prompt = build_generate_prompt(FACTS)
    assert "<data" in prompt and "</data>" in prompt  # quoted data, not instructions
    for banned in ("CAP-", "REQ-", "PROD-", "BC-", "BP-"):
        assert banned not in prompt  # vocabulary rule: no canonical IDs
    assert "Okta" in prompt and "Identity Management" in prompt


def test_clarify_prompt_never_lists_products():
    prompt = build_clarify_prompt({"behavior_summary": "browsed", "constraints": {"budget": "Unknown"}})
    assert "Do not recommend any product" in prompt


def test_malformed_once_regenerates_exactly_once():
    gw = FakeGateway()
    gw.malformed_tier1_remaining = 1
    payload, version, calls = generate_sections(gw, FACTS, "READY")
    assert calls == 2  # initial + exactly one regeneration
    assert payload["persuasive_narrative"]


def test_malformed_twice_is_node_failure():
    gw = FakeGateway()
    gw.malformed_tier1_remaining = 2
    with pytest.raises(MalformedResponse):
        generate_sections(gw, FACTS, "READY")
    assert len(gw.calls) == 2  # never a third attempt


# ---- Tier 2: bounded loop + degradation ----

def summaries():
    return ["Okta: identity", "Box: content"]


def test_tier2_pass_verdict_stops_loop(seeded, chroma, backend, policies):
    gw = FakeGateway()
    gw.evaluation_verdict = "pass"
    calls = []
    query = compose_query_document(
        [{"req_id": "REQ-002", "priority": "CRITICAL", "confidence": 0.9}],
        ["Security Evaluation"], "Research", [], {"REQ-002": "Identity Management"})
    candidates, history, _ = retrieve_with_refinement(
        seeded, chroma, backend, gw, query, policies,
        tier2_llm_allowed=True, record_tier2_call=lambda: calls.append(1))
    assert [h["action"] for h in history] == ["evaluate"]
    assert len(calls) == 1  # one evaluation call, no refinement
    assert candidates


def test_tier2_fail_verdict_refines_bounded(seeded, chroma, backend, policies):
    gw = FakeGateway()
    gw.evaluation_verdict = "fail"
    gw.missing_aspects = ["audit logging depth"]
    calls = []
    query = compose_query_document(
        [{"req_id": "REQ-002", "priority": "CRITICAL", "confidence": 0.9}],
        [], "Research", [], {"REQ-002": "Identity Management"})
    _candidates, history, final_query = retrieve_with_refinement(
        seeded, chroma, backend, gw, query, policies,
        tier2_llm_allowed=True, record_tier2_call=lambda: calls.append(1))
    refines = [h for h in history if h["action"] == "refine"]
    assert len(refines) == policies.param("POL-RETR-002", "max_refinements")
    assert final_query != query  # refined document was used
    assert refines[0]["missing_aspects"] == ["audit logging depth"]


def test_tier2_malformed_means_unavailable_initial_set_stands(seeded, chroma, backend, policies):
    gw = FakeGateway()
    gw.malformed_tier2_remaining = 1
    query = compose_query_document(
        [{"req_id": "REQ-002", "priority": "CRITICAL", "confidence": 0.9}],
        [], "Research", [], {"REQ-002": "Identity Management"})
    candidates, history, final_query = retrieve_with_refinement(
        seeded, chroma, backend, gw, query, policies,
        tier2_llm_allowed=True, record_tier2_call=lambda: None)
    assert history[-1]["action"] == "evaluation-unavailable"
    assert final_query == query  # pre-evaluation set stands, no refinement
    assert candidates


def test_tier2_budget_gate_skips_llm_entirely(seeded, chroma, backend, policies):
    gw = FakeGateway()
    candidates, history, _ = retrieve_with_refinement(
        seeded, chroma, backend, gw, "identity query", policies,
        tier2_llm_allowed=False, record_tier2_call=lambda: None)
    assert gw.calls == []  # zero LLM calls
    assert candidates  # deterministic retrieval still served


# ---- Pipeline-level: caching, budgets, full-catalog fallback ----

def _pump_requirements(db, user_id, gateway, chroma, backend, policies):
    """Three cooldown-spaced runs of growing security research → BC-001 0.6 →
    REQ-002 published at 0.6 → READY."""
    day = datetime(2026, 8, 3)
    batches = [
        (day.replace(hour=9, minute=0), [
            ("q1", "SEARCH", "HIGH", {"query": "single sign-on"}),
            ("q2", "SECURITY_VIEWED", "HIGH", {"page": "a"}),
            ("q3", "SECURITY_VIEWED", "HIGH", {"page": "b"}),
            ("q4", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"}),
            ("q5", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "mfa"}),
        ]),
        (day.replace(hour=9, minute=15), [
            ("q6", "SECURITY_VIEWED", "HIGH", {"page": "c"}),
            ("q7", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"}),
            ("q8", "SEARCH", "HIGH", {"query": "okta mfa"}),
            ("q9", "SECURITY_VIEWED", "HIGH", {"page": "d"}),
            ("q10", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "mfa"}),
        ]),
        (day.replace(hour=9, minute=30), [
            ("q11", "SECURITY_VIEWED", "HIGH", {"page": "e"}),
            ("q12", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "sso"}),
            ("q13", "SEARCH", "HIGH", {"query": "sso audit"}),
            ("q14", "SECURITY_VIEWED", "HIGH", {"page": "f"}),
            ("q15", "DOCUMENTATION_VIEWED", "HIGH", {"topic": "mfa"}),
        ]),
    ]
    runs = []
    for i, (ts, specs) in enumerate(batches):
        rows = [{"event_id": eid, "user_id": user_id, "session_id": "cache-s1",
                 "journey_id": None, "event_type": et, "signal_class": sig,
                 "event_metadata": md, "ts": ts, "received_at": ts,
                 "processed_at": None} for eid, et, sig, md in specs]
        if db.get(models.Session, "cache-s1") is None:
            db.add(models.Session(session_id="cache-s1", user_id=user_id,
                                  started_at=ts, last_event_at=ts))
        insert_events_idempotent(db, rows)
        db.commit()
        runs.append(run_workflow(db, chroma, backend, policies, user_id,
                                 "EVENT_ACCUMULATION", now=ts.replace(minute=ts.minute + 2),
                                 gateway=gateway))
    return runs


@pytest.fixture()
def cache_user(seeded):
    row = models.User(email="cache@example.com", password_hash="x")
    seeded.add(row)
    seeded.commit()
    return row


def test_aar_and_candidate_cache_prevent_regeneration(seeded, chroma, backend, policies,
                                                      cache_user, fake_gateway):
    runs = _pump_requirements(seeded, cache_user.id, fake_gateway, chroma, backend, policies)
    assert runs[-1].status == "COMPLETED"
    tier1_calls_after = len([c for c in fake_gateway.calls if "aar-" in c])

    # A pattern-neutral event arrives: no evidence delta → unchanged RP →
    # candidate-set cache hit (TTL) and AAR cache hit; zero new Tier 1 calls
    # (POL-CACHE-001 / core 23 material-change defense).
    ts = datetime(2026, 8, 3, 10, 0)
    insert_events_idempotent(seeded, [{
        "event_id": "q20", "user_id": cache_user.id, "session_id": "cache-s1",
        "journey_id": None, "event_type": "PRODUCT_VIEWED", "signal_class": "HIGH",
        "event_metadata": {"product_id": "PROD-010"}, "ts": ts, "received_at": ts,
        "processed_at": None}])
    seeded.commit()
    run = run_workflow(seeded, chroma, backend, policies, cache_user.id,
                       "SIGNIFICANT_EVENT", now=ts.replace(minute=5), gateway=fake_gateway)
    assert run.status == "COMPLETED"
    generate_nodes = [n for n in run.nodes if n["node"] in ("generate", "clarify")]
    assert generate_nodes and generate_nodes[0].get("cache_hit") is True
    assert len([c for c in fake_gateway.calls if "aar-" in c]) == tier1_calls_after

    retrieve_nodes = [n for n in run.nodes if n["node"] == "retrieve"]
    assert retrieve_nodes and retrieve_nodes[0]["cache_hit"] is True  # CS within TTL


def test_tier1_budget_exhaustion_serves_last_aar(seeded, chroma, backend, policies,
                                                 cache_user, fake_gateway):
    # Exhaust tier1 budget before any run
    limit = policies.param("POL-TRIG-003", "tier1_calls_per_user_per_day")
    seeded.add(models.AIUsage(user_id=cache_user.id, day="2026-08-03",
                              tier="tier1", calls=limit))
    seeded.commit()
    runs = _pump_requirements(seeded, cache_user.id, fake_gateway, chroma, backend, policies)
    assert runs[-1].status == "COMPLETED"  # deterministic run never blocked
    assert [c for c in fake_gateway.calls if "aar-" in c] == []  # no Tier 1 spend
    tier1_nodes = [n for run in runs for n in run.nodes if n["node"] in ("generate", "clarify")]
    assert any("budget" in str(n.get("skipped", "")) for n in tier1_nodes)
    # Deterministic package still published
    pkg = seeded.execute(select(models.RecommendationPackage)).scalars().all()
    assert pkg


class GatewayDownBackend:
    def embed(self, texts):
        raise GatewayUnavailable("stub: embeddings down")


def test_tier2_total_failure_falls_back_to_full_catalog(seeded, chroma, policies,
                                                        cache_user, fake_gateway):
    runs = _pump_requirements(seeded, cache_user.id, fake_gateway, chroma,
                              GatewayDownBackend(), policies)
    last = runs[-1]
    assert last.status == "COMPLETED"
    pkg = seeded.execute(
        select(models.RecommendationPackage)
        .order_by(models.RecommendationPackage.created_at.desc())).scalars().first()
    assert pkg is not None
    assert pkg.cs_id is None  # null Candidate Set reference — degradation observable
    assert pkg.entries  # full-catalog matching still produced ranked entries
    assert any(n["node"] == "match_fallback" for n in last.nodes)
