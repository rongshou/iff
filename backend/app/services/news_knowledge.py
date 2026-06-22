import re
import sqlite3
from pathlib import Path

from ..core.config import settings
from ..core.database import get_db

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "选校与申请": ["选校", "申请", "录取", "offer", "定位", "排名", "择校", "院校", "专业", "项目", "硕士", "本科", "博士", "文书", "PS", "简历", "CV", "推荐信", "作品集", "面试"],
    "语言考试": ["雅思", "托福", "IELTS", "TOEFL", "GRE", "GMAT", "PTE", "DET", "多邻国", "语言成绩", "语言考试"],
    "签证与出入境": ["签证", "出入境", "入境", "签证材料", "I-20", "CAS", "COE", "护照", "续签"],
    "就业与实习": ["就业", "实习", "求职", "OPT", "CPT", "工作", "秋招", "春招", "校招", "Offer", "面试", "薪酬"],
    "费用与奖学金": ["费用", "学费", "奖学金", "奖学金", "省钱", "花费", "开支", "助学金", "全奖", "半奖", "生活费"],
    "排名与榜单": ["排名", "QS", "USNews", "THE", "软科", "ARWU", "榜单", "榜单"],
    "政策与解读": ["政策", "解读", "改革", "变化", "新政", "规定", "调整"],
    "大学动态": ["大学", "学院", "校区", "新开", "扩招", "停招", "升级"],
    "低龄留学": ["低龄", "高中", "初中", "小学", "陪读", "预科", "游学", "夏校", "夏令营"],
    "生活适应": ["生活", "住宿", "租房", "医保", "交通", "饮食", "安全", "文化差异"],
    "考试技巧": ["技巧", "备考", "提分", "刷题", "蒙题", "单词", "口语", "写作"],
}

COUNTRY_KEYWORDS: dict[str, list[str]] = {
    "英国": ["英国", "英伦", "UK", "伦敦", "牛剑", "G5"],
    "美国": ["美国", "美本", "美研", "US", "常青藤", "常春藤", "Ivy"],
    "澳洲": ["澳洲", "澳大利亚", "墨尔本", "悉尼", "八大"],
    "加拿大": ["加拿大", "枫叶国", "多伦多", "温哥华"],
    "香港": ["香港", "港校", "港大", "港中文", "港科"],
    "新加坡": ["新加坡", "NUS", "NTU"],
    "日本": ["日本", "东大", "京大", "日语"],
    "德国": ["德国", "TU9", "德语", "慕尼黑"],
    "法国": ["法国", "巴黎", "高商"],
    "新西兰": ["新西兰"],
    "爱尔兰": ["爱尔兰"],
    "韩国": ["韩国", "首尔", "韩语"],
    "马来西亚": ["马来西亚"],
    "荷兰": ["荷兰", "代尔夫特"],
    "瑞士": ["瑞士", "ETH", "洛桑"],
    "意大利": ["意大利"],
    "西班牙": ["西班牙"],
    "瑞典": ["瑞典"],
    "丹麦": ["丹麦"],
    "芬兰": ["芬兰"],
    "挪威": ["挪威"],
    "比利时": ["比利时"],
}


def _extract_keywords(text: str) -> list[str]:
    keywords: list[str] = []
    for category, words in CATEGORY_KEYWORDS.items():
        for w in words:
            if w in text:
                keywords.append(category)
                break
    for country, words in COUNTRY_KEYWORDS.items():
        for w in words:
            if w in text:
                keywords.append(country)
                break
    gpa_match = re.search(r"(?:GPA|gpa|均分|绩点)\s*[:：]?\s*(\d+\.?\d*)", text)
    if gpa_match:
        keywords.append("选校与申请")
    return list(set(keywords))


def _load_excluded_ids() -> set[str]:
    """从 advisor.db 的 excluded_articles 表加载被排除的 article_id 集合"""
    try:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT article_id FROM excluded_articles"
            ).fetchall()
            return {r[0] for r in rows}
    except Exception:
        return set()


def search_articles(query: str, limit: int = 8) -> list[dict]:
    wers_db = Path(settings.WERS_DB_PATH)
    if not wers_db.exists():
        return []

    excluded_ids = _load_excluded_ids()

    keywords = _extract_keywords(query)
    if not keywords:
        text = re.sub(r"[^\w\u4e00-\u9fff]", " ", query)
        words = [w for w in text.split() if len(w) >= 2]
        keywords = words[:4] if words else ["留学"]

    try:
        conn = sqlite3.connect(str(wers_db))
        conn.row_factory = sqlite3.Row

        category_placeholders = ",".join("?" * len(keywords))
        sql = f"""
            SELECT id, title, ai_category, description
            FROM articles
            WHERE (ai_category IN ({category_placeholders})
                   OR title LIKE ?)
            ORDER BY publish_time DESC
            LIMIT ?
        """
        like_param = f"%{query[:20]}%"
        params = keywords + [like_param, limit * 5]

        rows = conn.execute(sql, params).fetchall()

        if not rows:
            sql = """
                SELECT id, title, ai_category, description
                FROM articles
                WHERE title LIKE ?
                ORDER BY publish_time DESC
                LIMIT ?
            """
            rows = conn.execute(sql, (like_param, limit * 3)).fetchall()

        results: list[dict] = []
        seen_titles: set[str] = set()
        for r in rows:
            if r["id"] in excluded_ids:
                continue
            if r["title"] in seen_titles:
                continue
            seen_titles.add(r["title"])
            desc = (r["description"] or "")[:120]
            results.append({
                "title": r["title"],
                "category": r["ai_category"] or "综合资讯",
                "description": desc,
            })
            if len(results) >= limit:
                break

        conn.close()
        return results
    except Exception:
        return []