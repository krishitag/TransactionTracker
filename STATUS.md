# Project Status: Transaction Risk Platform

_Last updated: 2026-10-18_

Legend: ✅ done · 🟡 partly done · ⬜ not started · ⛔ blocked

## Right now

- **Current phase:** Phases A–D done → **Phase E (ship) next**
- **Next task:** E2, Dockerfile (then E3 Neon → E4 Render → E5 Vercel → finish E6 README with the live link).
- **Run it:** `docker compose up -d` (repo root) · `venv/bin/uvicorn main:app` (backend/) · `npm run dev` (frontend/, port **3100**)
- Frontend tools installed: tasteskill (`design-taste-frontend`), `web-design-guidelines`, `playwright-cli` (uses your Chrome). Design system: `DESIGN.md` (blue). Disk ~1.7 GB free.
- **Improvement backlog:**
  1. ~~Time-of-day + category keyword filters for /ask~~ ✅
  2. ~~Night-time feature + retrain~~ ✅ (model v2, journal §19)
  3. ~~Readable category names in /ask statistics~~ ✅
  4. Daytime-fraud recall dropped with v2: try per-card hour baselines or a tree model (later)
  5. Dashboard filter + page in the URL (deep links), flagged by the Vercel audit; needs useSearchParams + Suspense under Next 16 cacheComponents
  6. /ask statistics: add a row for the *combination* of detected filters with count, high, fraud and **min/max/total amount** (e.g. late-night online shopping = 83 / 50 high / 44 fraud; late-night travel = 14 txns, all $1.11–$9.12). Today the stats are one dimension at a time, so answers can't state the intersection and hedge on "any large…?" questions
  7. Small-amount fraud is mostly missed: 33 of the 53 missed frauds are under $20 (89% of sub-$20 fraud scored Low). Likely card testing; needs sequence features (several small payments in a row, small-then-large on the same card)
- **Blockers:** none
- **To start the database:** `docker compose up -d` from the repo root (Postgres 16 on port **5433**)

## What exists today (commit `a0d5fe5`)

| File | State | Notes |
|---|---|---|
| `backend/peek.py` | ✅ | Exploration only. Prints columns and fraud counts. |
| `backend/features.py` | ✅ | Shared feature library: `compute_features`, `distance_threshold`, `add_distance_flag`, `FEATURE_COLUMNS`. |
| `backend/train_model.py` | ✅ | Trains scaled `LogisticRegression(class_weight="balanced")`, prints evaluation, saves bundle. |
| `backend/scoring.py` | ✅ | `score_transaction(txn, history)` returns risk score, level, plain-English reasons, features and contributions. |
| `backend/models/risk_model.joblib` | ✅ | Saved bundle: model + distance threshold + feature list (1.9 KB, committed). |
| `backend/main.py` | ✅ | `POST /transactions` validates, cleans, saves, scores and stores the risk score in one DB transaction. 409 on duplicate, 422 on bad input. |
| `backend/requirements.txt` | ✅ | Pinned versions, including sentence-transformers, torch and anthropic. |
| `backend/ask.py` | ✅ | Hybrid retrieval (risk-level filter + pgvector top 10 + SQL stats), grounded prompt, citation verification. LLM = Gemini (default) or Claude via `LLM_PROVIDER`. |
| `backend/embeddings.py` | ✅ | `build_summary`, `embed` (normalised, 384-dim), `to_pgvector`. |
| `backend/backfill_embeddings.py` | ✅ | Fills missing embeddings; `--all` rebuilds every row. |
| `backend/seed_transactions.py` | ✅ | Loads 2,440 real `fraudTest.csv` transactions (40 cards, 207 fraud) through the API. |
| `backend/queries.sql` | ✅ | Saved exploration queries: health checks, model quality, risk by category/merchant/time, card timelines, vector + hybrid search, EXPLAIN. |
| `backend/migrations/001_add_embeddings.sql` | ✅ | Adds pgvector columns + HNSW index to an older database. |
| `backend/schema.sql` | ✅ | `transactions` + `risk_scores` tables, constraints, indexes. |
| `docker-compose.yml` | ✅ | Local Postgres 16 on port 5433. Runs `schema.sql` on first start. |
| `frontend/` | ✅ | Next.js 16 dashboard on :3100: risk-tinted stat cards (the filter), transaction table with reasons, "Ask the AI analyst" panel with clickable citations. Google Sans, DESIGN.md tokens. |
| `DESIGN.md` | ✅ | Design system: blue palette + risk tints, Google Sans, dashboard revision (D9d). |
| `PORTFOLIO_PLAN.md` | ✅ | Notes for the separate portfolio site (later). |

## Phase A: Finish the model

