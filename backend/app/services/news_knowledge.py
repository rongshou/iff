"""
天权项目知识库检索 - 基于 kb_processed（AI 全结构化知识库）

架构：werss(采集) → kb_pipeline(AI处理) → kb_processed(轻量知识库) → 本模块(搜索)

搜索流程：
1. 用户查询 → 构造 FTS5 OR 查询
2. 搜索 kb_processed_fts（BM25 排序）
3. JOIN kb_processed 获取完整结构化数据（summary, article_type, countries, tags 等）
4. 过滤 excluded_articles + 广告检测
5. 返回结构化结果供 chat.py 注入 LLM

降级策略：
- 如果 kb_processed_fts 不存在/为空 → 尝试旧 articles_fts（过渡期兼容）
- 如果旧系统也不可用 → 返回空结果
"""

import json
import logging
import re
import time
from typing import Any

from ..core.config import settings
from ..repositories import ArticleRepository


logger = logging.getLogger(__name__)


# ============================================================
# Repository
# ============================================================

_article_repo: ArticleRepository | None = None


def _get_article_repo() -> ArticleRepository:
    global _article_repo
    if _article_repo is None:
        _article_repo = ArticleRepository(str(settings.DB_PATH))
    return _article_repo


# ============================================================
# 内容清洗工具
# ============================================================

def _clean_html(text: str) -> str:
    """去除 HTML 标签、多余空白，提取纯文本"""
    if not text:
        return ""
    # 去除 script/style 及其内容
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 去除所有 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 处理常见 HTML 实体
    for old, new in [('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'),
                     ('&gt;', '>'), ('&quot;', '"'), ('&#39;', "'"),
                     ('&mdash;', '—'), ('&ndash;', '–'), ('&hellip;', '…')]:
        text = text.replace(old, new)
    # 合并多余空白
    text = re.sub(r'[ \t]+', ' ', text)
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _space_chinese(text: str) -> str:
    """在连续中文字符之间插入空格，使 unicode61 分词器将每个汉字作为独立 token"""
    return re.sub(r'([\u4e00-\u9fff])', r' \1 ', text)


def _escape_fts_term(term: str) -> str:
    """转义 FTS5 查询词中的特殊字符，防止注入攻击。

    FTS5 MATCH 中以下字符有特殊含义：^ * " ( ) + - ~ AND OR NOT NEAR
    用双引号包裹每个 term，内部的 " 用 "" 转义。
    """
    escaped = term.replace('"', '""')
    return f'"{escaped}"'


def _prepare_query(query: str) -> str:
    """将用户查询转换为安全的 FTS5 OR 查询语法"""
    # 清洗查询
    cleaned = _clean_html(query)
    # 提取有意义的词：英文单词(>=2字符) + 中文字符
    terms = []
    # 英文词
    en_words = re.findall(r'[a-zA-Z][a-zA-Z0-9]{1,}', cleaned)
    for w in en_words[:5]:
        terms.append(_escape_fts_term(w.lower()))
    # 中文字符（每个字作为一个 token）
    cn_chars = re.findall(r'[\u4e00-\u9fff]', cleaned)
    for c in cn_chars[:10]:
        terms.append(_escape_fts_term(c))

    if not terms:
        # 退化处理：取前几个字符
        for c in cleaned[:5]:
            if c.strip():
                terms.append(_escape_fts_term(c))

    # 构造 OR 查询
    return " OR ".join(terms) if terms else ""


# ============================================================
# 分类关键词（用于查询理解，保留供未来扩展）
# ============================================================

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "选校与申请": ["选校", "申请", "录取", "offer", "定位", "排名", "择校", "院校", "专业", "项目", "硕士", "本科", "博士", "文书", "PS", "简历", "CV", "推荐信", "作品集", "面试"],
    "语言考试": ["雅思", "托福", "IELTS", "TOEFL", "GRE", "GMAT", "PTE", "DET", "多邻国", "语言成绩", "语言考试"],
    "签证与出入境": ["签证", "出入境", "入境", "签证材料", "I-20", "CAS", "COE", "护照", "续签"],
    "就业与实习": ["就业", "实习", "求职", "OPT", "CPT", "工作", "秋招", "春招", "校招", "Offer", "面试", "薪酬"],
    "费用与奖学金": ["费用", "学费", "奖学金", "省钱", "花费", "开支", "助学金", "全奖", "半奖", "生活费"],
    "排名与榜单": ["排名", "QS", "USNews", "THE", "软科", "ARWU", "榜单"],
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
    """从查询中提取分类和国家关键词"""
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


# ============================================================
# FTS5 索引检查
# ============================================================

_KB_INIT_DONE: bool = False
_KB_INIT_TIME: float = 0
_KB_CHECK_INTERVAL: float = 300  # 5 分钟检查一次


