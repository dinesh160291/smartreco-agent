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
from smartreco.engines.patterns import EventView, evaluate_patterns
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
