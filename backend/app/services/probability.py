"""真实录取概率评分服务 - 基于 17.6 万案例的百分位数据"""

import sqlite3
from typing import Optional

from ..core.database import get_connection


def get_school_percentiles(
    school_name: str, tier_label: str, conn: sqlite3.Connection | None = None
) -> Optional[dict]:
    """
    获取某学校在某层次下的真实 GPA 百分位
    优先级: school::tier > school > 404
    表不存在时优雅降级，返回 None

    可选传入 conn 复用连接，避免在循环中重复打开/关闭连接。
    """
    own_conn = conn is None
    if own_conn:
        conn = get_connection()
    try:
        cur = conn.cursor()

        # 精确匹配 university + tier
        row = cur.execute(
            "SELECT * FROM school_gpa_percentiles_by_tier WHERE university=? AND tier=?",
            (school_name, tier_label),
        ).fetchone()
        if row:
            return dict(row)

        # 回退到 school 不限 tier
        row = cur.execute(
            "SELECT * FROM school_gpa_percentiles_by_tier WHERE university=? AND tier=''",
            (school_name,),
        ).fetchone()
        if row:
            return dict(row)

        return None
    except sqlite3.OperationalError:
        return None
    finally:
        if own_conn:
            conn.close()


def classify_admission_chance(
    user_gpa_percent: float,
    school_name: str,
    tier_label: str,
) -> tuple[str, float, Optional[float], Optional[float]]:
    """
    返回: (分档, 概率分数 0-1, p50参考值, 案例数)

    分档:
      - "保底" (>p75, chance 0.9+)
      - "匹配" (p50-p75, chance 0.6-0.9)
      - "冲刺" (p25-p50, chance 0.3-0.6)
      - "彩票" (<p25, chance 0.1-0.3)
    """
    perc = get_school_percentiles(school_name, tier_label)
    if perc is None:
        return "未知", 0.5, None, None

    p25 = perc.get("p25")
    p50 = perc.get("p50")
    p75 = perc.get("p75")
    n = perc.get("n", 0)

    if p75 is not None and user_gpa_percent >= p75:
        return "保底", 0.92, p50, n
    if p50 is not None and user_gpa_percent >= p50:
        ratio = (user_gpa_percent - p50) / (p75 - p50) if p75 is not None and p75 > p50 else 0.5
        return "匹配", 0.55 + ratio * 0.35, p50, n
    if p25 is not None and user_gpa_percent >= p25:
        ratio = (user_gpa_percent - p25) / (p50 - p25) if p50 is not None and p50 > p25 else 0.5
        return "冲刺", 0.25 + ratio * 0.30, p50, n
    return "彩票", 0.15, p50, n


def get_country_gpa_benchmark(country: str, gpa_range: str) -> Optional[dict]:
    """获取某国家某GPA段的平均QS排名基准"""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM country_gpa_benchmark WHERE country=? AND gpa_range=?",
            (country, gpa_range),
        ).fetchone()
        if row:
            return dict(row)
        return None
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()


def gpa_to_range_label(gpa_percent: float) -> str:
    """GPA百分制 → 范围标签"""
    if gpa_percent >= 90:
        return "90+"
    lo = int(gpa_percent // 5) * 5
    hi = lo + 4
    return f"{lo}-{hi}"
