import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor

from ..core.database import get_db
from ..utils.gpa import normalize_gpa
from ..utils.tier import classify_school_tier
from .case_matcher import match_schools_by_background
from .pathway_service import find_pathway_suggestions
from .school_engine import enhance_with_rules, generate_application_strategy, generate_background_improvement

# ===== 推荐结果缓存（内存，5 分钟 TTL） =====
_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 300  # 5 分钟


def _profile_key(profile: dict) -> str:
    """从 profile 生成缓存键（hash），忽略 dynamic 字段"""
    relevant = {k: v for k, v in profile.items() if v is not None}
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


def run(profile: dict) -> dict:
    # 缓存命中直接返回
    key = _profile_key(profile)
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

        # 收集 pathway 结果
        pathway = pathway_future.result()

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
        "application_strategy": generate_application_strategy(background, match_result),
        "background_improvement": generate_background_improvement(background, match_result),
        "generated_at": "",
    }
    _cache_set(key, result)
    return result
