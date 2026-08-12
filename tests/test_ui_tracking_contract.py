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
import pathlib
import re

import pytest
from fastapi.testclient import TestClient

import apps.web.main as web
from smartreco import models
from smartreco.domain.software_buying import CANONICAL_PRODUCTS
from smartreco.domain.software_buying import patterns
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

# Every topic any pattern keys on. Sourced from the pack rather than restated
# here: the union is assembled beside the evaluators, from the same constants
# they read, so it cannot drift from them. Restating it meant this test agreed
# with a list instead of with the code.
RECOGNISED_TOPICS = patterns.PATTERN_TOPICS

ROSTER = [p["product_id"] for p in CANONICAL_PRODUCTS]


def test_the_whole_ui_vocabulary_is_read_by_some_pattern():
    """The reachability ratchet over the *tables*, not just the canonical ten.

    The test below can only see topics the ten fixture products emit, and they
    hold no CRM, HR, finance, marketing, DevOps or analytics capability — so
    every v1.2 topic is invisible to it. Checking the vocabulary itself is the
    only way a topic added for the wide catalog cannot go unread.
    """
    emitted = ({topic for _cap, topic in patterns.UI_DOC_TOPICS}
               | {topic for _cap, topic in patterns.UI_SECURITY_TOPICS}
               | {topic for _cap, topic in patterns.UI_INTEGRATION_TOPICS}
               | {patterns.UI_DOC_TOPIC_DEFAULT,
                  patterns.UI_SECURITY_TOPIC_DEFAULT,
                  patterns.UI_INTEGRATION_TOPIC_DEFAULT})
    unread = sorted(emitted - patterns.PATTERN_TOPICS)
    assert not unread, f"the product page can emit topics no pattern reads: {unread}"


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


def test_app_bar_neutralises_the_base_header_padding(client):
    """ui-design-spec §4.1: the bar is a fixed 56px border-box, so the base
    stylesheet's 20px block padding on <header> must be overridden — it leaves
    a 16px content box and the nav renders below the bar's bottom border.

    Asserted in CSS rather than by measuring a browser because the failure is
    a missing declaration, and a stylesheet regression should fail in CI
    rather than in someone's screenshot."""
    css = (pathlib.Path(web.__file__).parent / "static" / "style.css").read_text(encoding="utf-8")
    appbar = css[css.index(".appbar {"):css.index("}", css.index(".appbar {"))]
    assert "padding: 0" in appbar, (
        "the app bar must zero the base header padding, or its contents "
        f"overflow the 56px bar:\n{appbar}")


def test_compare_picker_is_alphabetical_case_insensitively(client):
    """A 250-entry picker is a lookup. Raw column order is byte order, which
    files 'dbt Cloud' and 'n8n' after 'Zoom Workplace' instead of among the
    d's and n's — technically sorted, useless to a shopper."""
    html = client.get("/compare").text
    options = re.findall(r"<option value=\"PROD-\d+\"[^>]*>([^<]+)</option>", html)
    assert options, "compare picker rendered no options"
    half = len(options) // 2 or len(options)   # the page renders two identical selects
    names = options[:half]
    assert names == sorted(names, key=str.lower), (
        f"picker is not case-insensitively alphabetical: {names[:8]}")


def test_compare_links_back_to_each_product(client):
    """Both compared products link to their own page.

    This is signal integrity, not only convenience. Without the link the way
    back to a product is Explore + typing its name, which emits a SEARCH event
    the shopper never meant — and search tokens feed BP-003/BP-006/BP-007 and
    the query document's recent-activity line. A navigation workaround was
    manufacturing behavioural evidence. Clicking through emits PRODUCT_VIEWED,
    which is what actually happened.
    """
    html = client.get("/compare?a=PROD-003&b=PROD-001").text
    for product_id in ("PROD-003", "PROD-001"):
        assert f'href="/product/{product_id}"' in html, (
            f"compare page offers no way back to {product_id}")


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


