import sqlite3
from collections import defaultdict
from typing import Optional

from ..utils.gpa import normalize_gpa, GPA_FORMAT_ALIASES
from ..utils.tier import classify_school_tier, get_tier_label
from .gpa_requirement import meets_requirement
from .probability import get_school_percentiles

from ..repositories import CaseRepository
from ..core.config import settings
from .case_utils import (
    COUNTRY_RANK_FIELD,
    NON_UNIVERSITY_KEYWORDS,
    _expand_major_keywords,
    _target_major_to_category,
    _normalize_tier_key,
    _get_major_percentiles,
    _get_major_percentiles_batch,
    _classify_chance_major_aware,
    _score_school_3d,
    _calculate_gpa_gap,
    _query_cases,
    _expand_countries,
    _fetch_university_requirements,
    _get_gpa_tolerance,
    _tier_adjacent,
)


_repo: CaseRepository | None = None
def _get_repo() -> CaseRepository:
    global _repo
    if _repo is None:
        _repo = CaseRepository(str(settings.DB_PATH))
    return _repo

def match_schools_by_background(
    conn: sqlite3.Connection,
    countries: list[str],
    gpa_score: float,
    gpa_format: str,
    study_level: str,
    target_major: Optional[str],
    original_major: Optional[str],
    undergrad_school: Optional[str],
) -> dict:
    gpa_percent, user_gpa4 = normalize_gpa(gpa_score, gpa_format, undergrad_school)
    user_tier, user_tier_label = classify_school_tier(undergrad_school)
    tier_key = get_tier_label(user_tier)

    rows = _query_cases(conn, countries, study_level, target_major)

    uni_requirements = _fetch_university_requirements(conn, rows)

    matched = _filter_and_score(
        rows, user_gpa4, user_tier, original_major,
        gpa_percent or 0, tier_key, uni_requirements,
    )

    result = _group_by_school(matched, gpa_percent or 0, user_gpa4 or 0, tier_key, uni_requirements)

    result = _enrich_with_ranking(conn, result, countries)

    return _build_response(result, countries, gpa_percent or 0, user_tier_label, conn, target_major)


def _filter_and_score(
    rows: list[dict],
    user_gpa4: Optional[float],
    user_tier: int,
    original_major: Optional[str],
    gpa_percent: float,
    tier_key: str,
    uni_requirements: dict,
) -> list[dict]:
    matched = []
    gpa_tolerance = _get_gpa_tolerance(user_gpa4)

    for r in rows:
        case_tier = None
        tier_diff = 0
        if r.get("undergraduate_school"):
            case_tier, _ = classify_school_tier(r["undergraduate_school"])
            tier_diff = abs(user_tier - case_tier) if case_tier is not None else 0

        # 允许同层次 + 相邻层次 (差1级) 的案例匹配
        if case_tier is not None and not _tier_adjacent(user_tier, case_tier):
            continue

        gpa_score = r.get("gpa_score")
        gpa_format = r.get("gpa_format", "")
        try:
            score = float(gpa_score) if gpa_score else None
        except (ValueError, TypeError):
            continue

        if score is None:
            continue

        fmt = GPA_FORMAT_ALIASES.get((gpa_format or "").strip(), gpa_format or "")
        if fmt in ("英制百分制", "学位等级对应分数", "中国高考"):
            continue

        _, case_gpa4 = normalize_gpa(score, fmt)
        if case_gpa4 is None:
            continue

        if user_gpa4 is not None and abs(case_gpa4 - user_gpa4) > gpa_tolerance:
            continue

        # 跨专业匹配：仅当用户明确指定了本科专业和目标专业时才过滤
        if original_major:
            case_orig = r.get("original_major") or ""
            if case_orig and original_major not in case_orig and case_orig not in original_major:
                # 如果案例中有跨专业案例（原专业≠录取专业），不排除
                admitted = r.get("admitted_major") or ""
                if original_major not in admitted:
                    continue

        uni_id = r.get("university_id")
        req_str = uni_requirements.get(uni_id)
        meets, close, req_val = meets_requirement(gpa_percent, user_gpa4 or 0, req_str, tier_key)

        # 双 pass: 先用宽松标准收集，后续在 _group_by_school 中排序
        # 标记是否严格符合要求
        r["_strict_meets"] = meets

        if req_val is not None:
            if req_val > 10:
                gap = (gpa_percent - req_val) / req_val * 100
            else:
                gap = ((user_gpa4 or 0) - req_val) / req_val * 100 if req_val else 100
            # 极严过滤：差距超过 30% 才排除
            if gap < -30:
                continue

        r["_gpa4"] = case_gpa4
        r["_meets_req"] = meets
        r["_close_req"] = close
        r["_req_value"] = req_val
        r["_tier_diff"] = tier_diff
        matched.append(r)

    return matched


