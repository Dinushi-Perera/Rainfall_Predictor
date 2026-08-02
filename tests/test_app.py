from __future__ import annotations

from datetime import datetime


def test_index_route_renders_weather_form(fresh_app_module):
    client = fresh_app_module.app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "RainFall Predictor" in body
    assert "Today's Readings" in body


def test_predict_route_returns_prediction_json(fresh_app_module, monkeypatch, raw_payload):
    monkeypatch.setattr(fresh_app_module, "validate_payload", lambda data: (raw_payload, {}))
    monkeypatch.setattr(fresh_app_module, "predict", lambda clean: ("Rain", 0.83))
    monkeypatch.setattr(fresh_app_module.db, "save_prediction", lambda *args, **kwargs: 12)

    client = fresh_app_module.app.test_client()
    response = client.post("/predict", json=raw_payload)
    data = response.get_json()

    assert response.status_code == 200
    assert data["ok"] is True
    assert data["prediction"] == "Rain"
    assert data["will_rain"] is True
    assert data["probability"] == 83.0
    assert data["confidence"] == 83.0
    assert data["saved"] is True


def test_predict_route_returns_validation_error(fresh_app_module, monkeypatch):
    monkeypatch.setattr(fresh_app_module, "validate_payload", lambda data: ({}, {"day": "required"}))

    client = fresh_app_module.app.test_client()
    response = client.post("/predict", json={})

    assert response.status_code == 400
    assert response.get_json()["errors"] == {"day": "required"}


def test_predict_route_returns_model_error(fresh_app_module, monkeypatch, raw_payload):
    monkeypatch.setattr(fresh_app_module, "validate_payload", lambda data: (raw_payload, {}))

    def raise_error(_clean):
        raise RuntimeError("boom")

    monkeypatch.setattr(fresh_app_module, "predict", raise_error)

    client = fresh_app_module.app.test_client()
    response = client.post("/predict", json=raw_payload)

    assert response.status_code == 500
    assert response.get_json()["errors"]["_model"].startswith("Prediction failed:")


def test_predict_batch_route_handles_mixed_rows(fresh_app_module, monkeypatch, raw_payload):
    monkeypatch.setattr(fresh_app_module, "validate_payload", lambda row: (row, {}) if row.get("day") != 99 else ({}, {"day": "invalid"}))

    def fake_predict(clean):
        return ("No Rain", 0.25)

    monkeypatch.setattr(fresh_app_module, "predict", fake_predict)

    client = fresh_app_module.app.test_client()
    response = client.post("/predict_batch", json={"rows": [raw_payload, {"day": 99}]})
    data = response.get_json()

    assert response.status_code == 200
    assert data["ok"] is True
    assert data["results"][0]["ok"] is True
    assert data["results"][1]["ok"] is False


def test_history_route_formats_datetime_and_returns_rows(fresh_app_module, monkeypatch):
    monkeypatch.setattr(
        fresh_app_module.db,
        "get_recent_predictions",
        lambda limit=10: [{"id": 1, "created_at": datetime(2026, 8, 2, 12, 34), "day": 42}],
    )

    client = fresh_app_module.app.test_client()
    response = client.get("/history")
    data = response.get_json()

    assert response.status_code == 200
    assert data["history"][0]["created_at"] == "2026-08-02 12:34"


def test_stats_route_returns_db_stats(fresh_app_module, monkeypatch):
    monkeypatch.setattr(
        fresh_app_module.db,
        "get_stats",
        lambda: {"total": 10, "rain_count": 4, "avg_probability": 0.61},
    )

    client = fresh_app_module.app.test_client()
    response = client.get("/stats")

    assert response.status_code == 200
    assert response.get_json()["stats"] == {"total": 10, "rain_count": 4, "avg_probability": 0.61}


def test_404_returns_json_error(fresh_app_module):
    client = fresh_app_module.app.test_client()

    response = client.get("/missing")

    assert response.status_code == 404
    assert response.get_json()["errors"] == {"_route": "Not found"}