def test_tracking_client_starts_a_new_session_when_the_user_changes(client):
    """A session is one person's sitting, but `sessionStorage` is scoped to the
    tab: logging out and in as someone else keeps the previous shopper's id
    alive, which is how one browser tab put two accounts' events on one journey
    (Decision #043).

    The server namespaces by user regardless — that is what enforces isolation,
    and `test_session_user_isolation` pins it. This pins the behavioural half:
    the client must not carry a session across a change of user. Asserted in the
    source because the failure mode is a missing condition, and the page has no
    observable output to measure until two accounts have already been mixed.
    """
    static = pathlib.Path(web.__file__).parent / "static"
    js = (static / "track.js").read_text(encoding="utf-8")
    session_fn = js[js.index("function sessionId()"):js.index("function track(")]

    # The *condition* that mints a new id, not the whole function: asserting on
    # the function body passes as soon as `cfg.user` appears anywhere in it,
    # including in the record it writes — which it does even with the guard
    # deleted. Sabotage caught exactly that.
    guard = session_fn[session_fn.index("if (!s"):session_fn.index("s.last = now")]
    assert "s.user" in guard and "cfg.user" in guard, (
        "the new-session condition does not compare the stored user with the "
        f"current one, so a session survives a logout/login in the tab:\n{guard}")
    assert "user:" in session_fn, "the new session records whose sitting it is"

    html = client.get("/").text
    assert "data-user=" in html, (
        "base.html does not pass the current user to the tracking client, so "
        "the client cannot tell one shopper's sitting from the next")


# Event types no clickable surface can produce, each with the reason it is
# reachable anyway. Anything not listed here must be emitted by a template.
SERVER_EMITTED = {
    "PURCHASE_COMPLETED": "written by the /checkout route after an order is placed",
    "DWELL": "emitted by the track.js heartbeat, not by a click (POL-TRACK-002)",
}


def test_no_registry_event_type_is_unreachable_from_the_product(client):
    """The registry is a promise that the platform can observe these things.

    Three of fourteen types were unreachable when this was written — nothing
    emitted DEMO_REQUESTED or RECOMMENDATION_CLICKED, so a shopper asking to
    talk to sales and a shopper acting on a recommendation both looked like
    ordinary browsing. Patterns keyed on them (BP-011 treats DEMO_REQUESTED as
    a Strong adoption trigger) could never fire in the live product.

    This is the same defect class as the topic bug in `2cb6134`, one level up:
    there the vocabulary was dead, here the event type was. Adding a type to
    the registry now costs a surface that emits it, or an explicit entry in
    SERVER_EMITTED saying why it needs none.
    """
    from apps.web.pages import templates
    from smartreco.domain import active as domain

    pages = ["/", "/?q=single+sign-on", "/?category=Security",
             "/product/PROD-003", "/compare?a=PROD-003&b=PROD-001",
             "/cart", "/for-you"]
    emitted = set()
    for path in pages:
        html = client.get(path).text
        emitted |= set(_tracked_events(html))
        emitted |= set(re.findall(r'"type":\s*"([A-Z_]+)"', html))

    # The recommendation feed only renders entries for a READY package, which
    # this fixture's user does not have. Render the partial directly rather
    # than exempt it — the hook has to survive on a real entry, not merely
    # exist in the file.
    feed = templates.get_template("_feed.html").render(feed={
        "updated": "now", "trigger": "EVENT_ACCUMULATION", "readiness": "READY",
        "sections": {"executive_summary": "s", "persuasive_narrative": "n",
                     "trade_offs": "", "next_best_actions": []},
        "entries": [{"rank": 1, "product_id": "PROD-003", "name": "Okta",
                     "vendor": "Okta", "hue": "#000", "initials": "O",
                     "coverage": 100, "why_covered": [], "why_missing": []}],
    })
    emitted |= set(_tracked_events(feed))

    unreachable = set(domain.EVENT_TYPES) - emitted - set(SERVER_EMITTED)
    assert not unreachable, (
        f"registry event types no surface can emit: {sorted(unreachable)} — "
        f"either wire a surface or record why they are server-emitted")


