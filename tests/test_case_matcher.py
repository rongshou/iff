"""case_matcher.py 纯函数单测 — 任务 H。

测试目标：backend/app/services/case_matcher.py 中的纯函数（不依赖外部数据/数据库）。
硬约束：不修改 case_matcher.py 源码，只读；不 mock 数据库，依赖 DB 的函数用 pytest.mark.skip 标注。
"""
import os
import sys

# 让 `from app.services.case_matcher import ...` 可解析
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import pytest

from app.services import case_matcher as cm


# ──────────────────────────────────────────────────────────────────────────────
# 工具：构造可控百分位字典
# ──────────────────────────────────────────────────────────────────────────────
def _perc(p10=None, p25=None, p50=None, p75=None, n=None):
    """构造 school_major_gpa_percentiles / school_percentiles 风格的字典。"""
    d = {}
    if p10 is not None:
        d["p10"] = p10
    if p25 is not None:
        d["p25"] = p25
    if p50 is not None:
        d["p50"] = p50
    if p75 is not None:
        d["p75"] = p75
    if n is not None:
        d["n"] = n
    return d


# ══════════════════════════════════════════════════════════════════════════════
# P0 — 三维评分函数 _score_school_3d
#   总分 = GPA 匹配分(0-40) + 学校排名分(0-30) + 案例证据分(0-30)
#   ≥75 = 安全 | 55-74 = 匹配 | <55 = 冲刺
# ══════════════════════════════════════════════════════════════════════════════

# ── GPA 维度：百分位细分档 ──────────────────────────────────────────────────
def test_p0_gpa_dimension_at_p75_returns_40():
    """GPA >= p75 时 GPA 维度满分为 40。"""
    perc = _perc(p25=60, p50=80, p75=90)
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=90)
    assert gpa_score == pytest.approx(40.0)


def test_p0_gpa_dimension_above_p75_returns_40():
    """GPA 显著高于 p75 仍是 40（在 0-40 内封顶）。"""
    perc = _perc(p25=60, p50=80, p75=90)
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=100)
    assert gpa_score == pytest.approx(40.0)


def test_p0_gpa_dimension_between_p50_and_p75_interpolates_24_to_40():
    """p50-p75 区间内 GPA 分为 24 ~ 40 的线性插值。"""
    perc = _perc(p25=60, p50=80, p75=90)
    # 取中点 85 → 24 + 16 * 0.5 = 32
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=85)
    assert gpa_score == pytest.approx(32.0)


def test_p0_gpa_dimension_at_p50_returns_24():
    """GPA 恰等于 p50 时 GPA 维度 24。"""
    perc = _perc(p25=60, p50=80, p75=90)
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=80)
    assert gpa_score == pytest.approx(24.0)


def test_p0_gpa_dimension_between_p25_and_p50_interpolates_8_to_24():
    """p25-p50 区间内 GPA 分为 8 ~ 24 的线性插值。"""
    perc = _perc(p25=60, p50=80, p75=90)
    # 取中点 70 → 8 + 16 * 0.5 = 16
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=70)
    assert gpa_score == pytest.approx(16.0)


def test_p0_gpa_dimension_at_p25_returns_8():
    """GPA 恰等于 p25 时 GPA 维度 8。"""
    perc = _perc(p25=60, p50=80, p75=90)
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=60)
    assert gpa_score == pytest.approx(8.0)


def test_p0_gpa_dimension_below_p25_scales_from_zero():
    """GPA 低于 p25 时分数随 GPA 比例收紧（max(0, 8 * gpa / p25)）。"""
    perc = _perc(p25=60, p50=80, p75=90)
    # 一半 p25 → 8 * 0.5 = 4
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=30)
    assert gpa_score == pytest.approx(4.0)


def test_p0_gpa_dimension_zero_gpa_zero_score():
    """GPA=0 时分数为 0（边界）。"""
    perc = _perc(p25=60, p50=80, p75=90)
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=0)
    assert gpa_score == pytest.approx(0.0)


