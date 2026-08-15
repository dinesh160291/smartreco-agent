# UI Design Specification

**Version:** 1.0

**Status:** Locked — approved against the interactive preview (2026-08-08)

This document locks the complete visual system of the SmartReco frontend. The implementation (Jinja2 templates + custom stylesheet) must match these values exactly; any deviation is recorded here first.

**Visual reference of record (approved interactive preview):** https://claude.ai/code/artifact/4cf53315-65ea-47f6-956c-191b47aecb72

Base framework: Pico.css supplies resets and form ergonomics; everything below is the custom layer and **overrides Pico where they conflict**.

---

# 1. Design Tokens

Tokens are CSS custom properties on `:root`. Components reference tokens only — never raw values.

## 1.1 Color — Light theme (default)

| Token | Value | Use |
|---|---|---|
| `--ground` | `#fbfcfd` | Page background |
| `--card` | `#ffffff` | Card / header surfaces |
| `--ink` | `#1b2832` | Primary text |
| `--muted` | `#5c6b7a` | Secondary text |
| `--line` | `#dfe6ec` | Borders, dividers, empty meter track |
| `--accent` | `#0b6e99` | Brand / interactive / filled meters |
| `--accent-ink` | `#ffffff` | Text on accent |
| `--accent-soft` | `#e3f0f7` | Accent tint backgrounds (active nav, chips) |
| `--good` | `#2e7d32` | Positive semantic (SYNCED, ✓ capabilities) |
| `--good-soft` | `#e6f2e7` | Positive tint background |
| `--warn` | `#9a5b00` | Caution semantic (PENDING, Medium priority, internal badge) |
| `--warn-soft` | `#fdf1de` | Caution tint background |
| `--crit` | `#b3261e` | Critical semantic (FAILED, Critical priority, ✗ missing) |
| `--crit-soft` | `#fbe9e7` | Critical tint background |

## 1.2 Color — Dark theme

| Token | Value |
|---|---|
| `--ground` | `#11171d` |
| `--card` | `#181f27` |
| `--ink` | `#e8edf2` |
| `--muted` | `#93a1ae` |
| `--line` | `#2a3540` |
| `--accent` | `#4aa3c7` |
| `--accent-ink` | `#0c1319` |
| `--accent-soft` | `#15303e` |
| `--good` / `--good-soft` | `#7fc783` / `#1c2e1d` |
| `--warn` / `--warn-soft` | `#e0a94f` / `#332815` |
| `--crit` / `--crit-soft` | `#e58f88` / `#3a1f1c` |

## 1.3 Theme mechanics

- Default follows OS: dark tokens redefined under `@media (prefers-color-scheme: dark)`.
- In-app toggle stamps `data-theme="dark"` / `"light"` on `<html>`; `:root[data-theme=…]` token blocks override the media query in **both** directions.
- Components never branch on theme — they read tokens only.
- Semantic colors (good/warn/crit) are distinct from the accent and never substitute for it.

---

# 2. Typography

| Role | Stack |
|---|---|
| UI / body | `system-ui, 'Segoe UI', Roboto, sans-serif` |
| Data / code / IDs | `ui-monospace, 'Cascadia Code', Consolas, monospace` |

No webfonts. System stacks match the SSR/no-build philosophy and render instantly.

## 2.1 Type scale (px / weight / notes)

| Element | Size | Weight | Notes |
|---|---|---|---|
| Page title (h1) | 24 | 700 (default bold) | `letter-spacing: -0.2px` |
| Section heading (h2) | 17 | 700 | 26px top / 10px bottom margin |
| Body | 16 | 400 | `line-height: 1.55` |
| Brand wordmark | 17 | 700 | `letter-spacing: .2px` |
| Page subtitle `.sub` | 14.5 | 400 | color `--muted` |
| Nav / buttons / inputs | 14.5 | 400 (600 active/primary) | |
| Product card name `.n` | 15.5 | 650 | |
| Card body / tab content | 13.5–14.5 | 400 | |
| Card vendor line `.v`, req rows | 12.5–14 | 400 | `--muted` for vendor |
| Pills / badges | 12 | 600 | |
| Field labels | 12.5 | 600 | UPPERCASE, `letter-spacing: .05em`, `--muted` |
| Admin table header | 12 | 400 | UPPERCASE, `letter-spacing: .06em`, `--muted` |
| Mono data (`.mono`, logs, buffer) | 12.5 | 400 | logs `line-height: 2.1` |
| Capability count `.caps`, stage chips | 11.5 | 400–600 | `.caps` in mono, `--accent` |
| Coverage % figure | 14 | 600 | mono, right-aligned, min-width 38px |
| Thumbnail monogram | 14 / 17 / 19 / 24 | 700 | per tile size sm/md/base/lg |

