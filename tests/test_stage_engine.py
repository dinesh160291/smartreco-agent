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
        evidence=[], hypotheses_by_concept={}, event_types=["SEARCH"], policies=policies)
    assert stage == "Awareness"


def test_research_on_weak_evaluation_evidence(policies):
    # Evaluation evidence at any strength satisfies Research, but Weak fails the
    # Technical Validation milestone (Medium or stronger required)
    stage, confidence, _ = determine_stage(
        evidence=[evid("BP-001", "WEAK")],
        hypotheses_by_concept={"BC-001": 0.8},
        event_types=["SECURITY_VIEWED"], policies=policies)
    assert stage == "Research"


def test_technical_validation_story1(policies):
    stage, confidence, _ = determine_stage(
        evidence=[evid("BP-001", "STRONG", "BE-1", ("BC-001",)),
                  evid("BP-002", "MEDIUM", "BE-2", ("BC-002",))],
        hypotheses_by_concept={"BC-001": 0.8, "BC-002": 0.7},
        event_types=["SECURITY_VIEWED", "COMPARISON_STARTED"], policies=policies)
    assert stage == "Technical Validation"
    assert confidence == 0.8  # max among supporting hypotheses


def test_stage_confidence_threshold_holds_stage_back(policies):
    # Milestone satisfied but supporting hypothesis confidence < 0.6 → stage not granted;
    # falls back to highest stage that passes (here Comparison via raw event)
    stage, _, _ = determine_stage(
        evidence=[evid("BP-001", "STRONG")],
        hypotheses_by_concept={"BC-001": 0.5},
        event_types=["SECURITY_VIEWED", "COMPARISON_STARTED"], policies=policies)
    assert stage == "Comparison"


def test_comparison_via_comparison_started_event(policies):
    stage, _, _ = determine_stage(
        evidence=[], hypotheses_by_concept={},
        event_types=["COMPARISON_STARTED"], policies=policies)
    assert stage == "Comparison"
