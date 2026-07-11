"""推荐引擎常识合理性测试 — 端到端集成测试。

测试目标：用真实 DB 跑完整推荐流程，验证分档逻辑是否符合大众常识。
硬约束：不 mock 数据库，依赖 API 端点。
"""
import os
# 必须在任何其他导入之前强制设定授权码，否则 Settings() 单例已被其他测试模块实例化
os.environ["TIANQUAN_VALID_AUTH_CODES"] = "88888888"

import sys

# 让 `from app.main import app` 可解析
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import pytest
from fastapi.testclient import TestClient
# 强制重新加载 settings（如果被其他测试模块抢先创建了单例）
import app.core.config
from importlib import reload
reload(app.core.config)
from app.main import app

client = TestClient(app)


AUTH_HEADERS = {"X-Auth-Code": "88888888"}


def _recommend(payload: dict) -> dict:
    resp = client.post("/api/recommend", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 200, f"API error: {resp.text}"
    return resp.json()


# ══════════════════════════════════════════════════════════════════════════════
# 测试用户画像
#   - 211 院校，财政学 → 金融，GPA 82/100 → 百分制
#   - 目标：澳大利亚，金融硕士
# ══════════════════════════════════════════════════════════════════════════════
BASE_PROFILE = {
    "target_countries": ["澳大利亚"],
    "gpa_score": 82.0,
    "gpa_format": "百分制",
    "study_level": "硕士",
    "target_major": "金融",
    "original_major": "财政学",
    "undergraduate_school": "苏州大学",        # 真实 211
}

BASE_PROFILE_985 = {
    "target_countries": ["澳大利亚"],
    "gpa_score": 82.0,
    "gpa_format": "百分制",
    "study_level": "硕士",
    "target_major": "金融",
    "original_major": "财政学",
    "undergraduate_school": "厦门大学",        # 真实 985
}

BASE_PROFILE_SHUANGFEI = {
    "target_countries": ["澳大利亚"],
    "gpa_score": 82.0,
    "gpa_format": "百分制",
    "study_level": "硕士",
    "target_major": "金融",
    "original_major": "财政学",
    "undergraduate_school": "集美大学",        # 真实 双非
}

# ── 英国 ──
UK_PROFILE = {
    "target_countries": ["英国"],
    "gpa_score": 82.0,
    "gpa_format": "百分制",
    "study_level": "硕士",
    "target_major": "金融",
    "original_major": "财政学",
    "undergraduate_school": "苏州大学",        # 211
}
UK_PROFILE_985 = {**UK_PROFILE, "undergraduate_school": "厦门大学"}
UK_PROFILE_SHUANGFEI = {**UK_PROFILE, "undergraduate_school": "集美大学"}

# ── 美国 ──
US_PROFILE = {
    "target_countries": ["美国"],
    "gpa_score": 82.0,
    "gpa_format": "百分制",
    "study_level": "硕士",
    "target_major": "金融",
    "original_major": "财政学",
    "undergraduate_school": "苏州大学",        # 211
}
US_PROFILE_985 = {**US_PROFILE, "undergraduate_school": "厦门大学"}
US_PROFILE_SHUANGFEI = {**US_PROFILE, "undergraduate_school": "集美大学"}


# ══════════════════════════════════════════════════════════════════════════════
# 通用检查
# ══════════════════════════════════════════════════════════════════════════════
def _get_schools(result: dict, country: str) -> list[dict]:
    for cr in result.get("by_country", []):
        if cr["country"] == country:
            return cr.get("schools", [])
    return []


def _get_australia_schools(result: dict) -> list[dict]:
    return _get_schools(result, "澳大利亚")


def test_has_australia_results():
    """基本检查：澳大利亚推荐不为空。"""
    result = _recommend(BASE_PROFILE)
    schools = _get_australia_schools(result)
    assert len(schools) >= 5, f"澳大利亚推荐学校不足5所: {len(schools)}"


def test_background_detected_correctly():
    """背景检测：211 院校 → tier=2, label='211'。"""
    result = _recommend(BASE_PROFILE)
    bg = result.get("background", {})
    assert bg.get("school_tier") == 2, f"学校层次应为211(tier=2), 实际={bg}"
    assert bg.get("school_tier_label") == "211"


def test_background_985_detected():
    """背景检测：985 院校 → tier=1, label='985'。"""
    result = _recommend(BASE_PROFILE_985)
    bg = result.get("background", {})
    assert bg.get("school_tier") == 1, f"学校层次应为985(tier=1), 实际={bg}"
    assert bg.get("school_tier_label") in ("985", "C9"), f"标签应为985/C9, 实际={bg}"


def test_background_shuangfei_detected():
    """背景检测：集美大学 → tier=4, label='双非'。"""
    result = _recommend(BASE_PROFILE_SHUANGFEI)
    bg = result.get("background", {})
    assert bg.get("school_tier") == 4, f"集美大学应为双非(tier=4), 实际={bg}"
    assert bg.get("school_tier_label") == "双非"


# ══════════════════════════════════════════════════════════════════════════════
# Tier 分档常识检查
# ══════════════════════════════════════════════════════════════════════════════
def test_three_tiers_all_present():
    """冲刺/匹配/安全 三档都应该存在学校。"""
    result = _recommend(BASE_PROFILE)
    schools = _get_australia_schools(result)
    tiers = {s.get("admission_chance") for s in schools}
    assert "安全" in tiers, f"缺少安全档: {tiers}"
    assert "匹配" in tiers, f"缺少匹配档: {tiers}"
    assert "冲刺" in tiers, f"缺少冲刺档: {tiers}"
    print(f"  三档分布: { {t: sum(1 for s in schools if s['admission_chance']==t) for t in ['安全','匹配','冲刺']} }")


def test_lower_qs_schools_more_reachable():
    """常识：QS 排名低的学校不应比 QS 排名高的学校更难录取（档位不应更差）。
    即：QS 排名更低的学校 admission_chance 不应劣于 QS 排名更高的学校。"""
    result = _recommend(BASE_PROFILE)
    schools = _get_australia_schools(result)
    tier_order = {"冲刺": 0, "匹配": 1, "安全": 2}
    ranked = [(s.get("qs_rank", 9999), tier_order.get(s.get("admission_chance", ""), 0), s["name"])
              for s in schools if s.get("qs_rank") and s["name"] in (
        "墨尔本大学", "悉尼大学", "新南威尔士大学", "莫纳什大学",
        "昆士兰大学", "西澳大学", "阿德莱德大学", "悉尼科技大学",
        "伍伦贡大学", "麦考瑞大学",
    )]
    ranked.sort()
    print("\n  QS→档位排序:")
    for qs, tier_val, name in ranked:
        tier_label = ["冲刺", "匹配", "安全"][tier_val]
        print(f"    QS#{qs} {name} → {tier_label}")

    for i in range(len(ranked) - 1):
        # QS 排名升序排列，越往后 QS 排名越低 → 档位不应更差
        assert ranked[i][1] <= ranked[i+1][1], \
            f"反常：{ranked[i][2]}(QS#{ranked[i][0]}:{['冲刺','匹配','安全'][ranked[i][1]]}) " \
            f"比 {ranked[i+1][2]}(QS#{ranked[i+1][0]}:{['冲刺','匹配','安全'][ranked[i+1][1]]}) 更容易"


def test_tier_consistency_for_known_outliers():
    """特定学校的常识分档检查。"""
    result = _recommend(BASE_PROFILE)
    schools = _get_australia_schools(result)
    school_map = {s["name"]: s for s in schools}

    # 墨尔本（QS#22, median 87 vs 82）→ 冲刺（GPA 差距大）
    mel = school_map.get("墨尔本大学")
    if mel:
        assert mel.get("admission_chance") == "冲刺", \
            f"墨尔本应为冲刺, 实际={mel.get('admission_chance')}"

    # 伍伦贡（QS#195, low tier）→ 安全（用户 GPA 明显超过）
    wol = school_map.get("伍伦贡大学")
    if wol:
        assert wol.get("admission_chance") == "安全", \
            f"伍伦贡应为安全, 实际={wol.get('admission_chance')}"

    # 悉尼科技大学（QS#96, median ≤ user GPA）→ 安全
    uts = school_map.get("悉尼科技大学")
    if uts:
        assert uts.get("admission_chance") == "安全", \
            f"悉尼科技大学应为安全, 实际={uts.get('admission_chance')}"


# ══════════════════════════════════════════════════════════════════════════════
# 满分位分档检查
# ══════════════════════════════════════════════════════════════════════════════
def test_high_gpa_all_safe():
    """GPA 95/100（优异）→ 几乎所有学校都是安全档。"""
    profile = {**BASE_PROFILE, "gpa_score": 95.0}
    result = _recommend(profile)
    schools = _get_australia_schools(result)
    tiers = {s.get("admission_chance") for s in schools}
    assert "安全" in tiers
    reach_count = sum(1 for s in schools if s.get("admission_chance") == "冲刺")
    assert reach_count <= 1, f"GPA 95 不应有多个冲刺校, 实际有 {reach_count} 个"


def test_low_gpa_more_reach():
    """GPA 70/100（偏低）→ 大部分学校应为冲刺或匹配，安全档很少。"""
    profile = {**BASE_PROFILE, "gpa_score": 70.0}
    result = _recommend(profile)
    schools = _get_australia_schools(result)
    safe_count = sum(1 for s in schools if s.get("admission_chance") == "安全")
    reach_count = sum(1 for s in schools if s.get("admission_chance") == "冲刺")
    print(f"  GPA 70: 安全={safe_count}, 匹配={sum(1 for s in schools if s.get('admission_chance')=='匹配')}, 冲刺={reach_count}")
    assert safe_count <= int(len(schools) * 0.3), \
        f"GPA 70 安全档不应超过30%, 实际 {safe_count}/{len(schools)}"


def test_985_vs_shuangfei_tier_shift():
    """同样 GPA 下，985 背景应得到比双非更乐观的推荐（同等学校档位不劣于双非）。"""
    result_985 = _recommend(BASE_PROFILE_985)
    result_sf = _recommend(BASE_PROFILE_SHUANGFEI)

    schools_985 = {s["name"]: s for s in _get_australia_schools(result_985)}
    schools_sf = {s["name"]: s for s in _get_australia_schools(result_sf)}

    tier_val = {"冲刺": 0, "匹配": 1, "安全": 2}
    divergences = []
    for name in schools_985:
        if name in schools_sf:
            t985 = tier_val.get(schools_985[name].get("admission_chance", ""), 1)
            tsf = tier_val.get(schools_sf[name].get("admission_chance", ""), 1)
            if t985 < tsf:
                divergences.append(f"  {name}: 985→{['冲刺','匹配','安全'][t985]}, 双非→{['冲刺','匹配','安全'][tsf]}")

    if divergences:
        print("\n  985 背景比双非更有利的差异:")
        for d in divergences:
            print(d)
    # 985 应该得到至少不差于双非的结果
    bad = [d for d in divergences if "冲刺" in d.split("双非→")[-1]]
    assert len(bad) == 0, f"985 不应比双非档位更差: {bad}"


# ══════════════════════════════════════════════════════════════════════════════
# 英国（UK）— 与澳大利亚相同逻辑
# ══════════════════════════════════════════════════════════════════════════════
def _get_uk_schools(result: dict) -> list[dict]:
    return _get_schools(result, "英国")


def test_uk_has_results():
    """英国推荐不为空。"""
    result = _recommend(UK_PROFILE)
    schools = _get_uk_schools(result)
    assert len(schools) >= 5, f"英国推荐学校不足5所: {len(schools)}"


def test_uk_three_tiers_present():
    """英国也应存在冲刺/匹配/安全三档。"""
    result = _recommend(UK_PROFILE)
    schools = _get_uk_schools(result)
    tiers = {s.get("admission_chance") for s in schools}
    assert "安全" in tiers, f"UK 缺少安全档: {tiers}"
    assert "匹配" in tiers, f"UK 缺少匹配档: {tiers}"
    assert "冲刺" in tiers, f"UK 缺少冲刺档: {tiers}"
    print(f"  UK 三档分布: { {t: sum(1 for s in schools if s['admission_chance']==t) for t in ['安全','匹配','冲刺']} }")


def test_uk_lower_qs_more_reachable():
    """英国同校对比：QS 更低不应比 QS 更高档位更差。"""
    result = _recommend(UK_PROFILE)
    schools = _get_uk_schools(result)
    tier_order = {"冲刺": 0, "匹配": 1, "安全": 2}
    ranked = [(s.get("qs_rank", 9999), tier_order.get(s.get("admission_chance", ""), 0), s["name"])
              for s in schools if s.get("qs_rank") and s["name"] in (
        "帝国理工学院", "伦敦大学学院", "爱丁堡大学", "曼彻斯特大学",
        "伦敦国王学院", "华威大学", "格拉斯哥大学", "南安普顿大学",
        "杜伦大学", "谢菲尔德大学",
    )]
    ranked.sort()
    print("\n  UK QS→档位排序:")
    for qs, tier_val, name in ranked:
        print(f"    QS#{qs} {name} → {['冲刺','匹配','安全'][tier_val]}")
    for i in range(len(ranked) - 1):
        assert ranked[i][1] <= ranked[i + 1][1], \
            f"UK 反常：{ranked[i][2]}(QS#{ranked[i][0]}) 比 {ranked[i+1][2]}(QS#{ranked[i+1][0]}) 更容易"


def test_uk_high_gpa_all_safe():
    """UK GPA 95 也应几乎全安全。"""
    profile = {**UK_PROFILE, "gpa_score": 95.0}
    result = _recommend(profile)
    schools = _get_uk_schools(result)
    reach_count = sum(1 for s in schools if s.get("admission_chance") == "冲刺")
    assert reach_count <= 2, f"UK GPA 95 冲刺校过多: {reach_count}"


def test_uk_low_gpa_more_reach():
    """UK GPA 70 安全档 ≤30%。"""
    profile = {**UK_PROFILE, "gpa_score": 70.0}
    result = _recommend(profile)
    schools = _get_uk_schools(result)
    safe_count = sum(1 for s in schools if s.get("admission_chance") == "安全")
    assert safe_count <= int(len(schools) * 0.3), \
        f"UK GPA 70 安全档过多: {safe_count}/{len(schools)}"


def test_uk_985_vs_shuangfei():
    """UK 同样 GPA 下 985 不劣于双非。"""
    r985 = _recommend(UK_PROFILE_985)
    rsf = _recommend(UK_PROFILE_SHUANGFEI)
    s985 = {s["name"]: s for s in _get_uk_schools(r985)}
    ssf = {s["name"]: s for s in _get_uk_schools(rsf)}
    tier_val = {"冲刺": 0, "匹配": 1, "安全": 2}
    bad = []
    for name in s985:
        if name in ssf and tier_val.get(s985[name].get("admission_chance", ""), 1) < tier_val.get(ssf[name].get("admission_chance", ""), 1):
            bad.append(name)
    assert len(bad) == 0, f"UK 985 不应比双非更差: {bad}"


# ══════════════════════════════════════════════════════════════════════════════
# 美国（US）— 美国 QS 排名不如英澳反映实际难度，但三档和高/低 GPA 检查仍有效
# ══════════════════════════════════════════════════════════════════════════════
def _get_us_schools(result: dict) -> list[dict]:
    return _get_schools(result, "美国")


def test_us_has_results():
    """美国推荐不为空。"""
    result = _recommend(US_PROFILE)
    schools = _get_us_schools(result)
    assert len(schools) >= 5, f"美国推荐学校不足5所: {len(schools)}"


def test_us_three_tiers_present():
    """美国至少应有冲刺和匹配两档（安全档较少是合理的）。"""
    result = _recommend(US_PROFILE)
    schools = _get_us_schools(result)
    tiers = {s.get("admission_chance") for s in schools}
    assert "冲刺" in tiers, f"US 缺少冲刺档: {tiers}"
    assert "匹配" in tiers, f"US 缺少匹配档: {tiers}"
    print(f"  US 三档分布: { {t: sum(1 for s in schools if s['admission_chance']==t) for t in ['安全','匹配','冲刺']} }")


def test_us_high_gpa_all_safe():
    """US GPA 95 极少冲刺校。"""
    profile = {**US_PROFILE, "gpa_score": 95.0}
    result = _recommend(profile)
    schools = _get_us_schools(result)
    reach_count = sum(1 for s in schools if s.get("admission_chance") == "冲刺")
    assert reach_count <= 3, f"US GPA 95 冲刺校过多: {reach_count}"


def test_us_low_gpa_more_reach():
    """US GPA 70 安全档 ≤30%。"""
    profile = {**US_PROFILE, "gpa_score": 70.0}
    result = _recommend(profile)
    schools = _get_us_schools(result)
    safe_count = sum(1 for s in schools if s.get("admission_chance") == "安全")
    assert safe_count <= int(len(schools) * 0.3), \
        f"US GPA 70 安全档过多: {safe_count}/{len(schools)}"


def test_us_985_vs_shuangfei():
    """US 同样 GPA 下 985 不劣于双非。"""
    r985 = _recommend(US_PROFILE_985)
    rsf = _recommend(US_PROFILE_SHUANGFEI)
    s985 = {s["name"]: s for s in _get_us_schools(r985)}
    ssf = {s["name"]: s for s in _get_us_schools(rsf)}
    tier_val = {"冲刺": 0, "匹配": 1, "安全": 2}
    bad = []
    for name in s985:
        if name in ssf and tier_val.get(s985[name].get("admission_chance", ""), 1) < tier_val.get(ssf[name].get("admission_chance", ""), 1):
            bad.append(name)
    assert len(bad) == 0, f"US 985 不应比双非更差: {bad}"


# ══════════════════════════════════════════════════════════════════════════════
# 跨专业测试 — 其他主要专业大类 × 澳/英
# ══════════════════════════════════════════════════════════════════════════════
_OTHER_MAJORS = [
    pytest.param("计算机科学", "计算机科学与技术", id="cs"),
    pytest.param("法学", "法学", id="law"),
    pytest.param("电子工程", "电子信息工程", id="ee"),
]

_GETTER = {"澳大利亚": _get_australia_schools, "英国": _get_uk_schools}
_COUNTRIES_FOR_MAJOR = [("澳大利亚", "AU"), ("英国", "UK")]


@pytest.mark.parametrize("target_major,original_major", _OTHER_MAJORS)
def test_major_has_results(target_major, original_major):
    """其他专业：澳大利亚/英国推荐不为空。"""
    for country, _ in _COUNTRIES_FOR_MAJOR:
        profile = {
            "target_countries": [country],
            "gpa_score": 82.0,
            "gpa_format": "百分制",
            "study_level": "硕士",
            "target_major": target_major,
            "original_major": original_major,
            "undergraduate_school": "苏州大学",
        }
        result = _recommend(profile)
        schools = _GETTER[country](result)
        assert len(schools) >= 3, f"{target_major}/{country} 推荐不足3所: {len(schools)}"


@pytest.mark.parametrize("target_major,original_major", _OTHER_MAJORS)
def test_major_has_tiers(target_major, original_major):
    """其他专业：至少两档存在。"""
    for country, _ in _COUNTRIES_FOR_MAJOR:
        profile = {
            "target_countries": [country],
            "gpa_score": 82.0,
            "gpa_format": "百分制",
            "study_level": "硕士",
            "target_major": target_major,
            "original_major": original_major,
            "undergraduate_school": "苏州大学",
        }
        result = _recommend(profile)
        schools = _GETTER[country](result)
        tiers = {s.get("admission_chance") for s in schools}
        assert "冲刺" in tiers, f"{target_major}/{country} 缺少冲刺: {tiers}"
        assert "匹配" in tiers, f"{target_major}/{country} 缺少匹配: {tiers}"
        # 不强制要求安全档存在（各国各专业难度不同）


@pytest.mark.parametrize("target_major,original_major", _OTHER_MAJORS)
def test_major_low_gpa_more_reach(target_major, original_major):
    """其他专业：GPA 70 安全档不宜超过30%。"""
    for country, _ in _COUNTRIES_FOR_MAJOR:
        profile = {
            "target_countries": [country],
            "gpa_score": 70.0,
            "gpa_format": "百分制",
            "study_level": "硕士",
            "target_major": target_major,
            "original_major": original_major,
            "undergraduate_school": "苏州大学",
        }
        result = _recommend(profile)
        schools = _GETTER[country](result)
        safe_count = sum(1 for s in schools if s.get("admission_chance") == "安全")
        assert safe_count <= int(len(schools) * 0.4), \
            f"{target_major}/{country} GPA70 安全档过多: {safe_count}/{len(schools)}"


# ══════════════════════════════════════════════════════════════════════════════
# 专业推荐（major_recommendations）字段检查
# ══════════════════════════════════════════════════════════════════════════════
def test_major_recommendations_field_exists():
    """专业推荐字段存在且为列表。"""
    result = _recommend(BASE_PROFILE)
    recs = result.get("major_recommendations", [])
    assert isinstance(recs, list), f"major_recommendations 应为 list, 实际={type(recs)}"


def test_major_recommendations_prioritizes_target():
    """用户目标专业对应的大类应排第一且契合度最高。"""
    result = _recommend(BASE_PROFILE)  # target_major=金融
    recs = result.get("major_recommendations", [])
    if recs:
        assert recs[0]["category"] == "金融", f"金融大类应排第一, 实际={recs[0].get('category')}"
        assert recs[0]["fit_score"] >= 50, f"目标专业契合度应≥50, 实际={recs[0].get('fit_score')}"
        assert len(recs[0]["schools"]) >= 1, f"应至少包含1所推荐学校, 实际={recs[0].get('schools')}"


def test_major_recommendations_cross_major_bonus():
    """跨专业时（软件工程→计算机）：专业推荐应有交叉加分。"""
    profile = {
        "target_countries": ["英国"],
        "gpa_score": 82.0,
        "gpa_format": "百分制",
        "study_level": "硕士",
        "target_major": "计算机科学",
        "original_major": "软件工程",
        "undergraduate_school": "苏州大学",
    }
    result = _recommend(profile)
    recs = result.get("major_recommendations", [])
    # 软件工程应与计算机(目标)和工程(本科)两大类别都有高契合度
    cs_rec = next((r for r in recs if r["category"] == "计算机"), None)
    eng_rec = next((r for r in recs if r["category"] == "工程"), None)
    assert cs_rec is not None, "应有计算机大类推荐"
    assert cs_rec["fit_score"] >= 80, f"CS 契合度应≥80(目标+本科), 实际={cs_rec.get('fit_score')}"
    if eng_rec:
        assert eng_rec["fit_score"] >= 30, f"工程应有交叉加分, 实际={eng_rec.get('fit_score')}"
