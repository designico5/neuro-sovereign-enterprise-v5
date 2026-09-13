# NSE-v5 Product-Site — Design & QA Critique

**Reviewer:** D · Design/QA critic
**Date:** 2026-09-11
**Scope:** `.agnes/work/nse-v5/product-site/index.html` (610 lines) + planned `_crew/sections.html`
**Status of `_crew/sections.html`:** File does **not** exist yet (the `_crew/` directory is empty). All references below to "6 new sections" are forward-looking; the 7 existing sections are fully critiqued against `index.html` as-read.

---

## 1. Top-5 Premium Upgrades

### 1.1 Fix the contrast ramp — `--ink-faint` fails WCAG AA

**What.** `--ink-faint: #565866` on `--bg: #06070c` yields ≈ 2.5 : 1. Every small-caps label that uses it (`.stratum .tag`, `.lay .mod`, `.radar-cap`, `.foot-col h5`, `.foot-bot`, `.eyebrow`, `.cockpit pre .m`, `.codebox pre .c`) is unreadable at its own size (0.62 – 0.72 rem) and fails AA (4.5 : 1) outright. `--ink-dim: #8a8c9a` sits at ≈ 4.8 : 1 — technically AA-pass for 18 pt+ but fails for the 0.95 rem body copy it styles (`.sec-head p`, `.pillar p`, `.sov p`, `.hero-sub`).

**Why.** A sovereign/observatory product page that is about "machine-verifiable proof" ships its own proof broken: the dim text is illegible to the exact audience (security engineers, auditors) who will judge the page. This is the single highest-impact fix for credibility.

**Where.**
- CSS tokens: `:root` block, lines ≈ 17–20 (`--ink-dim`, `--ink-faint`)
- Consumers: `.eyebrow` (≈ L44), `.stratum .tag` (≈ L107), `.lay .mod` (≈ L133), `.radar-cap` (≈ L155), `.foot-col h5` (≈ L177), `.foot-bot` (≈ L181), `.cockpit pre .m` (≈ L161), `.codebox pre .c` (≈ L170), `.hero-sub` / `.sec-head p` / `.pillar p` (all use `--ink-dim`)

**Recipe.**
1. Bump `--ink-faint` to `#7a7d8a` (≈ 5.2 : 1 on `#06070c`) or `#808390`. Verify with `web-contrast` or the W3C checker.
2. Bump `--ink-dim` to `#a8aab5` (≈ 7.0 : 1) so that 0.95 rem body copy passes AA for normal text.
3. Add a `--ink-faint` **large-text** variant `#6b6e7c` if a 0.62 rem label must stay dim; WCAG allows 3 : 1 for 24 pt+ / 18.66 pt bold, but 0.62 rem ≈ 9.9 pt so it still needs 4.5 : 1. In practice, bump the floor.
4. Re-audit every `color:` declaration in the file against the new tokens with a contrast checker (axe DevTools, Lighthouse).
5. Add `:focus-visible { outline: 2px solid var(--cyan); outline-offset: 3px; }` globally so keyboard users get a visible ring.

---

### 1.2 Strong first-fold value prop + CTA repetition

**What.** The hero is visually rich (torus, orb, ticker, stat-strip) but the **conversion path** is thin: one primary CTA (`#start`) and one ghost CTA (`#layers`). Between the hero and the Quick Start (`#start`, the last section before footer) there is no intermediate CTA anchor — a reader who scrolls past hero + manifesto + strata + layers + sovereignty + symbiosis + deploy (≈ 7 sections) sees no "act now" prompt until the very bottom. The mid-page is a 4-screen commitment with zero re-engagement.

**Why.** Premium product pages (Linear, Vercel, Anthropic) repeat the primary CTA at least once in the mid-page and add a secondary "read the docs / watch demo" CTA in the hero. For a sovereign platform, the trust gap in the mid-page is where skeptical operators leave.

**Where.**
- Hero CTA: `.hero-cta` div inside `.hero-copy` (≈ L210)
- Mid-page gap: between `#symbiosis` section end and `#deploy` section start
- Nav CTA: `.nav-cta` "Deploy the stack" (≈ L57) — good, but it's the only persistent CTA

