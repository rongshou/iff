import sqlite3
from typing import Optional

from ..utils.tier import classify_school_tier, get_tier_label
from .gpa_requirement import meets_requirement
from .probability import classify_admission_chance, get_school_percentiles
from ..core.config import settings
from ..repositories import CaseRepository

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


def _expand_major_keywords(major: str) -> list[str]:
    keywords = [major]
    for cat, kws in MAJOR_KEYWORD_EXPANSION.items():
        if cat in major.lower() or major in cat or any(kw in major.lower() for kw in kws if len(kw) <= 4):
            keywords.extend(kws)
    return list(dict.fromkeys(keywords))


def _target_major_to_category(target_major: Optional[str]) -> Optional[str]:
    """用户目标专业 -> 10 大专业类别之一(用于专业级 GPA 百分位查询)。"""
    if not target_major:
        return None
    low = target_major.lower()
    scores: dict[str, int] = {}
    for cat, kws in MAJOR_KEYWORD_EXPANSION.items():
        if cat in low or cat in target_major:
            scores[cat] = scores.get(cat, 0) + 5
        for kw in kws:
            if kw.lower() in low:
                scores[cat] = scores.get(cat, 0) + 1
                break
    if not scores:
        return None
    return max(scores, key=scores.get)


def _normalize_tier_key(tier_label: str) -> str:
    """tier_label(985/海本/C9/211/一本/双非...) -> 聚合表用的 985/211/双非。"""
    if tier_label in ("985", "985/海本", "C9", "海本"):
        return "985"
    if tier_label == "211":
        return "211"
    # 一本和双非共用同样的百分位数据
    return "双非"



_repo: CaseRepository | None = None
def _get_repo() -> CaseRepository:
    global _repo
    if _repo is None:
        _repo = CaseRepository(str(settings.DB_PATH))
    return _repo

def _get_major_percentiles(
    conn: sqlite3.Connection, university: str, major_category: str, tier_key: str,
) -> Optional[dict]:
    """从 school_major_gpa_percentiles 查专业级 GPA 百分位。"""
    row = _get_repo().get_major_percentiles(university, major_category, tier_key)
    if not row:
        return None
    return {"n": row["n"], "p10": row["p10"], "p25": row["p25"], "p50": row["p50"], "p75": row["p75"]}


def _get_major_percentiles_batch(
    conn: sqlite3.Connection, universities: list[str], major_category: str, tier_key: str,
) -> dict[str, dict]:
    """批量获取多所院校的专业级 GPA 百分位（消除 N+1）。"""
    return _get_repo().get_major_percentiles_batch(universities, major_category, tier_key)


# 专业 GPA 敏感度: 理工科 GPA 决定性强=1.0, 文商科 GPA 非决定性<1.0
# 阈值下移 (1-s)*区间宽度, 使文商科分档更宽松(贴合"GPA 非唯一因素"的现实)
# s<0.7 的专业: "彩票"档升级为"冲刺"(GPA 不够但其他因素可能弥补, 保留机会)
MAJOR_GPA_SENSITIVITY = {
    "计算机": 1.0, "工程": 1.0, "数学": 1.0, "医学": 1.0,
    "商科": 0.9,
    "金融": 0.6,
    "法律": 0.6,
    "教育": 0.65, "传媒": 0.65, "艺术": 0.65,
}


def _classify_chance_major_aware(
    conn: sqlite3.Connection,
    gpa_percent: float,
    uni_name: str,
    target_major: Optional[str],
    tier_label: str,
) -> tuple[str, float, Optional[float], Optional[float]]:
    """GPA 分档: 优先用专业级百分位(同校不同专业 GPA 要求不同),
    回退到学校级 real_case_probability.json。
    文商科(MAJOR_GPA_SENSITIVITY<1.0)按敏感度放宽门槛。"""
    category = _target_major_to_category(target_major)
    if category:
        tier_key = _normalize_tier_key(tier_label)
        perc = _get_major_percentiles(conn, uni_name, category, tier_key)
        if perc and perc["p25"] and perc["p50"] and perc["p75"]:
            p10, p25, p50, p75 = perc["p10"], perc["p25"], perc["p50"], perc["p75"]
            n = perc["n"]
            s = MAJOR_GPA_SENSITIVITY.get(category, 1.0)
            # 敏感度<1.0: 门槛下移, 放宽文商科分档
            safe_thr = p75 - (1 - s) * (p75 - p50)
            match_thr = p50 - (1 - s) * (p50 - p25)
            reach_thr = p25 - (1 - s) * (p25 - p10) if (p10 and p25 > p10) else p25
            if gpa_percent >= safe_thr:
                return "安全", 0.92, p50, n
            if gpa_percent >= match_thr:
                ratio = (gpa_percent - match_thr) / (safe_thr - match_thr) if safe_thr > match_thr else 0.5
                return "匹配", 0.55 + ratio * 0.35, p50, n
            if gpa_percent >= reach_thr:
                ratio = (gpa_percent - reach_thr) / (match_thr - reach_thr) if match_thr > reach_thr else 0.5
                return "冲刺", 0.25 + ratio * 0.30, p50, n
            # 低敏感度文商科: GPA 不够但其他因素可能弥补, "彩票"升级"冲刺"
            if s < 0.7:
                return "冲刺", 0.15, p50, n
            return "彩票", 0.15, p50, n
    return classify_admission_chance(gpa_percent, uni_name, tier_label)


