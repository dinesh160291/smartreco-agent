"""Live-gateway eval slice (testing contract: the eval suite and the smoke
test are the only live touchpoints).

Cases:
  E1 persuasion grounding — Scenario-1 facts → generated AAR must be
     structurally complete, name the provisioning/identity advantage class of
     facts, and contain no banned persuasion or canonical IDs.
  E2 retrieval evaluation contract — a deliberately mismatched candidate list
     must yield a parseable fail verdict with missing aspects.

Per the eval caveats: a failing case must fail 3x to count as a bug —
single-run LLM variance is not a signal. This script runs each case up to 3x
and reports flaky vs failing.

Run:  .venv\\Scripts\\python scripts\\eval_slice.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dotenv import load_dotenv

from smartreco.advisor import generate_sections
from smartreco.gateway import AIGateway
from smartreco.policies import load_policies
from smartreco.retrieval import EvaluationUnavailable, evaluate_candidates

BANNED = ["offer ends", "% off", "discount", "thousands of teams", "limited time"]

FACTS = {
    "products": [
        {"name": "Okta", "vendor": "Okta", "coverage": 81,
         "covered": ["Single Sign-On", "Multi-Factor Authentication", "SCIM Provisioning",
                     "Conditional Access", "Audit Logging"],
         "missing": ["Information Governance", "Data Retention", "eDiscovery"],
         "narrative": "Standardize identity across every application."}],
    "requirements": [{"name": "Identity Management", "priority": "Critical",
                      "confidence": 0.94}],
    "stage": "Technical Validation",
    "behavior_summary": "searched for: single sign-on; read pages about: sso, provisioning, mfa",
    "alternatives": [],
    "constraints": {},
}


def case_e1(gateway) -> list[str]:
    payload, _version, _calls = generate_sections(gateway, FACTS, "READY")
    problems = []
    text = json.dumps(payload).lower()
    for fragment in BANNED:
        if fragment in text:
            problems.append(f"banned persuasion: {fragment!r}")
    for banned_id in ("cap-0", "req-0", "prod-0"):
        if banned_id in text:
            problems.append(f"canonical ID leaked: {banned_id}")
    grounding_terms = ("sign-on", "sso", "provisioning", "identity")
    if not any(t in text for t in grounding_terms):
        problems.append("narrative never references the user's identity research")
    return problems


def case_e2(gateway) -> list[str]:
    try:
        verdict = evaluate_candidates(
            gateway,
            "requirement: Identity Management (priority CRITICAL)\n"
            "capability: Single Sign-On\ncapability: Multi-Factor Authentication",
            ["FlowReach: email campaign and social media scheduling platform",
             "BrightBooks: invoicing and general ledger for small firms"])
    except EvaluationUnavailable as exc:
        return [f"evaluation unavailable/malformed: {exc}"]
    if verdict["verdict"] != "fail":
        return ["mismatched candidates judged sufficient (expected fail verdict)"]
    if not verdict.get("missing_aspects"):
        return ["fail verdict without missing aspects"]
    return []


def run_case(name, fn, gateway) -> bool:
    failures = 0
    for attempt in range(3):
        problems = fn(gateway)
        if not problems:
            status = "PASS" + (f" (attempt {attempt + 1})" if attempt else "")
            print(f"{name}: {status}")
            if attempt:
                print(f"{name}: NOTE flaky — {failures} prior failure(s)")
            return True
        failures += 1
        print(f"{name}: attempt {attempt + 1} problems: {problems}")
    print(f"{name}: FAIL 3x — counts as a bug")
    return False


def main() -> int:
    load_dotenv()
    gateway = AIGateway(load_policies())
    ok = run_case("E1 persuasion-grounding", case_e1, gateway)
    ok = run_case("E2 retrieval-evaluation", case_e2, gateway) and ok
    print("\nEVAL SLICE:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
