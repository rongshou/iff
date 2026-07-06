"""
英国院校认可名单插件。
用真实案例数据推断：如果某本科院校从未被某英国学校录取过，大概率不在认可名单。
移植自 advisor/scripts/plugins/uk_acceptance_list.py
"""

from ...core.database import get_connection


def _load_uk_acceptance() -> dict:
    """从 advisor.db 加载 UK 认可名单数据"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT undergrad_school, uk_university, offer_count, total_uk_offers, unique_unis "
            "FROM uk_acceptance_lists ORDER BY undergrad_school"
        ).fetchall()
        result: dict = {}
        for row in rows:
            school = row["undergrad_school"]
            if school not in result:
                result[school] = {
                    "accepted_universities": {},
                    "total_uk_offers": row["total_uk_offers"],
                    "unique_unis": row["unique_unis"],
                }
            result[school]["accepted_universities"][row["uk_university"]] = row["offer_count"]
        return result
    finally:
        conn.close()


_UK_ACCEPTANCE = _load_uk_acceptance()


def _find_undergrad_school(undergrad_name: str) -> str | None:
    """模糊匹配本科院校名称"""
    if not undergrad_name:
        return None
    undergrad_name = undergrad_name.strip()
    if undergrad_name in _UK_ACCEPTANCE:
        return undergrad_name
    for key in _UK_ACCEPTANCE:
        if undergrad_name in key or key in undergrad_name:
            return key
    return None


def get_acceptance_score(uk_uni_name: str, undergrad_school: str) -> int:
    """
    返回英国院校对该本科学校的接受度分数
    0 = 无历史录取记录（可能不在认可名单）
    1 = 有少量录取（1-3 例）
    2 = 有稳定录取（4-10 例）
    3 = 大量录取（10+ 例）
    """
    if not uk_uni_name or not undergrad_school:
        return 1

    key = _find_undergrad_school(undergrad_school)
    if not key:
        return 1

    unis = _UK_ACCEPTANCE.get(key, {}).get("accepted_universities", {})
    count = 0
    for uni_name, cnt in unis.items():
        if uk_uni_name in uni_name or uni_name in uk_uni_name:
            count = cnt
            break

    if count >= 10:
        return 3
    elif count >= 4:
        return 2
    elif count >= 1:
        return 1
    else:
        return 0


def apply(conn, scored, profile, bg, rule, context):
    """英国院校认可名单过滤 - 仅标记，不覆盖概率"""
    countries = context.get("countries", [])
    is_uk = "英国" in countries
    if not is_uk:
        return scored

    undergrad_school = profile.get("undergraduate_school", "")
    if not undergrad_school:
        return scored

    for s in scored:
        acceptance_score = get_acceptance_score(s.get("name", ""), undergrad_school)
        s["acceptance_score"] = acceptance_score

    return scored
