"""通路学校数据库操作。"""
import sqlite3
from typing import Optional
from ..core.repository import Repository


class PathwayRepository(Repository):
    """预科/通路学校查询。"""

    def load_all(self, table: str) -> list[dict]:
        """读取指定通路表全部数据。"""
        rows = self.fetch_all(f"SELECT * FROM {table}")
        return [dict(r) for r in rows]

    def find_university(self, name: str) -> Optional[dict]:
        """按名称查找院校。"""
        row = self.fetch_one(
            "SELECT id, name, country, qs_rank, usnews_rank FROM universities WHERE name = ? LIMIT 1",
            (name,),
        )
        return dict(row) if row else None
