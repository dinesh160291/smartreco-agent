"""Signature test: the UI→pattern seam.

The acceptance stories hand-craft event metadata and never render a template,
so nothing pinned that the metadata the *product page* actually emits is the
metadata the Behavioral Reasoning Engine looks for. It wasn't: the Security tab
sent no `topic` and the Docs tab hardcoded `topic: "api"`, so BP-001 (Security
Evaluation) and BP-002 (Enterprise Evaluation) could never activate from a
browser session — and therefore REQ-002 could never be inferred and no shopper
could ever reach a READY recommendation through the UI.

Pins: a shopper who opens an identity product's Security, Docs and Pricing tabs
produces evidence for BP-001 and BP-002 (Domain Pack doc 02), which is what
Story 1 requires.
"""

import json
import re

import pytest
from fastapi.testclient import TestClient

import apps.web.main as web
from smartreco import models
from smartreco.domain.software_buying import CANONICAL_PRODUCTS
from smartreco.engines import patterns
from smartreco.engines.patterns import EventView, evaluate_patterns
from smartreco.policies import load_policies
from smartreco.seeding import seed_canonical_products, seed_capabilities

TRACKED = re.compile(
    r'data-track="([A-Z_]+)"\s+data-track-meta=\'([^\']*)\'')


@pytest.fixture()
def client(session_factory, chroma, backend, policies, fake_gateway):
    web._state.clear()
    web._state.update({
        "policies": policies, "session_factory": session_factory,
        "chroma": chroma, "backend": backend, "gateway": fake_gateway,
    })
    with session_factory() as db:
        seed_capabilities(db)
        seed_canonical_products(db, chroma, backend)
        db.add(models.User(email="s@example.com",
                           password_hash=web._hash_password("pw123456"), role="user"))
        db.commit()
    with TestClient(web.app) as c:
        c.post("/auth/login", json={"email": "s@example.com", "password": "pw123456"})
        yield c
    web._state.clear()


def _tracked_events(html: str) -> dict[str, dict]:
    """Every data-track hook on the page, keyed by the label it sits on."""
    found = {}
    for event_type, raw in TRACKED.findall(html):
        found.setdefault(event_type, []).append(json.loads(raw))
    return found


def test_product_page_tabs_emit_pattern_recognised_metadata(client, policies):
    """Okta's tabs must produce metadata BP-001 and BP-002 can act on."""
    html = client.get("/product/PROD-003").text
    tracked = _tracked_events(html)

    security = tracked["SECURITY_VIEWED"][0]
    docs = tracked["DOCUMENTATION_VIEWED"]
    pricing = tracked["PRICING_VIEWED"][0]

    # Replay the tabs as a shopper session and ask the BRE what it sees.
    views = [EventView(event_id="e1", event_type="PRODUCT_VIEWED", session_id="s1",
                       metadata={"product_id": "PROD-003"}),
             EventView(event_id="e2", event_type="SECURITY_VIEWED", session_id="s1",
                       metadata=security),
             EventView(event_id="e3", event_type="PRICING_VIEWED", session_id="s1",
                       metadata=pricing)]
    views += [EventView(event_id=f"e{4 + i}", event_type="DOCUMENTATION_VIEWED",
                        session_id="s1", metadata=meta)
              for i, meta in enumerate(docs)]

    fired = {draft.pattern_id for draft in evaluate_patterns(views, policies)}

    assert "BP-001" in fired, (
        f"Security Evaluation unreachable from the product page. "
        f"security={security} docs={docs}")
    assert "BP-002" in fired, (
        f"Enterprise Evaluation unreachable from the product page. "
        f"security={security} docs={docs} pricing={pricing}")


def test_security_tab_declares_a_topic(client):
    """BP-002 keys on SECURITY_VIEWED topic in {compliance, audit}; a security
    view with no topic can never contribute to Enterprise Evaluation."""
    html = client.get("/product/PROD-003").text
    security = _tracked_events(html)["SECURITY_VIEWED"][0]
    assert security.get("topic") in {"compliance", "audit"}, security


def test_docs_topics_match_the_products_own_capabilities(client):
    """The tracked topic must describe what the pane actually documents, so an
    identity product's docs read as identity docs — not a hardcoded 'api'."""
    identity_docs = _tracked_events(client.get("/product/PROD-003").text)
    topics = {meta.get("topic") for meta in identity_docs["DOCUMENTATION_VIEWED"]}
    assert topics & {"sso", "mfa"}, f"no identity doc topic emitted: {topics}"
    assert topics & {"provisioning", "federation", "admin"}, (
        f"no enterprise doc topic emitted: {topics}")


