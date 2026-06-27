import json
import re
import httpx
from ..core.config import settings
from ..core.database import get_db
from .news_knowledge import search_articles
from .recommend import run as run_recommend
from ..utils.gpa import GPA_RANGES, GPA_FORMAT_ALIASES
from ..utils.countries import VALID_COUNTRIES



# =====================================================================
# 信息收集：推荐引擎所需的用户画像字段及追问模板
# =====================================================================

# 核心必填字段（缺一不可，否则不调推荐引擎）
# 每个字段对应一个自然提问模板
REQUIRED_PROFILE_FIELDS: list[dict] = [
    {
        "field": "gpa_score",
        "label": "GPA",
        "check": lambda p: p.get("gpa_score") is not None,
        "questions": [
            "你的 GPA 是多少？是什么分制（比如 4分制、5分制、百分制）？",
            "方便说一下你的 GPA 和分制吗？",
            "你的绩点或均分大概多少？",
        ],
    },
    {
        "field": "undergraduate_school",
        "label": "毕业学校",
        "check": lambda p: p.get("undergraduate_school") is not None,
        "questions": [
            "你的毕业学校是什么？是高中、大专、本科还是其他？学校大概是什么层次？",
            "你目前就读或毕业于哪所学校？是什么学历层次？",
        ],
    },
    {
        "field": "target_countries",
        "label": "目标国家/地区",
        "check": lambda p: p.get("target_countries") not in (None, [], ""),
        "questions": [
            "你打算申请哪些国家或地区？比如英国、美国、澳洲、香港、新加坡……",
            "有想去的国家或地区吗？",
        ],
    },
    {
        "field": "study_level",
        "label": "申请学历",
        "check": lambda p: p.get("study_level") is not None,
        "questions": [
            "你要申请本科、硕士还是博士？",
            "打算读哪个阶段？本科、硕士还是博士？",
        ],
    },
    {
        "field": "target_major",
        "label": "目标专业",
        "check": lambda p: (
            p.get("target_major") is not None
            and p["target_major"] not in ("其他", "其它", "不限", "不确定", "还没想好", "未定")
        ),
        "questions": [
            "你想申请什么专业方向？可以继续深挖本专业，也可以考虑跨到计算机、商科或其他方向——你更倾向哪一种？",
            "有目标专业吗？比如继续读本专业、转CS/商科，或者其他方向？",
        ],
    },
]


def _get_missing_fields(profile: dict) -> list[dict]:
    """返回 profile 中缺失的字段定义列表"""
    return [f for f in REQUIRED_PROFILE_FIELDS if not f["check"](profile)]


def _is_profile_complete(profile: dict) -> bool:
    """检查用户画像是否满足推荐引擎所需的核心字段"""
    return len(_get_missing_fields(profile)) == 0


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


# 关键词：用于判断用户意图（选校推荐 vs 通用问答）
# 注意：避免被"推荐信"这类词组误触发
RECOMMEND_KEYWORDS = [
    "选校", "选校定位", "学校推荐", "推荐学校", "匹配学校",
    "定位", "冲刺", "保底", "主申",
    "GPA", "gpa", "均分", "绩点",
    "录取概率", "录取案例",
    "留学申请", "申请留学", "留学选校",
]

# 排除词：包含这些词时不视为选校意图
RECOMMEND_EXCLUDE = ["推荐信", "推荐人"]

GENERIC_GATHERING_INSTRUCTION = """【信息收集模式】在回答之前，先通过对话了解用户的具体情况。

**规则**：
1. 不要在不了解背景的情况下直接给出详细建议。
2. 每次问 1 个问题，用友好、自然的语气逐步了解情况。
3. 信息收集完整后再给出有针对性的回答。"""

