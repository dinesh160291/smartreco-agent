"""SmartReco web app — Phase 1 surface: minimal auth + event ingestion.

POST /events/batch follows Core 22: structural validation, append-only raw
persistence, 202 immediately; behavioral processing is asynchronous (background
task evaluates triggers — never inline reasoning). Jinja2 SSR pages arrive in
Phase 3.
"""

import hashlib
import os
import secrets
from datetime import datetime, timezone

from smartreco.models import utcnow

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from smartreco import models
from smartreco.db import Base, make_engine, make_session_factory
from smartreco.enums import EVENT_TYPES
from smartreco.gateway import AIGateway, GatewayUnavailable
from smartreco.pipeline import run_workflow
from smartreco.policies import load_policies
from smartreco.repos import insert_events_idempotent
from smartreco.retrieval import make_embedding_backend, reconcile_pending
from smartreco.seeding import seed_capabilities

load_dotenv()

app = FastAPI(title="SmartReco")
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "dev-only"))

from pathlib import Path

from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")),
          name="static")

_state: dict = {}


def _init_state():
    """Lazily constructed process state (overridable in tests via app.state)."""
    if _state:
        return _state
    import chromadb

    policies = load_policies()
    engine = make_engine()
    Base.metadata.create_all(engine)
    _state["policies"] = policies
    _state["engine"] = engine
    _state["session_factory"] = make_session_factory(engine)
    _state["chroma"] = chromadb.PersistentClient(
        path=os.environ.get("CHROMA_PATH", "./data/chroma"))
    _state["backend"] = make_embedding_backend(policies)
    try:
        _state["gateway"] = AIGateway(policies)
    except GatewayUnavailable:
        _state["gateway"] = None  # deterministic service continues (Core 21/23)
    with _state["session_factory"]() as db:
        seed_capabilities(db)
        if db.query(models.Product).count() == 0:
            from smartreco.seeding import seed_canonical_products

            seed_canonical_products(db, _state["chroma"], _state["backend"])
        reconcile_pending(db, _state["chroma"], _state["backend"])

    # Real background scheduler — the digest's only initiation path (Core 24).
    from apscheduler.schedulers.background import BackgroundScheduler

    from smartreco.delivery import run_digest_cycle
    from smartreco.models import utcnow as _utcnow

    hour, minute = map(int, str(policies.param(
        "POL-DELIV-002", "daily_time_local")).split(":"))

    def _digest_job():
        with _state["session_factory"]() as job_db:
            records = run_digest_cycle(job_db, _state["chroma"], _state["backend"],
                                       _state.get("gateway"), policies, _utcnow())
            sent = sum(1 for r in records if r.status == "SENT")
            print(f"[digest] window fired: {len(records)} evaluated, {sent} sent")

    scheduler = BackgroundScheduler()
    scheduler.add_job(_digest_job, "cron", hour=hour, minute=minute,
                      id="daily-digest")
    scheduler.start()
    _state["scheduler"] = scheduler
    return _state


def get_state():
    return _init_state()


def get_db(state=Depends(get_state)):
    db = state["session_factory"]()
    try:
        yield db
    finally:
        db.close()


# ---- Auth (minimal: register/login, roles checked at API layer) ----

def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    salt, _digest = stored.split("$", 1)
    return secrets.compare_digest(_hash_password(password, salt), stored)


class Credentials(BaseModel):
    email: str
    password: str


@app.post("/auth/register", status_code=201)
def register(creds: Credentials, request: Request, db=Depends(get_db)):
    if db.query(models.User).filter(models.User.email == creds.email).first():
        raise HTTPException(409, "email already registered")
    user = models.User(email=creds.email, password_hash=_hash_password(creds.password),
                       role="user")
    db.add(user)
    db.commit()
    request.session["user_id"] = user.id
    return {"id": user.id, "email": user.email, "role": user.role}


@app.post("/auth/login")
def login(creds: Credentials, request: Request, db=Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == creds.email).first()
    if user is None or not _verify_password(creds.password, user.password_hash):
        raise HTTPException(401, "invalid credentials")
    request.session["user_id"] = user.id
    return {"id": user.id, "email": user.email, "role": user.role}


def current_user(request: Request, db=Depends(get_db)) -> models.User:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(401, "not authenticated")
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(401, "not authenticated")
    return user


# ---- Event ingestion (Core 22) ----

class EventEnvelope(BaseModel):
    event_id: str
    session_id: str
    event_type: str
    ts: datetime
    metadata: dict = {}


class EventBatch(BaseModel):
    events: list[EventEnvelope]


def _evaluate_triggers_async(user_id: int):
    """Background: trigger evaluator decides whether reasoning runs (never inline)."""
    from smartreco.orchestration import adk_executor

    state = _init_state()
    with state["session_factory"]() as db:
        run_workflow(db, state["chroma"], state["backend"], state["policies"],
                     user_id, "EVENT_ACCUMULATION", gateway=state.get("gateway"),
                     executor=adk_executor)


@app.post("/events/batch", status_code=202)
def ingest_events(batch: EventBatch, background: BackgroundTasks,
                  user: models.User = Depends(current_user),
                  db=Depends(get_db), state=Depends(get_state)):
    max_batch = state["policies"].param("POL-TRACK-001", "server_max_batch")
    if len(batch.events) > max_batch:
        raise HTTPException(422, f"batch exceeds policy maximum ({max_batch})")

    accepted, rejected = [], []
    now = utcnow()
    touched_sessions: dict[str, models.Session] = {}
    for envelope in batch.events:
        if envelope.event_type not in EVENT_TYPES:  # closed registry (Core 22)
            rejected.append({"event_id": envelope.event_id, "reason": "unknown event_type"})
            continue
        ts = envelope.ts
        if ts.tzinfo is not None:
            ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
        accepted.append({
            "event_id": envelope.event_id,
            "user_id": user.id,
            "session_id": envelope.session_id,
            "journey_id": None,  # assigned by Journey Resolution, never by the client
            "event_type": envelope.event_type,
            "signal_class": EVENT_TYPES[envelope.event_type],
            "event_metadata": envelope.metadata,
            "ts": ts,
            "received_at": now,
            "processed_at": None,
        })
        session_row = (touched_sessions.get(envelope.session_id)
                       or db.get(models.Session, envelope.session_id))
        if session_row is None:
            session_row = models.Session(session_id=envelope.session_id, user_id=user.id,
                                         started_at=ts, last_event_at=ts)
            db.add(session_row)
        elif ts > session_row.last_event_at:
            session_row.last_event_at = ts
        touched_sessions[envelope.session_id] = session_row

    inserted = insert_events_idempotent(db, accepted)
    db.commit()
    background.add_task(_evaluate_triggers_async, user.id)
    return {"accepted": len(accepted), "inserted": inserted, "rejected": rejected}


@app.get("/health")
def health():
    return {"status": "ok"}


from apps.web import pages  # noqa: E402  (router needs the helpers above)

app.include_router(pages.router)
