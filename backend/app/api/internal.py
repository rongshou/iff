"""
内部接口 — 无鉴权，仅供本地 MCP 服务器调用。
两个入口：
  GET /api/internal/classify_tier?school=xxx
  GET /api/internal/normalize_gpa?score=87.5&fmt=百分制&school=中山大学
"""
from fastapi import APIRouter, Query

from ..utils.tier import classify_school_tier, get_tier_label
from ..utils.gpa import normalize_gpa

router = APIRouter(prefix="/api/internal", tags=["internal"])


@router.get("/classify_tier")
async def internal_classify_tier(school: str = Query(..., description="院校名称")):
    """
    根据院校名称返回档次分类。
    返回 tier(1-6) 和 label(985/211/一本/双非/海本 等)。
    """
    tier, label = classify_school_tier(school)
    return {
        "school": school,
        "tier": tier,
        "label": label,
    }


@router.get("/normalize_gpa")
async def internal_normalize_gpa(
    score: float = Query(..., description="GPA 原始分值"),
    fmt: str = Query(..., description="GPA 格式：百分制/四分制/五分制/9分制/7分制 等"),
    school: str | None = Query(None, description="院校名称（用于判断海本）"),
):
    """
    将任意格式 GPA 转换为百分制和四分制。
    """
    pct, gpa4 = normalize_gpa(score, fmt, school)
    return {
        "original_score": score,
        "original_format": fmt,
        "school": school,
        "percent": pct,
        "gpa4": gpa4,
    }


# ── N16: 咨询追踪（rid 管理）───────────────────────────────
import json, secrets, sqlite3
from fastapi import HTTPException

import os
DB_PATH = os.environ.get("TIANQUAN_DB", "/app/data/advisor.db")

def get_conn():
    return sqlite3.connect(DB_PATH)


@router.put("/consult-context")
async def create_consult_context(report_data: dict = None):
    """
    前端报告生成后写入 rid 索引。
    前端 → BFF PUT /internal/consult-context → 本文
    返回 rid，前端据此生成二维码。
    """
    rid = secrets.token_urlsafe(16)
    data_json = json.dumps(report_data or {}, ensure_ascii=False)
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO consult_sessions (rid, report_data) VALUES (?, ?)",
                (rid, data_json)
            )
            conn.commit()
        return {"rid": rid, "created_at": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail="存储失败: " + str(e))


@router.get("/consult-context")
async def get_consult_context(rid: str = Query(..., description="会话 RID")):
    """
    二维码扫码回查：返回该 rid 对应的报告档案摘要。
    前端 → BFF GET /internal/consult-context?rid=xxx → 本文
    """
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT report_data, created_at FROM consult_sessions WHERE rid = ?",
            (rid,)
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="rid 不存在或已过期")
    try:
        data = json.loads(row[0]) if row[0] else {}
    except Exception:
        data = {}
    return {"rid": rid, "report_data": data, "created_at": row[1]}
