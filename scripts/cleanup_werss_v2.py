#!/usr/bin/env python3
"""
清理 werss.db 中已处理文章的 content/content_html 字段。
使用 ATTACH + JOIN 方式避免大 IN 查询。
"""
import sqlite3
import os
import sys

WERS_DB = "/home/admin/werss/data/db.db"
ADVISOR_DB = "/home/admin/tianquan/backend/data/advisor.db"

def main():
    print("连接数据库...")
    conn = sqlite3.connect(WERS_DB)
    conn.execute(f"ATTACH DATABASE '{ADVISOR_DB}' AS advisor")

    # 直接用 SQL JOIN 清理，避免 Python 传 2000+ 参数
    print("统计待清理文章数...")
    c = conn.execute("""
        SELECT COUNT(*) FROM articles a
        INNER JOIN advisor.kb_process_state k ON a.id = k.article_id
        WHERE k.status IN ('done', 'skipped') AND a.content IS NOT NULL
    """)
    count = c.fetchone()[0]
    print(f"待清理: {count} 篇")

    if count == 0:
        print("无需清理")
        conn.close()
        return

    # 分批清理（用 rowid 范围分批）
    print("开始清理...")
    total_cleaned = 0
    while True:
        c = conn.execute("""
            UPDATE articles SET content = NULL, content_html = NULL
            WHERE rowid IN (
                SELECT a.rowid FROM articles a
                INNER JOIN advisor.kb_process_state k ON a.id = k.article_id
                WHERE k.status IN ('done', 'skipped') AND a.content IS NOT NULL
                LIMIT 200
            )
        """)
        conn.commit()
        cleaned = c.rowcount
        total_cleaned += cleaned
        if cleaned == 0:
            break
        print(f"  已清理: {total_cleaned}/{count}")

    print(f"清理完成: {total_cleaned} 篇")

    # 检查磁盘空间是否够 VACUUM
    db_size = os.path.getsize(WERS_DB)
    stat = os.statvfs(os.path.dirname(WERS_DB))
    free_space = stat.f_bavail * stat.f_frsize
    print(f"DB 大小: {db_size / 1024 / 1024:.1f} MB")
    print(f"磁盘可用: {free_space / 1024 / 1024:.1f} MB")

    if free_space > db_size * 1.5:
        print("磁盘空间充足，执行 VACUUM...")
        conn.execute("VACUUM")
        conn.commit()
        new_size = os.path.getsize(WERS_DB)
        print(f"VACUUM 完成: {db_size / 1024 / 1024:.1f} MB -> {new_size / 1024 / 1024:.1f} MB")
    else:
        print("磁盘空间不足，跳过 VACUUM（需先释放磁盘空间）")

    conn.close()
    print("完成!")

if __name__ == "__main__":
    main()
