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
]

MAJOR_KEYWORD_EXPANSION = {
    "计算机": ["computer", "computing", "software", "软件", "data science", "数据科学",
               "artificial intelligence", "ai", "machine learning", "机器学习", "cyber",
               "information technology", "informatics", "信息", "编程"],
    "金融": ["金融", "finance", "accounting", "会计", "account", "banking", "银行",
             "investment", "投资", "insurance", "保险", "actuarial", "精算", "经济", "economics", "econ"],
    "商科": ["business", "management", "商", "mba", "管理", "行政", "marketing", "市场",
             "人力资源", "hr", "logistics", "物流", "供应链", "supply chain", "enterprise", "创业"],
    "工程": ["engineer", "工程", "mechanical", "机械", "civil", "土木", "electronic", "电气",
             "electrical", "aerospace", "航空", "chemical", "化工", "材料", "materials",
             "建筑", "architecture", "环境", "environmental", "制造"],
    "教育": ["education", "教育", "teaching", "教学", "tesol", "pedagogy", "师范"],
    "传媒": ["media", "传媒", "communication", "传播", "新闻", "journalism", "广告", "advertising",
             "public relation", "公关", "电影", "film", "design", "设计", "创意"],
    "法律": ["law", "法律", "法学", "llm", "jd", "political", "政治", "国际关系",
             "public policy", "公共政策", "社会学", "sociology", "social work"],
    "医学": ["medicine", "医学", "临床", "clinical", "护理", "nursing", "pharmacy", "药学",
             "public health", "公共卫生", "nutrition", "营养", "生物", "biology"],
    "数学": ["mathematics", "数学", "math", "统计", "statistics", "actuarial", "精算", "运筹"],
    "艺术": ["art", "艺术", "music", "音乐", "fine art", "visual", "表演", "fashion", "时尚"],
}


def _expand_major_keywords(major: str) -> list[str]:
    keywords = [major]
    for cat, kws in MAJOR_KEYWORD_EXPANSION.items():
        if cat in major.lower() or major in cat or any(kw in major.lower() for kw in kws if len(kw) <= 4):
            keywords.extend(kws)
    return list(dict.fromkeys(keywords))


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

    return _build_response(result, countries, gpa_percent or 0, user_tier_label)


def _query_cases(
    conn: sqlite3.Connection,
    countries: list[str],
    study_level: str,
    target_major: Optional[str],
) -> list[dict]:
    conditions = []
    params: list = []

    if countries:
        expanded = _expand_countries(conn, countries)
        ph = ",".join("?" for _ in expanded)
        conditions.append(f"c.country IN ({ph})")
        params.extend(expanded)

    if study_level:
        conditions.append("c.study_level LIKE ?")
        params.append(f"%{study_level}%")

    # 排除非大学学位（中学/语言/专科）
    conditions.append("c.study_level NOT IN ('中学', '语言课程', '专科/职业学院', '预科')")

    if target_major:
        keywords = _expand_major_keywords(target_major)
        major_conds = []
        for kw in keywords:
            major_conds.append("c.admitted_major LIKE ?")
            params.append(f"%{kw}%")
        conditions.append(f"({' OR '.join(major_conds)})")

    where = " AND ".join(conditions) if conditions else "1=1"

    sql = f"""
        SELECT c.id, c.country, c.university, c.university_id,
               c.study_level, c.admitted_major, c.original_major,
               c.gpa_score, c.gpa_format,
               c.undergraduate_school, c.admission_time
        FROM cases c
        WHERE {where}
        LIMIT 80000
    """
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def _expand_countries(conn: sqlite3.Connection, countries: list[str]) -> list[str]:
    expanded = set()
    country_map = {}
    rows = conn.execute(
        "SELECT DISTINCT country FROM cases WHERE country IS NOT NULL"
    ).fetchall()
    for r in rows:
        cn = r["country"]
        if cn:
            country_map[cn] = cn

    for c in countries:
        expanded.add(c)
        for cn in country_map:
            if c in cn or cn in c:
                expanded.add(cn)
    return list(expanded)


def _fetch_university_requirements(
    conn: sqlite3.Connection, rows: list[dict],
) -> dict:
    uni_ids = list(set(r.get("university_id") for r in rows if r.get("university_id")))
    if not uni_ids:
        return {}

    ph = ",".join("?" for _ in uni_ids)
    req_rows = conn.execute(
        f"SELECT id, gpa_requirement FROM universities WHERE id IN ({ph})",
        uni_ids,
    ).fetchall()

    return {r["id"]: r["gpa_requirement"] for r in req_rows if r["gpa_requirement"]}


