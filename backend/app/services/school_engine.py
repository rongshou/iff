"""
校引擎：整合国家规则、插件系统、规则引擎，增强推荐结果。

在 case_matcher 的 3D 评分基础上，应用国家特定的学校和分类规则。
"""

from typing import Any

from .country_rules import get_rule, get_merged_rule
from .plugin_runner import run_plugins
from .rule_engine import get_rule_for_background
from ..utils.gpa import normalize_gpa
from ..utils.tier import classify_school_tier


def enhance_with_rules(
    conn,
    match_result: dict,
    profile: dict,
    background: dict,
) -> dict:
    """对推荐结果应用国家规则和插件增强。

    参数:
        match_result: case_matcher 的输出
        profile: 用户画像
        background: 背景信息

    返回:
        增强后的推荐结果（在原结果上附加属性）
    """
    countries = profile.get("target_countries", [])
    rule = get_merged_rule(countries)

    context = {
        "countries": countries,
        "profile": profile,
        "rule": rule,
    }

    # 对每个国家的学校列表应用插件
    for country_result in match_result.get("by_country", []):
        country = country_result.get("country", "")
        country_rule = get_rule(country)

        # 将学校列表适配为插件需要的格式
        scored = []
        for school in country_result.get("schools", []):
            scored.append({
                "name": school.get("name", ""),
                "country": country,
                "qs_rank": school.get("qs_rank"),
                "usnews_rank": school.get("usnews_rank"),
                "category": _map_tianquan_to_advisor_chance(school.get("admission_chance", "")),
                "admission_score": school.get("admission_score"),
                "matched_cases": school.get("matched_cases"),
                "gpa_min": school.get("gpa_min"),
                "gpa_max": school.get("gpa_max"),
                "gpa_p50": school.get("gpa_p50"),
            })

        scored = run_plugins(conn, scored, profile, background, country_rule, {
            "countries": [country],
            "profile": profile,
            "rule": country_rule,
        })

        # 将插件结果写回原结构
        plugin_changes: dict[str, dict] = {}
        for s in scored:
            name = s.get("name", "")
            new_category = s.get("category", "")
            if new_category and new_category != _map_tianquan_to_advisor_chance(
                next(
                    (sch.get("admission_chance", "") for sch in country_result.get("schools", [])
                     if sch.get("name") == name),
                    ""
                )
            ):
                plugin_changes[name] = {"adjusted_chance": _map_advisor_to_tianquan_chance(new_category)}

        for school in country_result.get("schools", []):
            if school["name"] in plugin_changes:
                school.update(plugin_changes[school["name"]])

    return match_result


def _map_tianquan_to_advisor_chance(chance: str) -> str:
    """将 tianquan 的录取分档映射到 advisor 的分档"""
    mapping = {
        "安全": "保底",
        "匹配": "稳妥",
        "冲刺": "冲刺",
    }
    return mapping.get(chance, "稳妥")


def _map_advisor_to_tianquan_chance(chance: str) -> str:
    """将 advisor 的分档映射回 tianquan 的分档"""
    mapping = {
        "保底": "安全",
        "稳妥": "匹配",
        "冲刺": "冲刺",
        "排除": "排除",
    }
    return mapping.get(chance, "匹配")


def generate_application_strategy(background: dict, match_result: dict) -> str:
    """生成申请策略建议。"""
    strategies = []

    tier = background.get("school_tier", 5)
    for country_result in match_result.get("by_country", []):
        country = country_result.get("country", "")
        schools = country_result.get("schools", [])
        safe_count = sum(1 for s in schools if s.get("admission_chance") == "安全")
        match_count = sum(1 for s in schools if s.get("admission_chance") == "匹配")
        reach_count = sum(1 for s in schools if s.get("admission_chance") == "冲刺")

        if safe_count < 2:
            strategies.append(f"{country}：保底校偏少（{safe_count}所），建议增加 2-3 所 QS 排名靠后但录取记录多的院校")

        if reach_count > match_count:
            strategies.append(f"{country}：冲刺校比例较高（冲刺{reach_count} > 匹配{match_count}），建议增加匹配档院校确保录取")

        if tier <= 2:
            strategies.append("背景较强（985/211），建议重点关注 QS 前 50 院校的主申机会")

    return "\n".join(strategies) if strategies else "选校结构合理，可按当前方案申请。"


def generate_background_improvement(background: dict, match_result: dict) -> list[str]:
    """生成背景提升建议。"""
    suggestions = []

    tier = background.get("school_tier", 5)
    gpa_percent = background.get("gpa_percent")
    gpa4 = background.get("gpa4")

    # GPA 建议
    if gpa4 and gpa4 < 3.0:
        suggestions.append("GPA 有较大提升空间，建议优先提高专业课成绩")
    elif gpa4 and gpa4 < 3.5:
        suggestions.append("GPA 处于中等水平，保持的同时可加强软背景")
    elif gpa4 and gpa4 >= 3.5:
        suggestions.append("GPA 表现优秀，继续保持")

    # 冲刺校提分建议
    gpa_gaps = []
    for country_result in match_result.get("by_country", []):
        for school in country_result.get("schools", []):
            if school.get("admission_chance") == "冲刺" and school.get("gpa_gap"):
                gpa_gaps.append(school["gpa_gap"])

    if gpa_gaps:
        avg_gap = sum(gpa_gaps) / len(gpa_gaps)
        if avg_gap < 5:
            suggestions.append(f"部分冲刺校平均需提分 {avg_gap:.0f} 百分点，短期努力有希望")
        elif avg_gap < 10:
            suggestions.append(f"冲刺校提分需求中等（平均 {avg_gap:.0f} 百分点），建议配合实习/科研背景提升")

    # 语言成绩
    if background.get("toefl_score") and background["toefl_score"] < 90:
        suggestions.append("托福成绩偏低，建议目标 100+ 以增加 Top50 录取机会")
    if background.get("ielts_score") and background["ielts_score"] < 6.5:
        suggestions.append("雅思成绩偏低，建议目标 7.0+ 以增加 Top 院校录取机会")

    # 学校层次建议
    if tier > 3:
        suggestions.append("本科院校背景一般，建议通过高 GPA、高语言成绩和丰富实习经历弥补")

    return suggestions if suggestions else ["背景良好，按计划准备即可"]
