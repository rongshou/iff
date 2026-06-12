"""
天权项目数据质量修复脚本 v2
第二波：ISC/预科合并、排名补充、通用名称清理
"""
import sqlite3

DB_PATH = "/home/admin/.openclaw/workspace-study-abroad/study-abroad-advisor/data/advisor.db"

def merge_pathway_schools(db):
    """
    合并 ISC/预科/学习中心/pathway 学校到主校
    """
    merges = [
        # UK ISC 学习中心
        ("利兹大学国际学习中心", "利兹大学"),
        ("兰卡斯特大学国际学习中心", "兰卡斯特大学"),
        ("卡迪夫国际学习中心", "卡迪夫大学"),
        ("阿伯丁大学国际学习中心", "阿伯丁大学"),
        ("萨里大学国际学习中心", "萨里大学"),
        ("伦敦大学皇家霍洛威学院国际学习中心", "伦敦大学皇家霍洛威学院"),
        ("思克莱德国际学习中心", "思克莱德大学"),
        ("玛丽皇后大学预科中心", "伦敦大学玛丽皇后学院"),

        # INTO 项目
        ("INTO 纽卡斯尔大学", "纽卡斯尔大学"),
        ("INTO 贝尔法斯特女王大学", "贝尔法斯特女王大学"),
        ("INTO 东英吉利大学", "东英吉利大学"),
        ("INTO 东安格利亚大学", "东英吉利大学"),

        # 预科
        ("南安普顿大学国际预科中心", "南安普顿大学"),
        ("伯明翰大学国际预科学院", "伯明翰大学"),
        ("伦敦预科中心", "伦敦大学"),
        ("Oncampus雷丁大学预科", "雷丁大学"),
        ("朴茨茅斯大学预科", "朴茨茅斯大学"),
        ("赫特福德大学预科", "赫特福德大学"),
        ("桑德兰大学预科", "桑德兰大学"),
        ("斯特灵大学预科中心", "斯特灵大学"),
        ("普利茅斯大学预科", "普利茅斯大学"),
        ("西英格兰大学国际预科", "西英格兰大学"),
        ("斯特灵大学 INTO预科中心", "斯特灵大学"),
        ("伦敦大学金匠学院预科", "伦敦大学金匠学院"),
        ("拉夫堡大学预科-CEG", "拉夫堡大学"),

        # 澳大利亚预科/学院
        ("阿德莱德预科学院", "阿德莱德大学"),
        ("迪肯大学预科学院", "迪肯大学"),
        ("科廷大学预科学院", "科廷大学"),
        ("昆士兰大学预科", "昆士兰大学"),
        ("塔斯马尼亚大学国际预科学院", "塔斯马尼亚大学"),
        ("国立大学预科", "澳大利亚国立大学"),
        ("国立大学预科学院", "澳大利亚国立大学"),
        ("泰勒学院奥克兰预科", "奥克兰大学"),  # 其实是奥克兰大学的预科
        ("泰勒学院悉尼大学预科", "悉尼大学"),  # already done

        # 其他
        ("都柏林大学国际学习中心", "都柏林大学"),
        ("多柏林城市大学预科项目", "都柏林城市大学"),
        ("都柏林国际预科学院", "都柏林大学"),
        ("南加州大学预科", "南加州大学"),
        ("多伦多大学国际预科课程", "多伦多大学"),
        ("奥克兰大学预科", "奥克兰大学"),
        ("坎特伯雷大学预科", "坎特伯雷大学"),
        ("奥克兰理工大学预科", "奥克兰理工大学"),
    ]

    fixed = 0
    for pathway_name, main_name in merges:
        pw = db.execute("SELECT id FROM universities WHERE name = ?", (pathway_name,)).fetchone()
        if not pw:
            continue
        main = db.execute("SELECT id FROM universities WHERE name = ?", (main_name,)).fetchone()
        if not main:
            continue

        db.execute(
            "UPDATE cases SET university_id = ?, university = ? WHERE university_id = ?",
            (main["id"], main_name, pw["id"])
        )
        cnt = db.execute("SELECT changes()").fetchone()["changes()"]
        if cnt > 0:
            print(f"  [合并] {pathway_name} → {main_name} ({cnt} cases)")
            fixed += 1
    db.commit()
    return fixed


