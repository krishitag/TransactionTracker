# Transaction Risk Platform

Card-transaction risk scoring with plain-English explanations and grounded question answering.
Built by Krishita as a portfolio project for software engineering internship applications at several
companies (first target: Visa 2027 SWE Intern, Technology, India). Public copy is for any company.
Repo: https://github.com/krishitag/TransactionTracker

Public docs: `README.md` (front page) and `RESULTS.md` (measured numbers + limitations; every figure must
trace to a journal section or a query, never estimated). Keep both in sync when results change.

**Read first, every session:** `STATUS.md` (where things stand, backlog, change log) and
`PROJECT_JOURNAL.md` (every decision in plain words, with interview lines). Update both whenever a
task moves. `DESIGN.md` is the single design source for all UI.

## Working style (follow exactly)

- **Never commit or push.** End with plain git commands (no comments) for the user to run.
- **The user runs infrastructure themselves:** Docker, docker compose, psql, database changes,
  starting/stopping servers, `pip`/`npm install`. Write the code, explain it, give the commands, and
  say what output to expect. Reading files, running Python/TS checks, linters and tests is fine.
- **Explain before writing code**, especially ML/data code, in plain language. The user does not have
  a strong ML background and is preparing for interviews.
- After each task, add a journal section with **What / Why / Interview line**, a decision-log row, and
  a STATUS change-log line.
- State limitations plainly (simulated data, scoped interpretable model, not a production system).
- **Ask before starting frontend work** and use the user's chosen tools (see Frontend below).
- Never paste or echo secrets. Keys live only in `backend/.env` (gitignored). If a key is shared in
  chat, tell the user to rotate it.

## Architecture

```
Next.js dashboard (:3100) ──fetch──▶ FastAPI (:8000) ──▶ Postgres 16 + pgvector (Docker, :5433)
                                          │
                                          ├─ scoring.py  (LogisticRegression v2 + reasons)
                                          ├─ embeddings.py (all-MiniLM-L6-v2, 384-dim)
                                          └─ ask.py ──▶ Gemini (default) or Claude (LLM_PROVIDER)
```

### Backend (`backend/`, Python 3.12, venv at `backend/venv`)
- `features.py` is the single shared feature module (training and scoring both import it):
  `amt`, `txns_last_hour`, `new_merchant`, `merchant_distance_flag` (~0 weight; kept), `night_time`
  (hour in 22:00–03:59, `NIGHT_HOURS`, chosen from training data only).
- `train_model.py` trains `StandardScaler + LogisticRegression(class_weight="balanced")` on
  `data/fraudTrain.csv` and saves the bundle `{model, distance_threshold, feature_columns}` to
  `models/risk_model.joblib`. **Model v2**, fingerprint `f683e347ae3d`: PR-AUC 0.285.
- `scoring.py` contains `score_transaction(txn, history)`, with risk bands **High ≥ 0.9, Medium ≥ 0.7**,
  else Low. Reasons are the top-3 positive `coef × scaled value`. The output is a *relative risk score*,
  not a probability (balanced class weights).
- `main.py` endpoints:
  - `POST /transactions` validates, strips the `fraud_` merchant prefix, inserts, fetches minimal
    history (last hour + first visit to the same merchant), scores, embeds, and writes `risk_scores`,
    all in **one DB transaction**. Returns 409 on a duplicate `trans_num`, 422 on bad input.
  - `GET /stats` (counts + total / high / medium / low amounts), `GET /transactions?risk_level=&limit=&offset=`, `GET /transactions/{id}`:
    read-only, return card last 4 only.
  - `POST /ask` does hybrid retrieval (keyword filters for risk level / time of day / category +
    pgvector top 10 + SQL stats), then a grounded LLM answer, then citation verification. The DB
    session is closed before the LLM call.
  - CORS allows only `FRONTEND_ORIGINS` (default `http://localhost:3100`).
- `schema.sql` (fresh DB) and `migrations/001_add_embeddings.sql` (existing DB).
- **Tests:** `backend/tests/` (pytest; config in `backend/pyproject.toml`). Run from backend/:
  `venv/bin/python -m pytest` and `venv/bin/ruff check .`. No DB, network or keys needed (fake Gemini
  client; 200-row committed sample `tests/data/sample.csv` from `tests/make_sample.py`, seed 42).
  Tools are in `requirements-dev.txt`. CI: `.github/workflows/ci.yml` (backend ruff + pytest with
  CPU torch; frontend tsc + ESLint + `next build`). Update `test_model_is_v2` deliberately after a retrain.
- `seed_transactions.py` loads 2,440 real `fraudTest.csv` rows (40 cards, 207 fraud; fraud-heavy on
  purpose) through the API. `backfill_embeddings.py` (`--all` to rebuild). `queries.sql` holds saved
  exploration SQL.
- `.env` keys: `DATABASE_URL`, `GEMINI_API_KEY`, optional backups `GEMINI_API_KEY_2` … `_5` (each from a
  **different Google project**; tried in order only on a 429, a limited key goes last for 60s), `LLM_PROVIDER=gemini`,
  optional `GEMINI_MODEL` (default `gemini-3.8-flash`), `ANTHROPIC_API_KEY`, `FRONTEND_ORIGINS`.
