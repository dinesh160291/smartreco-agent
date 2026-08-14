# User Journey Stories — Expected Outcomes

**Version:** 1.0

**Status:** Locked — these are the end-to-end acceptance criteria

> **Instruction to the implementing agent:** These stories are the expected behavior of the finished system, derived from the specification (core chapters, Policy Catalog v1, Domain Pack). Treat them as acceptance tests: Stories 1–8 must be automatable (seed → replay clickstream → assert); Stories 9–10 are semi-automated. **Every "Failure looks like" condition is a bug, not a design choice.** When implementation and story disagree, the spec + story win. Stories 1–2 reuse the derivations in Domain 09; the rest extend coverage to gates, noise, journey intelligence, commerce, and operations.

Conventions: events named per Core 22; policies per Core 10 (Policy Catalog v1); UI surfaces per `docs/implementation/ui-design-spec.md`. "Run" = one orchestration workflow execution (Core 21).

**Placement.** These stories live in the Domain Pack because they are written entirely in software-buying terms — identity platforms, capability coverage, named products and exact percentages. The platform they exercise is domain-agnostic; the expectations are not. A second domain would carry its own stories at this position, and `docs/implementation/` stays reusable across domains.

---

## Group A — Happy paths

### Story 1 — The Security Evaluator

**Persona:** IT lead at a financial-services firm, standardizing identity.

**Clickstream (2 sessions):**

| # | Action | Event | Signal |
|---|---|---|---|
| 1 | Logs in, searches "single sign-on", opens Okta | SEARCH, PRODUCT_VIEWED | High |
| 1 | Security tab; SSO + admin/provisioning docs | SECURITY_VIEWED, DOCUMENTATION_VIEWED topic=sso/admin/provisioning | High |
| 2 | Audit page + MFA docs, reads 60s | SECURITY_VIEWED topic=audit, DOCUMENTATION_VIEWED topic=mfa, DWELL×6 | High + Low |
| 2 | Compares Okta vs Microsoft 365 | COMPARISON_STARTED | High |
| 3 | *(session 2, next day)* Security pages of four identity platforms, plus their admin docs | SECURITY_VIEWED×4, DOCUMENTATION_VIEWED topic=admin/provisioning | High |
| 4 | Narrows to Okta: SSO/MFA docs, enterprise pricing | DOCUMENTATION_VIEWED, PRICING_VIEWED tier=enterprise | High |
| 5 | Final pass over the same material | SECURITY_VIEWED, PRICING_VIEWED, DOCUMENTATION_VIEWED | High |

