#!/usr/bin/env python3
"""
迁移 us_admission_info 中的 TOEFL 数据到 universities 表。
在 universities 表新增 toefl_total / toefl_new_total / toefl_new_sections / toefl_notes 列，
并与 us_admission_info 通过校名匹配后填入。
"""
import sqlite3
import json

DB_PATH = "/home/admin/tianquan/backend/data/advisor.db"

# us_admission_info 校名 → universities 校名的映射
NAME_MAP = {
    "伊利诺伊大学厄巴纳-香槟分校": "伊利诺伊大学厄巴纳香槟分校",
    "东北大学(美国)": "东北大学（美国）",
    "华盛顿大学圣路易斯": "圣路易斯华盛顿大学",
    "德州大学奥斯汀分校": "德克萨斯大学奥斯汀分校",
    "理海大学": "里海大学",
}


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. 加列 (IF NOT EXISTS 用 try-except 兼容重复运行)
    new_cols = [
        ("toefl_total", "INTEGER"),         # 旧托福 0-120
        ("toefl_new_total", "REAL"),         # 新托福 1-6
        ("toefl_new_sections", "TEXT"),      # JSON 单科要求
        ("toefl_notes", "TEXT"),             # 补充说明
    ]
    for col_name, col_type in new_cols:
        existing = [r[1] for r in cur.execute("PRAGMA table_info(universities)").fetchall()]
        if col_name not in existing:
            cur.execute(f"ALTER TABLE universities ADD COLUMN {col_name} {col_type}")
            print(f"  + 新增列: {col_name} ({col_type})")
        else:
            print(f"  = 列已存在: {col_name}")

    # 2. 读取 us_admission_info 的 TOEFL 数据
    rows = cur.execute("""
        SELECT university, toefl_min, toefl_new_total, toefl_new_sections, toefl_notes
        FROM us_admission_info
        WHERE toefl_min IS NOT NULL OR toefl_new_total IS NOT NULL
    """).fetchall()

    updated = 0
    skipped_name = []
    skipped_empty = []

    for row in rows:
        uni_name = row[0]
        toefl_min = row[1]
        toefl_new_total = row[2]
        toefl_new_sections = row[3] if row[3] else None
        toefl_notes = row[4] if row[4] else None

        if toefl_min is None and toefl_new_total is None:
            skipped_empty.append(uni_name)
            continue

        # 校名映射
        target_name = NAME_MAP.get(uni_name, uni_name)

        t = cur.execute("SELECT id FROM universities WHERE name = ?", (target_name,)).fetchone()
        if not t:
            skipped_name.append(uni_name)
            continue

        uni_id = t[0]
        # 处理 sections JSON (存储为字符串)
        sections_str = None
        if toefl_new_sections:
            if isinstance(toefl_new_sections, str):
                sections_str = toefl_new_sections
            else:
                sections_str = json.dumps(toefl_new_sections, ensure_ascii=False)

        cur.execute("""
            UPDATE universities
            SET toefl_total = ?,
                toefl_new_total = ?,
                toefl_new_sections = ?,
                toefl_notes = ?
            WHERE id = ?
        """, (toefl_min, toefl_new_total, sections_str, toefl_notes, uni_id))
        updated += 1

        if updated <= 5 or uni_name in ["波士顿大学", "佛罗里达大学"]:
            print(f"  ✓ {uni_name:20s} → toefl_total={toefl_min!s:>4s}  new_total={str(toefl_new_total or ''):>4s}")

    conn.commit()
    conn.close()

    print(f"\n完成！更新了 {updated} 所学校")
    if skipped_name:
        print(f"  ⚠ 未匹配校名 ({len(skipped_name)}): {', '.join(skipped_name)}")
    if skipped_empty:
        print(f"  - 跳过无数据的 ({len(skipped_empty)}): 已忽略")


if __name__ == "__main__":
    main()