def test_p0_gpa_dimension_only_p50_uses_simple_bucket_high():
    """仅有 p50 时走简单分档：gpa>=p50 直接 40。"""
    perc = _perc(p50=80)
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=80)
    assert gpa_score == pytest.approx(40.0)


def test_p0_gpa_dimension_only_p50_bucket_85pct():
    """[p50*0.85, p50) 区间得到 24。"""
    perc = _perc(p50=80)
    # 取 70 >= 80*0.85=68
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=70)
    assert gpa_score == pytest.approx(24.0)


def test_p0_gpa_dimension_only_p50_bucket_70pct():
    """[p50*0.70, p50*0.85) 区间得到 12。"""
    perc = _perc(p50=80)
    # 取 58 >= 80*0.7=56 且 < 80*0.85=68
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=58)
    assert gpa_score == pytest.approx(12.0)


def test_p0_gpa_dimension_only_p50_low():
    """低于 p50*0.70 时简单分档给出 4。"""
    perc = _perc(p50=80)
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=40)
    assert gpa_score == pytest.approx(4.0)


def test_p0_gpa_dimension_no_percentiles_returns_neutral_20():
    """无百分位数据时 GPA 维度给中性 20 分。"""
    gpa_score, _, _, _, _ = cm._score_school_3d(None, qs_rank=None, case_count=0, gpa_percent=50)
    assert gpa_score == pytest.approx(20.0)


def test_p0_gpa_dimension_empty_percentiles_returns_neutral_20():
    """空字典（无 p25/p50/p75）退中性分 20。"""
    gpa_score, _, _, _, _ = cm._score_school_3d({}, qs_rank=None, case_count=0, gpa_percent=50)
    assert gpa_score == pytest.approx(20.0)


def test_p0_gpa_dimension_degenerate_p75_equals_p25_uses_p50_branch():
    """p75 == p25 退化情形：detailed 分支失效，回退 p50 简单分档。"""
    perc = _perc(p25=80, p50=80, p75=80)
    # p75 > p25 为 False，进入 elif p50 分档
    gpa_score, _, _, _, _ = cm._score_school_3d(perc, qs_rank=None, case_count=0, gpa_percent=85)
    assert gpa_score == pytest.approx(40.0)


# ── 排名维度：QS 分档边界 ───────────────────────────────────────────────────
def test_p0_rank_dimension_qs1_to_20_returns_18():
    """QS 排名 1-20 → 18 分（顶级校，偏冲刺）。"""
    gpa_score, rank_score, _, _, _ = cm._score_school_3d(None, qs_rank=1, case_count=0, gpa_percent=50)
    assert rank_score == pytest.approx(18.0)


def test_p0_rank_dimension_qs20_boundary_returns_18():
    """边界 QS#20 仍 18 分。"""
    _, rank_score, _, _, _ = cm._score_school_3d(None, qs_rank=20, case_count=0, gpa_percent=50)
    assert rank_score == pytest.approx(18.0)


def test_p0_rank_dimension_qs21_boundary_returns_22():
    """边界 QS#21 跳到 22 分。"""
    _, rank_score, _, _, _ = cm._score_school_3d(None, qs_rank=21, case_count=0, gpa_percent=50)
    assert rank_score == pytest.approx(22.0)


def test_p0_rank_dimension_qs50_boundary_returns_22():
    """边界 QS#50 仍 22 分。"""
    _, rank_score, _, _, _ = cm._score_school_3d(None, qs_rank=50, case_count=0, gpa_percent=50)
    assert rank_score == pytest.approx(22.0)


def test_p0_rank_dimension_qs51_boundary_returns_25():
    """边界 QS#51 跳到 25 分。"""
    _, rank_score, _, _, _ = cm._score_school_3d(None, qs_rank=51, case_count=0, gpa_percent=50)
    assert rank_score == pytest.approx(25.0)


