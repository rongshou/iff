"""Favorite Schools Repository —— 收藏院校持久化

支持按 auth_code 保存、查询和删除收藏的院校。
表结构:

  favorite_schools
  ├── id            INTEGER PRIMARY KEY AUTOINCREMENT
  ├── auth_code     TEXT NOT NULL           — 用户授权码
  ├── school_name   TEXT NOT NULL           — 院校名称
  ├── country       TEXT                    — 国家
  ├── qs_rank       INTEGER                 — QS 排名
  ├── usnews_rank   INTEGER                 — US News 排名
  ├── match_level   TEXT                    — 匹配等级
  ├── gpa_median    REAL                    — 中位 GPA
  ├── matched_cases INTEGER                 — 匹配案例数
  ├── toefl_req     TEXT                    — 托福要求描述
  ├── meets_toefl   INTEGER                 — 是否满足托福要求 (0/1)
  ├── created_at    TEXT DEFAULT (datetime('now'))
  └── UNIQUE(auth_code, school_name)
"""

import sqlite3
import logging
from typing import Any

from ..core.config import settings

logger = logging.getLogger(__name__)

TABLE = "favorite_schools"

CREATE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auth_code TEXT NOT NULL,
    school_name TEXT NOT NULL,
    country TEXT,
    qs_rank INTEGER,
    usnews_rank INTEGER,
    match_level TEXT,
    gpa_median REAL,
    matched_cases INTEGER,
    toefl_req TEXT,
    meets_toefl INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(auth_code, school_name)
);
CREATE INDEX IF NOT EXISTS idx_fav_auth_code ON {TABLE}(auth_code);
"""


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_favorites_table():
    """确保 favorite_schools 表存在（幂等）。"""
    with _get_conn() as conn:
        conn.executescript(CREATE_SQL)
        conn.commit()


def add_favorite(auth_code: str, school_data: dict[str, Any]) -> dict[str, Any]:
    """保存一个收藏院校。如果已存在相同 auth_code + school_name 则抛出异常。"""
    ensure_favorites_table()
    with _get_conn() as conn:
        try:
            cur = conn.execute(
                f"""INSERT INTO {TABLE}
                    (auth_code, school_name, country, qs_rank, usnews_rank,
                     match_level, gpa_median, matched_cases, toefl_req, meets_toefl)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    auth_code,
                    school_data["school_name"],
                    school_data.get("country"),
                    school_data.get("qs_rank"),
                    school_data.get("usnews_rank"),
                    school_data.get("match_level"),
                    school_data.get("gpa_median"),
                    school_data.get("matched_cases"),
                    school_data.get("toefl_req"),
                    school_data.get("meets_toefl"),
                ),
            )
            conn.commit()
            row = conn.execute(
                f"SELECT * FROM {TABLE} WHERE id = ?",
                (cur.lastrowid,),
            ).fetchone()
            return dict(row)
        except sqlite3.IntegrityError:
            raise ValueError(f"院校 '{school_data['school_name']}' 已经收藏过了")


def get_favorites(auth_code: str) -> list[dict[str, Any]]:
    """获取用户所有收藏院校，按创建时间倒序。"""
    ensure_favorites_table()
    with _get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM {TABLE} WHERE auth_code = ? ORDER BY created_at DESC",
            (auth_code,),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_favorite(auth_code: str, school_name: str) -> bool:
    """删除指定收藏院校。返回是否成功删除。"""
    ensure_favorites_table()
    with _get_conn() as conn:
        cur = conn.execute(
            f"DELETE FROM {TABLE} WHERE auth_code = ? AND school_name = ?",
            (auth_code, school_name),
        )
        conn.commit()
        return cur.rowcount > 0