RECOMMEND_GATHERING_INSTRUCTION = """【选校信息收集模式】你正在以对话方式收集用户进行选校推荐所需的完整背景信息。

**你的任务**：通过自然的对话，逐步收集用户的 GPA/均分、毕业学校、目标国家、申请学历和目标专业。

**规则**：
1. 每次最多问 1 个方面的问题，不要一次性列出所有问题。
2. 用友好、自然的语气提问，不要像表单一样生硬。
3. 当用户提供的信息不够明确时（比如只说"均分80"没说分制），追问细节。
4. **绝对不要自行编造选校方案或学校列表。** 没有推荐引擎数据时，你能做的只有收集信息。
5. 如果用户问了一个其他方面的问题（比如签证流程），可以先简要回答，然后继续收集选校所需的信息。
6. 收集完所有信息后，系统会自动调用推荐引擎并提供分析结果，届时你会看到"推荐引擎分析结果"的标识。在没有这个标识之前，不要做选校推荐。
7. 如果用户说"随便"、"其他"、"还没想好"等模糊的目标专业，请友好地引导用户思考一下方向，而不是跳过这个字段。"""


SYSTEM_PROMPT = """你是天权留学助手，一个专业的留学选校顾问。你可以：
1. 回答留学相关问题（选校、专业、国家、申请流程等）
2. 根据学生的背景信息给出选校建议
3. 解释不同国家的留学优势、费用、签证政策等
4. 提供申请时间线规划建议

请用友好、专业的语气回答。如果用户提供了GPA、学校等信息，尝试结合案例给出建议。
如果系统提供了相关历史数据作为参考，可以引用其中的内容来支撑回答（如排名趋势、选校建议、行业分析等），让回答更有依据。引用时统一使用"历史数据显示"来引出，不要使用"文章中显示"、"系统文章显示"等说法，避免生硬标注来源。
注意：历史数据是参考素材，你的核心任务是根据用户的具体情况给出有针对性的建议。如果用户提供了背景信息（如GPA、学校、专业等），优先结合案例和推荐引擎结果来回答；历史数据内容作为补充支撑。

当系统提供了"推荐引擎分析结果"时，请基于该结果回答：
- 按"冲刺/主申/保底"的梯度方式组织选校建议
- 每推荐一所院校，都必须同时标注"同背景录取案例 N 例"（N是匹配案例数），以及往年录取GPA中位数
- 格式示例："帝国理工学院 QS#2 | 同背景录取案例 8 例 | 录取GPA中位数 83.9"
- 如果有 pathway（预科/桥梁课程）建议，也要提及
- 不要编造数据，只使用系统提供的真实案例和概率
- 保底校的QS排名通常比冲刺校低，这是正常的梯度设计

【Pathway 预科数据说明】
当推荐结果中包含 pathway 预科/桥梁课程数据时，请注意区分不同层级的入学要求：
- "硕士预科 (Pre-Master)" 是为已有本科学位但条件不足直接读硕的学生设置的，其入学要求（"本科毕业"）指的是入读预科的前提条件，不是本科直录的条件。语言要求通常是雅思 5.5，这是预科的语言门槛，不是硕士直录的语言门槛（硕士直录通常要求 6.5+）。
- "本科预科 (Foundation)" 是为高二/高三学生设置的本科前桥梁课程，入学要求是高中成绩（如高二75%），语言要求通常是雅思 5.0-5.5。
- 描述时一定要区分清楚是哪种预科，不要混淆两者的要求，也不要把预科的语言要求说成直录的语言要求。"""


# 国家/地区别名 → 推荐引擎识别的正式名
COUNTRY_ALIASES = {
    "英国": "英国", "美国": "美国", "澳洲": "澳大利亚", "澳大利亚": "澳大利亚",
    "加拿大": "加拿大", "香港": "中国香港", "港": "中国香港",
    "新加坡": "新加坡", "日本": "日本", "德国": "德国", "法国": "法国",
    "新西兰": "新西兰", "爱尔兰": "爱尔兰", "荷兰": "荷兰",
    "韩国": "韩国", "马来西亚": "马来西亚", "澳门": "中国澳门",
}

VALID_COUNTRIES = set(COUNTRY_ALIASES.values())


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


