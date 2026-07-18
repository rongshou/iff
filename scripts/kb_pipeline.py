#!/usr/bin/env python3
"""知识库 ETL 管道 v3：内存优化版，游标迭代，不 fetchall"""
import os, sys, json, time, re, sqlite3, argparse

WERS_DB_PATH = "/home/admin/werss/data/db.db"
ADVISOR_DB_PATH = "/home/admin/tianquan/backend/data/advisor.db"
LLM_BASE_URL = "https://opencode.ai/zen/go/v1"
LLM_API_KEY = "sk-J7OYUgPKmRT3pcOD8W3Vld7YiEu1G1fVhBPHlGBHeWB8dPOWh0aSpCtTIR9jpPUn"
LLM_MODEL = "qwen3.6-plus"
REQUEST_INTERVAL = 0.5
MAX_CONTENT_LENGTH = 2000
MAX_RETRIES = 3

def to_str(v):
    if v is None: return ""
    if isinstance(v, str): return v
    return json.dumps(v, ensure_ascii=False)

RETRY_BASE_DELAY = 5

STRUCTURE_PROMPT = """你是一个留学资讯分析专家。请分析以下文章并输出严格的 JSON，包含：
- article_type: 综合资讯/申请指南/院校介绍/政策动态/排名解读/就业实习/录取案例/签证指南/费用分析/考试备考/文书辅导/广告营销/其他
- summary: 100-200字中文摘要
- countries: 国家/地区列表
- universities: 大学列表
- key_data: 关键数据点
- target_audience: 目标受众
- tags: 3-5个标签
- quality_score: 0-1质量评分
只输出 JSON。"""

AD_TITLE_PATTERNS = [r"实习信息汇总", r"实习.*汇总", r"5\.\d+实习", r"6\.\d+实习", r"7\.\d+实习"]

def pre_filter_ad(title):
    return bool(title) and any(re.search(p, title) for p in AD_TITLE_PATTERNS)

def clean_html(html):
    if not html: return ""
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    return re.sub(r'\s+', ' ', text).strip()[:5000]

def call_llm_structure(text, title):
    import httpx
    prompt = f"{STRUCTURE_PROMPT}\n标题：{title}\n\n正文：\n{text[:MAX_CONTENT_LENGTH]}"
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(
                    f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
                    json={"model": LLM_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 4096})
                if resp.status_code == 429 or resp.status_code >= 400:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    print(f"  API error {resp.status_code}, retrying in {delay:.0f}s...", flush=True)
                    time.sleep(delay); continue
                resp.raise_for_status()
                resp_content = resp.json()["choices"][0]["message"]["content"]
                m = re.search(r'\{[\s\S]*\}', resp_content)
                if m:
                    try: return json.loads(m.group())
                    except: 
                        for t in range(3):
                            try: return json.loads(m.group().rstrip().rstrip(',') + '}'*(t+1))
                            except: continue
                return None
        except Exception as e:
            delay = RETRY_BASE_DELAY * (2 ** attempt)
            print(f"  LLM error: {e}, retrying in {delay:.0f}s...", flush=True)
            time.sleep(delay)
    return None