def test_p0_rank_dimension_qs101_boundary_returns_28():
    """边界 QS#101 跳到 28 分。"""
    _, rank_score, _, _, _ = cm._score_school_3d(None, qs_rank=101, case_count=0, gpa_percent=50)
    assert rank_score == pytest.approx(28.0)


def test_p0_rank_dimension_qs200_boundary_returns_28():
    """边界 QS#200 仍 28 分。"""
    _, rank_score, _, _, _ = cm._score_school_3d(None, qs_rank=200, case_count=0, gpa_percent=50)
    assert rank_score == pytest.approx(28.0)


def test_p0_rank_dimension_qs201_returns_30():
    """QS#201+ → 30 分（基础分封顶、最低门槛）。"""
    _, rank_score, _, _, _ = cm._score_school_3d(None, qs_rank=201, case_count=0, gpa_percent=50)
    assert rank_score == pytest.approx(30.0)


def test_p0_rank_dimension_qs_none_returns_30():
    """无 QS 排名数据 → 30 分（低门槛默认值）。"""
    _, rank_score, _, _, _ = cm._score_school_3d(None, qs_rank=None, case_count=0, gpa_percent=50)
    assert rank_score == pytest.approx(30.0)


def test_p0_rank_dimension_qs_zero_returns_30():
    """QS 排名 0 视为缺失 → 30 分。"""
    _, rank_score, _, _, _ = cm._score_school_3d(None, qs_rank=0, case_count=0, gpa_percent=50)
    # qs_rank=0 falsy → else 分支 → 30
    assert rank_score == pytest.approx(30.0)


def test_p0_rank_dimension_qs_above_9998_returns_30():
    """QS 排名 > 9998（哨兵值）视为无排名 → 30 分。"""
    _, rank_score, _, _, _ = cm._score_school_3d(None, qs_rank=9999, case_count=0, gpa_percent=50)
    assert rank_score == pytest.approx(30.0)


# ── 案例证据维度边界 ────────────────────────────────────────────────────────
def test_p0_evidence_dimension_zero_returns_0():
    """0 案例 → 0 分。"""
    _, _, evidence_score, _, _ = cm._score_school_3d(None, qs_rank=None, case_count=0, gpa_percent=50)
    assert evidence_score == pytest.approx(0.0)


def test_p0_evidence_dimension_one_returns_12():
    """1 案例 → 12 分（边界）。"""
    _, _, evidence_score, _, _ = cm._score_school_3d(None, qs_rank=None, case_count=1, gpa_percent=50)
    assert evidence_score == pytest.approx(12.0)


def test_p0_evidence_dimension_five_returns_12():
    """5 案例 → 12 分（边界上界）。"""
    _, _, evidence_score, _, _ = cm._score_school_3d(None, qs_rank=None, case_count=5, gpa_percent=50)
    assert evidence_score == pytest.approx(12.0)


def test_p0_evidence_dimension_six_returns_15():
    """6 案例 → 15 分（边界跳档）。"""
    _, _, evidence_score, _, _ = cm._score_school_3d(None, qs_rank=None, case_count=6, gpa_percent=50)
    assert evidence_score == pytest.approx(15.0)


def test_p0_evidence_dimension_fifteen_returns_15():
    """15 案例 → 15 分（边界上界）。"""
    _, _, evidence_score, _, _ = cm._score_school_3d(None, qs_rank=None, case_count=15, gpa_percent=50)
    assert evidence_score == pytest.approx(15.0)


def test_p0_evidence_dimension_sixteen_returns_20():
    """16 案例 → 20 分（封顶）。"""
    _, _, evidence_score, _, _ = cm._score_school_3d(None, qs_rank=None, case_count=16, gpa_percent=50)
    assert evidence_score == pytest.approx(20.0)


