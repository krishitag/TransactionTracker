"""The saved model, its risk bands and its plain-English reasons."""
from pathlib import Path

import pandas as pd
import pytest
from sklearn.metrics import average_precision_score

from features import add_distance_flag, compute_features
from scoring import load_bundle, model_version, risk_level, score_transaction

SAMPLE = Path(__file__).parent / "data" / "sample.csv"


def txn(time, amt, merchant="Shop A"):
    return {"cc_num": 1, "merchant": merchant, "amt": amt, "trans_date_trans_time": time,
            "lat": 40.0, "long": -74.0, "merch_lat": 40.1, "merch_long": -74.1}


@pytest.mark.parametrize("score, expected", [
    (0.95, "high"), (0.90, "high"), (0.8999, "medium"), (0.70, "medium"), (0.6999, "low"), (0.0, "low"),
])
def test_risk_bands(score, expected):
    assert risk_level(score) == expected


def test_model_is_v2():
    # Changes whenever the model file changes; update deliberately after a retrain.
    assert model_version() == "f683e347ae3d"


def test_large_night_first_time_purchase_is_high_with_reasons():
    result = score_transaction(txn("2020-06-01 23:15:00", 1000.0))
    assert result["risk_level"] == "high"
    reasons = " | ".join(result["reasons"])
    assert "14x the typical transaction" in reasons
    assert "22:00-04:00 window" in reasons
    assert "First time this card has paid Shop A" in reasons


def test_small_daytime_repeat_purchase_is_low_with_no_unusual_signals():
    history = [txn("2020-06-01 12:00:00", 35.0)]
    result = score_transaction(txn("2020-06-03 14:00:00", 40.0), history=history)
    assert result["risk_level"] == "low"
    assert result["reasons"] == ["No unusual signals: amount, activity and merchant all look typical for this card"]


def test_same_purchase_scores_higher_at_night():
    # Journal §19: the night-time feature lifts a $300 first-time purchase from low to medium.
    day = score_transaction(txn("2020-06-01 14:15:00", 300.0))
    night = score_transaction(txn("2020-06-01 23:15:00", 300.0))
    assert day["risk_level"] == "low" and night["risk_level"] == "medium"
    assert night["risk_score"] > day["risk_score"]


def test_merchant_fraud_prefix_is_not_shown_in_reasons():
    result = score_transaction(txn("2020-06-01 23:15:00", 1000.0, merchant="fraud_Price Inc"))
    assert any("First time this card has paid Price Inc" in r for r in result["reasons"])
    assert not any("fraud_" in r for r in result["reasons"])


def test_model_quality_on_committed_sample():
    """Safety net, not a benchmark: 200 real rows (20 fraud). Fails if the model silently degrades."""
    bundle = load_bundle()
    df = add_distance_flag(compute_features(pd.read_csv(SAMPLE)), bundle["distance_threshold"])
    scores = bundle["model"].predict_proba(df[bundle["feature_columns"]].astype(float))[:, 1]
    is_fraud = df["is_fraud"] == 1

    pr_auc = average_precision_score(is_fraud, scores)
    assert pr_auc > 4 * is_fraud.mean()  # measured 0.59 vs a 0.10 random baseline
    assert scores[is_fraud].mean() > scores[~is_fraud].mean() + 0.3  # measured 0.77 vs 0.22
