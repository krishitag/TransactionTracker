import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

df = pd.read_csv("../data/fraudTrain.csv")
print("Total rows loaded:", len(df))

df["trans_date_trans_time"] = pd.to_datetime(df["trans_date_trans_time"])
df = df.sort_values(["cc_num", "trans_date_trans_time"])

df = df.set_index("trans_date_trans_time")
rolling_counts = df.groupby("cc_num")["trans_num"].rolling("1h").count()
df["txns_last_hour"] = rolling_counts.reset_index(level=0, drop=True) - 1
df = df.reset_index()

df["new_merchant"] = ~df.duplicated(subset=["cc_num", "merchant"], keep="first")

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

df["distance_km"] = haversine_distance(df["lat"], df["long"], df["merch_lat"], df["merch_long"])

X = df[["amt", "txns_last_hour", "new_merchant", "distance_km"]].copy()
y = df["is_fraud"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

threshold = X_train["distance_km"].quantile(0.90)
print("Distance threshold (from training data only):", threshold)

X_train["merchant_distance_flag"] = X_train["distance_km"] > threshold
X_test["merchant_distance_flag"] = X_test["distance_km"] > threshold

X_train = X_train.drop(columns=["distance_km"])
X_test = X_test.drop(columns=["distance_km"])

print("Train shape:", X_train.shape)
print("Test shape:", X_test.shape)
print("Fraud in train:", y_train.sum(), "/", len(y_train))
print("Fraud in test:", y_test.sum(), "/", len(y_test))