Reading measure: long-form text blocks capped at `max-width: 68ch` (disclaimer 75ch).

---

# 3. Spacing, Radii, Elevation

- **Container:** `max-width: 1060px`, `padding: 0 20px`, centered.
- **App bar:** height 56px, sticky, `--card` surface, 1px `--line` bottom border, content gap 18px.
- **Main:** `padding: 28px 0 64px`.
- **Cards:** `padding: 18px 20px`, radius **10px**, 1px `--line` border, no shadows (flat system — elevation via borders and surface contrast only).
- **Card grids:** `repeat(auto-fill, minmax(230px, 1fr))`, gap **14px**.
- **Product card:** header row (`.phrow`) gap 12px, **margin-bottom 12px** before body text; internal column gap 6px. Cards are column flex at `height: 100%` so they fill their grid row, and the capability count is pushed to the bottom (`margin-top: auto`) so the counts line up across the page instead of floating wherever each description happens to end. The `vendor · category` line clamps to 1 line and the description to 3, keeping header heights equal; clamping is done in CSS rather than by truncating server-side, which cuts mid-word.
- **Radii:** cards 10 · buttons/inputs/fields 8 · pills & chips 20 (full) · thumbs 8 (sm) / 9 (md) / 10 (base) / 12 (lg) · toast 8.
- **Meters:** height 8px, radius 4, track `--line`, fill `--accent`.
- **Two-column layouts** (Reasoning, checkout): `grid-template-columns` 1fr 1fr (Reasoning) / 1.2fr 1fr (checkout), gap 14px; collapse to single column ≤ 760px.

---

# 4. Components

## 4.1 App bar
Brand = 10px accent dot + wordmark. Nav buttons: 14.5px, `--muted`, padding 6×12, radius 6; hover → `--ink`; active → `--accent-soft` bg, `--accent` text, weight 600. Right cluster: event-buffer pill (mono 12.5, `--ground` bg, `--line` border, radius 20, count in `--accent`), cart icon-button with count, theme toggle 🌓 (both: 1px `--line` border, radius 20, padding 5×12).

The buffer pill shows **`count/batch_size`** (e.g. `buffer 3/10`), the denominator read from POL-TRACK-001 so the pill cannot drift from the batch size the client actually uses. A bare count reads as a dead counter; the denominator makes it legible as a queue that flushes at N, which is the architectural point it exists to show (Law 9 — tracking is batched, never one call per event).

The bar itself sets `padding: 0` — the CSS base gives `<header>` 20px of block padding, which against a 56px border-box height leaves a 16px content box and drops the nav and brand below the bottom border. Every item in the right cluster is `inline-flex` with `margin: 0` and `line-height: 1`, and the inner container uses `min-height: 56px` rather than a fixed height. Both are explicit overrides of the CSS base: element types otherwise pick up different default margins and line-box behaviour, so a `<span>`, an `<a>` and a `<button>` sitting side by side drift off the bar's vertical centre, and a nav that wraps on a narrow viewport spills past the bottom border instead of growing the bar.

