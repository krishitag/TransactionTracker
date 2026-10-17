# Portfolio site: plan and notes (for later)

A separate personal portfolio site that links all of Krishita's projects, with this Transaction Risk
Platform as one case study. **Not built in this repo.** Decided 2026-10-18 (journal §24 and the
decision log in `PROJECT_JOURNAL.md`).

## Audience and goal

- Recruiters and engineers at **any company** (not written for one employer).
- In 30 seconds they should know who Krishita is and what Krishita builds, then open a project
  (live demo or GitHub) or get in touch.

## Setup (Krishita runs these; explain first)

1. New folder outside this repo, e.g. `~/Desktop/portfolio`, plus a new GitHub repo.
2. Stack choice, decided at the start:
   - **Next.js** (same as this dashboard): `npm` install of roughly 300–400 MB. **Check free disk first**
     (the Mac had ~1.7 GB free on 2026-10-18).
   - **Plain HTML/CSS/JS**: no install, deploys anywhere. Fine for a one-page portfolio.
3. Copy the tasteskill skill (`.agents/skills/design-taste-frontend`) and adapt `DESIGN.md` (blue
   palette, Inter) so the portfolio and this project look related.
4. Open a **new Claude Code session in that folder** with its own `CLAUDE.md`, `STATUS.md` and journal.
5. Deploy (Vercel or GitHub Pages).

## What Krishita needs to provide

- [ ] List of projects: name, one line each, GitHub link, live link, screenshots if any
- [ ] Portrait photo (square, at least 600×600 px)
- [ ] Email to show publicly
- [ ] LinkedIn URL
- [ ] GitHub profile URL (repo for this project: https://github.com/krishitag/TransactionTracker)
- [ ] Short bio: university, year, the roles being targeted
- [ ] Name/wordmark for the site (Krishita's own name?)

## Design process: full tasteskill run

Inventory → argument (claims + proof per section) → `draw.mjs --options 3` → choose a direction and
write why → idea sentence + one live thing → copy deck → build still → `lint.mjs` + `inspect.mjs` with
**no** `--allow` exceptions → up to 3 critique rounds on screenshots → motion layer → inspector again →
Vercel web-design-guidelines audit → report with picture credits. Pass `--keep palette,type` if
reusing DESIGN.md. The sector is probably `personal-portfolio`, with `--sections` chosen from the argument.

Proof is never invented: no fake testimonials, logos or statistics. Every number comes from a real project.

## Reusable ideas from the superseded showcase plan (journal §24)

For this project's **case study** on the portfolio:

- **Direction that fitted:** `editorial-report` ("The printed annual", seed 1360379183, finance
  sector). A fixed 42% axis, margin notes, solid colour pages. The project is a set of findings, so a report layout suits it.
- **Idea:** the model's own plain-English reasons ("Made at 22:09, in the 22:00–04:00 window when most
  fraud happens") become the report's margin notes.
- **Live thing: "score a payment yourself".** Export the v2 model's weights (scaler mean/scale,
  coefficients, intercept, distance threshold, `NIGHT_HOURS`) from `backend/models/risk_model.joblib`
  to JSON and repeat `scoring.py`'s maths in the browser, so no backend is needed. **Parity test:** about 100 real
  transactions scored in Python and in the JS maths must match to 6 decimals, with identical reasons.
  Controls: amount, hour, first time at this merchant, payments in the last hour.
- **Content that's real and verified:**
  - 84.7% of training fraud happens 22:00–03:59 (23.5% of transactions)
  - PR-AUC 0.285 for v2 vs 0.0058 for random; v1 was 0.21
  - At the high cutoff (0.9): alerts −22%, precision 22.9% → 32.9%, recall 53.1% → 59.8%
  - Seed demo: 141 high-risk alerts, 126 actually fraud (89%)
  - `/ask` answers checked against SQL in manual testing; the "Mumbai" trap question correctly declined
  - Honest limits: simulated (Sparkov) data; daytime-fraud recall fell with v2; 33 of 53 missed frauds
    are under $20 (likely card testing)
- **Pictures:** real dashboard screenshots (Playwright) and interface fragments marked `data-ui`;
  optionally one credited archive photo (e.g. a city at night, for the night-time finding).
- **Type note:** DESIGN.md caps display type at 56px; tasteskill heroes want around 7–12vw. Add larger
  display sizes for the portfolio only.
