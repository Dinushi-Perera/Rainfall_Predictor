from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def raw_payload():
    return {
        "day": 42,
        "pressure": 1020.4,
        "maxtemp": 22.5,
        "temparature": 20.1,
        "mintemp": 18.2,
        "dewpoint": 16.0,
        "humidity": 78.0,
        "cloud": 60.0,
        "sunshine": 4.2,
        "winddirection": 35.0,
        "windspeed": 18.5,
    }


@pytest.fixture
def full_feature_payload(raw_payload):
    return {
        **raw_payload,
        "temp_range": 4.3,
        "dewpoint_depression": 4.1,
        "sunshine_cloud_ratio": 4.2 / 61.0,
        "humidity_cloud_interaction": 46.8,
        "temp_dewpoint_ratio": 16.0 / 20.1,
        "wind_power": 18.5 ** 2,
        "sunshine_humidity_diff": 4.2 - 78.0,
        "day_sin": 0.0,
        "day_cos": 1.0,
    }


@pytest.fixture
def fresh_app_module(monkeypatch):
    import db
    import predictor

    monkeypatch.setattr(predictor, "load_model", lambda: None)
    monkeypatch.setattr(db, "init_db", lambda: None)

    sys.modules.pop("app", None)
    module = importlib.import_module("app")
    module.app.config.update(TESTING=True)

    yield module

    sys.modules.pop("app", None)