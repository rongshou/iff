import json
import re
from typing import Optional


def parse_gpa_requirement(gpa_req_str: str, tier_key: str) -> Optional[float]:
    try:
        req = json.loads(gpa_req_str)
    except (json.JSONDecodeError, TypeError):
        return None

    value = req.get(tier_key)
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        nums = re.findall(r"\d+\.?\d*", value)
        if nums:
            return float(nums[0])

    return None


def normalise_to_percent(value: float) -> float:
    if value <= 10:
        return value * 25
    return value


def meets_requirement(
    user_gpa_percent: float,
    user_gpa4: float,
    gpa_req_str: Optional[str],
    tier_key: str,
    target_major: Optional[str] = None,
) -> tuple[bool, bool, Optional[float]]:
    if not gpa_req_str:
        return True, True, None

    req_raw = parse_gpa_requirement(gpa_req_str, tier_key)
    if req_raw is None:
        return True, True, None

    if req_raw <= 10:
        req_value = req_raw
        user_value = user_gpa4 or 0
        gap_pct = (user_value - req_value) / req_value * 100 if req_value else 100
        meets = user_value >= req_value
    else:
        req_value = req_raw
        user_value = user_gpa_percent or 0
        gap_pct = (user_value - req_value) / req_value * 100 if req_value else 100
        meets = user_value >= req_value

    close = not meets and gap_pct >= -20

    return meets, close, req_raw


def classify_school_by_requirement(
    meets: bool, close: bool,
) -> str:
    if meets:
        return "可达"
    if close:
        return "冲刺"
    return "不推荐"
