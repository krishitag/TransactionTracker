# Project Status: Transaction Risk Platform

_Last updated: 2026-10-17_

Legend: ✅ done · 🟡 partly done · ⬜ not started · ⛔ blocked

## Right now

- **Current phase:** Phase A (finish the model)
- **Next task:** A1, consolidate feature engineering into one `compute_features(df)` function
- **Blocker:** `data/fraudTrain.csv` is missing from disk (the `data/` folder is empty). Re-download it from Kaggle (`kartik2112/fraud-detection`) into `data/` before running `train_model.py`.

## What exists today (commit `6928f16`)

| File | State | Notes |
|---|---|---|
| `backend/peek.py` | ✅ | Exploration only. Prints columns and fraud counts. |
| `backend/features.py` | 🟡 | Prototype on a 5,000-row sample. Print-heavy, not importable. |
| `backend/train_model.py` | 🟡 | Loads the data, builds features, splits train/test. **Doesn't train or save a model yet.** |
| `backend/main.py` | 🟡 | `POST /transactions` inserts into Postgres, but the `transactions` table is never created anywhere. No scoring yet. |
| `frontend/` | ⬜ | Empty folder. |

## Phase A: Finish the model

| # | Task | Status |
|---|---|---|
| A1 | One shared `compute_features(df)` in `features.py`, imported by training and scoring | ⬜ |
| A2 | Train `LogisticRegression(class_weight="balanced")`, evaluate with precision/recall/confusion matrix, save with joblib | ⛔ needs dataset |
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

- **2026-10-17:** Created `STATUS.md` and `PROJECT_JOURNAL.md`. Found that the dataset is missing locally.
- **2026-09-19:** First commit `6928f16`: exploration, feature prototype, train/test split, raw insert endpoint.
