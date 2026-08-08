"""SSR pages — Jinja2 templates per docs/implementation/ui-design-spec.md.

The frontend is the signal generator (stack-decisions): page loads and tab
clicks emit the event types the Behavioral Patterns activate on, through the
tracking client. Canonical IDs never reach shopper surfaces (vocabulary rule);
they appear only on Admin and the Reasoning Panel.
"""

import hashlib
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from smartreco import models
from smartreco.domain.software_buying import BC_TO_REQ, BEHAVIORAL_CONCEPTS, REQUIREMENTS
from smartreco.enums import JOURNEY_STAGES
from smartreco.models import utcnow
from smartreco.repos import insert_events_idempotent
from smartreco.retrieval import _CAP_BY_ID, save_product

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Preview-reference hues (ui-design-spec §4.3); other vendors hash deterministically.
_REFERENCE_HUES = {"okta": 210, "microsoft": 16, "google": 135, "servicenow": 160,
                   "slack": 280, "salesforce": 280, "zapier": 25, "box": 220, "zoom": 200,
                   "atlassian": 45}


def monogram(name: str, vendor: str) -> tuple[str, str]:
    initials = "".join(w[0] for w in name.split()[:2]).upper()
    key = vendor.lower().split()[0] if vendor else name.lower()
    if key in ("notion", "notion labs"):
        return initials, "hsl(0 0% 25%)"
    hue = _REFERENCE_HUES.get(
        key, int(hashlib.md5(key.encode()).hexdigest(), 16) % 360)
    return initials, f"hsl({hue} 45% 42%)"


def _product_view(p: models.Product, cap_count: int | None = None) -> dict:
    initials, hue = monogram(p.name, p.vendor)
    return {"product_id": p.product_id, "name": p.name, "vendor": p.vendor,
            "category": p.category, "description": p.description,
            "business_purpose": p.business_purpose, "price_note": p.price_note,
            "initials": initials, "hue": hue, "cap_count": cap_count or 0}


def _base_ctx(request: Request, db, user, state, active_nav, page_events=None,
              dwell_topic=None) -> dict:
    cart_count = 0
    if user:
        cart_count = len(db.execute(select(models.CartItem).where(
            models.CartItem.user_id == user.id)).scalars().all())
    track = state["policies"].get("POL-TRACK-001").params | \
        state["policies"].get("POL-TRACK-002").params | \
        state["policies"].get("POL-TRACK-003").params
    return {"request": request, "user": user, "cart_count": cart_count,
            "active_nav": active_nav, "tracking": track,
            "page_events": page_events or [], "dwell_topic": dwell_topic}


def _optional_user(request: Request, db) -> models.User | None:
    user_id = request.session.get("user_id")
    return db.get(models.User, user_id) if user_id else None


def _require_admin(user: models.User | None):
    if user is None or user.role != "admin":
        raise HTTPException(403, "admin only")


def _caps_of(db, product_id: str) -> list[str]:
    return db.execute(select(models.ProductCapability.capability_id).where(
        models.ProductCapability.product_id == product_id)).scalars().all()


# ---- Auth pages ----

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "auth.html", {
        "request": request, "mode": "login", "user": None, "cart_count": 0,
        "active_nav": None, "tracking": _no_tracking(), "page_events": [],
        "dwell_topic": None})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "auth.html", {
        "request": request, "mode": "register", "user": None, "cart_count": 0,
        "active_nav": None, "tracking": _no_tracking(), "page_events": [],
        "dwell_topic": None})


def _no_tracking() -> dict:
    return {"batch_size": 10, "flush_interval_seconds": 15, "heartbeat_seconds": 10,
            "inactivity_minutes": 30, "max_flush_retries": 3}


def _auth_form(request, db, mode, email, password):
    from apps.web.main import _hash_password, _verify_password

    if mode == "register":
        if db.query(models.User).filter(models.User.email == email).first():
            return None, "Email already registered"
        user = models.User(email=email, password_hash=_hash_password(password), role="user")
        db.add(user)
        db.commit()
    else:
        user = db.query(models.User).filter(models.User.email == email).first()
        if user is None or not _verify_password(password, user.password_hash):
            return None, "Invalid credentials"
    request.session["user_id"] = user.id
    return user, None


