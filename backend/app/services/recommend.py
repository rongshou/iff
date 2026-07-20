import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from ..core.database import get_db
from ..utils.gpa import normalize_gpa
from ..utils.tier import classify_school_tier
from .case_matcher import match_schools_by_background
from .pathway_service import find_pathway_suggestions
from .school_engine import enhance_with_rules, generate_application_strategy, generate_background_improvement, generate_major_recommendations


# ── 知识库校名归一化 ──
# handbook_texts 中的校名 → universities 表校名
_HANDBOOK_NAME_MAP = {
    "伊利诺伊大学厄巴纳-香槟分校": "伊利诺伊大学厄巴纳香槟分校",
}


def _normalize_school_name(name: str) -> str:
    """归一化校名以便在知识库中检索（去连字符、全半角括号转换）。"""
    return _HANDBOOK_NAME_MAP.get(name, name.replace("-", "").replace("（", "(").replace("）", ")"))


# ── 知识库原文消化分类器 ──
# 关键词规则 → 分类
_KB_CLASSIFIERS = [
    # 分数要求
    (["不低于", "要求", "minimum", "required", "总分", "以上", "需达到", "score of"],
     "score_requirements"),
    # 单项要求
    (["口语", "写作", "阅读", "听力", "section", "单项"],
     "section_requirements"),
    # 政策/豁免
    (["豁免", "waive", "免除", "免提交", "免考", "exception", "conditions"],
     "policies"),
    # 申请建议
    (["建议", "推荐", "建议申请", "advisable", "should", "tip", "攻略"],
     "application_notes"),
]


def _classify_toefl_text(text: str) -> str:
    """根据文本内容分类托福信息类型。"""
    text_lower = text.lower()
    for keywords, category in _KB_CLASSIFIERS:
        for kw in keywords:
            if kw in text_lower or kw in text:
                return category
    return "references"


def _extract_toefl_scores(text: str) -> list[dict]:
    """从文本中提取具体的托福分数信息。"""
    results = []
    # 匹配含 TOEFL 关键词 + 附近 2-3 位数字（允许中间有其他中文/英文词）
    text_clean = text.replace("\n", " ")
    patterns = [
        # "托福[要求|不低于|...]100[分]"  — 中文语境
        r'(?:托福|TOEFL|toefl)\s*(?:要求|不低于|需达|minimum|required|总分|score[s]?\s*of|成绩|达到|or higher|[和到至])*\s*[:：]?\s*(\d{2,3})(?:\s*(?:分|or|以上|or more))?',
        # "80 or higher on the TOEFL"  — 英文语境
        r'(\d{2,3})\s*(?:or\s+higher|or\s+more|and\s+above)\s+(?:on\s+the)?\s*(?:TOEFL|toefl)',
        # "100分以上" / "100 分"（纯数字后跟分）
        r'(?<![.\d])(\d{2,3})\s*分',
        # total score of X
        r'total\s+score\s+(?:of\s+)?(\d{2,3})',
    ]
    seen = set()
    for pat in patterns:
        for m in re.finditer(pat, text_clean, re.IGNORECASE):
            score = int(m.group(1))
            if 60 <= score <= 120 and score not in seen:
                seen.add(score)
                results.append({"score": score, "matched": m.group(0).strip()})
    return results


def _detect_scoring(text: str, source: str = "") -> str:
    """判断文本属于旧托福(0-120)、新托福(1-6)还是不确定。
    handbook 来源默认为旧托福。"""
    if "新托福" in text:
        return "new"
    # 匹配 TOEFL 相关的 2-3 位数字（允许中间有其他中文/英文词）
    scores_old = re.findall(
        r'(?:托福|TOEFL|toefl)\s*(?:要求|不低于|需达|minimum|required|总分|score[s]?\s*of|成绩|达到|or higher|[和到至])*\s*[:：]?\s*(\d{2,3})\s*(?:分|or|以上)',
        text, re.IGNORECASE)
    for s in scores_old:
        val = int(s)
        if 60 <= val <= 120:
            return "old"
    # 新托福 1-6 含小数点
    scores_new = re.findall(r'(?:托福|TOEFL)\s*(?:要求|不低于|需达|minimum|required|总分|score[s]?\s*of)?\s*[:：]?\s*(\d\.\d)', text, re.IGNORECASE)
    for s in scores_new:
        val = float(s)
        if 1.0 <= val <= 6.0:
            return "new"
    # 默认：handbook 来源 → old，其他 → 按 old 处理
    return "old"