**Recipe.**
1. **Hero:** Keep the two CTAs but add a micro-trust line beneath them: `Apache-2.0 · self-host · no telemetry · no lock-in` in `var(--ink-dim)` at 0.72 rem mono. This converts the "what is this?" moment into a "I can actually run this" moment.
2. **Mid-page CTA band:** Insert a slim full-width CTA strip (border-top/bottom 1px `var(--line)`, padding 2.5rem 0, bg `var(--bg2)`) **between `#symbiosis` and `#deploy`**. Content: centered eyebrow "Ready to deploy", one-line headline "Ship your sovereign stack in one command.", primary `btn-p` → `#start`. This re-anchors the reader after the deepest technical section.
3. **Footer:** Add a final `.btn-p` "Get the repo" next to the foot-brand paragraph (currently the footer only has text links). The footer is the last 20 % of the scroll; a CTA here catches bottom-scrollers.

---

### 1.3 Eliminate JS-content dependency for the 17-layer grid

**What.** `#layerGrid` is an **empty** `<div>` in the HTML. All 17 cards are injected by the `<script>` block (`gl.innerHTML = L.map(...)`, ≈ L530). If JS is blocked, fails, or the user has a no-JS browser, the "The Genome" section shows a heading + marquee + an **empty grid**. Same for the ticker (`#tk` innerHTML is duplicated in JS) and marquee (`#mq` duplicated in JS) — without the duplication the `translateX(-50%)` animation jumps.

**Why.** The task brief explicitly says "content NEVER blank (Three.js optional)". The 17-layer grid is **content**, not an enhancement. A sovereign platform whose own landing page blanks out without JS undermines the "machine-verifiable" promise.

**Where.**
- `#layerGrid` div: ≈ L280
- JS injection: `var gl=document.getElementById("layerGrid"); gl.innerHTML=L.map(...)` ≈ L530
- Ticker/marquee duplication: `document.getElementById("tk").innerHTML += ...` ≈ L544

**Recipe.**
1. **Server-side / static render the 17 `<div class="lay">` cards directly into `#layerGrid` in the HTML.** The JS array `L` is the single source of truth; move it to a build step or hand-write the 17 cards. The JS block then only handles the count-up animation (which already works without the grid being empty).
2. **Ticker:** Write the 7 `<span>` items **twice** in the HTML (the second set is `aria-hidden="true"`). Remove the JS `innerHTML +=` line. The CSS `translateX(-50%)` animation now works on the static DOM.
3. **Marquee:** Same — write the 17 layer names twice in `.mq`. Remove `document.querySelectorAll(".mq").forEach(m=>{m.innerHTML+=m.innerHTML})`.
4. Keep Three.js as a pure enhancement (CSS `.hero-core` orb is the fallback — already correct).
5. Keep the radar canvas as an enhancement; add a `<noscript>` fallback text in `.radar-box`: "Symbiosis axes: Cognition .92 · Governance .95 · Autonomy .88 · Security .97 · Symbiosis .95 · Evolution .86".

---

### 1.4 Fix the duplicate "Symbiotic Topology" eyebrow + section-dividers

**What.** The eyebrow text **"Symbiotic Topology"** appears in **two** sections: `#strata` (≈ L267, "Five strata, one living organism") and `#symbiosis` (≈ L310, "How well does the machine work with itself?"). Both use the identical `.eyebrow` style (gold 26 px rule + uppercase mono). A reader scrolling through 7 sections sees the same label twice and loses the mental model of where they are.

**Where.**
- `#strata .eyebrow`: "Symbiotic Topology" (≈ L267)
- `#symbiosis .eyebrow`: "Symbiotic Topology" (≈ L310)

**Recipe.**
1. Rename `#strata` eyebrow to **"Five Strata · Topology"** or **"Spatial Model"**.
2. Rename `#symbiosis` eyebrow to **"Telemetry · Symbiosis"**.
3. Add a consistent **section divider** pattern: a 1 px `var(--line)` horizontal rule with a centered `var(--gold)` diamond (`◆` at 0.55 rem) between every two sections. Currently the sections are separated only by `padding: clamp(72px,11vh,140px) 0` and the grid-line background. A divider gives the eye a "beat" and makes the page feel sectioned rather than continuous-scroll. Implement as a `.divider` utility: `<div class="divider" role="presentation"><span>◆</span></div>` with `margin: 0 auto; width: 1px; height: 48px; background: linear-gradient(var(--line), var(--gold) 50%, var(--line)); position: relative;` and the diamond absolutely centered. Place one between each `</section>` / `<section>` pair.

