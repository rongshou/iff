"""工具函数模块 —— 从 chat.py 分离，保持单一职责。

包含：用户画像解析、GPA/标化成绩提取、广告检测等纯函数，
不依赖 FastAPI / httpx 等运行时框架。
"""
from __future__ import annotations

import re
from ..utils.gpa import GPA_RANGES
from .school_abbrev import _UNIV_ABBREV


# =====================================================================
# 国家/地区别名
# =====================================================================

# 国家/地区别名 → 推荐引擎识别的正式名
COUNTRY_ALIASES = {
    "英国": "英国", "美国": "美国", "澳洲": "澳大利亚", "澳大利亚": "澳大利亚",
    "加拿大": "加拿大", "香港": "中国香港", "港": "中国香港",
    "新加坡": "新加坡", "日本": "日本", "德国": "德国", "法国": "法国",
    "新西兰": "新西兰", "爱尔兰": "爱尔兰", "荷兰": "荷兰",
    "韩国": "韩国", "马来西亚": "马来西亚", "澳门": "中国澳门",
}

VALID_COUNTRIES = set(COUNTRY_ALIASES.values())


def _parse_countries(text: str) -> list[str]:
    found: list[str] = []
    for alias, formal in COUNTRY_ALIASES.items():
        if alias in text and formal not in found:
            found.append(formal)
    return found


# =====================================================================
# GPA / 标化成绩解析
# =====================================================================

def _infer_gpa_format(gpa: float) -> str | None:
    """根据 GPA 数值推断分制"""
    for fmt, (lo, hi) in GPA_RANGES.items():
        if lo <= gpa <= hi:
            if fmt == "学位等级对应分数" or fmt == "英制百分制":
                continue
            return fmt
    return None


def _extract_gpa_from_text(text: str) -> tuple[float | None, str | None]:
    """从文本中提取 GPA 数值（无关键词前缀时的回退模式）"""
    # 模式 A: "X/Y"（如 3.5/4.0, 82/100）
    m = re.search(r"(\d+\.?\d*)\s*/\s*(\d+)", text)
    if m:
        score = float(m.group(1))
        fmt = _infer_gpa_format(score)
        return score, fmt
    # 模式 B: "X分"（如 85分）
    m = re.search(r"(\d+\.?\d*)\s*分", text)
    if m:
        score = float(m.group(1))
        fmt = _infer_gpa_format(score)
        return score, fmt
    # 模式 C: 纯数字（仅限单独出现的数字，如 "3.5"）
    m = re.search(r"\b(\d{2}\.?\d?)\b", text)
    if m and text.strip() not in ("985", "211", "C9"):
        score = float(m.group(1))
        if 1.0 <= score <= 100.0:
            fmt = _infer_gpa_format(score)
            return score, fmt
    return None, None


def _parse_gpa_from_conversation(messages: list[dict]) -> tuple[float | None, str | None]:
    """从对话历史中提取 GPA，既支持关键词前缀也支持上下文推断。
    
    策略：
    1. 先从所有 user 消息合并文本中搜关键词前缀（GPA/gpa/均分/绩点）
    2. 如果没找到，检查是否有 assistant 问过 GPA 相关的问题，
       然后看后续 user 消息中是否有数字模式（如 3.5/4.0、82/100、3.5）
    3. 如果还没找到，从 user 消息中搜"数字/数字"或"数字分"模式
    """
    combined = " ".join(
        m["content"] for m in messages if m["role"] == "user"
    )

    # 策略1: 关键词前缀
    gpa_match = re.search(
        r"(?:GPA|gpa|均分|绩点)\s*[:：]?\s*(\d+\.?\d*)", combined
    )
    if gpa_match:
        score = float(gpa_match.group(1))
        fmt = _infer_gpa_format(score)
        return score, fmt

    # 策略2: 对话上下文 — assistant 问 GPA → 用户回答数字
    GPA_ASK_KEYWORDS = ["gpa", "GPA", "均分", "绩点", "分制", "分数", "成绩"]
    for i, msg in enumerate(messages):
        if msg["role"] != "assistant":
            continue
        if not any(k in msg["content"] for k in GPA_ASK_KEYWORDS):
            continue
        # 找下一个 user 消息
        for j in range(i + 1, len(messages)):
            if messages[j]["role"] != "user":
                continue
            text = messages[j]["content"].strip()
            score, fmt = _extract_gpa_from_text(text)
            if score is not None:
                return score, fmt
            break

    # 策略3: 直接从 user 文本中搜 GPA 模式
    score, fmt = _extract_gpa_from_text(combined)
    if score is not None:
        return score, fmt

    return None, None