def test_pricing_tab_does_not_assert_an_intent_the_shopper_has_not_stated(client):
    """Opening the Pricing tab used to emit `tier: "enterprise"`, so every
    shopper who glanced at pricing was recorded as evaluating enterprise.
    BP-002 keys on exactly that value, and BP-002's contradiction branch keys
    on individual/free/personal — which no surface could ever emit, leaving
    half the pattern unreachable and the other half fed by an assumption.

    The tab now records only that pricing was read; the tier comes from the
    plan the shopper actually opens.
    """
    html = client.get("/product/PROD-003").text
    pricing = _tracked_events(html)["PRICING_VIEWED"]

    tab_hooks = [m for m in pricing if "tier" not in m]
    assert len(tab_hooks) == 1, (
        f"expected exactly one tier-less pricing hook (the tab): {pricing}")

    tiers = {m["tier"] for m in pricing if "tier" in m}
    assert tiers == {"personal", "enterprise"}, (
        f"pricing tiers the shopper can choose: {tiers}")


def test_both_pricing_tiers_are_vocabulary_the_patterns_read(client):
    """A tier no pattern reads would be a click that means nothing."""
    html = client.get("/product/PROD-003").text
    tiers = {m["tier"] for m in _tracked_events(html)["PRICING_VIEWED"] if "tier" in m}

    source = pathlib.Path(patterns.__file__).read_text(encoding="utf-8")
    contradicting = set(re.search(
        r'tier"\)\s+in\s+\(([^)]*)\)', source).group(1).replace('"', "").split(", "))

    assert patterns.BP002_ENTERPRISE_TIER in tiers, (
        "no surface emits the tier BP-002 treats as enterprise intent")
    assert tiers & contradicting, (
        f"no surface emits a tier BP-002's contradiction branch reads: {contradicting}")


def test_only_the_security_pane_runs_a_dwell_stopwatch(client):
    """Security Evaluation is the one pattern where reading time substitutes
    for activity, and doc 02 is deliberate about it: its evidence lives on a
    single page per product, so reaching four qualifying events means visiting
    four products. Sixty seconds of reading is the fair alternative.

    Every other pane leaves the topic empty. A dwell topic starts a 10s
    heartbeat writing LOW-signal rows for as long as the pane is open, so on a
    pane no clause reads it is storage bought for nothing.
    """
    html = client.get("/product/PROD-002").text          # Slack — an AI product
    dwell = dict(re.findall(r'data-tab="(\w+)" data-dwell-topic="([^"]*)"', html))

    assert dwell.get("security") == "security", (
        f"the security dwell clause keys on that literal topic: {dwell}")
    for pane in ("pricing", "docs", "integrations", "overview"):
        assert dwell.get(pane) == "", (
            f"the {pane} pane sets dwell topic {dwell.get(pane)!r}, which no "
            f"pattern reads — either add the clause to the Domain Pack or "
            f"leave the stopwatch off")


def test_no_pane_runs_a_stopwatch_no_dwell_clause_reads(client):
    """The rule stated as an invariant rather than two examples.

    Checked across the roster rather than on one page because the Docs pane's
    topic varies per product — it is `ai` on Slack and `sso` on Okta — so a
    single-page check can pass while another product quietly runs a heartbeat
    nothing reads. `DWELL_TOPICS` comes from the Domain Pack: if a pack adds a
    dwell clause, the surfaces follow without an edit here.
    """
    from smartreco.domain import active as domain

    for product_id in ROSTER:
        html = client.get(f"/product/{product_id}").text
        for pane, topic in re.findall(
                r'data-tab="(\w+)" data-dwell-topic="([^"]*)"', html):
            assert topic == "" or topic in domain.DWELL_TOPICS, (
                f"{product_id} {pane} pane runs a dwell heartbeat on "
                f"{topic!r}, which no dwell clause reads")

    # …and the one that does work is still on, so "switch everything off"
    # cannot pass this.
    assert 'data-dwell-topic="security"' in client.get("/product/PROD-003").text, (
        "the security stopwatch — the only specified one — is not running")