def _ensure_fts_index() -> None:
    """确保知识库索引可用。

    优先检查 kb_processed_fts（新版 AI 结构化知识库）。
    如果不可用，降级检查旧 articles_fts（过渡期兼容）。
    不再自动从 werss.db 构建索引 —— 索引由 kb_pipeline.py 负责。
    """
    global _KB_INIT_DONE, _KB_INIT_TIME
    now = time.time()

    if _KB_INIT_DONE:
        return

    try:
        repo = _get_article_repo()
        with repo.get_conn() as conn:
            # 优先检查 kb_processed_fts
            if repo.kb_fts_exists(conn):
                kb_count = repo.kb_count(conn)
                if kb_count > 0:
                    _KB_INIT_DONE = True
                    _KB_INIT_TIME = now
                    logger.info("kb_processed ready: %s articles", kb_count)
                    return

            # 降级：检查旧 articles_fts
            if repo.fts_table_exists(conn):
                old_count = repo.fts_count(conn)
                if old_count > 0:
                    _KB_INIT_DONE = True
                    _KB_INIT_TIME = now
                    logger.warning("kb_processed empty, falling back to old articles_fts (%s articles)", old_count)
                    return

            logger.warning("No knowledge index available. Run kb_pipeline.py to populate kb_processed.")

        _KB_INIT_DONE = True
        _KB_INIT_TIME = now
    except Exception as e:
        logger.warning("Index check failed: %s", e)


# ============================================================
# 排除列表缓存
# ============================================================

_EXCLUDED_CACHE: set[str] | None = None
_EXCLUDED_CACHE_TIME: float = 0
_CACHE_TTL = 600  # 10 分钟


def _load_excluded_ids() -> set[str]:
    """从 advisor.db 的 excluded_articles 表加载被排除的 article_id 集合"""
    global _EXCLUDED_CACHE, _EXCLUDED_CACHE_TIME
    now = time.time()
    if _EXCLUDED_CACHE is not None and (now - _EXCLUDED_CACHE_TIME) < _CACHE_TTL:
        return _EXCLUDED_CACHE
    try:
        _EXCLUDED_CACHE = _get_article_repo().load_excluded_article_ids()
        _EXCLUDED_CACHE_TIME = now
        return _EXCLUDED_CACHE
    except Exception:
        logger.warning("load_excluded_article_ids failed", exc_info=True)
        return set()


# ============================================================
# 主检索函数
# ============================================================

_SEARCH_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_SEARCH_CACHE_MAX = 128  # prevent unbounded memory growth


def search_articles(query: str, limit: int = 8) -> list[dict[str, Any]]:
    """搜索知识库文章和院校手册。

    优先从 kb_processed（AI 结构化知识库）搜索，降级到旧 articles_fts。

    返回格式：
    - title: 文章标题
    - category: 分类（article_type）
    - description: 简短描述
    - content_snippet: 相关段落片段（用于 LLM 引用）
    - publish_time: 发布时间戳
    - quality_score: 质量评分（0-1，仅 kb_processed 有）
    """
    cache_key = f"{query}:{limit}"
    now = time.time()
    cached = _SEARCH_CACHE.get(cache_key)
    if cached and (now - cached[0]) < _CACHE_TTL:
        return cached[1]

    # 确保索引就绪
    _ensure_fts_index()

    excluded_ids = _load_excluded_ids()

    # 构造 FTS5 查询
    fts_query = _prepare_query(query)
    if not fts_query:
        return []

    results: list[dict] = []

    try:
        repo = _get_article_repo()

        # ── 优先：从 kb_processed_fts 搜索 ──
        with repo.get_conn() as conn:
            if repo.kb_fts_exists(conn) and repo.kb_count(conn) > 0:
                results = _search_kb(fts_query, limit, excluded_ids, conn)

        # ── 降级：旧 articles_fts ──
        if not results:
            with repo.get_conn() as conn:
                if repo.fts_table_exists(conn) and repo.fts_count(conn) > 0:
                    results = _search_old_fts(fts_query, limit, excluded_ids, conn)

        # 补充手册搜索结果（上限 3 条）
        if len(results) < limit:
            handbook_results = _search_handbooks(query, limit=3)
            for h in handbook_results:
                if len(results) >= limit:
                    break
                results.append(h)

        # LRU eviction before inserting new cache entry
        if len(_SEARCH_CACHE) >= _SEARCH_CACHE_MAX:
            oldest_key = min(_SEARCH_CACHE.keys(), key=lambda k: _SEARCH_CACHE[k][0])
            del _SEARCH_CACHE[oldest_key]
        _SEARCH_CACHE[cache_key] = (now, results)
        return results

    except Exception as e:
        logger.warning("Search failed: %s", e)
        return []