# --- Whole-vocabulary invariants ---------------------------------------------

# Every topic any pattern keys on (patterns.py). The inline literals are the
# ones written directly into an evaluator rather than a module constant.
RECOGNISED_TOPICS = (
    patterns.BP001_DOC_TOPICS | patterns.BP002_DOC_TOPICS
    | patterns.BP002_SECURITY_TOPICS | patterns.BP004_DOC_TOPICS
    | patterns.BP005_DOC_TOPICS | patterns.BP006_DOC_TOPICS
    | patterns.BP007_DOC_TOPICS | patterns.BP008_DOC_TOPICS
    | {"ai", "security", "certifications", "onboarding", "migration"}
)

ROSTER = [p["product_id"] for p in CANONICAL_PRODUCTS]


def test_no_ui_topic_is_dead_vocabulary(client):
    """The invariant that would have caught the original bug: every topic the
    product page can emit, for every product in the roster, must be a topic
    some pattern actually reads. A topic nothing recognises is a silent hole —
    the events are recorded, look healthy, and reason about nothing."""
    emitted: dict[str, set[str]] = {}
    for product_id in ROSTER:
        tracked = _tracked_events(client.get(f"/product/{product_id}").text)
        for event_type in ("DOCUMENTATION_VIEWED", "SECURITY_VIEWED"):
            for meta in tracked.get(event_type, []):
                if meta.get("topic"):
                    emitted.setdefault(meta["topic"], set()).add(product_id)

    dead = {topic: sorted(pids) for topic, pids in emitted.items()
            if topic not in RECOGNISED_TOPICS}
    assert not dead, f"topics no pattern reads: {dead}"
    assert len(emitted) >= 6, f"vocabulary suspiciously narrow: {sorted(emitted)}"


def test_compliance_posture_is_reachable_across_governance_products(client):
    """BP-004 Compliance Evaluation needs 2 qualifying signals (Domain Pack
    doc 02). Comparing the compliance posture of two governance products in one
    session is exactly that behaviour, and must activate it."""
    governance = ["PROD-001", "PROD-010"]  # both carry CAP-012/CAP-013
    views = []
    for i, product_id in enumerate(governance):
        tracked = _tracked_events(client.get(f"/product/{product_id}").text)
        views.append(EventView(event_id=f"s{i}", event_type="SECURITY_VIEWED",
                               session_id="s1",
                               metadata=tracked["SECURITY_VIEWED"][0]))

    fired = {d.pattern_id for d in evaluate_patterns(views, load_policies())}
    assert "BP-004" in fired, (
        "Compliance Evaluation unreachable from the browser; security topics="
        f"{[v.metadata.get('topic') for v in views]}")


def test_explore_reports_how_many_products_matched(client):
    """ui-design-spec §4.7a: the count tells a shopper whether a search
    narrowed anything, and distinguishes 'no matches' from a broken page."""
    unfiltered = client.get("/").text
    assert "10 products" in unfiltered           # canonical fixture size

    narrowed = client.get("/?q=single+sign-on").text
    assert "of 10 products" in narrowed
    assert "single sign-on" in narrowed

    empty = client.get("/?q=nonexistent-capability-xyz").text
    assert "0 of 10 products" in empty
    assert "No products match" in empty


def test_identity_product_does_not_masquerade_as_compliance_research(client):
    """The counterpart: Okta carries no governance capability, so reading its
    pages is identity research, not compliance evaluation. Topics must not be
    widened until every pattern fires for every product."""
    tracked = _tracked_events(client.get("/product/PROD-003").text)
    views = [EventView(event_id="s1", event_type="SECURITY_VIEWED", session_id="s1",
                       metadata=tracked["SECURITY_VIEWED"][0])]
    views += [EventView(event_id=f"d{i}", event_type="DOCUMENTATION_VIEWED",
                        session_id="s1", metadata=meta)
              for i, meta in enumerate(tracked["DOCUMENTATION_VIEWED"])]

    fired = {d.pattern_id for d in evaluate_patterns(views, load_policies())}
    assert "BP-004" not in fired, "identity browsing wrongly reads as compliance"
    assert "BP-001" in fired
