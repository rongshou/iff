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


def ensure_schema(advisor_db: Path) -> None:
    conn = sqlite3.connect(str(advisor_db))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_search_index (
            article_id TEXT PRIMARY KEY,
            search_text TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now', '+8 hours'))
        )
    """)
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

    batch: list[tuple[str, str]] = []
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
            batch.append((r[0], text))
        dst.executemany(
            "INSERT OR REPLACE INTO article_search_index(article_id, search_text) VALUES(?, ?)",
            batch,
        )
        dst.commit()
        done += len(batch)
        print(f"  进度: {done}/{total}", file=sys.stderr)
        batch.clear()

    src.close()
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
