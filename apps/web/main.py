"""SmartReco web app — Phase 1 surface: minimal auth + event ingestion.

POST /events/batch follows Core 22: structural validation, append-only raw
persistence, 202 immediately; behavioral processing is asynchronous (background
task evaluates triggers — never inline reasoning). Jinja2 SSR pages arrive in
Phase 3.
"""

import hashlib
import os
import secrets
import threading
from datetime import datetime, timezone

from smartreco.models import utcnow

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import func, select
from starlette.middleware.sessions import SessionMiddleware

from smartreco import models
from smartreco.db import Base, make_engine, make_session_factory
from smartreco.domain import active as domain
from smartreco.gateway import AIGateway, GatewayUnavailable
from smartreco.pipeline import run_workflow
from smartreco.policies import load_policies
from smartreco.repos import insert_events_idempotent
from smartreco.retrieval import (
    get_collection, make_embedding_backend, reconcile_pending)
from smartreco.seeding import seed_capabilities

load_dotenv()

app = FastAPI(title="SmartReco")
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "dev-only"))

from pathlib import Path

from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")),
          name="static")

_state: dict = {}

# One process builds state once. Without the lock the readiness warm-up and a
# first request that arrives beside it both run the constructor, and both seed
# the catalog — on a cold start that is two concurrent embedding passes over
# 250 products against the same Chroma path.
#
# **Reentrant deliberately.** Construction takes this lock and then calls
# `_run_slots`, which takes it again. With a plain Lock that is a deadlock on
# first boot — and an invisible one, because every test injects state and never
# runs the constructor, so the suite stays green while a cold start hangs
# forever.
_state_lock = threading.RLock()

# Liveness and readiness answer different questions, and conflating them is how
# a platform routes live traffic into a warm-up. Measured on a cold start with
# an empty data directory: `/health` answered "ok" immediately while the first
# page request took 3m29s, because state is built lazily and the first request
# pays for the whole catalog embedding.
_readiness: dict = {"ready": False, "detail": "warming up"}


def _init_state():
    """Lazily constructed process state (overridable in tests via app.state)."""
    if _state:
        return _state
    with _state_lock:
        if _state:                      # another thread won the race
            return _state
        return _build_state()


def _build_state():
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
        # Unconditionally, not only on an empty database: the seeders skip
        # every product that already matches, so this costs nothing when the
        # catalog has not moved and picks up edits when it has. Gating on
        # "count() == 0" froze the catalog at first boot (Decision #069).
        from smartreco.seeding import seed_canonical_products, seed_demo_catalog

        seed_canonical_products(db, _state["chroma"], _state["backend"])
        seed_demo_catalog(db, _state["chroma"], _state["backend"])
        reconcile_pending(db, _state["chroma"], _state["backend"])
        _bootstrap_admin(db)

    # Real background scheduler — the digest's only initiation path (Core 24),
    # and the SESSION_END sweep's (Core 23; Decision #047).
    from apscheduler.schedulers.background import BackgroundScheduler

    from smartreco.delivery import run_digest_cycle
    from smartreco.models import utcnow as _utcnow
    from smartreco.pipeline import session_end_sweep

    hour, minute = map(int, str(policies.param(
        "POL-DELIV-002", "daily_time_local")).split(":"))

    def _digest_job():
        with _state["session_factory"]() as job_db:
            records = run_digest_cycle(job_db, _state["chroma"], _state["backend"],
                                       _state.get("gateway"), policies, _utcnow())
            sent = sum(1 for r in records if r.status == "SENT")
            print(f"[digest] window fired: {len(records)} evaluated, {sent} sent")

    def _session_end_job():
        """Event ingestion only ever raises EVENT_ACCUMULATION, so a shopper who
        stops clicking below its threshold is never reasoned about again. This
        is the only path that reaches them."""
        from smartreco.orchestration import adk_executor

        with _state["session_factory"]() as job_db:
            runs = session_end_sweep(job_db, _state["chroma"], _state["backend"],
                                     policies, _utcnow(), gateway=_state.get("gateway"),
                                     executor=adk_executor)
            if runs:
                completed = sum(1 for r in runs if r.status == "COMPLETED")
                print(f"[session-end] {len(runs)} closed session(s), {completed} reasoned")

    scheduler = BackgroundScheduler()
    scheduler.add_job(_digest_job, "cron", hour=hour, minute=minute,
                      id="daily-digest")
    scheduler.add_job(_session_end_job, "interval",
                      minutes=policies.param("POL-TRACK-003", "end_sweep_interval_minutes"),
                      id="session-end-sweep")
    scheduler.start()
    _state["scheduler"] = scheduler

    _run_slots(_state)
    return _state