def _get_gpa_tolerance(user_gpa4: Optional[float]) -> float:
    """根据用户 GPA 动态调整匹配容差 — 高分用户放宽以获取更多参考案例"""
    if user_gpa4 is None:
        return 0.45
    if user_gpa4 < 2.5:
        return 0.55
    if user_gpa4 < 3.0:
        return 0.45
    return 0.40


def _tier_adjacent(user_tier: int, case_tier: int) -> bool:
    """层次匹配: 同级或相邻(≤1); 若用户层次更高则允许差2级"""
    diff = abs(case_tier - user_tier)
    if diff <= 1:
        return True
    if diff == 2 and user_tier < case_tier:
        return True
    return False


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
                     "meets_req": True, "strict_meets": True, "req_value": None}
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


def _adjust_chance_by_rank(school_list: list[dict], gpa_percent: float) -> None:
    """以 GPA 百分位分档为主，QS 排名作为名校下限保护。

    GPA 百分位（p25/p50/p75 来自 classify_admission_chance）是分档核心依据，
    QS 排名仅防止"名校保底"这种不合理结果：
      - QS≤30 顶尖名校：最低"冲刺"（即使 GPA 远超 p75 也不算保底）
      - QS≤50 名校：最低"匹配"
      - QS>50：完全按 GPA 百分位分档
    """
    chance_num = {"彩票": -1, "冲刺": 0, "匹配": 1, "安全": 2}
    num_chance = {-1: "彩票", 0: "冲刺", 1: "匹配", 2: "安全"}

    for s in school_list:
        rank = s["_sort_rank"]
        if rank >= 9999:
            continue  # 无排名保持 GPA 分档

        current = chance_num.get(s["admission_chance"])
        if current is None:
            continue  # 未知保持

        if rank <= 30:
            floor = 0  # 顶尖名校最低冲刺
        elif rank <= 50:
            floor = 1  # 名校最低匹配
        else:
            continue  # QS>50 完全按 GPA 百分位

        if current > floor:
            current = floor

        s["admission_chance"] = num_chance[current]


def _build_response(by_country: dict, target_countries: list[str], gpa_percent: float, tier_label: str) -> dict:
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

        school_list = []
        for uni_name, slot in schools.items():
            rank = slot.get(rank_field)
            if rank is None or rank == 0:
                rank = 9999

            chance_label, chance_score, p50_ref, prob_n = classify_admission_chance(
                gpa_percent, uni_name, tier_label,
            )

            # D: GPA 展示用匹配案例区间 + 该校录取 GPA 中位数(p50)
            all_gpas = slot.get("all_gpas", [])
            matched_gpas = slot["gpas"]
            case_count = len(slot["cases"])

            import math
            strict_bonus = 1.2 if slot.get("strict_meets", True) else 1.0
            composite = math.sqrt(max(case_count, 1)) * chance_score * strict_bonus

            # 获取 p25/p75 用于 A 的 QS 排名调整
            perc = get_school_percentiles(uni_name, tier_label)
            p25 = perc.get("p25") if perc else None
            p75 = perc.get("p75") if perc else None

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
                "admission_chance": chance_label,
                "admission_score": round(chance_score, 2),
                "p50_reference": p50_ref,
                "_strict_meets": slot.get("strict_meets", True),
                "_composite": composite,
                "_sort_rank": rank,
                "_p25": p25,
                "_p75": p75,
            })

        # A: 结合 QS 排名和 GPA 重新分档
        _adjust_chance_by_rank(school_list, gpa_percent)

        # C: 每档最多 8 所（按综合评分排序），不硬编码 3-7-2
        chance_order = {"冲刺": 0, "匹配": 1, "安全": 2, "彩票": 3, "未知": 4}
        by_chance: dict[str, list] = {}
        for s in school_list:
            by_chance.setdefault(s["admission_chance"], []).append(s)
        for group in by_chance.values():
            group.sort(key=lambda x: -x["_composite"])

        MAX_PER_CHANCE = 8
        selected = []
        for chance in ("冲刺", "匹配", "安全", "彩票", "未知"):
            selected.extend(by_chance.get(chance, [])[:MAX_PER_CHANCE])

        # 按档位+QS排名排序
        selected.sort(key=lambda x: (chance_order.get(x["admission_chance"], 9), x["_sort_rank"]))

        for s in selected:
            for key in ("_sort_rank", "_strict_meets", "_composite", "_p25", "_p75"):
                s.pop(key, None)

        total_cases = sum(s["matched_cases"] for s in selected)

        result_countries.append({
            "country": country_name,
            "matched_cases": total_cases,
            "matched_schools": len(selected),
            "schools": selected,
        })

    return {"by_country": result_countries}