_GRE_PATTERN = re.compile(r"GRE\s*[:：]?\s*(\d{3})", re.IGNORECASE)


def _parse_gre(text: str) -> int | None:
    m = _GRE_PATTERN.search(text)
    if m:
        score = int(m.group(1))
        if 260 <= score <= 340:
            return score
    return None


_TOEFL_PATTERN = re.compile(r"(?:托福|TOEFL|toefl)\s*[:：]?\s*(\d{2,3})")


def _parse_toefl(text: str) -> int | None:
    m = _TOEFL_PATTERN.search(text)
    if m:
        score = int(m.group(1))
        if 30 <= score <= 120:
            return score
    return None


_IELTS_PATTERN = re.compile(r"(?:雅思|IELTS|ielts)\s*[:：]?\s*(\d+(?:\.\d)?)")


def _parse_ielts(text: str) -> float | None:
    m = _IELTS_PATTERN.search(text)
    if m:
        score = float(m.group(1))
        if 1.0 <= score <= 9.0:
            return score
    return None


# =====================================================================
# 专业解析
# =====================================================================

_MAJOR_STOPWORDS = {
    "香港", "英国", "美国", "澳洲", "澳大利亚", "加拿大", "新加坡", "日本",
    "德国", "法国", "新西兰", "爱尔兰", "荷兰", "韩国", "马来西亚", "澳门",
    "中国香港", "中国澳门", "硕士", "本科", "博士", "申请", "留学", "选校",
    "专业", "方向", "什么", "哪些", "可以", "可能", "怎么", "如何", "我的",
    "申请香港硕士", "申请英国硕士", "申请美国硕士", "申请澳洲硕士",
    "读硕士", "读本科", "读博士", "想读", "想去",
}


def _parse_major(text: str) -> str | None:
    # 模式0: 常见英文缩写 + 硕士/专业/方向
    _EN_ABBREV = {"CS": "计算机科学", "EE": "电子工程", "ECE": "电子与计算机工程",
                  "DS": "数据科学", "AI": "人工智能", "ML": "机器学习",
                  "BA": "商业分析", "FE": "金融工程", "MFE": "金融工程",
                  "SE": "软件工程", "IT": "信息技术", "MIS": "信息系统管理",
                  "HCI": "人机交互", "NLP": "自然语言处理", "CV": "计算机视觉",
                  "STAT": "统计学", "MATH": "数学", "PHY": "物理学",
                  "BIO": "生物学", "CHEM": "化学", "CSR": "企业社会责任"}
    m = re.search(rf"\b({'|'.join(_EN_ABBREV.keys())})\b\s*(?:硕士|专业|方向|申请|留学)?", text)
    if m:
        return _EN_ABBREV[m.group(1)]
    # 模式1: 专业|方向 : XXX (到标点或空格结束)
    m = re.search(r"(?:专业|方向)\s*[:：]\s*([^\s，。,.!？?]+)", text)
    if m:
        major = m.group(1).strip()
        if major and major not in _MAJOR_STOPWORDS:
            return major
    # 模式2: XXX专业 (优先长匹配,但排除含动词/国家名的组合)
    # 先剥离学历词和国家名,避免污染专业名
    cleaned = re.sub(r"(硕士|本科|博士)(?:生)?", "", text)
    cleaned = re.sub(r"(英国|美国|澳洲|澳大利亚|加拿大|香港|新加坡|日本|德国|法国|新西兰|爱尔兰|荷兰|韩国|马来西亚|澳门|中国香港|中国澳门)", "", cleaned)
    cleaned = re.sub(r"(申请|想去|想读|读|学)", "", cleaned)
    cleaned = re.sub(r"(双非|985|211|海本|英本|美本|加本|澳本)", "", cleaned)
    for length in range(6, 1, -1):
        m = re.search(rf"([\u4e00-\u9fffA-Za-z]{{{length}}})专业", cleaned)
        if not m:
            continue
        major = m.group(1).strip()
        if major in _MAJOR_STOPWORDS:
            continue
        if any(x in major for x in ("申请", "读", "学", "想去", "想读")):
            continue
        return major
    return None


