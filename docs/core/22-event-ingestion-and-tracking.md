# Event Ingestion & Tracking

**Version:** 1.0

---

# Purpose

This chapter defines how Behavioral Events are captured in the client and ingested by the platform.

The Event Schema (Chapter 13) defines what an event **is**.

This chapter defines how events are **collected and delivered** — efficiently, non-blockingly, and losslessly enough to power behavioral reasoning without ever degrading the user experience.

---

# Guiding Principle

Tracking must be invisible.

The user experience is never delayed, blocked, or broken by telemetry.

Lose an event before you lose a frame.

---

# Tracked Interactions

The active Domain Pack defines the approved Event Types and their signal classes — **Domain Pack artifact 7** (`knowledge/architecture/domain-pack-contract.md`). The registry is *closed*: an event whose type is not in the active pack's table fails structural validation, and new types arrive only through a Domain Pack version.

This chapter owns the ingestion mechanism — batching, idempotency, signal handling, the tracking contract below. It does not own the vocabulary. Which interactions a domain tracks is a statement about that domain: a travel pack has no PRICING_VIEWED and a software pack has no DATE_RANGE_SELECTED.

**Reference registry:** `docs/domains/software-buying/13-event-registry.md`.

Signal class is domain knowledge consumed by Execution Triggers (Chapter 23). Raw scroll and hover activity is not tracked as discrete events; dwell is sampled via heartbeat.

---

# Client Tracking Contract

The tracking client is a small script embedded in every page. It must obey:

## 1. Buffer, don't send

Events append to an in-memory buffer. Nothing is sent per interaction.

## 2. Flush on threshold, interval, or exit

The buffer flushes when any of these occur:

- Buffer reaches N events (policy: `tracking.batch_size`)
- T seconds elapse since first buffered event (policy: `tracking.flush_interval`)
- Page becomes hidden or unloads — flushed via a fire-and-forget beacon transport (`navigator.sendBeacon`-class), which survives navigation without blocking it

## 3. Throttle high-frequency signals

Dwell heartbeats fire at a fixed cadence (policy: `tracking.heartbeat_interval`) and only while the page is visible. Repeated identical events within a debounce window collapse client-side.

## 4. Never block

All sends are asynchronous. No tracking call ever runs on the interaction path, awaits before navigation, or throws into application code. Tracking failures are silent to the user.

## 5. Identify honestly

Each event carries: anonymous-or-authenticated User ID, Session ID (client-generated, rotated after the inactivity timeout policy `tracking.session_timeout`), client Event ID (UUID, for idempotency), Event Type, timestamp, and type-specific metadata per the Event Schema. No content beyond what the Event Schema defines.

**Session identity belongs to the server (Decision #043).** The Session ID is a client suggestion, never an identity claim. Client session storage is scoped to a browser tab, not to a person, so the same ID keeps arriving after a shopper logs out and another logs in. Ingestion therefore **namespaces the client's Session ID by the authenticated User ID** before it is stored or matched, so one stored session can never span two accounts. The client should also start a new session when the logged-in user changes — a session is one person's sitting — but that is a behavioural nicety, not the isolation mechanism.

## 6. Tolerate failure

Failed flushes re-queue with capped retry and exponential backoff. The buffer has a maximum size; overflow drops **oldest low-signal events first** (dwell before views). Loss of low-signal events is acceptable by design.

---

# Ingestion API

## POST /events/batch

Accepts an array of event envelopes (Chapter 13 schema).

Contract:

- **Accept fast, process later.** The endpoint validates structure, persists the raw batch append-only, and returns `202 Accepted` immediately. Behavioral processing is asynchronous.
- **Idempotent.** Client Event IDs deduplicate replays of the same batch.
- **Order by timestamp, not arrival.** Late batches (e.g., beacon-delivered after navigation) are ordered by event timestamp during processing.
- **Reject only structural invalidity.** Per-event validation failures reject the individual event, never the whole batch; rejections are observable.
- **Bounded batches.** Batches larger than the policy maximum (POL-TRACK-001; v1: 50 events) are rejected wholesale as structurally invalid — the client contract never legitimately produces them.
- **Never trigger reasoning inline.** Ingestion enqueues; Execution Triggers (Chapter 23) decide when reasoning runs.

---

# Storage

Events persist to an append-only event store (batch inserts) before any processing. The event store is the immutable system of record that powers deterministic replay.

Processing state (which events have entered behavioral reasoning) is tracked separately from the events themselves — events are never mutated.

---

# Sessionization

- The client owns Session ID generation; the platform owns session boundary policy.
- A session ends after `tracking.session_timeout` of inactivity; the next event starts a new session.
- Session end is itself a platform-detected signal available to Execution Triggers (SESSION_END).

Journey Resolution (Chapter 12) — not sessionization — decides which Journey a session belongs to.

---

# Invariants

## Invariant 1

No tracking operation blocks or delays the user experience.

## Invariant 2

No network call per raw interaction — batching is mandatory.

## Invariant 3

Ingestion accepts and persists before processing; reasoning is never inline.

## Invariant 4

Event IDs make ingestion idempotent.

## Invariant 5

Events are append-only and immutable once persisted.

## Invariant 6

All thresholds (batch size, intervals, timeouts) are Decision Policy values, not code constants.

## Invariant 7

Overflow degrades by dropping low-signal events first; high-signal events are protected.

## Invariant 8

No Session and no Journey ever holds more than one user's events. Client-supplied identifiers are namespaced by the authenticated user at ingestion, and journey assignment filters on user as well as session.

---

# Claude Implementation Contract

Claude MUST:

- Implement client tracking as buffered, throttled, visibility-aware, beacon-flushed batches.
- Return 202 from ingestion after structural validation and raw persistence.
- Deduplicate by client Event ID.
- Batch-insert into an append-only store.
- Source every threshold from Decision Policies.

Claude MUST NOT:

- Send an event per interaction.
- Run behavioral reasoning inline with ingestion.
- Block navigation or interaction on tracking.
- Mutate persisted events.
- Surface tracking errors to the user.

---

# Relationship to Core Documentation

| Chapter | Responsibility |
|---------|----------------|
| 12 | Journey Resolution Engine |
| 13 | Event Schema |
| 10 | Decision Policies |
| 16 | API Contracts |
| 19 | Behavioral Reasoning Engine |
| 23 | Execution Triggers & Caching |

---

# Summary

Tracking captures rich behavioral signal — views, searches, dwell, comparisons — through a buffered, throttled, non-blocking client and an accept-fast/process-later ingestion API. Events land immutably and in order; reasoning about them is always someone else's job, on someone else's schedule.

---
