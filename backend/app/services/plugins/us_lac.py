"""
美国文理学院 (LAC) 推荐插件。
仅面向高中背景申请本科的学生。
移植自 advisor/scripts/plugins/us_lac.py
"""


def apply(conn, scored, profile, bg, rule, context):
    """美国文理学院推荐"""
    countries = context.get("countries", [])
    if "美国" not in countries:
        return scored

    study_level = profile.get("study_level")

    # LAC 插件仅面向本科申请者（study_level == "本科" 暗示高中生背景）
    if study_level != "本科":
        return scored

    tier = bg.get("school_tier", 5)
    gpa4 = bg.get("gpa4")
    major = profile.get("target_major")

    try:
        rows = conn.execute("""
            SELECT l.name_cn, l.usnews_lac_rank, l.acceptance_rate,
                   u.accept_rate as uni_accept, u.gpa_requirement
            FROM lac_rankings l
            LEFT JOIN universities u ON u.name = l.name_cn AND u.country = 'US'
            ORDER BY l.usnews_lac_rank
        """).fetchall()

        for row in rows:
            lac_name = row[0]
            lac_rank = row[1]
            lac_accept = row[2]
            uni_accept = row[3] or ""
            lac_gpa_req = row[4] or ""

            # 文理学院分类
            if tier == 1 and gpa4 and gpa4 >= 3.5:
                if lac_rank <= 15:
                    lac_category = "冲刺"
                elif lac_rank <= 30:
                    lac_category = "稳妥"
                else:
                    lac_category = "保底"
            elif tier <= 2 and gpa4 and gpa4 >= 3.0:
                if lac_rank <= 20:
                    lac_category = "冲刺"
                elif lac_rank <= 35:
                    lac_category = "稳妥"
                else:
                    lac_category = "保底"
            else:
                if lac_rank <= 25:
                    lac_category = "冲刺"
                elif lac_rank <= 40:
                    lac_category = "稳妥"
                else:
                    lac_category = "保底"

            safe_major = major.replace("%", r"\%").replace("_", r"\_") if major else "%"
            lac_total_cases = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE admitted_university = ? AND major LIKE ? ESCAPE '\\' AND study_level = ?",
                (lac_name, f"%{safe_major}%" if major else "%", study_level)
            ).fetchone()[0]

            scored.append({
                "name": lac_name,
                "country": "美国",
                "qs_rank": None,
                "usnews_rank": None,
                "lac_rank": lac_rank,
                "case_count": lac_total_cases,
                "category": lac_category,
                "gpa_requirement": lac_gpa_req,
                "acceptance_score": None,
                "school_type": "文理学院",
                "reasons": [f"文理学院排名第{lac_rank}", "优质本科教育"],
            })
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("us_lac plugin error")

    return scored