def _db(request: Request):
    from apps.web.main import _init_state

    state = _init_state()
    db = state["session_factory"]()
    try:
        yield state, db
    finally:
        db.close()


@router.post("/login")
def login_form(request: Request, email: str = Form(...), password: str = Form(...),
               sd=Depends(_db)):
    state, db = sd
    user, error = _auth_form(request, db, "login", email, password)
    if error:
        return templates.TemplateResponse(request, "auth.html", {
            "request": request, "mode": "login", "error": error, "user": None,
            "cart_count": 0, "active_nav": None, "tracking": _no_tracking(),
            "page_events": [], "dwell_topic": None}, status_code=401)
    return RedirectResponse("/", status_code=303)


@router.post("/register")
def register_form(request: Request, email: str = Form(...), password: str = Form(...),
                  sd=Depends(_db)):
    state, db = sd
    user, error = _auth_form(request, db, "register", email, password)
    if error:
        return templates.TemplateResponse(request, "auth.html", {
            "request": request, "mode": "register", "error": error, "user": None,
            "cart_count": 0, "active_nav": None, "tracking": _no_tracking(),
            "page_events": [], "dwell_topic": None}, status_code=409)
    return RedirectResponse("/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


# ---- Explore ----

@router.get("/", response_class=HTMLResponse)
def explore(request: Request, q: str | None = None, category: str | None = None,
            sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    stmt = select(models.Product).where(models.Product.deleted_at.is_(None))
    products = db.execute(stmt).scalars().all()
    categories = sorted({p.category for p in products if p.category})
    if q:
        needle = q.lower()
        products = [p for p in products
                    if needle in f"{p.name} {p.vendor} {p.description}".lower()]
    if category:
        products = [p for p in products if p.category == category]

    events = []
    if q:
        events.append({"type": "SEARCH", "metadata": {"query": q}})
    if category:
        events.append({"type": "CATEGORY_VIEWED", "metadata": {"category": category}})

    views = [_product_view(p, len(_caps_of(db, p.product_id))) for p in products]
    ctx = _base_ctx(request, db, user, state, "explore", events)
    ctx.update({"products": views, "categories": categories, "q": q, "category": category})
    return templates.TemplateResponse(request, "explore.html", ctx)


# ---- Product detail ----

@router.get("/product/{product_id}", response_class=HTMLResponse)
def product_page(request: Request, product_id: str, sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    p = db.get(models.Product, product_id)
    if p is None or p.deleted_at is not None:
        raise HTTPException(404)
    cap_ids = _caps_of(db, product_id)
    cap_names = [_CAP_BY_ID[c][0] for c in cap_ids if c in _CAP_BY_ID]
    security_caps = [_CAP_BY_ID[c][0] for c in cap_ids
                     if c in _CAP_BY_ID and _CAP_BY_ID[c][1] in
                     ("Identity & Access", "Security", "Compliance")]
    view = _product_view(p, len(cap_ids))
    view["capabilities"] = sorted(cap_names)
    view["security_caps"] = sorted(security_caps)

    events = [{"type": "PRODUCT_VIEWED",
               "metadata": {"product_id": product_id, "category": (p.category or "").lower()}}]
    ctx = _base_ctx(request, db, user, state, "explore", events)
    ctx.update({"p": view})
    return templates.TemplateResponse(request, "product.html", ctx)


# ---- Comparison ----

@router.get("/compare", response_class=HTMLResponse)
def compare(request: Request, a: str | None = None, b: str | None = None, sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    products = db.execute(select(models.Product).where(
        models.Product.deleted_at.is_(None))).scalars().all()

    def enrich(pid):
        p = db.get(models.Product, pid) if pid else None
        if p is None:
            return None
        view = _product_view(p)
        view["capability_names"] = {_CAP_BY_ID[c][0] for c in _caps_of(db, pid) if c in _CAP_BY_ID}
        return view

    va, vb = enrich(a), enrich(b)
    events = []
    comparison_caps = []
    if va and vb:
        comparison_caps = sorted(va["capability_names"] | vb["capability_names"])
        events.append({"type": "COMPARISON_STARTED",
                       "metadata": {"product_a": a, "product_b": b}})
    ctx = _base_ctx(request, db, user, state, "explore", events)
    ctx.update({"all_products": [_product_view(p) for p in products],
                "a": va, "b": vb, "comparison_caps": comparison_caps})
    return templates.TemplateResponse(request, "compare.html", ctx)


# ---- For you ----

def _build_feed(db, user) -> dict | None:
    journey = db.execute(
        select(models.Journey).where(models.Journey.user_id == user.id)
        .order_by(models.Journey.created_at.desc())).scalars().first()
    if journey is None:
        return None
    pkg = db.execute(
        select(models.RecommendationPackage)
        .where(models.RecommendationPackage.journey_id == journey.journey_id)
        .order_by(models.RecommendationPackage.created_at.desc())).scalars().first()
    if pkg is None:
        return None
    aar = db.execute(
        select(models.AdvisoryResponse)
        .where(models.AdvisoryResponse.rpkg_id == pkg.rpkg_id,
               models.AdvisoryResponse.surface == "ONSITE")
        .order_by(models.AdvisoryResponse.created_at.desc())).scalars().first()
    last_run = db.execute(
        select(models.WorkflowRun).where(models.WorkflowRun.user_id == user.id,
                                         models.WorkflowRun.status == "COMPLETED")
        .order_by(models.WorkflowRun.finished_at.desc())).scalars().first()

    entries = []
    for entry in pkg.entries:
        p = db.get(models.Product, entry["product_id"])
        if p is None:
            continue
        initials, hue = monogram(p.name, p.vendor)
        covered = sorted({_CAP_BY_ID[c][0]
                          for per in entry["per_requirement"].values()
                          for c in per["supported_capability_ids"] if c in _CAP_BY_ID})
        missing = [_CAP_BY_ID[c][0] for c in entry["missing_capability_ids"] if c in _CAP_BY_ID]
        entries.append({
            "product_id": p.product_id, "name": p.name, "vendor": p.vendor,
            "initials": initials, "hue": hue, "rank": entry["rank"],
            "coverage": entry["overall_coverage"],
            "why_covered": covered[:6], "why_missing": missing[:4],
        })

    return {
        "readiness": pkg.readiness,
        "entries": entries,
        "sections": aar.sections if aar else {},
        "updated": pkg.created_at.strftime("%Y-%m-%d %H:%M UTC"),
        "trigger": last_run.trigger_type if last_run else "—",
    }


@router.get("/for-you", response_class=HTMLResponse)
def for_you(request: Request, sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    ctx = _base_ctx(request, db, user, state, "foryou")
    ctx["feed"] = _build_feed(db, user)
    return templates.TemplateResponse(request, "foryou.html", ctx)


@router.get("/for-you/feed", response_class=HTMLResponse)
def for_you_feed(request: Request, sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    if user is None:
        raise HTTPException(401)
    return templates.TemplateResponse(request, "_feed.html", {
        "request": request, "feed": _build_feed(db, user)})


# ---- Cart & checkout ----

@router.get("/cart", response_class=HTMLResponse)
def cart_page(request: Request, sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    items = []
    for ci in db.execute(select(models.CartItem).where(
            models.CartItem.user_id == user.id)).scalars().all():
        p = db.get(models.Product, ci.product_id)
        if p:
            items.append(_product_view(p))
    ctx = _base_ctx(request, db, user, state, None)
    ctx["items"] = items
    return templates.TemplateResponse(request, "cart.html", ctx)


@router.post("/cart/add/{product_id}")
def cart_add(request: Request, product_id: str, sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if db.get(models.Product, product_id) is None:
        raise HTTPException(404)
    if db.get(models.CartItem, (user.id, product_id)) is None:
        db.add(models.CartItem(user_id=user.id, product_id=product_id))
        db.commit()
    return RedirectResponse("/cart", status_code=303)


@router.post("/cart/remove/{product_id}")
def cart_remove(request: Request, product_id: str, sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    item = db.get(models.CartItem, (user.id, product_id))
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse("/cart", status_code=303)


@router.post("/checkout")
def checkout(request: Request, card_name: str = Form(...), card_number: str = Form(...),
             card_expiry: str = Form(...), card_cvc: str = Form(...), sd=Depends(_db)):
    """Demonstration flow — card details format-validated, never stored, always
    succeed. Emits PURCHASE_COMPLETED through the standard event pipeline."""
    state, db = sd
    user = _optional_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if not (re.fullmatch(r"[0-9 ]{12,23}", card_number)
            and re.fullmatch(r"[0-9]{2}/[0-9]{2}", card_expiry)
            and re.fullmatch(r"[0-9]{3,4}", card_cvc) and card_name.strip()):
        raise HTTPException(422, "card details failed format validation")

    items = db.execute(select(models.CartItem).where(
        models.CartItem.user_id == user.id)).scalars().all()
    if not items:
        return RedirectResponse("/cart", status_code=303)

    now = utcnow()
    order_id = f"ORD-{uuid.uuid4().hex[:10]}"
    latest_session = db.execute(
        select(models.Session).where(models.Session.user_id == user.id)
        .order_by(models.Session.last_event_at.desc())).scalars().first()
    session_id = latest_session.session_id if latest_session else f"srv-{order_id}"
    journey_id = latest_session.journey_id if latest_session else None

    db.add(models.Order(order_id=order_id, user_id=user.id,
                        journey_id=journey_id, created_at=now))
    product_names = []
    event_rows = []
    for item in items:
        p = db.get(models.Product, item.product_id)
        product_names.append(p.name if p else item.product_id)
        db.add(models.OrderItem(order_id=order_id, product_id=item.product_id,
                                price_note=p.price_note if p else None))
        event_rows.append({
            "event_id": str(uuid.uuid4()), "user_id": user.id, "session_id": session_id,
            "journey_id": None, "event_type": "PURCHASE_COMPLETED",
            "signal_class": "HIGH",
            "event_metadata": {"product_id": item.product_id, "order_id": order_id},
            "ts": now, "received_at": now, "processed_at": None})
        db.delete(item)
    if latest_session is None:
        db.add(models.Session(session_id=session_id, user_id=user.id,
                              started_at=now, last_event_at=now))
    insert_events_idempotent(db, event_rows)
    db.commit()

    from apps.web.main import _evaluate_triggers_async

    _evaluate_triggers_async(user.id)

    ctx = _base_ctx(request, db, user, state, None)
    ctx.update({"order_id": order_id, "product_names": product_names})
    return templates.TemplateResponse(request, "confirmation.html", ctx)


# ---- Account ----

@router.get("/account", response_class=HTMLResponse)
def account(request: Request, sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    ctx = _base_ctx(request, db, user, state, "account")
    ctx["chat_id"] = user.telegram_chat_id
    return templates.TemplateResponse(request, "account.html", ctx)


@router.post("/account")
def account_save(request: Request, digest_channel: str = Form("TELEGRAM"),
                 telegram_chat_id: str = Form(""), digest_opt_in: str = Form(None),
                 sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if digest_channel not in ("TELEGRAM", "EMAIL"):
        raise HTTPException(422, "unknown channel")
    user.digest_opt_in = digest_opt_in is not None
    user.digest_channel = digest_channel
    user.telegram_chat_id = telegram_chat_id.strip() or None
    db.commit()
    ctx = _base_ctx(request, db, user, state, "account")
    ctx.update({"chat_id": user.telegram_chat_id, "saved": True})
    return templates.TemplateResponse(request, "account.html", ctx)


# ---- Admin ----

def _admin_products(db) -> list[dict]:
    out = []
    for p in db.execute(select(models.Product).where(
            models.Product.deleted_at.is_(None))
            .order_by(models.Product.product_id)).scalars().all():
        out.append({"product_id": p.product_id, "name": p.name, "vendor": p.vendor,
                    "sync_status": p.sync_status, "cap_ids": _caps_of(db, p.product_id)})
    return out


@router.get("/admin", response_class=HTMLResponse)
def admin(request: Request, sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    _require_admin(user)
    ctx = _base_ctx(request, db, user, state, "admin")
    ctx["products"] = _admin_products(db)
    return templates.TemplateResponse(request, "admin.html", ctx)


@router.get("/admin/table", response_class=HTMLResponse)
def admin_table(request: Request, sd=Depends(_db)):
    state, db = sd
    _require_admin(_optional_user(request, db))
    return templates.TemplateResponse(request, "_admin_table.html", {
        "request": request, "products": _admin_products(db)})


def _all_capabilities(db):
    return db.execute(select(models.Capability)
                      .order_by(models.Capability.capability_id)).scalars().all()


@router.get("/admin/new", response_class=HTMLResponse)
def admin_new(request: Request, sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    _require_admin(user)
    ctx = _base_ctx(request, db, user, state, "admin")
    ctx.update({"p": None, "all_capabilities": _all_capabilities(db)})
    return templates.TemplateResponse(request, "admin_form.html", ctx)


@router.get("/admin/product/{product_id}", response_class=HTMLResponse)
def admin_edit(request: Request, product_id: str, sd=Depends(_db)):
    state, db = sd
    user = _optional_user(request, db)
    _require_admin(user)
    p = db.get(models.Product, product_id)
    if p is None:
        raise HTTPException(404)
    view = _product_view(p)
    view["cap_ids"] = _caps_of(db, product_id)
    ctx = _base_ctx(request, db, user, state, "admin")
    ctx.update({"p": view, "all_capabilities": _all_capabilities(db)})
    return templates.TemplateResponse(request, "admin_form.html", ctx)


async def _admin_save(request: Request, db, state, product: models.Product):
    form = await request.form()
    cap_ids = form.getlist("capabilities")
    valid = {c.capability_id for c in _all_capabilities(db)}
    unknown = [c for c in cap_ids if c not in valid]
    if unknown:
        raise HTTPException(422, f"unknown capability IDs: {unknown}")  # Core 14
    product.name = str(form.get("name", "")).strip()
    product.vendor = str(form.get("vendor", "")).strip()
    product.category = str(form.get("category", "")).strip()
    product.description = str(form.get("description", "")).strip()
    product.business_purpose = str(form.get("business_purpose", "")).strip()
    product.price_note = str(form.get("price_note", "")).strip() or None
    product.record_version = (product.record_version or 0) + 1
    product.updated_at = utcnow()
    try:
        save_product(db, state["chroma"], state["backend"], product, list(cap_ids))
    except Exception:
        pass  # row stays PENDING/FAILED; reconciliation sweep retries (POL-RETR-004)


@router.post("/admin/new")
async def admin_create(request: Request, sd=Depends(_db)):
    state, db = sd
    _require_admin(_optional_user(request, db))
    existing = db.execute(select(models.Product.product_id)).scalars().all()
    numbers = [int(pid.split("-")[1]) for pid in existing if pid.startswith("PROD-")]
    product = models.Product(product_id=f"PROD-{(max(numbers, default=0) + 1):03d}")
    await _admin_save(request, db, state, product)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/product/{product_id}")
async def admin_update(request: Request, product_id: str, sd=Depends(_db)):
    state, db = sd
    _require_admin(_optional_user(request, db))
    product = db.get(models.Product, product_id)
    if product is None:
        raise HTTPException(404)
    await _admin_save(request, db, state, product)
    return RedirectResponse("/admin", status_code=303)


# ---- Reasoning Panel (admin-gated) ----

@router.get("/reasoning", response_class=HTMLResponse)
def reasoning(request: Request, user_id: int | None = None, sd=Depends(_db)):
    state, db = sd
    admin_user = _optional_user(request, db)
    _require_admin(admin_user)
    users = db.execute(select(models.User).order_by(models.User.email)).scalars().all()
    selected = db.get(models.User, user_id) if user_id else (users[0] if users else None)

    ctx = _base_ctx(request, db, admin_user, state, "reasoning")
    ctx.update({"users": users, "selected": selected, "journey": None})
    if selected is None:
        return templates.TemplateResponse(request, "reasoning.html", ctx)

    journey = db.execute(
        select(models.Journey).where(models.Journey.user_id == selected.id)
        .order_by(models.Journey.created_at.desc())).scalars().first()
    if journey is None:
        return templates.TemplateResponse(request, "reasoning.html", ctx)

    stage_row = db.execute(
        select(models.JourneyStage).where(models.JourneyStage.journey_id == journey.journey_id)
        .order_by(models.JourneyStage.version.desc())).scalars().first()
    current_stage = stage_row.stage if stage_row else "Awareness"
    current_index = JOURNEY_STAGES.index(current_stage)
    stages = [{"name": s, "state": ("current" if i == current_index
                                    else "done" if i < current_index else "")}
              for i, s in enumerate(JOURNEY_STAGES)]

    latest: dict[str, models.Hypothesis] = {}
    for h in db.execute(select(models.Hypothesis).where(
            models.Hypothesis.journey_id == journey.journey_id)
            .order_by(models.Hypothesis.version)).scalars().all():
        latest[h.hypothesis_id] = h
    hypotheses = [{
        "concept_id": h.concept_id,
        "concept_name": BEHAVIORAL_CONCEPTS.get(h.concept_id, h.concept_id),
        "confidence": h.confidence, "status": h.status, "version": h.version,
    } for h in sorted(latest.values(), key=lambda x: -x.confidence)]

    # Requirements: published entries + held derivations (full noisy-OR view)
    active = {h["concept_id"]: h["confidence"] for h in hypotheses}
    weights = state["policies"].param("POL-REQ-003", "association_weights")
    publish_min = state["policies"].param("POL-REQ-001", "min_confidence")
    derived: dict[str, float] = {}
    for bc_id, confidence in active.items():
        for req_id, association in BC_TO_REQ.get(bc_id, {}).items():
            derived.setdefault(req_id, 1.0)
            derived[req_id] *= 1.0 - weights[association] * confidence
    rp = db.execute(
        select(models.RequirementProfile)
        .where(models.RequirementProfile.journey_id == journey.journey_id)
        .order_by(models.RequirementProfile.version.desc())).scalars().first()
    published = {e["req_id"]: e for e in (rp.requirements if rp else [])}
    requirements = []
    for req_id, survival in sorted(derived.items(), key=lambda kv: kv[1]):
        raw = round(1.0 - survival, 2)
        entry = published.get(req_id)
        requirements.append({
            "req_id": req_id, "name": REQUIREMENTS.get(req_id, req_id),
            "confidence": entry["confidence"] if entry else raw,
            "priority": entry["priority"] if entry else None,
            "held": entry is None and raw < publish_min,
        })

    trigger_log = [{
        "ts": r.started_at.strftime("%m-%d %H:%M:%S"),
        "status": r.status, "trigger_type": r.trigger_type,
        "reason": (r.gates or {}).get("decision", "")[:80],
    } for r in db.execute(
        select(models.WorkflowRun).where(models.WorkflowRun.user_id == selected.id)
        .order_by(models.WorkflowRun.started_at.desc()).limit(20)).scalars().all()]

    traits = db.execute(
        select(models.BehavioralTrait).where(models.BehavioralTrait.user_id == selected.id)
        .order_by(models.BehavioralTrait.strength.desc())).scalars().all()
    all_journeys = db.execute(
        select(models.Journey).where(models.Journey.user_id == selected.id)
        .order_by(models.Journey.created_at)).scalars().all()

    ctx.update({"journey": journey, "stages": stages, "hypotheses": hypotheses,
                "requirements": requirements, "trigger_log": trigger_log,
                "traits": traits, "all_journeys": all_journeys})
    return templates.TemplateResponse(request, "reasoning.html", ctx)
