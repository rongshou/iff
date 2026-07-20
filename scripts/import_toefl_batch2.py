#!/usr/bin/env python3
"""
批量导入美国大学新托福(2026年1-6分制)要求 — 第二批
覆盖：文理学院Top30+、更多国立大学、艺术/特殊院校
"""
import sqlite3
import json

DB_PATH = "/home/admin/tianquan/backend/data/advisor.db"

# ============================================================
# A. 修复已有学校缺失的新托福数据
# ============================================================
FIX_EXISTING = {
    "哈佛大学": (None, None, "无官方最低；竞争者旧制110+/新制5.5+。GSAS最低80(各科22+)；商学院最低109(口语/写作26+)；教育学院最低104(各科26+)；工程最低90(建议100+)"),
    "普林斯顿大学": (None, None, "无官方最低；竞争者旧制115+/新制5.5+。建议口语27+"),
    "华盛顿大学": (4.0, None, "旧制76→新制3.5-4.0。因项目而异（此为DC的George Washington University，非UW Seattle）"),
}

# ============================================================
# B. 新增学校数据
# ============================================================
# 格式: (中文名, 英文名, qs_rank, usnews_rank, toefl_old, toefl_new_total, toefl_new_sections, notes)

NEW_SCHOOLS = [
    # ====== 顶级文理学院 ======
    ("威廉姆斯学院", "Williams College", 0, 1, None, None, None, "无官方最低；竞争者旧制100+/新制5.0+"),
    ("阿默斯特学院", "Amherst College", 0, 2, 100, 5.0, None, "旧制100→新制5.0。各科25+(旧制)/5.0+(新制)"),
    ("斯沃斯莫尔学院", "Swarthmore College", 0, 3, None, None, None, "无官方最低；竞争者旧制100+/新制5.0+"),
    ("韦尔斯利学院", "Wellesley College", 0, 4, None, None, None, "无官方最低；竞争者旧制100+/新制5.0+(女校)"),
    ("波莫纳学院", "Pomona College", 0, 5, 100, 5.0, None, "旧制100→新制5.0"),
    ("鲍登学院", "Bowdoin College", 0, 6, 100, 5.0, None, "旧制100→新制5.0"),
    ("明德学院", "Middlebury College", 0, 7, 109, 5.5, None, "旧制109→新制5.5。文理学院中最高之一"),
    ("哈弗福德学院", "Haverford College", 0, 8, 100, 5.0, None, "旧制100→新制5.0"),
    ("克莱蒙特·麦肯纳学院", "Claremont McKenna College", 0, 9, 100, 5.0, None, "旧制100→新制5.0"),
    ("卡尔顿学院", "Carleton College", 0, 10, 100, 5.0, None, "旧制100→新制5.0"),
    ("瓦萨学院", "Vassar College", 0, 11, 100, 5.0, None, "旧制100→新制5.0"),
    ("汉密尔顿学院", "Hamilton College", 0, 12, 100, 5.0, None, "旧制100→新制5.0。建议5.5+"),
    ("科尔盖特大学", "Colgate University", 0, 13, None, None, None, "无官方最低；竞争者旧制100+/新制5.0+"),
    ("格林内尔学院", "Grinnell College", 0, 14, 105, 5.0, None, "旧制105→新制5.0+"),
    ("戴维森学院", "Davidson College", 0, 15, 100, 5.0, None, "旧制100→新制5.0"),
    ("卫斯理安大学", "Wesleyan University", 0, 16, 100, 5.0, None, "旧制100→新制5.0"),
    ("科尔比学院", "Colby College", 0, 17, 100, 5.0, None, "旧制100→新制5.0"),
    ("玛卡莱斯特学院", "Macalester College", 0, 18, 100, 5.0, None, "旧制100→新制5.0"),
    ("欧柏林学院", "Oberlin College", 0, 19, 100, 5.0, None, "旧制100→新制5.0。音乐院要求更高"),
    ("凯尼恩学院", "Kenyon College", 0, 20, 100, 5.0, None, "旧制100→新制5.0"),
    ("盖茨堡学院", "Gettysburg College", 0, 21, 100, 5.0, None, "旧制100→新制5.0"),
    ("巴克内尔大学", "Bucknell University", 0, 22, 100, 5.0, None, "旧制100→新制5.0"),
    ("科罗拉多学院", "Colorado College", 0, 23, 100, 5.0, None, "旧制100→新制5.0"),
    ("西方学院", "Occidental College", 0, 24, 100, 5.0, None, "旧制100→新制5.0"),
    ("惠特曼学院", "Whitman College", 0, 25, 85, 4.5, None, "旧制85→新制4.5"),
    ("拉法耶特学院", "Lafayette College", 0, 26, 95, 5.0, None, "旧制95→新制5.0"),
    ("联合学院", "Union College", 0, 27, 90, 4.5, None, "旧制90→新制4.5"),
    ("里士满大学", "University of Richmond", 0, 28, 80, 4.0, None, "旧制80→新制4.0"),
    ("斯基德莫尔学院", "Skidmore College", 0, 29, None, None, None, "无官方最低；竞争者旧制90+/新制4.5+"),
    ("傅尔曼大学", "Furman University", 0, 30, None, None, None, "无官方最低；竞争者旧制90+/新制4.5+"),
    ("里德学院", "Reed College", 0, 31, None, None, None, "无官方最低；竞争者旧制90+/新制4.5+"),

    # ====== 更多国立大学（Top 50-150） ======
    ("凯斯西储大学", "Case Western Reserve University", 169, 51, 90, 4.5, None, "旧制90→新制4.5"),
    ("杜兰大学", "Tulane University", 256, 63, 95, 5.0, None, "旧制95→新制5.0"),
    ("维拉诺瓦大学", "Villanova University", 0, 55, None, None, None, "无官方最低；竞争者旧制100+/新制5.0+"),
    ("维克森林大学", "Wake Forest University", 0, 46, None, None, None, "无官方最低；竞争者旧制100+/新制5.0+"),
    ("威廉与玛丽学院", "William & Mary", 0, 41, 100, 5.0, None, "旧制100→新制5.0"),
    ("佩珀代因大学", "Pepperdine University", 0, 76, 80, 4.0, None, "旧制80→新制4.0。法学要求更高"),
    ("南卫理公会大学", "Southern Methodist University", 0, 76, 80, 4.0, None, "旧制80→新制4.0"),
    ("雪城大学", "Syracuse University", 252, 63, 80, 4.0, None, "旧制80→新制4.0。新闻学院旧制100/新制5.0+"),
    ("罗格斯大学", "Rutgers University", 0, 40, 79, 4.0, None, "旧制79→新制4.0。因学院而异"),
    ("克莱姆森大学", "Clemson University", 0, 70, 79, 4.0, None, "旧制79→新制4.0"),
    ("爱荷华州立大学", "Iowa State University", 0, 113, 71, 3.5, None, "旧制71→新制3.5"),
    ("印第安纳大学伯明顿", "Indiana University Bloomington", 0, 73, 79, 4.0, None, "旧制79→新制4.0。Jacobs音乐院要求更高"),
    ("明尼苏达大学双城", "University of Minnesota Twin Cities", 134, 53, 79, 4.0, None, "旧制79→新制4.0"),
    ("堪萨斯大学", "University of Kansas", 0, 152, 75, 4.0, None, "旧制75→新制4.0"),
    ("爱荷华大学", "University of Iowa", 0, 93, 78, 4.0, None, "旧制78→新制4.0"),
    ("俄克拉荷马大学", "University of Oklahoma", 0, 137, 70, 3.5, None, "旧制70→新制3.5"),
    ("阿拉巴马大学", "University of Alabama", 0, 170, 71, 3.5, None, "旧制71→新制3.5"),
    ("奥本大学", "Auburn University", 0, 93, 79, 4.0, None, "旧制79→新制4.0"),
    ("田纳西大学", "University of Tennessee", 0, 105, 78, 4.0, None, "旧制78→新制4.0"),
    ("南卡罗来纳大学", "University of South Carolina", 0, 113, 77, 4.0, None, "旧制77→新制4.0"),
    ("犹他大学", "University of Utah", 0, 115, 75, 4.0, None, "旧制75→新制4.0"),
    ("亚利桑那大学", "University of Arizona", 0, 120, 75, 4.0, None, "旧制75→新制4.0"),
    ("亚利桑那州立大学", "Arizona State University", 176, 105, 75, 4.0, None, "旧制75→新制4.0"),
    ("科罗拉多大学波德", "University of Colorado Boulder", 0, 100, 79, 4.0, None, "旧制79→新制4.0。工程要求更高"),
    ("俄勒冈大学", "University of Oregon", 0, 105, 75, 4.0, None, "旧制75→新制4.0"),
    ("丹佛大学", "University of Denver", 0, 115, 80, 4.0, None, "旧制80→新制4.0"),
    ("美利坚大学", "American University", 0, 132, 79, 4.0, None, "旧制79→新制4.0"),
    ("贝勒大学", "Baylor University", 0, 120, 79, 4.0, None, "旧制79→新制4.0"),
    ("马凯特大学", "Marquette University", 0, 120, 78, 4.0, None, "旧制78→新制4.0"),
    ("洛约拉芝加哥大学", "Loyola University Chicago", 0, 132, 79, 4.0, None, "旧制79→新制4.0"),
    ("德保罗大学", "DePaul University", 0, 137, 80, 4.0, None, "旧制80→新制4.0"),
    ("旧金山大学", "University of San Francisco", 0, 171, 80, 4.0, None, "旧制80→新制4.0"),
    ("乔治华盛顿大学", "George Washington University", 0, 73, 80, 4.0, None, "旧制80→新制4.0"),
    ("康涅狄格大学", "University of Connecticut", 0, 58, 79, 4.0, None, "旧制79→新制4.0"),
    ("马萨诸塞大学阿默斯特", "University of Massachusetts Amherst", 0, 67, 80, 4.0, None, "旧制80→新制4.0"),
    ("弗吉尼亚理工", "Virginia Tech", 0, 47, 80, 4.0, None, "旧制80→新制4.0。工程建议更高"),
    ("伦斯勒理工学院", "Rensselaer Polytechnic Institute", 0, 47, 88, 4.5, None, "旧制88→新制4.5"),
    ("史蒂文斯理工学院", "Stevens Institute of Technology", 0, 83, 80, 4.0, None, "旧制80→新制4.0"),
    ("德雷塞尔大学", "Drexel University", 0, 97, 79, 4.0, None, "旧制79→新制4.0"),
    ("天普大学", "Temple University", 0, 105, 79, 4.0, None, "旧制79→新制4.0"),
    ("霍夫斯特拉大学", "Hofstra University", 0, 171, 79, 4.0, None, "旧制79→新制4.0"),
    ("迈阿密大学", "University of Miami", 0, 53, 80, 4.0, None, "旧制80→新制4.0。竞争者旧制100+/新制5.0+"),
    ("特拉华大学", "University of Delaware", 0, 83, 90, 4.5, None, "旧制90→新制4.5"),
    ("昆尼皮亚克大学", "Quinnipiac University", 0, 140, 79, 4.0, None, "旧制79→新制4.0"),
    ("太平洋大学(美国)", "University of the Pacific", 0, 171, 80, 4.0, None, "旧制80→新制4.0"),
    ("冈萨加大学", "Gonzaga University", 0, 132, 78, 4.0, None, "旧制78→新制4.0"),
    ("西雅图大学", "Seattle University", 0, 200, 78, 4.0, None, "旧制78→新制4.0"),
    ("波特兰大学", "University of Portland", 0, 200, 70, 3.5, None, "旧制70→新制3.5"),
    ("代顿大学", "University of Dayton", 0, 137, 79, 4.0, None, "旧制79→新制4.0"),
    ("塔尔萨大学", "University of Tulsa", 0, 171, 61, 3.5, None, "旧制61→新制3.5"),

    # ====== 艺术/特殊院校 ======
    ("朱莉亚学院", "Juilliard School", 0, 0, 79, 4.0, None, "本科旧制79→新制4.0；研究生旧制100→新制5.0。因项目而异"),
    ("罗德岛设计学院", "Rhode Island School of Design", 0, 0, 93, 4.5, None, "旧制93→新制4.5。作品集最重要"),
    ("帕森斯设计学院", "Parsons School of Design", 0, 0, 92, 4.5, None, "旧制92→新制4.5。作品集最重要"),
    ("普瑞特艺术学院", "Pratt Institute", 0, 0, 79, 4.0, None, "旧制79→新制4.0"),
    ("纽约视觉艺术学院", "School of Visual Arts", 0, 0, 79, 4.0, None, "旧制79→新制4.0。部分项目需旧制100/新制5.0"),
    ("芝加哥艺术学院", "School of the Art Institute of Chicago", 0, 0, 82, 4.0, None, "旧制82→新制4.0。部分项目需旧制100/新制5.0"),
    ("加州艺术学院", "California Institute of the Arts", 0, 0, 80, 4.0, None, "旧制80→新制4.0。作品集最重要"),
    ("伯克利音乐学院", "Berklee College of Music", 0, 0, 72, 4.0, None, "旧制72→新制4.0。研究生旧制91-100+/新制4.5-5.0+"),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 获取已有大学名
    cur.execute("SELECT id, university FROM us_admission_info")
    existing = {row[1]: row[0] for row in cur.fetchall()}
    print(f"数据库已有 {len(existing)} 所学校")

    # A. 修复已有学校
    fixed = 0
    for name, (total, sections, notes) in FIX_EXISTING.items():
        if name in existing:
            sections_json = json.dumps(sections, ensure_ascii=False) if sections else None
            cur.execute(
                "UPDATE us_admission_info SET toefl_new_total=?, toefl_new_sections=?, toefl_notes=? WHERE university=?",
                (total, sections_json, notes, name)
            )
            fixed += 1
            print(f"  ✓ 修复: {name} → 新托福={total}")
        else:
            print(f"  ? 未找到: {name}")

    # B. 新增学校
    inserted = 0
    skipped = 0
    for item in NEW_SCHOOLS:
        cn_name, en_name, qs, usn, toefl_old, toefl_new, sections, notes = item
        if cn_name in existing:
            # 已存在 → 更新
            sections_json = json.dumps(sections, ensure_ascii=False) if sections else None
            cur.execute(
                "UPDATE us_admission_info SET toefl_new_total=?, toefl_new_sections=?, toefl_notes=? WHERE university=?",
                (toefl_new, sections_json, notes, cn_name)
            )
            updated_label = "updated"
            skipped += 1
            print(f"  ↻ 已存在更新: {cn_name} → {toefl_new}")
        else:
            cur.execute(
                """INSERT INTO us_admission_info 
                   (university, university_en, qs_rank, us_news_rank, toefl_min, toefl_new_total, toefl_new_sections, toefl_notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (cn_name, en_name, qs, usn, toefl_old, toefl_new,
                 json.dumps(sections, ensure_ascii=False) if sections else None, notes)
            )
            inserted += 1
            print(f"  + 新增: {cn_name} → 新托福{toefl_new}")

    conn.commit()

    # 统计
    cur.execute("SELECT COUNT(*) FROM us_admission_info")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM us_admission_info WHERE toefl_new_total IS NOT NULL")
    with_new = cur.fetchone()[0]

    conn.close()

    print(f"\n完成！修复 {fixed} 所，新增 {inserted} 所，更新已有 {skipped} 所")
    print(f"数据库总计 {total} 所学校，其中 {with_new} 所有新托福数据")


if __name__ == "__main__":
    main()
