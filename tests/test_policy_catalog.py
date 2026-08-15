"""Signature test: pins the Policy Catalog v1 transcription (docs/core/10) and the
single-loader contract (CLAUDE.md Law 4). If a policy ID disappears or a v1 value
drifts from the spec, this goes red."""

import pytest

from smartreco.policies import PolicyError, load_policies

# Every Policy ID published in Policy Catalog v1 (docs/core/10-decision-policies.md).
CATALOG_V1_IDS = [
    "POL-BEH-001", "POL-BEH-002",
    "POL-CONF-001", "POL-CONF-002", "POL-CONF-003", "POL-CONF-004", "POL-CONF-005",
    "POL-REQ-001", "POL-REQ-002", "POL-REQ-003", "POL-REQ-004",
    "POL-STAGE-001", "POL-STAGE-002",
    "POL-REC-001", "POL-REC-002", "POL-REC-003", "POL-REC-004",
    "POL-RETR-001", "POL-RETR-002", "POL-RETR-003", "POL-RETR-004", "POL-RETR-005",
    "POL-SRCH-001", "POL-SRCH-002",
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
    # v1.14: POL-SRCH-001 gained neighbour_band (#090). min_similarity now gates
    # the *top hit only*; the page is filled from within a band of it. Same
    # query, same set of pages — measured, the band cannot make an unanswerable
    # query answerable — but a page that held one product now holds several,
    # which is the difference between a fallback that produces evidence and one
    # that does not.
    # v1.13: POL-SRCH-001/002 are new — a search that matches nothing lexically
    # may now be answered from the vector index (#089). The same query under
    # 1.12 rendered an empty page, so this is a change in what a run *does*,
    # not only in how fast it gets there.
    # v1.12: POL-TRIG-002 gained closing_events_bypass_debounce_and_cooldown
    # (#085). A purchase now runs immediately where 1.11 made it wait out the
    # debounce window and the cooldown — the same events, a journey CLOSED up to
    # 75 seconds earlier, and traits written in time for the confirmation page.
    # v1.11: POL-REC-002 gained subject_category_min_confidence (#082) — the
    # categories a candidate is measured against now come from a lower bar than
    # POL-REQ-004's anchoring one. Same events, different match scores: a
    # shopper whose subject sits at 0.20 now has a subject *category*, so
    # Story 1 marks Microsoft 365 off-subject where 1.10 did not.
    # v1.10: POL-REC-002 split the published figure from the ranking one (#078).
    # `off_subject_factor` no longer multiplies coverage, so the same events
    # under 1.10 publish a *different percentage* than under 1.9 with the same
    # order — the widest kind of change this version string exists to record.
    # v1.9: POL-REQ-004's demotion narrowed — a lens is demoted only where it
    # feeds a Requirement other than an anchored one (#077). No parameter moved,
    # and the rule's scope did: an automation shopper who checks integrations
    # now keeps that contribution to the Requirement being anchored, so a run
    # under 1.9 publishes a different confidence than the same events under 1.8.
    # v1.8: POL-REQ-004 is new (subject anchoring) and POL-REC-002 gained
    # capability_weights + off_subject_factor (#073). Both change what a run
    # concludes, not merely how fast it gets there — the four doc 09 derivations
    # publish different percentages under v1.8 than under v1.7, with the same
    # ordering, so policy_version is the only thing distinguishing a package
    # produced before the change from one produced after.
    # v1.7: POL-JRES-001's recent_window_events changed meaning (#072) — it
    # bounds the journey's own history; the settled block is now "now".
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
    assert catalog.version == "1.14"
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


def test_search_fallback_bounds_match_pol_srch_001(catalog):
    """The floor is measured, not chosen (scripts/measure_search_floor.py), and
    it is the only thing standing between this feature and guessing: the two
    query classes overlap, so a floor set for recall answers "best pizza near
    the office" with a CRM. Pinned so a later retune is a deliberate act."""
    assert catalog.param("POL-SRCH-001", "min_similarity") == -0.38
    assert catalog.param("POL-SRCH-001", "neighbour_band") == 0.15
    assert catalog.param("POL-SRCH-001", "lexical_min_results") == 1
    assert catalog.param("POL-SRCH-001", "top_k") == 8
    assert catalog.param("POL-SRCH-001", "max_query_chars") == 200


def test_search_budget_is_its_own_ledger(catalog):
    """POL-SRCH-002 must never be POL-TRIG-003. A shopper who types a run of
    unmatched searches would otherwise spend the Tier 2 budget their own
    recommendations depend on — the platform's actual product — as a side
    effect of using the search box."""
    assert catalog.param("POL-SRCH-002", "searches_per_user_per_day") == 20
    assert catalog.param("POL-SRCH-002", "searches_per_anonymous_session") == 5
    assert catalog.param("POL-SRCH-002", "cache_ttl_seconds") == 3600
    assert catalog.param("POL-SRCH-002", "cache_max_entries") == 256
    # The separation that matters is structural, not numeric: search spend must
    # not appear among POL-TRIG-003's parameters at all.
    assert not [p for p in catalog.get("POL-TRIG-003").params if "search" in p]


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
