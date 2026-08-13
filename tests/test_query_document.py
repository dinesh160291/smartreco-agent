"""Signature tests: the Behavioral Query Document describes the *need*, not the
shopper (Decision #059).

The document is embedded and matched against product Embedding Documents, which
contain a product's name, vendor, category, description, purpose and
capabilities — and nothing whatever about a shopper's state. Every line of the
query that describes state rather than need is therefore noise competing with
the lines that carry meaning.

Measured on a live index before the change: a DevOps journey's eight retrieved
candidates averaged 60% coverage of the one requirement it had published, two
of them covered 0%, and a Marketing product outranked two products covering
100%. Removing the state lines took the same query to 87.5% mean coverage, five
perfect-coverage products, and no useless ones.
"""

import pytest

from smartreco.retrieval import QUERY_TEMPLATE_VERSION, compose_query_document

REQS = [{"req_id": "REQ-010", "priority": "CRITICAL", "confidence": 0.9}]
NAMES = {"REQ-010": "Engineering Delivery"}
CONCEPTS = ["Engineering Delivery Evaluation", "Pricing Sensitivity",
            "Product Affinity", "Decision Confidence"]


def test_the_need_is_described():
    doc = compose_query_document(REQS, CONCEPTS, "Decision", ["cicd"], NAMES)
    assert "requirement: Engineering Delivery" in doc
    assert "capability: CI/CD Pipelines." in doc
    assert "recent activity: cicd" in doc


def test_the_shoppers_state_is_not():
    """Pricing Sensitivity and Decision Confidence say how someone is buying,
    not what would suit them. No product document contains anything they can
    match against, so they can only dilute the ones that do."""
    doc = compose_query_document(REQS, CONCEPTS, "Decision", ["cicd"], NAMES)
    for state in ("Pricing Sensitivity", "Product Affinity", "Decision Confidence"):
        assert state not in doc, f"{state!r} describes the shopper, not the need"
    assert "interest:" not in doc
    assert "journey stage" not in doc


def test_subject_concepts_are_not_reinstated_by_the_back_door():
    """Even the subject-bearing concepts stay out: the requirement they produced
    is already in the document, so they are at best a restatement. Measured as
    making no difference to retrieval, so the simpler document wins."""
    doc = compose_query_document(REQS, CONCEPTS, "Decision", [], NAMES)
    assert "Engineering Delivery Evaluation" not in doc
    assert "requirement: Engineering Delivery" in doc


def test_the_template_version_is_bookkeeping_and_stays_out_of_the_document():
    """Recorded on the Candidate Set's params, not embedded.

    Embedding the marker cost 20 points of mean coverage on the live index by
    itself — three perfect-coverage products became five, and a useless one
    dropped out, purely by deleting one line of bookkeeping from the text.
    """
    doc = compose_query_document(REQS, CONCEPTS, "Decision", ["cicd"], NAMES)
    assert "query-template" not in doc
    assert QUERY_TEMPLATE_VERSION not in doc
    assert doc.splitlines()[0].startswith("requirement: ")


def test_document_is_deterministic():
    a = compose_query_document(REQS, CONCEPTS, "Decision", ["cicd", "devops"], NAMES)
    b = compose_query_document(REQS, CONCEPTS, "Decision", ["cicd", "devops"], NAMES)
    assert a == b
