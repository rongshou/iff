import sqlite3
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Query
from typing import Optional

# werss db path
WERSS_DB = Path("/home/admin/werss/data/db.db")

# ---------------------------------------------------------------------------
# AI 智能分类体系（12个类）
# ---------------------------------------------------------------------------
CATEGORIES = {
    "语言考试": ["雅思", "托福", "PTE", "GRE", "GMAT", "SAT", "ACT", "A-level", "IB", "GPA"],
    "签证与出入境": ["签证", "护照", "入境", "海关", "通关", "续签", "出签", "面签"],
    "就业与实习": ["就业", "实习", "求职", "招聘", "内推", "跳槽", "OPT", "H1B", "工签"],
    "选校与申请": ["申请", "选校", "录取", "offer", "保录", "拒信", "waitlist", "文书", "PS", "CV", "推荐信"],
    "费用与奖学金": ["学费", "奖学金", "费用", "全奖", "半奖", "资助", "免学费", "预算", "性价比"],
    "排名与榜单": ["排名", "QS", "USNews", "Times", "榜单", "TOP", "四大榜", "世界大学"],
    "政策与解读": ["政策", "教育部", "官方", "公告", "限制", "禁止", "禁令", "规定", "新规"],
    "大学动态": ["扩招", "停招", "新开", "专业", "截止", "恢复", "开放", "关闭", "新增"],
    "考试技巧": ["备考", "复习", "技巧", "经验", "方法", "攻略", "真题", "模拟"],
    "低龄留学": ["高中", "美高", "英高", "澳高", "加高", "国际学校", "中学", "私校", "寄宿"],
    "生活适应": ["行前", "住宿", "机票", "文化", "适应", "保险", "银行卡", "租房"],
    "综合资讯": [],
}

# 旧版关键词分类（兜底用）
LEGACY_CATEGORIES = {
    "语言考试": ["雅思", "托福", "PTE", "GRE", "GMAT", "SAT", "ACT", "A-level", "IB"],
    "签证": ["签证", "护照", "入境", "海关"],
    "就业实习": ["就业", "实习", "求职", "招聘", "内推"],
    "择校申请": ["申请", "选校", "录取", "offer", "保录"],
    "费用奖学金": ["学费", "奖学金", "费用", "全奖", "半奖", "资助", "免学费"],
    "排名榜单": ["排名", "QS", "USNews", "榜单", "TOP", "四大榜", "世界大学"],
    "留学政策": ["政策", "教育部", "官方", "限制", "禁止", "禁令", "规定"],
    "大学动态": ["扩招", "新增", "开放", "截止", "恢复", "关闭", "停招"],
    "考试技巧": ["考试", "备考", "复习", "技巧", "经验"],
    "国际高中": ["高中", "中学", "低龄", "私校", "国际学校", "美高", "英高"],
}


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(WERSS_DB), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def get_ai_category(title: str, description: str = "") -> str:
    """基于关键词的兜底分类（当 ai_category 字段为空时使用）"""
    text = (title + " " + (description or "")).lower()
    for cat, keywords in CATEGORIES.items():
        if cat == "综合资讯":
            continue
        if any(kw.lower() in text for kw in keywords):
            return cat
    return "综合资讯"


def get_articles(category: str = None, page: int = 1, page_size: int = 20):
    offset = (page - 1) * page_size
    conn = get_connection()
    try:
        params = []
        ai_cat_filter = category and category in CATEGORIES
        legacy_cat = category and category in LEGACY_CATEGORIES

        if ai_cat_filter:
            base_where = "WHERE ai_category = ?"
            params.append(category)
        elif legacy_cat:
            keywords = LEGACY_CATEGORIES[category]
            conditions = " OR ".join([f"(title LIKE ? OR description LIKE ?)" for _ in keywords])
            base_where = f"WHERE ({conditions}) AND ai_category IS NULL"
            params = [f"%{kw}%" for kw in keywords for _ in range(2)]
        elif category == "综合资讯":
            # 综合资讯 = 有 ai_category 但值是"综合资讯"，或者既没 ai_category 也没命中关键词
            base_where = "WHERE (ai_category = '综合资讯' OR (ai_category IS NULL AND 1=0))"
        else:
            base_where = "WHERE 1=1"

        # COUNT
        count_sql = f"SELECT COUNT(*) as total FROM articles {base_where}"
        total = conn.execute(count_sql, params).fetchone()["total"]

        # SELECT
        sql = f"""
            SELECT id, title, pic_url, url, description, publish_time, mp_id, ai_category
            FROM articles
            {base_where}
            ORDER BY publish_time DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(sql, params + [page_size, offset]).fetchall()

        articles = []
        for r in rows:
            ai_cat = r["ai_category"] if r["ai_category"] else get_ai_category(r["title"], r["description"])
            articles.append({
                "id": r["id"],
                "title": r["title"],
                "pic_url": r["pic_url"],
                "url": r["url"],
                "description": (r["description"][:200] + "...") if r["description"] and len(r["description"]) > 200 else r["description"],
                "publish_time": r["publish_time"],
                "publish_date": datetime.fromtimestamp(r["publish_time"]).strftime("%Y-%m-%d") if r["publish_time"] else None,
                "category": ai_cat,
            })

        return {
            "articles": articles,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }
    finally:
        conn.close()


def get_categories():
    """单次 SQL 统计所有分类数量"""
    conn = get_connection()
    try:
        cat_names = [c for c in CATEGORIES if c != "综合资讯"]
        # Single aggregation query - 11 params (one per category)
        case_parts = ", ".join([f'SUM(CASE WHEN ai_category = ? THEN 1 ELSE 0 END)' for _ in cat_names])
        sql = f"SELECT {case_parts} FROM articles"

        row = conn.execute(sql, cat_names).fetchone()
        cats = []
        for i, c in enumerate(cat_names):
            cnt = row[i] or 0
            if cnt > 0:
                cats.append({"name": c, "count": cnt})
        # 综合资讯 = ai_category = '综合资讯'
        uncount = conn.execute(
            "SELECT COUNT(*) as c FROM articles WHERE ai_category = '综合资讯'"
        ).fetchone()["c"]
        if uncount > 0:
            cats.append({"name": "综合资讯", "count": uncount})
        return sorted(cats, key=lambda x: -x["count"])
    finally:
        conn.close()


def get_latest_articles(limit: int = 10):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, title, pic_url, url, description, publish_time, ai_category FROM articles ORDER BY publish_time DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "pic_url": r["pic_url"],
                "url": r["url"],
                "description": (r["description"][:150] + "...") if r["description"] and len(r["description"]) > 150 else r["description"],
                "publish_time": r["publish_time"],
                "publish_date": datetime.fromtimestamp(r["publish_time"]).strftime("%m-%d") if r["publish_time"] else "",
                "category": r["ai_category"] if r["ai_category"] else get_ai_category(r["title"], r["description"]),
            }
            for r in rows
        ]
    finally:
        conn.close()


router = APIRouter(prefix="/api/news", tags=["留学资讯"])


@router.get("/categories")
def list_categories():
    return get_categories()


@router.get("/articles")
def list_articles(
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return get_articles(category=category, page=page, page_size=page_size)


@router.get("/latest")
def latest_articles(limit: int = Query(10, ge=1, le=50)):
    return get_latest_articles(limit=limit)