def test_p0_evidence_dimension_large_count_caps_at_20():
    """大量案例仍封顶 20 分。"""
    _, _, evidence_score, _, _ = cm._score_school_3d(None, qs_rank=None, case_count=999, gpa_percent=50)
    assert evidence_score == pytest.approx(20.0)


# ── 三维综合与分档逻辑 ────────────────────────────────────────────────────
def test_p0_total_score_is_sum_of_three_dimensions():
    """总分 = GPA + 排名 + 证据。"""
    perc = _perc(p25=60, p50=80, p75=90)
    _, _, _, total, _ = cm._score_school_3d(perc, qs_rank=50, case_count=10, gpa_percent=85)
    # GPA 32 + rank 22 + evidence 15 = 69
    assert total == pytest.approx(69.0)


def test_p0_full_stack_returns_total_near_100():
    """所有维度接近满分时总分接近 90。"""
    perc = _perc(p25=60, p50=80, p75=90)
    _, _, _, total, _ = cm._score_school_3d(perc, qs_rank=201, case_count=50, gpa_percent=95)
    # GPA 40 + rank 30 + evidence 20 = 90
    assert total == pytest.approx(90.0)


# ══════════════════════════════════════════════════════════════════════════════
# P3 — 档位划分（嵌入在 _score_school_3d 末尾返回的 tier）
#   ≥75 = 安全 | 55-74 = 匹配 | <55 = 冲刺
# ══════════════════════════════════════════════════════════════════════════════
def test_p3_tier_safe_boundary_75_is_safe():
    """分数恰好 75.0 → 安全（边界含）。"""
    # 构造：GPA 25 + 排名 30 + 证据 20 = 75
    # 见 P0：p25=60, p50=80, p75=90 时 gpa=80.625 → GPA 分 25
    perc = _perc(p25=60, p50=80, p75=90)
    _, _, _, total, tier = cm._score_school_3d(perc, qs_rank=201, case_count=16, gpa_percent=80.625)
    assert total == pytest.approx(75.0)
    assert tier == "安全"


def test_p3_tier_just_below_safe_boundary_is_match():
    """分数 74.9 → 匹配（边界外）。"""
    # GPA 分 24.9 → 24+1.6*(gpa-80)=24.9 ⇒ gpa=80.5625
    perc = _perc(p25=60, p50=80, p75=90)
    _, _, _, total, tier = cm._score_school_3d(perc, qs_rank=201, case_count=16, gpa_percent=80.5625)
    assert total == pytest.approx(74.9, abs=0.05)
    assert tier == "匹配"


def test_p3_tier_match_boundary_55_is_match():
    """分数恰好 55.0 → 匹配（边界含）。"""
    # GPA 37 + 排名 18 + 证据 0 = 55
    # p50=70, p75=90：24 + 16*(gpa-70)/20 = 37 ⇒ gpa = 86.25
    perc = _perc(p25=60, p50=70, p75=90)
    _, _, _, total, tier = cm._score_school_3d(perc, qs_rank=20, case_count=0, gpa_percent=86.25)
    assert total == pytest.approx(55.0)
    assert tier == "匹配"


def test_p3_tier_just_below_match_boundary_is_reach():
    """分数 54.9 → 冲刺（边界外）。"""
    # GPA 36.9 + rank 18 + evidence 0 = 54.9
    perc = _perc(p25=60, p50=70, p75=90)
    _, _, _, total, tier = cm._score_school_3d(perc, qs_rank=20, case_count=0, gpa_percent=86.125)
    assert total == pytest.approx(54.9, abs=0.05)
    assert tier == "冲刺"


def test_p3_tier_minimum_total_is_reach():
    """最低组合（无数据 + 无案例 + 顶级校）→ 冲刺。"""
    _, _, _, total, tier = cm._score_school_3d(None, qs_rank=10, case_count=0, gpa_percent=0)
    # GPA 20 + rank 18 + evidence 0 = 38
    assert total == pytest.approx(38.0)
    assert tier == "冲刺"


