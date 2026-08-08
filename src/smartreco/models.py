"""SQLAlchemy models — one-to-one transcription of docs/implementation/data-model.md.

Immutability (D2) is enforced in the repository layer, not here: runtime-object
tables get insert-only helpers and no UPDATE path. Mutable state is exactly:
users, products (+sync), cart_items, sessions, journeys (lifecycle),
behavioral_traits. Categorical columns are TEXT holding closed-enum values
(docs/core/17); the API layer validates them.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from smartreco.db import Base


def utcnow() -> datetime:
    """Naive UTC — SQLite stores naive datetimes; the platform is UTC throughout."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---- Identity & Catalog (mutable) ----


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, default="user")  # user | admin
    digest_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    digest_channel: Mapped[str | None] = mapped_column(Text, nullable=True)  # EMAIL | TELEGRAM
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Capability(Base):
    """Seeded taxonomy — read-only at runtime (Domain 10 Capability Catalog)."""

    __tablename__ = "capabilities"

    capability_id: Mapped[str] = mapped_column(Text, primary_key=True)  # CAP-xxx
    name: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(Text, nullable=False)
    business_value_narrative: Mapped[str] = mapped_column(Text, default="")


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(Text, primary_key=True)  # PROD-xxx
    name: Mapped[str] = mapped_column(Text, nullable=False)
    vendor: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    business_purpose: Mapped[str] = mapped_column(Text, default="")
    business_value_narrative: Mapped[str] = mapped_column(Text, default="")
    price_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    record_version: Mapped[int] = mapped_column(Integer, default=1)
    sync_status: Mapped[str] = mapped_column(Text, default="PENDING")  # PENDING | SYNCED | FAILED
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow)


class ProductCapability(Base):
    __tablename__ = "product_capabilities"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), primary_key=True)
    capability_id: Mapped[str] = mapped_column(
        ForeignKey("capabilities.capability_id"), primary_key=True
    )


class CartItem(Base):
    __tablename__ = "cart_items"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(default=utcnow)


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    journey_id: Mapped[str | None] = mapped_column(ForeignKey("journeys.journey_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class OrderItem(Base):
    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), primary_key=True)
    price_note: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---- Behavioral Spine (append-only) ----


class Event(Base):
    """Immutable behavioral system of record. Only journey_id assignment and
    processed_at stamping are permitted updates (data-model: events)."""

    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(Text, primary_key=True)  # client UUID → idempotency
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[str] = mapped_column(Text)
    journey_id: Mapped[str | None] = mapped_column(ForeignKey("journeys.journey_id"), nullable=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    signal_class: Mapped[str] = mapped_column(Text, nullable=False)  # HIGH | MEDIUM | LOW
    event_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    ts: Mapped[datetime] = mapped_column(nullable=False)  # client event time
    received_at: Mapped[datetime] = mapped_column(default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    journey_id: Mapped[str | None] = mapped_column(ForeignKey("journeys.journey_id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    last_event_at: Mapped[datetime] = mapped_column(default=utcnow)


class Journey(Base):
    __tablename__ = "journeys"

    journey_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    lifecycle: Mapped[str] = mapped_column(Text, default="NEW")  # NEW/ACTIVE/DORMANT/CLOSED/ARCHIVED
    context: Mapped[str] = mapped_column(Text, default="")
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)


class JourneyTransition(Base):
    __tablename__ = "journey_transitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.journey_id"))
    from_state: Mapped[str] = mapped_column(Text)
    to_state: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text, default="")
    policy_version: Mapped[str] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(default=utcnow)


class Evidence(Base):
    __tablename__ = "evidence"

    evidence_id: Mapped[str] = mapped_column(Text, primary_key=True)  # BE-…
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.journey_id"))
    pattern_id: Mapped[str] = mapped_column(Text)  # BP-xxx
    strength: Mapped[str] = mapped_column(Text)  # Weak/Medium/Strong/Very Strong
    supporting_event_ids: Mapped[list] = mapped_column(JSON, default=list)
    concept_ids: Mapped[list] = mapped_column(JSON, default=list)  # BC-xxx
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Hypothesis(Base):
    __tablename__ = "hypotheses"

    hypothesis_id: Mapped[str] = mapped_column(Text, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)  # current = MAX(version)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.journey_id"))
    concept_id: Mapped[str] = mapped_column(Text)  # BC-xxx
    status: Mapped[str] = mapped_column(Text)  # Created/Strengthened/Stable/Weakened/Retired
    confidence: Mapped[float] = mapped_column(Float)  # written only by the Confidence Engine
    confidence_explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class HypothesisEvidence(Base):
    __tablename__ = "hypothesis_evidence"

    hypothesis_id: Mapped[str] = mapped_column(Text, primary_key=True)
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("evidence.evidence_id"), primary_key=True
    )
    relation: Mapped[str] = mapped_column(Text, default="SUPPORTING")  # SUPPORTING | CONTRADICTING


