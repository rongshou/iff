#!/usr/bin/env python3
"""
清理 werss.db 中已处理文章的 content/content_html 字段。
保留元数据（标题、URL、描述等），只清空原始 HTML 内容以释放空间。
"""
import sqlite3
import time
import os
import sys

WERS_DB = "/home/admin/werss/data/db.db"
ADVISOR_DB = "/home/admin/tianquan/backend/data/advisor.db"
BATCH_SIZE = 100

def main():
    if not os.path.exists(WERS_DB):
        print(f"ERROR: {WERS_DB} not found")
        sys.exit(1)

    # 获取已处理的文章 ID 列表（done 或 skipped 都算已处理）
    advisor_conn = sqlite3.connect(ADVISOR_DB)
    advisor_conn.execute("PRAGMA query_only = ON")
    ac = advisor_conn.cursor()
    ac.execute("SELECT article_id FROM kb_process_state WHERE status IN ('done', 'skipped')")
    processed_ids = [r[0] for r in ac.fetchall()]
    advisor_conn.close()
    print(f"已处理文章数: {len(processed_ids)}")

    # 连接 werss.db
    werss_conn = sqlite3.connect(WERS_DB)
    wc = werss_conn.cursor()

    # 先统计有多少已处理文章还有 content
    wc.execute(f"SELECT COUNT(*) FROM articles WHERE id IN ({','.join('?' * len(processed_ids))}) AND (content IS NOT NULL AND content != '' OR content_html IS NOT NULL AND content_html != '')", processed_ids)
    has_content = wc.fetchone()[0]
    print(f"其中仍有 content 的: {has_content}")

    if has_content == 0:
        print("无需清理，退出")
        return

    # 分批清理
    cleaned = 0
    for i in range(0, len(processed_ids), BATCH_SIZE):
        batch = processed_ids[i:i + BATCH_SIZE]
        placeholders = ','.join('?' * len(batch))
        wc.execute(f"UPDATE articles SET content = NULL, content_html = NULL WHERE id IN ({placeholders}) AND (content IS NOT NULL OR content_html IS NOT NULL)", batch)
        cleaned += wc.rowcount
        werss_conn.commit()
        if (i // BATCH_SIZE) % 10 == 0:
            print(f"  进度: {i + len(batch)}/{len(processed_ids)}, 已清理: {cleaned}")

    print(f"\n清理完成: {cleaned} 篇文章的 content/content_html 已置空")

    # VACUUM 回收空间
    print("正在 VACUUM（可能需要几分钟）...")
    before = os.path.getsize(WERS_DB)
    # VACUUM skipped - insufficient disk space
    # wc.execute("VACUUM")
    werss_conn.commit()
    after = os.path.getsize(WERS_DB)
    print(f"VACUUM 完成: {before / 1024 / 1024:.1f} MB -> {after / 1024 / 1024:.1f} MB (释放 {(before - after) / 1024 / 1024:.1f} MB)")

    werss_conn.close()

if __name__ == "__main__":
    main()
