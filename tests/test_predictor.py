import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from predictor import predict


def test_predict_accepts_full_feature_row():
    payload = {
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

    label, probability = predict(payload)

    assert label in {"Rain", "No Rain"}
    assert 0.0 <= probability <= 1.0