def add_missing_rankings(db):
    """
    补充热门学校缺失的 QS 和 USNews 排名
    """
    ranking_fixes = [
        # 英国
        ("伦敦大学", "UK", 0, 0, None),  # 联邦制大学，不单独排名
        ("创意艺术大学", "UK", 0, 0, None),  # 艺术类
        ("伦敦艺术大学", "UK", 0, 0, None),  # 艺术类，不参与综合排名
        ("格拉斯哥艺术学院", "UK", 0, 0, None),  # 艺术类
        ("伦敦大学金匠学院", "UK", 396, 0, None),

        # 美国 (USNews + QS)
        ("加州大学", "US", 0, 0, None),  # 泛指，不具体
        ("麻省大学阿姆赫斯特校区", "US", 245, 67, None),
        ("得克萨斯大学奥斯汀分校", "US", 68, 30, None),  # QS 2025
        ("约翰斯·霍普金斯大学", "US", 28, 6, None),
        ("加州大学美熹德分校", "US", 0, 58, None),
        ("福德汉姆大学", "US", 0, 91, None),
        ("纽约州立大学水牛城分校", "US", 0, 76, None),
        ("萨凡纳艺术与设计学院", "US", 0, 0, None),  # 艺术类
        ("视觉艺术学院", "US", 0, 0, None),  # 艺术类

        # 澳大利亚
        ("詹姆斯库克大学", "AU", 415, 0, None),

        # 加拿大
        ("英属哥伦比亚大学-奥克那根校区", "CA", 0, 0, "英属哥伦比亚大学"),

        # 新加坡
        ("科廷大学新加坡校区", "SG", 0, 0, "科廷大学"),
        ("詹姆斯库克大学新加坡校区", "SG", 0, 0, "詹姆斯库克大学"),  # already merged

        # 中国香港
        ("香港珠海学院", "HK", 0, 0, None),
        ("香港恒生大学", "HK", 0, 0, None),
        ("香港树仁大学", "HK", 0, 0, None),
    ]

    # First, do merges for campus variations
    campus_merges = {
        "英属哥伦比亚大学-奥克那根校区": "英属哥伦比亚大学",
        "科廷大学新加坡校区": "科廷大学",
        "麻省大学阿姆赫斯特校区": "麻省大学",
    }

    merge_fixed = 0
    for campus, main_name in campus_merges.items():
        c = db.execute("SELECT id FROM universities WHERE name = ?", (campus,)).fetchone()
        m = db.execute("SELECT id FROM universities WHERE name = ?", (main_name,)).fetchone()
        if c and m:
            db.execute(
                "UPDATE cases SET university_id = ?, university = ? WHERE university_id = ?",
                (m["id"], main_name, c["id"])
            )
            cnt = db.execute("SELECT changes()").fetchone()["changes()"]
            if cnt > 0:
                print(f"  [校区合并] {campus} → {main_name} ({cnt} cases)")
                merge_fixed += 1

    # Then add rankings
    rank_fixed = 0
    for name, country, qs, usnews, merge_to in ranking_fixes:
        if merge_to:
            continue  # handled above
        u = db.execute("SELECT id, qs_rank, usnews_rank FROM universities WHERE name = ?", (name,)).fetchone()
        if not u:
            continue
        updates = []
        params = []
        if qs and u["qs_rank"] == 0:
            updates.append("qs_rank = ?")
            params.append(qs)
        if usnews and u["usnews_rank"] == 0:
            updates.append("usnews_rank = ?")
            params.append(usnews)
        if updates:
            params.append(u["id"])
            db.execute(f"UPDATE universities SET {', '.join(updates)} WHERE id = ?", params)
            print(f"  [排名] {name} → QS={qs}, USNews={usnews}")
            rank_fixed += 1

    db.commit()
    return merge_fixed + rank_fixed


def fix_GPA_outliers(db):
    """
    检查并标记异常 GPA 案例
    """
    # Find cases with obviously wrong GPA formats
    outliers = db.execute("""
        SELECT COUNT(*) as cnt FROM cases
        WHERE gpa_score IS NOT NULL
          AND gpa_format = '英制百分制'
    """).fetchone()
    print(f"  [GPA] 英制百分制案例: {outliers['cnt']}")

    # Check Chinese Gaokao cases (should be excluded from standard GPA calc)
    gaokao = db.execute("""
        SELECT COUNT(*) as cnt FROM cases
        WHERE gpa_format = '中国高考'
    """).fetchone()
    print(f"  [GPA] 高考分数案例: {gaokao['cnt']}")

    # These are already excluded in case_matcher.py's _filter_and_score


def clean_null_names(db):
    """
    清理无意义/空名称的学校
    """
    null_name = db.execute("SELECT COUNT(*) FROM universities WHERE name IS NULL OR name = ''").fetchone()
    print(f"  [名称] 空名称学校: {null_name[0]}")

    null_case_university = db.execute("""
        SELECT COUNT(*) FROM cases
        WHERE university IS NULL OR university = ''
    """).fetchone()
    print(f"  [名称] cases 中空学校名: {null_case_university[0]}")


def main():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")

    print("=" * 60)
    print("天权数据质量修复 v2")
    print("=" * 60)

    print("\n[1/4] 合并 ISC/预科/学习中心到主校...")
    n1 = merge_pathway_schools(db)
    print(f"  → 合并了 {n1} 对 pathway/主校")

    print("\n[2/4] 补充缺失的 QS/USNews 排名...")
    n2 = add_missing_rankings(db)
    print(f"  → 修复了 {n2} 处排名/合并")

    print("\n[3/4] 检查 GPA 数据异常...")
    fix_GPA_outliers(db)

    print("\n[4/4] 清理空名称...")
    clean_null_names(db)

    # Stats
    total = db.execute("SELECT COUNT(*) FROM universities").fetchone()[0]
    ranked = db.execute(
        "SELECT COUNT(*) FROM universities WHERE (qs_rank > 0 AND qs_rank < 1000) OR (usnews_rank > 0)"
    ).fetchone()[0]
    print(f"\n最终: {total} 学校, {ranked} 有排名")
    db.close()

if __name__ == "__main__":
    main()