def _run_slots(state: dict):
    """The instance's reasoning ceiling, created on first use.

    State is injected wholesale in tests and by any embedding caller, so the
    limiter cannot only exist on the path that builds state — reading it
    directly would make "who assembled this dict" decide whether background
    reasoning works. Created under the state lock so two threads arriving at
    once share one semaphore rather than getting a ceiling each.
    """
    slots = state.get("run_slots")
    if slots is None:
        with _state_lock:
            slots = state.get("run_slots")
            if slots is None:
                slots = threading.BoundedSemaphore(
                    state["policies"].param("POL-TRIG-005", "max_concurrent_runs"))
                state["run_slots"] = slots
    return slots


def _warm_up() -> None:
    """Build state off the request path so readiness can report it honestly."""
    try:
        _init_state()
        _readiness.update(ready=True, detail="ready")
    except Exception as exc:                      # stay live, report not-ready
        _readiness.update(ready=False, detail=f"{type(exc).__name__}: {exc}")


@app.on_event("startup")
def _start_warm_up():
    threading.Thread(target=_warm_up, name="smartreco-warmup", daemon=True).start()


def _bootstrap_admin(db) -> None:
    """Demo convenience: create/promote an admin account from environment
    (ADMIN_EMAIL + ADMIN_PASSWORD). No-op when unset."""
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        return
    user = db.query(models.User).filter(models.User.email == admin_email).first()
    if user is None:
        db.add(models.User(email=admin_email,
                           password_hash=_hash_password(admin_password), role="admin"))
    else:
        user.role = "admin"
    db.commit()


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


def _session_key(user_id: int, client_session_id: str) -> str:
    """Namespace the client's session id by the authenticated user (Decision #043).

    The client keeps its id in `sessionStorage`, which is scoped to the tab and
    origin, not to the logged-in user — so a logout/login in the same tab keeps
    sending the previous shopper's id. Trusting it let one session row, and then
    one journey, hold two accounts' events. The client stays free to send
    whatever it likes; identity is decided here, where it is known.
    """
    return f"u{user_id}:{client_session_id}"


def _evaluate_triggers_async(user_id: int):
    """Background: trigger evaluator decides whether reasoning runs (never inline).

    **Shed rather than queue when the instance is already at its ceiling**
    (POL-TRIG-005 `max_concurrent_runs`). Dropping an evaluation costs nothing:
    the events are already durable, and the next flush raises the trigger
    again. Queueing would cost the thread the server needs to render pages,
    which is the failure this prevents — background reasoning nobody is waiting
    on, starving a request somebody is.

    Nothing is recorded for a shed evaluation. A Delivery-Record-style
    "observable silence" would need a journey to attach to, and resolving one
    is the work being declined.
    """
    from smartreco.orchestration import adk_executor

    state = _init_state()
    slots = _run_slots(state)
    if not slots.acquire(blocking=False):
        return
    try:
        with state["session_factory"]() as db:
            run_workflow(db, state["chroma"], state["backend"], state["policies"],
                         user_id, "EVENT_ACCUMULATION", gateway=state.get("gateway"),
                         executor=adk_executor)
    finally:
        slots.release()


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
        if envelope.event_type not in domain.EVENT_TYPES:  # closed registry (Core 22)
            rejected.append({"event_id": envelope.event_id, "reason": "unknown event_type"})
            continue
        ts = envelope.ts
        if ts.tzinfo is not None:
            ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
        session_id = _session_key(user.id, envelope.session_id)
        accepted.append({
            "event_id": envelope.event_id,
            "user_id": user.id,
            "session_id": session_id,
            "journey_id": None,  # assigned by Journey Resolution, never by the client
            "event_type": envelope.event_type,
            "signal_class": domain.EVENT_TYPES[envelope.event_type],
            "event_metadata": envelope.metadata,
            "ts": ts,
            "received_at": now,
            "processed_at": None,
        })
        session_row = (touched_sessions.get(session_id)
                       or db.get(models.Session, session_id))
        if session_row is None:
            session_row = models.Session(session_id=session_id, user_id=user.id,
                                         started_at=ts, last_event_at=ts)
            db.add(session_row)
        elif ts > session_row.last_event_at:
            session_row.last_event_at = ts
        touched_sessions[session_id] = session_row

    inserted = insert_events_idempotent(db, accepted)
    db.commit()
    background.add_task(_evaluate_triggers_async, user.id)
    return {"accepted": len(accepted), "inserted": inserted, "rejected": rejected}


