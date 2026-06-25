"""
天权项目知识库检索优化版 - 基于 FTS5 BM25

核心改进：
1. HTML 清洗 + 纯文本提取
2. 全部文章灌入 FTS5 索引（替代 LIKE 匹配）
3. 中文分词：在连续中文字符间插入空格，配合 unicode61 分词器
4. OR 语义 + BM25 排序，标题权重 10x
5. 返回相关段落片段给 LLM（而非仅标题+120字摘要）
"""

import re
import sqlite3
import time
from pathlib import Path

from ..core.config import settings
from ..core.database import get_db


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


def _prepare_for_index(text: str, max_length: int = 3000) -> str:
    """清洗 HTML 并为中文分词做准备，返回可直接索引的文本"""
    cleaned = _clean_html(text)
    if not cleaned:
        return ""
    # 截断到合理长度（在句子边界）
    if len(cleaned) > max_length:
        truncated = cleaned[:max_length]
        last_boundary = max(
            truncated.rfind('。'), truncated.rfind('.'),
            truncated.rfind('！'), truncated.rfind('?'),
            truncated.rfind('\n'),
        )
        if last_boundary > max_length * 0.7:
            truncated = truncated[:last_boundary + 1]
        cleaned = truncated
    # 为中文分词加空格
    return _space_chinese(cleaned)


def _prepare_query(query: str) -> str:
    """将用户查询转换为 FTS5 OR 查询语法"""
    # 清洗查询
    cleaned = _clean_html(query)
    # 提取有意义的词：英文单词(>=2字符) + 中文字符
    terms = []
    # 英文词
    en_words = re.findall(r'[a-zA-Z][a-zA-Z0-9]{1,}', cleaned)
    terms.extend(w.lower() for w in en_words[:5])
    # 中文字符（每个字作为一个 token）
    cn_chars = re.findall(r'[\u4e00-\u9fff]', cleaned)
    terms.extend(cn_chars[:10])
    
    if not terms:
        # 退化处理：取前几个字符
        terms = [c for c in cleaned[:5] if c.strip()]
    
    # 构造 OR 查询
    return " OR ".join(terms)


# ============================================================
# 分类关键词（用于查询理解）
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
# FTS5 索引管理
# ============================================================

_FTS_INIT_DONE: bool = False
_FTS_INIT_TIME: float = 0
_FTS_CHECK_INTERVAL: float = 300  # 5 分钟检查一次新文章


def _ensure_fts_index():
    """确保 FTS5 索引已建立。只做存在性检查，不做增量同步（同步由外部脚本处理）"""
    global _FTS_INIT_DONE, _FTS_INIT_TIME
    now = time.time()
    
    if _FTS_INIT_DONE:
        return
    
    try:
        with get_db() as conn:
            fts_exists = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='articles_fts'"
            ).fetchone()[0]
            
            if fts_exists:
                fts_count = conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0]
                if fts_count > 0:
                    _FTS_INIT_DONE = True
                    _FTS_INIT_TIME = now
                    return
                # 空表，删除后重建
                conn.execute("DROP TABLE IF EXISTS articles_fts")
                conn.commit()
            
            # 全量构建
            _build_fts_index(conn)
        
        _FTS_INIT_DONE = True
        _FTS_INIT_TIME = now
    except Exception as e:
        print(f"[news_knowledge] FTS index init failed: {e}")


