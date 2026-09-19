import pandas as pd

df = pd.read_csv("../data/fraudTrain.csv", nrows=1000)

print("Columns:")
print(list(df.columns))
print()
print("First 3 rows:")
print(df.head(3))
print()
print("How many of these 1000 are fraud?")
print(df["is_fraud"].value_counts())

lf = pd.read_csv("../data/fraudTrain.csv", usecols=["is_fraud"])
print("Total rows:", len(lf))
print(lf["is_fraud"].value_counts())