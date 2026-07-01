"""文章主库 FTS5 索引操作 —— 封装 news_knowledge 中的 SQL 查询。

覆盖以下数据库操作：
- FTS5 表管理（exists / count / drop / create）
- excluded_articles 查询
- FTS5 文章 ID 列表查询
- FTS5 BM25 搜索
- FTS5 批量插入（共享连接上下文）
- kb_processed 知识库查询（新版 AI 结构化数据）
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

    # ── 排除文章管理 ──────────────────────────────────────────

    def add_excluded(self, article_id: str, reason: str, title: str = "") -> None:
        """添加一条排除记录。"""
        self.execute(
            "INSERT OR REPLACE INTO excluded_articles "
            "(article_id, reason, title, created_at) VALUES (?, ?, ?, datetime('now'))",
            (article_id, reason, title[:200]),
        )

    def remove_excluded(self, article_id: str) -> None:
        """移除一条排除记录。"""
        self.execute(
            "DELETE FROM excluded_articles WHERE article_id = ?",
            (article_id,),
        )

    def list_excluded(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """分页获取排除文章列表。"""
        rows = self.fetch_all(
            "SELECT article_id, reason, title, created_at FROM excluded_articles "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [dict(r) for r in rows]

    def count_excluded(self) -> int:
        """获取排除文章总数。"""
        row = self.fetch_one("SELECT COUNT(*) as cnt FROM excluded_articles")
        return row["cnt"] if row else 0

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

    # ── Handbook FTS 搜索 ─────────────────────────────────

    def search_handbook_fts(self, fts_query: str, limit: int) -> list[dict]:
        """搜索 handbook_fts 表，BM25 排序。

        返回字段: school, content, rank
        """
        sql = """
            SELECT hc.school, hc.content, hc.source_file, hc.chunk_index,
                   rank as rank_score
            FROM handbook_fts f
            JOIN handbook_chunks hc ON f.rowid = hc.id
            WHERE handbook_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        rows = self.fetch_all(sql, (fts_query, limit))
        return [dict(r) for r in rows]

    # ================================================================
    # kb_processed 知识库查询（新版 AI 结构化数据）
    # ================================================================

    def kb_table_exists(self, conn: sqlite3.Connection | None = None) -> bool:
        """检查 kb_processed 表是否存在。"""
        if conn is not None:
            row = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='kb_processed'"
            ).fetchone()
            return row[0] > 0
        row = self.fetch_one(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='kb_processed'"
        )
        return row[0] > 0 if row else False

    def kb_count(self, conn: sqlite3.Connection | None = None) -> int:
        """获取 kb_processed 中的文章数。"""
        if conn is not None:
            row = conn.execute("SELECT COUNT(*) FROM kb_processed").fetchone()
            return row[0]
        row = self.fetch_one("SELECT COUNT(*) FROM kb_processed")
        return row[0] if row else 0

    def kb_fts_exists(self, conn: sqlite3.Connection | None = None) -> bool:
        """检查 kb_processed_fts 表是否存在。"""
        if conn is not None:
            row = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='kb_processed_fts'"
            ).fetchone()
            return row[0] > 0
        row = self.fetch_one(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='kb_processed_fts'"
        )
        return row[0] > 0 if row else False

    def search_kb_fts(self, fts_query: str, limit: int) -> list[dict]:
        """搜索 kb_processed_fts，BM25 排序。

        权重分配（列顺序: article_id=0, title=1, summary=2, clean_text=3,
                     article_type=4, countries=5, tags=6）：
        - title: 10x（标题匹配最重要）
        - tags: 8x（关键词标签高权重）
        - summary: 5x（摘要中等权重）
        - countries: 3x（国家匹配）
        - article_type: 2x（类型匹配）
        - clean_text: 1x（全文最低权重）
        - article_id: 0（不参与排序）

        返回字段: article_id, title, summary, article_type, countries, tags,
                  quality_score, publish_time
        """
        sql = """
            SELECT f.article_id,
                   k.title, k.summary, k.article_type, k.countries, k.tags,
                   k.quality_score, k.publish_time,
                   bm25(kb_processed_fts, 0, 10.0, 5.0, 1.0, 2.0, 3.0, 8.0) as rank_score
            FROM kb_processed_fts f
            JOIN kb_processed k ON f.article_id = k.article_id
            WHERE kb_processed_fts MATCH ?
            ORDER BY rank_score ASC
            LIMIT ?
        """
        rows = self.fetch_all(sql, (fts_query, limit))
        return [dict(r) for r in rows]

    def get_kb_article(self, article_id: str) -> dict | None:
        """获取单条 kb_processed 文章详情。"""
        row = self.fetch_one(
            "SELECT * FROM kb_processed WHERE article_id = ?",
            (article_id,),
        )
        return dict(row) if row else None

    def list_kb_article_ids(self, conn: sqlite3.Connection | None = None) -> set[str]:
        """获取 kb_processed 中已有的 article_id 集合。"""
        if conn is not None:
            rows = conn.execute("SELECT article_id FROM kb_processed").fetchall()
            return {r[0] for r in rows}
        rows = self.fetch_all("SELECT article_id FROM kb_processed")
        return {r[0] for r in rows}
