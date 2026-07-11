"""基础 Repository —— 数据库访问基类。

所有具体 Repository 继承此类，提供统一连接管理和查询接口。
"""
import sqlite3
from typing import Optional


class Repository:
    """数据库操作基类。"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def fetch_one(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        with self.get_conn() as conn:
            return conn.execute(sql, params).fetchone()

    def fetch_all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self.get_conn() as conn:
            return conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple = ()) -> int:
        with self.get_conn() as conn:
            conn.execute(sql, params)
            conn.commit()
            return conn.total_changes

    def execute_many(self, sql: str, params_list: list[tuple]) -> None:
        with self.get_conn() as conn:
            conn.executemany(sql, params_list)
            conn.commit()
