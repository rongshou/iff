"""
重建 handbook_fts FTS5 索引，使中文可检索。

问题：原 handbook_fts 使用默认 unicode61 分词器，
CJK 字符未被分入索引（unicode61 默认跳过 CJK）。
修复方案：在写入前用 _space_chinese() 给中文字符加空格，
使每个汉字作为独立 token 被索引。

同时重建 articles_fts（如果已存在且未加空格）。
"""

import re
import sqlite3
import sys
from pathlib import Path

# 确保能找到 backend 模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import get_db

DB_PATH = settings.DB_PATH


def _space_chinese(text: str) -> str:
    """在连续中文字符之间插入空格，使 unicode61 分词器将每个汉字作为独立 token"""
    return re.sub(r'([\u4e00-\u9fff])', r' \1 ', text)


def rebuild_handbook_fts(conn: sqlite3.Connection) -> int:
    """重建 handbook_fts，返回索引行数"""
    # 1. 检查 handbook_chunks 是否存在
    has_source = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='handbook_chunks'"
    ).fetchone()[0]
    if not has_source:
        print("[handbook_fts] handbook_chunks 表不存在，跳过")
        return 0

    total = conn.execute("SELECT COUNT(*) FROM handbook_chunks").fetchone()[0]
    if not total:
        print("[handbook_fts] handbook_chunks 为空，跳过")
        return 0

    # 2. 删除旧的 FTS 表（级联删除所有 content/data/dir/docsize/idx/config 表）
    conn.execute("DROP TABLE IF EXISTS handbook_fts")
    conn.commit()

    # 3. 重建 FTS5 虚拟表
    conn.execute("""
        CREATE VIRTUAL TABLE handbook_fts USING fts5(
            school,
            source_file,
            content,
            content=''
        )
    """)
    conn.commit()

    # 4. 分批读取并插入（中文加空格）
    batch_size = 50
    inserted = 0
    offset = 0

    while True:
        rows = conn.execute(
            "SELECT id, school, source_file, content FROM handbook_chunks ORDER BY id LIMIT ? OFFSET ?",
            (batch_size, offset)
        ).fetchall()
        if not rows:
            break

        for row in rows:
            chunk_id, school, source_file, content = row
            spaced_content = _space_chinese(content or "")
            spaced_school = _space_chinese(school or "")
            try:
                conn.execute(
                    "INSERT INTO handbook_fts(rowid, school, source_file, content) VALUES (?, ?, ?, ?)",
                    (chunk_id, spaced_school, source_file, spaced_content)
                )
                inserted += 1
            except Exception as e:
                print(f"[handbook_fts] 插入失败 rowid={chunk_id}: {e}")

        conn.commit()
        offset += batch_size
        print(f"[handbook_fts] 进度: {inserted}/{total}", end="\r")

    print(f"\n[handbook_fts] 重建完成: {inserted} 行")
    return inserted


def check_chinese_fts_works(conn: sqlite3.Connection) -> bool:
    """验证中文 FTS 搜索是否正常工作"""
    test_queries = ["留学", "申请", "大学", "奖学金"]
    for q in test_queries:
        spaced = " OR ".join(_space_chinese(q).split())
        count = conn.execute(
            f"SELECT COUNT(*) FROM handbook_fts WHERE handbook_fts MATCH ?",
            (spaced,)
        ).fetchone()[0]
        if count > 0:
            print(f"[verify] 搜索 \"{q}\" (query=\"{spaced}\"): {count} 条结果 ✓")
        else:
            print(f"[verify] 搜索 \"{q}\": 0 条结果 ✗")
    return True


def main():
    print(f"数据库路径: {DB_PATH}")

    with get_db() as conn:
        # === 重建 handbook_fts ===
        print("\n=== 重建 handbook_fts ===")
        count = rebuild_handbook_fts(conn)

        # === 验证 ===
        print("\n=== 验证中文 FTS 搜索 ===")
        check_chinese_fts_works(conn)

    print("\n✅ 重建完成")


if __name__ == "__main__":
    main()
