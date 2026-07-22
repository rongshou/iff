"""语言要求（托福/雅思）查询 —— 当用户询问语言成绩要求时注入参考数据。

解决的问题：用户问"XX大学托福/雅思要求"时，此前系统既不查数据库、也不把
语言数据交给 LLM，导致回答无效。本模块负责：
1. 检测语言要求类提问；
2. 从用户文本中识别学校（用数据库中已有语言数据的校名做子串匹配，规避
   通用校名抽取的截断问题）；
3. 合并 universities 与 us_admission_info 两张表的语言要求数据；
4. 格式化为上下文字符串注入 system prompt。

数据源：
- universities: toefl_total / toefl_new_total / toefl_notes / ielts_overall
- us_admission_info（美国院校，更密）: toefl_min / ielts_min / toefl_new_total /
  toefl_new_sections / toefl_notes
"""
from __future__ import annotations

import json
import logging
import re

from ..core.database import get_connection

logger = logging.getLogger(__name__)

# 语言要求提问关键词（小写匹配）
_LANGUAGE_KEYWORDS = ("托福", "雅思", "toefl", "ielts", "语言要求", "语言成绩", "语言分数")

_SECTION_CN = {
    "reading": "阅读",
    "listening": "听力",
    "writing": "写作",
    "speaking": "口语",
}

# 常见中文简称 → 数据库校名（高频且前缀匹配覆盖不到的）
_COMMON_ABBREV = {
    "哥大": "哥伦比亚大学",
    "纽大": "纽约大学",
    "波士顿大学": "波士顿大学",
    "伯克利": "加州大学伯克利分校",
    "加州理工": "加州理工学院",
    "佐治亚理工": "佐治亚理工学院",
    "卡耐基梅隆": "卡耐基梅隆大学",
    "卡内基梅隆": "卡耐基梅隆大学",
    "约翰霍普金斯": "约翰霍普金斯大学",
    "霍普金斯": "约翰霍普金斯大学",
    "华盛顿圣路易斯": "华盛顿大学圣路易斯",
    "密歇根安娜堡": "密歇根大学安娜堡分校",
    "威斯康星麦迪逊": "威斯康星大学麦迪逊分校",
    "伊利诺伊香槟": "伊利诺伊大学厄巴纳-香槟分校",
    "香槟分校": "伊利诺伊大学厄巴纳-香槟分校",
}


def is_language_query(text: str) -> bool:
    """判断文本是否在询问托福/雅思/语言成绩要求。"""
    t = (text or "").lower()
    return any(k in t for k in _LANGUAGE_KEYWORDS)


def _load_language_data(conn) -> dict[str, dict]:
    """加载所有带语言要求的学校数据，按校名合并两张表。"""
    data: dict[str, dict] = {}

    def slot(name: str) -> dict:
        if name not in data:
            data[name] = {
                "name": name,
                "toefl_old": None,
                "toefl_new": None,
                "toefl_sections": None,
                "ielts": None,
                "notes": None,
            }
        return data[name]

    # universities 表
    for row in conn.execute(
        """
        SELECT name, toefl_total, toefl_new_total, toefl_notes, ielts_overall
        FROM universities
        WHERE toefl_total IS NOT NULL
           OR toefl_new_total IS NOT NULL
           OR (ielts_overall IS NOT NULL AND ielts_overall != '')
        """
    ):
        rec = slot(row["name"])
        rec["toefl_old"] = row["toefl_total"]
        rec["toefl_new"] = row["toefl_new_total"]
        rec["notes"] = row["toefl_notes"]
        ielts = row["ielts_overall"]
        rec["ielts"] = ielts if ielts not in (None, "") else None

    # us_admission_info 表（美国院校，数据更密）—— 仅填补空缺字段
    for row in conn.execute(
        """
        SELECT university, toefl_min, ielts_min, toefl_new_total,
               toefl_new_sections, toefl_notes
        FROM us_admission_info
        WHERE toefl_min IS NOT NULL
           OR ielts_min IS NOT NULL
           OR toefl_new_total IS NOT NULL
        """
    ):
        rec = slot(row["university"])
        if rec["toefl_old"] is None:
            rec["toefl_old"] = row["toefl_min"]
        if rec["toefl_new"] is None:
            rec["toefl_new"] = row["toefl_new_total"]
        if rec["ielts"] is None:
            rec["ielts"] = row["ielts_min"]
        if rec["toefl_sections"] is None:
            rec["toefl_sections"] = row["toefl_new_sections"]
        if not rec["notes"] and row["toefl_notes"]:
            rec["notes"] = row["toefl_notes"]

    return data