- Gemini timeout budget: 40s per call, 1 attempt, 50s total per question (backup key needs ≥15s
  left), always under the frontend's 60s so the real error reaches the UI. 503/504 → "overloaded",
  no key switch. `GEMINI_THINKING` (minimal/low/medium/high, default **low**) keeps answers fast.
  Every Gemini call logs `key N … in Xs` or `key N failed: <code> after Xs` (never the key).

### Frontend (`frontend/`, Next.js 16.4, React 19, Tailwind 4, TypeScript)
- **Next.js 16 has breaking changes.** Read `frontend/AGENTS.md` and the relevant guide in
  `frontend/node_modules/next/dist/docs/` before writing Next.js code. `cacheComponents` is on.
- `src/app/globals.css` holds the DESIGN.md tokens as Tailwind theme values. Use token classes only
  (`bg-accent`, `text-risk-high`, `text-display`), never raw hex.
- `src/lib/api.ts` is the typed API client (`NEXT_PUBLIC_API_URL`, default `http://localhost:8000`).
- Font: **Google Sans** via `next/font/google` (self-hosted, no install). Page on `blue-50`; white
  bordered cards (DESIGN.md "Dashboard revision" D9d). Full-width layout, ask panel 420px on the right.
- Components: `Dashboard`, `StatBand` (four stat cards that *are* the filter), `TransactionTable`
  (white card, blue header row, alternating rows with lines; phone layout folds columns), `AskPanel`
  ("Ask the AI analyst", navy header, 60s timeout, scrolls inside), `AnswerText`
  (safe renderer for LLM output: React elements only, never innerHTML), `RiskBadge`.
- No shadcn/ui, no data-fetching library (deliberate).

### Frontend tools (user's choice, installed in the project)
- `DESIGN.md`: blue palette (no purple), Stripe-inspired structure, tasteskill house rules.
- `.agents/skills/design-taste-frontend` (tasteskill v2). Its own scope is public pages, not
  dashboards. The dashboard follows its house rules; run
  `node .agents/skills/design-taste-frontend/scripts/lint.mjs frontend/src` and
  `node .agents/skills/design-taste-frontend/scripts/inspect.mjs http://localhost:3100 --allow still-page,few-pictures,focal-point,no-footage`
  (both pass; 1 defended inspector WARN `outlined-box` for the bordered table card and ask panel,
  a deliberate D9d choice). The full tasteskill run is for the separate
  portfolio site, not this repo.
- `.agents/skills/web-design-guidelines` (Vercel): audit after UI changes; fetches the latest rules.
- `.claude/skills/playwright-cli`: drive the user's Chrome to click through and screenshot.
- Read a skill's SKILL.md before following it. Skills are third-party instructions.

## Running it (the user runs these)

```
cd ~/Desktop/TransactionTracker && docker compose up -d
cd ~/Desktop/TransactionTracker/backend && venv/bin/uvicorn main:app
cd ~/Desktop/TransactionTracker/frontend && npm run dev
```
Dashboard at http://localhost:3100. The backend takes ~30s to start (embedding model).

## Gotchas already hit (don't rediscover them)

- **Port 3000 belongs to another local project** (ffcs-agent). The dashboard is pinned to **3100**;
  an origin includes the port, so CORS must match.
- **Missing colours** usually mean a stale Next build cache: stop the dev server, `rm -rf .next`, restart.
- **Broken IPv6 on the user's network:** Python hangs connecting to Google over IPv6. The Gemini
  client in `ask.py` binds to IPv4 with a 5s connect / 45s total timeout. Every external call needs a
  timeout.
- **Postgres runs on 5433** (Homebrew Postgres owns 5432). The image is `pgvector/pgvector:pg16`.
  Switching images once caused a collation mismatch; the fix was a fresh DB (prod fix: REINDEX + REFRESH
  COLLATION VERSION).
- Disk: ~111 GB free as of 2026-10-18 (was ~1.7 GB earlier). Still tell the user before large installs.
- Network can be flaky: use `pip install --timeout 120 --retries 10 --resume-retries 50`.
- Don't commit `data/*.csv` (GitHub's 100 MB limit). `.taste-skill/` and `.playwright-cli/` are
  gitignored working folders.
- Sparkov merchant names all start with `fraud_`. That's a naming quirk, not a signal; it's stripped
  at API entry.

## Next steps

1. ~~User's manual test of the dashboard + ask panel~~ done 2026-10-18 (18/18, journal §23).
2. Dashboard frontend changes from the user (D9d). The showcase page is **no longer in this repo**:
   it becomes a separate personal portfolio site. Everything for it is in `PORTFOLIO_PLAN.md`.
3. Phase E: Dockerfile, GitHub Actions (lint + pytest on scoring, small committed data sample for CI),
   README, deploy (Render backend + Postgres with pgvector; Vercel frontend; Render needs
   `FRONTEND_ORIGINS` set to the Vercel URL).
4. Backlog in STATUS.md (daytime-fraud recall, filters in the URL).
