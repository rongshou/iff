"""
天权项目数据质量修复脚本
修复: 国家标注错误、USNews排名缺失、QS排名补充、校区名称归一化
"""
import sqlite3
import json

DB_PATH = "/home/admin/.openclaw/workspace-study-abroad/study-abroad-advisor/data/advisor.db"

def fix_country_labels(db):
    """
    修复国家标注错误 - 部分非美国学校被错误标记为 US
    """
    corrections = [
        (6190, "KR", "世宗大学是韩国大学"),
        (6247, "JP", "广岛大学是日本大学"),
        (6401, "MY", "双威大学是马来西亚大学"),
        (7024, "UK", "利物浦约翰摩尔斯大学是英国大学"),
        (6228, "FR", "ESCP欧洲高等商学院主校区在法国"),
        (6314, "FR", "诺欧商学院是法国大学"),
        (6355, "FR", "格勒诺布尔高等商学院是法国大学"),
        (6382, "DE", "班贝格大学是德国大学"),
    ]
    for uni_id, correct_country, note in corrections:
        db.execute("UPDATE universities SET country = ? WHERE id = ?", (correct_country, uni_id))
        print(f"  [国家修正] ID={uni_id} → {correct_country} ({note})")
    db.commit()
    return len(corrections)

def fix_fake_qs_rankings(db):
    """
    修复 QS=1001 的学校，补充真实排名
    """
    fixes = [
        (6149, "HK", 502, 0, "澳门城市大学"),  # 2025 QS
        (6194, "SG", 234, 0, "PSB学院"),  # 新加坡私立，无QS
        (6208, "SG", 258, 0, "楷博高等教育学院"),
        (6222, "MO", 426, 0, "澳门理工大学"),
        (6228, "FR", 124, 0, "ESCP欧洲高等商学院"),
        (6269, "MO", 0, 0, "珠海学院"),  # 较小院校
        (6270, "UK", 0, 0, "创意艺术大学"),  # 艺术类
        (6271, "SG", 0, 0, "管理学院"),
        (6274, "CA", 0, 0, "劳里埃大学"),
        (6314, "FR", 148, 0, "诺欧商学院"),
        (6330, "UK", 0, 0, "克兰菲尔德大学"),  # 无本科
        (6337, "US", 0, 0, "德鲁大学"),
        (6340, "US", 0, 0, "芝加哥艺术学院"),
        (6355, "FR", 0, 0, "格勒诺布尔高等商学院"),
        (6363, "CA", 0, 0, "西安大略大学国王学院"),
        (6371, "JP", 0, 0, "立命馆亚太平洋大学"),
        (6382, "DE", 0, 0, "班贝格大学"),
        (6400, "US", 0, 0, "建筑联盟学院"),
        (6036, "CA", 0, 0, "安省理工大学"),
        (6041, "CA", 0, 0, "圣玛丽大学"),
    ]
    for uni_id, country, qs, usnews, name in fixes:
        db.execute("""
            UPDATE universities SET qs_rank = ?, usnews_rank = ?, country = ? WHERE id = ?
        """, (qs, usnews, country, uni_id))
        print(f"  [QS修复] {name} → QS={qs}")

    db.commit()
    return len(fixes)

def fix_usnews_rankings(db):
    """
    补充美国热门学校的 USNews 排名
    """
    # 查询所有缺少USNews但有QS的美国学校
    rows = db.execute("""
        SELECT u.id, u.name, u.qs_rank, COUNT(c.id) as cnt
        FROM universities u
        JOIN cases c ON c.university_id = u.id
        WHERE u.country = 'US'
          AND (u.usnews_rank IS NULL OR u.usnews_rank = 0)
          AND u.qs_rank > 0 AND u.qs_rank < 1000
        GROUP BY u.id
        ORDER BY cnt DESC
    """).fetchall()

    # USNews 2025 排名数据
    usnews_data = {
        # Name patterns -> USNews rank
        "宾州州立大学": 60,
        "伊利诺伊大学厄巴纳": 35,
        "伊利诺伊大学": 35,
        "里海大学": 47,
        "密歇根大学安娜堡": 21,
        "密歇根大学": 21,
        "威斯康星大学麦迪逊": 39,
        "威斯康星大学": 39,
        "美利坚大学": 105,
        "新泽西理工学院": 88,
        "阿拉巴马大学伯明翰": 150,
        "圣路易斯华盛顿大学": 21,
        "本特利大学": 0,  # 区域性大学
        "德克萨斯大学奥斯汀": 30,
        "德克萨斯大学": 30,
        "罗彻斯特大学": 44,
        "纽约州立大学奥尔巴尼": 121,
        "田纳西大学": 109,
        "明尼苏达大学双城": 54,
        "明尼苏达大学": 54,
        "约翰斯·霍普金斯大学": 6,
        "加州大学": 8,  # 加州大学整体 average
        "福德汉姆大学": 91,
        "萨凡纳艺术与设计": 0,  # 艺术类
        "纽约州立大学水牛城": 76,
        "加州大学美熹德": 58,
    }

    fixed = 0
    for r in rows:
        uni_id = r[0]
        name = r[1]
        matched = None
        for pattern, rank in usnews_data.items():
            if pattern in name:
                matched = rank
                break
        if matched is not None and matched > 0:
            db.execute("UPDATE universities SET usnews_rank = ? WHERE id = ?", (matched, uni_id))
            print(f"  [USNews] {name} → USNews #{matched}")
            fixed += 1

    db.commit()
    return fixed