def test_p3_tier_maximum_total_is_safe():
    """最高组合 → 安全。"""
    perc = _perc(p25=60, p50=80, p75=90)
    _, _, _, total, tier = cm._score_school_3d(perc, qs_rank=300, case_count=100, gpa_percent=100)
    assert total == pytest.approx(90.0)
    assert tier == "安全"


# ══════════════════════════════════════════════════════════════════════════════
# P1 — GPA 提升建议 _calculate_gpa_gap
# ══════════════════════════════════════════════════════════════════════════════
def test_p1_gpa_gap_positive_when_user_below_required():
    """用户 GPA 低于"匹配档"所需 → 返回正数缺口。"""
    perc = _perc(p25=60, p50=80, p75=90)
    # rank=18, evidence=18 ⇒ gpa_needed = 55 - 18 - 18 = 19 ⇒ ≤24 分支:
    #   needed_percent = 60 + (19-8)*(80-60)/16 = 60 + 11*20/16 = 60 + 13.75 = 73.75
    # user_gpa=70 ⇒ gap = 73.75 - 70 = 3.75 → round(3.75,1) = 3.8
    gap = cm._calculate_gpa_gap(perc, user_gpa_percent=70.0, gpa_score=0.0, rank_score=18.0, evidence_score=18.0)
    assert gap == pytest.approx(3.8, abs=0.05)


def test_p1_gpa_gap_zero_when_user_above_required():
    """用户 GPA 高于所需 → 缺口截断为 0。"""
    perc = _perc(p25=60, p50=80, p75=90)
    # needed_percent = 73.75；user=85 ⇒ negative ⇒ max(0, ...) = 0
    gap = cm._calculate_gpa_gap(perc, user_gpa_percent=85.0, gpa_score=0.0, rank_score=18.0, evidence_score=18.0)
    assert gap == 0.0


def test_p1_gpa_gap_zero_when_user_equals_required():
    """用户 GPA 恰等于所需 → gap 为 0（边界）。"""
    perc = _perc(p25=60, p50=80, p75=90)
    # needed_percent = 73.75
    gap = cm._calculate_gpa_gap(perc, user_gpa_percent=73.75, gpa_score=0.0, rank_score=18.0, evidence_score=18.0)
    assert gap == 0.0


def test_p1_gpa_gap_low_band_below_p25():
    """gpa_needed 落在 ≤8 分支：所需百分比在 [0, p25] 内线性。"""
    perc = _perc(p25=60, p50=80, p75=90)
    # rank=30, evidence=30 ⇒ gpa_needed = max(0, 55-60) = 0 ⇒ needed_percent = 0
    gap = cm._calculate_gpa_gap(perc, user_gpa_percent=10.0, gpa_score=0.0, rank_score=30.0, evidence_score=30.0)
    # needed=0 ⇒ needed_percent = 0 ⇒ gap = 0 - 10 ⇒ max(0, -10) = 0
    assert gap == 0.0


def test_p1_gpa_gap_high_band_minimal():
    """gpa_needed 落在 >24 分支（p50-p75 段）。"""
    perc = _perc(p25=60, p50=80, p75=90)
    # rank=18, evidence=0 ⇒ gpa_needed = 37 ⇒ ≤40 分支:
    #   needed_percent = p50 + (37-24)*(p75-p50)/16 = 80 + 13*10/16 = 80 + 8.125 = 88.125
    # user=80 ⇒ gap = 8.125 → round() = 8.1
    gap = cm._calculate_gpa_gap(perc, user_gpa_percent=80.0, gpa_score=0.0, rank_score=18.0, evidence_score=0.0)
    assert gap == pytest.approx(8.1, abs=0.1)