| # | Task | Status |
|---|---|---|
| A1 | One shared `compute_features(df)` in `features.py`, imported by training and scoring | ✅ |
| A2 | Train `LogisticRegression(class_weight="balanced")`, evaluate with precision/recall/confusion matrix, save with joblib | ✅ recall 0.79, precision 0.07 @0.5, PR-AUC 0.21 |
| A3 | `scoring.py`: load model, score one transaction, return ranked plain-English reasons | ✅ |

## Phase B: Wire it into a real API

| # | Task | Status |
|---|---|---|
| B4 | `schema.sql` with `transactions` + `risk_scores` tables | ✅ |
| B5 | `requirements.txt` + `docker-compose.yml` (Postgres) | ✅ |
| B6 | `POST /transactions` pulls card history, scores, writes to `risk_scores` | ✅ |

## Phase C: RAG ("ask questions about transactions")

| # | Task | Status |
|---|---|---|
| C7 | pgvector: `embedding vector(384)` + HNSW cosine index; embed a summary of each transaction in the same DB transaction as the insert; backfill script for existing rows | ✅ 2,440 seeded, all embedded |
| C8 | `POST /ask`: top 8-10 vector hits + SQL aggregate + LLM, grounded answers with transaction IDs | ✅ tested live with Gemini 3.8 Flash: 4/4 questions grounded, 0 invalid citations, trap question correctly declined |

## Phase D: Frontend

| # | Task | Status |
|---|---|---|
| D9a | Backend for the dashboard: `GET /stats`, `GET /transactions` (filter + pagination), `GET /transactions/{id}`, CORS for the dashboard origin (localhost:3100) | ✅ |
| D9b | Next.js dashboard: stat band (doubles as filter), transaction table with risk badges and reasons, ask panel with clickable citations | ✅ built, checked by tools, and manually tested 18/18 (4 /ask answers verified against SQL) |
| D9c | ~~Project showcase page~~ moved out: separate personal portfolio site (own repo, later) | ➖ out of scope here |
| D9d | Dashboard restyle: risk-tinted stat cards, blue scale, bordered table with tinted header, green Low badges, AI panel on the right, Google Sans | ✅ approved by you; tsc, ESLint, tasteskill lint + inspector, Playwright, contrast, Vercel audit (2 small fixes) |

## Phase E: Ship

| # | Task | Status |
|---|---|---|
| E1 | pytest (features, scorer, Gemini key fallback, citation check) + small committed data sample + GitHub Actions (Python lint + tests, frontend tsc + ESLint + build) | ✅ CI run #2 (`ea2c52d`) green: backend ruff + 43 tests, frontend typegen + tsc + ESLint + build. Run #1 failed on `LayoutProps` (fixed with `next typegen`) |
| E2 | Dockerfile for the backend (CPU-only torch, embedding model baked in at build) | ⬜ |
| E3 | Neon Postgres + pgvector: schema, seed the 2,440 transactions | ⬜ |
| E4 | Backend on Render (Docker; env vars for DB, Gemini keys, `FRONTEND_ORIGINS`); check memory fits 512 MB | ⬜ |
| E5 | Dashboard on Vercel (`frontend/`, `NEXT_PUBLIC_API_URL`), then CORS for the Vercel URL | ⬜ |
| E6 | README: what, screenshot, live link, architecture, model, results + limitations, run locally, dataset link | 🟡 README + RESULTS.md + `backend/.env.example` written; live link and CI badge go green after deploy / first CI run |

## Change log

Add one line every time something moves.

