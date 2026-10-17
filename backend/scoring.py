"""Score one incoming transaction and explain the score in plain English.

Uses the bundle saved by train_model.py and the same feature code (features.py)
that training used, so live features match training features exactly.
"""
import hashlib
import os

import joblib
import pandas as pd

from features import add_distance_flag, compute_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "risk_model.joblib")

HIGH_RISK = 0.9
MEDIUM_RISK = 0.5

# Contributions below this are too small to be worth showing as a reason.
MIN_REASON_CONTRIBUTION = 0.1
MAX_REASONS = 3

_bundle = None


def load_bundle():
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def model_version():
    """Short fingerprint of the saved model file; changes whenever the model is retrained."""
    with open(MODEL_PATH, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def risk_level(score):
    if score >= HIGH_RISK:
        return "high"
    if score >= MEDIUM_RISK:
        return "medium"
    return "low"


def _reason_text(feature, row, typical_amt):
    if feature == "amt":
        ratio = row["amt"] / typical_amt
        return f"Amount ${row['amt']:,.2f} is about {ratio:.0f}x the typical transaction (${typical_amt:,.0f})"
    if feature == "txns_last_hour":
        n = int(row["txns_last_hour"])
        return f"{n} other transaction{'s' if n != 1 else ''} on this card in the past hour"
    if feature == "new_merchant":
        # Sparkov prefixes every merchant name with "fraud_"; it isn't a fraud signal.
        merchant = str(row["merchant"]).removeprefix("fraud_")
        return f"First time this card has paid {merchant}"
    if feature == "merchant_distance_flag":
        return f"Merchant is {row['distance_km']:.0f} km from the cardholder's home, farther than usual"
    return feature


def score_transaction(txn, history=None):
    """Score one transaction.

    txn: dict with the raw Sparkov columns (cc_num, merchant, amt,
        trans_date_trans_time, lat, long, merch_lat, merch_long).
    history: earlier transactions for the same card (list of dicts or DataFrame),
        used for velocity and first-time-merchant features. Empty/None means no history.
    """
    bundle = load_bundle()
    model = bundle["model"]
    columns = bundle["feature_columns"]
    scaler, clf = model[0], model[-1]

    history = pd.DataFrame(history if history is not None else [])
    new = pd.DataFrame([txn])
    history["_is_new"] = False
    new["_is_new"] = True

    # New transaction goes last so a history row with the same timestamp counts as earlier.
    feats = compute_features(pd.concat([history, new], ignore_index=True))
    feats = add_distance_flag(feats, bundle["distance_threshold"])
    row = feats[feats["_is_new"]].iloc[0]

    x = row[columns].astype(float).to_frame().T
    score = float(model.predict_proba(x)[0, 1])

    # coefficient x scaled value = how far this feature pushed the score up (+) or down (-),
    # compared with an average transaction.
    scaled = scaler.transform(x)[0]
    contributions = dict(zip(columns, (clf.coef_[0] * scaled).round(3).tolist()))

    typical_amt = scaler.mean_[columns.index("amt")]
    ranked = sorted(contributions.items(), key=lambda kv: kv[1], reverse=True)
    reasons = [
        _reason_text(feature, row, typical_amt)
        for feature, contribution in ranked[:MAX_REASONS]
        if contribution >= MIN_REASON_CONTRIBUTION
    ]
    if not reasons:
        reasons = ["No unusual signals: amount, activity and merchant all look typical for this card"]

    return {
        "risk_score": round(score, 4),
        "risk_level": risk_level(score),
        "reasons": reasons,
        "features": {
            "amt": float(row["amt"]),
            "txns_last_hour": int(row["txns_last_hour"]),
            "new_merchant": bool(row["new_merchant"]),
            "merchant_distance_flag": bool(row["merchant_distance_flag"]),
            "distance_km": round(float(row["distance_km"]), 1),
        },
        "contributions": contributions,
    }
