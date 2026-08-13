"""Signature test: pins the Policy Catalog v1 transcription (docs/core/10) and the
single-loader contract (CLAUDE.md Law 4). If a policy ID disappears or a v1 value
drifts from the spec, this goes red."""

import pytest

from smartreco.policies import PolicyError, load_policies

# Every Policy ID published in Policy Catalog v1 (docs/core/10-decision-policies.md).
CATALOG_V1_IDS = [
    "POL-BEH-001", "POL-BEH-002",
    "POL-CONF-001", "POL-CONF-002", "POL-CONF-003", "POL-CONF-004", "POL-CONF-005",
    "POL-REQ-001", "POL-REQ-002", "POL-REQ-003",
    "POL-STAGE-001", "POL-STAGE-002",
    "POL-REC-001", "POL-REC-002", "POL-REC-003", "POL-REC-004",
    "POL-RETR-001", "POL-RETR-002", "POL-RETR-003", "POL-RETR-004", "POL-RETR-005",
    "POL-GATE-001",
    "POL-TRIG-001", "POL-TRIG-002", "POL-TRIG-003", "POL-TRIG-004", "POL-TRIG-005",
    "POL-CACHE-001",
    "POL-TRACK-001", "POL-TRACK-002", "POL-TRACK-003",
    "POL-LEARN-001", "POL-DECAY-001",
    "POL-JRES-001", "POL-JRES-002", "POL-JRES-003",
    "POL-DELIV-001", "POL-DELIV-002",
]


@pytest.fixture(scope="module")
def catalog():
    return load_policies()


def test_catalog_version_is_recorded(catalog):
    # v1.6: POL-STAGE-001 gained the evidence-free milestone arm and
    # POL-STAGE-002 the regression floor (#065); POL-BEH-002 acquired its first
    # consumer, so evidence ageing went from published-and-inert to in force
    # (#067). No parameter value moved in either — which is precisely the case
    # the comment below was written about.
    # v1.5: POL-JRES-001 gained the intra-session fork params (#056/#057).
    # v1.4 redefined POL-CONF-002's identity (#054). Both change behaviour
    # rather than a number, and the version is how a run says which build
    # produced it — #056 shipped without bumping it and the omission cost a
    # debugging round, because policy_version 1.4 could not distinguish a
    # server running the fork from one that was not.
    assert catalog.version == "1.6"
    assert catalog.param("POL-TRIG-002", "debounce_seconds") == 30
    assert catalog.param("POL-TRIG-002", "cooldown_seconds") == 45
    assert catalog.param("POL-TRIG-001", "unprocessed_event_threshold") == 3
    assert catalog.param("POL-TRIG-003", "tier1_calls_per_user_per_day") == 30
    assert catalog.param("POL-TRIG-003", "tier2_calls_per_user_per_day") == 40


def test_judgment_thresholds_are_untouched_by_demo_pacing(catalog):
    """v1.1 and v1.3 retuned *how often* the platform reasons. What it concludes
    is a separate class of value, pinned here so a future pacing change cannot
    quietly drift into lowering the bar for a claim (Decision #048)."""
    assert catalog.param("POL-REQ-001", "min_confidence") == 0.5
    assert catalog.param("POL-REC-001", "min_requirement_confidence") == 0.6
    assert catalog.param("POL-REC-001", "min_high_signal_events") == 5
    assert catalog.param("POL-BEH-001", "min_supporting_evidence") == 2
    assert catalog.param("POL-TRACK-003", "inactivity_minutes") == 30


def test_every_v1_policy_id_present_and_no_extras(catalog):
    assert catalog.policy_ids == sorted(CATALOG_V1_IDS)


def test_confidence_contributions_match_pol_conf_001(catalog):
    contribution = catalog.param("POL-CONF-001", "contribution")
    assert contribution == {"Weak": 0.05, "Medium": 0.10, "Strong": 0.20, "VeryStrong": 0.30}
    assert catalog.param("POL-CONF-001", "diversity_increment") == 0.10


def test_saturation_bounds_match_pol_conf_004(catalog):
    assert catalog.param("POL-CONF-004", "cap") == 0.95
    assert catalog.param("POL-CONF-004", "floor") == 0.05


def test_requirement_derivation_weights_match_pol_req_003(catalog):
    weights = catalog.param("POL-REQ-003", "association_weights")
    assert weights == {"Primary": 1.0, "Secondary": 0.6, "Supporting": 0.3}
    assert catalog.param("POL-REQ-003", "combination") == "noisy_or"


def test_ranking_weights_match_pol_rec_002(catalog):
    weights = catalog.param("POL-REC-002", "priority_weights")
    assert weights == {"Critical": 3, "High": 2, "Medium": 1, "Low": 0.5}


def test_readiness_thresholds_match_pol_rec_001(catalog):
    assert catalog.param("POL-REC-001", "min_requirement_confidence") == 0.6
    assert catalog.param("POL-REC-001", "min_high_signal_events") == 5


def test_retrieval_and_gateway_bounds(catalog):
    assert catalog.param("POL-RETR-001", "top_k") == 8
    assert catalog.param("POL-RETR-002", "max_refinements") == 2
    assert catalog.param("POL-GATE-001", "timeout_seconds") == 30
    assert catalog.param("POL-GATE-001", "max_retries") == 2


def test_journey_resolution_weights_match_pol_jres_001(catalog):
    weights = catalog.param("POL-JRES-001", "signal_weights")
    assert weights == {"topic": 0.4, "behavioral": 0.3, "time_decay": 0.3}
    assert catalog.param("POL-JRES-001", "reuse_active_min_score") == 0.6
    assert catalog.param("POL-JRES-001", "reactivate_dormant_min_score") == 0.7
    # Session settlement (Decision #041): ownership is decided once per session,
    # so it must not be decided while the session is too small to judge.
    assert catalog.param("POL-JRES-001", "min_session_events") == 5


def test_unknown_policy_or_param_fails_loud(catalog):
    with pytest.raises(PolicyError):
        catalog.get("POL-NOPE-999")
    with pytest.raises(PolicyError):
        catalog.param("POL-CONF-004", "not_a_param")
