"""知识库管理 API —— 排除文章、统计、重建索引、批量操作。"""
import time
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
from fastapi import APIRouter, Query, Body
from typing import Optional
from pydantic import BaseModel

from ..core.config import settings
from ..core.database import get_db
from ..repositories import ArticleRepository

router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])

# ---------------------------------------------------------------------------
# Repository（惰性初始化）
# ---------------------------------------------------------------------------

_article_repo: ArticleRepository | None = None


def _get_article_repo() -> ArticleRepository:
    global _article_repo
    if _article_repo is None:
        _article_repo = ArticleRepository(str(settings.DB_PATH))
    return _article_repo


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ExcludeRequest(BaseModel):
    article_id: str
    reason: str = "manual"
    title: str = ""


class BulkExcludeRequest(BaseModel):
    """批量排除条件（至少提供一个）"""
    mp_id: Optional[str] = None          # 按公众号排除
    category: Optional[str] = None       # 按分类排除
    older_than_days: Optional[int] = None  # 排除 N 天前的文章


# ---------------------------------------------------------------------------
# 排除文章管理
# ---------------------------------------------------------------------------

@router.get("/excluded")
def list_excluded(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    reason: Optional[str] = None,
):
    """查看被排除的文章列表（分页）。"""
    repo = _get_article_repo()
    offset = (page - 1) * page_size

    if reason:
        total_row = repo.fetch_one(
            "SELECT COUNT(*) as cnt FROM excluded_articles WHERE reason = ?",
            (reason,),
        )
        total = total_row["cnt"] if total_row else 0
        rows = repo.fetch_all(
            "SELECT article_id, reason, title, created_at FROM excluded_articles "
            "WHERE reason = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (reason, page_size, offset),
        )
    else:
        total_row = repo.fetch_one("SELECT COUNT(*) as cnt FROM excluded_articles")
        total = total_row["cnt"] if total_row else 0
        rows = repo.fetch_all(
            "SELECT article_id, reason, title, created_at FROM excluded_articles "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (page_size, offset),
        )

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/excluded")
def add_excluded(req: ExcludeRequest):
    """手动排除指定文章。"""
    repo = _get_article_repo()
    now = datetime.now().isoformat()
    try:
        repo.execute(
            "INSERT OR REPLACE INTO excluded_articles (article_id, reason, title, created_at) "
            "VALUES (?, ?, ?, ?)",
            (req.article_id, req.reason, req.title, now),
        )
        return {"ok": True, "article_id": req.article_id, "reason": req.reason}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.delete("/excluded/{article_id}")
