"""Proactive delivery — daily digest (docs/core/24; POL-DELIV-001/002).

The digest is a delivery surface, not a new reasoning path: it consumes the
latest deterministic Recommendation Package and generates a digest AAR with a
dedicated prompt version. Delivery is idempotent per (user, digest window) by
DB constraint; ineligible users are skipped AND recorded — silence is a
feature. Channel adapters: Telegram primary (one HTTP POST), Email optional
(self-reports unavailable without SMTP config); every delivery also renders
in-app via the Delivery Record + digest AAR.
"""

import os
import smtplib
import uuid
from datetime import datetime
from email.mime.text import MIMEText

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from smartreco import models, repos
from smartreco.advisor import MalformedResponse, generate_digest_sections
from smartreco.gateway import GatewayUnavailable
from smartreco.policies import PolicyCatalog


class TelegramAdapter:
    """Primary channel: one bot-API POST per delivery. Token from environment;
    self-reports unavailable when absent."""

    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN")

    @property
    def available(self) -> bool:
        return bool(self.token)

    def send(self, chat_id: str, text: str) -> None:
        response = httpx.post(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            json={"chat_id": chat_id, "text": text}, timeout=15)
        response.raise_for_status()


class EmailAdapter:
    """Optional channel behind SMTP environment variables."""

    def __init__(self):
        self.host = os.environ.get("SMTP_HOST")
        self.port = int(os.environ.get("SMTP_PORT") or 0)
        self.user = os.environ.get("SMTP_USER")
        self.password = os.environ.get("SMTP_PASSWORD")

    @property
    def available(self) -> bool:
        return bool(self.host and self.port)

    def send(self, to_address: str, text: str) -> None:
        message = MIMEText(text)
        message["Subject"] = "Your SmartReco digest"
        message["From"] = self.user or "smartreco@localhost"
        message["To"] = to_address
        with smtplib.SMTP(self.host, self.port, timeout=15) as server:
            if self.user and self.password:
                server.starttls()
                server.login(self.user, self.password)
            server.send_message(message)


def digest_window(now: datetime) -> str:
    return now.strftime("%Y-%m-%d")


def _record(db: OrmSession, user_id: int, channel: str, aar_id: str | None,
            status: str, reason: str, window: str, now: datetime) -> None:
    repos.insert_delivery_record(db, models.DeliveryRecord(
        user_id=user_id, channel=channel, aar_id=aar_id, status=status,
        reason=reason, digest_window=window, created_at=now))


def digest_text(sections: dict) -> str:
    return (f"{sections.get('recap', '')}\n\n"
            f"{sections.get('top_recommendation', '')}\n\n"
            f"Next step: {sections.get('next_action', '')}\n\n"
            f"{sections.get('disclaimer', '')}").strip()


