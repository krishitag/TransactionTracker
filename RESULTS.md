# Results

What the Transaction Risk Platform achieves, measured, with its limits stated plainly. Every number
here comes from a run recorded in [`PROJECT_JOURNAL.md`](PROJECT_JOURNAL.md) (section numbers in brackets).

> **Read this first.** The data is **simulated** (Sparkov, see [Dataset](#dataset)), the model is a
> deliberately simple, interpretable logistic regression, and this is a portfolio project, **not a
> production fraud system**. Scores are *relative risk*, not probabilities.

## At a glance

| | Result |
|---|---|
| Model | Logistic regression on 5 features, with plain-English reasons for every score |
| PR-AUC (held-out test set) | **0.285** for model v2, vs **0.0058** for random guessing (≈ 49×) |
| High-risk band (score ≥ 0.9), test set | **32.9% precision, 59.8% recall** |
| Demo database (2,440 real test-split transactions) | 141 flagged High, **126 of them real fraud (89%)** |
| AI question answering | 8 questions checked against SQL: every cited transaction and statistic correct, trap questions declined |
| Automated tests | **43 passing** (features, scoring, LLM fallback logic); CI on every push |

## Dataset

[**Credit Card Transactions Fraud Detection Dataset**](https://www.kaggle.com/datasets/kartik2112/fraud-detection)
by Kartik Shenoy on Kaggle (licence: CC0 Public Domain), generated with the
[Sparkov data generator](https://github.com/namebrandon/Sparkov_Data_Generation).

| | Rows | Fraud |
|---|---|---|
| `fraudTrain.csv` (used for training and evaluation) | 1,296,675 | 7,506 (**0.58%**) [§2] |
| Training split (80%, stratified) | 1,037,340 | 6,005 [§11] |
| Test split (20%, never seen in training) | 259,335 | 1,501 [§11] |
| `fraudTest.csv` slice loaded into the demo database | 2,440 (40 cards) | 207 (fraud-heavy on purpose) [§17] |

**Why accuracy isn't reported:** with 0.58% fraud, a model that always says "not fraud" is 99.4% accurate
and catches nothing. The model is judged on precision, recall and PR-AUC instead [§2].

## The model

`StandardScaler` + `LogisticRegression(class_weight="balanced")`. Features [§3, §19]:

| Feature | What it measures |
|---|---|
| `amt` | Transaction amount |
| `txns_last_hour` | Other payments on the same card in the previous hour |
| `new_merchant` | First time this card pays this merchant |
| `night_time` | Made between 22:00 and 03:59 |
| `merchant_distance_flag` | Merchant unusually far from the cardholder (carries ~no signal here; see below) |

Each score comes with up to three reasons, from the features that pushed it up most (coefficient × scaled
value), e.g. *"Amount $1,034.66 is about 15x the typical transaction ($70)"*, *"Made at 22:09, in the
22:00-04:00 window when most fraud happens"*.

### Model v1 → v2: finding and adding the night-time signal [§18, §19]

The AI question-answering layer surfaced a pattern the model couldn't see: most fraud happens late at
night. Checked on the training split only (to avoid leakage):

| Hours | Share of transactions | Share of all fraud | Fraud rate |
|---|---|---|---|
| **22:00–03:59** | 23.5% | **84.7%** | **2.09%** |
| all other hours | 76.5% | 15.3% | 0.12% |

Adding `night_time` (model v2, fingerprint `f683e347ae3d`), same test set:

| | v1 (4 features) | v2 (+ night_time) |
|---|---|---|
| PR-AUC | 0.210 | **0.285** (+36%) |
| Alerts at score ≥ 0.9 | 3,476 | **2,725** (−22%) |
| Precision at ≥ 0.9 | 22.9% | **32.9%** |
| Recall at ≥ 0.9 | 53.1% | **59.8%** |
| Night-time fraud caught at ≥ 0.9 | 52.8% | **61.8%** |
| Daytime fraud caught at ≥ 0.9 | 54.6% | 48.5% ⚠️ |

**Risk bands:** High ≥ 0.9, Medium ≥ 0.7, Low below. The medium cutoff moved from 0.5 to 0.7 for v2,
because v2 lifts every night transaction: at 0.7 it gives about the same recall as v1 at 0.5 (76.6% vs
78.9%) with **half the alerts** (8,751 vs 17,472) and about double the precision (13.1% vs 6.8%) [§19].

## The demo database [§19, §25]

2,440 real `fraudTest.csv` transactions, scored by v2 through the live API:

| | Count | Real fraud | Money |
|---|---|---|---|
| High | 141 | **126 (89%)** | $108,017 (42% of all money) |
| Medium | 113 | 28 (25%) | $19,292 (7%) |
| Low | 2,186 | 53 (missed) | $130,932 (51%) |
| **All** | **2,440** | **207** | **$258,240** |

Total alerts (High + Medium) fell from 453 under v1 to **254** under v2, and 61% of them are real fraud
(v1: 36%). Risky transactions are few but large: High is 6% of transactions and 42% of the money.
*Precision here is inflated by the fraud-heavy demo slice; the test-set figures above are the honest ones.*

## AI question answering (`/ask`) [§18, §23]

Hybrid retrieval (keyword filters + pgvector similarity + SQL statistics), a grounded LLM answer
(Gemini 3.8 Flash), and **citation checking in code**: any transaction ID the model cites that it
wasn't given is removed. Answers were checked against the database with SQL:

| Question | Outcome |
|---|---|
| Which spending categories have the most high-risk transactions? | ✅ Exact counts (online shopping 61 of 203, 55 fraud; in-store shopping 27) |
| Show me suspicious late-night online shopping purchases | ✅ All statistics correct; all 8 cited transactions match (amount, time, label) |
| Which merchants have the most high-risk transactions? | ✅ 8 merchants tied at 3; every name, dollar total and citation exact |
| Were there any large travel purchases at night? | ✅ Correct but cautious: all 14 late-night travel transactions are $1.11–$9.12 |
| Why were the high-risk transactions flagged? | ✅ Named the model's signals, 9 valid citations |
| Show me transactions in Mumbai *(trap)* | ✅ Declined: the data has no city names |
| What was the average transaction amount in Mumbai? *(trap)* | ✅ Declined, no invented number |

Invalid citations removed across these runs: **0**.

## Known limitations and blind spots

These are measured, not guessed, and they're the next things to work on:

1. **Small-amount fraud is mostly missed** [§23]. 33 of the 53 frauds scored Low are under $20; 89% of
   sub-$20 fraud scores Low. The model leans on "amount far above normal". In real payments these are often
   *card testing* (a tiny charge before a big one), which needs sequence features.

   | Fraud amount | Fraud | Scored Low | Scored High |
   |---|---|---|---|
   | $100+ | 159 | 13 | 125 |
   | $20–99 | 11 | 7 | 1 |
   | under $20 | 37 | **33** | 0 |

2. **Daytime fraud recall fell with v2** (54.6% → 48.5% at ≥ 0.9). Logistic regression adds evidence, so
   "not at night" now counts against a transaction. Fixes: per-card hour baselines, or a tree model
   (which would need SHAP for explanations).
3. **The distance feature carries no signal on this data** (weight ≈ 0; fraud rate 0.579% far vs 0.575%
   near), because Sparkov places merchants randomly near the customer [§11]. It's kept as an honest finding.
4. **Random, not time-based, train/test split** [§11]. Training on earlier months and testing on later ones
   would be more realistic.
5. **`/ask` statistics are one dimension at a time**, so a question that combines filters gets per-category
   and per-time totals rather than the combination, and can hedge (backlog item 6 in `STATUS.md`).
6. **Free-tier LLM:** Gemini's free tier can be slow or rate-limited; the backend has backup keys, a timeout
   budget under the browser's, and clear error messages [§23].
7. **Simulated data and a scoped model.** Not validated on real transactions, and not a production system.

## How it's verified

- **43 automated tests** (`backend/tests/`): feature maths and window edges, exact risk-band thresholds,
  the model fingerprint, explanation text, a model-quality safety net on a committed 200-row real sample
  (PR-AUC 0.59 vs 0.10 random), and the LLM fallback logic with a fake client (no network or keys).
- **CI** (GitHub Actions): ruff + pytest for the backend; TypeScript, ESLint and a production build for the
  frontend, on every push.
- **Manual end-to-end test** of the dashboard: 18/18 checks, including phone layout, keyboard navigation,
  and the backend-down error state [§23].
- **Design checks:** a browser-based design inspector at three screen widths, the Vercel web interface
  guidelines audit, and WCAG AA contrast on every text colour (lowest 4.7:1) [§22, §25].
