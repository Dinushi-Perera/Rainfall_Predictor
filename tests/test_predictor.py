from __future__ import annotations

import math

import pandas as pd
import pytest

from predictor import FEATURE_ORDER, engineer_features, predict, validate_payload


def test_validate_payload_accepts_raw_payload_and_coerces_strings(raw_payload):
    payload = {key: str(value) for key, value in raw_payload.items()}

    clean, errors = validate_payload(payload)

    assert errors == {}
    assert clean["day"] == 42.0
    assert clean["pressure"] == 1020.4
    assert clean["windspeed"] == 18.5


def test_validate_payload_rejects_missing_fields():
    clean, errors = validate_payload({"day": 1, "pressure": 1000})

    assert clean == {"day": 1.0, "pressure": 1000.0}
    assert errors["maxtemp"] == "Max Temperature is required."
    assert errors["temparature"] == "Average Temperature is required."


def test_validate_payload_rejects_min_temp_above_max_temp(raw_payload):
    payload = dict(raw_payload)
    payload["mintemp"] = 30
    payload["maxtemp"] = 20

    clean, errors = validate_payload(payload)

    assert clean["mintemp"] == 30.0
    assert clean["maxtemp"] == 20.0
    assert errors["mintemp"] == "Min temperature can't be higher than max temperature."


def test_validate_payload_accepts_full_feature_row(full_feature_payload):
    clean, errors = validate_payload(full_feature_payload)

    assert errors == {}
    assert set(clean) == set(full_feature_payload)


def test_engineer_features_derives_expected_columns_from_raw_payload(raw_payload):
    frame = engineer_features(raw_payload)

    assert list(frame.columns) == FEATURE_ORDER
    row = frame.iloc[0].to_dict()
    assert row["temp_range"] == pytest.approx(raw_payload["maxtemp"] - raw_payload["mintemp"])
    assert row["dewpoint_depression"] == pytest.approx(raw_payload["temparature"] - raw_payload["dewpoint"])
    assert row["sunshine_cloud_ratio"] == pytest.approx(raw_payload["sunshine"] / (raw_payload["cloud"] + 1.0))
    assert row["humidity_cloud_interaction"] == pytest.approx((raw_payload["humidity"] * raw_payload["cloud"]) / 100.0)
    assert row["temp_dewpoint_ratio"] == pytest.approx(raw_payload["dewpoint"] / raw_payload["temparature"])
    assert row["wind_power"] == pytest.approx(raw_payload["windspeed"] ** 2)
    assert row["sunshine_humidity_diff"] == pytest.approx(raw_payload["sunshine"] - raw_payload["humidity"])
    assert row["day_sin"] == pytest.approx(math.sin(2 * math.pi * raw_payload["day"] / 365.0))
    assert row["day_cos"] == pytest.approx(math.cos(2 * math.pi * raw_payload["day"] / 365.0))


def test_engineer_features_preserves_complete_feature_row(full_feature_payload):
    frame = engineer_features(full_feature_payload)

    expected = pd.DataFrame([{key: float(value) for key, value in full_feature_payload.items()}], columns=FEATURE_ORDER)
    pd.testing.assert_frame_equal(frame, expected)


def test_predict_uses_model_probability_threshold(monkeypatch, raw_payload):
    class FakeModel:
        def predict_proba(self, frame):
            assert list(frame.columns) == FEATURE_ORDER
            return [[0.2, 0.8]]

    monkeypatch.setattr("predictor.load_model", lambda: FakeModel())

    label, probability = predict(raw_payload)

    assert label == "Rain"
    assert probability == pytest.approx(0.8)
