# SmartReco — Demo Script

A ~10-minute arc through four stories: precision (1) → restraint (4) → commerce & learning (9) → proactive delivery (10). Start from a clean database (`delete ./data`), set `ADMIN_EMAIL`/`ADMIN_PASSWORD` in `.env`, run `uvicorn apps.web.main:app --port 8000`.

## Beat 1 — The Security Evaluator (precision)

1. Register a fresh account. Open **Explore**, search “single sign-on”.
2. Open **Okta** → read the **Security & Compliance** tab (let dwell tick), then **Docs & API**, then **Pricing**. Compare Okta vs Microsoft 365. Repeat a couple of passes — depth, not breadth.
3. Open **For you**: first a clarify response grounded in *your* clicks; within a run or two (runs pace at the policy cooldown, ~3 min) the READY package appears — Okta first, with coverage bars, plain-language ✓/✗, and a persuasive narrative that cites your own research.
4. Side window: **Reasoning Panel** (admin) — watch hypotheses strengthen, the held requirement at 0.48, the stage chip, the trigger log recording every run *and* skip.

## Beat 2 — The Time-Waster (restraint)

1. Second account: skim a dozen products across unrelated categories. No docs, no pricing, no depth.
2. **For you** stays honest: no recommendations, no popularity fallback — a clarifying question instead. Reasoning Panel: one weak Discovery hypothesis, empty requirements. Breadth is not intent.

## Beat 3 — The Buyer (the learning arc)

1. Back as the evaluator: add Okta to cart, check out (demo card `4242 4242 4242 4242`, any future expiry — format-checked only, never stored, always succeeds).
2. Confirmation shows the learning arc: purchase → journey closed → what you valued becomes a prior.
3. Reasoning Panel: journey CLOSED · PURCHASED; long-term traits (Security / Enterprise Evaluation) at 0.30 — labeled as priors that never drive the next journey's ranking.

## Beat 4 — The Digest (proactive delivery)

1. In **Account**: opt into the digest, channel Telegram, paste your chat ID (message the bot once to get it).
2. Trigger the daily window (or wait for 17:00): the active account receives one grounded Telegram digest — recap, top recommendation, one next action. The idle account receives nothing; **Admin → Delivery Records** shows its skip, with the reason. Silence is a feature.

**Closing line:** every number on screen was computed deterministically and is replayable; the AI wrote only the words.