def _parse_major_from_conversation(messages: list[dict]) -> str | None:
    """从对话上下文推断目标专业。
    
    当 assistant 问了"什么专业"之类的问题后，
    用户回复的简短中文词视为专业名。
    """
    MAJOR_ASK_KEYWORDS = ["专业", "方向", "什么"]
    for i, msg in enumerate(messages):
        if msg["role"] != "assistant":
            continue
        if not any(k in msg["content"] for k in MAJOR_ASK_KEYWORDS):
            continue
        # 找下一个 user 消息
        for j in range(i + 1, len(messages)):
            if messages[j]["role"] != "user":
                continue
            text = messages[j]["content"].strip()
            # 简短中文词（2-6字）且不含常见非专业词
            m = re.search(r"^([\u4e00-\u9fffA-Za-z]{2,6})$", text)
            if m:
                candidate = m.group(1)
                non_major = {"英国", "美国", "澳洲", "香港", "新加坡", "加拿大",
                             "本科", "硕士", "博士", "留学", "选校", "申请",
                             "985", "211", "双非"}
                if candidate not in non_major:
                    return candidate
            break  # 只检查紧跟着的那个 user 消息
    return None


# =====================================================================
# 本科院校解析
# =====================================================================

def _parse_upgrad(text: str) -> str | None:
    """解析本科院校背景"""
    tier_keywords = {
        "双非": "双非",
        "985": "985",
        "C9": "C9",
        "211": "211",
        "海本": "海本", "英本": "英本", "美本": "美本",
    }
    for kw, label in tier_keywords.items():
        if kw in text:
            return label
    return None


_undergrad_pattern = re.compile(r"(?:本科|本科院校|学校|院校)\s*[:：]\s*(\S+?)(?:[，。,.\s]|$)")


# 常用前置噪声词（出现在大学名之前的非名称单字）
_PREFIX_NOISE: set[str] = {
    "我", "你", "他", "她", "它", "在", "是", "的", "了", "和", "与", "及",
    "有", "没", "不", "把", "被", "让", "给", "向", "从", "对", "比", "跟",
    "读", "上", "去", "来", "考", "申", "学", "读", "想", "要", "能", "会",
    "就", "还", "也", "都", "只", "但", "可", "所", "该", "这", "那",
}


def _extract_best_university(text: str) -> str | None:
    """从文本中提取最可能的大学名称（右对齐子串，选最短的名称部分）"""
    candidates: list[tuple[int, int, str]] = []  # (pos, name_part_len, full_name)
    for suffix in ("大学", "学院"):
        idx = 0
        while True:
            idx = text.find(suffix, idx)
            if idx == -1:
                break
            # 向左找到连续中文的起点
            start = idx
            while start > 0 and '\u4e00' <= text[start - 1] <= '\u9fff':
                start -= 1
            prefix = text[start:idx]

            # 从右向左取子串作为候选名称（取最短的有效名）
            for name_len in range(min(len(prefix), 16), 1, -1):
                name_part = prefix[-name_len:]
                if 2 <= len(name_part) <= 16:
                    # 修剪前导噪声字（允许去掉开头 1-2 个非名称字）
                    trimmed = name_part
                    while len(trimmed) > 2 and trimmed[0] in _PREFIX_NOISE:
                        trimmed = trimmed[1:]
                    if 2 <= len(trimmed) <= 16:
                        candidates.append((start + len(prefix) - len(trimmed),
                                          len(trimmed),
                                          trimmed + suffix))

            idx += len(suffix)

    if not candidates:
        return None

    # 排序：优先右起（靠后的提取更精准），再选最短的名称
    candidates.sort(key=lambda x: (-x[0], x[1]))
    return candidates[0][2]


