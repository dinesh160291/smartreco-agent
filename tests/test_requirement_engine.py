"""Signature tests: Requirement Engine derivation.

Pins POL-REQ-003 (noisy-OR over association weights), POL-REQ-001 (publication
threshold), POL-REQ-002 (priority bands incl. the Critical stage condition) —
exact numbers from all four validation scenarios in
docs/domains/software-buying/09."""

import pytest

from smartreco.domain.software_buying import BC_TO_REQ
from smartreco.engines.requirements import derive_requirements
from smartreco.policies import load_policies


@pytest.fixture(scope="module")
def policies():
    return load_policies()


def by_req(profile):
    return {entry["req_id"]: entry for entry in profile}


def test_scenario_1_security_identity(policies):
    hypotheses = {"BC-001": 0.80, "BC-002": 0.70}
    profile = derive_requirements(hypotheses, BC_TO_REQ, "Technical Validation", policies)
    reqs = by_req(profile)
    assert set(reqs) == {"REQ-002", "REQ-004"}  # REQ-001 at 0.48 held below 0.5
    assert reqs["REQ-002"]["confidence"] == 0.94
    assert reqs["REQ-002"]["priority"] == "CRITICAL"
    assert reqs["REQ-004"]["confidence"] == 0.56
    assert reqs["REQ-004"]["priority"] == "MEDIUM"


def test_scenario_2_collaboration_productivity(policies):
    hypotheses = {"BC-005": 0.80, "BC-006": 0.50, "BC-003": 0.50}
    profile = derive_requirements(hypotheses, BC_TO_REQ, "Technical Validation", policies)
    reqs = by_req(profile)
    assert set(reqs) == {"REQ-001", "REQ-005"}  # REQ-003 0.41 and REQ-002 0.24 held
    assert reqs["REQ-001"]["confidence"] == 0.83
    assert reqs["REQ-001"]["priority"] == "CRITICAL"
    assert reqs["REQ-005"]["confidence"] == 0.75
    assert reqs["REQ-005"]["priority"] == "HIGH"


def test_scenario_3_process_automation(policies):
    hypotheses = {"BC-007": 0.80, "BC-008": 0.70}
    profile = derive_requirements(hypotheses, BC_TO_REQ, "Technical Validation", policies)
    reqs = by_req(profile)
    assert set(reqs) == {"REQ-003"}
    assert reqs["REQ-003"]["confidence"] == 0.94
    assert reqs["REQ-003"]["priority"] == "CRITICAL"


def test_scenario_4_governance_compliance(policies):
    hypotheses = {"BC-004": 0.80}
    profile = derive_requirements(hypotheses, BC_TO_REQ, "Technical Validation", policies)
    reqs = by_req(profile)
    assert set(reqs) == {"REQ-004"}
    assert reqs["REQ-004"]["confidence"] == 0.80
    assert reqs["REQ-004"]["priority"] == "CRITICAL"


def test_critical_band_requires_stage_pol_req_002(policies):
    # Same 0.94 confidence, but stage below Technical Validation → HIGH, not CRITICAL
    hypotheses = {"BC-001": 0.80, "BC-002": 0.70}
    profile = derive_requirements(hypotheses, BC_TO_REQ, "Research", policies)
    assert by_req(profile)["REQ-002"]["priority"] == "HIGH"


def test_retired_hypotheses_contribute_nothing_pol_req_003(policies):
    # Only BC-001 active: REQ-002 = 1 − (1 − 1.0×0.8) = 0.80
    profile = derive_requirements({"BC-001": 0.80}, BC_TO_REQ, "Technical Validation", policies)
    assert by_req(profile)["REQ-002"]["confidence"] == 0.80


def test_requirements_carry_explanations(policies):
    profile = derive_requirements({"BC-001": 0.80}, BC_TO_REQ, "Technical Validation", policies)
    entry = by_req(profile)["REQ-002"]
    assert "BC-001" in entry["explanation"]
    assert "noisy-OR" in entry["explanation"] or "POL-REQ-003" in entry["explanation"]