def test_p1_gpa_gap_overflow_band_caps_at_p75_plus_5():
    """gpa_needed > 40（极冲刺）→ needed_percent = p75 + 5。"""
    perc = _perc(p25=60, p50=80, p75=90)
    # rank=0, evidence=0 ⇒ gpa_needed = 55 ⇒ >40 ⇒ needed_percent = 90 + 5 = 95
    # user=50 ⇒ gap = 95-50 = 45 → round = 45.0
    gap = cm._calculate_gpa_gap(perc, user_gpa_percent=50.0, gpa_score=0.0, rank_score=0.0, evidence_score=0.0)
    assert gap == pytest.approx(45.0)


def test_p1_gpa_gap_returns_none_when_no_percentiles():
    """无 percentiles → 返回 None。"""
    assert cm._calculate_gpa_gap(None, 50.0, 0.0, 30.0, 18.0) is None


def test_p1_gpa_gap_returns_none_when_missing_keys():
    """percentiles 缺少 p25/p50/p75 → 返回 None。"""
    assert cm._calculate_gpa_gap(_perc(p50=80), 50.0, 0.0, 30.0, 18.0) is None


def test_p1_gpa_gap_returns_none_when_degenerate_flat():
    """p75 <= p25 → 返回 None（避免除零）。"""
    perc = _perc(p25=80, p50=80, p75=80)
    assert cm._calculate_gpa_gap(perc, 50.0, 0.0, 30.0, 18.0) is None


# ══════════════════════════════════════════════════════════════════════════════
# P2 — 案例聚合（纯函数 _group_by_school，不依赖 DB）
#   DB 相关的 match_schools_by_background / _filter_and_score 用 skip 标注
# ══════════════════════════════════════════════════════════════════════════════
def test_p2_group_by_school_basic_aggregation():
    """同国家同学校案例被聚合到同一槽位，并统计 case 数。"""
    rows = [
        {"country": "美国", "university": "MIT", "university_id": 1,
         "_gpa4": 3.8, "_meets_req": True, "_strict_meets": True, "_req_value": None,
         "_tier_diff": 1, "admitted_major": "CS"},
        {"country": "美国", "university": "MIT", "university_id": None,
         "_gpa4": 3.5, "_meets_req": True, "_strict_meets": True, "_req_value": None,
         "_tier_diff": 1, "admitted_major": "DS"},
    ]
    grouped = cm._group_by_school(rows, gpa_percent=85.0, gpa4=3.6, tier_key="985", uni_requirements={})
    slot = grouped["美国"]["MIT"]
    assert len(slot["cases"]) == 2
    assert slot["gpas"] == [3.8, 3.5]
    assert "CS" in slot["majors"] and "DS" in slot["majors"]
    assert slot["uni_id"] == 1
    assert slot["meets_req"] is True


def test_p2_group_by_school_filters_non_university_keywords():
    """非大学机构（如语言学校）被排除，不出现在聚合结果中。"""
    rows = [
        {"country": "英国", "university": "伦敦某语言学院", "university_id": 100,
         "_gpa4": 3.0, "_meets_req": True, "_strict_meets": True, "_req_value": None,
         "_tier_diff": 0, "admitted_major": "English"},
        {"country": "英国", "university": "UCL", "university_id": 101,
         "_gpa4": 3.5, "_meets_req": True, "_strict_meets": True, "_req_value": None,
         "_tier_diff": 0, "admitted_major": "CS"},
    ]
    grouped = cm._group_by_school(rows, gpa_percent=80.0, gpa4=3.5, tier_key="985", uni_requirements={})
    assert "UCL" in grouped["英国"]
    assert "伦敦某语言学院" not in grouped["英国"]


def test_p2_group_by_school_unknown_country_when_missing():
    """案例 country 字段缺失 → dict.get 回退到默认 "未知"。"""
    # 注：r.get("country", "未知") 只在 key 缺失时回退；country=None 时取 None 本身。
    rows = [
        {"university": "Unknown U", "university_id": None,
         "_gpa4": 3.0, "_meets_req": True, "_strict_meets": True, "_req_value": None,
         "_tier_diff": 0, "admitted_major": "X"},
    ]
    grouped = cm._group_by_school(rows, gpa_percent=70.0, gpa4=3.0, tier_key="双非", uni_requirements={})
    assert "未知" in grouped
    assert "Unknown U" in grouped["未知"]


