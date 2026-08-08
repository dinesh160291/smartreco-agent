"""Shared test fixtures.

Testing contract (CLAUDE.md): tests run against a stubbed gateway — the
embedding backend here is a deterministic bag-of-words stub implementing the
same EmbeddingBackend interface; no network, no model downloads. Fixture
separation: only the canonical 10 products are seeded.
"""

import hashlib
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
