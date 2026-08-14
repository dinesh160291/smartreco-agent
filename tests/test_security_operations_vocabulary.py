"""Signature tests for the security-operations capability vocabulary — Decision #074.

The defect these pin: Security Operations was described by two purpose-built
capabilities where People Operations and Engineering Delivery had five, and it
borrowed Identity Federation and Compliance Reporting to make up the difference.
CrowdStrike Falcon and SentinelOne each held exactly Encryption, Threat
Protection and Data Loss Prevention — identical to one another and a strict
subset of LastPass's eight — so the pack could not tell an endpoint-security
product from a password manager, and ranking put the password manager first.

Requirement→capability structure is asserted here, never product prose.
"""

import json
import pathlib

import pytest

from smartreco.domain.software_buying import (
    CAPABILITIES, REQ_TO_CAP, UI_DOC_TOPICS, UI_SECURITY_TOPICS,
    UI_SECURITY_TOPIC_DEFAULT,
)
from smartreco.engines.matching import rank_products
from smartreco.policies import load_policies

SECOPS = "REQ-012"


@pytest.fixture(scope="module")
def policies():
    return load_policies()


@pytest.fixture(scope="module")
def catalog():
    raw = json.loads(pathlib.Path("seed/products.json").read_text(encoding="utf-8"))
    rows = raw["products"] if isinstance(raw, dict) else raw
    return {r["name"]: r for r in rows}


def test_security_operations_is_described_by_security_capabilities():
    """It borrowed Identity Federation because it had nothing of its own to say.
    That borrowing is what let identity products out-cover endpoint-security ones
    on the security requirement."""
    domain_of = {cap_id: domain for cap_id, _n, domain, _v in CAPABILITIES}
    assert {domain_of[c] for c in REQ_TO_CAP[SECOPS]} == {"Security"}
    assert "CAP-008" not in REQ_TO_CAP[SECOPS], "Identity Federation is an identity capability"
    assert "CAP-027" not in REQ_TO_CAP[SECOPS], "Compliance Reporting is what REQ-004 is for"


def test_security_operations_has_a_subject_areas_worth_of_vocabulary():
    """People Operations and Engineering Delivery each get five capabilities. A
    subject area described by two cannot distinguish the products inside it."""
    assert len(REQ_TO_CAP[SECOPS]) >= 5
    primaries = [c for c, a in REQ_TO_CAP[SECOPS].items() if a == "Primary"]
    assert "CAP-059" in primaries, "endpoint detection is the defining security-ops capability"


def test_endpoint_products_are_no_longer_indistinguishable(catalog):
    """The two archetypal endpoint products held identical capability sets, so no
    ranking could ever separate them or lift either above a password manager."""
    falcon = set(catalog["CrowdStrike Falcon"]["capabilities"])
    sentinel = set(catalog["SentinelOne"]["capabilities"])
    lastpass = set(catalog["LastPass"]["capabilities"])
    assert falcon != sentinel
    assert not falcon <= lastpass, "endpoint security still reads as a subset of a password manager"
    assert "CAP-059" in falcon and "CAP-059" in sentinel
    assert "CAP-059" not in lastpass


def test_an_endpoint_product_fully_covers_security_operations_and_a_vault_does_not(catalog, policies):
    """The end of the chain: with Security Operations Critical, the endpoint
    product must cover it outright and outrank the password manager that used to
    win by holding more of the same three capabilities."""
    reqs = [{"req_id": SECOPS, "priority": "CRITICAL", "confidence": 0.65}]
    caps = {name: set(catalog[name]["capabilities"])
            for name in ("CrowdStrike Falcon", "SentinelOne", "LastPass", "1Password Business")}
    entries = rank_products(reqs, sorted(caps), caps, REQ_TO_CAP, policies)
    by = {e["product_id"]: e for e in entries}
    assert by["CrowdStrike Falcon"]["overall_coverage"] == 100
    assert by["CrowdStrike Falcon"]["rank"] == 1
    assert by["SentinelOne"]["rank"] == 2
    for vault in ("LastPass", "1Password Business"):
        assert by[vault]["overall_coverage"] < by["SentinelOne"]["overall_coverage"]


# ---- UI reachability: a capability no surface reports cannot be researched ----

def _topic_for(capability_ids, table, default):
    held = set(capability_ids)
    for cap_id, topic in table:
        if cap_id in held:
            return topic
    return default


def test_an_endpoint_products_security_pane_reports_threat(catalog):
    """With no threat row in the table at all, the security pane of every
    endpoint-security product fell to the "compliance" default and voted for
    Enterprise Evaluation — a shopper reading CrowdStrike's security page was
    emitting evidence that they were vetting a vendor's paperwork."""
    for name in ("CrowdStrike Falcon", "SentinelOne"):
        topic = _topic_for(catalog[name]["capabilities"], UI_SECURITY_TOPICS,
                           UI_SECURITY_TOPIC_DEFAULT)
        assert topic == "threat", f"{name} security pane reported {topic!r}"


def test_a_governance_products_security_pane_still_reports_certifications(catalog):
    """Threat Protection is held by twenty-one products including analytics and
    content suites, so it must not lead this table: ordering it first took
    Compliance Evaluation out of the browser's reach entirely."""
    assert _topic_for(catalog["Vanta"]["capabilities"], UI_SECURITY_TOPICS,
                      UI_SECURITY_TOPIC_DEFAULT) == "certifications"


def test_every_new_capability_is_reachable_from_a_documentation_tab():
    """A pattern keyed on a topic no surface emits cannot fire from a browser
    (Decision #044). Each new capability must map to some doc topic."""
    mapped = {cap_id for cap_id, _topic in UI_DOC_TOPICS}
    for cap_id in ("CAP-059", "CAP-060", "CAP-061", "CAP-062"):
        assert cap_id in mapped, f"{cap_id} reaches no documentation tab"
