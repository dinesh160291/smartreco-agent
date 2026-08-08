"""Signature tests: Phase 3 frontend.

Pins: shopper pages render; the vocabulary rule (no canonical IDs on shopper
surfaces — ui-design-spec §6.1); checkout demo flow emits PURCHASE_COMPLETED
through the standard pipeline and stores no card data; admin/Reasoning are
role-gated; htmx partials serve."""

import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import apps.web.main as web
from smartreco import models
from smartreco.seeding import seed_canonical_products, seed_capabilities

CANONICAL_ID = re.compile(r"\b(CAP|REQ|PROD|BC|BP)-\d")


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
        db.add(models.User(email="admin@example.com",
                           password_hash=web._hash_password("adminpw"), role="admin"))
        db.commit()
    with TestClient(web.app) as c:
        yield c
    web._state.clear()


def _register(client, email="shopper@example.com"):
    response = client.post("/auth/register", json={"email": email, "password": "pw123456"})
    assert response.status_code == 201
    return response.json()


def _login_admin(client):
    response = client.post("/auth/login",
                           json={"email": "admin@example.com", "password": "adminpw"})
    assert response.status_code == 200


SHOPPER_PATHS = ["/", "/?q=single+sign-on", "/product/PROD-003", "/compare?a=PROD-003&b=PROD-001"]


def test_shopper_pages_render_without_canonical_ids(client):
    _register(client)
    for path in SHOPPER_PATHS + ["/for-you", "/cart"]:
        response = client.get(path)
        assert response.status_code == 200, path
        # Vocabulary rule: strip attributes/scripts (IDs ride in URLs and
        # tracking metadata by design); no canonical ID may appear as TEXT.
        text_only = re.sub(r"<script[\s\S]*?</script>", "", response.text)
        text_only = re.sub(r"<[^>]+>", "", text_only)
        assert not CANONICAL_ID.search(text_only), f"canonical ID visible on {path}"


def test_product_page_has_five_tabs_and_tracking_hooks(client):
    response = client.get("/product/PROD-003")
    body = response.text
    for tab in ["Overview", "Pricing", "Security &amp; Compliance", "Docs &amp; API", "Integrations"]:
        assert tab in body
    for event in ["SECURITY_VIEWED", "PRICING_VIEWED", "DOCUMENTATION_VIEWED",
                  "ADD_TO_CART", "TRIAL_STARTED", "COMPARISON_STARTED"]:
        assert event in body  # data-track hooks — the frontend is the signal generator


def test_checkout_emits_purchase_completed_and_stores_no_card(client, session_factory):
    _register(client)
    assert client.post("/cart/add/PROD-003", follow_redirects=False).status_code == 303
    response = client.post("/checkout", data={
        "card_name": "Demo User", "card_number": "4242 4242 4242 4242",
        "card_expiry": "12/28", "card_cvc": "123"})
    assert response.status_code == 200
    assert "Order confirmed" in response.text

    with session_factory() as db:
        orders = db.execute(select(models.Order)).scalars().all()
        assert len(orders) == 1
        purchase_events = db.execute(select(models.Event).where(
            models.Event.event_type == "PURCHASE_COMPLETED")).scalars().all()
        assert len(purchase_events) == 1
        # No card fields exist anywhere in the schema — spot-check the order rows
        assert not any(hasattr(orders[0], col) for col in
                       ("card_number", "card_name", "card_cvc", "card_expiry"))


def test_checkout_rejects_malformed_card_format(client):
    _register(client)
    client.post("/cart/add/PROD-003", follow_redirects=False)
    response = client.post("/checkout", data={
        "card_name": "Demo", "card_number": "not-a-card",
        "card_expiry": "12/28", "card_cvc": "123"})
    assert response.status_code == 422


def test_admin_and_reasoning_are_role_gated(client):
    _register(client)  # plain shopper
    assert client.get("/admin").status_code == 403
    assert client.get("/reasoning").status_code == 403


def test_admin_pages_render_for_admin(client):
    _login_admin(client)
    admin = client.get("/admin")
    assert admin.status_code == 200 and "SYNCED" in admin.text
    table = client.get("/admin/table")
    assert table.status_code == 200 and "PROD-003" in table.text  # IDs allowed here
    reasoning = client.get("/reasoning")
    assert reasoning.status_code == 200 and "Internal · admin only" in reasoning.text


def test_admin_save_validates_capability_ids(client, session_factory):
    _login_admin(client)
    response = client.post("/admin/product/PROD-009", data={
        "name": "Notion", "vendor": "Notion Labs", "category": "Knowledge & Docs",
        "description": "d", "business_purpose": "b", "price_note": "",
        "capabilities": ["CAP-999"]})
    assert response.status_code == 422  # unknown IDs rejected (Core 14)


def test_feed_partial_serves_for_htmx(client):
    _register(client)
    response = client.get("/for-you/feed")
    assert response.status_code == 200


def test_checkout_demo_notice_verbatim(client):
    _register(client)
    client.post("/cart/add/PROD-001", follow_redirects=False)
    body = client.get("/cart").text
    assert "Demo checkout — card details are format-checked only, never stored, and always succeed." in body
