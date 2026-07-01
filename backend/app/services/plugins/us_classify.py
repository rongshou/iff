"""
美国学校 USNews 分类插件。
美国学校用 USNews 排名做分类（QS 对美校不准确：BU QS=1001 但 USNews=39）。
移植自 advisor/scripts/plugins/us_classify.py
"""


def _usnews_reach(tier: int, gpa4: float | None) -> int:
    """根据背景返回冲刺校 USNews 排名阈值（简化版）"""
    if tier == 1 and gpa4 and gpa4 >= 3.5:
        return 15
    elif tier <= 2 and gpa4 and gpa4 >= 3.0:
        return 25
    elif tier <= 3 and gpa4 and gpa4 >= 2.5:
        return 40
    else:
        return 60


def _usnews_match(tier: int, gpa4: float | None) -> int:
    """根据背景返回匹配校 USNews 排名阈值"""
    if tier == 1 and gpa4 and gpa4 >= 3.5:
        return 30
    elif tier <= 2 and gpa4 and gpa4 >= 3.0:
        return 60
    elif tier <= 3 and gpa4 and gpa4 >= 2.5:
        return 100
    else:
        return 150


def apply(conn, scored, profile, bg, rule, context):
    """美国学校 USNews 重分类"""
    countries = context.get("countries", [])
    if "美国" not in countries:
        return scored

    tier = bg.get("school_tier", 5)
    gpa4 = bg.get("gpa4")

    usnews_reach = _usnews_reach(tier, gpa4)
    usnews_match_val = _usnews_match(tier, gpa4)

    for s in scored:
        if s.get("lac_rank"):
            continue
        usn = s.get("usnews_rank") or 999
        if usn <= usnews_reach:
            s["category"] = "冲刺"
        elif usn <= usnews_match_val:
            s["category"] = "稳妥"
        else:
            s["category"] = "保底"

    # 美国顶尖校 USNews≤30 一律算冲刺
    for s in scored:
        if s.get("country") in ("美国", "US") and s.get("usnews_rank") and s["usnews_rank"] <= 30:
            if s["category"] != "冲刺":
                s["category"] = "冲刺"

    return scored