def _infer_gpa_format(gpa: float) -> str | None:
    """根据 GPA 数值推断分制"""
    for fmt, (lo, hi) in GPA_RANGES.items():
        if lo <= gpa <= hi:
            if fmt == "学位等级对应分数" or fmt == "英制百分制":
                continue
            return fmt
    return None


def _parse_countries(text: str) -> list[str]:
    found: list[str] = []
    for alias, formal in COUNTRY_ALIASES.items():
        if alias in text and formal not in found:
            found.append(formal)
    return found


_MAJOR_STOPWORDS = {
    "香港", "英国", "美国", "澳洲", "澳大利亚", "加拿大", "新加坡", "日本",
    "德国", "法国", "新西兰", "爱尔兰", "荷兰", "韩国", "马来西亚", "澳门",
    "中国香港", "中国澳门", "硕士", "本科", "博士", "申请", "留学", "选校",
    "专业", "方向", "什么", "哪些", "可以", "可能", "怎么", "如何", "我的",
    "申请香港硕士", "申请英国硕士", "申请美国硕士", "申请澳洲硕士",
    "读硕士", "读本科", "读博士", "想读", "想去",
}


def _parse_major(text: str) -> str | None:
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


_undergrad_pattern = re.compile(r"(?:本科|本科院校|学校|院校)\s*[:：]?\s*(\S+?)(?:[，。,.\s]|$)")


def _parse_undergrad(text: str) -> str | None:
    tier = _parse_upgrad(text)
    if tier:
        return tier
    m = _undergrad_pattern.search(text)
    if m:
        school = m.group(1).strip()
        if len(school) <= 30 and school not in ("的", "了"):
            return school
    return None


def _format_recommend_result(result: dict) -> str:
    """把 recommend.run() 的结果格式化为 LLM 上下文文本"""
    lines: list[str] = ["推荐引擎基于真实案例的分析结果（请基于此数据回答）："]

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

    for country_result in result.get("by_country", []):
        country = country_result.get("country", "")
        schools = country_result.get("schools", [])
        if not schools:
            continue
        lines.append(f"\n【{country}】同背景录取 {country_result.get('matched_cases', 0)} 案例:")

        # 按档位分组展示
        chance_groups: dict[str, list] = {"冲刺": [], "匹配": [], "安全": [], "彩票": [], "未知": []}
        for s in schools:
            chance_groups.get(s.get("admission_chance", "未知"), chance_groups["未知"]).append(s)

        chance_labels = {"冲刺": "🎯 冲刺", "匹配": "🎓 主申", "安全": "🛡️ 保底", "彩票": "🎲 彩票", "未知": "❓ 未知"}
        for chance in ("冲刺", "匹配", "安全", "彩票", "未知"):
            group = chance_groups.get(chance, [])
            if not group:
                continue
            lines.append(f"  {chance_labels[chance]} ({len(group)}所):")
            for s in group:
                name = s.get("name", "")
                qs = s.get("qs_rank")
                cases = s.get("matched_cases", 0)
                p50 = s.get("gpa_p50")
                qs_str = f" QS#{qs}" if qs else ""
                p50_str = f" | 往年录取GPA中位数 {p50}" if p50 else ""
                lines.append(
                    f"    - {name}{qs_str} | 同背景录取案例 {cases} 例{p50_str}"
                )

    pathways = result.get("pathway_suggestions", [])
    if pathways:
        lines.append("\n【Pathway 预科/桥梁课程建议】:")
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

    return "\n".join(lines)