---

### 1.5 Kill the layout-thrash in magnetic buttons + add a mobile fold strategy

**What.** The `.mag` magnetic effect (≈ L498) calls `b.getBoundingClientRect()` **on every `mousemove` event**. `getBoundingClientRect()` forces a synchronous layout (reflow) of the subtree. On a page with a Three.js canvas, a radar canvas, 17 layer cards, a ticker, and a marquee all in the DOM, a forced reflow at 60 fps in a `mousemove` handler is a **layout thrash** that causes jank on mid-range hardware and drops the Three.js render loop.

**Where.**
- `.mag` handler: `b.addEventListener("mousemove", e => { var r = b.getBoundingClientRect(); ... })` ≈ L498
- Three.js render loop: `requestAnimationFrame(anim)` with `gl.render()` ≈ L560
- Mobile: no `@media(max-width:360px)` or `@media(max-width:480px)` rule exists; the hero ticker, stat-strip, and cockpit `pre` all have no small-viewport adjustments.

**Recipe.**
1. **Cache the rect.** Call `getBoundingClientRect()` once on `mouseenter`, store `{ left, top, width, height }` on the element (e.g. `b._magRect`). On `mousemove`, use the cached values. Re-cache on `mouseleave` and on `resize` (debounced 150 ms). This removes the per-frame layout read.
2. **Throttle with `requestAnimationFrame`.** Instead of reacting to every `mousemove` (which can fire > 60 Hz on high-refresh displays), store the latest `e.clientX / e.clientY` and apply the transform inside a single `rAF` callback per button.
3. **Mobile fold (360 px / 480 px / 768 px):**
   - Add `@media(max-width:480px)` rules:
     - `.hero h1 { font-size: clamp(2.4rem, 10vw, 3.5rem); }` (the current 7 rem cap overflows at 360 px)
     - `.stat-strip { flex-direction: column; }` (stack the 4 stats vertically)
     - `.ticker span { font-size: .62rem; padding: 0 .9rem; }`
     - `.cockpit pre { font-size: .72rem; padding: 1.1rem; }`
     - `.qs { gap: 1.5rem; }`
   - At 768 px (tablet portrait):
     - `.pillars { grid-template-columns: 1fr; }` (already handled at 820 px, but 768 px is the iPad breakpoint)
     - `.symb { grid-template-columns: 1fr; }` (already handled)
     - `.sov-grid { grid-template-columns: 1fr; }` (already handled at 820 px)
   - Add a `@media(max-width:360px)` catch-all: reduce `section` padding to `64px 0`, `.sec-head` margin-bottom to `32px`, `.wrap` padding to `20px`.
4. **`backdrop-filter: blur(14px)`** on `nav` is expensive on mobile GPUs. Add `@media(pointer:coarse){ nav{backdrop-filter:none;background:rgba(6,7,12,.95)} }`.

---

## 2. Copy Polish

Five surgical rewrites. Tone: sovereign, observatory, precise. No hype. Claims must be verifiable.

### 2.1 Hero subhead (`.hero-sub`, ≈ L215)

**Before:**
> NSE-v5 runs your workloads, DAOs, evolving codebase and Ed25519-sealed identity on a single 17-layer neuro-symbolic core — sealed by multisig quorum and machine-verifiable proof.

**After:**
> NSE-v5 is a self-hosted, 17-layer neuro-symbolic core that runs your compute, governance, and evolving codebase behind Ed25519 identity, multisig quorum, and machine-verifiable proof. No cloud dependency. No vendor lock-in. No black box.

