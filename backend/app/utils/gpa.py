from typing import Optional


GPA_SCALE_4 = [
    (90, 4.0),
    (85, 3.7),
    (80, 3.3),
    (75, 3.0),
    (70, 2.7),
    (60, 2.3),
    (0, 1.0),
]

GPA_FORMAT_ALIASES = {
    "四分制": "4分制",
    "五分制": "5分制",
    "4分制": "4分制",
    "5分制": "5分制",
    "百分制": "百分制",
    "7分制": "7分制",
    "9分制": "9分制",
    "十分制": "9分制",
    "九分制/十分制": "9分制",
    "学位等级对应分数": "学位等级对应分数",
    "英制百分制": "英制百分制",
}

GPA_RANGES = {
    "4分制": (0.1, 4.0),
    "5分制": (0.1, 5.0),
    "百分制": (1.0, 100.0),
    "7分制": (0.1, 7.0),
    "9分制": (0.1, 9.0),
    "学位等级对应分数": (1.0, 100.0),
    "英制百分制": (1.0, 100.0),
}

KNOWN_OVERSEAS = {
    "海本", "英本", "美本", "加本", "澳本", "日韩本", "欧陆本",
}

KNOWN_SINO_FOREIGN = {
    "西交利物浦大学", "宁波诺丁汉大学", "温州肯恩大学", "广东以色列理工学院",
    "上海纽约大学", "昆山杜克大学", "北京师范大学-香港浸会大学联合国际学院",
    "香港中文大学（深圳）", "深圳北理莫斯科大学",
}


def percent_to_gpa4(score: float) -> float:
    for threshold, gpa in GPA_SCALE_4:
        if score >= threshold:
            return gpa
    return 1.0


def gpa5_to_gpa4(score: float) -> float:
    return round(score * 0.8, 2)


def normalize_gpa(
    gpa_score: float,
    gpa_format: str,
    undergrad_school: Optional[str] = None,
) -> tuple[Optional[float], Optional[float]]:

    fmt = GPA_FORMAT_ALIASES.get((gpa_format or "").strip(), gpa_format)

    try:
        score = float(gpa_score)
    except (ValueError, TypeError):
        return None, None

    if score <= 0 or score > 200:
        return None, None

    is_overseas = undergrad_school and undergrad_school in KNOWN_OVERSEAS

    if fmt == "学位等级对应分数":
        if score >= 80:
            pct = 90.0
        elif score >= 70:
            pct = 85.0
        elif score >= 60:
            pct = 80.0
        elif score >= 50:
            pct = 75.0
        elif score >= 40:
            pct = 68.0
        else:
            pct = 60.0
        return round(pct, 1), percent_to_gpa4(pct)

    if fmt in ("9分制", "十分制"):
        pct = round(score / 9.0 * 100, 1)
        return pct, percent_to_gpa4(pct)

    if fmt == "5分制" or (4.0 < score <= 5.5 and fmt not in ("4分制", "四分制")):
        pct = round(score / 5.0 * 100, 1)
        return pct, gpa5_to_gpa4(score)

    if fmt == "7分制" or (5.5 < score <= 7.5 and fmt != "百分制"):
        pct = round(score / 7.0 * 100, 1)
        return pct, percent_to_gpa4(pct)

    if is_overseas and score <= 4.0:
        pct = min(100, round(score * 25, 1))
        return pct, round(score, 2)

    if fmt == "4分制" or score <= 4.0:
        pct = min(100, round(score * 25, 1))
        return pct, round(score, 2)

    if fmt == "英制百分制" or is_overseas:
        if score >= 75:
            pct = 92.0
        elif score >= 70:
            pct = 85.0
        elif score >= 65:
            pct = 78.0
        elif score >= 60:
            pct = 70.0
        elif score >= 55:
            pct = 62.0
        else:
            pct = score
        return round(pct, 1), percent_to_gpa4(pct)

    if fmt == "百分制" or score > 10:
        return round(score, 1), percent_to_gpa4(score)

    return None, None


def get_gpa_bin(gpa4: Optional[float]) -> str:
    if gpa4 is None:
        return "75-79"
    pct = gpa4 * 25
    if pct >= 90:
        return "90+"
    elif pct >= 85:
        return "85-89"
    elif pct >= 80:
        return "80-84"
    elif pct >= 75:
        return "75-79"
    elif pct >= 70:
        return "70-74"
    else:
        return "<70"


def validate_gpa(gpa_score: float, gpa_format: str) -> tuple[str, Optional[str]]:
    fmt = GPA_FORMAT_ALIASES.get(gpa_format.strip(), gpa_format)
    gpa_range = GPA_RANGES.get(fmt)
    if gpa_range is None:
        return fmt, f"不支持的 GPA 格式: {gpa_format}，支持: {list(GPA_RANGES.keys())}"
    lo, hi = gpa_range
    if gpa_score < lo or gpa_score > hi:
        return fmt, f"GPA 超出范围: {fmt} 应在 {lo}-{hi} 之间，当前值: {gpa_score}"
    return fmt, None