def _load_english_name_map(conn) -> dict[str, str]:
    """加载英文名→中文校名映射（us_admission_info.university_en）。"""
    mapping: dict[str, str] = {}
    try:
        for row in conn.execute(
            "SELECT university, university_en FROM us_admission_info "
            "WHERE university_en IS NOT NULL AND university_en != ''"
        ):
            en = (row["university_en"] or "").strip()
            cn = (row["university"] or "").strip()
            if en and cn:
                mapping[en.lower()] = cn
    except Exception:
        logger.warning("load english name map failed", exc_info=True)
    return mapping


def find_schools_in_text(text: str, conn) -> list[dict]:
    """在文本中识别带有语言要求数据的学校。

    匹配策略（按优先级）：
    1. 数据库中文校名子串匹配（长名优先，跳过被包含的短名）；
    2. 常见简称词典（哥大、纽大、伯克利…）；
    3. 中文名前缀匹配（"麻省理工"→"麻省理工学院"，前缀≥4字符）；
    4. 英文名词边界匹配（MIT、UCLA、UIUC…，忽略大小写）。
    """
    data = _load_language_data(conn)
    matched: list[str] = []

    # 1. 中文校名全名子串匹配（长名优先）
    for name in sorted(data.keys(), key=len, reverse=True):
        if not name or name not in text:
            continue
        if any(name != m and name in m for m in matched):
            continue
        matched.append(name)

    # 2. 常见简称词典
    for abbrev, full_name in _COMMON_ABBREV.items():
        if abbrev in text and full_name in data and full_name not in matched:
            matched.append(full_name)

    # 3. 前缀匹配：用户写"麻省理工"，DB 里是"麻省理工学院"
    #    尝试 DB 校名的前缀（长度≥4），避免误命中太短的片段
    for name in sorted(data.keys(), key=len, reverse=True):
        if not name or name in matched or len(name) < 5:
            continue
        found = False
        for end in range(len(name) - 1, 3, -1):
            prefix = name[:end]
            if prefix in text:
                # 排除前缀恰好落在已匹配校名内部的情况
                if not any(prefix in m for m in matched):
                    matched.append(name)
                found = True
                break
        if found:
            continue

    # 4. 英文名匹配（词边界，忽略大小写）
    en_map = _load_english_name_map(conn)
    for en_name, cn_name in en_map.items():
        if len(en_name) < 2 or cn_name not in data or cn_name in matched:
            continue
        pattern = r"(?<![A-Za-z0-9])" + re.escape(en_name) + r"(?![A-Za-z0-9])"
        if re.search(pattern, text, re.IGNORECASE):
            matched.append(cn_name)

    return [data[n] for n in matched]


def _format_language_context(schools: list[dict]) -> str:
    lines = [
        "【语言要求参考数据】（以下为数据库中对应学校的官方语言成绩要求，"
        "请严格据此回答，不要编造；新旧托福分数均为学校要求）："
    ]
    for s in schools:
        parts = []
        if s["toefl_new"] is not None:
            parts.append(f"新托福 {s['toefl_new']}")
        if s["toefl_old"] is not None:
            parts.append(f"旧托福 {s['toefl_old']}")
        if s["ielts"] is not None:
            parts.append(f"雅思 {s['ielts']}")
        lines.append(f"- {s['name']}: " + (" | ".join(parts) if parts else "（暂无语言要求数据）"))
        if s["toefl_sections"]:
            try:
                sec = json.loads(s["toefl_sections"])
                sec_str = "、".join(
                    f"{_SECTION_CN.get(k, k)} {v}" for k, v in sec.items()
                )
                if sec_str:
                    lines.append(f"  新托福小分: {sec_str}")
            except (ValueError, TypeError):
                pass
        if s["notes"]:
            lines.append(f"  补充说明: {s['notes']}")
    lines.append(
        "请基于以上数据直接、明确地回答用户关于语言要求的问题；"
        "若用户询问的学校不在上述数据中，请如实说明暂无该校的收录数据。"
    )
    return "\n".join(lines)


def build_language_context(last_user: str, messages: list[dict]) -> str | None:
    """构建语言要求上下文。非语言提问或未识别到学校时返回 None。"""
    if not is_language_query(last_user):
        return None

    conn = get_connection()
    try:
        # 先在当前消息中找学校
        schools = find_schools_in_text(last_user, conn)
        # 当前消息没有校名（如"这个学校雅思要多少"），回看最近几条用户消息
        if not schools:
            recent = [m["content"] for m in messages if m.get("role") == "user"][-4:]
            for text in reversed(recent):
                schools = find_schools_in_text(text, conn)
                if schools:
                    break
        if not schools:
            return None
        return _format_language_context(schools)
    except Exception:
        logger.warning("build_language_context failed", exc_info=True)
        return None
    finally:
        conn.close()
