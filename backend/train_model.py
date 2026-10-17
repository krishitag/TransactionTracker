import os

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from features import FEATURE_COLUMNS, add_distance_flag, compute_features, distance_threshold

MODEL_PATH = "models/risk_model.joblib"

df = pd.read_csv("../data/fraudTrain.csv")
print("Total rows loaded:", len(df))

df = compute_features(df)

X = df[["amt", "txns_last_hour", "new_merchant", "distance_km"]].copy()
y = df["is_fraud"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

threshold = distance_threshold(X_train)
print("Distance threshold (from training data only):", threshold)

X_train = add_distance_flag(X_train, threshold)[FEATURE_COLUMNS].astype(float)
X_test = add_distance_flag(X_test, threshold)[FEATURE_COLUMNS].astype(float)

print("Train shape:", X_train.shape)
print("Test shape:", X_test.shape)
print("Fraud in train:", y_train.sum(), "/", len(y_train))
print("Fraud in test:", y_test.sum(), "/", len(y_test))

# Scaling puts every feature on the same footing, so coefficients are comparable
# and coefficient x scaled value is a fair per-feature contribution.
model = make_pipeline(
    StandardScaler(),
    LogisticRegression(class_weight="balanced", max_iter=1000),
)
model.fit(X_train, y_train)

# Accuracy is misleading at a 0.58% fraud rate, so report precision/recall instead.
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

print("\nConfusion matrix (rows = actual, cols = predicted; [not fraud, fraud]):")
print(confusion_matrix(y_test, y_pred))
print("\nClassification report:")
print(classification_report(y_test, y_pred, target_names=["not fraud", "fraud"], digits=3))
print("PR-AUC (average precision):", round(average_precision_score(y_test, y_proba), 3))
print("Baseline PR-AUC (random guessing = fraud rate):", round(y_test.mean(), 4))

print("\nCoefficients (on scaled features):")
for name, coef in zip(FEATURE_COLUMNS, model[-1].coef_[0]):
    print(f"  {name:>24}: {coef:+.3f}")

os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
joblib.dump(
    {"model": model, "distance_threshold": threshold, "feature_columns": FEATURE_COLUMNS},
    MODEL_PATH,
)
print("\nSaved model bundle to", MODEL_PATH)
