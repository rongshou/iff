#!/usr/bin/env python3
"""
导入美国大学新托福(2026年1-6分制)要求到 advisor.db
数据来源：各校官网 + 公开资料汇总（2025-2026申请季）

旧托福(0-120) → 新托福(1-6) 对照：
  114-120 → 6.0 | 107-113 → 5.5 | 95-106 → 5.0
  86-94 → 4.5 | 72-85 → 4.0 | 60-71 → 3.5
"""
import sqlite3
import json

DB_PATH = "/home/admin/tianquan/backend/data/advisor.db"

# 大学名 → 新托福数据
# toefl_new_total: 新托福最低总分 (1-6)
# toefl_new_sections: 单科要求 dict (1-6 scale)
# toefl_notes: 补充说明
TOEFL_DATA = {
    # ====== 常春藤 + 顶级私立 ======
    "哈佛大学": {
        "total": None,  # 无官方最低，但竞争极强
        "sections": None,
        "notes": "无官方最低分；竞争申请者旧制110+/新制5.5+。GSAS最低80(各科22+)；商学院最低109(口语/写作26+)；教育学院最低104(各科26+)；工程最低90(建议100+)"
    },
    "普林斯顿大学": {
        "total": None,
        "sections": None,
        "notes": "无官方最低分；竞争申请者旧制115+/新制5.5+。建议口语27+"
    },
    "耶鲁大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制最低100(竞争约110+)。博士项目要求口语26+(新制5.0+)；竞争者听说各28+(新制5.5+)"
    },
    "哥伦比亚大学": {
        "total": 5.5,
        "sections": None,
        "notes": "旧制105→新制5.5。新闻学院旧制114+/新制5.5+；工程旧制99+/新制5.0+。不接受MyBest Scores"
    },
    "宾夕法尼亚大学": {
        "total": 5.0,
        "sections": {"reading": 5.0, "listening": 5.0, "writing": 5.0, "speaking": 4.5},
        "notes": "旧制最低100。建议R/L/W 25+(新制5.0+)，S 24+(新制4.5+)。Wharton竞争均分旧制112+/新制5.5+"
    },
    "康奈尔大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制最低100→新制5.0(建议5.5+)。不同学院要求有差异"
    },
    "布朗大学": {
        "total": 5.5,
        "sections": None,
        "notes": "旧制105→新制5.5。从之前100提高"
    },
    "达特茅斯学院": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0"
    },
    "斯坦福大学": {
        "total": 5.0,
        "sections": None,
        "notes": "工程旧制89→新制4.5；人文/商科/社科旧制100→新制5.0。建议各科25+(新制5.0+)。竞争者旧制110+/新制5.5+。部分项目不接受Home Edition"
    },
    "麻省理工学院": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制官方最低90→新制4.5；竞争者旧制100+/新制5.0+。录取均分旧制~115/新制6.0。研究生最低100(各科25+)。CS/商科建议旧制105+/新制5.5+。竞争者写作28+口语27+"
    },
    "加州理工学院": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0。各科25+(新制5.0+)"
    },
    "芝加哥大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100-104→新制5.0。人文各科5.0+；生物科学听力5.5+口语4.5+"
    },
    "杜克大学": {
        "total": 5.0,
        "sections": None,
        "notes": "本科旧制100→新制5.0(建议105+/5.5+)；研究生旧制90→新制4.5"
    },
    "西北大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0。各科22+(新制4.5+)。媒体项目需旧制105+/新制5.5+"
    },
    "约翰霍普金斯大学": {
        "total": 5.0,
        "sections": {"reading": 5.0, "listening": 5.0, "writing": 4.5, "speaking": 5.0},
        "notes": "旧制100→新制5.0-5.5。R/L 26+(新制5.0+)，W 22+(新制4.5+)，S 25+(新制5.0+)"
    },

    # ====== 顶级私立 ======
    "范德堡大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0"
    },
    "莱斯大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0"
    },
    "圣母大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0"
    },
    "乔治城大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0"
    },
    "埃默里大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0"
    },
    "纽约大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0，各科5.0+。商科/媒体项目需5.5+"
    },
    "南加州大学": {
        "total": 5.5,
        "sections": None,
        "notes": "旧制100-105→新制5.0-5.5。各科20+(旧制)/4.0+(新制)"
    },
    "卡耐基梅隆大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制102→新制5.0。各科25+(新制5.0+)"
    },
    "塔夫茨大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0"
    },
    "波士顿大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制90-100→新制5.0。各科20+(旧制)"
    },
    "罗切斯特大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0"
    },
    "华盛顿大学圣路易斯": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制90-100→新制5.0"
    },

    # ====== 顶级公立 ======
    "加州大学伯克利分校": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制最低80(本科)/90(研究生)→新制4.0-4.5；竞争者旧制100+/新制5.0+。工程/CS建议旧制105+/新制5.5+；Haas商科建议旧制110+/新制5.5+。部分系口语22+"
    },
    "加州大学洛杉矶分校": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0。各科24+(旧制)/5.0(新制)。近期提高了要求"
    },
    "加州大学圣地亚哥分校": {
        "total": 4.0,
        "sections": None,
        "notes": "旧制83→新制4.0"
    },
    "密歇根大学安娜堡分校": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0-6.0。各科5.0+(新制)。L/R 23+(旧制)，S/W 21+(旧制)"
    },
    "北卡罗来纳大学教堂山": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0"
    },
    "弗吉尼亚大学": {
        "total": 4.5,
        "sections": None,
        "notes": "旧制90→新制4.5。L/R 23+(旧制)，S/W 22+(旧制)"
    },
    "佐治亚理工学院": {
        "total": 4.5,
        "sections": None,
        "notes": "旧制90→新制4.5。各科19+(旧制)"
    },
    "德克萨斯大学奥斯汀分校": {
        "total": 4.0,
        "sections": None,
        "notes": "旧制79→新制4.0。因项目而异"
    },
    "伊利诺伊大学厄巴纳-香槟": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0。写作24+(旧制)/4.5+(新制)"
    },
    "威斯康星大学麦迪逊": {
        "total": 4.0,
        "sections": None,
        "notes": "旧制80→新制4.0"
    },
    "俄亥俄州立大学": {
        "total": 4.0,
        "sections": None,
        "notes": "旧制80→新制4.0"
    },
    "华盛顿大学西雅图分校": {
        "total": 4.0,
        "sections": None,
        "notes": "旧制76→新制3.5-4.0。因项目而异"
    },
    "普渡大学": {
        "total": 4.0,
        "sections": None,
        "notes": "旧制80→新制4.0。各科20+(旧制)"
    },
    "宾州州立大学": {
        "total": 4.0,
        "sections": None,
        "notes": "旧制80→新制4.0-4.5。University Park校区建议4.5+"
    },
    "马里兰大学帕克分校": {
        "total": 4.5,
        "sections": None,
        "notes": "旧制90→新制4.5"
    },
    "佛罗里达大学": {
        "total": 4.0,
        "sections": None,
        "notes": "旧制80→新制4.0"
    },
    "东北大学(美国)": {
        "total": 4.5,
        "sections": None,
        "notes": "旧制92→新制4.5"
    },
    "理海大学": {
        "total": 4.5,
        "sections": None,
        "notes": "旧制90→新制4.5"
    },
    "加州大学戴维斯分校": {
        "total": 4.0,
        "sections": None,
        "notes": "旧制80→新制4.0"
    },
    "加州大学欧文分校": {
        "total": 4.5,
        "sections": None,
        "notes": "旧制80→新制4.0-4.5"
    },
    "加州大学圣塔芭芭拉分校": {
        "total": 4.0,
        "sections": None,
        "notes": "旧制80→新制4.0"
    },
    "佐治亚大学": {
        "total": 4.0,
        "sections": None,
        "notes": "旧制80→新制4.0"
    },
    "匹兹堡大学": {
        "total": 5.0,
        "sections": None,
        "notes": "旧制100→新制5.0。建议各科4.0+(新制)"
    },
    "密歇根州立大学": {
        "total": 4.0,
        "sections": None,
        "notes": "旧制80→新制4.0。各科4.0+(新制)；口语3.5+(新制)"
    },
}


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 获取已有大学名
    cur.execute("SELECT id, university FROM us_admission_info")
    existing = {row["university"]: row["id"] for row in cur.fetchall()}
    print(f"数据库已有 {len(existing)} 所学校")

    updated = 0
    not_found = []

    for uni_name, data in TOEFL_DATA.items():
        if uni_name in existing:
            sections_json = json.dumps(data["sections"], ensure_ascii=False) if data["sections"] else None
            cur.execute(
                """UPDATE us_admission_info
                   SET toefl_new_total = ?, toefl_new_sections = ?, toefl_notes = ?
                   WHERE university = ?""",
                (data["total"], sections_json, data["notes"], uni_name)
            )
            updated += 1
            print(f"  ✓ 更新: {uni_name} → 新托福总分={data['total']}")
        else:
            not_found.append(uni_name)
            print(f"  ? 未找到: {uni_name}")

    conn.commit()
    conn.close()

    print(f"\n完成！更新了 {updated} 所学校")
    if not_found:
        print(f"\n以下 {len(not_found)} 所学校在数据库中未找到（需手动添加）:")
        for n in not_found:
            print(f"  - {n}")


if __name__ == "__main__":
    main()
