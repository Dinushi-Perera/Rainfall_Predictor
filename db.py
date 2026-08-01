"""
Thin MySQL data-access layer built on PyMySQL.

The app must keep working (predictions still render) even if the
database is briefly unreachable, so every function here fails soft:
it logs the problem and returns a safe default instead of crashing
the request.
"""
import logging

import pymysql
from pymysql.cursors import DictCursor

from config import Config

logger = logging.getLogger("rainfall.db")


def get_connection():
    """Open a fresh MySQL connection. Raises on failure — callers decide
    whether that's fatal for their use case."""
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=5,
    )


def init_db():
    """Create the predictions table if it doesn't exist yet. Safe to call
    on every app start."""
    ddl = """
    CREATE TABLE IF NOT EXISTS predictions (
        id                  INT AUTO_INCREMENT PRIMARY KEY,
        created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        day                 SMALLINT NOT NULL,
        pressure            FLOAT NOT NULL,
        maxtemp             FLOAT NOT NULL,
        temparature         FLOAT NOT NULL,
        mintemp             FLOAT NOT NULL,
        dewpoint            FLOAT NOT NULL,
        humidity            FLOAT NOT NULL,
        cloud               FLOAT NOT NULL,
        sunshine            FLOAT NOT NULL,
        winddirection       FLOAT NOT NULL,
        windspeed           FLOAT NOT NULL,
        prediction_label    VARCHAR(16) NOT NULL,
        rain_probability    FLOAT NOT NULL,
        client_ip           VARCHAR(64)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(ddl)
            logger.info("MySQL: predictions table ready.")
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("MySQL not reachable at startup (%s). "
                        "Predictions will still work; history/storage will be skipped "
                        "until the database is available.", exc)


def save_prediction(payload: dict, label: str, probability: float, client_ip: str = None):
    """Persist one prediction. Returns the new row id, or None if the
    database write failed (the caller should not treat that as fatal)."""
    sql = """
    INSERT INTO predictions
        (day, pressure, maxtemp, temparature, mintemp, dewpoint, humidity,
         cloud, sunshine, winddirection, windspeed, prediction_label,
         rain_probability, client_ip)
    VALUES
        (%(day)s, %(pressure)s, %(maxtemp)s, %(temparature)s, %(mintemp)s,
         %(dewpoint)s, %(humidity)s, %(cloud)s, %(sunshine)s,
         %(winddirection)s, %(windspeed)s, %(prediction_label)s,
         %(rain_probability)s, %(client_ip)s)
    """
    params = {**payload, "prediction_label": label, "rain_probability": probability,
              "client_ip": client_ip}
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.lastrowid
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not save prediction to MySQL: %s", exc)
        return None


def get_recent_predictions(limit: int = 10):
    """Return the most recent predictions, newest first. Empty list if the
    database is unavailable."""
    sql = """
        SELECT id, created_at, day, pressure, maxtemp, temparature, mintemp,
               dewpoint, humidity, cloud, sunshine, winddirection, windspeed,
               prediction_label, rain_probability
        FROM predictions
        ORDER BY created_at DESC
        LIMIT %s
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (limit,))
                return cur.fetchall()
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not fetch prediction history from MySQL: %s", exc)
        return []


def get_stats():
    """Return simple aggregate stats for the dashboard strip. Safe default
    of zeros if the database is unavailable."""
    sql = """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN prediction_label = 'Rain' THEN 1 ELSE 0 END) AS rain_count,
            AVG(rain_probability) AS avg_probability
        FROM predictions
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                row = cur.fetchone()
                return {
                    "total": row["total"] or 0,
                    "rain_count": row["rain_count"] or 0,
                    "avg_probability": float(row["avg_probability"] or 0.0),
                }
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not fetch stats from MySQL: %s", exc)
        return {"total": 0, "rain_count": 0, "avg_probability": 0.0}