def _digest_toefl_knowledge(conn, school_name: str) -> dict:
    """搜索全部知识库，消化托福信息为结构化洞察，区分新旧分制。

    返回格式:
    {
        "old": {                         # 旧托福 (0-120)
            "score_requirements": [...],
            "section_requirements": [...],
            "policies": [...],
            "application_notes": [...],
            "references": [...],
        },
        "new": {                         # 新托福 (1-6)
            ...同上...
        }
    }
    """
    # old / new 两个独立容器
    containers: dict[str, dict] = {"old": {}, "new": {}}

    def _add(scoring: str, category: str, entry: dict):
        if category not in containers[scoring]:
            containers[scoring][category] = []
        if not any(e.get("detail") == entry.get("detail") for e in containers[scoring][category]):
            containers[scoring][category].append(entry)

    norm = _normalize_school_name(school_name)
    prefix = norm[:4]

    # ── 1. handbook_fts 搜索（按 school 列精确匹配，均为旧托福）──
    for name_variant in [norm, f"{prefix}%"]:
        if name_variant == f"{prefix}%" and norm[:4] == prefix:
            if any(v.get("score_requirements") or v.get("section_requirements") for v in containers.values()):
                break
        rows = conn.execute(
            """SELECT snippet(handbook_fts, 2, '【【', '】】', '...', 80) as snip,
                      substr(content, 1, 500) as raw
               FROM handbook_fts
               WHERE school {} ? AND content MATCH 'TOEFL OR 托福'
               LIMIT 5""".format("=" if not name_variant.endswith("%") else "LIKE"),
            (name_variant,),
        ).fetchall()
        for snip, raw in rows:
            category = _classify_toefl_text(raw)
            entry = {"source": "handbook", "detail": snip}
            scores = _extract_toefl_scores(raw)
            if scores:
                entry["scores"] = scores
            # handbook 内容均为旧托福
            _add("old", category, entry)

    # ── 2. kb_processed 搜索（按 universities + 关键词），区分新/旧 ──
    for univ_pattern in [norm, norm.replace("(", "（").replace(")", "）"), school_name]:
        rows = conn.execute(
            """SELECT title, substr(clean_text, 1, 500) as excerpt
               FROM kb_processed
               WHERE universities LIKE ?
               AND (clean_text LIKE '%新托福%' OR clean_text LIKE '%托福%' OR clean_text LIKE '%TOEFL%')
               LIMIT 8""",
            (f'%{univ_pattern}%',),
        ).fetchall()
        if rows:
            break
    for title, excerpt in rows:
        scoring = _detect_scoring(excerpt)
        category = _classify_toefl_text(excerpt)
        detail = excerpt[:200].replace("\n", " ").strip()
        _add(scoring, category, {
            "source": "kb_article",
            "title": title,
            "detail": detail,
        })

    # ── 3. kb_chunks_fts 搜索 ──
    try:
        rows = conn.execute(
            """SELECT c.article_id, substr(c.content, 1, 300) as excerpt
               FROM kb_chunks c
               WHERE c.id IN (
                   SELECT rowid FROM kb_chunks_fts
                   WHERE content MATCH ?
               ) AND c.content LIKE ?
               LIMIT 3""",
            (f'"TOEFL" OR "托福" OR "新托福" OR "toefl"', f'%{norm[:4]}%'),
        ).fetchall()
        for article_id, excerpt in rows:
            a = conn.execute("SELECT title FROM kb_articles WHERE id = ?", (article_id,)).fetchone()
            title = a[0] if a else article_id
            scoring = _detect_scoring(excerpt)
            category = _classify_toefl_text(excerpt)
            _add(scoring, category, {
                "source": "kb_article",
                "title": title,
                "detail": excerpt[:200].replace("\n", " ").strip(),
            })
    except Exception:
        pass

    # ── 4. articles_fts 搜索 ──
    try:
        rows = conn.execute(
            """SELECT snippet(articles_fts, 2, '【【', '】】', '...', 50) as snip
               FROM articles_fts WHERE content MATCH ?
               LIMIT 5""",
            (f'"TOEFL" OR "托福"',),
        ).fetchall()
    except Exception:
        rows = []
    for (snip,) in rows:
        if norm[:4] not in snip and school_name[:4] not in snip:
            continue
        scoring = _detect_scoring(snip)
        category = _classify_toefl_text(snip)
        _add(scoring, category, {"source": "article", "detail": snip})

    # 去掉空的分组
    result = {}
    for scoring, cats in containers.items():
        non_empty = {k: v for k, v in cats.items() if v}
        if non_empty:
            result[scoring] = non_empty
    return result


