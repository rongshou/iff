"""werss 数据库操作 —— 封装 news_knowledge 中的 SQL 查询。

覆盖以下数据库操作：
- 文章 ID 列表查询（有正文的文章）
- 按照 ID 获取单篇文章
- 有正文的文章总数
- 游标迭代获取所有文章（增量同步用）
- 降级 LIKE 搜索（_fallback_search）
"""
import sqlite3
from typing import Optional
from ..core.repository import Repository


class WerssRepository(Repository):
    """werss 数据库的文章查询操作。"""

    def get_article_ids_with_content(self) -> list[int]:
        """获取全部有正文的文章 ID（轻量查询）。"""
        rows = self.fetch_all(
            "SELECT id FROM articles WHERE content IS NOT NULL AND length(content) > 100"
        )
        return [r[0] for r in rows]

    def get_article_count_with_content(self) -> int:
        """获取有正文的文章总数。"""
        row = self.fetch_one(
            "SELECT COUNT(*) FROM articles WHERE content IS NOT NULL AND length(content) > 100"
        )
        return row[0] if row else 0

    def get_article_by_id(self, aid: int) -> Optional[dict]:
        """按 ID 获取单篇文章。"""
        row = self.fetch_one(
            "SELECT id, title, content, ai_category FROM articles WHERE id = ?",
            (aid,),
        )
        return dict(row) if row else None

    def iterate_articles_with_content(self) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
        """获取有正文文章的游标迭代器。

        返回 (conn, cursor)，调用方必须在使用后关闭 conn。
        """
        conn = self.get_conn()
        cursor = conn.execute(
            "SELECT id, title, content, ai_category "
            "FROM articles WHERE content IS NOT NULL AND length(content) > 100"
        )
        return conn, cursor

    # ── 资讯列表（给 news.py API 使用） ─────────────────────

    def count_articles(self, where_clause: str, params: tuple) -> int:
        """通用文章计数。"""
        row = self.fetch_one(
            f"SELECT COUNT(*) as total FROM articles {where_clause}", params
        )
        return row["total"] if row else 0

    def list_articles(
        self, where_clause: str, params: tuple, page: int, page_size: int
    ) -> list[dict]:
        """通用文章分页查询（含 ai_category 和 publish_time）。"""
        offset = (page - 1) * page_size
        rows = self.fetch_all(
            f"""
            SELECT id, title, pic_url, url, description, publish_time, mp_id, ai_category
            FROM articles
            {where_clause}
            ORDER BY publish_time DESC
            LIMIT ? OFFSET ?
            """,
            params + (page_size, offset),
        )
        return [dict(r) for r in rows]

    def get_category_counts(self, cat_names: list[str]) -> tuple:
        """聚合查询各 ai_category 的文章数。返回元组顺序同 cat_names。"""
        case_parts = ", ".join(
            f"SUM(CASE WHEN ai_category = ? THEN 1 ELSE 0 END)" for _ in cat_names
        )
        row = self.fetch_one(f"SELECT {case_parts} FROM articles", tuple(cat_names))
        return tuple(row) if row else tuple(0 for _ in cat_names)

    def count_uncategorized(self) -> int:
        """统计 ai_category = '综合资讯' 的文章数。"""
        row = self.fetch_one(
            "SELECT COUNT(*) as c FROM articles WHERE ai_category = '综合资讯'"
        )
        return row["c"] if row else 0

    def get_latest(self, limit: int) -> list[dict]:
        """获取最新文章。"""
        rows = self.fetch_all(
            "SELECT id, title, pic_url, url, description, publish_time, ai_category "
            "FROM articles ORDER BY publish_time DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in rows]

    def search_fallback(self, terms: list[str], limit: int) -> list[dict]:
        """降级方案的 LIKE 搜索（LIMIT 为返回目标值，实际查 limit*2 条用于去重）。"""
        conditions = " OR ".join(
            "(title LIKE ? OR content LIKE ?)" for _ in terms[:4]
        )
        params: list[str | int] = []
        for t in terms[:4]:
            params.extend([f"%{t}%", f"%{t}%"])
        params.append(limit * 2)

        sql = f"""
            SELECT id, title, ai_category, description, content
            FROM articles
            WHERE ({conditions}) AND content IS NOT NULL
            ORDER BY LENGTH(content) DESC
            LIMIT ?
        """
        rows = self.fetch_all(sql, tuple(params))
        return [dict(r) for r in rows]
