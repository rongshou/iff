"""
国家配置表：每个国家的选校规则差异用配置表达。
移植自 advisor/scripts/country_rules.py
"""

COUNTRY_RULES: dict[str, dict] = {
    "加拿大": {
        "rank_field": "qs_rank",
        "total_schools": 10,
        "ratio": {"冲刺": 0.2, "稳妥": 0.3, "保底": 0.5},
        "reach_limit": 2,
        "elite_threshold": 100,
        "safe_max_qs": 1500,
        "case_qs_threshold": 200,
        "tier_filters": {
            "双非": {"exclude_qs_below": 50},
        },
        "plugins": [],
    },
    "英国": {
        "rank_field": "qs_rank",
        "total_schools": 20,
        "ratio": {"冲刺": 0.25, "稳妥": 0.4, "保底": 0.35},
        "reach_limit": 5,
        "elite_threshold": 50,
        "safe_max_qs": 500,
        "case_qs_threshold": 50,
        "tier_filters": {
            "双非": {"exclude_names": ["牛津大学", "剑桥大学", "帝国理工学院"]},
        },
        "plugins": ["uk_acceptance_list"],
    },
    "美国": {
        "rank_field": "usnews_rank",
        "alt_rank_field": "qs_rank",
        "total_schools": 25,
        "ratio": {"冲刺": 0.25, "稳妥": 0.4, "保底": 0.35},
        "reach_limit": 10,
        "elite_threshold": 30,
        "safe_max_qs": 200,
        "case_qs_threshold": 50,
        "tier_filters": {
            "大专": {"exclude_rank_below": 50},
        },
        "plugins": ["us_classify", "us_lac"],
    },
    "澳大利亚": {
        "rank_field": "qs_rank",
        "total_schools": 14,
        "ratio": {"冲刺": 0.3, "稳妥": 0.4, "保底": 0.3},
        "reach_limit": 5,
        "elite_threshold": 20,
        "safe_max_qs": 500,
        "case_qs_threshold": 100,
        "tier_filters": {},
        "plugins": [],
    },
    "中国香港": {
        "rank_field": "qs_rank",
        "total_schools": 8,
        "ratio": {"冲刺": 0.25, "稳妥": 0.4, "保底": 0.35},
        "reach_limit": 3,
        "elite_threshold": 50,
        "safe_max_qs": 1500,
        "case_qs_threshold": 50,
        "tier_filters": {
            "双非": {"exclude_names": ["香港大学", "香港中文大学", "香港科技大学"]},
        },
        "plugins": ["hk_tier_override"],
    },
    "新加坡": {
        "rank_field": "qs_rank",
        "total_schools": 8,
        "ratio": {"冲刺": 0.2, "稳妥": 0.4, "保底": 0.4},
        "reach_limit": 3,
        "elite_threshold": 15,
        "safe_max_qs": 1500,
        "case_qs_threshold": 50,
        "tier_filters": {
            "双非": {"exclude_names": ["新加坡国立大学", "南洋理工大学"]},
        },
        "plugins": ["sg_cross_country"],
    },
    "日本": {
        "rank_field": "qs_rank",
        "total_schools": 10,
        "ratio": {"冲刺": 0.3, "稳妥": 0.4, "保底": 0.3},
        "reach_limit": 3,
        "elite_threshold": 50,
        "safe_max_qs": 1500,
        "case_qs_threshold": 50,
        "tier_filters": {},
        "plugins": [],
    },
}

EUROPE_COUNTRIES = [
    "英国", "德国", "法国", "荷兰", "瑞典", "芬兰", "丹麦", "爱尔兰",
    "比利时", "奥地利", "瑞士", "意大利", "西班牙", "葡萄牙", "挪威",
    "捷克", "波兰", "俄罗斯", "希腊",
]

MAJOR_EUROPE = {"英国", "德国", "法国"}

DEFAULT_RULE: dict = {
    "rank_field": "qs_rank",
    "total_schools": 10,
    "ratio": {"冲刺": 0.3, "稳妥": 0.4, "保底": 0.3},
    "reach_limit": 5,
    "elite_threshold": 50,
    "safe_max_qs": 500,
    "case_qs_threshold": 50,
    "tier_filters": {},
    "plugins": [],
}


def get_rule(country: str) -> dict:
    """获取指定国家的配置规则"""
    return COUNTRY_RULES.get(country, DEFAULT_RULE)


def get_merged_rule(countries: list[str]) -> dict:
    """多国取并集配置"""
    if not countries:
        return DEFAULT_RULE.copy()
    if len(countries) == 1:
        return get_rule(countries[0]).copy()

    merged = DEFAULT_RULE.copy()
    total_schools = 0
    for c in countries:
        r = get_rule(c)
        total_schools = max(total_schools, r.get("total_schools", 10))
        merged["safe_max_qs"] = max(merged["safe_max_qs"], r.get("safe_max_qs", 500))
        merged["case_qs_threshold"] = max(merged["case_qs_threshold"], r.get("case_qs_threshold", 50))
        for p in r.get("plugins", []):
            if p not in merged.get("plugins", []):
                merged.setdefault("plugins", []).append(p)
    merged["total_schools"] = total_schools
    return merged
