import re
import sqlite3
import time
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


_EXCLUDED_CACHE: set[str] | None = None
_EXCLUDED_CACHE_TIME: float = 0
_CACHE_TTL = 600  # 10 分钟


def _load_excluded_ids() -> set[str]:
    """从 advisor.db 的 excluded_articles 表加载被排除的 article_id 集合。
    带 10 分钟内存缓存,避免每次查询都读 DB。
    """
    global _EXCLUDED_CACHE, _EXCLUDED_CACHE_TIME
    now = time.time()
    if _EXCLUDED_CACHE is not None and (now - _EXCLUDED_CACHE_TIME) < _CACHE_TTL:
        return _EXCLUDED_CACHE
    try:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT article_id FROM excluded_articles"
            ).fetchall()
        _EXCLUDED_CACHE = {r[0] for r in rows}
        _EXCLUDED_CACHE_TIME = now
        return _EXCLUDED_CACHE
    except Exception:
        return set()


STOPWORD_BIGRAMS = {
    "的", "了", "是", "在", "和", "与", "或", "也", "都", "就", "还", "又",
    "可以", "什么", "怎么", "如何", "为什么", "需要", "应该", "可能",
    "他们", "我们", "你们", "自己", "这个", "那个", "这些", "那些",
}


def _split_query_terms(query: str) -> list[str]:
    """把查询拆成搜索词: 英文按空格,中文按 2-gram 拆分"""
    terms: list[str] = []
    # 提取英文词
    en_words = re.findall(r"[a-zA-Z]{2,}", query)
    terms.extend(w.lower() for w in en_words[:3])

    # 提取中文连续段,做 2-gram
    cn_segments = re.findall(r"[\u4e00-\u9fff]+", query)
    for seg in cn_segments:
        if len(seg) <= 2:
            if seg not in STOPWORD_BIGRAMS:
                terms.append(seg)
        else:
            for i in range(len(seg) - 1):
                bigram = seg[i : i + 2]
                if bigram not in STOPWORD_BIGRAMS:
                    terms.append(bigram)
                if len(terms) >= 8:
                    break

    return terms[:8] if terms else [query[:10]]


_SEARCH_CACHE: dict[str, tuple[float, list[dict]]] = {}


_INDEX_CACHE: list[dict] | None = None
_INDEX_CACHE_TIME: float = 0


def _load_index() -> list[dict]:
    """预加载 article_search_index 到内存,避免每次 LIKE 都扫表。
    2153 行,约 4MB,加载一次后常驻内存。
    """
    global _INDEX_CACHE, _INDEX_CACHE_TIME
    now = time.time()
    if _INDEX_CACHE is not None and (now - _INDEX_CACHE_TIME) < _CACHE_TTL:
        return _INDEX_CACHE
    try:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT article_id, search_text, inferred_category FROM article_search_index"
            ).fetchall()
        _INDEX_CACHE = [
            {
                "id": r[0],
                "text": r[1] or "",
                "category": r[2] or "综合资讯",
            }
            for r in rows
        ]
        _INDEX_CACHE_TIME = now
        return _INDEX_CACHE
    except Exception:
        return []


def search_articles(query: str, limit: int = 8) -> list[dict]:
    cache_key = f"{query}:{limit}"
    now = time.time()
    cached = _SEARCH_CACHE.get(cache_key)
    if cached and (now - cached[0]) < _CACHE_TTL:
        return cached[1]

    wers_db = Path(settings.WERS_DB_PATH)
    if not wers_db.exists():
        return []

    excluded_ids = _load_excluded_ids()
    index_rows = _load_index()

    keywords = _extract_keywords(query)
    if not keywords:
        text = re.sub(r"[^\w\u4e00-\u9fff]", " ", query)
        words = [w for w in text.split() if len(w) >= 2]
        keywords = words[:4] if words else ["留学"]

    terms = _split_query_terms(query)
    top_terms = terms[:4]

    try:
        # 在内存中做全文匹配(索引表小,4MB,加载快)
        matched: list[dict] = []
        for row in index_rows:
            if any(t in row["text"] for t in top_terms):
                if row["id"] not in excluded_ids:
                    matched.append(row)

        # 按相关性评分排序(标题命中加分),只取 top N 去查 werss.db
        # 这样最多只查几十篇,避免大 IN 查询
        scored_matched: list[tuple[int, dict]] = []
        for m in matched:
            # 用 search_text 前 80 字符(通常是标题)做评分
            title_hint = m["text"][:80]
            score = 0
            for term in terms:
                if term in title_hint:
                    score += 5
                else:
                    score += 1
            if query[:10] in title_hint:
                score += 10
            scored_matched.append((score, m))

        scored_matched.sort(key=lambda x: x[0], reverse=True)
        # 只取 top 30 去查 werss.db 取标题/描述
        top_matched = scored_matched[:30]
        top_ids = [m["id"] for _, m in top_matched]
        inferred_map = {m["id"]: m["category"] for _, m in top_matched}

        if top_ids:
            wers_conn = sqlite3.connect(str(Path(settings.WERS_DB_PATH)))
            wers_conn.row_factory = sqlite3.Row
            id_placeholders = ",".join("?" * len(top_ids))
            sql = f"""
                SELECT id, title, ai_category, description
                FROM articles
                WHERE id IN ({id_placeholders})
            """
            rows = wers_conn.execute(sql, top_ids).fetchall()
            wers_conn.close()
        else:
            rows = []

        results: list[dict] = []
        seen_titles: set[str] = set()
        scored: list[tuple[int, dict]] = []
        for r in rows:
            if r["id"] in excluded_ids:
                continue
            title = r["title"] or ""
            if title in seen_titles:
                continue
            seen_titles.add(title)
            cat = r["ai_category"] or inferred_map.get(r["id"], "") or "综合资讯"
            item = {
                "title": title,
                "category": cat,
                "description": (r["description"] or "")[:120],
            }
            score = 0
            for term in terms:
                if term in title:
                    score += 5
                else:
                    score += 1
            if query[:10] in title:
                score += 10
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [item for _, item in scored[:limit]]

        _SEARCH_CACHE[cache_key] = (now, results)
        return results
    except Exception:
        return []