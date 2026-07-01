"""
规则引擎：读取 full_rules.json / uk_rules.json，提供规则匹配推荐。
移植自 advisor 的推荐规则系统。

规则格式：
  country -> tier -> gpa_bucket -> major_category -> { schools: [{name, count, percentage}], total_cases }
"""

import json
from pathlib import Path
from ..core.config import settings


_RULES_CACHE: dict[str, dict] = {}
_RULES_PATH = Path(settings.DB_PATH).parent / "rules"


def _load_rules(name: str) -> dict:
    """加载一个规则文件，带缓存"""
    if name in _RULES_CACHE:
        return _RULES_CACHE[name]

    path = _RULES_PATH / name
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _RULES_CACHE[name] = data
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_full_rules() -> list[dict]:
    """获取完整规则数据（扁平列表，每条有 country/tier/gpa_bucket/major_cat/total_cases/schools）"""
    return _load_rules("full_rules.json")


def get_uk_rules() -> dict:
    """获取 UK 特殊规则"""
    return _load_rules("uk_rules.json")


def get_rule_for_background(
    country: str,
    tier: int | str,
    gpa_percent: float | None,
    major_category: str = "",
    *,
    gpa_4scale: float | None = None,
) -> list[dict]:
    """根据背景获取规则推荐的学校列表。

    Args:
        country: 国家
        tier: 学校层次（1=985, 2=211, 3=强双非, 4=中双非, 5=弱双非）
        gpa_percent: GPA 百分制成绩（如 82）
        major_category: 专业方向
        gpa_4scale: GPA 4.0 制成绩（如 3.2）
    """
    rules = get_full_rules()
    if not rules:
        return []

    tier_str = _map_numeric_tier_to_label(tier)
    gpa_bucket = _get_gpa_bucket(gpa_percent, gpa_4scale)
    matched: list[dict] = []

    # 精确匹配 country + tier + gpa_bucket + major_cat
    for entry in rules:
        if (entry.get("country") == country
                and entry.get("tier") == tier_str
                and entry.get("gpa_bucket") == gpa_bucket):
            if not major_category:
                return entry.get("schools", [])
            if major_category in entry.get("major_cat", ""):
                return entry.get("schools", [])
            matched.append(entry)

    # 回退：匹配 country + tier
    if not matched:
        for entry in rules:
            if entry.get("country") == country and entry.get("tier") == tier_str:
                matched.append(entry)

    if matched:
        return matched[0].get("schools", [])

    return []


def _map_numeric_tier_to_label(tier: int | str) -> str:
    """将数字 tier 映射到规则中的标签"""
    try:
        t = int(tier)
    except (TypeError, ValueError):
        return "弱双非"
    mapping = {1: "985", 2: "211", 3: "强双非", 4: "中双非", 5: "弱双非"}
    return mapping.get(t, "弱双非")


def _get_gpa_bucket(gpa_percent: float | None, gpa_4scale: float | None = None) -> str:
    """将 GPA 映射到规则中的 bucket 名称"""
    # 优先使用 4.0 制
    if gpa_4scale is not None:
        if gpa_4scale >= 3.8:
            return "gpa_4.0"
        elif gpa_4scale >= 3.3:
            return "gpa_3.5"
        elif gpa_4scale >= 2.8:
            return "gpa_3.0"
        elif gpa_4scale >= 2.3:
            return "gpa_2.5"
        else:
            return "gpa_2.0"

    # 百分制
    if gpa_percent is None:
        return "pct_75"  # 默认
    if gpa_percent >= 90:
        return "pct_95"
    elif gpa_percent >= 85:
        return "pct_85"
    elif gpa_percent >= 80:
        return "pct_80"
    elif gpa_percent >= 75:
        return "pct_75"
    elif gpa_percent >= 70:
        return "pct_70"
    elif gpa_percent >= 65:
        return "pct_65"
    elif gpa_percent >= 60:
        return "pct_60"
    else:
        return "pct_55"