def test_p2_group_by_school_tracks_meets_req_flag():
    """只要任一案例未达要求，槽位 meets_req 即为 False。"""
    rows = [
        {"country": "美国", "university": "MIT", "university_id": 1,
         "_gpa4": 3.8, "_meets_req": True, "_strict_meets": True, "_req_value": 3.5,
         "_tier_diff": 0, "admitted_major": "CS"},
        {"country": "美国", "university": "MIT", "university_id": 1,
         "_gpa4": 3.2, "_meets_req": False, "_strict_meets": True, "_req_value": 3.5,
         "_tier_diff": 0, "admitted_major": "EE"},
    ]
    grouped = cm._group_by_school(rows, gpa_percent=80.0, gpa4=3.4, tier_key="985", uni_requirements={})
    assert grouped["美国"]["MIT"]["meets_req"] is False


def test_p2_group_by_school_empty_rows_returns_empty_dict():
    """空案例列表 → 空聚合（不抛错）。"""
    grouped = cm._group_by_school([], gpa_percent=70.0, gpa4=3.0, tier_key="211", uni_requirements={})
    assert grouped == {}


# ── 其他纯辅助函数 ──────────────────────────────────────────────────────────
def test_helper_get_gpa_tolerance_buckets():
    """_get_gpa_tolerance: 三档容差随 user_gpa4 单调递减。"""
    assert cm._get_gpa_tolerance(None) == 0.45
    assert cm._get_gpa_tolerance(2.0) == 0.55   # <2.5
    assert cm._get_gpa_tolerance(2.5) == 0.45   # 2.5~3.0 区间边界
    assert cm._get_gpa_tolerance(2.9) == 0.45
    assert cm._get_gpa_tolerance(3.0) == 0.40   # >=3.0
    assert cm._get_gpa_tolerance(4.0) == 0.40


def test_helper_tier_adjacent_same_tier():
    """同层级 → 相邻。"""
    assert cm._tier_adjacent(3, 3) is True


def test_helper_tier_adjacent_one_apart():
    """差 1 级 → 相邻。"""
    assert cm._tier_adjacent(3, 4) is True
    assert cm._tier_adjacent(4, 3) is True


def test_helper_tier_adjacent_two_apart_higher_user_allows():
    """差 2 级、用户层级更高（user_tier 数字更小）→ 允许匹配（向下兼容看更强案例）。

    源码注释："若用户层次更高则允许差2级" → user_tier < case_tier 判真。
    """
    assert cm._tier_adjacent(1, 3) is True  # 用户 tier=1，案例 tier=3


def test_helper_tier_adjacent_two_apart_lower_user_blocks():
    """差 2 级、用户层级更低（user_tier 数字更大）→ 不相邻。"""
    assert cm._tier_adjacent(3, 1) is False  # 用户 tier=3，案例 tier=1


def test_helper_tier_adjacent_three_apart_blocks():
    """差 3 级 → 不相邻。"""
    assert cm._tier_adjacent(1, 4) is False
    assert cm._tier_adjacent(4, 1) is False


def test_helper_normalize_tier_key_aggregates_985_family():
    """985 / 985+海本 / C9 / 海本 → "985"。"""
    assert cm._normalize_tier_key("985") == "985"
    assert cm._normalize_tier_key("985/海本") == "985"
    assert cm._normalize_tier_key("C9") == "985"
    assert cm._normalize_tier_key("海本") == "985"


def test_helper_normalize_tier_key_211_standalone():
    """211 → "211"。"""
    assert cm._normalize_tier_key("211") == "211"


