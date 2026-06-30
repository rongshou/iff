import sqlite3
from collections import defaultdict
from typing import Optional

from ..utils.gpa import normalize_gpa, GPA_FORMAT_ALIASES
from ..utils.tier import classify_school_tier, get_tier_label
from .gpa_requirement import meets_requirement
from .probability import classify_admission_chance, get_school_percentiles

COUNTRY_RANK_FIELD = {
    "英国": "qs_rank", "美国": "usnews_rank", "澳大利亚": "qs_rank",
    "加拿大": "qs_rank", "中国香港": "qs_rank", "新加坡": "qs_rank",
    "日本": "qs_rank", "韩国": "qs_rank", "中国澳门": "qs_rank",
    "新西兰": "qs_rank", "爱尔兰": "qs_rank", "德国": "qs_rank",
    "法国": "qs_rank", "荷兰": "qs_rank", "瑞士": "qs_rank",
    "瑞典": "qs_rank", "丹麦": "qs_rank", "意大利": "qs_rank",
    "西班牙": "qs_rank", "马来西亚": "qs_rank",
}

MAX_SCHOOLS_PER_COUNTRY = 15

# 非大学机构关键词 - 排除语言学校/教育局/中学
NON_UNIVERSITY_KEYWORDS = [
    "语言学院", "语言学校", "语言中心", "语言课程",
    "教育局", "中学", "高中", "国际学校",
    "培训", "补习", "私塾", "专门学校",
    "国际学院", "预科", "校区",
]

MAJOR_KEYWORD_EXPANSION = {
    "计算机": ["computer", "computing", "software", "软件", "data science", "数据科学",
               "artificial intelligence", "ai", "machine learning", "机器学习", "cyber",
               "information technology", "informatics", "信息", "编程",
               "ds", "ba", "hci", "cse", "ece", "cs", "se", "it"],
    "金融": ["金融", "finance", "accounting", "会计", "account", "banking", "银行",
             "investment", "投资", "insurance", "保险", "actuarial", "精算", "经济", "economics", "econ",
             "fe", "mfe", "quant"],
    "商科": ["business", "management", "商", "mba", "管理", "行政", "marketing", "市场",
             "人力资源", "hr", "logistics", "物流", "供应链", "supply chain", "enterprise", "创业",
             "mis", "information system", "信息系统"],
    "工程": ["engineer", "工程", "mechanical", "机械", "civil", "土木", "electronic", "电气",
             "electrical", "aerospace", "航空", "chemical", "化工", "材料", "materials",
             "建筑", "architecture", "环境", "environmental", "制造",
             "ee", "me", "ce", "ieor", "or", "运筹"],
    "教育": ["education", "教育", "teaching", "教学", "tesol", "pedagogy", "师范", "双语"],
    "传媒": ["media", "传媒", "communication", "传播", "新闻", "journalism", "广告", "advertising",
             "public relation", "公关", "电影", "film", "design", "设计", "创意",
             "imc", "digital media", "新传"],
    "法律": ["law", "法律", "法学", "llm", "jd", "political", "政治", "国际关系",
             "public policy", "公共政策", "社会学", "sociology", "social work",
             "mpp", "mpa"],
    "医学": ["medicine", "医学", "临床", "clinical", "护理", "nursing", "pharmacy", "药学",
             "public health", "公共卫生", "nutrition", "营养", "生物", "biology",
             "mph", "biostat", "生物统计"],
    "数学": ["mathematics", "数学", "math", "统计", "statistics", "actuarial", "精算", "运筹",
             "applied math", "应数"],
    "艺术": ["art", "艺术", "music", "音乐", "fine art", "visual", "表演", "fashion", "时尚",
             "交互设计", "interaction design", "ux", "平面设计", "graphic design"],
}


from .case_utils import (
    _expand_major_keywords,
    _target_major_to_category,
    _normalize_tier_key,
    _get_major_percentiles,
    _classify_chance_major_aware,
    _score_school_3d,
    _calculate_gpa_gap,
    _query_cases,
    _expand_countries,
    _fetch_university_requirements,
    _get_gpa_tolerance,
    _tier_adjacent,
)

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
    rows = conn.execute(
        f"SELECT id, qs_rank, usnews_rank, the_rank FROM universities WHERE id IN ({ph})",
        id_list,
    ).fetchall()
    rank_map = {r["id"]: {"qs_rank": r["qs_rank"], "usnews_rank": r["usnews_rank"], "the_rank": r["the_rank"]} for r in rows}

    # D: 查每个学校所有录取案例的真实 GPA（不受过滤容差限制）
    gpa_rows = conn.execute(
        f"""SELECT c.university_id, c.gpa_score, c.gpa_format
            FROM cases c
            WHERE c.university_id IN ({ph})
              AND c.gpa_score IS NOT NULL
              AND c.gpa_format IS NOT NULL
              AND c.gpa_format NOT IN ('英制百分制', '学位等级对应分数', '中国高考')
              AND c.study_level NOT IN ('中学', '语言课程', '专科/职业学院', '预科')""",
        id_list,
    ).fetchall()

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
    """三维评分模型构建输出: 冲刺/匹配/安全 各最多 6 所, 档内按 QS 排名排序."""
    MAX_PER_TIER = 6
    TIER_ORDER = {"冲刺": 0, "匹配": 1, "安全": 2}

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

        school_list = []
        for uni_name, slot in schools.items():
            qs_rank = slot.get(rank_field)
            if qs_rank is None or qs_rank == 0:
                qs_rank = 9999

            # GPA 百分位: 优先专业级 → 学校级回退
            school_percentiles = None
            if major_category:
                tier_key = _normalize_tier_key(tier_label)
                school_percentiles = _get_major_percentiles(conn, uni_name, major_category, tier_key)
            if not school_percentiles:
                school_percentiles = get_school_percentiles(uni_name, tier_label)

            p50_ref = school_percentiles.get("p50") if school_percentiles else None
            case_count = len(slot["cases"])

            # ── 三维评分 + 分档 ──
            gpa_score, rank_score, evidence_score, total, tier = _score_school_3d(
                school_percentiles, qs_rank, case_count, gpa_percent,
            )

            # ── 冲刺校 GPA 提升建议 ──
            gpa_gap = None
            if tier == "冲刺":
                gpa_gap = _calculate_gpa_gap(
                    school_percentiles, gpa_percent,
                    gpa_score, rank_score, evidence_score,
                )

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
        for tier_name in ("冲刺", "匹配", "安全"):
            group = by_tier.get(tier_name, [])
            selected.extend(group[:MAX_PER_TIER])

        # 最终排序: 冲刺 → 匹配 → 安全, 每档内 QS 排名升序
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
