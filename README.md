# 🌦️ RainFall Predict AI

A Flask web app that predicts whether it will rain from weather input data using
your trained XGBoost model. It now supports both the original form-style input
and full row-style data from my test CSV files, so you can score all
rows in a dataset instead of only a single 11-field example.

## What's inside

```
rainfall_predict_ai/
├── app.py              # Flask routes (/, /predict, /history, /stats)
├── predictor.py         # Feature engineering + model loading + prediction
├── db.py                 # MySQL access layer (PyMySQL)
├── config.py              # Env-driven configuration
├── schema.sql              # MySQL schema (run once, or let the app auto-create it)
├── requirements.txt
├── model/
│   └── xgboost_model.joblib   # model
├── templates/
│   └── index.html               # single-page UI
└── static/
    ├── css/style.css              # design + animations
    └── js/script.js                 # validation, fetch calls, animation triggers
```

## 1. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Set up MySQL

Create the database and table (or skip this — the app will auto-create the
table on first run if the database itself already exists):

```bash
mysql -u root -p < schema.sql
```

Then set your connection details as environment variables (defaults shown):

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DB=rainfall_db
```

On Windows (PowerShell): `$env:MYSQL_PASSWORD="your_password"`

> The app is resilient to a missing/offline database — predictions will still
> work and display normally, they just won't be logged to History until MySQL
> is reachable.

## 3. Run it

```bash
python app.py
```

Visit **http://localhost:5000**.

## How a prediction works

1. You can submit the original 11 raw readings from the web form.
2. You can also submit a full row-like payload from your CSV data (for example,
   values from `train.csv` or `test.csv`) because the server now accepts the
   same feature structure the model was trained on.
3. The server validates the incoming values, including range checks and a
   min-temp-≤-max-temp sanity check, then passes them through the model.
4. `predictor.py` derives the engineered features the model expects (such as
   temperature range, dew-point depression, sunshine/cloud ratio, and the
   cyclical day-of-year terms) and calls `model.predict_proba()`.
5. The result - label + probability is returned as JSON, rendered with the
   animated mascot/gauge, and logged to the `predictions` table in MySQL.
6. The "Recent Forecasts" table and stats strip read straight from that table.

### Batch prediction

You can also send a batch of rows to the `/predict_batch` endpoint:

```bash
curl -X POST http://localhost:5000/predict_batch \
  -H "Content-Type: application/json" \
  -d '{"rows":[{"day":1,...}, {"day":2,...}]}'
```

This is useful when you want to predict every row in a test file or a full CSV dataset.

## Customizing the feature engineering

The uploaded model expects 20 features in total: 11 raw inputs plus 9 engineered
features. Their exact formulas weren't packaged with the model file, so
`predictor.engineer_features()` uses standard meteorological definitions (temp
range, dew-point depression, cyclical day-of-year encoding, etc.). If your
original training notebook computed these differently, open `predictor.py` and
edit that one function everything else (routes, UI, validation) stays the
same.

## Deploying

For production, run behind gunicorn instead of the Flask dev server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Set `FLASK_DEBUG=0` and a strong `SECRET_KEY` in production.
