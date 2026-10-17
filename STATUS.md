# Project Status: Transaction Risk Platform

_Last updated: 2026-10-17_

Legend: ✅ done · 🟡 partly done · ⬜ not started · ⛔ blocked

## Right now

- **Current phase:** Phase C done → Phase D (frontend)
- **Next task:** D9c, the showcase page with the full tasteskill run (plan first, then build).
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

## What exists today (commit `6928f16`)

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
| `frontend/` | ⬜ | Empty folder. |

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
| D9c | Project showcase page (full tasteskill run, DESIGN.md tokens, `--keep palette,type`) | ⬜ planning |

## Phase E: Ship

| # | Task | Status |
|---|---|---|
| E10 | Dockerfile, GitHub Actions (lint + pytest), README, deploy (Render + Vercel) | ⬜ |

## Change log

Add one line every time something moves.

- **2026-10-17:** Manual test, sections 1–3 (load, stat-band filter, table/pagination/reasons) pass. Ask panel timed out at 60s: Gemini returned 504 "deadline expired" twice and then 429 (Google-side overload/quota), and our backend's retry budget (2 × 45s) outlasted the browser's 60s, hiding the real error. Fixed in `ask.py`: 1 attempt × 40s, 50s total budget, clear "overloaded" message on 503/504, and an optional backup key `GEMINI_API_KEY_2` used only on 429 (60s cooldown on a limited key). 10/10 offline fallback tests pass. Live: first retry showed the new "overloaded" message (Google still busy), next retry answered; every claim in the late-night online shopping answer checked against SQL (stats + 8 transactions, all correct). Backup keys generalised to `GEMINI_API_KEY_2`…`_5` (12/12 offline tests). Citation click (#1945) and the Mumbai trap question pass. Two more 502s (not 429s), so added `GEMINI_THINKING` (default low) to cut answer time, plus a log line for every Gemini success/failure with code and duration (14/14 offline tests). Live: thinking low accepted; "large travel purchases at night" answered correctly but hedged (SQL: 14 txns, max $9.12). Found small-amount fraud blind spot (backlog 7).
- **2026-10-18:** D9c planned (journal §24): tasteskill direction `editorial-report` (seed 1360379183); showcase at `/`, dashboard moves to `/dashboard`; live "score it yourself" section using exported v2 weights in the browser. Waiting on: portrait photo, email, LinkedIn URL.
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