def _build_fts_index(conn):
    """从 werss.db 构建完整的 FTS5 索引（逐条处理，带重试）"""
    wers_db = Path(settings.WERS_DB_PATH)
    if not wers_db.exists():
        print("[news_knowledge] werss.db not found, skipping FTS build")
        return
    
    # 创建 FTS5 虚拟表（unicode61 分词器）
    conn.execute("""
        CREATE VIRTUAL TABLE articles_fts USING fts5(
            article_id, title, content, ai_category,
            tokenize='unicode61'
        )
    """)
    conn.commit()
    
    # 先获取全部文章 ID（轻量查询）
    wers_conn = sqlite3.connect(str(wers_db), timeout=30)
    article_ids = [r[0] for r in wers_conn.execute(
        "SELECT id FROM articles WHERE content IS NOT NULL AND length(content) > 100"
    ).fetchall()]
    wers_conn.close()
    
    inserted = 0
    for i, aid in enumerate(article_ids):
        retry = 0
        while retry < 3:
            try:
                wers_conn = sqlite3.connect(str(wers_db), timeout=30)
                row = wers_conn.execute(
                    "SELECT id, title, content, ai_category FROM articles WHERE id = ?",
                    (aid,)
                ).fetchone()
                wers_conn.close()
                
                if not row:
                    break
                
                article_id = str(row[0])
                title = row[1] or ""
                raw_content = row[2] or ""
                category = row[3] or "综合资讯"
                
                clean_content = _prepare_for_index(raw_content, max_length=2000)
                clean_title = _space_chinese(title)
                
                if not clean_content.strip():
                    break
                
                conn.execute(
                    "INSERT INTO articles_fts(article_id, title, content, ai_category) VALUES (?, ?, ?, ?)",
                    (article_id, clean_title, clean_content, category)
                )
                inserted += 1
                break
            except Exception:
                retry += 1
                time.sleep(0.5)
        
        # 每 100 篇提交一次
        if (i + 1) % 100 == 0:
            conn.commit()
    
    conn.commit()
    print(f"[news_knowledge] FTS index built: {inserted}/{len(article_ids)} articles indexed")


def _sync_new_articles_to_fts(conn):
    """增量同步新文章到 FTS5（轻量级：只检查文章总数差异）"""
    wers_db = Path(settings.WERS_DB_PATH)
    if not wers_db.exists():
        return
    
    # 快速检查：比较 FTS 索引数量和 werss.db 文章数量
    fts_count = conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0]
    
    try:
        wers_conn = sqlite3.connect(str(wers_db), timeout=10)
        wers_count = wers_conn.execute(
            "SELECT COUNT(*) FROM articles WHERE content IS NOT NULL AND length(content) > 100"
        ).fetchone()[0]
        wers_conn.close()
    except Exception:
        return
    
    # 差异不大则跳过（允许少量不同步）
    if wers_count - fts_count < 10:
        return
    
    # 有较大差异时才做增量同步
    print(f"[news_knowledge] FTS sync needed: FTS={fts_count}, werss={wers_count}")
    
    # 获取 FTS 中已有的 article_id
    existing_ids = set(
        r[0] for r in conn.execute("SELECT article_id FROM articles_fts").fetchall()
    )
    
    # 从 werss.db 获取新文章（使用游标逐条读取，避免大查询）
    try:
        wers_conn = sqlite3.connect(str(wers_db), timeout=30)
        cursor = wers_conn.execute(
            "SELECT id, title, content, ai_category FROM articles WHERE content IS NOT NULL AND length(content) > 100"
        )
        
        inserted = 0
        while True:
            row = cursor.fetchone()
            if not row:
                break
            
            article_id = str(row[0])
            if article_id in existing_ids:
                continue
            
            title = row[1] or ""
            raw_content = row[2] or ""
            category = row[3] or "综合资讯"
            
            clean_content = _prepare_for_index(raw_content, max_length=2000)
            clean_title = _space_chinese(title)
            
            if not clean_content.strip():
                continue
            
            conn.execute(
                "INSERT OR IGNORE INTO articles_fts(article_id, title, content, ai_category) VALUES (?, ?, ?, ?)",
                (article_id, clean_title, clean_content, category)
            )
            inserted += 1
        
        wers_conn.close()
        
        if inserted > 0:
            conn.commit()
            print(f"[news_knowledge] FTS index synced: {inserted} new articles")
    except Exception as e:
        print(f"[news_knowledge] FTS sync error: {e}")


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
        with get_db() as conn:
            rows = conn.execute("SELECT article_id FROM excluded_articles").fetchall()
        _EXCLUDED_CACHE = {r[0] for r in rows}
        _EXCLUDED_CACHE_TIME = now
        return _EXCLUDED_CACHE
    except Exception:
        return set()