def load_context_from_history(messages: list[dict]) -> str:
    parts = [SYSTEM_PROMPT]

    user_msgs = [m for m in messages if m["role"] == "user"]
    if not user_msgs:
        return "\n".join(parts)

    last_user = user_msgs[-1]["content"]

    # ====================================================================
    # 1. 加载相关历史数据（排名趋势、选校建议等，供 LLM 引用）
    # ====================================================================
    try:
        articles = search_articles(last_user, limit=5)
        if articles:
            lines = ["以下是相关的历史数据，供你参考（可以引用其中信息来丰富回答）："]
            for a in articles:
                lines.append(f"\n【{a['title']}】（{a['category']}）")
                if a.get("content_snippet"):
                    lines.append(a["content_snippet"])
                elif a.get("description"):
                    lines.append(a["description"])
            parts.append("\n".join(lines))
    except Exception:
        pass

    # ====================================================================
    # 2. 判断用户意图：选校相关 vs 通用问答
    # ====================================================================
    all_user_text = " ".join(m["content"] for m in user_msgs)
    is_recommend_intent = (
        any(k in all_user_text for k in RECOMMEND_KEYWORDS)
        and not any(e in all_user_text for e in RECOMMEND_EXCLUDE)
    )

    if is_recommend_intent:
        # --- 选校模式：做 5 字段完整性检查 ---
        profile = _extract_profile_from_history(messages)

        if not _is_profile_complete(profile):
            parts.append(RECOMMEND_GATHERING_INSTRUCTION)

            collected = []
            if profile.get("gpa_score"):
                gpa = profile["gpa_score"]
                fmt = profile.get("gpa_format", "未知分制")
                collected.append(f"GPA: {gpa} ({fmt})")
            if profile.get("undergraduate_school"):
                collected.append(f"毕业学校: {profile['undergraduate_school']}")
            if profile.get("target_countries"):
                collected.append(f"目标国家: {', '.join(profile['target_countries'])}")
            if profile.get("study_level"):
                collected.append(f"学历: {profile['study_level']}")
            if profile.get("target_major"):
                collected.append(f"专业: {profile['target_major']}")

            missing_labels = [f["label"] for f in _get_missing_fields(profile)]

            status = ""
            if collected:
                status += f"已收集到: {' | '.join(collected)}\n"
            status += f"还缺少的信息: {'、'.join(missing_labels)}"
            parts.append(status)
        else:
            # profile 已完整，调推荐引擎
            try:
                result = run_recommend(profile)
                hint = _format_recommend_result(result)
                if hint:
                    parts.append(hint)
            except Exception:
                pass
    else:
        # --- 通用模式（文书、签证等）：通用信息收集 ---
        parts.append(GENERIC_GATHERING_INSTRUCTION)

    return "\n".join(parts)


async def call_llm(messages: list[dict], stream: bool = False):
    provider = settings.LLM_PROVIDER
    api_key = settings.LLM_API_KEY
    base_url = settings.LLM_BASE_URL
    model = settings.LLM_MODEL

    if not api_key:
        return "抱歉，AI 对话功能尚未配置。请联系管理员设置 LLM_API_KEY。"

    system_msg = load_context_from_history(messages)

    req_messages = [{"role": "system", "content": system_msg}] + messages

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": req_messages,
        "temperature": 0.7,
        "max_tokens": 8192,
        "stream": stream,
    }

    if stream:
        return _stream_response(url, headers, payload)

    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _stream_response(url: str, headers: dict, payload: dict):
    from fastapi.responses import StreamingResponse

    async def generate():
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:].strip()
                        if chunk == "[DONE]":
                            break
                        try:
                            obj = json.loads(chunk)
                            delta = obj["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield f"data: {json.dumps({'content': content})}\n\n"
                            reasoning = delta.get("reasoning_content", "")
                            if reasoning:
                                yield f"data: {json.dumps({'reasoning': reasoning})}\n\n"
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
                yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


async def chat(messages: list[dict], stream: bool = False):
    if not settings.LLM_API_KEY:
        return {
            "reply": "抱歉，AI 对话功能尚未配置。请联系管理员设置 LLM_API_KEY。",
            "messages": messages + [
                {"role": "assistant", "content": "抱歉，AI 对话功能尚未配置。请联系管理员设置 LLM_API_KEY。"}
            ],
        }

    if stream:
        return await call_llm(messages, stream=True)

    result = await call_llm(messages, stream=False)
    reply = result if isinstance(result, str) else "抱歉，发生了未知错误。"
    return {
        "reply": reply,
        "messages": messages + [{"role": "assistant", "content": reply}],
    }