# ── TOEFL 分数转换 ──
# 旧托福 (0-120) → 新托福 (1-6) 映射（参考 ETS 官方 band 对应）
_TOEFL_OLD_TO_NEW = [
    (114, 6.0), (107, 5.5), (95, 5.0), (86, 4.5), (72, 4.0), (60, 3.5),
]


def old_toefl_to_new(toefl_score: int) -> float:
    """旧托福 0-120 分 → 新托福 1-6 分档"""
    for threshold, new_score in _TOEFL_OLD_TO_NEW:
        if toefl_score >= threshold:
            return new_score
    return 3.0


def new_toefl_to_old(toefl_new_score: float) -> int:
    """新托福 1-6 分档 → 旧托福 0-120 分（取对应下限，偏保守）"""
    # 从低到高排序
    sorted_pairs = sorted(_TOEFL_OLD_TO_NEW, key=lambda x: x[1])
    for old_threshold, new_score in sorted_pairs:
        if toefl_new_score <= new_score:
            return old_threshold
    return 120  # 超过 6.0 的按满分 120 算


def check_toefl_requirement(
    user_toefl: Optional[int],
    school_toefl_total: Optional[int],
    school_toefl_new_total: Optional[float],
    user_toefl_new: Optional[float] = None,
) -> tuple[Optional[int], Optional[float], Optional[bool]]:
    """
    检查用户托福分是否达标（同时支持新旧分制）。

    输入:
      user_toefl: 旧分制用户分数 (0-120)
      school_toefl_total: 学校旧分制要求 (0-120)
      school_toefl_new_total: 学校新分制要求 (1-6)
      user_toefl_new: 新分制用户分数 (1-6)

    返回: (toefl_total_requirement, toefl_new_requirement, meets_bool)
    - meets_bool=None: 无要求或无分数
    - meets_bool=True: 达标
    - meets_bool=False: 不达标

    优先级: 用户新分制 > 用户旧分制 | 学校新分制 > 学校旧分制
    用户有新分制时，优先直接对比学校新分制要求。
    """
    # ── 用户提供的是新分制分数 (1-6) ──
    if user_toefl_new is not None:
        if school_toefl_new_total is not None:
            # 新 vs 新：直接对比
            return school_toefl_total, school_toefl_new_total, user_toefl_new >= school_toefl_new_total
        if school_toefl_total is not None:
            # 新 vs 旧：转换后对比
            user_old_equiv = new_toefl_to_old(user_toefl_new)
            return school_toefl_total, school_toefl_new_total, user_old_equiv >= school_toefl_total
        # 学校无要求
        return None, None, None

    # ── 用户提供的是旧分制分数 (0-120) ──
    if user_toefl is not None:
        # 优先用旧托福要求对比
        if school_toefl_total is not None:
            return school_toefl_total, school_toefl_new_total, user_toefl >= school_toefl_total
        # 回退到新托福要求对比
        if school_toefl_new_total is not None:
            user_new = old_toefl_to_new(user_toefl)
            return school_toefl_total, school_toefl_new_total, user_new >= school_toefl_new_total
        # 学校无要求
        return None, None, None

    # 用户无任何分数
    return school_toefl_total, school_toefl_new_total, None


