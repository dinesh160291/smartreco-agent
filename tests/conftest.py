"""Shared test fixtures.

Testing contract (CLAUDE.md): tests run against a stubbed gateway — the
embedding backend here is a deterministic bag-of-words stub implementing the
same EmbeddingBackend interface; no network, no model downloads. Fixture
separation: only the canonical 10 products are seeded.
"""

import hashlib
import json
import math

import chromadb
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from smartreco.db import Base
from smartreco.policies import load_policies
from smartreco.seeding import seed_canonical_products, seed_capabilities

DIM = 128


class HashedEmbeddings:
    """Deterministic token-hash embeddings — semantic-lite: documents sharing
    vocabulary (capability names, narratives) land close; unrelated ones don't."""

    def embed(self, texts):
        vectors = []
        for text in texts:
            vec = [0.0] * DIM
            for token in text.lower().split():
                index = int(hashlib.md5(token.encode()).hexdigest(), 16) % DIM
                vec[index] += 1.0
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            vectors.append([v / norm for v in vec])
        return vectors


@pytest.fixture(autouse=True)
def _rate_limiting_off(monkeypatch):
    """Every request from a TestClient shares one caller identity, so the
    per-IP limiter would refuse the legitimate bursts these tests make. Off by
    default here and switched back on, with distinct callers, by the tests that
    exist to exercise it."""
    import apps.web.main as web

    monkeypatch.setattr(web, "RATE_LIMIT_ENABLED", False, raising=False)


@pytest.fixture(scope="session")
def policies():
    return load_policies()


def _make_test_engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def db_engine():
    return _make_test_engine()


@pytest.fixture()
def session_factory(db_engine):
    return sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def chroma():
    client = chromadb.EphemeralClient()
    yield client


@pytest.fixture()
def backend():
    return HashedEmbeddings()


@pytest.fixture()
def seeded(db, chroma, backend):
    """Capability taxonomy + canonical 10 products via the dual-write path."""
    seed_capabilities(db)
    seed_canonical_products(db, chroma, backend)
    return db


class FakeGateway:
    """Stubbed AI Provider Gateway (testing contract): canned, schema-valid
    responses; can be told to return malformed ones — the fallback paths need
    tests too. Same interface as smartreco.gateway.AIGateway."""

    model = "stub-model"
    embed_model = "stub-embed"

    def __init__(self):
        self.calls: list[str] = []
        self.malformed_tier1_remaining = 0
        self.malformed_tier2_remaining = 0
        self.evaluation_verdict = "pass"
        self.missing_aspects: list[str] = []
        self.fail_all = False

    def complete(self, prompt: str, max_tokens: int = 1024) -> str:
        from smartreco.gateway import GatewayUnavailable

        if self.fail_all:
            raise GatewayUnavailable("stub: gateway down")
        self.calls.append(prompt)
        if "### TASK: aar-generate" in prompt:
            if self.malformed_tier1_remaining > 0:
                self.malformed_tier1_remaining -= 1
                return "sorry, here is prose instead of the contract"
            return json.dumps({
                "executive_summary": "Based on your research, one product stands out.",
                "why_we_recommend": "It covers the capabilities your behavior emphasized.",
                "persuasive_narrative": "You kept returning to the areas it is strongest in.",
                "trade_offs": "Gaps listed below remain gaps.",
                "next_best_actions": ["Review the security documentation"],
            })
        if "### TASK: aar-clarify" in prompt:
            if self.malformed_tier1_remaining > 0:
                self.malformed_tier1_remaining -= 1
                return "{not json"
            return json.dumps({
                "executive_summary": "We need a little more signal before recommending.",
                "clarifying_questions": ["What are you evaluating for — your team or yourself?"],
                "next_best_actions": ["Explore a category that matches your needs"],
            })
        if "### TASK: aar-digest" in prompt:
            if self.malformed_tier1_remaining > 0:
                self.malformed_tier1_remaining -= 1
                return "prose, not the contract"
            return json.dumps({
                "recap": "Today you kept returning to security and SSO research.",
                "top_recommendation": "One product keeps standing out for what you value.",
                "next_action": "Review its security documentation",
            })
        if "### TASK: retrieval-evaluate" in prompt:
            if self.malformed_tier2_remaining > 0:
                self.malformed_tier2_remaining -= 1
                return "no json here"
            return json.dumps({"verdict": self.evaluation_verdict,
                               "missing_aspects": self.missing_aspects})
        if "### TASK: retrieval-refine" in prompt:
            if self.malformed_tier2_remaining > 0:
                self.malformed_tier2_remaining -= 1
                return ""
            return "refined query document covering the missing aspects"
        raise AssertionError(f"unexpected prompt: {prompt[:80]}")

    def embed(self, texts):
        raise AssertionError("tests embed via the deterministic backend, not the gateway")


@pytest.fixture()
def fake_gateway():
    return FakeGateway()
