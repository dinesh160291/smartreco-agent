# SmartReco — Project Instructions

SmartReco is a behavioral AI recommendation platform: a software marketplace that observes user behavior, reasons deterministically about intent, and delivers persuasive, grounded recommendations. Core platform and domain knowledge are strictly separated so the platform is reusable across domains.

All paths below are **relative to the repository root**. Never write absolute local paths into any file.

## Document Map (read before implementing anything)

| Path | Authority |
|---|---|
| `knowledge/architecture/` | Platform laws + domain governance — highest authority |
| `docs/core/` | Core chapters 00–24 + 99 (constitution), plus `glossary.md` and `decision-log.md` (#001–#034). Chapter 10 holds Policy Catalog v1 — every threshold |
| `docs/domains/software-buying/` | Domain Pack: ontology (BC registry), patterns (BP-001…012), requirement/capability catalogs, mappings, product roster, validation scenarios (09 = derivation math) |
| `docs/implementation/stack-decisions.md` | Locked stack, models, delivery channel, deployment compatibility |
| `docs/implementation/data-model.md` | Locked schema, catalog seed strategy (~250 products), design decisions D1–D3 |
| `docs/implementation/ui-design-spec.md` | Locked visual system — templates must match it exactly (preview URL inside) |
| `docs/domains/software-buying/11-user-journey-stories.md` | 12 E2E acceptance stories — binding; every "Failure looks like" is a bug |
| `docs/requirements-compliance.md` | Requirement → chapter map; deployment checklist |
| Problem-statement file (repo root, `problem_statement_*.md`) | Reference-only input, unmodified. **Local-only, gitignored — never committed** |

**Change control: spec first, code second.** If implementation and spec disagree, **the spec wins** — unless you deliberately change it. A spec that quietly disagrees with the code is worse than no spec, because the next session reads it and trusts it.

**If a fix contradicts a pinned document, amend the document in the same commit.** Not the next commit, not "I'll tidy the docs later" — a deferred amendment creates a window where code and spec disagree, and that window becomes permanent the moment anyone reads the stale side. A spec-contradicting change lands as **one commit** containing: the code, the test that pins the new behavior, the amended document, and — for architectural changes — a `docs/core/decision-log.md` entry saying what changed and why (smaller behavior changes: note it in the phase report).

## Non-Negotiable Laws (follow at all costs)

1. **Deterministic truth, two-tier AI.** Engines never call AI. Tier 1 (generation) and Tier 2 (embeddings, retrieval evaluation/refinement — inside the Semantic Retrieval Engine only) are the only AI touchpoints. AI proposes candidates and writes words; it never produces rankings, scores, requirements, stages, or readiness.
2. **LLMs have no tools.** Every model call is pure text completion — no function-calling, no actuators. User/admin-authored text enters prompts as delimited quoted data, never instructions.
3. **All AI calls go through the single AI Provider Gateway**, configured only from environment (`AI_GATEWAY_BASE_URL/_API_KEY/_MODEL/_EMBED_MODEL`, `EMBEDDINGS_BACKEND`). **Never name the provider in any file** — the provider is deployment configuration.
4. **No business thresholds in code.** Every number lives in `config/policies.yaml` mirroring Policy Catalog v1 (`docs/core/10`); engines consume via one loader; every workflow run records `policy_version`.
5. **Everything bounded.** Every loop, retry, and call has a cap and a deterministic fallback (POL-GATE-001, POL-RETR-002/004, POL-TRIG-002/003/005, POL-TRACK-001). Budget/AI failure always degrades to deterministic service — never an error page, never an infinite retry.
6. **Runtime Objects are immutable.** Insert-only repositories for the decision spine; new versions, never edits. Mutable state is only: users, products (+sync), cart, sessions, journeys (lifecycle), behavioral_traits.
7. **Closed enums.** Every categorical value comes from `docs/core/17` or the EventType registry (`docs/core/22` table). Never invent codes, statuses, or event types.
8. **Dual-write contract** (`docs/core/20`): relational store is the system of record; vector index is always re-derivable; product mutations follow PENDING→SYNCED with bounded reconciliation. Never write the vector store outside this contract.
9. **No AI call per raw event.** Tracking is buffered/throttled/non-blocking (`docs/core/22`); AI runs only via named triggers + material change + caches (`docs/core/23`).
10. **Vocabulary rule.** Canonical IDs (CAP/REQ/PROD/BC/BP) never appear on shopper-facing surfaces — display names only. IDs belong to Admin screens and the admin-gated Reasoning Panel.
11. **Grounded persuasion.** Persuasive copy uses only facts present in Runtime Objects — no invented social proof, scarcity, discounts, or capabilities (`docs/core/09`).
12. **Secrets:** only in `.env` (gitignored) / host secret store. Never committed, never printed in logs or docs. Checkout stores no payment data — no card fields exist in the schema.

## Doc Hygiene (all committed files)

- External requirements are always phrased as the "reference deployment" — never by the name or nature of their originating event, and never with event- or evaluation-flavored wording. If a word would reveal where the requirements came from, it doesn't belong in a committed file.
- Never name the AI provider (see Law 3).
- The problem-statement file at repo root is external input, unmodified — and local-only (gitignored), so it never reaches the public repository.

## Testing Contract

- Acceptance: the 12 stories in `docs/domains/software-buying/11-user-journey-stories.md` + the four derivation scenarios in `docs/domains/software-buying/09-…`. Assertions are exact (e.g., Okta 81% / M365 70% / Google 58% in Scenario 1).
- **Fixture separation:** automated tests seed only the canonical 10 products (PROD-001…010). The demo database seeds the full ~250-product catalog (`data-model.md` §Catalog Seed Strategy).
- Time-based policies (trait decay, dormancy, closure, recency) are unit-tested with a simulated clock — never with real waits.
- CI must stay green on every push (compile check + dependency manifest).
- **Signature tests over coverage.** Each test proves a spec requirement, story, or policy — name which one in the test. Coverage is measured, never gated.
- **TDD for pure functions** — the engines are pure functions by design: confidence arithmetic (POL-CONF), noisy-OR derivation (POL-REQ-003), coverage/ranking math (POL-REC-002), resolution signals (Jaccard/cosine/decay), stage milestones, the trigger evaluator. Write their tests first. Test-after is fine for wiring, routes, and UI.
- **Never assert on generated prose** — assert on the structured decision underneath (Recommendation Package entries, readiness, coverage numbers, AAR *section structure*). Where a story says the narrative "must reference X," assert grounding — the fact appears / banned content (invented discounts, social proof) is absent — never exact wording.
- **Tests run against a stubbed gateway.** The stub returns canned, schema-valid responses (and, when told to, malformed ones — the fallback paths need tests too). The live provider is touched only by the eval suite and one startup smoke test.
- **Eval caveats:** a failing eval case (persuasion quality, retrieval evaluation) must fail 3× to count as a bug — single-run LLM variance is not a signal. After any prompt change, run the full eval slice, not just the pinned case.

## Stack (locked — do not relitigate)

FastAPI · SQLAlchemy/SQLite (WAL) · Chroma embedded (`PersistentClient`) · APScheduler · Jinja2 SSR + htmx + Pico.css + hand-written vanilla-JS tracking client (no npm, no build step) · Agent framework: Google ADK, with LangGraph as fallback (switch triggers in `stack-decisions.md`) · Digest channel: Telegram primary, Email optional · Deployment: long-running host with persistent disk; serverless is incompatible.

## Change Discipline

### Before you change

- **Diagnose before changing.** When a test fails, first verify the test delivered the input you think it did; the suspected layer is often innocent. Name the root cause before writing the fix.
- **Replay-then-repair.** Never fix a bug you have not watched fail. Write the test that reproduces it and see it red — that is the proof it captures the bug. Diagnosis tells you *where*; the replay proves you were right.
- **Pin-then-fix.** The test or acceptance case lands *before* the prompt, policy, or engine changes, so "did it work?" has an answer that predates your investment in one.
- **Stop-and-ask thresholds.** A fix that wants to touch >3 files, add a dependency, or change a public seam gets explained first, not done first.

### While you change

- **Smallest diff that fixes the problem.** No drive-by refactors, renames, or cleanups of code you weren't asked to touch. If you see something worth improving, note it in the phase report — don't fold it into an unrelated change.
- **Match the neighborhood.** Follow the file's existing style, naming, and idioms — and prefer editing in place over rewriting whole files.
- **No speculative structure.** Don't add abstractions, options, or generality for futures nobody asked for. Three concrete uses before an abstraction.

  > **Exempt: the seams the spec mandates** — the AI Provider Gateway, the two-backend embedding abstraction (`EMBEDDINGS_BACKEND`), the vector-store adapter behind the Semantic Retrieval Engine contract, delivery channel adapters (Telegram/Email), the policy loader over `config/policies.yaml`, the orchestration framework wrapper (ADK ↔ LangGraph swap), and the simulated clock used by time-based tests. Each is justified in the specs and several ship with one implementation on purpose. They are not speculative; removing one is a spec change, not a cleanup.

- **Fail loud.** No broad try/except that swallows errors to keep things running. Catch specifically, or let it raise. In this codebase that is not only hygiene: the agent framework uses exceptions to drive retries and node-failure fallbacks (Core 21), and catching broadly **silently breaks the orchestration's degradation paths** — a Tier-2 failure that never raises never falls back to the cached Candidate Set. The only sanctioned silent failure is the client tracking script (Core 22, by design).

### Before you believe it worked

- **Never make a test pass by weakening it.** No deleted tests, no loosened assertions, no broadened matchers to get green. **In this project that includes data:** never adjust seed fixtures, capability profiles, or policy values to make an exact-number acceptance assertion pass — the canonical-10 fixture and the derivations in `docs/domains/software-buying/09` are part of the spec. A red test is information; killing the messenger is the one forbidden move.
- **Distrust green.** A passing check is evidence only if it could have failed. Before trusting a PASS, ask what the check would have shown had the claim been false.
- **Sabotage to earn the trust.** After a fix, break the rule, watch the test go red, restore. For a prompt, delete the instruction the eval case depends on and confirm the case fails — if it still passes, the model was already doing it and your instruction is dead weight.

## Working Agreements

- **Session bookkeeping:** `plan.md` is the single source of "where are we" — update its status markers at session end. `handoff.md` gets a new top entry every session (template inside). Read both at session start. **Both are local working files — gitignored, never committed.**
- Work phase-by-phase; report after each phase: what changed and why, in plain language.
- Surface trade-offs and gaps before building around them; never invent a rule the spec doesn't state — extend the spec instead.
- Frontend work must match `ui-design-spec.md` token-for-token; explain frontend concepts briefly when introducing them.
- Keep `README.md` describing SmartReco as a product on its own terms (see Doc Hygiene).
