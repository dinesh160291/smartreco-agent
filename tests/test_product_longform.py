"""Signature tests: the deep-dive panes carry enough real copy to read.

Dwell is only a signal if there is something to dwell on. BP-001 and BP-003
escalate to Strong at 60 seconds on a pane's topic, and the panes previously
held roughly a hundred words each — perhaps twenty seconds of reading — so the
dwell branch could never be earned honestly by a shopper who was genuinely
evaluating. Long-form copy is what makes reading time mean something.

Two failure modes are worth pinning, because both are easy to introduce and
invisible once shipped:

* **Boilerplate.** One passage repeated across 250 products would make every
  page's reading time identical and tell the platform nothing.
* **Leakage into the index.** This copy is presentation. If it ever reached
  the Embedding Document it would swamp the capability vocabulary that gives
  retrieval its discrimination (Core 20, Law 8).
"""

import re

import pytest
from fastapi.testclient import TestClient

import apps.web.main as web
from apps.web import content
from smartreco import models
from smartreco.seeding import seed_canonical_products, seed_capabilities
from smartreco.domain.software_buying import CANONICAL_PRODUCTS
from smartreco.retrieval import _CAP_BY_ID, embedding_document

PANES = ("security_sections", "docs_sections", "integrations_sections")

# Two minutes of attentive reading is ~400-500 words; the floor sits well above
# that so a sparse three-capability product still outlasts the 60s dwell bar.
MIN_WORDS = 800


def _view(product):
    return {"name": product["name"], "vendor": product["vendor"],
            "category": product["category"]}


def _sections(pane, product):
    return getattr(content, pane)(_view(product), product["capabilities"])


def _words(sections):
    return sum(len(para.split()) for _heading, paras in sections for para in paras)


@pytest.mark.parametrize("product", CANONICAL_PRODUCTS, ids=lambda p: p["product_id"])
@pytest.mark.parametrize("pane", PANES)
def test_every_pane_is_long_enough_to_be_worth_reading(pane, product):
    """The whole point of the copy: a shopper who reads it spends real time."""
    words = _words(_sections(pane, product))
    assert words >= MIN_WORDS, (
        f"{product['product_id']} {pane}: {words} words — too short to earn "
        f"the 60s dwell that BP-001/BP-003 treat as Strong evidence")


@pytest.mark.parametrize("product", CANONICAL_PRODUCTS, ids=lambda p: p["product_id"])
@pytest.mark.parametrize("pane", PANES)
def test_every_pane_is_anchored_to_this_product(pane, product):
    """Composition, asserted directly rather than by diffing two products —
    comparing a 7-capability product against a 22-capability one makes overlap
    high by construction and measures nothing."""
    text = " ".join(p for _h, ps in _sections(pane, product) for p in ps)
    assert text.count(product["name"]) >= 2, (
        f"{product['product_id']} {pane} barely names the product — the copy "
        f"is scaffolding, not composition")


@pytest.mark.parametrize("pane", PANES)
def test_products_with_different_capabilities_get_different_sections(pane):
    """The sections must track the record. Two products whose capability sets
    barely overlap must not produce the same page."""
    identity = next(p for p in CANONICAL_PRODUCTS if p["product_id"] == "PROD-003")
    automation = next(p for p in CANONICAL_PRODUCTS if p["product_id"] == "PROD-008")
    # Not disjoint — Okta and Zapier both hold CAP-016 Integration Connectors —
    # but different enough that identical section structure would be a bug.
    assert set(identity["capabilities"]) != set(automation["capabilities"])

    identity_headings = [h for h, _ in _sections(pane, identity)]
    automation_headings = [h for h, _ in _sections(pane, automation)]
    assert identity_headings != automation_headings, (
        f"{pane}: two products with disjoint capabilities produced identical "
        f"section structure")


@pytest.mark.parametrize("product", CANONICAL_PRODUCTS, ids=lambda p: p["product_id"])
def test_a_pane_never_presents_a_capability_the_product_lacks(product):
    """Section headings name capabilities, so a heading is an implicit claim
    that the product holds one. Absent capabilities are named only in the
    'Not covered' prose, deliberately and as absences."""
    held = {_CAP_BY_ID[c][0] for c in product["capabilities"] if c in _CAP_BY_ID}
    every_capability = {name for name, _d, _n in _CAP_BY_ID.values()}

    for pane in PANES:
        for heading, _paras in _sections(pane, product):
            if heading in every_capability:
                assert heading in held, (
                    f"{product['product_id']} {pane} has a section for "
                    f"'{heading}', which this product does not hold")


@pytest.mark.parametrize("product", CANONICAL_PRODUCTS, ids=lambda p: p["product_id"])
def test_longform_copy_never_reaches_the_embedding_document(product):
    """Core 20 / Law 8: the index is derived from the product record. Prose in
    a template is not part of that record, and folding ~1,200 words per product
    into the document would dilute the capability terms retrieval ranks on."""
    class _Row:
        product_id = product["product_id"]
        name = product["name"]
        vendor = product["vendor"]
        category = product["category"]
        description = product["description"]
        business_purpose = product["business_purpose"]

    document = embedding_document(_Row, product["capabilities"])

    # Capability narratives are part of the product record and belong in the
    # document by design (Core 20); the panes quote them, which is the point of
    # composing from the record. What must never appear is the surrounding
    # prose — the ~1,200 words of scaffolding written for a human reader.
    narratives = {narrative for _n, _d, narrative in _CAP_BY_ID.values()}

    for pane in PANES:
        for _heading, paras in _sections(pane, product):
            for para in paras:
                if para in narratives:
                    continue
                sentence = re.split(r"(?<=\.)\s+", para)[0]
                assert sentence not in document, (
                    f"long-form copy leaked into the Embedding Document via "
                    f"{pane}: {sentence[:80]}…")


@pytest.fixture()
def client(session_factory, chroma, backend, policies, fake_gateway):
    web._state.clear()
    web._state.update({"policies": policies, "session_factory": session_factory,
                       "chroma": chroma, "backend": backend, "gateway": fake_gateway})
    with session_factory() as db:
        seed_capabilities(db)
        seed_canonical_products(db, chroma, backend)
        db.add(models.User(email="reader@example.com",
                           password_hash=web._hash_password("pw123456"), role="user"))
        db.commit()
    with TestClient(web.app) as c:
        c.post("/auth/login", json={"email": "reader@example.com", "password": "pw123456"})
        yield c
    web._state.clear()


@pytest.mark.parametrize("pane", ["security", "docs", "integrations"])
def test_the_copy_actually_reaches_the_rendered_page(client, pane):
    """The gap every test above left open.

    Composing the sections and *rendering* them are two different things, and
    the tests here passed for a while against a page that showed nothing: the
    view dict had not been given the new keys, so Jinja resolved `p.docs_body`
    to Undefined and the macro looped over it silently, emitting an empty
    pane. A unit test on the composer cannot see that; only the response can.
    """
    html = client.get("/product/PROD-003").text
    # Slice between pane markers rather than matching a closing tag: the panes
    # contain nested divs, and `integrations` is the last one, so a regex
    # anchored on the next pane silently matches nothing.
    start = html.find(f'data-pane="{pane}"')
    assert start != -1, f"no {pane} pane in the rendered product page"
    following = [html.find('data-pane="', start + 1), len(html)]
    body = html[start:min(x for x in following if x != -1)]
    headings = body.count('class="lf-h"')
    assert headings >= 4, (
        f"{pane} pane rendered {headings} headings — the long-form sections "
        f"are not reaching the page")
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    assert words >= MIN_WORDS, f"{pane} pane rendered only {words} words"
