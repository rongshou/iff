#!/usr/bin/env python3
"""
知识库 ETL 管道 —— 从 werss 采集、清洗、AI 全结构化提取，存入知识库。

架构：werss.db(原始) → 清洗 → 质量过滤 → AI 结构化 → kb_processed(知识库)

用法：
    python3 kb_pipeline.py                    # 处理所有未处理的文章
    python3 kb_pipeline.py --limit 50         # 只处理前 50 篇
    python3 kb_pipeline.py --reprocess-all    # 重新处理所有文章
    python3 kb_pipeline.py --stats            # 查看处理状态
"""
import argparse
import json
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional, Tuple, List, Dict

import httpx

# =====================================================================
# 配置
# =====================================================================

# 数据库路径（在服务器上直接访问文件）
WERS_DB_PATH = "/home/admin/werss/data/db.db"
ADVISOR_DB_PATH = "/home/admin/tianquan/backend/data/advisor.db"

# LLM 配置（与 tianquan .env 一致）
LLM_BASE_URL = "https://opencode.ai/zen/go/v1"
LLM_API_KEY = "sk-1ctYojVxgodzjiQBt0dFyKbJ6HIfvPzzk8ZLtgBhkyEDZ3yGrYdheG1JGwDIVw6N"
LLM_MODEL = "deepseek-v4-flash"

# 处理参数
MAX_CONTENT_LENGTH = 2000     # 发送给 AI 的最大字符数
MIN_CLEAN_LENGTH = 200        # 清洗后最少字数
MIN_CHINESE_RATIO = 0.25      # 中文字符最低占比
MAX_ARTICLE_AGE_DAYS = 730    # 文章最大年龄（2年）
BATCH_SIZE = 5                # 每批处理数量
REQUEST_INTERVAL = 0.5        # 请求间隔（秒），避免限流
MAX_RETRIES = 3               # 最大重试次数
RETRY_BASE_DELAY = 5.0        # 重试基础延迟（秒）


# =====================================================================
# HTML 清洗
# =====================================================================

def clean_html(text: str) -> str:
    """去除 HTML 标签、脚本、样式，提取纯文本。"""
    if not text:
        return ""
    # 去除 script/style
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 去除所有 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # HTML 实体
    for old, new in [('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'),
                     ('&gt;', '>'), ('&quot;', '"'), ('&#39;', "'"),
                     ('&mdash;', '—'), ('&ndash;', '–'), ('&hellip;', '…')]:
        text = text.replace(old, new)
    # 合并空白
    text = re.sub(r'[ \t]+', ' ', text)
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# =====================================================================
# 质量过滤
# =====================================================================

def check_quality(text_clean, publish_time=None):
    # type: (str, Optional[int]) -> Tuple[bool, str]
    """检查文章质量是否值得处理。"""
    if not text_clean or len(text_clean) < MIN_CLEAN_LENGTH:
        return False, "too_short"

    chinese_chars = sum(1 for c in text_clean if '\u4e00' <= c <= '\u9fff')
    total = len(text_clean.strip())
    if total > 0 and chinese_chars / total < MIN_CHINESE_RATIO:
        return False, "low_chinese_ratio"

    if publish_time:
        age_days = (time.time() - publish_time) / 86400
        if age_days > MAX_ARTICLE_AGE_DAYS:
            return False, "outdated"

    return True, "ok"


# 广告预过滤关键词（标题匹配即跳过，不调 LLM，节省 API 调用）
AD_TITLE_PATTERNS = [
    r"实习信息汇总",
    r"实习.*汇总",
    r"5\.\d+实习",   # "5.13实习" pattern
    r"6\.\d+实习",
    r"7\.\d+实习",
]

def pre_filter_ad(title):
    # type: (str) -> bool
    """标题级别广告预过滤。返回 True 表示判定为广告，应跳过。"""
    if not title:
        return False
    for pattern in AD_TITLE_PATTERNS:
        if re.search(pattern, title):
            return True
    return False


# =====================================================================
# AI 结构化
# =====================================================================