@app.get("/health")
def health():
    """Liveness: is this process alive. Deliberately does no work — a liveness
    probe that touches the database or the index is a way to have a busy
    instance restarted for being busy."""
    return {"status": "ok"}


@app.get("/ready")
def ready(response: Response):
    """Readiness: can this process actually serve a request.

    Point the platform's health check here, not at `/health`. State is built
    off the request path, and on a cold start that means embedding the whole
    catalog — measured at 3m29s. For that window the process is alive and
    cannot serve anything, and only this endpoint says so.

    The catalog and index counts are checked rather than assumed: a process
    that came up against an empty volume is running, not ready.
    """
    if not _readiness["ready"]:
        response.status_code = 503
        return {"ready": False, "detail": _readiness["detail"]}
    try:
        with _state["session_factory"]() as db:
            catalog = db.execute(select(func.count()).select_from(models.Product)).scalar()
        index = get_collection(_state["chroma"]).count()
    except Exception as exc:
        response.status_code = 503
        return {"ready": False, "detail": f"{type(exc).__name__}: {exc}"}
    if not catalog or not index:
        response.status_code = 503
        return {"ready": False, "detail": "catalog or index empty",
                "catalog": catalog, "index": index}
    return {"ready": True, "detail": "ready", "catalog": catalog, "index": index,
            "policy_version": _state["policies"].version}


from apps.web import pages  # noqa: E402  (router needs the helpers above)

app.include_router(pages.router)


@app.exception_handler(StarletteHTTPException)
def _http_error(request: Request, exc: StarletteHTTPException):
    """Render errors as a page for browser navigations, as JSON for everything else.

    A shopper who follows a stale product link was shown a bare
    `{"detail":"Not Found"}` — the raw API contract leaking onto a shopper-facing
    surface, with no way back into the catalog. The JSON body is the right answer
    for `/events/batch`, `/auth/*` and the htmx partials, so the two are told
    apart the only way they honestly can be: by what the caller says it accepts.

    `hx-request` is checked too. htmx sends `Accept: text/html`, but it swaps the
    response into a fragment of an existing page, so handing it a full document
    would nest one page inside another.
    """
    wants_html = ("text/html" in request.headers.get("accept", "")
                  and request.headers.get("hx-request") != "true")
    if not wants_html:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    headings = {403: "Not yours to see", 404: "Nothing here"}
    details = {
        403: "That page is for administrators.",
        404: "That product or page does not exist — it may have been removed.",
    }
    state = _init_state()
    with state["session_factory"]() as db:
        ctx = pages._base_ctx(request, db, pages._optional_user(request, db),
                              state, None)
    ctx.update({"status": exc.status_code,
                "heading": headings.get(exc.status_code, "Something went wrong"),
                "detail": details.get(exc.status_code, str(exc.detail))})
    return pages.templates.TemplateResponse(request, "error.html", ctx,
                                            status_code=exc.status_code)
