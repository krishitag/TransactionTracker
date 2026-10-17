# Project Status: Transaction Risk Platform

_Last updated: 2026-10-17_

Legend: ✅ done · 🟡 partly done · ⬜ not started · ⛔ blocked

## Right now

- **Current phase:** Phase C (RAG)
- **Next task:** C7, MongoDB Atlas vector index + embed transaction summaries on insert
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
| `backend/requirements.txt` | ✅ | Pinned versions of what the code uses today. RAG packages get added in Phase C. |
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
| C7 | MongoDB Atlas vector index (384-dim, cosine), embed summaries on each insert | ⬜ |
| C8 | `POST /ask`: top 8-10 vector hits + Postgres aggregate + Claude, grounded answers with transaction IDs | ⬜ |

## Phase D: Frontend

| # | Task | Status |
|---|---|---|
| D9 | Next.js + Tailwind + shadcn: stat tiles, transaction table with risk badges and reasons, chat panel | ⬜ |

## Phase E: Ship

| # | Task | Status |
|---|---|---|
| E10 | Dockerfile, GitHub Actions (lint + pytest), README, deploy (Render + Vercel) | ⬜ |

## Change log

Add one line every time something moves.

- **2026-10-17:** B6 done, so **Phase B is complete**. End-to-end test via curl: 4 transactions scored low/low/medium/high with correct reasons, a duplicate gave 409, a negative amount gave 422, and the DB holds exactly 4 scored rows with clean merchant names and model version `c8b8b28efe16`.
- **2026-10-17:** B5 done; B6 code written. The reduced history query matched full-history scores on 300 real transactions (0 differences).
- **2026-10-17:** B4 done. The old Supabase DB no longer exists, so we switched `.env` to local Docker Postgres (port 5433; Homebrew Postgres already uses 5432). Freed disk space first, since the Mac had 188 MB left. Tested: the API insert works, the constraints reject bad scores/levels/orphan rows/duplicate IDs, and card-history lookups use the index.
- **2026-10-17:** A3 done, so **Phase A is complete**. `scoring.py` was tested on unseen `fraudTest.csv` rows: a real $996 fraud scored 0.998 (high), a normal $53 purchase scored 0.26 (low), a 4-in-an-hour burst made velocity the top reason, and a routine repeat purchase gave "no unusual signals".
- **2026-10-17:** A2 done. Model trained on 1.04M rows and tested on 259K. At a 0.5 cutoff it catches 79% of fraud with 6.8% precision; PR-AUC is 0.21 vs a 0.0058 random baseline. The distance flag turned out to carry no signal (see journal §11).
- **2026-10-17:** A1 done. Feature logic now lives only in `features.py`; `train_model.py` imports it. Checked against hand-made test transactions.
- **2026-10-17:** Created `STATUS.md` and `PROJECT_JOURNAL.md`. Found that the dataset is missing locally.
- **2026-09-19:** First commit `6928f16`: exploration, feature prototype, train/test split, raw insert endpoint.