def remove_excluded(article_id: str):
    """恢复被排除的文章。"""
    repo = _get_article_repo()
    try:
        repo.execute(
            "DELETE FROM excluded_articles WHERE article_id = ?",
            (article_id,),
        )
        return {"ok": True, "article_id": article_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# 批量操作
# ---------------------------------------------------------------------------

@router.post("/bulk-exclude")
def bulk_exclude(req: BulkExcludeRequest):
    """按条件批量排除文章。

    将匹配到的文章写入 excluded_articles 表，不直接删除原始数据。
    """
    repo = _get_article_repo()
    now = datetime.now().isoformat()
    excluded_count = 0

    # 从 werss.db 查找匹配的文章
    werss_conn = sqlite3.connect(settings.WERS_DB_PATH)
    werss_conn.row_factory = sqlite3.Row

    try:
        conditions = []
        params = []

        if req.mp_id:
            conditions.append("mp_id = ?")
            params.append(req.mp_id)
        if req.category:
            conditions.append("ai_category = ?")
            params.append(req.category)
        if req.older_than_days:
            cutoff = int(time.time()) - req.older_than_days * 86400
            conditions.append("publish_time < ?")
            params.append(cutoff)

        if not conditions:
            return {"ok": False, "error": "至少提供一个过滤条件"}

        where = " AND ".join(conditions)
        rows = werss_conn.execute(
            f"SELECT id, title FROM articles WHERE {where}", params
        ).fetchall()

        for row in rows:
            article_id = str(row["id"])
            title = row["title"] or ""
            reason_parts = []
            if req.mp_id:
                reason_parts.append(f"mp:{req.mp_id}")
            if req.category:
                reason_parts.append(f"cat:{req.category}")
            if req.older_than_days:
                reason_parts.append(f"old:{req.older_than_days}d")
            reason = ",".join(reason_parts)

            try:
                repo.execute(
                    "INSERT OR IGNORE INTO excluded_articles (article_id, reason, title, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (article_id, reason, title[:200], now),
                )
                excluded_count += 1
            except Exception as e:
                logger.warning("Insert into excluded_articles failed: %s", e, exc_info=True)

    finally:
        werss_conn.close()

    return {
        "ok": True,
        "excluded_count": excluded_count,
    }


# ---------------------------------------------------------------------------
# 知识库统计
# ---------------------------------------------------------------------------

@router.get("/stats")
def knowledge_stats():
    """返回知识库统计信息。

    包含：
    - kb_processed: AI 结构化知识库（新）
    - articles_fts: 旧 FTS5 索引（过渡期）
    - excluded_articles: 排除列表
    - handbook_fts: 院校手册
    - essay 知识库
    """
    repo = _get_article_repo()

    # ── kb_processed 统计（新知识库）──
    kb_count = 0
    kb_by_type = {}
    kb_quality_dist = {}
    try:
        kb_count = repo.kb_count()
        # 按文章类型分布
        type_rows = repo.fetch_all(
            "SELECT article_type, COUNT(*) as cnt FROM kb_processed "
            "GROUP BY article_type ORDER BY cnt DESC"
        )
        kb_by_type = {r["article_type"]: r["cnt"] for r in type_rows}
        # 质量评分分布
        quality_rows = repo.fetch_all(
            "SELECT CASE "
            "  WHEN quality_score >= 0.8 THEN 'high' "
            "  WHEN quality_score >= 0.5 THEN 'medium' "
            "  ELSE 'low' END as tier, "
            "COUNT(*) as cnt FROM kb_processed GROUP BY tier"
        )
        kb_quality_dist = {r["tier"]: r["cnt"] for r in quality_rows}
    except Exception as e:
        logger.warning("Query kb_processed stats failed: %s", e, exc_info=True)

    # ── 旧 FTS 索引统计（过渡期）──
    old_fts_count = 0
    try:
        old_fts_count = repo.fts_count()
    except Exception as e:
        logger.warning("Query fts_count failed: %s", e, exc_info=True)

    # ── 处理状态统计（kb_pipeline 产出）──
    process_state = {}
    try:
        state_rows = repo.fetch_all(
            "SELECT status, COUNT(*) as cnt FROM kb_process_state GROUP BY status"
        )
        process_state = {r["status"]: r["cnt"] for r in state_rows}
    except Exception as e:
        logger.warning("Query kb_process_state failed: %s", e, exc_info=True)

    # ── 排除文章统计 ──
    exc_row = repo.fetch_one("SELECT COUNT(*) as cnt FROM excluded_articles")
    excluded_count = exc_row["cnt"] if exc_row else 0

    reason_rows = repo.fetch_all(
        "SELECT reason, COUNT(*) as cnt FROM excluded_articles GROUP BY reason ORDER BY cnt DESC"
    )
    by_reason = {r["reason"]: r["cnt"] for r in reason_rows}

    # ── 手册 FTS ──
    handbook_count = 0
    try:
        handbook_row = repo.fetch_one("SELECT COUNT(*) as cnt FROM handbook_fts")
        handbook_count = handbook_row["cnt"] if handbook_row else 0
    except Exception as e:
        logger.warning("Query handbook_fts failed: %s", e, exc_info=True)

    # ── 文书知识库统计 ──
    essay_stats = {}
    for tbl in ["essay_samples", "essay_prompts", "essay_criteria", "essay_brainstorm"]:
        try:
            row = repo.fetch_one(f"SELECT COUNT(*) as cnt FROM {tbl}")
            essay_stats[tbl] = row["cnt"] if row else 0
        except Exception as e:
            logger.warning("Query essay stats for table %s failed: %s", tbl, e, exc_info=True)
            essay_stats[tbl] = 0

    return {
        # 新知识库
        "kb_processed_count": kb_count,
        "kb_by_type": kb_by_type,
        "kb_quality_dist": kb_quality_dist,
        # 旧索引（过渡期）
        "old_fts_count": old_fts_count,
        # 处理管道状态
        "process_state": process_state,
        # 排除列表
        "excluded_total": excluded_count,
        "excluded_by_reason": by_reason,
        # 手册 & 文书
        "handbook_chunks": handbook_count,
        "essay_stats": essay_stats,
    }


# ---------------------------------------------------------------------------
# 索引管理
# ---------------------------------------------------------------------------

@router.post("/rebuild-index")
def rebuild_index():
    """重置知识库索引缓存，触发重新检查。

    注意：kb_processed 由 kb_pipeline.py 构建，此接口仅重置运行时缓存。
    """
    try:
        from ..services import news_knowledge
        news_knowledge._KB_INIT_DONE = False
        news_knowledge._KB_INIT_TIME = 0
        return {"ok": True, "message": "知识库索引缓存已重置，下次搜索时重新检查"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