# 知名大学简称 → 全称：数据已迁移到 ./school_abbrev.py，
# 通过 `_UNIV_ABBREV` 别名导入以保持下面所有引用代码不变。


def _parse_undergrad(text: str) -> str | None:
    # 1. 优先提取完整的 XX大学/XX学院（能避免"山大"误匹配"中山大学"）
    full = _extract_best_university(text)
    if full:
        return full

    # 2. 简称匹配（在全文提取之后用简单 in，不会误吞完整大学名）
    for abbrev, full_name in _UNIV_ABBREV.items():
        if abbrev in text:
            return full_name

    # 3. 检查层次关键词（985/211/双非等）
    tier = _parse_upgrad(text)
    if tier:
        return tier

    # 4. "本科: XXX" / "学校: XXX" 前缀模式（必须带冒号）
    m = _undergrad_pattern.search(text)
    if m:
        school = m.group(1).strip()
        if len(school) <= 30 and school not in ("的", "了"):
            return school

    return None


# =====================================================================
# 用户画像提取
# =====================================================================

def _parse_profile(user_input: str) -> dict | None:
    """从用户提问中解析背景信息,返回 recommend.run() 所需的 profile dict。
    解析失败返回 None。
    """
    gpa_match = re.search(
        r"(?:GPA|gpa|均分|绩点)\s*[:：]?\s*(\d+\.?\d*)", user_input
    )
    if not gpa_match:
        return None
    gpa = float(gpa_match.group(1))

    gpa_format = _infer_gpa_format(gpa)
    if gpa_format is None:
        return None

    countries = _parse_countries(user_input)
    if not countries:
        return None

    level_match = re.search(r"(本科|硕士|博士)", user_input)
    study_level = level_match.group(1) if level_match else "硕士"

    major = _parse_major(user_input)
    undergrad = _parse_undergrad(user_input)

    # 解析标化考试成绩
    gre = _parse_gre(user_input)
    toefl = _parse_toefl(user_input)
    ielts = _parse_ielts(user_input)

    return {
        "target_countries": countries,
        "gpa_score": gpa,
        "gpa_format": gpa_format,
        "gre_score": gre,
        "toefl_score": toefl,
        "ielts_score": ielts,
        "study_level": study_level,
        "target_major": major,
        "original_major": major,
        "undergraduate_school": undergrad,
    }


def _extract_profile_from_history(messages: list[dict]) -> dict:
    """从全部对话历史中提取累积的用户画像。
    
    不同于 _parse_profile()（一旦没找到 GPA 就返回 None），
    此函数逐个字段提取，能返回部分完成的 profile。
    """
    combined = " ".join(
        m["content"] for m in messages if m["role"] == "user"
    )

    profile: dict = {}

    # GPA（支持对话上下文）
    gpa_score, gpa_fmt = _parse_gpa_from_conversation(messages)
    if gpa_score is not None:
        profile["gpa_score"] = gpa_score
        if gpa_fmt:
            profile["gpa_format"] = gpa_fmt

    # 目标国家/地区
    countries = _parse_countries(combined)
    if countries:
        profile["target_countries"] = countries

    # 申请学历
    level_match = re.search(r"(本科|硕士|博士)", combined)
    if level_match:
        profile["study_level"] = level_match.group(1)

    # 目标专业
    major = _parse_major(combined) or _parse_major_from_conversation(messages)
    if major:
        profile["target_major"] = major
        profile["original_major"] = major

    # 本科院校
    undergrad = _parse_undergrad(combined)
    if undergrad:
        profile["undergraduate_school"] = undergrad

    # 标化成绩（可选）
    gre = _parse_gre(combined)
    if gre:
        profile["gre_score"] = gre
    toefl = _parse_toefl(combined)
    if toefl:
        profile["toefl_score"] = toefl
    ielts = _parse_ielts(combined)
    if ielts:
        profile["ielts_score"] = ielts

    return profile