class AIUsage(Base):
    """Per-user per-day AI call counters (POL-TRIG-003 budgets). Mutable by
    design — a counter, not a Runtime Object (data-model §ai_usage)."""

    __tablename__ = "ai_usage"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    day: Mapped[str] = mapped_column(Text, primary_key=True)  # YYYY-MM-DD (UTC)
    tier: Mapped[str] = mapped_column(Text, primary_key=True)  # tier1 | tier2
    calls: Mapped[int] = mapped_column(Integer, default=0)


class BehavioralTrait(Base):
    """Mutable long-term profile — written only by Learning and Decay engines."""

    __tablename__ = "behavioral_traits"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    trait_name: Mapped[str] = mapped_column(Text, primary_key=True)
    strength: Mapped[float] = mapped_column(Float)
    reinforcement_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reinforced: Mapped[datetime] = mapped_column(default=utcnow)
    decay_explanation: Mapped[str] = mapped_column(Text, default="")


# ---- Decision Spine (immutable, versioned Runtime Objects — JSON snapshots) ----


class RequirementProfile(Base):
    __tablename__ = "requirement_profiles"

    rp_id: Mapped[str] = mapped_column(Text, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.journey_id"))
    version: Mapped[int] = mapped_column(Integer)
    requirements: Mapped[list] = mapped_column(JSON)  # [{req_id, confidence, priority, explanation}]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class JourneyStage(Base):
    __tablename__ = "journey_stages"

    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.journey_id"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    stage: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class CandidateSet(Base):
    __tablename__ = "candidate_sets"

    cs_id: Mapped[str] = mapped_column(Text, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.journey_id"))
    rp_id: Mapped[str] = mapped_column(ForeignKey("requirement_profiles.rp_id"))
    query_document: Mapped[str] = mapped_column(Text)
    params: Mapped[dict] = mapped_column(JSON)  # {top_k, embed_model, index_version}
    candidates: Mapped[list] = mapped_column(JSON)  # [{product_id, similarity, record_version}]
    refinement_history: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class RecommendationPackage(Base):
    __tablename__ = "recommendation_packages"

    rpkg_id: Mapped[str] = mapped_column(Text, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.journey_id"))
    rp_id: Mapped[str] = mapped_column(ForeignKey("requirement_profiles.rp_id"))
    cs_id: Mapped[str | None] = mapped_column(ForeignKey("candidate_sets.cs_id"), nullable=True)
    entries: Mapped[list] = mapped_column(JSON)
    readiness: Mapped[str] = mapped_column(Text)  # READY | NOT_READY
    constraints: Mapped[dict] = mapped_column(JSON, default=dict)
    policy_version: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class AdvisoryResponse(Base):
    __tablename__ = "advisory_responses"
    __table_args__ = (
        UniqueConstraint("rpkg_id", "prompt_version", "surface", name="uq_aar_cache_key"),
    )

    aar_id: Mapped[str] = mapped_column(Text, primary_key=True)
    rpkg_id: Mapped[str] = mapped_column(ForeignKey("recommendation_packages.rpkg_id"))
    surface: Mapped[str] = mapped_column(Text)  # ONSITE | DIGEST
    prompt_version: Mapped[str] = mapped_column(Text)
    model_id: Mapped[str] = mapped_column(Text, default="")
    sections: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class DeliveryRecord(Base):
    __tablename__ = "delivery_records"
    __table_args__ = (
        UniqueConstraint("user_id", "digest_window", name="uq_delivery_idempotency"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    channel: Mapped[str] = mapped_column(Text)
    aar_id: Mapped[str | None] = mapped_column(ForeignKey("advisory_responses.aar_id"), nullable=True)
    status: Mapped[str] = mapped_column(Text)  # SENT | FAILED | SKIPPED
    reason: Mapped[str] = mapped_column(Text, default="")
    digest_window: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class WorkflowRun(Base):
    """Observability; powers the Reasoning Panel. Every run — including the
    decision NOT to run (status SKIPPED) — writes one row."""

    __tablename__ = "workflow_runs"

    run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    journey_id: Mapped[str | None] = mapped_column(ForeignKey("journeys.journey_id"), nullable=True)
    trigger_type: Mapped[str] = mapped_column(Text)
    gates: Mapped[dict] = mapped_column(JSON, default=dict)
    nodes: Mapped[list] = mapped_column(JSON, default=list)
    policy_version: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
