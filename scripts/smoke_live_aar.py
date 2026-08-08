"""Live-gateway smoke test (Gate G2): one real Tier 1 call producing a
persuasive AAR from canonical Scenario 1 facts.

The only place outside the eval suite that touches the live provider
(testing contract). Asserts structure and grounding hygiene — never prose.

Run:  .venv\\Scripts\\python scripts\\smoke_live_aar.py
"""

import json
import sys

from dotenv import load_dotenv

from smartreco.advisor import generate_sections, assemble_aar_sections
from smartreco.gateway import AIGateway
from smartreco.policies import load_policies

FACTS = {
    "products": [
        {"name": "Okta", "vendor": "Okta", "coverage": 81,
         "covered": ["Single Sign-On", "Multi-Factor Authentication",
                     "SCIM Provisioning", "Conditional Access", "Audit Logging"],
         "missing": ["Information Governance", "Data Retention", "eDiscovery"],
         "narrative": "Standardize identity across every application while reducing "
                      "authentication risk and manual identity administration."},
        {"name": "Microsoft 365", "vendor": "Microsoft", "coverage": 70,
         "covered": ["Single Sign-On", "Multi-Factor Authentication", "Audit Logging",
                     "Information Governance", "Data Retention", "eDiscovery"],
         "missing": ["SCIM Provisioning", "Conditional Access"],
         "narrative": "Enable secure collaboration and organizational productivity "
                      "through an integrated cloud platform."},
    ],
    "requirements": [
        {"name": "Identity Management", "priority": "Critical", "confidence": 0.94},
        {"name": "Regulatory Compliance", "priority": "Medium", "confidence": 0.56},
    ],
    "stage": "Technical Validation",
    "behavior_summary": ("searched for: single sign-on okta; okta scim provisioning. "
                         "read documentation and pages about: compliance, sso, "
                         "provisioning, audit, mfa, admin"),
    "alternatives": ["Google Workspace"],
    "constraints": {},
}

BANNED_FRAGMENTS = ["offer ends", "% off", "discount", "thousands of teams",
                    "limited time", "act now before"]


def main() -> int:
    load_dotenv()
    policies = load_policies()
    gateway = AIGateway(policies)
    payload, version, calls = generate_sections(gateway, FACTS, "READY")
    sections = assemble_aar_sections(payload, FACTS, "READY")

    print(f"prompt_version={version} model={gateway.model} calls={calls}\n")
    print(json.dumps(sections, indent=2)[:3000])

    problems = []
    for key in ("executive_summary", "why_we_recommend", "persuasive_narrative",
                "trade_offs", "next_best_actions", "disclaimer"):
        if not sections.get(key):
            problems.append(f"missing/empty section: {key}")
    joined = json.dumps(payload).lower()
    for fragment in BANNED_FRAGMENTS:
        if fragment in joined:
            problems.append(f"banned persuasion fragment present: {fragment!r}")
    for banned_id in ("CAP-", "REQ-", "PROD-"):
        if banned_id in json.dumps(payload):
            problems.append(f"canonical ID leaked into copy: {banned_id}")

    if problems:
        print("\nSMOKE FAIL:")
        for p in problems:
            print(" -", p)
        return 1
    print("\nSMOKE PASS: structured, grounded persuasive AAR generated live.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