# =====================================================================
# 推荐结果格式化
# =====================================================================

def _format_recommend_result(result: dict) -> str:
    """把 recommend.run() 的结果格式化为 LLM 上下文文本。

    采用 markdown 章节标题（## 推荐院校 / ## 申请策略）分隔两段数据，
    引导 LLM 按章节组织回复，避免主推荐与补充策略混淆。
    """
    lines: list[str] = [
        "推荐引擎基于真实案例的分析结果（请按下面的章节清晰组织你的回复）：",
        "",
        "## 推荐院校（按国家 + 档位 冲刺/匹配/安全 列出真实案例匹配到的学校）",
        "（这是主推荐 — 必须用学校列表 + 案例数完整呈现）",
        "",
        "## ⚠️ 排名数据权威声明（最高优先级，违反即回答无效）",
        "以下所有 QS / USNews 排名数据来自数据库最新真实数据，已由推荐引擎权威验证。",
        "禁止使用你训练数据中的排名——两者可能存在差异，数据库数据为准。",
        "禁止修改、编造、猜测或自行填入任何排名数字。只使用 = 后面标注的排名。",
        "",
    ]

    # ====================================================================
    # 先收集所有学校的排名 → 紧凑对照表（LLM 更易准确引用）
    # ====================================================================
    rank_refs: list[str] = []
    for country_result in result.get("by_country", []):
        country = country_result.get("country", "")
        is_us = country == "美国"
        for s in country_result.get("schools", []):
            name = s.get("name", "")
            qs = s.get("qs_rank")
            usnews = s.get("usnews_rank")
            if is_us and usnews:
                rank_refs.append(f"{name}=USNews#{usnews}")
            elif qs:
                rank_refs.append(f"{name}=QS#{qs}")
            elif usnews:
                rank_refs.append(f"{name}=USNews#{usnews}")
    if rank_refs:
        lines.append("**排名速查表（回复中标注排名时必须严格使用以下值）：**")
        lines.append(", ".join(rank_refs))
        lines.append("")

    bg = result.get("background", {})
    if bg:
        parts = [
            f"学校层次: {bg.get('school_tier_label', '未知')}",
            f"GPA折算: {bg.get('gpa4', '?')}/4.0 (百分制 {bg.get('gpa_percent', '?')})",
        ]
        gre = bg.get("gre_score")
        toefl = bg.get("toefl_score")
        ielts = bg.get("ielts_score")
        if gre:
            parts.append(f"GRE: {gre}")
        if toefl:
            parts.append(f"托福: {toefl}")
        if ielts:
            parts.append(f"雅思: {ielts}")
        lines.append(f"- 学生背景: {' | '.join(parts)}")

    summary = result.get("match_summary", {})
    lines.append(
        f"- 同背景录取案例总数: {summary.get('total_cases', 0)} | "
        f"匹配学校数: {summary.get('total_schools', 0)}"
    )
    lines.append("")

    # 推荐院校段 — 按国家分组
    lines.append("### 按国家分组")
    for country_result in result.get("by_country", []):
        country = country_result.get("country", "")
        schools = country_result.get("schools", [])
        if not schools:
            continue
        lines.append(f"\n【{country}】同背景录取 {country_result.get('matched_cases', 0)} 案例:")

        # 按档位分组展示（冲刺/匹配/安全）
        chance_groups: dict[str, list] = {"冲刺": [], "匹配": [], "安全": [], "未知": []}
        for s in schools:
            chance = s.get("admission_chance", "未知")
            if chance not in chance_groups:
                chance = "未知"
            chance_groups[chance].append(s)

        chance_labels = {"冲刺": "⚡ 冲刺", "匹配": "🎯 匹配", "安全": "✅ 安全", "未知": "❓ 未知"}
        for chance in ("冲刺", "匹配", "安全", "未知"):
            group = chance_groups.get(chance, [])
            if not group:
                continue
            lines.append(f"  {chance_labels[chance]} ({len(group)}所):")
            for s in group:
                name = s.get("name", "")
                qs = s.get("qs_rank")
                usnews = s.get("usnews_rank")
                cases = s.get("matched_cases", 0)
                p50 = s.get("gpa_p50")
                score = s.get("admission_score", 0)
                gap = s.get("gpa_gap")
                majors = s.get("majors", [])
                
                if country == "美国" and usnews:
                    rank_str = f" USNews#{usnews}"
                elif qs:
                    rank_str = f" QS#{qs}"
                else:
                    rank_str = ""
                
                p50_str = f" | 录取GPA中位数 {p50}" if p50 else ""
                gap_str = f" | 需提分 {gap}百分点可进匹配档" if chance == "冲刺" and gap else ""
                majors_str = ""
                if majors:
                    shown = majors[:3]
                    more = len(majors) - 3
                    majors_str = f" | 录取专业: {'/'.join(shown)}"
                    if more > 0:
                        majors_str += f" 等{more}个专业"
                lines.append(
                    f"    - {name}{rank_str} | {cases} 例{p50_str}{majors_str}{gap_str}"
                )

    lines.append("")
    lines.append("---")
    lines.append("")

    # 申请策略段 — 单独章节（补充，不喧宾夺主）
    pathways = result.get("pathway_suggestions", [])
    lines.append("## 申请策略（针对你背景的补充策略 — 预科/桥梁/双录取等）")
    lines.append("（这是基于你背景的申请路径建议，不是主推荐。简要列出即可，不要重复院校段已讲的内容）")
    lines.append("")
    if pathways:
        lines.append("可考虑的策略:")
        for p in pathways[:3]:
            uni = p.get("university", "")
            reason = p.get("reason", "")
            programs = p.get("programs", [])
            lines.append(f"  - {uni}: {reason}")
            for prog in programs[:3]:
                prog_type = prog.get("program_type", "")
                duration = prog.get("duration", "")
                academic = prog.get("academic_req", "")
                ielts = prog.get("ielts_req", "")
                detail = f"{prog.get('provider', '')} {prog_type}"
                if duration:
                    detail += f" | {duration}"
                if academic:
                    detail += f" | 入学学术要求: {academic}"
                if ielts:
                    detail += f" | 语言要求: 雅思 {ielts}"
                lines.append(f"    · {detail}")
    else:
        lines.append("（你的背景适合直录，无需特别策略）")

    return "\n".join(lines)


