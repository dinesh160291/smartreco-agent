"""Signature tests: Journey Stage Engine.

Pins the Stage Qualification Milestones (Domain 00 §4.1) and POL-STAGE-001
(highest satisfied milestone, stage confidence = max supporting hypothesis
confidence, threshold ≥ 0.6). Story 1 expects Technical Validation."""

import pytest

from smartreco.engines.stages import determine_stage
from smartreco.policies import load_policies


@pytest.fixture(scope="module")
def policies():
    return load_policies()


def evid(pattern, strength, evidence_id="BE-1", concepts=("BC-001",)):
    return {"evidence_id": evidence_id, "pattern_id": pattern, "strength": strength,
            "concept_ids": list(concepts)}


def test_awareness_when_events_but_no_evidence(policies):
    stage, confidence, _ = determine_stage(
        evidence=[], hypotheses_by_concept={}, events=[{"event_type": "SEARCH", "metadata": {}}], policies=policies)
    assert stage == "Awareness"


def test_research_on_weak_evaluation_evidence(policies):
    # Evaluation evidence at any strength satisfies Research, but Weak fails the
    # Technical Validation milestone (Medium or stronger required)
    stage, confidence, _ = determine_stage(
        evidence=[evid("BP-001", "WEAK")],
        hypotheses_by_concept={"BC-001": 0.8},
        events=[{"event_type": "SECURITY_VIEWED", "metadata": {}}], policies=policies)
    assert stage == "Research"


def test_technical_validation_story1(policies):
    stage, confidence, _ = determine_stage(
        evidence=[evid("BP-001", "STRONG", "BE-1", ("BC-001",)),
                  evid("BP-002", "MEDIUM", "BE-2", ("BC-002",))],
        hypotheses_by_concept={"BC-001": 0.8, "BC-002": 0.7},
        events=[{"event_type": "SECURITY_VIEWED", "metadata": {}}, {"event_type": "COMPARISON_STARTED", "metadata": {}}], policies=policies)
    assert stage == "Technical Validation"
    assert confidence == 0.8  # max among supporting hypotheses


def test_stage_confidence_threshold_holds_stage_back(policies):
    # Milestone satisfied but supporting hypothesis confidence < 0.6 → stage not granted;
    # falls back to highest stage that passes (here Comparison via raw event)
    stage, _, _ = determine_stage(
        evidence=[evid("BP-001", "STRONG")],
        hypotheses_by_concept={"BC-001": 0.5},
        events=[{"event_type": "SECURITY_VIEWED", "metadata": {}}, {"event_type": "COMPARISON_STARTED", "metadata": {}}], policies=policies)
    assert stage == "Comparison"


def test_comparison_via_comparison_started_event(policies):
    stage, _, _ = determine_stage(
        evidence=[], hypotheses_by_concept={},
        events=[{"event_type": "COMPARISON_STARTED", "metadata": {}}], policies=policies)
    assert stage == "Comparison"


# --- Adoption: the milestone is about onboarding *this* product (Decision #046) ---

def _ev(event_type, **metadata):
    return {"event_type": event_type, "metadata": metadata}


ADOPTION_EVIDENCE = [{"evidence_id": "BE-a", "pattern_id": "BP-011",
                      "strength": "STRONG", "concept_ids": ["BC-015"]}]
CONFIDENT = {"BC-015": 0.9}


def test_adoption_needs_onboarding_activity_not_just_any_documentation(policies):
    """Domain 00 §4.1: Adoption requires BP-011 evidence *and the journey's
    affinity product has onboarding/migration activity*.

    The engine only received a list of event-type names, so it could not ask
    what a documentation view was about and settled for "any DOCUMENTATION_VIEWED
    exists". A shopper who started a trial and had once opened any product's
    docs tab jumped to the highest stage in the model — and stage gates the
    Critical priority band, which carries triple weight in ranking.
    """
    stage, _, _ = determine_stage(
        evidence=ADOPTION_EVIDENCE, hypotheses_by_concept=CONFIDENT,
        events=[_ev("TRIAL_STARTED", product_id="PROD-003"),
                _ev("DOCUMENTATION_VIEWED", product_id="PROD-003", topic="sso")],
        policies=policies)
    assert stage != "Adoption", (
        "reading unrelated documentation advanced the journey to Adoption")


def test_adoption_needs_the_onboarding_to_be_for_the_adopted_product(policies):
    """Onboarding a different product is somebody else's rollout."""
    stage, _, _ = determine_stage(
        evidence=ADOPTION_EVIDENCE, hypotheses_by_concept=CONFIDENT,
        events=[_ev("TRIAL_STARTED", product_id="PROD-003"),
                _ev("DOCUMENTATION_VIEWED", product_id="PROD-185", topic="onboarding")],
        policies=policies)
    assert stage != "Adoption", (
        "onboarding activity on an unrelated product advanced the journey")


def test_adoption_is_reached_when_the_adopted_product_is_being_onboarded(policies):
    """The counterpart, so the fix cannot be 'Adoption is unreachable'."""
    stage, _, _ = determine_stage(
        evidence=ADOPTION_EVIDENCE, hypotheses_by_concept=CONFIDENT,
        events=[_ev("TRIAL_STARTED", product_id="PROD-003"),
                _ev("DOCUMENTATION_VIEWED", product_id="PROD-003", topic="migration")],
        policies=policies)
    assert stage == "Adoption"


def test_adoption_falls_back_to_topic_alone_when_no_product_is_identifiable(policies):
    """Some adoption triggers carry no product — a checkout covers the cart.
    Requiring a product match then would make Adoption unreachable, so the
    topic condition stands on its own in that case.
    """
    stage, _, _ = determine_stage(
        evidence=ADOPTION_EVIDENCE, hypotheses_by_concept=CONFIDENT,
        events=[_ev("CHECKOUT_STARTED"),
                _ev("DOCUMENTATION_VIEWED", product_id="PROD-003", topic="onboarding")],
        policies=policies)
    assert stage == "Adoption"
