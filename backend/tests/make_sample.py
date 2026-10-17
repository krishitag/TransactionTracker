"""Build the small committed test sample from the full (uncommitted) Sparkov test split.

Run once from backend/:  venv/bin/python tests/make_sample.py
The full CSVs are too big for GitHub, so CI tests use this ~200-row file instead.
Fixed random seed: re-running gives the same rows.
"""
from pathlib import Path

import pandas as pd

SOURCE = Path(__file__).resolve().parents[2] / "data" / "fraudTest.csv"
TARGET = Path(__file__).resolve().parent / "data" / "sample.csv"
COLUMNS = ["trans_num", "cc_num", "merchant", "category", "amt", "trans_date_trans_time",
           "lat", "long", "merch_lat", "merch_long", "is_fraud"]
N_FRAUD, N_NORMAL, SEED = 20, 180, 42


def main():
    df = pd.read_csv(SOURCE, usecols=COLUMNS)
    sample = pd.concat([
        df[df["is_fraud"] == 1].sample(N_FRAUD, random_state=SEED),
        df[df["is_fraud"] == 0].sample(N_NORMAL, random_state=SEED),
    ]).sort_values("trans_date_trans_time")
    TARGET.parent.mkdir(exist_ok=True)
    sample[COLUMNS].to_csv(TARGET, index=False)
    print(f"wrote {len(sample)} rows ({sample['is_fraud'].sum()} fraud) to {TARGET}")


if __name__ == "__main__":
    main()