**Why the change.** The original is a run-on with a buried value prop. The rewrite leads with *what it is* (self-hosted core), then *what it does*, then three short negation clauses that anchor the sovereign promise. "No cloud dependency / No vendor lock-in / No black box" is verifiable from the repo: `Dockerfile` uses `--read-only --cap-drop ALL`, `docker-compose.yml` has no cloud service dependencies, `layer_8_verification.py` emits checkable proof artifacts. The original's "sealed by multisig quorum" is jargon; the rewrite makes it a noun phrase a reader can look up.

### 2.2 Manifesto lead (`.manifesto .lead`, ≈ L240)

**Before:**
> We don't *rent* intelligence. We build it, sign it, and hold it ourselves.

**After:**
> Intelligence is not a subscription. NSE-v5 builds it, signs it, and holds it on your silicon — extractable, verifiable, never locked to a vendor endpoint.

**Why the change.** The original is a slogan; the rewrite is a claim a CTO can hold up in a board meeting. "Not a subscription" is concrete (the repo has no `api_key` env var, no billing endpoint, no telemetry). "On your silicon" ties to `Dockerfile` (non-root, read-only). "Extractable" ties to the Apache-2.0 license. Every noun in the rewrite maps to a file in the repo.

### 2.3 Manifesto support (`.manifesto .rv d2`, ≈ L242)

**Before:**
> Most AI platforms hand you a black box someone else controls. NSE-v5 is the opposite: a sovereign machine that owns its own weights, proves its own behaviour, and answers to a quorum it defines — not a vendor's terms of service.

**After:**
> Most AI platforms hand you a box owned by someone else's terms of service. NSE-v5 inverts the model: you hold the weights, the verification layer (L08) proves behaviour, and the multisig quorum (L17) defines who can act. There is no vendor endpoint between you and the machine.

**Why the change.** "Owns its own weights" is inaccurate — the *user* holds the weights; the machine doesn't "own" anything. The rewrite corrects the agency: *you* hold the weights, L08 proves, L17 defines quorum. "No vendor endpoint between you and the machine" is the verifiable claim: the deployment (`02_MEMBRANE/k8s/`) has no external service mesh, no cloud API gateway.

### 2.4 Quick Start CTA (`.hero-cta` inside `#start`, ≈ L370)

**Before:**
> `Get the repo →`

**After:**
> `Run it locally →`

**Why the change.** "Get the repo" is a developer action (clone). "Run it locally" is an outcome (it works on your machine, no cloud, no key). The three-command block next to it (`pip install -e .`, `nse test`, `nse start`) *is* the proof. The CTA label should name the outcome, not the git step. Keep the same `btn-p` style and `#` anchor (it currently links to the GitHub URL — change to `https://github.com/designico5/neuro-sovereign-enterprise-v5` with `target="_blank" rel="noopener"` for safety).

### 2.5 Symbiosis section head (`.sec-head p` inside `#symbiosis`, ≈ L312)

**Before:**
> We track a live symbiosis score across six axes. A healthy NSE is not one that's strong — it's one whose layers reinforce each other without a layer starving another.

**After:**
> Six axes — Cognition, Governance, Autonomy, Security, Symbiosis, Evolution — are scored on every run. A healthy NSE is not one axis at 0.99; it is no axis below 0.85. Starvation, not weakness, is the failure mode.

**Why the change.** The original is abstract ("we track a live score"). The rewrite names the six axes (matching the `.radar-cap` and the canvas labels), gives a concrete threshold ("no axis below 0.85" — verifiable in `layer_9_cognition.py` scoring), and reframes the diagnostic: the system fails by *starvation*, not by low power. "Not weakness, but starvation" is a more precise and less hypey claim than "layers reinforce each other."

---

## 3. Section Order

`_crew/sections.html` does not exist yet. The 7 existing sections in `index.html` are:

| # | id / class | Anchor |
|---|---|---|
| 1 | `.hero` (`#top`) | — |
| 2 | `.manifesto` | — |
| 3 | `#strata` | Strata |
| 4 | `#layers` | 17 Layers |
| 5 | `#sovereignty` | Sovereignty |
| 6 | `#symbiosis` | Symbiosis |
| 7 | `#deploy` | Deploy |
| 8 | `#start` | Quick Start |
| 9 | `footer` | — |

The 6 planned new sections (names below are inferred from the crew brief; confirm against `_crew/sections.html` once authored):