# ====================================================================
# 广告检测：知识库中混入的部分软广不应被推荐给用户
# ====================================================================

# 强信号：直接判定为广告
_AD_STRONG_PATTERNS = [
    # 导流/诱导
    "立即咨询", "立即报名", "立即申请", "立即领取",
    "免费咨询", "免费领取", "限时领取", "限时优惠", "限时免费",
    "点击咨询", "在线咨询", "预约咨询",
    # 物料导流
    "大礼包", "领取资料", "领取福利", "免费资料",
    # 品牌推广（以内容名义行销特定机构）
    "棕榈君专门", "棕榈君为你",
    # 联系方式/私域导流
    "扫码", "添加微信", "联系顾问", "联系我们",
    "微信扫一扫", "后台回复",
    # 留学广告常见话术
    "免费评估", "免费选校", "免费定位",
    "名额有限", "抢占名额",
    "名校保录取", "保录取",
    # 留学服务承诺（保分/保过/保offer — 不同于保录取，多见于语培/中介软文）
    "保分", "保过", "保offer",
    # 试听/低价导流
    "免费试听", "0元试听", "试听课", "9.9元", "限时秒杀",
    # 促销/优惠
    "报名立减", "优惠券", "抢先报名",
    # 社群/私域导流扩展（"扫码"之外的新话术）
    "加微咨询", "进群咨询", "进群领取",
    # 代报名服务
    "代报名",
    # 新增：更多广告模式
    "私信领取", "私信回复", "后台回复",
    "加微信", "加V", "加微",
    "0元领", "0元学", "1元学",
    "限时秒杀", "限量特惠",
    "免费领取", "免费获取",
    "课程顾问", "规划师",
    "留学中介", "代办",
]

