"""
Loads the trained XGBoost model and turns raw meteorological inputs into
the 20-feature vector it expects, then returns a clean prediction.

The model was trained on these engineered features (in this exact order):
    day, pressure, maxtemp, temparature, mintemp, dewpoint, humidity,
    cloud, sunshine, winddirection, windspeed, temp_range,
    dewpoint_depression, sunshine_cloud_ratio, humidity_cloud_interaction,
    temp_dewpoint_ratio, wind_power, sunshine_humidity_diff, day_sin, day_cos

The 11 raw fields are the ones collected from the user. The remaining 9
are derived below from standard meteorological relationships:

  - temp_range                 = maxtemp - mintemp
  - dewpoint_depression         = temparature - dewpoint  (how far air is from saturation)
  - sunshine_cloud_ratio        = sunshine / (cloud + 1)
  - humidity_cloud_interaction  = humidity * cloud / 100
  - temp_dewpoint_ratio         = dewpoint / temparature   (guarded against div-by-zero)
  - wind_power                  = windspeed ** 2           (kinetic-energy-like proxy)
  - sunshine_humidity_diff      = sunshine - humidity
  - day_sin / day_cos           = cyclical encoding of day-of-year (sin/cos on a 365-day period)

If your original training pipeline defined these differently, edit the
`engineer_features` function below to match — the rest of the app is
unaffected.
"""
import logging
import math

import joblib
import pandas as pd

from config import Config

logger = logging.getLogger("rainfall.predictor")

FEATURE_ORDER = [
    "day", "pressure", "maxtemp", "temparature", "mintemp", "dewpoint",
    "humidity", "cloud", "sunshine", "winddirection", "windspeed",
    "temp_range", "dewpoint_depression", "sunshine_cloud_ratio",
    "humidity_cloud_interaction", "temp_dewpoint_ratio", "wind_power",
    "sunshine_humidity_diff", "day_sin", "day_cos",
]

RAW_FIELDS = [
    "day", "pressure", "maxtemp", "temparature", "mintemp", "dewpoint",
    "humidity", "cloud", "sunshine", "winddirection", "windspeed",
]

# (min, max, label, unit) — used for both server-side validation and the
# client-side form hints so the two never drift apart.
FIELD_SPECS = {
    "day":           (1, 366, "Day of Year", ""),
    "pressure":      (870, 1085, "Atmospheric Pressure", "hPa"),
    "maxtemp":       (-30, 55, "Max Temperature", "°C"),
    "temparature":   (-30, 55, "Average Temperature", "°C"),
    "mintemp":       (-30, 55, "Min Temperature", "°C"),
    "dewpoint":      (-40, 40, "Dew Point", "°C"),
    "humidity":      (0, 100, "Humidity", "%"),
    "cloud":         (0, 100, "Cloud Cover", "%"),
    "sunshine":      (0, 15, "Sunshine", "hrs"),
    "winddirection": (0, 360, "Wind Direction", "°"),
    "windspeed":     (0, 200, "Wind Speed", "km/h"),
}

_model = None


def load_model():
    global _model
    if _model is None:
        logger.info("Loading XGBoost model from %s", Config.MODEL_PATH)
        _model = joblib.load(Config.MODEL_PATH)
    return _model


def validate_payload(data: dict):
    """Validate raw input dict. Returns (clean_dict, errors_dict)."""
    clean = {}
    errors = {}
    for field, (lo, hi, label, unit) in FIELD_SPECS.items():
        raw = data.get(field, None)
        if raw is None or str(raw).strip() == "":
            errors[field] = f"{label} is required."
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            errors[field] = f"{label} must be a number."
            continue
        if not (lo <= value <= hi):
            errors[field] = f"{label} must be between {lo} and {hi}{(' ' + unit) if unit else ''}."
            continue
        clean[field] = value

    # Cross-field sanity checks (only if the individual fields already passed)
    if "mintemp" in clean and "maxtemp" in clean and clean["mintemp"] > clean["maxtemp"]:
        errors["mintemp"] = "Min temperature can't be higher than max temperature."

    return clean, errors


def engineer_features(clean: dict) -> pd.DataFrame:
    day = clean["day"]
    pressure = clean["pressure"]
    maxtemp = clean["maxtemp"]
    temparature = clean["temparature"]
    mintemp = clean["mintemp"]
    dewpoint = clean["dewpoint"]
    humidity = clean["humidity"]
    cloud = clean["cloud"]
    sunshine = clean["sunshine"]
    winddirection = clean["winddirection"]
    windspeed = clean["windspeed"]

    temp_range = maxtemp - mintemp
    dewpoint_depression = temparature - dewpoint
    sunshine_cloud_ratio = sunshine / (cloud + 1.0)
    humidity_cloud_interaction = (humidity * cloud) / 100.0
    temp_dewpoint_ratio = dewpoint / temparature if temparature != 0 else 0.0
    wind_power = windspeed ** 2
    sunshine_humidity_diff = sunshine - humidity
    day_sin = math.sin(2 * math.pi * day / 365.0)
    day_cos = math.cos(2 * math.pi * day / 365.0)

    row = {
        "day": day, "pressure": pressure, "maxtemp": maxtemp,
        "temparature": temparature, "mintemp": mintemp, "dewpoint": dewpoint,
        "humidity": humidity, "cloud": cloud, "sunshine": sunshine,
        "winddirection": winddirection, "windspeed": windspeed,
        "temp_range": temp_range, "dewpoint_depression": dewpoint_depression,
        "sunshine_cloud_ratio": sunshine_cloud_ratio,
        "humidity_cloud_interaction": humidity_cloud_interaction,
        "temp_dewpoint_ratio": temp_dewpoint_ratio, "wind_power": wind_power,
        "sunshine_humidity_diff": sunshine_humidity_diff,
        "day_sin": day_sin, "day_cos": day_cos,
    }
    return pd.DataFrame([row], columns=FEATURE_ORDER)


def predict(clean: dict):
    """Returns (label:str, probability:float 0..1)."""
    model = load_model()
    X = engineer_features(clean)
    proba = model.predict_proba(X)[0]
    # class order matches model.classes_; assume binary [No Rain, Rain] style
    # (index 1 = positive class, i.e. "will rain")
    rain_probability = float(proba[1]) if len(proba) > 1 else float(proba[0])
    label = "Rain" if rain_probability >= 0.5 else "No Rain"
    return label, rain_probability
