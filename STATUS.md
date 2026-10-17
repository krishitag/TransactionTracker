# Project Status: Transaction Risk Platform

_Last updated: 2026-10-17_

Legend: ✅ done · 🟡 partly done · ⬜ not started · ⛔ blocked

## Right now

- **Current phase:** Phase A (finish the model)
- **Next task:** A3, `scoring.py` (score one transaction + plain-English reasons)
- **Blockers:** none

## What exists today (commit `6928f16`)

| File | State | Notes |
|---|---|---|
| `backend/peek.py` | ✅ | Exploration only. Prints columns and fraud counts. |
| `backend/features.py` | ✅ | Shared feature library: `compute_features`, `distance_threshold`, `add_distance_flag`, `FEATURE_COLUMNS`. |
| `backend/train_model.py` | ✅ | Trains scaled `LogisticRegression(class_weight="balanced")`, prints evaluation, saves bundle. |
| `backend/models/risk_model.joblib` | ✅ | Saved bundle: model + distance threshold + feature list (1.9 KB, committed). |
| `backend/main.py` | 🟡 | `POST /transactions` inserts into Postgres, but the `transactions` table is never created anywhere. No scoring yet. |
| `frontend/` | ⬜ | Empty folder. |

## Phase A: Finish the model

| # | Task | Status |
|---|---|---|
| A1 | One shared `compute_features(df)` in `features.py`, imported by training and scoring | ✅ |
| A2 | Train `LogisticRegression(class_weight="balanced")`, evaluate with precision/recall/confusion matrix, save with joblib | ✅ recall 0.79, precision 0.07 @0.5, PR-AUC 0.21 |
| A3 | `scoring.py`: load model, score one transaction, return ranked plain-English reasons | ⬜ |

## Phase B: Wire it into a real API

| # | Task | Status |
|---|---|---|
| B4 | `schema.sql` with `transactions` + `risk_scores` tables | ⬜ |
| B5 | `requirements.txt` + `docker-compose.yml` (Postgres) | ⬜ |
| B6 | `POST /transactions` pulls card history, scores, writes to `risk_scores` | ⬜ |

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

- **2026-10-17:** A2 done. Model trained on 1.04M rows and tested on 259K. At a 0.5 cutoff it catches 79% of fraud with 6.8% precision; PR-AUC is 0.21 vs a 0.0058 random baseline. The distance flag turned out to carry no signal (see journal §11).
- **2026-10-17:** A1 done. Feature logic now lives only in `features.py`; `train_model.py` imports it. Checked against hand-made test transactions.
- **2026-10-17:** Created `STATUS.md` and `PROJECT_JOURNAL.md`. Found that the dataset is missing locally.
- **2026-09-19:** First commit `6928f16`: exploration, feature prototype, train/test split, raw insert endpoint.
