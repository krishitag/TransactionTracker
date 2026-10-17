"""Load a realistic slice of fraudTest.csv into the running API, in time order.

Picks cards that had fraud (their 14 days before the first fraud plus 3 days after)
and cards that never did (a similar-length window), so the database holds both
normal spending and fraud bursts with natural card history.

Start the API first, then run from backend/:  venv/bin/python seed_transactions.py
Safe to re-run: transactions already loaded come back as 409 and are skipped.
"""
import json
import sys
import urllib.error
import urllib.request

import pandas as pd

API_URL = "http://localhost:8000/transactions"
DATA_PATH = "../data/fraudTest.csv"
CARDS_PER_GROUP = 20
SEED = 42


def pick_transactions(df):
    df["trans_date_trans_time"] = pd.to_datetime(df["trans_date_trans_time"])
    fraud_cards = df.loc[df["is_fraud"] == 1, "cc_num"].drop_duplicates()
    normal_cards = df.loc[~df["cc_num"].isin(fraud_cards), "cc_num"].drop_duplicates()
    fraud_cards = fraud_cards.sample(CARDS_PER_GROUP, random_state=SEED)
    normal_cards = normal_cards.sample(CARDS_PER_GROUP, random_state=SEED)

    parts = []
    for card in fraud_cards:
        rows = df[df["cc_num"] == card]
        first_fraud = rows.loc[rows["is_fraud"] == 1, "trans_date_trans_time"].min()
        window = rows["trans_date_trans_time"].between(
            first_fraud - pd.Timedelta(days=14), first_fraud + pd.Timedelta(days=3)
        )
        parts.append(rows[window])
    for card in normal_cards:
        rows = df[df["cc_num"] == card]
        start = rows["trans_date_trans_time"].min()
        parts.append(rows[rows["trans_date_trans_time"] <= start + pd.Timedelta(days=17)])

    # Time order, so each card's history exists before its later transactions arrive.
    return pd.concat(parts).sort_values("trans_date_trans_time")


def to_payload(row):
    return {
        "trans_num": row["trans_num"],
        "cc_num": str(row["cc_num"]),
        "merchant": row["merchant"],
        "category": row["category"],
        "amount": float(row["amt"]),
        "trans_time": row["trans_date_trans_time"].isoformat(),
        "cust_lat": float(row["lat"]),
        "cust_long": float(row["long"]),
        "merch_lat": float(row["merch_lat"]),
        "merch_long": float(row["merch_long"]),
        "is_fraud": bool(row["is_fraud"]),
    }


def post(payload):
    request = urllib.request.Request(
        API_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status
    except urllib.error.HTTPError as e:
        return e.code


def main():
    txns = pick_transactions(pd.read_csv(DATA_PATH))
    print(f"Loading {len(txns)} transactions "
          f"({txns['cc_num'].nunique()} cards, {int(txns['is_fraud'].sum())} fraud) into {API_URL}")

    counts = {}
    for i, (_, row) in enumerate(txns.iterrows(), start=1):
        status = post(to_payload(row))
        counts[status] = counts.get(status, 0) + 1
        if status not in (201, 409):
            print(f"Unexpected HTTP {status} for {row['trans_num']}; stopping.")
            sys.exit(1)
        if i % 250 == 0:
            print(f"  {i}/{len(txns)}")
    print("Done. HTTP status counts:", counts)


if __name__ == "__main__":
    main()