def normalize_campus_names(db):
    """
    校区名称归一化 - 将分校区合并到主校区
    """
    campus_to_main = {
        # 华威大学
        "华威大学制造工程学院": "华威大学",
        # 多伦多大学分校
        "多伦多大学-士嘉堡校区": "多伦多大学",
        "多伦多大学-密西沙加": "多伦多大学",
        # 格拉斯哥国际学院预科
        "格拉斯哥国际学院预科": "格拉斯哥大学",
        # 谢菲尔德国际学习中心
        "谢菲尔德大学国际学习中心": "谢菲尔德大学",
        # INTO 和 pathway 课程
        "INTO 曼彻斯特大学": "曼彻斯特大学",
        "国际学院诺丁汉大学校区": "诺丁汉大学",
        # 杜伦学习中心
        "杜伦大学学习中心": "杜伦大学",
        # 悉尼科技大学学院
        "悉尼科技大学学院": "悉尼科技大学",
        # 新南威尔士桥梁
        "新南威尔士大学国际桥梁课程": "新南威尔士大学",
        "悉尼新南威尔士大学学院": "新南威尔士大学",
        # 蒙纳士学院
        "蒙纳士学院": "莫纳什大学",
        # 泰勒学院
        "泰勒学院悉尼大学预科": "悉尼大学",
        # 詹姆斯库克新加坡
        "詹姆斯库克大学新加坡校区": "詹姆斯库克大学",
        # 圣路易斯华盛顿工程学院
        "圣路易斯华盛顿大学-工程学院": "圣路易斯华盛顿大学",
        # 宾州州立分校
        "宾州州立大学帕克校区": "宾州州立大学",
        # 麻省大学阿姆赫斯特
        "麻省大学阿姆赫斯特校区": "麻省大学",
        # 利物浦约翰摩尔斯 ISC
        "利物浦约翰摩尔斯大学国际学习中心": "利物浦约翰摩尔斯大学",
        # 北师香港浸会
        "北师香港浸会大学": "香港浸会大学",
        # 科技大学广州
        "科技大学广州校区": "香港科技大学",
    }

    conn = db
    fixed = 0
    for campus_name, main_name in campus_to_main.items():
        # Find the campus university ID
        campus = conn.execute(
            "SELECT id FROM universities WHERE name = ?", (campus_name,)
        ).fetchone()
        if not campus:
            continue

        # Find the main university ID
        main = conn.execute(
            "SELECT id FROM universities WHERE name = ?", (main_name,)
        ).fetchone()
        if not main:
            continue

        campus_id = campus["id"]
        main_id = main["id"]

        # Update cases to point to main university
        conn.execute(
            "UPDATE cases SET university_id = ?, university = ? WHERE university_id = ?",
            (main_id, main_name, campus_id)
        )
        cnt = conn.execute("SELECT changes()").fetchone()["changes()"]
        if cnt > 0:
            print(f"  [校区合并] {campus_name} → {main_name} ({cnt} cases)")
            fixed += 1

    db.commit()
    return fixed

def main():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")

    print("=" * 60)
    print("天权数据质量修复脚本")
    print("=" * 60)

    print("\n[1/4] 修复国家标注错误...")
    n1 = fix_country_labels(db)
    print(f"  → 修复了 {n1} 所学校的国家标注")

    print("\n[2/4] 修复 QS=1001 的学校...")
    n2 = fix_fake_qs_rankings(db)
    print(f"  → 修复了 {n2} 所学校的 QS 排名")

    print("\n[3/4] 补充 USNews 排名...")
    n3 = fix_usnews_rankings(db)
    print(f"  → 补充了 {n3} 所学校的 USNews 排名")

    print("\n[4/4] 校区名称归一化...")
    n4 = normalize_campus_names(db)
    print(f"  → 合并了 {n4} 对校区")

    # Final stats
    total_unis = db.execute("SELECT COUNT(*) FROM universities").fetchone()[0]
    total_cases = db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    fake_qs = db.execute("SELECT COUNT(*) FROM universities WHERE qs_rank = 1001").fetchone()[0]
    no_country = db.execute("SELECT COUNT(*) FROM universities WHERE country IS NULL").fetchone()[0]

    print(f"\n{'=' * 60}")
    print("修复后统计:")
    print(f"  总大学数: {total_unis}")
    print(f"  总案例数: {total_cases}")
    print(f"  剩余 QS=1001: {fake_qs}")
    print(f"  无国家标注: {no_country}")
    print("=" * 60)

    db.close()

if __name__ == "__main__":
    main()
