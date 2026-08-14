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
    """Doc 09 Scenario 1, as amended by Decision #050.

    Identity Management is derived from Security Evaluation alone (0.80).
    Enterprise Evaluation no longer contributes to it: buying at organizational
    scale is a fact about the buyer, not a statement that they need identity
    software. Its Secondary link to Regulatory Compliance survives — governance
    obligations genuinely do follow from organizational adoption — so REQ-004
    is unchanged, and with it the priority bands and every coverage percentage
    the story asserts.
    """
    hypotheses = {"BC-001": 0.80, "BC-002": 0.70}
    profile = derive_requirements(hypotheses, BC_TO_REQ, "Technical Validation", policies)
    reqs = by_req(profile)
    assert set(reqs) == {"REQ-002", "REQ-004"}  # REQ-001 at 0.48 held below 0.5
    assert reqs["REQ-002"]["confidence"] == 0.80  # was 0.94 with BC-002 Primary
    assert reqs["REQ-002"]["priority"] == "CRITICAL"
    assert reqs["REQ-004"]["confidence"] == 0.56
    assert reqs["REQ-004"]["priority"] == "MEDIUM"


def test_enterprise_evaluation_states_no_identity_need(policies):
    """The defect Decision #050 closes, at the mapping layer.

    An enterprise buyer with no security research at all must not produce an
    Identity Management requirement. Before this change a lone Enterprise
    Evaluation hypothesis at 0.70 published one at 0.70 — which is how an HR
    shopper reading a provisioning page could be told they need identity
    software.
    """
    profile = derive_requirements({"BC-002": 0.70}, BC_TO_REQ, "Technical Validation", policies)
    reqs = by_req(profile)
    assert "REQ-002" not in reqs
    # Governance still follows from organizational scale, but Secondary weight
    # puts it at 0.42 — below POL-REQ-001's 0.5 bar. So knowing only that the
    # buyer is an enterprise publishes nothing at all, which is the point.
    assert reqs == {}


def test_scenario_2_collaboration_productivity(policies):
    hypotheses = {"BC-005": 0.80, "BC-006": 0.50, "BC-003": 0.50}
    profile = derive_requirements(hypotheses, BC_TO_REQ, "Technical Validation", policies)
    reqs = by_req(profile)
    # REQ-013 joins and REQ-005 falls a band, both for the same reason
    # (Decision #079): Productivity Evaluation used to be Primary evidence of
    # wanting an AI assistant, which it never was. This shopper read
    # documentation about templates and tasks — that is a work-management need,
    # and their AI interest now rests on their AI research alone, where it
    # belongs. REQ-003 0.41 and REQ-002 0.24 still held.
    assert set(reqs) == {"REQ-001", "REQ-005", "REQ-013"}
    assert reqs["REQ-001"]["confidence"] == 0.83
    assert reqs["REQ-001"]["priority"] == "CRITICAL"
    assert reqs["REQ-005"]["confidence"] == 0.50
    assert reqs["REQ-005"]["priority"] == "MEDIUM"
    assert reqs["REQ-013"]["confidence"] == 0.50
    assert reqs["REQ-013"]["priority"] == "MEDIUM"


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


def test_scenario_5_sales_and_customer_management(policies):
    """Doc 09 Scenario 5 — the v1.2 coverage extension's derivation.

    The first four scenarios all resolve inside the original five requirements.
    This one is the regression case for the journey that motivated doc 14: before
    the extension it published Workflow Automation and Identity Management,
    because the platform had no way to represent wanting a CRM.
    """
    hypotheses = {"BC-019": 0.80, "BC-022": 0.50}
    profile = derive_requirements(hypotheses, BC_TO_REQ, "Technical Validation", policies)
    reqs = by_req(profile)
    # REQ-003 0.24, REQ-011 0.30, REQ-005 0.15 all held below 0.5
    assert set(reqs) == {"REQ-006", "REQ-009"}
    assert reqs["REQ-006"]["confidence"] == 0.80
    assert reqs["REQ-006"]["priority"] == "CRITICAL"
    assert reqs["REQ-009"]["confidence"] == 0.74
    assert reqs["REQ-009"]["priority"] == "HIGH"


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
