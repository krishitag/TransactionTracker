"""Feature engineering shared by training (train_model.py) and live scoring (scoring.py).

Both must import from here so the model always sees features computed the same way.
"""
import numpy as np
import pandas as pd

FEATURE_COLUMNS = ["amt", "txns_last_hour", "new_merchant", "merchant_distance_flag"]

DISTANCE_PERCENTILE = 0.90


def haversine_distance(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two lat/long points."""
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def compute_features(df):
    """Add txns_last_hour, new_merchant and distance_km to a copy of df.

    Expects the raw Sparkov columns: cc_num, merchant, amt, trans_date_trans_time,
    lat, long, merch_lat, merch_long. Rows can be in any order; the result is
    sorted by card, then time. Each card's earlier history must be included, since
    both velocity and new_merchant look backwards through earlier rows.
    """
    df = df.copy()
    df["trans_date_trans_time"] = pd.to_datetime(df["trans_date_trans_time"])
    df = df.sort_values(["cc_num", "trans_date_trans_time"], kind="stable").reset_index(drop=True)

    # Transactions by the same card in the past hour, not counting this one.
    # groupby sorts by cc_num, matching df's order, so positional assignment is safe.
    rolling_counts = (
        df.set_index("trans_date_trans_time")
        .groupby("cc_num")["amt"]
        .rolling("1h")
        .count()
    )
    df["txns_last_hour"] = rolling_counts.to_numpy() - 1

    # True the first time this card pays this merchant.
    df["new_merchant"] = ~df.duplicated(subset=["cc_num", "merchant"], keep="first")

    df["distance_km"] = haversine_distance(df["lat"], df["long"], df["merch_lat"], df["merch_long"])
    return df


def distance_threshold(df):
    """Distance cutoff for the flag. Call on training data only to avoid leakage."""
    return df["distance_km"].quantile(DISTANCE_PERCENTILE)


def add_distance_flag(df, threshold):
    """Add merchant_distance_flag using a threshold learned from training data."""
    df = df.copy()
    df["merchant_distance_flag"] = df["distance_km"] > threshold
    return df


if __name__ == "__main__":
    sample = compute_features(pd.read_csv("../data/fraudTrain.csv", nrows=5000))
    sample = add_distance_flag(sample, distance_threshold(sample))
    print(sample[["cc_num", "trans_date_trans_time", "merchant"] + FEATURE_COLUMNS].head(20))
    print(sample["distance_km"].describe())
    print("Fraud count in this sample:", sample["is_fraud"].sum())
