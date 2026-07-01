"""
香港学校按名称硬分类插件。
移植自 advisor/scripts/plugins/hk_tier_override.py
"""


def apply(conn, scored, profile, bg, rule, context):
    """香港按学校名硬分类"""
    countries = context.get("countries", [])
    if "中国香港" not in countries:
        return scored

    tier = bg.get("school_tier", 5)
    gpa4 = bg.get("gpa4")
    is_high_bg = (tier <= 2) or (tier == 3 and gpa4 and gpa4 >= 3.0)

    for s in scored:
        name = s.get("name", "")
        hk = (
            "香港" in s.get("country", "")
            or "香港" in s.get("country_name", "")
            or "HK" == s.get("country", "")
        )
        if not hk:
            continue

        # 港三
        if "香港大学" in name or "香港中文" in name or "香港科技" in name:
            if is_high_bg:
                s["category"] = "冲刺"
            else:
                s["category"] = "排除"
        # 城大、理大、浸会
        elif "香港城市" in name or "香港理工" in name or "香港浸会" in name:
            s["category"] = "冲刺" if not is_high_bg else "稳妥"
        # 教大、岭南
        elif "香港教育" in name or "岭南" in name:
            s["category"] = "稳妥" if not is_high_bg else "保底"
        # 都会、恒生、公开、珠海
        elif "都会" in name or "恒生" in name or "公开" in name or "珠海学院" in name:
            s["category"] = "保底"

    return scored
