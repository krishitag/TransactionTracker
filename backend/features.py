import pandas as pd
import numpy as np

df = pd.read_csv("../data/fraudTrain.csv", nrows=5000)

df["trans_date_trans_time"] = pd.to_datetime(df["trans_date_trans_time"])
df = df.sort_values(["cc_num", "trans_date_trans_time"])

df = df.set_index("trans_date_trans_time")
rolling_counts = df.groupby("cc_num")["trans_num"].rolling("1h").count()
df["txns_last_hour"] = rolling_counts.reset_index(level=0, drop=True) - 1
df = df.reset_index()

print(df[["cc_num", "trans_date_trans_time", "txns_last_hour"]].head(20))

df["new_merchant"] = ~df.duplicated(subset=["cc_num", "merchant"], keep="first")

print(df[["cc_num", "merchant", "trans_date_trans_time", "new_merchant"]].head(20))
print("Repeat merchant visits found in this sample:", df.duplicated(subset=["cc_num", "merchant"]).sum())
print(df[df["new_merchant"] == False].head(10))

#to calculate coordinate distance between customer and merchant, we can use the haversine formula
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

df["distance_km"] = haversine_distance(df["lat"], df["long"], df["merch_lat"], df["merch_long"])
print(df["distance_km"].describe())

threshold = df["distance_km"].quantile(0.90)
print("90th percentile distance (km):", threshold)

df["merchant_distance_flag"] = df["distance_km"] > threshold
print(df["merchant_distance_flag"].value_counts())

print("Fraud count in this sample:", df["is_fraud"].sum())
