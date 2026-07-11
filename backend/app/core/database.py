import sqlite3
from contextlib import contextmanager

from .config import settings


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or str(settings.DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


@contextmanager
def get_db(db_path: str | None = None):
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def fetch_all(query: str, params: tuple = (), db_path: str | None = None) -> list[dict]:
    with get_db(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def fetch_one(query: str, params: tuple = (), db_path: str | None = None) -> dict | None:
    with get_db(db_path) as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None