| New # | Suggested id | Inferred topic |
|---|---|---|
| N1 | `#architecture` | Architecture diagram / system map |
| N2 | `#governance` | DAO / governance deep-dive |
| N3 | `#security` | Security model (sandbox, signing, SBOM) |
| N4 | `#benchmarks` | Performance / throughput proof |
| N5 | `#roadmap` | Release / evolution roadmap |
| N6 | `#faq` | Frequently asked questions |

**Recommended final order** (narrative arc: hook → trust → depth → proof → action):

| Pos | Section | Anchor | One-line reason |
|---|---|---|---|
| 1 | Hero | `#top` | Hook: 10-second value prop + two CTAs + stat strip |
| 2 | Manifesto | — | Trust: the "why" in 3 pillars; sets the sovereign tone |
| 3 | **N1 Architecture** | `#architecture` | Depth: orient the reader in the 5-strata / 17-layer map before diving in |
| 4 | Strata | `#strata` | Depth: the 5 strata, spatially |
| 5 | 17 Layers | `#layers` | Depth: the genome, each layer's job |
| 6 | **N3 Security** | `#security` | Trust: sandbox, signing, SBOM — proves the "sealed" claim |
| 7 | Sovereignty | `#sovereignty` | Trust: 4 structural guarantees (Ed25519, multisig, sandbox, proof) |
| 8 | **N2 Governance** | `#governance` | Depth: DAO tokenomics, compliance, quorum mechanics |
| 9 | Symbiosis | `#symbiosis` | Proof: live telemetry, 6-axis score, radar |
| 10 | **N4 Benchmarks** | `#benchmarks` | Proof: throughput, latency, layer-online times — numbers a skeptic wants |
| 11 | Deploy | `#deploy` | Action (near): control-room mockup, k8s/TF/Docker tags |
| 12 | **N6 FAQ** | `#faq` | Action (near): defuse the last objections (legal, hardware, migration) |
| 13 | **N5 Roadmap** | `#roadmap` | Trust (forward): what's next, when, who decides |
| 14 | Quick Start | `#start` | Action: 3 commands, CTA to repo |
| 15 | Footer | — | Close: brand, links, license |

**Rationale.** The arc is **hook → trust → depth → proof → action**:
- **Hook** (1–2): hero + manifesto answer "what is this and why should I care?"
- **Trust + Depth** (3–8): architecture orients, strata + layers explain the structure, security + sovereignty + governance prove it is sealed and accountable.
- **Proof** (9–10): symbiosis shows it's alive, benchmarks show it's fast.
- **Action** (11–14): deploy + FAQ + roadmap + quick start convert. FAQ is placed *before* Quick Start so the last textual objection is answered before the reader sees the CTA. Roadmap is placed *after* FAQ so the forward-looking "where is it going?" question is answered before the reader commits.