## 4.2 Buttons
- **Primary:** `--accent` bg, `--accent-ink` text, 14.5/600, padding 8×16, radius 8, no border.
- **Ghost:** transparent bg, 1px `--line` border, `--ink` text, 14/400, padding 7×14, radius 8.
- **Both:** `inline-flex` with centred content and `margin: 0`. Required, not cosmetic — the CSS base applies `margin-bottom` to `[type=submit]` only, so a primary submit button carries one while the ghost buttons beside it do not; in a stretch flex row the ghosts then grow taller while their labels stay pinned to the top of the box. Centring the content also makes an `<a class="btn-ghost">` and a `<button class="btn-ghost">` render identically, which any action row mixing the two depends on.
- **Action rows** (`.actions`): flex, gap 8, `align-items: center` so buttons size to their own content instead of the tallest sibling; nested `<form>` elements are `inline-flex` with `margin: 0`.
- **Focus (all interactive):** `outline: 2px solid var(--accent); outline-offset: 2px` via `:focus-visible`.

## 4.3 Monogram thumbnails
Square, radius per size, weight 700 white initials, background `hsl(H 45% 42%)` where **H = deterministic hash of vendor name** (preview reference hues: Okta 210, Microsoft 16, Google 135, ServiceNow 160, Slack 280, Zapier 25, Box 220, Notion neutral 0/0%/25%). Sizes: sm 34 · md 44 (product cards) · base 52 · lg 64 (product page).

## 4.4 Status pills
12px/600, padding 2.5×10, radius 20. Variants: `good` (SYNCED), `warn` (PENDING, Medium, "Internal · admin only"), `crit` (FAILED, Critical), `acc` (READY, informational). Held-back items (below-threshold requirements): `--line` bg, `--muted` text, row at 55% opacity.

## 4.5 Meters (coverage & confidence)
8px bar as §3; paired numeric always present (never color-only). Coverage rows: grid `34px 1fr 200px` (rank · content · meter+figure), gap 14; ≤760px the meter wraps under content.

## 4.6 Tabs (product page)
Underline style: 2px `--line` baseline; buttons 14.5, `--muted`, padding 9×16; active → `--accent` text, 600, 2px accent underline. Tab panes: 20px top/bottom padding, 68ch measure.

## 4.6b Long-form pane copy (product page)

**Why it exists.** Security & Compliance, Docs & API and Integrations each carry roughly 900–1,600 words. This is not decoration: the Domain Pack's patterns escalate evidence to Strong at 60 seconds of dwell on a pane's topic, and a hundred-word pane can never earn that from a shopper who is genuinely evaluating. Reading time is only a signal when there is something to read. Overview and Pricing are excluded — Overview renders the product record, and Pricing carries the tier cards.

**Composed, never boilerplate.** `apps/web/content.py` builds the sections from the product's own record: its name, vendor, category, and the capabilities it holds, each contributing a section with the capability's business-value narrative and the review angle for its family. One passage repeated across 250 products would make every page's reading time identical and would be obvious the moment a demo clicks through two products.

**Never asserts what the record does not carry.** The scaffolding describes what evaluating this *kind* of product involves — what reviewers ask, what rollouts need — rather than claiming certifications, versions or limits nobody recorded. Where a product lacks a capability the Security pane names the gap plainly; a page that lists only strengths reads as marketing.

**Never indexed.** This copy is presentation and stays out of the products table and the Embedding Document (Core 20, Law 8). Folding ~1,200 words per product into the document would swamp the capability terms retrieval discriminates on. Capability *narratives* are the exception and belong in both: they are part of the record, which is precisely why the panes quote them.

**Dwell topics follow the rules, not the panes.** A pane sets `data-dwell-topic` only when the topic appears in the Domain Pack's `DWELL_TOPICS` — the set of topics some pattern's dwell clause reads. A dwell topic starts a 10s heartbeat writing LOW-signal rows for as long as the pane is open, so on a pane no rule reads it is storage bought for nothing; clicks carry the pane's full signal either way.

