"""
RainFall Predict AI — Flask backend.

Routes
------
GET  /              → main page (form + animated result panel)
POST /predict        → JSON API: validates input, runs the XGBoost model,
                        logs the result to MySQL, returns label + probability
GET  /history         → JSON API: last 10 predictions from MySQL
GET  /stats            → JSON API: aggregate stats for the dashboard strip
"""
import logging

from flask import Flask, jsonify, render_template, request

import db
from config import Config
from predictor import FIELD_SPECS, load_model, predict, validate_payload

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("rainfall.app")

app = Flask(__name__)
app.config.from_object(Config)

# Warm things up at startup so the first request isn't slow.
with app.app_context():
    load_model()
    db.init_db()


@app.route("/")
def index():
    return render_template("index.html", field_specs=FIELD_SPECS)


@app.route("/predict", methods=["POST"])
def predict_route():
    data = request.get_json(silent=True) or request.form.to_dict()

    clean, errors = validate_payload(data)
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    try:
        label, probability = predict(clean)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Prediction failed")
        return jsonify({"ok": False, "errors": {"_model": f"Prediction failed: {exc}"}}), 500

    row_id = db.save_prediction(
        clean, label, probability, client_ip=request.remote_addr
    )

    return jsonify({
        "ok": True,
        "prediction": label,
        "will_rain": label == "Rain",
        "probability": round(probability * 100, 1),
        "confidence": round((probability if label == "Rain" else 1 - probability) * 100, 1),
        "saved": row_id is not None,
        "inputs": clean,
    })


@app.route("/predict_batch", methods=["POST"])
def predict_batch_route():
    payload = request.get_json(silent=True) or request.form.to_dict()
    rows = payload.get("rows") if isinstance(payload, dict) else payload
    if rows is None:
        rows = payload

    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list):
        return jsonify({"ok": False, "errors": {"_payload": "Expected a list of rows."}}), 400

    results = []
    for row in rows:
        clean, errors = validate_payload(row)
        if errors:
            results.append({"ok": False, "errors": errors, "row": row})
            continue
        try:
            label, probability = predict(clean)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Batch prediction failed")
            results.append({"ok": False, "errors": {"_model": str(exc)}, "row": row})
            continue
        results.append({
            "ok": True,
            "prediction": label,
            "will_rain": label == "Rain",
            "probability": round(probability * 100, 1),
            "inputs": clean,
        })

    return jsonify({"ok": True, "results": results})


@app.route("/history")
def history_route():
    rows = db.get_recent_predictions(limit=10)
    # datetime isn't JSON serialisable by default
    for r in rows:
        if "created_at" in r and r["created_at"] is not None:
            r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M")
    return jsonify({"ok": True, "history": rows})


@app.route("/stats")
def stats_route():
    return jsonify({"ok": True, "stats": db.get_stats()})


@app.errorhandler(404)
def not_found(_e):
    return jsonify({"ok": False, "errors": {"_route": "Not found"}}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