def process_articles(limit=None, reprocess=False):
    # 连接 DB
    kb_conn = sqlite3.connect(ADVISOR_DB_PATH)
    kb_conn.execute("""CREATE TABLE IF NOT EXISTS kb_process_state (article_id TEXT PRIMARY KEY, status TEXT, reason TEXT, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    kb_conn.execute("""CREATE TABLE IF NOT EXISTS kb_processed (article_id TEXT PRIMARY KEY, title TEXT, summary TEXT, article_type TEXT, countries TEXT, universities TEXT, key_data TEXT, target_audience TEXT, tags TEXT, quality_score REAL, clean_text TEXT, source_url TEXT, mp_id TEXT, publish_time INTEGER, processed_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    kb_conn.commit()

    # 获取已跟踪 ID（只取 ID，不占太多内存）
    tracked_ids = set(r[0] for r in kb_conn.execute("SELECT article_id FROM kb_process_state").fetchall())
    print(f"已跟踪: {len(tracked_ids)}", flush=True)

    # 统计
    kb_count = kb_conn.execute("SELECT COUNT(*) FROM kb_processed").fetchone()[0]
    done = kb_conn.execute("SELECT COUNT(*) FROM kb_process_state WHERE status='done'").fetchone()[0]
    skipped = kb_conn.execute("SELECT COUNT(*) FROM kb_process_state WHERE status='skipped'").fetchone()[0]

    wers_conn = sqlite3.connect(f"file:{WERS_DB_PATH}?mode=ro", uri=True)
    wers_total = wers_conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    print(f"知识库: kb_processed={kb_count} | 入库={done} 跳过={skipped} | werss总计={wers_total} | 待处理={wers_total-len(tracked_ids)}\n", flush=True)

    # 用游标逐条迭代，不 fetchall
    query = "SELECT id, title, content, url, mp_id, publish_time FROM articles WHERE content IS NOT NULL AND content != '' ORDER BY publish_time DESC"
    cursor = wers_conn.execute(query)

    processed = skipped_count = errors = count = 0
    target = limit or 999999

    for row in cursor:
        if count >= target: break
        aid, title, content, url, mp_id, publish_time = row

        # 跳过已跟踪
        if aid in tracked_ids: continue
        count += 1

        print(f"[{count}] Processing: {title[:50]}...", flush=True)

        # 广告预过滤
        if pre_filter_ad(title):
            print(f"  Skipped: ad_title_pattern", flush=True)
            kb_conn.execute("INSERT OR REPLACE INTO kb_process_state VALUES (?, 'skipped', 'ad_title_pattern', datetime('now'))", (aid,))
            kb_conn.commit(); skipped_count += 1; continue

        # HTML 清洗
        clean_text = clean_html(content)
        if len(clean_text) < 100:
            print(f"  Skipped: content_too_short", flush=True)
            kb_conn.execute("INSERT OR REPLACE INTO kb_process_state VALUES (?, 'skipped', 'content_too_short', datetime('now'))", (aid,))
            kb_conn.commit(); skipped_count += 1; continue

        # LLM 结构化
        structured = call_llm_structure(clean_text, title)
        if not structured:
            print(f"  Error: AI failed", flush=True)
            kb_conn.execute("INSERT OR REPLACE INTO kb_process_state VALUES (?, 'skipped', 'ai_error', datetime('now'))", (aid,))
            kb_conn.commit(); errors += 1; continue

        quality_score = float(structured.get("quality_score", 0))
        article_type = structured.get("article_type", "其他")

        if article_type == "广告营销":
            print(f"  Skipped: ad_detected", flush=True)
            kb_conn.execute("INSERT OR REPLACE INTO kb_process_state VALUES (?, 'skipped', 'ad_detected', datetime('now'))", (aid,))
            kb_conn.commit(); skipped_count += 1; continue

        if quality_score < 0.5:
            print(f"  Skipped: low_quality ({quality_score})", flush=True)
            kb_conn.execute("INSERT OR REPLACE INTO kb_process_state VALUES (?, 'skipped', 'low_quality', datetime('now'))", (aid,))
            kb_conn.commit(); skipped_count += 1; continue

        # 入库
        kb_conn.execute("""INSERT OR REPLACE INTO kb_processed (article_id, title, summary, article_type, countries, universities, key_data, target_audience, tags, quality_score, clean_text, source_url, mp_id, publish_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (aid, title, structured.get("summary",""), article_type, json.dumps(structured.get("countries",[]),ensure_ascii=False), json.dumps(structured.get("universities",[]),ensure_ascii=False), to_str(structured.get("key_data","")), to_str(structured.get("target_audience","")), json.dumps(structured.get("tags",[]),ensure_ascii=False), quality_score, clean_text[:2000], url, mp_id, publish_time))
        kb_conn.execute("INSERT OR REPLACE INTO kb_process_state VALUES (?, 'done', NULL, datetime('now'))", (aid,))
        kb_conn.commit()
        print(f"  Done: type={article_type}, score={quality_score}, countries={structured.get('countries',[])}", flush=True)
        processed += 1
        time.sleep(REQUEST_INTERVAL)

    print(f"\nComplete: Processed={processed}, Skipped={skipped_count}, Errors={errors}, Total={count}", flush=True)
    wers_conn.close(); kb_conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--reprocess-all", action="store_true")
    args = parser.parse_args()
    process_articles(limit=args.limit, reprocess=args.reprocess_all)