In practice that means the **Security pane is the only one with a stopwatch** (Decision #045). Its pattern is the only one whose evidence lives on a single page per product, which is why reading time is allowed to stand in for volume there and nowhere else. Every other pane leaves the attribute empty; their clicks carry the full signal regardless. Turning a topic on is a Domain Pack change — add the dwell clause and the constant, and the surfaces follow with no edit here.

**Rendering.** Sections render as `(heading, [paragraphs])` through the `longform` macro: `h2.lf-h` at 15/600, paragraphs at the pane's 68ch measure. Composing the sections and rendering them are separate failures — `tests/test_product_longform.py` asserts both, because the unit tests once passed against a page showing nothing when the view dict was missing its keys.

## 4.6a Pricing tiers (product page)

**Layout.** Two equal cards side by side, centred. The pricing pane sets `max-width: none` — the 68ch pane measure is a reading width for prose, and a price comparison is not prose — and the `.tiers` row is capped at 720 and centred with `margin-inline: auto`, giving ~351px cards; the pane's own intro line is centred to match. Row gap 18, `align-items: stretch`; each `.tier` is `flex: 1 1 0` (basis 0, so the row divides evenly regardless of copy length) as a column flex container, padding 16, 1px `--line` border, radius 10, `--card` background. Below 620px the row wraps to one full-width column.

**Card contents, in order:** plan name 12.5/600 uppercase `--muted` · price 24/700 `--ink` with the unit on its own line 12.5 `--muted` · one-line blurb 13.5 `--muted` · five feature bullets 13.5 · CTA. The CTA carries `margin-top: auto` so both buttons sit on the same baseline whatever the lists above them do, plus an explicit `height: 40px` with `box-sizing: border-box` — §4.2's `.btn` and `.btn-ghost` differ in padding and border, which otherwise leaves the two cards' buttons a pixel out of line.

**The two CTAs must agree with the price above them.** Personal is a paid plan, so its control is a *trial* of that plan — "Start 14-day trial", emitting `TRIAL_STARTED`, with the first bullet stating what happens when the trial ends. A bare "Start free" under a monthly price reads as a second, cheaper offer and makes the card contradict itself. Enterprise has no self-serve price, so its control is "Contact sales".

**Selection.** The whole card is clickable and takes `.selected` (accent border plus inset accent ring); hover previews it with the accent border alone.

**Two tiers only — Personal and Enterprise.** These are the discriminating axis for buying intent; a middle "Team" tier blurs exactly the signal the tab exists to capture. The Personal price is presentation-only demo copy derived deterministically from the product id (`pages._personal_price`) — it is deliberately not a product record field, so it can never reach the Embedding Document or any ranking input.

**Capabilities are never gated by tier.** Capability profiles are the substrate of coverage ranking; making them tier-dependent would make "does this product satisfy this requirement?" depend on which plan the shopper happened to open, and would reopen the pinned acceptance numbers.

**Behaviour (Decision #044).** Opening the Pricing tab emits `PRICING_VIEWED` carrying only `product_id`: it records that pricing was read, which is true, and asserts no intent. The tier arrives only from the plan the shopper engages with — `tier: "personal"` or `tier: "enterprise"` — carried by the card itself. Because the tracking client fires only the *nearest* `data-track` ancestor, a click landing straight on a card's CTA would record the CTA and lose the tier, so `app.js` emits the card's tier event alongside it. The Enterprise card carries the sole `DEMO_REQUESTED` surface ("Contact sales"), which confirms inline that the team will follow up at the account email; it collects no personal data.

## 4.7 Forms
Inputs: 1px `--line` border, radius 8, padding 9–10×12–14, `--card`/`--ground` bg, inherit font. Labels per §2.1. Field stack gap 5px, 12px between fields; paired fields (expiry/CVC) in 2-col grid gap 12.

## 4.7a Catalog Search (Explore)

**Layout.** One row, gap 10, margin-bottom 14: the input takes the remaining width (`flex: 1`), the primary button keeps its natural §4.2 size. Both need explicit `width: auto` — the CSS base sets `width: 100%` on inputs and buttons, which otherwise splits the row in half. Placeholder: "Search products, capabilities, categories…".

**Behaviour.** Deterministic and model-free: the same query always returns the same products in the same order, and the ordering is explainable without inspecting a model. This is *not* the Semantic Retrieval Engine — Chapter 20's vector index answers "what does this person's behaviour imply?", while the search box answers "what did this person ask for". Reusing the index here would be a new use of that seam and requires its own decision. **That decision is drafted in `docs/implementation/semantic-search-spec.md` — proposed, not implemented.** It reuses the index only on a *zero-result* query, so nothing specified in this section changes for any query that returns something today; until it ships, the behaviour below is complete.

**Fields searched**, in descending rank weight: product name · **capability names** · category · vendor · description and business purpose. Capability names are searched because they are what a product *does*; searching prose alone hides a product from a query naming a capability it holds.

**Matching.** Case- and punctuation-insensitive: every run of non-alphanumeric characters normalizes to a single space, so "Single Sign-On", "single sign on" and "single  sign--on" are one query. Query tokens are ANDed — every token must match somewhere — and a token matches as a **prefix** of any word in a field, so "provision" finds "SCIM Provisioning". Tokens shorter than 3 characters must match a whole word instead; without that floor the "on" in "sign-on" prefix-matches names like "OneLogin" at full name weight and dominates the ranking.

**Ranking.** Field weight → **domain completeness** → capability count → name.

A capability query matches every product holding that capability at identical weight, so the tiebreak decides the order — and which tiebreak is chosen decides whether specialists or suites surface. The choice is a normalization one, and each option carries a bias: dividing by nothing ranks on raw capability count and puts the broadest suite on top of every search; dividing by the *product's* own capability count rewards being thin, so three-capability distractors win. Dividing by the **searched domain's** size does neither — a product cannot inflate the measure by being large or by being small, only by genuinely covering the area asked about. Domain completeness is therefore `capabilities held in the matched domain ÷ capabilities that domain contains`, taken from the capability taxonomy.

This is computed from declared capabilities and is **not popularity or editorial prominence** — the platform refuses popularity-based ranking on its recommendation surface (§6), and the search box must not reinstate it. A consequence worth stating: a well-known vendor whose product is broad will rank below a narrower product that covers the searched domain more completely, and a product holding the searched capability incidentally (an identity product that also logs, under a query for audit logging) ranks below genuine compliance products. Both are intended.

**Acronyms.** Buyer shorthand (sso, mfa, saml, iam, rbac, dlp, siem, cicd) expands through the Domain Pack's alias table — **`docs/domains/software-buying/10-capability-catalog.md` § Buyer Shorthand** is the authority; this screen only consumes it. Expansion is retrieval-side only: the `SEARCH` event records what the shopper actually typed, never the expansion, so the reasoning engines never learn vocabulary the user did not use.

**Result count.** A 13px `--muted` line sits between the chips and the grid, `role="status"` so screen readers hear it change. Unfiltered it reads "N products"; filtered, "M of N products" plus the query in curly quotes and/or the category. It tells a shopper whether a search narrowed anything, and separates a genuine zero-result search from a page that failed to load. Zero results additionally render an empty-state line suggesting a capability or a category chip — never a fallback list of unrelated products, which would contradict the platform's refusal to guess (§6).

## 4.8 Category chips
13px, `--card` bg, 1px `--line`, `--muted`, padding 5×13, radius 20; active → accent border/text + `--accent-soft` bg.

## 4.9 Stage progression chips
11.5px, padding 3×9, radius 14. States: future = `--ground` bg / `--line` border / `--muted`; done = accent border + accent text; current = solid `--accent` bg, `--accent-ink`, 600.

## 4.10 Admin table
CSS grid rows `90px 1fr 130px 1fr 110px`, gap 12, row padding 10×4; header per §2.1; 1px `--line` row dividers; horizontal scroll container (`overflow-x: auto`, min-width 640px) — page never scrolls sideways.

## 4.11 Trigger log
Mono 12.5, line-height 2.1, `nowrap` + own scroll container. Timestamps `--muted`; RUN `--good`; SKIP `--warn`.

## 4.12 Toast
Fixed bottom-right 18px, inverted surface (`--ink` bg / `--ground` text), mono 12.5, padding 9×15, radius 8, opacity .94, 2.6s auto-dismiss, 200ms fade+8px rise (suppressed under `prefers-reduced-motion`), `role="status"`, max-width 85vw.

## 4.13 Notices
Demo-checkout notice: 12.5px, `--warn` text on `--warn-soft`, radius 8, padding 8×12. Learning-arc block (order confirmation): mono 12.5, line-height 2, `--ground` bg, 1px `--line`, radius 8, padding 12×16, max-width 480px; chain lines in `--good`, closing line `--muted`.

## 4.14 Motion
Only: card border-color hover (150ms), toast (200ms), nav/tab state changes (instant). All transitions removed under `prefers-reduced-motion: reduce`. No scroll animations, no parallax, no loaders beyond htmx swaps.

---

# 5. Screen Inventory (locked layouts)

| Screen | Audience | Key locked details |
|---|---|---|
| Explore | Shopper | H1 "Find the right software", subtitle "Browse the catalog — every view, search, and click quietly teaches SmartReco what you need." → search row (input + primary button) → category chips → result count §4.7a → card grid §3; card = header-row pattern §4.3/§4.4 |
| Compare | Shopper | Picker row: two product selects + primary button, all natural width (the base stylesheet's `width: 100%` on selects and buttons must be overridden). Options are sorted **case-insensitively** by display name — a raw column sort is byte order, filing lowercase-initial names after `Z`. Each compared product's header row is a link to its own page: without one the only route back is Explore plus typing the name, which emits a `SEARCH` event the shopper never intended and feeds search-term patterns with manufactured evidence. Navigation must not fabricate behavioural signal |
| Product detail | Shopper | Breadcrumb 13px `--muted` → lg thumb + title + vendor·category·price subtitle → actions right (Compare ghost · Free trial ghost · Add to cart primary) → 5 tabs: Overview / Pricing / Security & Compliance / Docs & API / Integrations. Pricing pane holds the two tier cards §4.6a |
| For you | Shopper | Status line (refresh recency + trigger + READY pill) → AAR card with 3px accent left border: persuasive narrative → ranked coverage rows → expandable plain-language "why" → ownership disclaimer above 1px top border |
| Cart & checkout | Shopper | 1.2fr/1fr grid: cart list (sm thumbs) · checkout card with demo notice + fake card form; confirmation = centered card, 40px ✅, order line, learning-arc block §4.13 |
| Admin catalog | Admin | Header row with description + "+ Add product" primary → table §4.10 with Sync pills → reconciliation note |
| Reasoning Panel | Admin-gated | "Internal · admin only" warn pill in title; user-selector line; 2-col: journey card (stage chips §4.9, hypothesis meters) · requirements card (priority pills, held rows) + trigger-log card |

---

# 6. Copy & Vocabulary Rules (binding)

1. **No canonical IDs on shopper surfaces** (CAP/REQ/PROD/BC/BP). Display names only. IDs appear exclusively on Admin and Reasoning Panel.
2. Recommendation "why" lines are plain language: `✓ Single Sign-On`, `✗ Information governance … partially covered`.
3. Every AAR surface carries the ownership disclaimer: *"Rankings, match scores, and coverage are computed deterministically… AI wrote the words — not the numbers."*
4. Checkout carries the demo notice verbatim: *"Demo checkout — card details are format-checked only, never stored, and always succeed."*
5. Persuasive copy tone per the Grounded Persuasion Mandate (Core 09): urgent, personal, grounded — never invented social proof, scarcity, or discounts.
6. Numbers that stack vertically (coverage %, confidences) use tabular alignment via the mono face.

---

# 7. Accessibility (locked)

- Visible `:focus-visible` state on every interactive element (§4.2).
- Status never encoded by color alone — pills carry text, meters carry figures, log states carry words.
- Toast uses `role="status"`; theme/cart buttons carry `aria-label`s.
- Both themes maintain legible contrast for text tokens on their grounds; semantic tints (`*-soft`) are backgrounds for their own semantic text color only.
- `prefers-reduced-motion` honored globally.

---

# 8. Change Control

This spec changes only by editing this document first, then the implementation. The preview artifact is regenerated to match on any visual change. Token additions are appended to §1; new components to §4.

---
