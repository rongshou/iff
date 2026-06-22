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

    terms = _split_query_terms(query)

    try:
        conn = sqlite3.connect(str(wers_db))
        conn.row_factory = sqlite3.Row

        like_param = f"%{query[:20]}%"

        # 第一优先: 全文匹配(title+description+content 摘要)
        # 通过 JOIN advisor.db 的 article_search_index 扩展检索字段
        # 对查询分词后多词 OR 匹配,提升召回率
        advisor_conn = sqlite3.connect(str(settings.DB_PATH))
        advisor_conn.row_factory = sqlite3.Row

        where_clauses = ["search_text LIKE ?"]
        params_idx = [like_param]
        for term in terms:
            where_clauses.append("search_text LIKE ?")
            params_idx.append(f"%{term}%")
        where_sql = " OR ".join(where_clauses)

        idx_rows = advisor_conn.execute(
            f"SELECT article_id, inferred_category FROM article_search_index WHERE {where_sql}",
            params_idx,
        ).fetchall()
        advisor_conn.close()

        matched_ids = [r["article_id"] for r in idx_rows]
        # article_id -> inferred_category 映射,用于补全空分类
        inferred_map: dict[str, str] = {
            r["article_id"]: r["inferred_category"] for r in idx_rows
        }

        if matched_ids:
            # SQLite 默认变量上限 999,分批查询
            all_rows: list = []
            chunk_size = 900
            for i in range(0, len(matched_ids), chunk_size):
                chunk = matched_ids[i : i + chunk_size]
                id_placeholders = ",".join("?" * len(chunk))
                sql = f"""
                    SELECT id, title, ai_category, description
                    FROM articles
                    WHERE id IN ({id_placeholders})
                    ORDER BY publish_time DESC
                """
                all_rows.extend(conn.execute(sql, chunk).fetchall())
            rows = all_rows
        else:
            # fallback: 只用分类 + title LIKE
            category_placeholders = ",".join("?" * len(keywords))
            sql = f"""
                SELECT id, title, ai_category, description
                FROM articles
                WHERE ai_category IN ({category_placeholders})
                   OR title LIKE ?
                ORDER BY publish_time DESC
                LIMIT ?
            """
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
        scored: list[tuple[int, dict]] = []
        for r in rows:
            if r["id"] in excluded_ids:
                continue
            if r["title"] in seen_titles:
                continue
            seen_titles.add(r["title"])
            desc = (r["description"] or "")[:120]
            cat = r["ai_category"] or inferred_map.get(r["id"], "") or "综合资讯"
            item = {
                "title": r["title"],
                "category": cat,
                "description": desc,
            }
            # 简单相关性评分: 标题命中 term 得 5 分, search_text 命中得 1 分
            # 标题匹配权重高,确保标题相关的文章排前面
            title = r["title"] or ""
            score = 0
            for term in terms:
                if term in title:
                    score += 5
                else:
                    score += 1
            # 完整查询短语出现在标题中,额外加分
            if query[:10] in title:
                score += 10
            scored.append((score, item))

        # 按相关性降序,同分按发布时间(已 DESC)保持稳定
        scored.sort(key=lambda x: x[0], reverse=True)
        for _, item in scored:
            results.append(item)
            if len(results) >= limit:
                break

        conn.close()
        return results
    except Exception:
        return []