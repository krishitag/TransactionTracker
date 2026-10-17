---
version: 1
name: Transaction Risk Platform
description: One design language for both surfaces of the project, the analyst dashboard and the public project showcase page. Structure adapted from the "Stripi-inspired" DESIGN.md in VoltAgent/awesome-design-md (deep navy ink, cool white surfaces, thin display type, tabular figures for money), recoloured to blue, and governed by the tasteskill v2 house rules. No Stripe name, logo or gradient mesh is used.

colors:
  # Blue family: the only hue on the page apart from risk status.
  accent: "#0b5fd3"          # primary action, links, focus, chart highlight
  accent-press: "#084aa6"    # pressed / hover on accent
  accent-soft: "#3d82e6"     # secondary chart series, selected-row marker
  accent-wash: "#e6effc"     # selected filter, tag ground, chat answer ground
  navy-900: "#0a1f3d"        # deep field (header band, showcase dark sections)
  ink: "#0d253d"             # all running text
  ink-secondary: "#273951"
  ink-mute: "#5b6b80"        # captions, table labels (5.4:1 on canvas)
  on-dark: "#ffffff"
  canvas: "#ffffff"          # ground
  canvas-soft: "#f5f8fc"     # tone step 1 (bands, panels)
  canvas-blue: "#eaf1fb"     # tone step 2 (stat band, hover rows)
  hairline: "#e3e8ee"        # ONLY table row separators and input borders
  # Risk status: the only non-blue colours, used only on risk badges and risk figures.
  risk-high: "#c8102e"
  risk-high-wash: "#fdecef"
  risk-medium: "#8a5a12"
  risk-medium-wash: "#fbf1e1"
  risk-low: "#3f5873"
  risk-low-wash: "#eef2f7"

typography:
  family: "Inter, system-ui, -apple-system, sans-serif"   # one family only
  features: "ss01"                                        # on body, globally
  display-xl: { size: 56px, weight: 300, lineHeight: 1.03, tracking: -1.4px }   # showcase hero
  display-lg: { size: 40px, weight: 300, lineHeight: 1.05, tracking: -1.0px }   # stat figures
  heading:    { size: 22px, weight: 400, lineHeight: 1.2,  tracking: -0.2px }
  body:       { size: 16px, weight: 400, lineHeight: 1.5 }                       # running text
  table:      { size: 14px, weight: 400, lineHeight: 1.4, features: "tnum" }     # data cells
  caption:    { size: 13px, weight: 400, lineHeight: 1.4 }                       # labels, notes

rounded:
  none: 0px        # panels, bands, media: square corners
  input: 6px       # text inputs only
  pill: 9999px     # every button and every badge, decided once

spacing:            # 8px base
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  xxl: 32px
  huge: 64px
---

## Intent

The data is the product. Screens are calm, dense where the analyst compares numbers, and loud only
where risk is high. Blue carries trust and action; red and amber appear only where risk does.

## Decisions (Stripe-inspired structure vs tasteskill house rules)

Each conflict was decided once and applies to **both** surfaces.

| Topic | Stripe-inspired source says | Decision |
|---|---|---|
| Accent colour | Indigo `#533afd` | **Blue `#0b5fd3`** and its shades (user choice; tasteskill also bans violet/indigo) |
| Gradient mesh on heroes | "Non-negotiable" | **Removed.** Flat colour fields only (`navy-900`, `canvas-soft`, `canvas-blue`) |
| Card borders and shadows at rest | 1px hairline + level-1 shadow | **None.** Surfaces separated by tone steps. Shadow only on things that truly float (popover, dialog) |
| Hairlines | On cards and tables | **Only** table row separators and input borders (tasteskill exempts real tables and form fields) |
| Body weight | 300 at 14–15px | **400 at 16px** for running text; 300 kept only for display sizes (thin 300 is hard to read small) |
| All-caps micro labels / eyebrows | `micro-cap` 10px uppercase | **Removed.** Sentence case at caption size or larger |
| Font | Sohne (proprietary) | **Inter**, one family, `ss01` on; `tnum` on every number |
| Buttons | Pills | **Pills**, flat fill, no gradient |
| Stat tiles | Card grid | **One stat band**: figures set large on a `canvas-blue` field, separated by space, not boxed cards |
| Risk colours | Not defined | Red / amber / blue-grey **badges only**, always with the word (never colour alone) |

## House rules (tasteskill v2, both surfaces)

- No gradients, glass/backdrop blur, glows, emoji, decorative blobs or fake grey-bar dashboards.
- No eyebrow labels, no tiny letter-spaced uppercase, no index numbering (01 / 02).
- No monospace outside real code.
- No icon-topped feature cards and no rows of identical cards.
- Headlines two lines or fewer at every width.
- Two type sizes do most of the work; five sizes on a screen at most.
- Running text in full `ink` at 16px or more; grey (`ink-mute`) only for secondary notes.
- Visible focus on every control; real `<button>`, `<a>`, `<table>`, `<label>` elements.
- Motion: transform and opacity only, with a `prefers-reduced-motion` fallback.

## Dashboard (app screen)

- **Header band** on `navy-900`: product name, model version, nothing else.
- **Stat band** on `canvas-blue`: total, high, medium, low as large `display-lg` figures with `tnum`.
  High's figure in `risk-high`; the rest in `ink`.
- **Transactions table** on `canvas`: real `<table>`, hairline row separators, `table` type, `tnum`
  amounts right-aligned. Risk badge = pill, wash ground + status colour text + the word.
  Row expands to show the reasons (plain list in `body`).
- **Filters**: pill buttons; the active one on `accent-wash` with `accent` text.
- **Ask panel** on `canvas-soft`: text input + one `accent` pill button. Answer on `accent-wash`.
  Citations `[#660]` are `accent` links that open that transaction.
- Motion: feedback on controls (hover/press/focus) and the row expand only.

## Showcase page (public, built with tasteskill)

Follows the full tasteskill run (direction, idea, copy deck, inspector, critique, motion layer),
inside these tokens. Imagery is the real dashboard interface (screenshots and interface fragments),
never invented proof or statistics.

## Exceptions to the tasteskill inspector

| Surface | Allowed | Why |
|---|---|---|
| Dashboard | `still-page`, picture floor | An app screen: its content is the live data, not photographs or scroll motion. tasteskill itself is scoped to public pages |
| Showcase | none | Full house style applies |

## Accessibility

- Text contrast ≥ 4.5:1 (WCAG AA). Measured: `ink` on `canvas` 15.6:1, `ink-mute` on `canvas` 5.4:1
  and on `canvas-blue` 4.8:1, white on `accent` 5.9:1, `accent` on `accent-wash` 5.0:1, risk text on
  its wash 5.2 / 5.3 / 6.5:1.
- Risk is never colour alone: every badge carries its word.
- Touch targets ≥ 40×40px; inputs ≥ 40px high.
