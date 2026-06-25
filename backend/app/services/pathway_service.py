"""预科/通路学校推荐服务"""
import sqlite3
from collections import defaultdict
from typing import Optional

from ..core.database import get_connection

PATHWAY_LEVEL_MAP = {
    "硕士": ("pre_masters", "硕士预科"),
    "本科": ("foundation_programs", "本科预科"),
    "博士": ("pre_masters", "硕士预科"),
}

STUDY_LEVEL_LABELS = {
    "硕士": "硕士预科 (Pre-Master)",
    "本科": "本科预科 (Foundation)",
}


def _load_pathway_data(conn: sqlite3.Connection, study_level: str) -> list[dict]:
    table, _ = PATHWAY_LEVEL_MAP.get(study_level, ("pre_masters", "预科"))
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    return [dict(r) for r in rows]


def _normalize_uni_name(name: str) -> str:
    for kw in ["国际学院", "国际学习中心", "ISC", "预科", "预科学院"]:
        name = name.replace(kw, "")
    return name.strip()


def build_pathway_map(
    conn: sqlite3.Connection,
    study_level: str,
) -> dict[str, list[dict]]:
    """
    构建: 目标大学名 → 可用的预科/通路项目列表
    """
    data = _load_pathway_data(conn, study_level)
    mapping: dict[str, list[dict]] = defaultdict(list)

    for row in data:
        target_uni = row.get("university", "")
        if not target_uni:
            continue

        entry = {
            "provider": row.get("provider", ""),
            "program_type": STUDY_LEVEL_LABELS.get(study_level, "预科"),
            "direction": row.get("direction", ""),
            "location": row.get("location", ""),
            "duration": row.get("duration", ""),
            "intake": row.get("intake_month", ""),
            "academic_req": row.get("academic_requirement", ""),
            "ielts_req": (row.get("ielts_requirement") or "").replace("雅思", "").strip(),
            "tuition_note": str(row.get("tuition_euro", "") or ""),
        }
        # 标准化目标大学名
        key = _normalize_uni_name(target_uni)
        mapping[key].append(entry)

        # 也保留原始名
        if key != target_uni:
            mapping[target_uni].append(entry)

    return mapping


def find_pathway_suggestions(
    conn: sqlite3.Connection,
    study_level: str,
    target_countries: list[str],
    gpa_percent: Optional[float],
    school_tier: int,
    original_major: Optional[str] = None,
    target_major: Optional[str] = None,
) -> list[dict]:
    """
    触发预科建议的场景：
    1. GPA 偏低 (百分制 < 75 或双非 < 80)
    2. 跨专业申请 (original_major != target_major)
    """
    pathway_map = build_pathway_map(conn, study_level)

    if gpa_percent is None:
        return []

    reasons = []

    # 低 GPA 触发
    low_gpa = gpa_percent < 75 or (school_tier >= 3 and gpa_percent < 80)
    if low_gpa:
        reasons.append("GPA偏低，预科可降低录取门槛")

    # 跨专业触发
    is_cross_major = (
        original_major and target_major
        and original_major.strip() != target_major.strip()
        and target_major.strip() not in original_major
        and original_major.strip() not in target_major
    )
    if is_cross_major and gpa_percent < 85:
        reasons.append(f"从「{original_major}」转「{target_major}」，预科可补修专业基础")

    if not reasons:
        return []

    reason_text = "；".join(reasons)
    suggestions = []

    for uni_name, programs in pathway_map.items():
        uni_row = conn.execute(
            "SELECT id, name, country, qs_rank, usnews_rank FROM universities WHERE name = ? LIMIT 1",
            (uni_name,),
        ).fetchone()
        if not uni_row:
            continue

        uni = dict(uni_row)
        if uni["country"] not in ["UK", "IE", "AU", "US", "SG", "MY"]:
            continue

        rank = uni.get("qs_rank") or 9999
        if rank > 200:
            continue

        # 跨专业时：优先推荐预科方向包含目标专业的项目
        if is_cross_major and target_major:
            matched_programs = [
                p for p in programs
                if not p["direction"] or any(
                    kw in p["direction"]
                    for kw in [target_major, "商科", "计算机", "工程", "社科", "传媒"]
                    if kw in target_major or target_major in kw
                )
            ]
            if matched_programs:
                programs = matched_programs

        suggestions.append({
            "university": uni["name"],
            "country": uni["country"],
            "qs_rank": uni["qs_rank"],
            "usnews_rank": uni["usnews_rank"],
            "programs": programs[:3],
            "reason": reason_text,
        })

    suggestions.sort(key=lambda x: x["qs_rank"] or 9999)
    return suggestions[:10]