def _search_kb(fts_query: str, limit: int, excluded_ids: set[str],
               conn) -> list[dict[str, Any]]:
    """从 kb_processed_fts 搜索（新版 AI 结构化知识库）。"""
    repo = _get_article_repo()
    rows = repo.search_kb_fts(fts_query, limit * 3)

    results: list[dict] = []
    seen_ids: set[str] = set()

    for row in rows:
        article_id = row["article_id"]
        if article_id in excluded_ids or article_id in seen_ids:
            continue
        seen_ids.add(article_id)

        title = row.get("title") or ""
        summary = row.get("summary") or ""
        article_type = row.get("article_type") or "综合资讯"
        quality_score = row.get("quality_score") or 0.5
        publish_time = row.get("publish_time")

        # 跳过广告类型（pipeline 已标记）
        if article_type == "广告营销":
            continue

        # 解析 JSON 字段
        try:
            countries = json.loads(row.get("countries") or "[]")
        except (json.JSONDecodeError, TypeError):
            countries = []
        try:
            tags = json.loads(row.get("tags") or "[]")
        except (json.JSONDecodeError, TypeError):
            tags = []

        # 使用 AI 生成的 summary 作为内容片段（质量远高于原文截取）
        snippet = summary if summary else ""

        # 生成描述（summary 前 120 字）
        desc = summary[:120] if summary else ""

        results.append({
            "title": title,
            "category": article_type,
            "description": desc,
            "content_snippet": snippet,
            "publish_time": publish_time,
            "quality_score": quality_score,
            "countries": countries,
            "tags": tags,
            "source": "kb_processed",
        })

        if len(results) >= limit:
            break

    return results


def _search_old_fts(fts_query: str, limit: int, excluded_ids: set[str],
                    conn) -> list[dict[str, Any]]:
    """从旧 articles_fts 搜索（过渡期降级方案）。"""
    repo = _get_article_repo()
    rows = repo.search_fts(fts_query, limit * 3)

    results: list[dict] = []
    seen_ids: set[str] = set()

    for row in rows:
        article_id = row["article_id"]
        if article_id in excluded_ids or article_id in seen_ids:
            continue
        seen_ids.add(article_id)

        raw_title = row.get("title") or ""
        raw_content = row.get("content") or ""
        category = row.get("ai_category") or "综合资讯"

        # 去除中文间的空格，恢复原始文本
        title = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', raw_title)
        clean_content = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', raw_content)

        desc = clean_content[:120] if clean_content else ""
        snippet = _extract_snippet(clean_content, fts_query, context_chars=300)

        results.append({
            "title": title,
            "category": category,
            "description": desc,
            "content_snippet": snippet,
            "publish_time": None,  # 旧系统无 publish_time
            "quality_score": 0.5,
            "source": "articles_fts",
        })

        if len(results) >= limit:
            break

    return results


def _search_handbooks(query: str, limit: int = 4) -> list[dict[str, Any]]:
    """搜索 handbook_fts，将手册内容作为知识库结果返回。

    返回格式与 search_articles 兼容：
    - title: "【手册】{school}"
    - category: "院校手册"
    - description: 内容前120字
    - content_snippet: 相关片段
    - source: "handbook"
    """
    fts_query = _prepare_query(query)
    if not fts_query:
        return []

    try:
        rows = _get_article_repo().search_handbook_fts(fts_query, limit)

        results: list[dict] = []
        for row in rows:
            school = row.get("school") or "未知院校"
            content = row.get("content") or ""

            desc = content[:120] if content else ""
            snippet = _extract_snippet(content, query, context_chars=300)

            results.append({
                "title": f"【手册】{school}",
                "category": "院校手册",
                "description": desc,
                "content_snippet": snippet,
                "source": "handbook",
            })
            if len(results) >= limit:
                break

        return results
    except Exception as e:
        logger.warning("Handbook FTS search failed: %s", e)
        return []


def _extract_snippet(content: str, query: str, context_chars: int = 300) -> str:
    """从内容中提取包含查询关键词的相关片段"""
    if not content:
        return ""

    # 提取查询中的关键词
    terms = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', query)
    if not terms:
        return content[:context_chars]

    # 查找第一个匹配位置
    best_pos = -1
    for term in terms:
        pos = content.find(term)
        if pos >= 0 and (best_pos == -1 or pos < best_pos):
            best_pos = pos

    if best_pos == -1:
        return content[:context_chars]

    # 以匹配位置为中心截取
    start = max(0, best_pos - context_chars // 3)
    end = min(len(content), start + context_chars)

    # 调整到句子边界
    if start > 0:
        for sep in ['。', '.', '！', '?', '\n', '；', ';']:
            boundary = content.rfind(sep, start - 50, start)
            if boundary > 0:
                start = boundary + 1
                break

    if end < len(content):
        for sep in ['。', '.', '！', '?', '\n', '；', ';']:
            boundary = content.find(sep, end - 30, end + 50)
            if boundary > 0:
                end = boundary + 1
                break

    snippet = content[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(content):
        snippet = snippet + "…"

    return snippet