# ===== 推荐结果缓存（内存，5 分钟 TTL） =====
_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 300  # 5 分钟


def _profile_key(profile: dict, tianshu_data: Optional[dict] = None) -> str:
    """从 profile 生成缓存键（hash），忽略 dynamic 字段"""
    relevant = {k: v for k, v in profile.items() if v is not None}
    if tianshu_data:
        relevant["_tianshu"] = tianshu_data
    raw = json.dumps(relevant, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> dict | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.time() - ts > _CACHE_TTL:
        del _cache[key]
        return None
    return value


def _cache_set(key: str, value: dict) -> None:
    # 最多缓存 64 条，超限时清理最旧的
    if len(_cache) >= 64:
        oldest = min(_cache.keys(), key=lambda k: _cache[k][0])
        del _cache[oldest]
    _cache[key] = (time.time(), value)


def run(profile: dict, tianshu_data: Optional[dict] = None) -> dict:
    # 缓存命中直接返回
    key = _profile_key(profile, tianshu_data)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    countries = profile["target_countries"]
    gpa_score = profile["gpa_score"]
    gpa_format = profile["gpa_format"]
    study_level = profile["study_level"]
    target_major = profile.get("target_major")
    original_major = profile.get("original_major")
    undergrad_school = profile.get("undergraduate_school")

    gpa_percent, gpa4 = normalize_gpa(gpa_score, gpa_format, undergrad_school)
    tier, tier_label = classify_school_tier(undergrad_school)

    background = {
        "gpa_percent": gpa_percent,
        "gpa4": gpa4,
        "school_tier": tier,
        "school_tier_label": tier_label,
        "gre_score": profile.get("gre_score"),
        "toefl_score": profile.get("toefl_score"),
        "toefl_new_score": profile.get("toefl_new_score"),
        "ielts_score": profile.get("ielts_score"),
    }

    with get_db() as conn:
        match_result = match_schools_by_background(
            conn=conn,
            countries=countries,
            gpa_score=gpa_score,
            gpa_format=gpa_format,
            study_level=study_level,
            target_major=target_major,
            original_major=original_major,
            undergrad_school=undergrad_school,
        )

        # 启动 pathway 搜索（使用独立连接，可与规则增强并行）
        with ThreadPoolExecutor(max_workers=1) as executor:
            pathway_future = executor.submit(
                find_pathway_suggestions,
                conn=conn,
                study_level=study_level,
                target_countries=countries,
                gpa_percent=gpa_percent,
                school_tier=tier,
                original_major=original_major,
                target_major=target_major,
            )

            # 应用国家插件增强推荐结果
            match_result = enhance_with_rules(conn, match_result, profile, background)

            # 生成专业推荐（需要 conn 查 school_major_strength）
            major_recs = generate_major_recommendations(conn, match_result, profile)

        # 收集 pathway 结果
        pathway = pathway_future.result()

        # ── TOEFL 达标检查（在 enhance 之后，确保操作最终版 match_result） ──
        user_toefl = profile.get("toefl_score")        # 旧分制 0-120
        user_toefl_new = profile.get("toefl_new_score")  # 新分制 1-6
        for country_entry in match_result.get("by_country", []):
            for school in country_entry.get("schools", []):
                school_name = school.get("name")
                if not school_name:
                    continue
                row = conn.execute(
                    """SELECT u.toefl_total, u.toefl_new_total
                       FROM universities u
                       WHERE u.name = ?
                       UNION
                       SELECT u.toefl_total, u.toefl_new_total
                       FROM university_aliases a
                       JOIN universities u ON a.university_id = u.id
                       WHERE a.alias = ?""",
                    (school_name, school_name),
                ).fetchone()
                req_total = row[0] if row else None
                req_new = row[1] if row else None
                # 学校要求（始终展示，无需用户分数）
                school["toefl_requirement"] = req_total
                school["toefl_new_requirement"] = req_new
                # 用户是否达标（优先新分制判断）
                _, _, meets = check_toefl_requirement(
                    user_toefl, req_total, req_new,
                    user_toefl_new=user_toefl_new,
                )
                school["meets_toefl"] = meets

                # ── 展示用 TOEFL 要求（优先新托福） ──
                if req_new is not None:
                    school["toefl_display"] = {"type": "new", "value": req_new, "label": f"新托福 {req_new}"}
                elif req_total is not None:
                    school["toefl_display"] = {"type": "old", "value": req_total, "label": f"托福 {req_total}"}
                else:
                    school["toefl_display"] = None

                # ── 知识库托福信息消化（区分新旧分制） ──
                insights = _digest_toefl_knowledge(conn, school_name)
                school["toefl_kb_insights"] = insights
                # 兼容旧版：保留原文片段列表（展平所有分制+分类）
                school["toefl_kb_sources"] = []
                for scoring_cats in insights.values():
                    for entries in scoring_cats.values():
                        for e in entries:
                            detail = e.get("detail", "")
                            if detail and detail not in school["toefl_kb_sources"]:
                                school["toefl_kb_sources"].append(detail)

    # ── 天枢测评数据加持（MBTI fitMajors 匹配提升） ──
    if tianshu_data:
        fit_majors = tianshu_data.get("mbti", {}).get("fitMajors", "")
        mbti_type = tianshu_data.get("mbti", {}).get("type", "")
        # fit_majors 是逗号/换行分隔的多个专业名字符串
        fit_major_list = [m.strip() for m in re.split(r'[,，\n]', fit_majors) if m.strip()]
        if fit_major_list:
            for country_entry in match_result.get("by_country", []):
                for school in country_entry.get("schools", []):
                    school_majors = school.get("majors", [])
                    # 检查学校录取专业是否与 fitMajors 中的任何专业重叠
                    has_overlap = any(
                        any(fm in sm or sm in fm for sm in school_majors)
                        for fm in fit_major_list
                    )
                    if has_overlap:
                        school["tianshu_boost"] = True
                        school["mbti_type"] = mbti_type
                        current_score = school.get("admission_score", 0) or 0
                        school["admission_score"] = round(current_score + 0.3, 1)
                    else:
                        school["tianshu_boost"] = False
        else:
            # fit_major_list 为空时标记 boost=false
            for country_entry in match_result.get("by_country", []):
                for school in country_entry.get("schools", []):
                    school["tianshu_boost"] = False
    else:
        # 无 tianshu_data: 标记所有 school 的 tianshu_boost = False
        for country_entry in match_result.get("by_country", []):
            for school in country_entry.get("schools", []):
                school["tianshu_boost"] = False

    total_cases = sum(c["matched_cases"] for c in match_result["by_country"])
    total_schools = sum(c["matched_schools"] for c in match_result["by_country"])

    result = {
        "background": background,
        "match_summary": {
            "total_cases": total_cases,
            "total_schools": total_schools,
        },
        "by_country": match_result["by_country"],
        "pathway_suggestions": pathway,
        "major_recommendations": major_recs,
        "application_strategy": generate_application_strategy(background, match_result),
        "background_improvement": "\n".join(generate_background_improvement(background, match_result)),
        "generated_at": "",
    }
    _cache_set(key, result)
    return result