- **2026-10-17:** Manual test, sections 1–3 (load, stat-band filter, table/pagination/reasons) pass. Ask panel timed out at 60s: Gemini returned 504 "deadline expired" twice and then 429 (Google-side overload/quota), and our backend's retry budget (2 × 45s) outlasted the browser's 60s, hiding the real error. Fixed in `ask.py`: 1 attempt × 40s, 50s total budget, clear "overloaded" message on 503/504, and an optional backup key `GEMINI_API_KEY_2` used only on 429 (60s cooldown on a limited key). 10/10 offline fallback tests pass. Live: first retry showed the new "overloaded" message (Google still busy), next retry answered; every claim in the late-night online shopping answer checked against SQL (stats + 8 transactions, all correct). Backup keys generalised to `GEMINI_API_KEY_2`…`_5` (12/12 offline tests). Citation click (#1945) and the Mumbai trap question pass. Two more 502s (not 429s), so added `GEMINI_THINKING` (default low) to cut answer time, plus a log line for every Gemini success/failure with code and duration (14/14 offline tests). Live: thinking low accepted; "large travel purchases at night" answered correctly but hedged (SQL: 14 txns, max $9.12). Found small-amount fraud blind spot (backlog 7).
- **2026-10-18:** D9d built (journal §25): four bordered stat cards with share lines, full-width layout, "Ask the AI analyst" panel fixed on the right with a navy header, table as a white card with a blue header and row lines, blue-50…300 scale, Google Sans. tsc, ESLint, tasteskill lint 0/0, inspector 0 FAIL / 1 defended WARN, contrast ≥ 4.7:1. The dev server served stale body CSS (page stayed white), so it needs a restart with `.next` cleared.
- **2026-10-18:** **E1 done:** CI run #2 green on GitHub (both jobs).
- **2026-10-18:** CI #1: backend passed (ruff + 43 tests on GitHub). Frontend failed: `LayoutProps` is generated by Next.js into `.next/`, which a fresh checkout lacks. Added a `npx next typegen` step before `tsc` (reproduced and verified in a clean copy). Bumped actions to their Node 24 versions and pinned `ubuntu-24.04`. ESLint and `next build` pass locally (one harmless warning: no fallback-font metrics for Google Sans).
- **2026-10-18:** README.md (with the verified Kaggle link: "Credit Card Transactions Fraud Detection Dataset", Kartik Shenoy, CC0, Sparkov), RESULTS.md (all numbers from the journal; Medium fraud count 28 checked with SQL), `docs/dashboard.png`, `backend/.env.example`. Local run of E1: 43 passed; ruff flagged 1 import order in `ask.py` (fixed).
- **2026-10-18:** E1 written (journal §26): `backend/tests/` (features, scoring, ask), 200-row sample `tests/data/sample.csv` (PR-AUC 0.59 vs 0.10 baseline), `pyproject.toml` (pytest + ruff config), `requirements-dev.txt`, `.github/workflows/ci.yml` (backend ruff + pytest with CPU torch; frontend tsc + ESLint + build).
- **2026-10-18:** Phase E planned: Vercel (dashboard) → Render (Docker backend) → **Neon** (Postgres + pgvector, chosen over Render Postgres, which expires after 30 days, and Supabase, which pauses). Order: tests/CI first. Risks noted: Render free = 512 MB RAM (backend 167 MB on Mac; measure on Linux; ONNX fallback), free servers sleep after 15 min, Gemini free-tier limits. Disk now 111 GB free.
- **2026-10-18:** Table summary line now matches the selected filter (option A): `/stats` adds `medium_risk_amount` / `low_risk_amount` (High $108,017 = 42%, Medium $19,292 = 7%, Low $130,932 = 51% of $258,240, checked with SQL). Frontend falls back to the count on an older backend. Verified live after the backend restart and a page refresh (Medium: "113 transactions worth $19,292, 7% of all money").
- **2026-10-18:** **D9d done, so Phase D is complete.** Low badges green (the `risk-low` token itself is now green). Vercel audit: removed a redundant wrapper and added `overscroll-contain` to the AI panel; the rest passes (deliberate exceptions: sentence case, URL state = backlog 5). Inspector 0 FAIL, 1 defended WARN; page background confirmed `#f3f7fd`. Open: the table summary line always describes high-risk money, even on the Medium/Low views.
- **2026-10-18:** D9d round 5: the table header row takes the selected filter's tint (red / amber / green, blue for All). Checked in Playwright for all three risk filters.
- **2026-10-18:** D9d round 4: hover borders in each card's colour (50%), and the Medium/Low figures in amber/green like High's red. Verified in Playwright: tints, borders, green and the blue-50 page background all render now (the dev server picked up the tokens).
- **2026-10-18:** D9d round 3: stat cards tinted by risk on hover and selection (All blue, High red, Medium amber, Low green: your choice, trade-off in DESIGN.md). Contrast ≥ 4.8:1. Playwright: High and Medium tints render; Low green doesn't yet, because the dev server's stale cache lacks the new tokens (needs a `.next`-cleared restart).
- **2026-10-18:** D9d round 2: light-blue hover fill on stat cards; table title moved inside the table card so the table and AI panel tops and titles align. Checks still pass (0 FAIL, same 1 defended WARN).
- **2026-10-18:** D9c dropped from this repo: the showcase becomes a separate personal portfolio site (later; details in `PORTFOLIO_PLAN.md`), and the dashboard stays at `/`. Next: dashboard frontend changes (D9d), as you specify them.
- **2026-10-18:** D9c planned (journal §24, now superseded): tasteskill direction `editorial-report` (seed 1360379183); showcase at `/`, dashboard moves to `/dashboard`; live "score it yourself" section using exported v2 weights in the browser. Waiting on: portrait photo, email, LinkedIn URL.
- **2026-10-18:** **Manual test complete (18/18), so D9b is done.** The merchants question was exact (8 merchants tied at 3 high-risk, names, totals and citations all match SQL). Also passed: error states, Enter/Shift+Enter, backend-down message, phone layout and keyboard/skip link all pass. Fixed 3 polish issues it found: gap before commas after citations, focus ring on the programmatically focused citation card (global rule now skips `tabindex="-1"` targets), and the examples vanishing behind the "3 characters" error that pointed to them. tsc, ESLint, tasteskill lint (0 FAIL, 1 defended WARN) and inspector (0/0) pass.

- **2026-10-17:** D9b built: Next.js 16 dashboard following DESIGN.md. Found and fixed: a port clash with another local app (dashboard pinned to 3100, CORS updated), a stale CSS cache, a phone layout hiding the Risk column, and `/ask` hanging on a network with broken IPv6 (Gemini client now IPv4 + strict timeouts; frontend 60s safety net).
- **2026-10-17:** D9a done: read endpoints + CORS, all tested (stats, filtered page, single transaction, 404, 422).
- **2026-10-17:** Re-seeded with v2 (all 2,440 scored by `f683e347ae3d`). High: 141 alerts, 126 fraud; total alerts 453 → 254; fraud missed 43 → 53. /ask late-night online shopping question now filters correctly (7 valid citations).
- **2026-10-17:** Model v2: added `night_time` (22:00–03:59). PR-AUC 0.21 → 0.285; at 0.9 alerts −22%, precision 22.9% → 32.9%, recall 53.1% → 59.8%; daytime recall fell 54.6% → 48.5% (documented). Medium band moved 0.5 → 0.7. /ask gained time and category filters with a fallback, plus readable category names. "Late night" redefined as 22:00–04:00 everywhere.
- **2026-10-17:** C8 done, so **Phase C is complete**. Live test with `gemini-3.8-flash`: all 4 questions grounded, 0 invalid citations, the Mumbai trap correctly declined. Found a model blind spot (late-night fraud) and a retrieval gap (time questions); both are in the backlog.
- **2026-10-17:** Added Gemini (free tier) as the default `/ask` LLM; Claude stays available with `LLM_PROVIDER=claude`. Errors are normalised to 503/429/502.
- **2026-10-17:** C8 code written: `POST /ask` using Claude Opus 5.5, effort medium, server-side refusal fallback. Offline checks passed. Found and fixed a gap: with no credentials the SDK raises TypeError, not AnthropicError, so we now check up front and return a clear 503.
- **2026-10-17:** C7 done. Seeded 2,440 transactions through the API (all 201). Every row is embedded. The high band holds 110 of 129 actual fraud; overall the model caught 164 of 207 fraud as medium/high. Vector search works, but merchant names dominate similarity (journal §17).
- **2026-10-17:** C7 code written: summaries + embeddings saved in the same DB transaction as the score, plus backfill and seed scripts. The DB was recreated on the pgvector image after a collation mismatch (test data only). Installed sentence-transformers 6.1.0, torch 2.14.1 and anthropic 1.15.0 (after a network dropout).
- **2026-10-17:** Decision change: MongoDB Atlas → **pgvector** for vector search (journal §16).
- **2026-10-17:** B6 done, so **Phase B is complete**. End-to-end test via curl: 4 transactions scored low/low/medium/high with correct reasons, a duplicate gave 409, a negative amount gave 422, and the DB holds exactly 4 scored rows with clean merchant names and model version `c8b8b28efe16`.
- **2026-10-17:** B5 done; B6 code written. The reduced history query matched full-history scores on 300 real transactions (0 differences).
- **2026-10-17:** B4 done. The old Supabase DB no longer exists, so we switched `.env` to local Docker Postgres (port 5433; Homebrew Postgres already uses 5432). Freed disk space first, since the Mac had 188 MB left. Tested: the API insert works, the constraints reject bad scores/levels/orphan rows/duplicate IDs, and card-history lookups use the index.
- **2026-10-17:** A3 done, so **Phase A is complete**. `scoring.py` was tested on unseen `fraudTest.csv` rows: a real $996 fraud scored 0.998 (high), a normal $53 purchase scored 0.26 (low), a 4-in-an-hour burst made velocity the top reason, and a routine repeat purchase gave "no unusual signals".
- **2026-10-17:** A2 done. Model trained on 1.04M rows and tested on 259K. At a 0.5 cutoff it catches 79% of fraud with 6.8% precision; PR-AUC is 0.21 vs a 0.0058 random baseline. The distance flag turned out to carry no signal (see journal §11).
- **2026-10-17:** A1 done. Feature logic now lives only in `features.py`; `train_model.py` imports it. Checked against hand-made test transactions.
- **2026-10-17:** Created `STATUS.md` and `PROJECT_JOURNAL.md`. Found that the dataset is missing locally.
- **2026-09-19:** First commit `6928f16`: exploration, feature prototype, train/test split, raw insert endpoint.
