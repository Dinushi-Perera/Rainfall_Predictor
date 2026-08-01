"""
Configuration for RainFall Predict AI.
All values can be overridden with environment variables, so the same
code works locally, in Docker, or on a production host without edits.
"""
import os
from pathlib import Path


def _load_env_file() -> None:
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("$env:"):
            line = line[5:]

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()


class Config:
    # --- MySQL connection -------------------------------------------------
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "rainfall_db")

    # --- Flask --------------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "rainfall-predict-ai-dev-key")
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"

    # --- Model ---------------------------------------------------------------
    MODEL_PATH = os.environ.get(
        "MODEL_PATH", os.path.join(os.path.dirname(__file__), "model", "xgboost_model.joblib")
    )
