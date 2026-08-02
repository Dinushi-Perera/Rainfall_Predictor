from __future__ import annotations

from datetime import datetime

import db


class FakeCursor:
    def __init__(self, rows=None, row=None):
        self.rows = rows if rows is not None else []
        self.row = row if row is not None else {}
        self.executed = []
        self.lastrowid = 77

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def close(self):
        self.closed = True


def test_get_connection_uses_config(monkeypatch):
    captured = {}

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(db.pymysql, "connect", fake_connect)

    connection = db.get_connection()

    assert connection is not None
    assert captured["host"] == db.Config.MYSQL_HOST
    assert captured["port"] == db.Config.MYSQL_PORT
    assert captured["cursorclass"] is db.DictCursor


def test_init_db_logs_warning_when_connection_fails(monkeypatch, caplog):
    def raise_error():
        raise RuntimeError("offline")

    monkeypatch.setattr(db, "get_connection", raise_error)

    db.init_db()

    assert "MySQL not reachable at startup" in caplog.text


def test_save_prediction_inserts_and_returns_lastrowid(monkeypatch):
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: connection)

    row_id = db.save_prediction(
        {
            "day": 1,
            "pressure": 1000,
            "maxtemp": 20,
            "temparature": 18,
            "mintemp": 16,
            "dewpoint": 14,
            "humidity": 70,
            "cloud": 40,
            "sunshine": 5,
            "winddirection": 120,
            "windspeed": 15,
        },
        "Rain",
        0.85,
        client_ip="127.0.0.1",
    )

    assert row_id == 77
    assert connection.closed is True
    assert cursor.executed[0][1]["prediction_label"] == "Rain"
    assert cursor.executed[0][1]["client_ip"] == "127.0.0.1"


def test_save_prediction_returns_none_on_error(monkeypatch):
    def raise_error():
        raise RuntimeError("offline")

    monkeypatch.setattr(db, "get_connection", raise_error)

    assert db.save_prediction({}, "Rain", 0.6) is None


def test_get_recent_predictions_returns_rows(monkeypatch):
    rows = [{"id": 1, "created_at": datetime(2026, 8, 2, 12, 0)}]
    cursor = FakeCursor(rows=rows)
    connection = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: connection)

    result = db.get_recent_predictions(limit=5)

    assert result == rows
    assert connection.closed is True
    assert cursor.executed[0][1] == (5,)


def test_get_stats_returns_safe_defaults_on_error(monkeypatch):
    def raise_error():
        raise RuntimeError("offline")

    monkeypatch.setattr(db, "get_connection", raise_error)

    assert db.get_stats() == {"total": 0, "rain_count": 0, "avg_probability": 0.0}