STRUCTURE_PROMPT = """你是一个留学行业资讯分析专家。请分析以下留学相关文章，提取结构化信息。

请严格按以下 JSON 格式输出，不要输出任何其他内容：

{
  "summary": "用2-3句话概括文章核心内容（50-150字）",
  "article_type": "文章类型，从以下选一个：录取案例/院校介绍/排名解读/签证指南/考试备考/费用分析/政策动态/申请指南/就业实习/文书辅导/综合资讯",
  "countries": ["涉及的国家/地区，如：英国、美国、澳洲、香港、新加坡等，最多3个"],
  "universities": ["提到的大学名称，最多5个"],
  "key_data": {
    "gpa": "提到的GPA要求或案例GPA，如'3.5/4.0'或'85/100'，没有则为null",
    "ielts": "雅思要求/分数，如'7.0'，没有则为null",
    "toefl": "托福要求/分数，没有则为null",
    "gre": "GRE分数，没有则为null",
    "tuition": "学费信息，没有则为null",
    "deadline": "申请截止日期，没有则为null"
  },
  "target_audience": ["目标人群，从以下选：本科申请/硕士申请/博士申请/低龄留学/语言考试/签证办理/求职就业，最多3个"],
  "tags": ["3-5个关键词标签"],
  "quality_score": 0.0到1.0的质量评分（原创深度、数据丰富度、实用性）
}

注意：
- 如果文章是广告或营销软文（含"保录取""免费试听""扫码咨询"等），article_type 设为"广告营销"
- summary 要提炼核心信息，不要照搬原文
- key_data 中只提取明确提到的数据，不要推测
- tags 应该是有检索价值的关键词

文章内容：
"""


def call_llm_structure(text, title):
    # type: (str, str) -> Optional[dict]
    """调用 LLM 对文章进行结构化提取（带重试）。"""
    content = text[:MAX_CONTENT_LENGTH]
    prompt = f"{STRUCTURE_PROMPT}\n标题：{title}\n\n正文：\n{content}"

    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(
                    f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {LLM_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": LLM_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 4096,
                    },
                )

                # 429 限流 → 等待后重试
                if resp.status_code == 429:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    print(f"  Rate limited (429), retrying in {delay:.0f}s...")
                    time.sleep(delay)
                    continue

                resp.raise_for_status()
                data = resp.json()
                resp_content = data["choices"][0]["message"]["content"]

                # 提取 JSON（可能被 markdown 代码块包裹）
                json_match = re.search(r'\{[\s\S]*\}', resp_content)
                if json_match:
                    json_str = json_match.group()
                    try:
                        result = json.loads(json_str)
                        return result
                    except json.JSONDecodeError:
                        # 尝试修复截断的 JSON（reasoning tokens 可能导致截断）
                        # 逐步尝试闭合大括号
                        for trim in range(3):
                            try:
                                fixed = json_str.rstrip()
                                if fixed.endswith(','):
                                    fixed = fixed[:-1]
                                fixed += '}' * (trim + 1)
                                result = json.loads(fixed)
                                return result
                            except json.JSONDecodeError:
                                continue
                        # 最后尝试：只提取到最后一个完整对象
                        brace_count = 0
                        for i, c in enumerate(json_str):
                            if c == '{':
                                brace_count += 1
                            elif c == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    try:
                                        result = json.loads(json_str[:i+1])
                                        return result
                                    except json.JSONDecodeError:
                                        break
                        return None
                return None

        except httpx.HTTPStatusError:
            raise
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"  LLM error: {e}, retrying in {delay:.0f}s...")
                time.sleep(delay)
            else:
                print(f"  LLM error (final): {e}")
                return None

    return None


# =====================================================================
# 数据库操作
# =====================================================================

