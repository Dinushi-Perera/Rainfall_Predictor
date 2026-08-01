# 🌦️ RainFall Predict AI

A Flask web app that predicts whether it will rain today from 11 meteorological
readings, using your trained XGBoost model — with an animated, cute-cloud-mascot
frontend and a MySQL log of every forecast made.

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
│   └── xgboost_model.joblib   # your uploaded model
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

1. You fill in the 11 raw readings (day of year, pressure, max/avg/min temp,
   dew point, humidity, cloud cover, sunshine hours, wind direction, wind speed).
2. The server validates every field (range + required + a min-temp-≤-max-temp
   sanity check) and rejects anything out of bounds with a specific message.
3. `predictor.py` derives the 9 extra features the model was trained on
   (temperature range, dew-point depression, sunshine/cloud ratio, etc. — see
   the docstring at the top of that file for exact formulas) and calls
   `model.predict_proba()`.
4. The result — label + probability — is returned as JSON, rendered with the
   animated mascot/gauge, and logged to the `predictions` table in MySQL.
5. The "Recent Forecasts" table and stats strip read straight from that table.

## Customizing the feature engineering

The uploaded model expects 9 engineered features beyond the 11 raw inputs.
Their exact formulas weren't packaged with the model file, so
`predictor.engineer_features()` uses standard, well-documented meteorological
definitions (temp range, dew-point depression, cyclical day-of-year encoding,
etc.). If your original training notebook computed these differently, open
`predictor.py` and edit that one function — everything else (routes, UI,
validation) stays the same.

## Deploying

For production, run behind gunicorn instead of the Flask dev server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Set `FLASK_DEBUG=0` and a strong `SECRET_KEY` in production.