def test_helper_normalize_tier_key_other_falls_back_to_shuangfei():
    """其他未知 tier_label → "双非"（一本共用）。"""
    assert cm._normalize_tier_key("一本") == "双非"
    assert cm._normalize_tier_key("双非") == "双非"
    assert cm._normalize_tier_key("未知层级") == "双非"


def test_helper_target_major_to_category_recognizes_computer():
    """计算机相关专业 → "计算机"。"""
    assert cm._target_major_to_category("计算机科学") == "计算机"
    assert cm._target_major_to_category("Computer Science") == "计算机"
    assert cm._target_major_to_category("AI") == "计算机"


def test_helper_target_major_to_category_recognizes_finance():
    """金融相关专业 → "金融"。"""
    assert cm._target_major_to_category("金融工程") == "金融"
    assert cm._target_major_to_category("Finance") == "金融"


def test_helper_target_major_to_category_recognizes_business():
    """商科 → "商科"。

    不使用 "MBA"（"mba" 含 "ba" 子串冲突计算机关键词），改用中文显式标记。
    """
    assert cm._target_major_to_category("工商管理") == "商科"
    assert cm._target_major_to_category("人力资源管理") == "商科"


def test_helper_target_major_to_category_unknown_returns_none():
    """完全无法识别的目标专业 → None。"""
    assert cm._target_major_to_category(None) is None
    assert cm._target_major_to_category("") is None
    assert cm._target_major_to_category("zzzz_unknown_xyz") is None


def test_helper_expand_major_keywords_returns_dedup():
    """关键词展开去重且保留顺序，输入包含自身。"""
    kws = cm._expand_major_keywords("计算机")
    assert kws[0] == "计算机"
    assert "computer" in [k.lower() for k in kws]
    # 去重
    assert len(kws) == len(set(kws))


def test_helper_expand_major_keywords_unknown_major_only_self():
    """未命中任何分类时仅返回自身。"""
    kws = cm._expand_major_keywords("zzz_unknown_xyz")
    assert kws == ["zzz_unknown_xyz"]


# ── 跳过：依赖外部 DB/资源 的函数（占位说明覆盖范围） ────────────────────────
@pytest.mark.skip(reason="match_schools_by_background 依赖 sqlite3.Connection 与真实数据；不在纯函数测试范围")
def test_p2_match_schools_by_background_skipped():
    """占位：同背景匹配主流程依赖 DB，跳过。"""
    assert False, "此用例仅作 skip 占位，不应执行"


@pytest.mark.skip(reason="_classify_chance_major_aware 依赖 sqlite3.Connection；不在纯函数测试范围")
def test_p2_classify_chance_major_aware_skipped():
    """占位：专业感知分档依赖 DB 百分位，跳过。"""
    assert False, "此用例仅作 skip 占位，不应执行"


@pytest.mark.skip(reason="_get_major_percentiles 依赖 sqlite3.Connection；不在纯函数测试范围")
def test_p2_get_major_percentiles_skipped():
    """占位：专业百分位查询依赖 DB，跳过。"""
    assert False, "此用例仅作 skip 占位，不应执行"


@pytest.mark.skip(reason="_filter_and_score 依赖 normalize_gpa / classify_school_tier 等被测方外部工具；走集成测试更合适")
def test_p2_filter_and_score_skipped():
    """占位：候选评分过滤依赖外部稳定工具的输入构造，跳过。"""
    assert False, "此用例仅作 skip 占位，不应执行"


@pytest.mark.skip(reason="_enrich_with_ranking 依赖 sqlite3.Connection；不在纯函数测试范围")
def test_p2_enrich_with_ranking_skipped():
    """占位：补充排名依赖 DB，跳过。"""
    assert False, "此用例仅作 skip 占位，不应执行"


@pytest.mark.skip(reason="_build_response 内部调用 _get_major_percentiles（依赖 DB）；不在纯函数测试范围")
def test_p2_build_response_skipped():
    """占位：响应构建依赖专业百分位查询，跳过。"""
    assert False, "此用例仅作 skip 占位，不应执行"