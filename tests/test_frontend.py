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


def test_admin_save_rejects_a_category_outside_the_enum(client):
    """Law 7, Decision #083. A mistyped category is not a cosmetic error: it is
    matched against SUBJECT_CATEGORIES, so the product becomes off-subject for
    every shopper, quietly and permanently."""
    _login_admin(client)
    response = client.post("/admin/product/PROD-009", data={
        "name": "Notion", "vendor": "Notion Labs", "category": "Knowledge and Docs",
        "description": "d", "business_purpose": "b", "price_note": "",
        "capabilities": ["CAP-007"]})
    assert response.status_code == 422
    assert "unknown category" in response.text


def test_admin_save_rejects_a_product_no_requirement_can_reach(client):
    """The seed catalog has had this ratchet since #075; an admin could still
    create one by hand. Such a product is searchable, viewable, cartable and
    permanently unrecommendable."""
    _login_admin(client)
    response = client.post("/admin/product/PROD-009", data={
        "name": "Notion", "vendor": "Notion Labs", "category": "Knowledge & Docs",
        "description": "d", "business_purpose": "b", "price_note": "",
        "capabilities": ["CAP-024"]})       # allowlisted as reaching nothing
    assert response.status_code == 422
    assert "never be recommended" in response.text


def test_feed_partial_serves_for_htmx(client):
    _register(client)
    response = client.get("/for-you/feed")
    assert response.status_code == 200


def _render_feed(entries):
    from apps.web.pages import templates

    return templates.get_template("_feed.html").render(feed={
        "readiness": "READY", "label": "Identity", "updated": "just now",
        "trigger": "EVENT_ACCUMULATION",
        "sections": {"executive_summary": "s", "persuasive_narrative": "n",
                     "trade_offs": "", "next_best_actions": []},
        "entries": entries})


def _entry(product_id, name, rank, coverage, on_subject):
    return {"product_id": product_id, "name": name, "vendor": "v",
            "initials": "XX", "hue": "#000", "rank": rank, "coverage": coverage,
            "on_subject": on_subject, "why_covered": ["Single Sign-On"],
            "why_missing": []}


def test_feed_says_why_a_higher_covering_product_ranks_lower():
    """Decision #078 made the list non-monotonic in the figure it prints: an
    off-subject product shows its true coverage and still sits below one that
    covers less. Unexplained, that reads as a broken sort.

    Rendered, not composed. The two fail separately — a view key the template
    never reads produces green unit tests over a blank page.
    """
    html = _render_feed([_entry("PROD-005", "Zoom", 1, 33, True),
                         _entry("PROD-009", "Notion", 2, 49, False)])
    assert html.count("Ranked lower") == 1, "the off-subject entry carries no reason"
    assert "49%" in html and "33%" in html          # true coverage, both shown
    for banned in ("CAP-", "REQ-", "BC-", "BP-"):
        assert banned not in html                   # vocabulary rule (Law 10)


def test_feed_says_nothing_when_every_entry_is_on_subject():
    html = _render_feed([_entry("PROD-005", "Zoom", 1, 33, True)])
    assert "Ranked lower" not in html


def test_the_view_actually_carries_the_key_the_template_reads():
    """The other half. The render tests above hand the template a dict they
    built themselves, so they cannot see `_build_feed` failing to supply the
    key — and Jinja resolves a missing key to Undefined, which is falsy, so
    `not entry.on_subject` would print the caveat on *every* product.
    """
    import inspect

    from apps.web import pages

    source = inspect.getsource(pages._build_feed)
    assert '"on_subject"' in source, (
        "_build_feed no longer supplies on_subject; the feed will caveat every "
        "entry, because Jinja reads a missing key as falsy")


def test_checkout_demo_notice_verbatim(client):
    _register(client)
    client.post("/cart/add/PROD-001", follow_redirects=False)
    body = client.get("/cart").text
    assert "Demo checkout — card details are format-checked only, never stored, and always succeed." in body


def test_for_you_refreshes_when_the_tab_comes_back(client):
    """Decision #084. Browsers throttle timers in background tabs, so the poll
    alone leaves a shopper who returns from another tab looking at a stale panel
    — the "5-minute skew" reported against the admin table, which is polled
    while it is the visible one.
    """
    _register(client)
    body = client.get("/for-you").text
    assert "every 20s" in body                      # the poll still runs
    assert "visibilitychange" in body
    assert "document.visibilityState==='visible'" in body, (
        "unguarded visibilitychange also fires on *hide*, doubling requests")
    assert "from:document" in body, "visibilitychange is fired at document, not the element"


