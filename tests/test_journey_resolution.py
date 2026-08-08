"""Signature tests: Journey Resolution signals + decision (docs/core/12, POL-JRES-001).

Topic = Jaccard over entity sets; behavioral = cosine over normalized event-type
histograms; time decay = 0.5^(days/half_life); cold start → create; CLOSED
journeys are never candidates."""

import math

import pytest

from smartreco.engines.journey_resolution import (
    behavioral_similarity,
    resolution_score,
    resolve,
    time_decay,
    topic_similarity,
)
from smartreco.policies import load_policies


@pytest.fixture(scope="module")
def policies():
    return load_policies()


def test_topic_similarity_jaccard():
    assert topic_similarity({"okta", "sso"}, {"okta", "sso"}) == 1.0
    assert topic_similarity({"okta"}, {"slack"}) == 0.0
    assert topic_similarity({"okta", "sso"}, {"okta", "pricing"}) == pytest.approx(1 / 3)
    assert topic_similarity(set(), set()) == 0.0


def test_behavioral_similarity_cosine():
    same = {"SEARCH": 2, "PRODUCT_VIEWED": 4}
    assert behavioral_similarity(same, same) == pytest.approx(1.0)
    assert behavioral_similarity({"SEARCH": 3}, {"DWELL": 5}) == 0.0
    assert behavioral_similarity({}, {"SEARCH": 1}) == 0.0


def test_time_decay_half_life(policies):
    half_life = policies.param("POL-JRES-001", "time_decay_half_life_days")
    assert time_decay(0, half_life) == 1.0
    assert time_decay(half_life, half_life) == pytest.approx(0.5)
    assert time_decay(10, 7) == pytest.approx(0.5 ** (10 / 7))


def test_resolution_score_weights(policies):
    score = resolution_score(1.0, 1.0, 1.0, policies)
    assert score == pytest.approx(1.0)
    score = resolution_score(1.0, 0.0, 0.0, policies)
    assert score == pytest.approx(0.4)  # topic weight


def test_cold_start_creates(policies):
    decision = resolve(session_entities={"okta"}, session_histogram={"SEARCH": 1},
                       candidates=[], policies=policies)
    assert decision.action == "CREATE"


def test_reuse_active_at_threshold(policies):
    candidate = {"journey_id": "J1", "lifecycle": "ACTIVE",
                 "entities": {"okta", "sso"}, "histogram": {"SEARCH": 1, "PRODUCT_VIEWED": 1},
                 "days_inactive": 0}
    decision = resolve(session_entities={"okta", "sso"},
                       session_histogram={"SEARCH": 1, "PRODUCT_VIEWED": 1},
                       candidates=[candidate], policies=policies)
    assert decision.action == "CONTINUE" and decision.journey_id == "J1"


def test_dormant_needs_higher_threshold(policies):
    # Score ≈ 0.4×1 + 0.3×1 + 0.3×decay(10d) ≈ 0.81 ≥ 0.7 → reactivate
    candidate = {"journey_id": "J2", "lifecycle": "DORMANT",
                 "entities": {"okta"}, "histogram": {"SEARCH": 1}, "days_inactive": 10}
    decision = resolve(session_entities={"okta"}, session_histogram={"SEARCH": 1},
                       candidates=[candidate], policies=policies)
    assert decision.action == "REACTIVATE"
    # Disjoint topics + different behavior → score ≈ 0.3×0.37 < 0.7 → create new
    decision2 = resolve(session_entities={"zapier"}, session_histogram={"DOCUMENTATION_VIEWED": 3},
                        candidates=[candidate], policies=policies)
    assert decision2.action == "CREATE"


def test_closed_journeys_are_never_candidates(policies):
    candidate = {"journey_id": "J3", "lifecycle": "CLOSED",
                 "entities": {"okta"}, "histogram": {"SEARCH": 1}, "days_inactive": 0}
    decision = resolve(session_entities={"okta"}, session_histogram={"SEARCH": 1},
                       candidates=[candidate], policies=policies)
    assert decision.action == "CREATE"