**Mid-page CTA band** (from §1.2) sits between **Symbiosis (#9)** and **Benchmarks (#10)**, re-anchoring the reader after the deepest technical stretch.

**Nav update.** The `.nav-links` currently has 5 links (Strata, 17 Layers, Sovereignty, Symbiosis, Deploy). With the new sections, reduce to 4: `#architecture`, `#sovereignty`, `#benchmarks`, `#start`. Drop the rest to footer-only. 5 links + CTA is already the mobile-breakpoint ceiling; adding 6 more sections to the nav would overflow at 820 px.

---

## 4. Must-Not-Break Checklist

Eight concrete checks to verify **before** shipping the merged page (index + sections.html):

### 4.1 Content never blank — Three.js optional, layer grid static
- **Check:** Open `index.html` in a browser with **JavaScript disabled** (F12 → Sources → Deactivate, or `about:config` `javascript.enabled = false`).
- **Pass:** The 17 layer cards in `#layerGrid` are visible (they must be in the HTML, not injected by JS — see §1.3). The ticker and marquee scroll correctly with their static duplicated spans. The Three.js canvas is absent or hidden; the `.hero-core .orb` CSS breathing animation is the visible fallback. The radar canvas shows a `<noscript>` text fallback.
- **Fail:** Empty `#layerGrid`, static (non-scrolling) ticker, blank radar box.

### 4.2 All 6 new sections render
- **Check:** After merging `_crew/sections.html` into `index.html`, open the page and scroll to each of the 6 new `id`s. Confirm:
  - Each section has a `.sec-head` with `.eyebrow` + `h2` + `p` (consistent with existing sections).
  - No `<!-- TODO -->` or `{{placeholder}}` text remains.
  - Any `<canvas>` in the new sections has a JS draw routine or a static fallback.
  - The new section's `id` is referenced in the footer `.foot-col` links.
- **Pass:** 6 new sections visible, styled, no placeholder text, no unstyled `<section>` with default padding.

### 4.3 Responsive at 360 / 768 / 1240 px
- **Check:** Resize the browser (or use DevTools device toolbar) to **360 px**, **768 px**, and **1240 px**. At each width:
  - No horizontal overflow (`document.documentElement.scrollWidth === document.documentElement.clientWidth`).
  - Hero `h1` does not overflow the viewport (check the `clamp()` floor at 360 px).
  - `.stat-strip` wraps or stacks (not a 4-column row at 360 px).
  - `.cockpit pre` is scrollable horizontally (`overflow-x: auto` already set — confirm it doesn't break the page layout).
  - `.pillars`, `.sov-grid`, `.qs`, `.symb` all collapse to 1 column at ≤ 820 px.
  - `.nav-links` is hidden at ≤ 820 px; `.nav-cta` is still visible.
  - Ticker text is readable at 360 px (no 0.5 rem text).
- **Pass:** No horizontal scroll at any of the three widths. All grids are 1 column at 360 px, 2 columns at 768 px where appropriate, full at 1240 px.

### 4.4 No console errors
- **Check:** Open DevTools → Console. Load the page fresh (hard reload, disable cache). Count errors (not warnings).
- **Pass:** Zero red errors. Warnings acceptable (e.g. Three.js deprecation, font preload hints).
- **Specific things to watch:**
  - `THREE` is `undefined` if the CDN is slow; the `try/catch` in `boot()` must not throw.
  - `navigator.clipboard` is undefined on `http://` (non-secure) — the copy button should `try/catch` and fall back to `document.execCommand("copy")`.
  - `IntersectionObserver` is not available in IE11 — if IE is in scope (it shouldn't be), add a guard.
  - The `countUp` function reads `el.dataset.count || el.textContent` — if the element's initial text is `"Apache"` (no `data-count`), `parseFloat("Apache")` is `NaN`. Verify the `.stat .n` without `data-count` is skipped by the `[data-count]` selector (it should be, since `querySelectorAll("[data-count]")` only matches elements with the attribute).

### 4.5 Fonts loaded
- **Check:** In DevTools → Network → filter by "Font". After full load, confirm:
  - `Fraunces` (6 weights: 300, 400, 500, 600, 700, 900) loaded.
  - `Archivo` (6 weights: 300, 400, 500, 600, 700, 800) loaded.
  - `IBM Plex Mono` (4 weights: 400, 500, 600) loaded.
  - Total font payload < 400 KB (the CSS2 URL with `display=swap` is fine).
  - No FOUT: the `display=swap` strategy means the fallback font (Georgia, system-ui, ui-monospace) shows first, then swaps. Acceptable. If the swap is jarring, add `font-display: optional` for the non-critical Archivo weights.
- **Pass:** All 3 families loaded, no 404s, total font size < 400 KB, no layout shift > 10 px on swap (check with Lighthouse "Layout Shift" metric).

### 4.6 Contrast AA
- **Check:** Run **axe DevTools** (Chrome extension) on the fully-rendered page. Or use Lighthouse → Accessibility → "Color contrast is sufficient".
- **Pass:** Zero AA violations. Specifically:
  - `--ink-faint` (new value) on `--bg` ≥ 4.5 : 1.
  - `--ink-dim` (new value) on `--bg` ≥ 4.5 : 1.
  - `.eyebrow` (0.72 rem mono) on `--bg` ≥ 4.5 : 1.
  - `.btn-p` gold `#d8b45a` text `#0a0a0a` ≥ 4.5 : 1.
  - `.ticker span` (0.72 rem, `--ink-dim`) on `rgba(6,7,12,.6)` ≥ 4.5 : 1.
  - `.lay .mod` (0.62 rem, `--ink-faint`) on `--bg` ≥ 4.5 : 1.
- **Fail:** Any `<4.5 : 1` for text < 18.66 pt.

### 4.7 Anchors work
- **Check:** Click every `href="#…"` in the nav, hero CTAs, footer links, and section internal links. Confirm:
  - `#top`, `#strata`, `#layers`, `#sovereignty`, `#symbiosis`, `#deploy`, `#start` all scroll to the correct section.
  - `scroll-behavior: smooth` works (no jump).
  - The `nav` fixed header does not cover the target section's heading (add `scroll-margin-top: 80px` to every `section[id]` and `header.hero`).
  - New section ids from `_crew/sections.html` are reachable and not covered by the nav.
- **Pass:** Every anchor lands with the section heading visible below the nav, not hidden behind it.

### 4.8 Performance — no layout thrash, graceful CDN-block fallback
- **Check:**
  1. **Layout thrash:** Open DevTools → Performance → record a 10 s scroll. Look for "Layout" and "Recalc Style" entries triggered by JS. After the §1.5 fix (cached `getBoundingClientRect`), there should be **zero** JS-triggered layout in the scroll recording.
  2. **CDN-block fallback:** Set Chrome DevTools → Network → "Offline" or use `--block-network` for `cdn.jsdelivr.net`. Reload. Confirm:
     - Three.js fails to load → `s.onerror` fires → `canvas.style.display = "none"` → CSS `.hero-core .orb` is visible. No JS error in console (the `try/catch` in `boot()` must catch `THREE` being undefined).
     - Google Fonts fails → fallback fonts (Georgia, system-ui, ui-monospace) render. No broken layout. The `preconnect` hints are harmless.
  3. **Lighthouse (mobile, throttled):**
     - Performance score ≥ 80.
     - LCP < 2.5 s (the hero orb + Three.js init is the LCP candidate; if Three.js takes > 1 s, the CSS orb should be the LCP element).
     - CLS < 0.1 (the font swap and the grid population must not shift layout).
     - TBT < 200 ms (the magnetic + cursor + Three.js + radar loops must not block the main thread > 50 ms in any frame).
  4. **`requestAnimationFrame` loops:** The cursor loop (≈ L495) runs **permanently** even when the mouse is idle. Add an early-out: if `Math.abs(x-rx) < 0.5 && Math.abs(y-ry) < 0.5`, skip the `ring.style` write. The Three.js loop runs while the tab is visible; add `document.hidden` check to pause `gl.render()` when the tab is backgrounded.

- **Pass:** No JS-triggered layout in the performance trace. Offline reload shows the CSS orb, no console errors. Lighthouse mobile score ≥ 80, LCP < 2.5 s, CLS < 0.1.

---

## Appendix — Quick Reference: Line Map of `index.html`

| Approx. line | Content |
|---|---|
| 17–22 | `:root` CSS tokens |
| 44–48 | `.eyebrow` style |
| 55–75 | Nav styles + `.nav-cta` |
| 76–130 | Hero styles (`.hero`, `.hero-copy`, `.hero h1`, `.hero-sub`, `.hero-cta`, `.stat-strip`, `.ticker`) |
| 131–145 | Manifesto + `.pillars` styles |
| 146–170 | Strata styles |
| 171–190 | 17-layer grid + marquee styles |
| 191–210 | Sovereignty styles |
| 211–230 | Symbiosis + radar styles |
| 231–250 | Cockpit / deploy styles |
| 251–270 | Quick start styles |
| 271–290 | Footer styles |
| 291–310 | Reveal (`.rv`) styles |
| 312–340 | HTML: nav |
| 341–400 | HTML: hero |
| 401–430 | HTML: manifesto |
| 431–480 | HTML: strata |
| 481–530 | HTML: 17 layers + JS layer injection |
| 531–570 | HTML: sovereignty |
| 571–610 | HTML: symbiosis + deploy + quick start + footer + script block |

*(Line numbers are approximate from the 610-line file; use the class/id names above as the primary anchor for any edits.)*
