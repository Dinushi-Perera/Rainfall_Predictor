# 🌦️ RainFall Predictor

Flask app for predicting rainfall from weather inputs using a trained XGBoost model.
It supports the 11 raw weather fields from the web form, batch row input, MySQL-backed
history/statistics, local pytest coverage, and Docker-based execution.

## Project Layout

```text
app.py                  Flask routes and API endpoints
predictor.py            Payload validation, feature engineering, model prediction
db.py                   MySQL access helpers
config.py               Environment-driven configuration
model/xgboost_model.joblib   Trained model artifact
templates/index.html    Frontend UI
static/                 CSS and browser-side JavaScript
tests/                  Pytest suite for predictor, DB, and Flask routes
Dockerfile              Container image definition
docker-compose.yml      Local container run with host port mapping
requirements.txt        Python dependencies
schema.sql              Optional MySQL schema bootstrap
```

## Requirements

- Python 3.11+
- pip
- Optional: Docker and Docker Compose
- Optional: MySQL if you want prediction history and dashboard stats persisted

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The app reads settings from environment variables or from a root-level `.env` file
using standard `KEY=VALUE` lines.

Example:

MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=rainfall_db
```

If MySQL is unavailable, predictions still work. Only history and stats are skipped.

## Run Locally

Start the Flask app:

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

## Testing

Run the full test suite with the workspace virtual environment:

```bash
.venv\Scripts\python.exe -m pytest -q
```

The tests cover:

- payload validation
- feature engineering
- model prediction flow
- database helper behavior
- Flask routes and JSON responses

## Docker

The container now runs the app through Gunicorn on `0.0.0.0:5000`, so the service
is reachable from the host when the port is published.

### Build the Image

```bash
docker build -t rainfall-predictor .
```

### Run the Container

```bash
docker run --rm -p 5000:5000 rainfall-predictor
```

Then open:
### Run With Docker Compose

```bash
docker compose up --build
```

Docker Compose publishes the app on port 5000 automatically.

## API Endpoints

- `GET /` - main UI
- `POST /predict` - single prediction
- `POST /predict_batch` - batch prediction
- `GET /history` - recent predictions
- `GET /stats` - dashboard stats

## Batch Prediction Example

```bash
curl -X POST http://localhost:5000/predict_batch \
   -H "Content-Type: application/json" \
   -d '{"rows":[{"day":1,"pressure":1000,"maxtemp":25,"temparature":23,"mintemp":20,"dewpoint":18,"humidity":70,"cloud":40,"sunshine":5,"winddirection":180,"windspeed":15}]}'
```

## Notes on the Model

The model expects 20 features total: 11 raw fields and 9 engineered fields.
`predictor.py` builds the engineered values automatically when only the raw weather
inputs are provided.

## Troubleshooting

- If the app opens on `127.0.0.1:5000` inside the container but not from your browser,
   make sure you published the port with `-p 5000:5000` or used Docker Compose.
- If Docker Compose fails to read `.env`, keep that file in standard `KEY=VALUE` format.
- If predictions work but history is empty, MySQL is likely unavailable or misconfigured.

A Flask web app that predicts whether it will rain from weather input data using
your trained XGBoost model. It now supports both the original form-style input
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