Each run brings a kind of evidence the last one lacked — pages, then reading
time, then a cross-product sweep, then documentation — which is what earns the
confidences below under POL-CONF-002 (Decision #054). The final run is
deliberately a repeat, and contributes half.

**Expected pipeline:** BP-001 fires (Medium→Strong with dwell), BP-002 fires (enterprise tier + admin docs) → BC-001 0.80, BC-002 0.70 → REQ-002 0.80 Critical, REQ-004 0.56 Medium, REQ-001 0.48 **held** → stage Technical Validation → retrieval + match.

**Expected outcome:** For-you page READY. **Okta rank 1 (82%)**, Microsoft 365 rank 2 (78%), Google Workspace rank 3 (53%). Persuasive narrative references *this user's* security/SSO research and names the SCIM/provisioning advantage; plain language only. Reasoning Panel (admin) shows both hypotheses, the held REQ-001 at 0.48, stage chip on Technical Validation.

**Failure looks like:** M365 ranked first (priority weighting broken) · narrative cites facts not in Runtime Objects · REQ-001 published · CAP codes visible on For-you.

---

### Story 2 — The Collaboration Modernizer

**Persona:** Ops director consolidating collaboration tools, curious about AI.

**Clickstream:** collaboration category → Google Workspace, Notion, Zoom product views → search "AI meeting summaries" → AI feature pages → *(second session)* the same platforms again, then meetings/template/task docs.

**Expected pipeline:** BP-005 (0.8), BP-006 (0.5), BP-003 (0.5) → REQ-001 0.83 Critical, REQ-005 0.75 High, REQ-003 0.41 held.

**Expected outcome:** **Google Workspace 97%**, Notion 49%, Zoom 33% (exact, per Scenario 2), ranked in that relative order. Broad-suite products whose profiles fully cover both requirements (Microsoft 365 at 100%) may legitimately rank above Google Workspace over the full catalog — the Scenario 2 derivation evaluated only the three products above, and the deterministic ranker must not be bent to exclude a product that honestly covers more (Decision #037). Narrative connects collaboration consolidation + AI curiosity. Workflow-automation products (ServiceNow, Zapier) absent from the top 3.

**Failure looks like:** REQ-003 published from secondary/supporting signals alone · automation products recommended.

---

## Group B — Gates and noise (the platform saying "not yet" and "no")

### Story 3 — The Cold-Start Browser

**Persona:** Brand-new account, two clicks, then idle.

**Clickstream:** login → home → one PRODUCT_VIEWED → leaves.

**Expected pipeline:** Below POL-TRIG-001 accumulation (< 5 high-signal); if SIGNIFICANT_EVENT fires, fast path runs → no pattern reaches activation → no hypotheses → empty Requirement Profile → **NOT_READY** (POL-REC-001).

**Expected outcome:** For-you shows the NOT_READY state: no product recommendations, no generic "popular products" fallback — a clarifying prompt ("What are you evaluating for — your team or yourself?") sourced from Recommendation Constraints. **Zero Tier-2 calls; at most one Tier-1 clarify call, then cached.**

**Failure looks like:** any ranked product list · a popularity fallback · LLM calls on every visit while state is unchanged.

---

### Story 4 — The Time-Waster (noise rejection)

**Persona:** Bored browser with no intent: skims 15 products across random categories in 12 minutes, short dwells, never opens a pricing/security/docs tab, never searches with intent.

**Clickstream:** 15 × PRODUCT_VIEWED across 6 categories, a few CATEGORY_VIEWED, DWELL heartbeats < 20s each, no tab-depth events.

**Expected pipeline:** Only BP-012 Product Discovery fires (Weak→Medium) → activates **BC-011, which deliberately maps to no Requirement** (Domain 06 — Unmapped Registry Concepts) → Requirement Profile stays empty → NOT_READY. Repeated same-type evidence hits diminishing returns (POL-CONF-002) — confidence saturates low. Stage never leaves Discovery (no evaluation evidence, milestone table §4.1). Triggers fire on accumulation, but **fast path only**: no material change ever occurs, so the slow path never spends a token beyond one cached clarify.

**Expected outcome:** The system correctly concludes *nothing* — no recommendations, no persuasion, near-zero AI spend, and the Reasoning Panel honestly shows: one weak Discovery hypothesis, empty requirements, stage Discovery. This story is the efficiency requirement (M11) proven behaviorally: **breadth of clicking is not evidence of intent; depth is.**

**Failure looks like:** recommendations produced from view-count popularity · confidence climbing linearly with repeated views · Tier-1/Tier-2 calls scaling with event volume.

---

### Story 5 — The Frenzy (burst & duplicate storm)

**Persona:** Impatient user (or misbehaving tab): rage-refreshes Okta's page, fires 30 near-identical events in 60 seconds.

**Expected pipeline:** Client throttling collapses repeats and drops overflow low-signal first (Core 22); server dedupes by client event UUID (replayed batches no-op); SIGNIFICANT_EVENT trigger **debounces 60s → exactly one run** for the burst (POL-TRIG-002); BRE evidence dedup (identical pattern activation over same events → no duplicate Evidence); diminishing returns cap the confidence effect of what remains.

**Expected outcome:** One workflow run, one evidence delta, bounded confidence movement, one (or zero) new Recommendation Package. `workflow_runs` shows the burst as 1 RUN + n SKIP(debounce) rows.

**Failure looks like:** 30 runs · duplicated evidence rows · confidence 0.95 from one page refreshed repeatedly.

---

## Group C — Journey intelligence

### Story 6 — The Multi-Journey User (context switch)

**Persona:** The Story-1 user, three weeks after purchasing Okta (journey closed, "Security Focus" + "Enterprise Preference"-class traits exist). Returns researching **personal note-taking**: Notion views, personal-tier pricing, templates docs.

**Expected pipeline:** Journey Resolution (Core 12 signal computation): topic similarity vs. the closed identity journey ≈ 0 (disjoint entity sets — and CLOSED journeys aren't candidates anyway) → **new journey created**. New journey infers productivity-side requirements. Old traits exist as Behavioral Profile priors but **current journey outranks profile** (Core 02, Principle 4).

**Expected outcome:** Recommendations are productivity/collaboration products for the *new* intent — no identity products pushed because of history. Reasoning Panel shows two journeys (one CLOSED · PURCHASED, one ACTIVE) and the long-term traits listed as priors, visibly *not* driving the current ranking.

**Failure looks like:** Okta or identity add-ons recommended in the note-taking journey · old journey reactivated for an unrelated topic · traits overriding current intent.

---

### Story 7 — The Returning Researcher (dormancy & resumption)

**Persona:** Mid-evaluation user goes quiet for 10 days (journey → DORMANT per POL-JRES-002), then resumes the *same* research: same products, same search terms.

**Expected pipeline:** Resolution signals: topic similarity high (overlapping entity sets), behavioral similarity high, time-decay = 0.5^(10/7) ≈ 0.37 → weighted score ≈ 0.4×hi + 0.3×hi + 0.3×0.37 ≥ 0.7 → **DORMANT journey reactivated**, not replaced.

**Expected outcome:** Hypotheses, requirements, and stage **resume** (evidence recency weighting applies, POL-BEH-002) — the user picks up where they left off; recommendations refresh rather than reset to cold start.

**Failure looks like:** a duplicate parallel journey for the same intent · confidence reset to zero · cold-start clarifying questions for a user with 3 weeks of history.

---

### Story 8 — The Mind-Changer (contradiction & reversal)

**Persona:** Starts as an enterprise identity evaluator (Story 1, sessions 1–2), then pivots: repeatedly views **individual/free tiers** and small-team products across the next two sessions.

**Expected pipeline:** BP-002's contradicting evidence rule fires (repeated individual-tier pricing) → Confidence Engine applies the contradiction penalty (POL-CONF-003, 75% of class contribution, gradual) → BC-002 weakens over successive runs → REQ-002/REQ-004 confidence recomputes downward (noisy-OR with lower inputs); priority bands shift; possible stage regression on 3 consecutive earlier-stage events (POL-STAGE-002). Material change → slow path re-runs.

**Expected outcome:** Within ~2 runs of sustained contradiction, rankings shift toward individual/small-team fits; the narrative acknowledges the shift ("you've moved from enterprise rollout toward a personal setup…") — gradually, not whiplash: one contrary click changes nothing.

**Failure looks like:** instant flip after a single contrary event · enterprise hypothesis never weakening despite sustained contradiction · narrative still selling enterprise rollout.

---

## Group D — Commerce, learning, proactive

### Story 9 — The Buyer (the learning arc)

**Persona:** Story-1 user proceeds: adds Okta to cart, checks out with the demo card.

**Clickstream:** Add to cart (ADD_TO_CART) → cart → Place order (CHECKOUT_STARTED → PURCHASE_COMPLETED).

**Expected pipeline:** BP-011 Very Strong → journey **CLOSED (PURCHASED) immediately** (POL-JRES-003) → Learning Engine runs: concept-derived traits created per POL-LEARN-001 ("Security Focus" from BC-001 ≥ 0.6; "Enterprise Preference"-class from BC-002 ≥ 0.6) at strength 0.30. Order recorded; no card data stored anywhere.

**Expected outcome:** Confirmation page shows the arc (event → closure → trait). Next session starts a fresh journey whose Reasoning Panel lists the traits as priors. Delivery of the arc is the demo's closing beat.

**Failure looks like:** journey still ACTIVE after purchase · traits created from an unclosed journey · any card field persisted.

---

### Story 10 — The Digest Pair (proactive delivery & silence)

**Personas:** A — Story-1 user with 6 high-signal events this morning, Telegram connected, opted in. B — opted-in user with zero activity since their last digest.

**Expected pipeline (17:00, APScheduler → SCHEDULED trigger):** eligibility per POL-DELIV-001/002: A qualifies (≥3 high-signal since last digest); B does not.

**Expected outcome:** A receives one Telegram message: persuasive recap of *this morning's* interests + top recommendations + one next action; Delivery Record SENT; unique (user, window) prevents double-send on scheduler rerun. **B receives nothing** — Delivery Record SKIPPED with reason. No manual send path exists.

**Failure looks like:** B gets a padded generic digest · A gets two messages after a rerun · digest content disagrees with A's on-site recommendations.

---

## Group E — Operational edges

### Story 11 — The Catalog Shift (admin change mid-journey)

**Persona:** Admin adds a new identity product ("Auth0-class", full identity capability set) while Story-1's user is mid-evaluation.

**Expected pipeline:** Dual-write (PENDING → SYNCED, visible in admin) → ADMIN_CATALOG_CHANGE invalidates candidate/recommendation caches keyed on catalog index version → user's next trigger re-retrieves → new product enters the Candidate Set and is ranked deterministically against the same Requirement Profile.

**Expected outcome:** The new product appears in the user's refreshed recommendations, ranked purely by coverage — proof the catalog is live end-to-end. If its vector write is still PENDING, it is absent from retrieval (never half-present).

**Failure looks like:** stale rankings served after catalog change (cache key missing index version) · a PENDING product surfacing in recommendations.

---

### Story 12 — The Budget Wall (graceful degradation)

**Persona:** Hyperactive legitimate user exhausts the Tier-1 daily budget (POL-TRIG-003) by mid-afternoon, then continues meaningful research.

**Expected pipeline:** Deterministic fast path continues on every trigger; new Recommendation Packages still publish; Tier-2 falls back to cached Candidate Sets (or full-catalog matching if none, Core 21); Tier-1 serves the last stored AAR alongside the fresh package.

**Expected outcome:** The user still sees updated rankings with the most recent narrative; nothing errors; `workflow_runs` records budget-gated nodes. Next day, generation resumes.

**Failure looks like:** blank recommendations page · errors surfaced to the user · budget bypassed.

---

# Deliberate Non-Story Coverage

**Trait decay (POL-DECAY-001)** is not covered by an E2E story: it operates on multi-week timescales (−0.05 per 14 idle days) that cannot occur inside a demo or test session. It is verified instead by a **clock-simulated unit test**: seed traits with known strengths and reinforcement counts, advance a simulated clock 14/28/56 days, and assert (a) strength decreases per policy, (b) higher Reinforcement Count slows decay per the resistance formula, (c) Reinforcement Count itself never changes, (d) traits are never deleted. The same simulated-clock harness also unit-tests journey dormancy/closure timing (POL-JRES-002/003) and evidence recency weighting (POL-BEH-002) at exact boundaries.

---

# Coverage Map

| Subsystem | Proven by |
|---|---|
| Patterns → requirements → ranking math | 1, 2 |
| Readiness gate / no popularity fallback | 3, 4 |
| Noise rejection, diminishing returns, efficiency (M11) | 4, 5 |
| Ingestion idempotency, debounce, evidence dedup | 5 |
| Journey Resolution: new / reactivate / current-over-profile | 6, 7 |
| Contradiction, gradual reversal, stage regression | 8 |
| Commerce closure + Learning Engine | 9 |
| Scheduler, eligibility, idempotent delivery, silence | 10 |
| Dual-write liveness + cache invalidation | 11 |
| Budgets + graceful degradation | 12 |

---
