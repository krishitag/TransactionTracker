"""Feature maths: the inputs the model sees must be computed exactly as intended."""
import pandas as pd
import pytest

from features import NIGHT_HOURS, compute_features, haversine_distance


def txn(time, cc=1, merchant="Shop A", amt=10.0):
    return {"cc_num": cc, "merchant": merchant, "amt": amt, "trans_date_trans_time": time,
            "lat": 40.0, "long": -74.0, "merch_lat": 40.1, "merch_long": -74.1}


def features_of(*rows):
    return compute_features(pd.DataFrame(rows))


@pytest.mark.parametrize("time, expected", [
    ("2020-06-01 22:00:00", True),   # window opens
    ("2020-06-01 23:15:00", True),
    ("2020-06-01 03:59:00", True),   # last minute inside
    ("2020-06-01 04:00:00", False),  # window closes
    ("2020-06-01 14:15:00", False),
])
def test_night_time_window_edges(time, expected):
    assert bool(features_of(txn(time))["night_time"].iloc[0]) is expected


def test_night_hours_are_22_to_03():
    assert NIGHT_HOURS == {22, 23, 0, 1, 2, 3}


def test_txns_last_hour_counts_earlier_payments_on_the_same_card():
    f = features_of(txn("2020-06-01 10:00:00"), txn("2020-06-01 10:20:00"), txn("2020-06-01 10:50:00"))
    assert f["txns_last_hour"].tolist() == [0, 1, 2]


def test_txns_last_hour_ignores_payments_over_an_hour_ago():
    f = features_of(txn("2020-06-01 08:59:00"), txn("2020-06-01 10:00:00"))
    assert f["txns_last_hour"].tolist() == [0, 0]


def test_txns_last_hour_ignores_other_cards():
    f = features_of(txn("2020-06-01 10:00:00", cc=1), txn("2020-06-01 10:05:00", cc=2))
    assert f["txns_last_hour"].tolist() == [0, 0]


def test_new_merchant_only_on_first_visit_per_card():
    f = features_of(
        txn("2020-06-01 10:00:00", cc=1, merchant="Shop A"),
        txn("2020-06-02 10:00:00", cc=1, merchant="Shop A"),  # repeat visit
        txn("2020-06-03 10:00:00", cc=2, merchant="Shop A"),  # same shop, different card
    )
    assert f["new_merchant"].tolist() == [True, False, True]


def test_rows_in_any_order_are_sorted_by_card_then_time():
    f = features_of(txn("2020-06-01 12:00:00"), txn("2020-06-01 11:30:00"))
    assert f["txns_last_hour"].tolist() == [0, 1]
    assert f["trans_date_trans_time"].is_monotonic_increasing


def test_haversine_one_degree_of_latitude_is_about_111_km():
    assert haversine_distance(0.0, 0.0, 1.0, 0.0) == pytest.approx(111.2, abs=0.5)
    assert haversine_distance(40.0, -74.0, 40.0, -74.0) == 0