# ── 三维评分模型 ──
# 总分 = GPA匹配分(40) + 学校排名分(30) + 案例证据分(20)
# ≥75 = 安全 | 55-74 = 匹配 | <55 = 冲刺

QS_RANK_BANDS = [
    (20, 18),   # QS 1-20: 顶级校, 低基础分 → 偏冲刺
    (50, 22),   # QS 21-50
    (100, 25),  # QS 51-100
    (200, 28),  # QS 101-200
]


def _score_school_3d(
    school_percentiles: Optional[dict],
    qs_rank: Optional[int],
    case_count: int,
    gpa_percent: float,
) -> tuple[float, float, float, float, str]:
    """三维评分: 返回 (gpa_score, rank_score, evidence_score, total, tier)."""
    # ── 维度一: GPA 匹配分 (0-40) ──
    if school_percentiles:
        p25 = school_percentiles.get("p25")
        p50 = school_percentiles.get("p50")
        p75 = school_percentiles.get("p75")
        if p50 is not None and p75 is not None and p25 is not None and p75 > p25:
            if gpa_percent >= p75:
                gpa_score = 40.0
            elif gpa_percent >= p50:
                gpa_score = 24.0 + 16.0 * (gpa_percent - p50) / (p75 - p50)
            elif gpa_percent >= p25:
                gpa_score = 8.0 + 16.0 * (gpa_percent - p25) / (p50 - p25)
            else:
                gpa_score = max(0.0, 8.0 * gpa_percent / p25)
        elif p50 is not None:
            # 仅 p50 可用时用简单分档
            if gpa_percent >= p50:
                gpa_score = 40.0
            elif gpa_percent >= p50 * 0.85:
                gpa_score = 24.0
            elif gpa_percent >= p50 * 0.70:
                gpa_score = 12.0
            else:
                gpa_score = 4.0
        else:
            gpa_score = 20.0
    else:
        gpa_score = 20.0  # 无百分位数据, 中性分

    # ── 维度二: 学校排名分 (0-30) ──
    # 排名越靠前(数字越小) → 基础分越低 → 天然偏冲刺
    if qs_rank and qs_rank <= 9998:
        rank_score = 30.0  # default for QS 200+
        for threshold, score in QS_RANK_BANDS:
            if qs_rank <= threshold:
                rank_score = float(score)
                break
    else:
        rank_score = 30.0  # 无 QS → 最高基础分(低门槛)

    # ── 维度三: 案例证据分 (0-20) ──
    # 案例多 → 置信度高 → 更高分（方向不变，上限收紧）
    if case_count >= 16:
        evidence_score = 20.0
    elif case_count >= 6:
        evidence_score = 13.0
    elif case_count >= 1:
        evidence_score = 7.0
    else:
        evidence_score = 0.0

    total = gpa_score + rank_score + evidence_score

    # 档位阈值（证件分降低后保持原阈值，冲刺档自然出现）
    if total >= 75:
        tier = "安全"
    elif total >= 55:
        tier = "匹配"
    else:
        tier = "冲刺"

    return gpa_score, rank_score, evidence_score, total, tier


def _calculate_gpa_gap(
    school_percentiles: Optional[dict],
    user_gpa_percent: float,
    gpa_score: float,
    rank_score: float,
    evidence_score: float,
) -> Optional[float]:
    """冲刺校: 计算 GPA 需提升多少百分点才能进入匹配档(总分≥55)."""
    if not school_percentiles:
        return None
    p25 = school_percentiles.get("p25")
    p50 = school_percentiles.get("p50")
    p75 = school_percentiles.get("p75")
    if not all([p25, p50, p75]) or p75 <= p25:
        return None

    matching_target = 55.0
    gpa_needed = max(0.0, matching_target - rank_score - evidence_score)

    if gpa_needed <= 8.0:
        needed_percent = (gpa_needed / 8.0) * p25
    elif gpa_needed <= 24.0:
        needed_percent = p25 + (gpa_needed - 8.0) * (p50 - p25) / 16.0
    elif gpa_needed <= 40.0:
        needed_percent = p50 + (gpa_needed - 24.0) * (p75 - p50) / 16.0
    else:
        needed_percent = p75 + 5.0

    gap = needed_percent - user_gpa_percent
    return round(max(0.0, gap), 1)


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
            safe_kw = kw.replace("%", r"\%").replace("_", r"\_")
            major_conds.append("c.admitted_major LIKE ? ESCAPE '\\'")
            params.append(f"%{safe_kw}%")
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
    return _get_repo().query_cases(sql, params)


def _expand_countries(conn: sqlite3.Connection, countries: list[str]) -> list[str]:
    expanded = set()
    country_map = {}
    all_db_countries = _get_repo().expand_countries()
    for cntry in all_db_countries:
        cn = cntry
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
    req_map = _get_repo().fetch_university_requirements(tuple(uni_ids))
    return {k: v for k, v in req_map.items() if v}


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


