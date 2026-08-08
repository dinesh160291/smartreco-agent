# Proactive Delivery

**Version:** 1.0

---

# Purpose

Proactive Delivery brings recommendations to the user instead of waiting for a visit: a scheduled digest that recaps recent behavioral interests and delivers a persuasive, grounded recommendation narrative through an outbound channel (email, Telegram, or equivalent).

Proactive Delivery is a **delivery surface**, not a new reasoning path. It reuses the standard recommendation workflow end to end. There is no separate "digest pipeline" — only a scheduled trigger and a channel at the end.

---

# Guiding Principle

Same truth, new doorstep.

A digest is the platform's existing deterministic outputs, re-narrated for an outbound moment — never a second opinion.

---

# Scheduler Contract

- Digests are initiated by a **real background scheduler** (APScheduler-, Celery Beat-, or cron-class; implementation-agnostic). A manual "send digest" button is a demo aid at most — it is never the mechanism.
- The scheduler fires the SCHEDULED Execution Trigger (Chapter 23) at the configured digest window (`delivery.digest_schedule`, e.g., daily 17:00 user-local or platform-local per policy).
- Scheduler runs are observable: fire time, users evaluated, digests sent, skips and reasons.

---

# Digest Pipeline

```text
Scheduler fires (SCHEDULED trigger)
        ↓
Eligibility selection (deterministic, per policy)
        ↓  eligible users only
Standard workflow run (Chapter 21) — fast path; slow path per cache state
        ↓
Readiness gate
   NOT_READY ─► skip user (recorded); optionally a light "we're still learning your interests" touch — policy-controlled
        ↓ READY
Digest AAR generation (Tier 1, digest prompt variant)
        ↓
Channel adapter delivery (email / Telegram / …)
        ↓
Delivery Record persisted
```

## Eligibility

Deterministic policy over: activity since last digest (`delivery.min_new_events`), account delivery preferences (opt-in, channel), frequency cap (`delivery.max_per_day`, typically 1), and quiet hours. Users with nothing meaningfully new receive nothing — silence is a feature.

## Digest AAR variant

The digest uses a dedicated prompt version in the Prompt Library (Chapter 15): a short persuasive recap of the period's observed interests ("this morning you kept returning to security and SSO docs…"), the top deterministic recommendations, and one clear next action. Grounding rules are identical to every AAR: persuasion from platform facts only.

## Delivery Records

Every attempt persists: user, channel, digest AAR reference, Recommendation Package reference, sent/failed/skipped status, reason, timestamp. Delivery is idempotent per (user, digest window) — reruns never double-send.

---

# Channel Adapters

Channels implement one narrow adapter contract: `deliver(recipient, rendered_digest) → DeliveryStatus`.

- Email and Telegram are the reference adapters.
- Adding a channel adds an adapter — never a change to reasoning, generation, or scheduling.
- Rendering (HTML email vs. chat message) is presentation, owned by the adapter.

---

# Invariants

## Invariant 1

Digests are initiated only by the scheduler-fired SCHEDULED trigger — never manually as the primary mechanism, never inline with user actions.

## Invariant 2

Proactive Delivery reuses the standard workflow; it introduces no alternative reasoning path.

## Invariant 3

Digest content is grounded in the same deterministic Runtime Objects as on-site recommendations.

## Invariant 4

Delivery is idempotent per user per digest window.

## Invariant 5

Eligibility, frequency, and quiet hours are Decision Policy values.

## Invariant 6

Every delivery attempt is recorded and observable.

## Invariant 7

Users with no material new behavior are skipped — the digest never pads.

---

# Claude Implementation Contract

Claude MUST:

- Initiate digests from a real background scheduler firing the SCHEDULED trigger.
- Reuse the standard workflow and readiness gate.
- Use the digest prompt variant with full grounding rules.
- Enforce idempotency per digest window and persist Delivery Records.
- Implement channels as adapters behind the delivery contract.

Claude MUST NOT:

- Build a manual-button delivery mechanism as the digest path.
- Create a parallel reasoning pipeline for digests.
- Send content ungrounded in deterministic Runtime Objects.
- Deliver to users with no material new behavior.
- Double-send on scheduler reruns.

---

# Relationship to Core Documentation

| Chapter | Responsibility |
|---------|----------------|
| 09 | AI Buying Advisor (digest AAR generation) |
| 10 | Decision Policies (eligibility, schedule, caps) |
| 15 | LLM Contract (digest prompt variant) |
| 21 | Agent Orchestration (the reused workflow) |
| 23 | Execution Triggers & Caching (SCHEDULED trigger) |

---

# Summary

Proactive Delivery is the scheduled, outbound face of the platform: a real scheduler fires the standard workflow for eligible users, the AI Buying Advisor re-narrates the deterministic results as a persuasive digest, and channel adapters put it on the user's doorstep — same truth, new doorstep.

---