def run_digest_cycle(db: OrmSession, chroma_client, backend, gateway,
                     policies: PolicyCatalog, now: datetime,
                     telegram: TelegramAdapter | None = None,
                     email: EmailAdapter | None = None) -> list[models.DeliveryRecord]:
    """One SCHEDULED digest cycle over all users. Eligible users get a standard
    workflow run (SCHEDULED trigger — no separate digest pipeline, core 24)
    before the readiness gate; every decision — including every skip — writes
    a Delivery Record (observable silence)."""
    from smartreco.advisor import PROMPT_VERSION_DIGEST, REQUIRED_DISCLAIMER
    from smartreco.pipeline import (
        _behavior_summary,
        lifecycle_sweep,
        record_ai_call,
        run_workflow,
    )

    telegram = telegram or TelegramAdapter()
    email = email or EmailAdapter()
    window = digest_window(now)
    min_events = policies.param("POL-DELIV-001", "min_high_signal_events_since_last")
    max_per_day = policies.param("POL-DELIV-002", "max_digests_per_user_per_day")
    records: list[models.DeliveryRecord] = []

    users = db.execute(select(models.User)).scalars().all()
    for user in users:
        lifecycle_sweep(db, policies, user.id, now)  # daily dormancy/closure sweep
        channel = user.digest_channel or "TELEGRAM"

        def record(channel, aar_id, status, reason):
            _record(db, user.id, channel, aar_id, status, reason, window, now)

        # Idempotent by (user, digest_window): exactly one record per window,
        # enforced by DB constraint — a rerun of the cycle is a no-op.
        existing = db.execute(
            select(models.DeliveryRecord).where(
                models.DeliveryRecord.user_id == user.id,
                models.DeliveryRecord.digest_window == window)
        ).scalars().first()
        if existing is not None:
            continue

        if not user.digest_opt_in or not user.digest_channel:
            record(channel, None, "SKIPPED", "not opted in")
            continue

        last_digest = db.execute(
            select(models.DeliveryRecord).where(
                models.DeliveryRecord.user_id == user.id,
                models.DeliveryRecord.status == "SENT")
            .order_by(models.DeliveryRecord.created_at.desc())).scalars().first()
        since = last_digest.created_at if last_digest else datetime.min
        high_signal_since = db.execute(
            select(models.Event).where(
                models.Event.user_id == user.id,
                models.Event.signal_class == "HIGH",
                models.Event.ts > since)
        ).scalars().all()
        if len(high_signal_since) < min_events:
            record(user.digest_channel, None, "SKIPPED",
                   f"only {len(high_signal_since)} high-signal events since last "
                   f"digest (< {min_events}, POL-DELIV-001)")
            continue

        # Standard workflow run for the eligible user (SCHEDULED trigger) —
        # the digest reuses the pipeline, it never re-reasons on its own
        run_workflow(db, chroma_client, backend, policies, user.id, "SCHEDULED",
                     now=now, gateway=gateway)

        journey = db.execute(
            select(models.Journey).where(models.Journey.user_id == user.id)
            .order_by(models.Journey.created_at.desc())).scalars().first()
        pkg = db.execute(
            select(models.RecommendationPackage)
            .where(models.RecommendationPackage.journey_id == journey.journey_id)
            .order_by(models.RecommendationPackage.created_at.desc())
        ).scalars().first() if journey else None
        if pkg is None or pkg.readiness != "READY" or not pkg.entries:
            record(user.digest_channel, None, "SKIPPED",
                   "no READY recommendation package — silence is a feature")
            continue

        # Digest AAR: cache-first per (package, prompt version, DIGEST surface)
        aar = db.execute(
            select(models.AdvisoryResponse).where(
                models.AdvisoryResponse.rpkg_id == pkg.rpkg_id,
                models.AdvisoryResponse.prompt_version == PROMPT_VERSION_DIGEST,
                models.AdvisoryResponse.surface == "DIGEST")
        ).scalars().first()
        if aar is None:
            if gateway is None:
                record(user.digest_channel, None, "SKIPPED", "gateway unavailable")
                continue
            products = []
            for entry in pkg.entries[:3]:
                product = db.get(models.Product, entry["product_id"])
                products.append({"name": product.name, "vendor": product.vendor,
                                 "coverage": entry["overall_coverage"],
                                 "on_subject": entry.get("on_subject", True)})
            facts = {"products": products,
                     "behavior_summary": _behavior_summary(
                         repos.journey_events(db, journey.journey_id))}
            try:
                sections, version, calls = generate_digest_sections(gateway, facts)
            except (MalformedResponse, GatewayUnavailable) as exc:
                record(user.digest_channel, None, "FAILED",
                       f"digest generation failed: {exc}")
                continue
            for _ in range(calls):
                record_ai_call(db, user.id, "tier1", now)
            sections["disclaimer"] = REQUIRED_DISCLAIMER
            aar = models.AdvisoryResponse(
                aar_id=f"AAR-{uuid.uuid4().hex[:10]}", rpkg_id=pkg.rpkg_id,
                surface="DIGEST", prompt_version=version,
                model_id=getattr(gateway, "model", ""), sections=sections,
                created_at=now)
            repos.insert_advisory_response(db, aar)
            db.flush()

        text = digest_text(aar.sections)
        try:
            if user.digest_channel == "TELEGRAM":
                if not telegram.available or not user.telegram_chat_id:
                    record("TELEGRAM", aar.aar_id, "SKIPPED",
                           "telegram unavailable or chat not connected")
                    continue
                telegram.send(user.telegram_chat_id, text)
            elif user.digest_channel == "EMAIL":
                if not email.available:
                    record("EMAIL", aar.aar_id, "SKIPPED",
                           "email adapter unavailable (no SMTP config)")
                    continue
                email.send(user.email, text)
            record(user.digest_channel, aar.aar_id, "SENT", "delivered")
        except Exception as exc:
            record(user.digest_channel, aar.aar_id, "FAILED",
                   f"{type(exc).__name__}: {exc}")

    db.commit()
    for r in db.execute(select(models.DeliveryRecord).where(
            models.DeliveryRecord.digest_window == window)).scalars().all():
        records.append(r)
    return records
