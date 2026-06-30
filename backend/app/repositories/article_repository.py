"""文章主库 FTS5 索引操作 —— 封装 news_knowledge 中的 SQL 查询。

覆盖以下数据库操作：
- FTS5 表管理（exists / count / drop / create）
- excluded_articles 查询
- FTS5 文章 ID 列表查询
- FTS5 BM25 搜索
- FTS5 批量插入（共享连接上下文）
"""
import sqlite3
from ..core.repository import Repository


class ArticleRepository(Repository):
    """文章 FTS5 索引相关的数据库操作（主库 advisor.db）。"""

    # ── FTS 表管理 ──────────────────────────────────────────

    def fts_table_exists(self, conn: sqlite3.Connection | None = None) -> bool:
        """检查 articles_fts 表是否存在。"""
        if conn is not None:
            row = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='articles_fts'"
            ).fetchone()
            return row[0] > 0
        row = self.fetch_one(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='articles_fts'"
        )
        return row[0] > 0 if row else False

    def fts_count(self, conn: sqlite3.Connection | None = None) -> int:
        """获取 FTS5 索引中的文章数。"""
        if conn is not None:
            row = conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()
            return row[0]
        row = self.fetch_one("SELECT COUNT(*) FROM articles_fts")
        return row[0] if row else 0

    def drop_fts_table(self, conn: sqlite3.Connection | None = None) -> None:
        """删除 FTS5 表。"""
        if conn is not None:
            conn.execute("DROP TABLE IF EXISTS articles_fts")
            conn.commit()
        else:
            self.execute("DROP TABLE IF EXISTS articles_fts")

    def create_fts_table(self, conn: sqlite3.Connection | None = None) -> None:
        """创建 FTS5 虚拟表（unicode61 分词器）。"""
        sql = """
            CREATE VIRTUAL TABLE articles_fts USING fts5(
                article_id, title, content, ai_category,
                tokenize='unicode61'
            )
        """
        if conn is not None:
            conn.execute(sql)
            conn.commit()
        else:
            self.execute(sql)

    # ── 排除文章列表 ────────────────────────────────────────

    def load_excluded_article_ids(self) -> set[str]:
        """从 excluded_articles 表加载被排除的 article_id 集合。"""
        rows = self.fetch_all("SELECT article_id FROM excluded_articles")
        return {r[0] for r in rows}

    # ── FTS5 记录操作 ───────────────────────────────────────

    def list_fts_article_ids(self, conn: sqlite3.Connection | None = None) -> set[str]:
        """获取 FTS 中已有的 article_id 集合。"""
        if conn is not None:
            rows = conn.execute("SELECT article_id FROM articles_fts").fetchall()
            return {r[0] for r in rows}
        rows = self.fetch_all("SELECT article_id FROM articles_fts")
        return {r[0] for r in rows}

    def insert_into_fts(
        self,
        conn: sqlite3.Connection,
        article_id: str,
        title: str,
        content: str,
        category: str,
    ) -> None:
        """向 FTS5 索引插入一条记录（需传入共享连接）。"""
        conn.execute(
            "INSERT INTO articles_fts(article_id, title, content, ai_category) VALUES (?, ?, ?, ?)",
            (article_id, title, content, category),
        )

    def insert_or_ignore_into_fts(
        self,
        conn: sqlite3.Connection,
        article_id: str,
        title: str,
        content: str,
        category: str,
    ) -> None:
        """向 FTS5 索引插入一条记录，重复则忽略（需传入共享连接）。"""
        conn.execute(
            "INSERT OR IGNORE INTO articles_fts(article_id, title, content, ai_category) VALUES (?, ?, ?, ?)",
            (article_id, title, content, category),
        )

    # ── FTS5 搜索 ───────────────────────────────────────────

    def search_fts(self, fts_query: str, limit: int) -> list[dict]:
        """FTS5 BM25 搜索：标题权重 10x，内容权重 1x。"""
        sql = """
            SELECT article_id, title, content, ai_category,
                   bm25(articles_fts, 10.0, 1.0, 0.0) as rank_score
            FROM articles_fts
            WHERE articles_fts MATCH ?
            ORDER BY rank_score ASC
            LIMIT ?
        """
        rows = self.fetch_all(sql, (fts_query, limit))
        return [dict(r) for r in rows]