# 弱信号：当出现多个时判定为广告
_AD_WEAK_PATTERNS = [
    "限时", "优惠", "免费", "赠送", "名额",
    "独家", "首发", "首次",
    "点击", "链接",
    "推荐信表格", "forms.office.com",
    # 常见广告弱信号
    "规划", "背景提升", "名校",
    "offer", "录取案例",
    # 促销弱信号
    "秒杀", "拼团", "倒计时", "钜惠", "特惠",
    # 新增弱信号
    "关注", "回复", "福利", "领取",
    "干货", "收藏", "转发",
]

# UI 碎片模式（爬取残留，本身不表示广告，但大量出现说明内容质量低）
_UI_NOISE_PATTERNS = [
    "小程序", "视频小程序",
    "轻触阅读原文",
    "取消允许",
    "点赞", "在看", "分享",
    "向上滑动", "使用完整服务",
    "轻点两下取消",
    "长按识别",
    # 新增 UI 噪音
    "阅读原文", "喜欢此内容", "人划线",
    "摩拜", "ofo", "微信扫一扫关注",
    "该内容由", "编辑：", "责编：",
    "排版：", "审核：",
]

# 品牌来源白名单：纯资讯类的来源品牌不判定为广告
_BRAND_SOURCES = {
    "棕榈君", "启德", "新东方", "前途出国", "棕榈大道",
    "金吉列", "澳际", "芥末留学", "留学360",
    "美世留学", "再来人", "托普仕",
}


def _is_likely_ad(snippet: str, title: str = "") -> bool:
    """检测知识库条目是否可能是广告/软广"""
    combined = f"{title} {snippet}"

    # 品牌来源白名单：知名留学媒体/机构的纯资讯内容不做广告判定
    for brand in _BRAND_SOURCES:
        if brand in combined:
            return False

    # 强信号：任一匹配即判定为广告
    for pattern in _AD_STRONG_PATTERNS:
        if pattern in combined:
            return True

    # 弱信号：匹配 ≥2 个判定为广告
    weak_hits = sum(1 for p in _AD_WEAK_PATTERNS if p in combined)
    if weak_hits >= 2:
        return True

    # UI 碎片检测（长模式优先，避免"轻触阅读原文"与"阅读原文"重叠计数）
    ui_hits = 0
    covered: set[int] = set()
    for p in sorted(_UI_NOISE_PATTERNS, key=len, reverse=True):
        start = 0
        while True:
            idx = combined.find(p, start)
            if idx == -1:
                break
            # 检查是否已被更长的模式覆盖
            if not any(c <= idx < c + len(p) for c in covered):
                ui_hits += 1
                covered.add(idx)
            start = idx + 1
    if ui_hits >= 2:
        return True

    # 有效中文占比过低（如只有标点/空白/UI 模板文字）
    chinese_chars = sum(1 for c in combined if '\u4e00' <= c <= '\u9fff')
    total_chars = len(combined.strip())
    if total_chars > 20 and chinese_chars / total_chars < 0.4:
        return True

    return False