def init_kb_tables(conn):
    """创建知识库表结构。"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kb_processed (
            article_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT,
            article_type TEXT DEFAULT '综合资讯',
            countries TEXT DEFAULT '[]',
            universities TEXT DEFAULT '[]',
            key_data TEXT DEFAULT '{}',
            target_audience TEXT DEFAULT '[]',
            tags TEXT DEFAULT '[]',
            quality_score REAL DEFAULT 0.5,
            clean_text TEXT,
            source_url TEXT,
            mp_id TEXT,
            publish_time INTEGER,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # FTS5 虚拟表（搜索用）
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS kb_processed_fts USING fts5(
            article_id, title, summary, clean_text, article_type, countries, tags,
            tokenize='unicode61'
        )
    """)

    # 处理状态追踪
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kb_process_state (
            article_id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'pending',
            reason TEXT,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    print("Knowledge base tables initialized")


def article_generator(werss_conn, kb_conn, limit=0, reprocess=False):
    """逐条生成未处理文章（生成器，避免大 content 撑爆内存）。"""
    processed_ids = set()
    if not reprocess:
        rows = kb_conn.execute("SELECT article_id FROM kb_process_state").fetchall()
        processed_ids = {r[0] for r in rows}

    total_fetched = 0
    cursor_id = None
    target = max(limit, 0) or 999999
    BATCH_SIZE = 10

    while total_fetched < target:
        if cursor_id:
            rows = werss_conn.execute(
                """SELECT id, title, ai_category, publish_time, url, mp_id
                   FROM articles
                   WHERE content IS NOT NULL AND id < ?
                   ORDER BY id DESC
                   LIMIT ?""",
                (cursor_id, BATCH_SIZE)
            ).fetchall()
        else:
            rows = werss_conn.execute(
                """SELECT id, title, ai_category, publish_time, url, mp_id
                   FROM articles
                   WHERE content IS NOT NULL
                   ORDER BY id DESC
                   LIMIT ?""",
                (BATCH_SIZE,)
            ).fetchall()

        if not rows:
            break

        for row in rows:
            aid = str(row[0])
            if aid not in processed_ids:
                # 只对真正要处理的文章加载 content
                content_row = werss_conn.execute(
                    "SELECT content FROM articles WHERE id=?", (row[0],)
                ).fetchone()
                content = content_row[0] if content_row else ""

                yield {
                    "id": aid,
                    "title": row[1] or "",
                    "content": content or "",
                    "ai_category": row[2] or "综合资讯",
                    "publish_time": row[3],
                    "url": row[4] or "",
                    "mp_id": row[5] or "",
                }
                total_fetched += 1
                if total_fetched >= target:
                    break

        cursor_id = rows[-1][0]  # 最后一个 id 作为游标
        
        # 如果这一批全部已处理，继续下一批
        all_processed = all(str(r[0]) in processed_ids for r in rows)
        if all_processed and len(rows) < BATCH_SIZE:
            break


def save_processed(kb_conn, article, structured, clean_text):
    """保存处理结果。"""
    article_id = article["id"]

    # 质量门槛：低于 0.5 不入库
    quality = structured.get("quality_score", 0)
    if quality < 0.5:
        return False

    # 保存结构化数据
    kb_conn.execute("""
        INSERT OR REPLACE INTO kb_processed
        (article_id, title, summary, article_type, countries, universities,
         key_data, target_audience, tags, quality_score, clean_text,
         source_url, mp_id, publish_time, processed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        article_id,
        article["title"],
        structured.get("summary", ""),
        structured.get("article_type", "综合资讯"),
        json.dumps(structured.get("countries", []), ensure_ascii=False),
        json.dumps(structured.get("universities", []), ensure_ascii=False),
        json.dumps(structured.get("key_data", {}), ensure_ascii=False),
        json.dumps(structured.get("target_audience", []), ensure_ascii=False),
        json.dumps(structured.get("tags", []), ensure_ascii=False),
        structured.get("quality_score", 0.5),
        clean_text,
        article.get("url", ""),
        article.get("mp_id", ""),
        article.get("publish_time"),
    ))

    # 更新处理状态
    kb_conn.execute("""
        INSERT OR REPLACE INTO kb_process_state (article_id, status, processed_at)
        VALUES (?, 'done', datetime('now'))
    """, (article_id,))

    # 更新 FTS5 索引
    # 先删除旧记录
    kb_conn.execute("DELETE FROM kb_processed_fts WHERE article_id = ?", (article_id,))

    # 中文分词：在连续中文字符间插入空格
    def space_chinese(text):
        return re.sub(r'([\u4e00-\u9fff])', r' \1 ', text)

    kb_conn.execute("""
        INSERT INTO kb_processed_fts(article_id, title, summary, clean_text, article_type, countries, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        article_id,
        space_chinese(article["title"]),
        space_chinese(structured.get("summary", "")),
        space_chinese(clean_text[:2000]),
        structured.get("article_type", "综合资讯"),
        space_chinese(" ".join(structured.get("countries", []))),
        space_chinese(" ".join(structured.get("tags", []))),
    ))

    kb_conn.commit()


def save_skipped(kb_conn, article_id, reason):
    """记录跳过的文章。"""
    kb_conn.execute("""
        INSERT OR REPLACE INTO kb_process_state (article_id, status, reason, processed_at)
        VALUES (?, 'skipped', ?, datetime('now'))
    """, (article_id, reason))
    kb_conn.commit()


# =====================================================================
# 主流程
# =====================================================================

def process_articles(limit=0, reprocess=False):
    """处理文章主流程。"""
    # 连接数据库
    werss_conn = sqlite3.connect(WERS_DB_PATH)
    werss_conn.row_factory = sqlite3.Row
    werss_conn.execute("PRAGMA query_only=ON")

    kb_conn = sqlite3.connect(ADVISOR_DB_PATH)
    kb_conn.row_factory = sqlite3.Row
    init_kb_tables(kb_conn)

    # 获取待处理文章（生成器）
    gen = article_generator(werss_conn, kb_conn, limit=limit, reprocess=reprocess)

    processed = 0
    skipped = 0
    errors = 0

    for i, article in enumerate(gen):
        title = article["title"][:50]
        print(f"\n[{i+1}] Processing: {title}...")

        # 0. 标题级广告预过滤（不调 LLM，直接跳过）
        if pre_filter_ad(article["title"]):
            print(f"  Skipped: ad_title_pattern")
            save_skipped(kb_conn, article["id"], "ad_title_pattern")
            skipped += 1
            continue

        # 1. 清洗 HTML
        clean_text = clean_html(article["content"])

        # 2. 质量检查
        ok, reason = check_quality(clean_text, article.get("publish_time"))
        if not ok:
            print(f"  Skipped: {reason}")
            save_skipped(kb_conn, article["id"], reason)
            skipped += 1
            continue

        # 3. AI 结构化
        structured = call_llm_structure(clean_text, article["title"])
        if not structured:
            print(f"  Error: AI processing failed")
            save_skipped(kb_conn, article["id"], "ai_error")
            errors += 1
            time.sleep(REQUEST_INTERVAL)
            continue

        # 跳过广告
        if structured.get("article_type") == "广告营销":
            print(f"  Skipped: ad detected by AI")
            save_skipped(kb_conn, article["id"], "ad_detected")
            skipped += 1
            time.sleep(REQUEST_INTERVAL)
            continue

        # 4. 保存结果
        save_processed(kb_conn, article, structured, clean_text)
        processed += 1
        print(f"  Done: type={structured.get('article_type')}, "
              f"score={structured.get('quality_score', 0):.2f}, "
              f"countries={structured.get('countries', [])}")

        # 限流
        time.sleep(REQUEST_INTERVAL)

    # 汇总
    total_processed = processed + skipped + errors
    print(f"\n{'='*50}")
    print(f"Processing complete:")
    print(f"  Processed: {processed}")
    print(f"  Skipped:   {skipped}")
    print(f"  Errors:    {errors}")
    print(f"  Total:     {total_processed}")

    werss_conn.close()
    kb_conn.close()


def show_stats():
    """显示处理状态统计。"""
    kb_conn = sqlite3.connect(ADVISOR_DB_PATH)

    try:
        total = kb_conn.execute("SELECT COUNT(*) FROM kb_process_state").fetchone()[0]
        done = kb_conn.execute("SELECT COUNT(*) FROM kb_process_state WHERE status='done'").fetchone()[0]
        skipped = kb_conn.execute("SELECT COUNT(*) FROM kb_process_state WHERE status='skipped'").fetchone()[0]
        # 查询 werss.db 总文章数（不检查 content，避免全表扫描）
        try:
            import sqlite3 as _sqlite3
            _wc = _sqlite3.connect(WERS_DB_PATH)
            werss_total = _wc.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            _wc.close()
            real_pending = max(0, werss_total - total)
        except Exception:
            real_pending = "?"
            werss_total = "?"

        print(f"\n=== 知识库处理状态 ===")
        print(f"已入库:     {done}")
        print(f"已跳过:     {skipped}")
        print(f"已跟踪:     {total}")
        print(f"待处理:     ~{real_pending}  (werss总文章: {werss_total})")

        if done > 0:
            print(f"\n=== 文章类型分布 ===")
            rows = kb_conn.execute(
                "SELECT article_type, COUNT(*) as cnt FROM kb_processed GROUP BY article_type ORDER BY cnt DESC"
            ).fetchall()
            for r in rows:
                print(f"  {r[0]}: {r[1]}")

            print(f"\n=== 国家/地区分布 ===")
            rows = kb_conn.execute("SELECT countries FROM kb_processed").fetchall()
            country_count = {}
            for r in rows:
                try:
                    countries = json.loads(r[0])
                    for c in countries:
                        country_count[c] = country_count.get(c, 0) + 1
                except:
                    pass
            for c, n in sorted(country_count.items(), key=lambda x: -x[1]):
                print(f"  {c}: {n}")

            print(f"\n=== 质量评分分布 ===")
            rows = kb_conn.execute(
                "SELECT CASE WHEN quality_score >= 0.8 THEN '高(0.8+)' "
                "WHEN quality_score >= 0.5 THEN '中(0.5-0.8)' "
                "ELSE '低(<0.5)' END, COUNT(*) FROM kb_processed GROUP BY 1"
            ).fetchall()
            for r in rows:
                print(f"  {r[0]}: {r[1]}")

        # 跳过原因统计
        if skipped > 0:
            print(f"\n=== 跳过原因 ===")
            rows = kb_conn.execute(
                "SELECT reason, COUNT(*) as cnt FROM kb_process_state WHERE status='skipped' GROUP BY reason ORDER BY cnt DESC"
            ).fetchall()
            for r in rows:
                print(f"  {r[0]}: {r[1]}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        kb_conn.close()


# =====================================================================
# CLI
# =====================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="知识库 ETL 管道")
    parser.add_argument("--limit", type=int, default=0, help="限制处理数量（0=全部）")
    parser.add_argument("--reprocess-all", action="store_true", help="重新处理所有文章")
    parser.add_argument("--stats", action="store_true", help="显示处理状态")
    args = parser.parse_args()

    if args.stats:
        show_stats()
    else:
        process_articles(limit=args.limit, reprocess=args.reprocess_all)