# ============================================================
# 主检索函数 - 基于 FTS5 BM25
# ============================================================

_SEARCH_CACHE: dict[str, tuple[float, list[dict]]] = {}


def search_articles(query: str, limit: int = 8) -> list[dict]:
    """使用 FTS5 BM25 搜索文章。
    
    返回格式：
    - title: 文章标题
    - category: 分类
    - description: 简短描述（前120字）
    - content_snippet: 相关段落片段（用于 LLM 引用）
    """
    cache_key = f"{query}:{limit}"
    now = time.time()
    cached = _SEARCH_CACHE.get(cache_key)
    if cached and (now - cached[0]) < _CACHE_TTL:
        return cached[1]
    
    # 确保 FTS5 索引就绪
    _ensure_fts_index()
    
    excluded_ids = _load_excluded_ids()
    
    # 构造 FTS5 查询
    fts_query = _prepare_query(query)
    if not fts_query:
        return []
    
    try:
        with get_db() as conn:
            # FTS5 BM25 搜索：标题权重 10x，内容权重 1x
            sql = """
                SELECT article_id, title, content, ai_category,
                       bm25(articles_fts, 10.0, 1.0, 0.0) as rank_score
                FROM articles_fts
                WHERE articles_fts MATCH ?
                ORDER BY rank_score ASC
                LIMIT ?
            """
            rows = conn.execute(sql, (fts_query, limit * 3)).fetchall()
        
        # 组装结果
        results: list[dict] = []
        seen_ids: set[str] = set()
        
        for row in rows:
            article_id = row[0]
            if article_id in excluded_ids or article_id in seen_ids:
                continue
            seen_ids.add(article_id)
            
            # title 和 content 是加了空格的版本，需要清理
            raw_title = row[1] or ""
            raw_content = row[2] or ""
            category = row[3] or "综合资讯"
            
            # 去除中文间的空格，恢复原始文本
            title = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', raw_title)
            
            # 生成描述和片段
            clean_content = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', raw_content)
            desc = clean_content[:120] if clean_content else ""
            snippet = _extract_snippet(clean_content, query, context_chars=300)
            
            results.append({
                "title": title,
                "category": category,
                "description": desc,
                "content_snippet": snippet,
            })
            
            if len(results) >= limit:
                break
        
        _SEARCH_CACHE[cache_key] = (now, results)
        return results
        
    except Exception as e:
        print(f"[news_knowledge] FTS search failed: {e}")
        # 降级到简单 LIKE 搜索
        return _fallback_search(query, limit, excluded_ids)


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


def _fallback_search(query: str, limit: int, excluded_ids: set[str]) -> list[dict]:
    """降级方案：当 FTS5 搜索失败时，使用 LIKE 查询"""
    wers_db = Path(settings.WERS_DB_PATH)
    if not wers_db.exists():
        return []
    
    terms = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', query)
    if not terms:
        return []
    
    try:
        wers_conn = sqlite3.connect(str(wers_db))
        wers_conn.row_factory = sqlite3.Row
        
        conditions = " OR ".join(
            "(title LIKE ? OR content LIKE ?)" for _ in terms[:4]
        )
        params = []
        for t in terms[:4]:
            params.extend([f"%{t}%", f"%{t}%"])
        
        sql = f"""
            SELECT id, title, ai_category, description, content
            FROM articles
            WHERE ({conditions}) AND content IS NOT NULL
            ORDER BY LENGTH(content) DESC
            LIMIT ?
        """
        params.append(limit * 2)
        
        rows = wers_conn.execute(sql, params).fetchall()
        wers_conn.close()
        
        results = []
        for r in rows:
            if r["id"] in excluded_ids:
                continue
            title = r["title"] or ""
            content = _clean_html(r["content"] or "")
            category = r["ai_category"] or "综合资讯"
            desc = content[:120]
            snippet = _extract_snippet(content, query, context_chars=300)
            
            results.append({
                "title": title,
                "category": category,
                "description": desc,
                "content_snippet": snippet,
            })
            if len(results) >= limit:
                break
        
        return results
    except Exception:
        return []