def _group_by_school(
    rows: list[dict],
    gpa_percent: float,
    gpa4: float,
    tier_key: str,
    uni_requirements: dict,
) -> dict:
    by_country: dict = defaultdict(
        lambda: defaultdict(
            lambda: {"cases": [], "gpas": [], "majors": set(), "uni_id": None,
                     "meets_req": True, "strict_meets": True, "req_value": None,
                     "tier_diffs": []}
        )
    )

    for r in rows:
        country = r.get("country", "未知")
        uni_name = r.get("university", "未知")
        uni_id = r.get("university_id")

        # 跳过非大学机构
        if any(kw in uni_name for kw in NON_UNIVERSITY_KEYWORDS):
            continue

        slot = by_country[country][uni_name]
        if uni_id and not slot["uni_id"]:
            slot["uni_id"] = uni_id
        slot["cases"].append(r)

        if not r.get("_meets_req"):
            slot["meets_req"] = False
        if not r.get("_strict_meets", True):
            slot["strict_meets"] = False
        slot["req_value"] = r.get("_req_value")
        td = r.get("_tier_diff", 0)
        if td is not None:
            slot["tier_diffs"].append(td)

        gpa = r.get("_gpa4")
        if gpa is not None:
            slot["gpas"].append(gpa)

        major = r.get("admitted_major", "")
        if major:
            slot["majors"].add(major)

    return by_country


def _enrich_with_ranking(
    conn: sqlite3.Connection, by_country: dict, target_countries: list[str],
) -> dict:
    all_ids = set()
    for schools in by_country.values():
        for slot in schools.values():
            if slot["uni_id"]:
                all_ids.add(slot["uni_id"])

    if not all_ids:
        return by_country

    id_list = list(all_ids)
    ph = ",".join("?" for _ in id_list)
    rows = _get_repo().fetch_ranking_batch(id_list)
    rank_map = {r["id"]: {"qs_rank": r["qs_rank"], "usnews_rank": r["usnews_rank"], "the_rank": r["the_rank"]} for r in rows}

    # D: 查每个学校所有录取案例的真实 GPA（不受过滤容差限制）
    gpa_rows = _get_repo().fetch_case_gpa_batch(id_list)

    all_gpas_by_uni: dict = defaultdict(list)
    for r in gpa_rows:
        try:
            score = float(r["gpa_score"])
        except (ValueError, TypeError):
            continue
        fmt = GPA_FORMAT_ALIASES.get((r["gpa_format"] or "").strip(), r["gpa_format"] or "")
        if fmt in ("英制百分制", "学位等级对应分数", "中国高考"):
            continue
        _, g4 = normalize_gpa(score, fmt)
        if g4:
            all_gpas_by_uni[r["university_id"]].append(g4)

    for country, schools in by_country.items():
        for slot in schools.values():
            r = rank_map.get(slot["uni_id"], {})
            slot["qs_rank"] = r.get("qs_rank")
            slot["usnews_rank"] = r.get("usnews_rank")
            slot["the_rank"] = r.get("the_rank")
            slot["majors"] = list(slot["majors"])[:5]
            slot["all_gpas"] = all_gpas_by_uni.get(slot["uni_id"], [])

    return by_country