def test_a_search_result_offers_the_way_back(client):
    """Decision #086. A shopper who opens a result had no route back to the list
    they built: the browser Back button covers it only until they open a tab or
    follow a recommendation, and the query was already addressable."""
    listing = client.get("/?q=single+sign-on").text
    assert "?q=single+sign-on" in listing, "product links do not carry the search"

    page = client.get("/product/PROD-003?q=single+sign-on").text
    assert "Back to results" in page
    assert 'href="/?q=single+sign-on"' in page
    assert "single sign-on" in page  # the search is named, so the link is honest


def test_a_product_opened_without_a_search_offers_no_false_return(client):
    """The link must never promise a return to a search that did not happen."""
    page = client.get("/product/PROD-003").text
    assert "Back to results" not in page
    assert '<div class="breadcrumb"><a href="/">Explore</a>' in page


def test_a_stale_product_link_lands_on_a_page_not_a_json_blob(client):
    """Decision #095. A shopper following a dead link was shown the raw API
    contract — `{"detail":"Not Found"}` — with no route back into the catalog.

    Found by running the site: a mistyped product id rendered the JSON body in
    the browser window."""
    response = client.get("/product/PROD-999", headers={"accept": "text/html"})
    assert response.status_code == 404
    body = response.text
    assert "detail" not in body[:200], "still serving the JSON error body to a browser"
    assert "Nothing here" in body
    assert 'href="/"' in body, "no way back into the catalog"
    assert CANONICAL_ID.search(body) is None, (
        "the error page leaks a canonical id onto a shopper surface")


def test_the_json_error_contract_is_unchanged_for_api_callers(client):
    """The page is for browsers only. `/events/batch`, `/auth/*` and the htmx
    partials are API surfaces and must keep the JSON body — the split is decided
    by what the caller says it accepts, which is the only honest signal."""
    api = client.get("/product/PROD-999", headers={"accept": "application/json"})
    assert api.status_code == 404
    assert api.json() == {"detail": "Not Found"}

    # htmx sends Accept: text/html but swaps into a fragment of a live page, so
    # a full document would nest one page inside another.
    htmx = client.get("/product/PROD-999",
                      headers={"accept": "text/html", "hx-request": "true"})
    assert htmx.status_code == 404
    assert htmx.json() == {"detail": "Not Found"}


def test_the_admin_gate_still_refuses_and_now_says_so_in_words(client):
    """403 was the other bare JSON body a shopper could reach by typing a URL.
    The gate itself must not have moved (Law 10)."""
    _register(client)
    response = client.get("/reasoning", headers={"accept": "text/html"})
    assert response.status_code == 403
    assert "Not yours to see" in response.text
    assert "administrators" in response.text


def test_the_digest_preferences_form_persists_all_three_fields(client, session_factory):
    """The opt-in is the gate on proactive delivery (POL-DELIV-001), and until
    now nothing exercised the form that sets it — the delivery stories set the
    column on the model directly. A form that silently failed to opt a shopper
    in would look exactly like a shopper who was never eligible.
    """
    _register(client, "digest@example.com")
    response = client.post("/account", data={"digest_opt_in": "on",
                                             "digest_channel": "TELEGRAM",
                                             "telegram_chat_id": " 12345 "})
    assert response.status_code == 200
    with session_factory() as db:
        user = db.execute(select(models.User).where(
            models.User.email == "digest@example.com")).scalars().one()
        assert user.digest_opt_in is True
        assert user.digest_channel == "TELEGRAM"
        assert user.telegram_chat_id == "12345", "chat id not trimmed"


def test_unticking_the_box_opts_out(client, session_factory):
    """An unchecked checkbox submits nothing at all, so opting *out* depends on
    the absent field meaning False rather than 'leave as it was'."""
    _register(client, "optout@example.com")
    client.post("/account", data={"digest_opt_in": "on",
                                  "digest_channel": "TELEGRAM",
                                  "telegram_chat_id": "12345"})
    client.post("/account", data={"digest_channel": "TELEGRAM",
                                  "telegram_chat_id": "12345"})   # box unticked
    with session_factory() as db:
        user = db.execute(select(models.User).where(
            models.User.email == "optout@example.com")).scalars().one()
        assert user.digest_opt_in is False, "unticking the box left the shopper opted in"


def test_the_saved_form_shows_the_state_it_saved(client):
    """A form that saves correctly but renders unticked teaches the shopper to
    tick it again, which is how a preference gets silently toggled off."""
    _register(client, "render@example.com")
    body = client.post("/account", data={"digest_opt_in": "on",
                                         "digest_channel": "TELEGRAM",
                                         "telegram_chat_id": "12345"}).text
    assert "Preferences saved" in body
    checkbox = body[body.index('name="digest_opt_in"'):][:200]
    assert "checked" in checkbox, "saved opt-in renders as unticked"
    assert 'value="12345"' in body
