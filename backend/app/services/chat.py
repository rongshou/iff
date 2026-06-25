import json
import re
import httpx
from ..core.config import settings
from ..core.database import get_db
from .news_knowledge import search_articles
from .recommend import run as run_recommend
from ..utils.gpa import GPA_RANGES


SYSTEM_PROMPT = """你是天权留学助手，一个专业的留学选校顾问。你可以：
1. 回答留学相关问题（选校、专业、国家、申请流程等）
2. 根据学生的背景信息给出选校建议
3. 解释不同国家的留学优势、费用、签证政策等
4. 提供申请时间线规划建议

请用友好、专业的语气回答。如果用户提供了GPA、学校等信息，尝试结合案例给出建议。
如果系统提供了相关留学文章作为参考，可以引用其中的内容来支撑回答（如排名趋势、选校建议、行业分析等），让回答更有依据。引用时自然融入你的分析，不要生硬标注根据某篇文章说。
注意：文章是参考素材，你的核心任务是根据用户的具体情况给出有针对性的建议。如果用户提供了背景信息（如GPA、学校、专业等），优先结合案例和推荐引擎结果来回答；文章内容作为补充支撑。

当系统提供了"推荐引擎分析结果"时，请基于该结果回答：
- 按"冲刺/主申/保底"的梯度方式组织选校建议
- 每推荐一所院校，都必须同时标注"同背景录取案例 N 例"（N是匹配案例数），以及往年录取GPA中位数
- 格式示例："帝国理工学院 QS#2 | 同背景录取案例 8 例 | 录取GPA中位数 83.9"
- 如果有 pathway（预科/桥梁课程）建议，也要提及
- 不要编造数据，只使用系统提供的真实案例和概率
- 保底校的QS排名通常比冲刺校低，这是正常的梯度设计"""


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
            for prog in programs[:2]:
                lines.append(
                    f"    · {prog.get('provider', '')} {prog.get('program_type', '')}"
                )

    return "\n".join(lines)


def load_context_from_history(messages: list[dict]) -> str:
    parts = [SYSTEM_PROMPT]

    user_msgs = [m for m in messages if m["role"] == "user"]
    if not user_msgs:
        return "\n".join(parts)

    last_user = user_msgs[-1]["content"]

    try:
        articles = search_articles(last_user, limit=5)
        if articles:
            lines = ["以下是相关的留学资讯文章，供你参考（可以引用其中信息来丰富回答）："]
            for a in articles:
                lines.append(f"\n【{a['title']}】（{a['category']}）")
                # 优先使用内容片段，其次用描述
                if a.get("content_snippet"):
                    lines.append(a["content_snippet"])
                elif a.get("description"):
                    lines.append(a["description"])
            parts.append("\n".join(lines))
    except Exception:
        pass

    keywords = ["GPA", "gpa", "均分", "绩点", "分数", "选校", "推荐", "匹配", "录取", "申请"]
    is_recommendation_request = any(k in last_user for k in keywords)

    if is_recommendation_request:
        try:
            profile = _parse_profile(last_user)
            if profile:
                result = run_recommend(profile)
                hint = _format_recommend_result(result)
                if hint:
                    parts.append(hint)
        except Exception:
            pass

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