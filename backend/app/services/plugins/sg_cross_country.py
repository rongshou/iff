"""
新加坡联合推荐插件。
移植自 advisor/scripts/plugins/sg_cross_country.py
"""

SG_PRIVATE_WITH_MASTER = {
    "楷博高等教育新加坡校区",
    "楷博高等教育学院",
    "PSB学院",
    "科廷大学新加坡校区",
    "詹姆斯库克大学新加坡校区",
    "管理学院",
    "新加坡管理学院",
    "莱佛士音乐学院",
    "莱佛士高等教育学院",
    "东亚管理学院",
}


def apply(conn, scored, profile, bg, rule, context):
    """新加坡专属逻辑"""
    countries = context.get("countries", [])
    if "新加坡" not in countries:
        return scored

    tier = bg.get("school_tier", 5)
    gpa4 = bg.get("gpa4")
    study_level = profile.get("study_level")
    is_high_bg = (tier <= 2) or (tier == 3 and gpa4 and gpa4 >= 3.0)

    for s in scored:
        name = s.get("name", "")
        qs = s.get("qs_rank") or 999
        sg_name = (
            "新加坡" in s.get("country", "")
            or "新加坡" in s.get("country_name", "")
            or "SG" == s.get("country", "")
        )
        hk_name = (
            "香港" in s.get("country", "")
            or "香港" in s.get("country_name", "")
            or "HK" == s.get("country", "")
        )
        uk_name = "英国" in s.get("country", "") or "UK" == s.get("country", "")

        if sg_name:
            if "新加坡国立" in name or "南洋理工" in name:
                if is_high_bg:
                    s["category"] = "稳妥"
                else:
                    s["category"] = "排除"
            elif "新加坡管理" in name or "SMU" in name or "科技设计" in name:
                s["category"] = "稳妥"
            else:
                if is_high_bg:
                    s["category"] = "排除"
                elif study_level == "硕士" and name not in SG_PRIVATE_WITH_MASTER:
                    s["category"] = "排除"
                else:
                    s["category"] = "保底"
        elif is_high_bg and (hk_name or uk_name):
            if qs <= 50:
                s["category"] = "冲刺"
            elif qs <= 100:
                s["category"] = "稳妥"
            else:
                s["category"] = "保底"

    return scored
