"""
天权知识库 - 文章搜索索引构建脚本

从 werss.articles 提取 title + description + content(去HTML, 前3000字符),
写入 tianquan advisor.db 的 article_search_index 表。

news_knowledge 检索时 JOIN 该表,用 search_text LIKE 提升召回率。
werss 原库不动;可重复运行(idempotent,会覆盖旧数据)。
"""
import re
import sqlite3
import sys
from pathlib import Path

WERS_DB = Path("/home/admin/werss/data/db.db")
ADVISOR_DB = Path(__file__).parent.parent / "backend" / "data" / "advisor.db"

CONTENT_EXCERPT_LEN = 3000
SQL_CONTENT_LEN = 8000
BATCH_SIZE = 200

# HTML 标签/实体清理
TAG_RE = re.compile(r"<[^>]+>")
ENTITY_RE = re.compile(r"&[a-zA-Z]+;|&#\d+;")
WS_RE = re.compile(r"\s+")

# 分类关键词(与 news_knowledge.py 的 CATEGORY_KEYWORDS 保持一致)
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "选校与申请": ["选校", "申请", "录取", "offer", "定位", "排名", "择校", "院校", "专业", "项目", "硕士", "本科", "博士", "文书", "PS", "简历", "CV", "推荐信", "作品集", "面试"],
    "语言考试": ["雅思", "托福", "IELTS", "TOEFL", "GRE", "GMAT", "PTE", "DET", "多邻国", "语言成绩", "语言考试", "标化", "SAT", "ACT"],
    "签证与出入境": ["签证", "出入境", "入境", "签证材料", "I-20", "CAS", "COE", "护照", "续签", "工签"],
    "就业与实习": ["就业", "实习", "求职", "OPT", "CPT", "秋招", "春招", "校招", "薪酬", "薪资", "年薪"],
    "费用与奖学金": ["费用", "学费", "奖学金", "省钱", "花费", "开支", "助学金", "全奖", "半奖", "生活费"],
    "排名与榜单": ["排名", "QS", "USNews", "THE", "软科", "ARWU", "榜单"],
    "政策与解读": ["政策", "解读", "改革", "变化", "新政", "规定", "调整"],
    "大学动态": ["大学", "学院", "校区", "新开", "扩招", "停招", "升级", "成立"],
    "低龄留学": ["低龄", "高中", "初中", "小学", "陪读", "预科", "游学", "夏校", "夏令营"],
    "生活适应": ["住宿", "租房", "医保", "交通", "饮食", "安全", "文化差异"],
    "考试技巧": ["技巧", "备考", "提分", "刷题", "单词", "口语", "写作"],
}


def strip_html(html: str) -> str:
    if not html:
        return ""
    text = TAG_RE.sub(" ", html)
    text = ENTITY_RE.sub(" ", text)
    text = WS_RE.sub(" ", text).strip()
    return text


def build_search_text(title: str, description: str, content_clean: str) -> str:
    parts = [p for p in [title, description, content_clean] if p]
    return " ".join(parts)[:8000]


def infer_category(title: str, description: str, content_excerpt: str) -> str:
    """根据标题+描述+正文摘要,用关键词规则推断文章分类。
    优先用标题命中(权重高),其次描述,最后正文。
    """
    scores: dict[str, int] = {}
    text_layers = [(title, 3), (description, 2), (content_excerpt[:500], 1)]
    for text, weight in text_layers:
        if not text:
            continue
        for category, words in CATEGORY_KEYWORDS.items():
            for w in words:
                if w.lower() in text.lower():
                    scores[category] = scores.get(category, 0) + weight
                    break
    if not scores:
        return "综合资讯"
    return max(scores, key=scores.get)


def ensure_schema(advisor_db: Path) -> None:
    conn = sqlite3.connect(str(advisor_db))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_search_index (
            article_id TEXT PRIMARY KEY,
            search_text TEXT NOT NULL,
            inferred_category TEXT DEFAULT '综合资讯',
            updated_at TEXT DEFAULT (datetime('now', '+8 hours'))
        )
    """)
    # 兼容已有表: 补列
    cols = {r[1] for r in conn.execute("PRAGMA table_info(article_search_index)").fetchall()}
    if "inferred_category" not in cols:
        conn.execute(
            "ALTER TABLE article_search_index ADD COLUMN inferred_category TEXT DEFAULT '综合资讯'"
        )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_search_text ON article_search_index(article_id)"
    )
    conn.commit()
    conn.close()


def build_index(wers_db: Path, advisor_db: Path) -> int:
    src = sqlite3.connect(str(wers_db))
    dst = sqlite3.connect(str(advisor_db))
    dst.execute("DELETE FROM article_search_index")

    # 在数据库侧用 substr 截取 content,避免把 1.9M 字符的完整内容加载到内存
    cursor = src.execute(
        f"SELECT id, title, description, substr(content, 1, {SQL_CONTENT_LEN}) FROM articles"
    )
    total = src.execute("SELECT COUNT(*) FROM articles").fetchone()[0]

    batch: list[tuple[str, str, str]] = []
    done = 0
    while True:
        rows = cursor.fetchmany(BATCH_SIZE)
        if not rows:
            break
        for r in rows:
            content_clean = strip_html(r[3] or "")
            if len(content_clean) > CONTENT_EXCERPT_LEN:
                content_clean = content_clean[:CONTENT_EXCERPT_LEN]
            text = build_search_text(r[1] or "", r[2] or "", content_clean)
            cat = infer_category(r[1] or "", r[2] or "", content_clean)
            batch.append((r[0], text, cat))
        dst.executemany(
            "INSERT OR REPLACE INTO article_search_index(article_id, search_text, inferred_category) "
            "VALUES(?, ?, ?)",
            batch,
        )
        dst.commit()
        done += len(batch)
        print(f"  进度: {done}/{total}", file=sys.stderr)
        batch.clear()

    src.close()

    # 统计推断分类覆盖率
    stats = dst.execute(
        "SELECT inferred_category, COUNT(*) FROM article_search_index "
        "GROUP BY inferred_category ORDER BY COUNT(*) DESC"
    ).fetchall()
    print("\n推断分类分布:", file=sys.stderr)
    for cat, n in stats:
        print(f"  {cat}: {n}", file=sys.stderr)

    dst.close()
    return done


def main() -> int:
    if not WERS_DB.exists():
        print(f"ERROR: werss db 不存在: {WERS_DB}", file=sys.stderr)
        return 1
    if not ADVISOR_DB.exists():
        print(f"ERROR: advisor db 不存在: {ADVISOR_DB}", file=sys.stderr)
        return 1

    print(f"建索引表: {ADVISOR_DB}")
    ensure_schema(ADVISOR_DB)
    print(f"从 werss 读取文章: {WERS_DB}")
    n = build_index(WERS_DB, ADVISOR_DB)
    print(f"完成,索引 {n} 篇文章。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