def _build_response(by_country: dict, target_countries: list[str], gpa_percent: float, tier_label: str, conn: sqlite3.Connection, target_major: Optional[str] = None) -> dict:
    """三维评分模型构建输出: 冲刺/匹配/保底 各最多 6 所, 档内按 QS 排名排序."""
    MAX_PER_TIER = 6
    TIER_ORDER = {"冲刺": 0, "匹配": 1, "保底": 2}

    result_countries = []

    for country_name in target_countries:
        if country_name not in by_country:
            result_countries.append({
                "country": country_name, "matched_cases": 0,
                "matched_schools": 0, "schools": [],
            })
            continue

        schools = by_country[country_name]
        rank_field = COUNTRY_RANK_FIELD.get(country_name, "qs_rank")

        # 预查专业级 GPA 百分位（同 target_major 只查一次 taxonomy）
        major_category = _target_major_to_category(target_major)

        # 批量查询所有学校的专业级百分位（消除 N+1）
        major_percentiles_batch: dict[str, dict] = {}
        if major_category:
            tier_key = _normalize_tier_key(tier_label)
            all_uni_names = list(schools.keys())
            major_percentiles_batch = _get_major_percentiles_batch(
                conn, all_uni_names, major_category, tier_key
            )

        school_list = []
        for uni_name, slot in schools.items():
            qs_rank = slot.get(rank_field)
            if qs_rank is None or qs_rank == 0:
                qs_rank = 9999

            # GPA 百分位: 优先专业级（批量查得）→ 学校级回退
            school_percentiles = major_percentiles_batch.get(uni_name)
            if not school_percentiles:
                school_percentiles = get_school_percentiles(uni_name, tier_label, conn=conn)

            p50_ref = school_percentiles.get("p50") if school_percentiles else None
            p25_ref = school_percentiles.get("p25") if school_percentiles else None
            case_count = len(slot["cases"])

            # ── 学校级合理性过滤 ──
            # 用户百分位远低于学校中位数时，说明即使有少量案例匹配也只是统计噪音
            # 排除: 用户 GPA 低于 p50 超过 10 个百分点 且 案例数 < 3
            if p50_ref is not None and (gpa_percent < p50_ref - 10) and case_count < 3:
                continue
            # 排除: 用户 GPA 低于 p25 超过 8 个百分点 且 案例数 < 5
            if p25_ref is not None and (gpa_percent < p25_ref - 8) and case_count < 5:
                continue
            # 排除: 无百分位数据时，用户 GPA 远低于匹配案例中位数
            if not school_percentiles and slot.get("gpas"):
                matched_median = sorted(slot["gpas"])[len(slot["gpas"]) // 2]
                matched_pct = matched_median * 25  # 4.0 → 百分制估算
                if gpa_percent < matched_pct - 12 and case_count < 3:
                    continue

            # 学校 GPA 中位数（从匹配案例估算，用于无百分位数据时的回退）
            school_median_gpa = None
            if slot.get("gpas"):
                sorted_gpas = sorted(slot["gpas"])
                n = len(sorted_gpas)
                if n % 2 == 0:
                    school_median_gpa = (sorted_gpas[n // 2 - 1] + sorted_gpas[n // 2]) / 2
                else:
                    school_median_gpa = sorted_gpas[n // 2]

            # ── 三维评分 + 分档 ──
            gpa_score, rank_score, evidence_score, total, tier = _score_school_3d(
                school_percentiles, qs_rank, case_count, gpa_percent, school_median_gpa,
            )

            # ── 冲刺校 GPA 提升建议 ──
            gpa_gap = None
            if tier == "冲刺":
                gpa_gap = _calculate_gpa_gap(
                    school_percentiles, gpa_percent,
                    gpa_score, rank_score, evidence_score,
                )
                # GPA 要求相差 12 个百分点以上: 提升幅度过于巨大，不展示
                if gpa_gap is not None and gpa_gap > 12:
                    continue

            matched_gpas = slot["gpas"]

            school_list.append({
                "name": uni_name,
                "qs_rank": slot.get("qs_rank"),
                "usnews_rank": slot.get("usnews_rank"),
                "matched_cases": case_count,
                "gpa_min": round(min(matched_gpas), 2) if matched_gpas else None,
                "gpa_max": round(max(matched_gpas), 2) if matched_gpas else None,
                "gpa_p50": round(p50_ref, 1) if p50_ref else None,
                "majors": slot["majors"],
                "meets_requirement": slot["meets_req"],
                "requirement_value": slot.get("req_value"),
                "admission_chance": tier,
                "admission_score": round(total, 1),
                "p50_reference": p50_ref,
                "gpa_gap": gpa_gap,
                "_sort_rank": qs_rank,
            })

        # 按分档分组, 档内按 QS 排名升序排队, 每档最多 6 所
        by_tier: dict[str, list] = {}
        for s in school_list:
            by_tier.setdefault(s["admission_chance"], []).append(s)

        for group in by_tier.values():
            group.sort(key=lambda x: x["_sort_rank"] if x["_sort_rank"] else 9999)

        selected = []
        for tier_name in ("冲刺", "匹配", "保底"):
            group = by_tier.get(tier_name, [])
            selected.extend(group[:MAX_PER_TIER])

        # 最终排序: 冲刺 → 匹配 → 保底, 每档内 QS 排名升序
        selected.sort(key=lambda x: (
            TIER_ORDER.get(x["admission_chance"], 9),
            x["_sort_rank"] if x["_sort_rank"] else 9999,
        ))

        for s in selected:
            s.pop("_sort_rank", None)

        total_cases = sum(s["matched_cases"] for s in selected)

        result_countries.append({
            "country": country_name,
            "matched_cases": total_cases,
            "matched_schools": len(selected),
            "schools": selected,
        })

    return {"by_country": result_countries}
