from __future__ import annotations

import json
import logging
import httpx
from typing import Any, TYPE_CHECKING
from ..core.config import settings
from ..core.database import get_db
from .news_knowledge import search_articles
from .essay_knowledge import is_essay_query, build_essay_context
from .recommend import run as run_recommend
from .chat_prompts import (
    SYSTEM_PROMPT,
    GENERIC_GATHERING_INSTRUCTION,
    RECOMMEND_GATHERING_INSTRUCTION,
)
from .chat_utils import (
    _is_likely_ad,
    _extract_profile_from_history,
    _format_recommend_result,
)

if TYPE_CHECKING:
    # 仅用于类型标注；运行时由 _stream_response 内部按需 import，避免模块加载时引入 fastapi 依赖
    from fastapi.responses import StreamingResponse


logger = logging.getLogger(__name__)



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


# ---------------------------------------------------------------------------
# 推荐引擎触发条件（收紧版，避免无关对话误触发）
# ---------------------------------------------------------------------------

# 强信号：含任一即触发选校推荐
STRONG_RECOMMEND_KEYWORDS = [
    "选校", "选校定位", "学校推荐", "推荐学校", "匹配学校",
    "定位", "冲刺", "保底", "主申",
    "录取概率", "录取案例",
    "留学选校",
]

# 弱信号：需要至少命中 2 个才触发（或与强信号叠加时按 1 个计算）
WEAK_RECOMMEND_KEYWORDS = [
    "GPA", "gpa", "均分", "绩点", "分数",
    "留学申请", "申请留学",
    "录取", "申请",
]

# 排除词：包含这些词时不视为选校意图
RECOMMEND_EXCLUDE = ["推荐信", "推荐人"]


def load_context_from_history(messages: list[dict]) -> tuple[str, dict | None]:
    """构建 LLM system 消息，并在触发推荐时一并返回结构化推荐结果。

    返回值: (system_msg, recommend_payload)
        - recommend_payload 为 run_recommend() 的原始 dict（含 pathway_suggestions），
          仅当选校意图且 profile 完整且推荐引擎成功时非 None；其余情况为 None。
        - 前端可据此渲染 PathwaySection，无需依赖 LLM 在 Markdown 回复里转述。
    """
    parts = [SYSTEM_PROMPT]
    recommend_payload: dict | None = None

    user_msgs = [m for m in messages if m["role"] == "user"]
    if not user_msgs:
        return "\n".join(parts), None

    last_user = user_msgs[-1]["content"]

    # ====================================================================
    # 1. 加载相关历史数据（排名趋势、选校建议等，供 LLM 引用）
    # ====================================================================
    try:
        articles = search_articles(last_user, limit=8)
        if articles:
            lines = [
                "【你的知识储备】（以下信息来自历年留学案例和行业观察，"
                "部分来源于第三方机构，请审慎判断，辨别客观数据与商业推广）："
            ]
            ad_skipped = 0
            # 按时间排序：优先近期文章（时间降权）
            import time as _time
            now_ts = _time.time()
            scored_articles = []
            for a in articles:
                snippet = a.get("content_snippet") or a.get("description") or ""
                title = a.get("title", "").strip()
                # 广告检测
                if _is_likely_ad(snippet, title):
                    ad_skipped += 1
                    continue
                # 跳过标题行，避免文章感
                if title and snippet.startswith(title):
                    snippet = snippet[len(title):].strip()
                if not snippet:
                    continue
                # 时间降权：6个月内的文章优先
                pub_time = a.get("publish_time")
                if pub_time:
                    age_days = (now_ts - pub_time) / 86400
                    if age_days > 365:
                        continue  # 超过1年的文章不注入
                scored_articles.append((snippet, pub_time or 0))

            # 按发布时间降序排列，取最新的5条
            scored_articles.sort(key=lambda x: x[1], reverse=True)
            for snippet, _ in scored_articles[:5]:
                lines.append(f"\n- {snippet}")
            if ad_skipped > 0:
                lines.append(f"\n（注：另有 {ad_skipped} 条推广内容已过滤）")
            if len(lines) > 1:
                parts.append(" ".join(lines))
    except Exception:
        logger.warning("load_article_context failed", exc_info=True)

    # ====================================================================
    # 1b. 注入文书辅导知识（当问题涉及文书写作时）
    # ====================================================================
    try:
        if is_essay_query(last_user):
            essay_ctx = build_essay_context(last_user)
            if essay_ctx:
                parts.append(
                    "【文书辅导知识库】\n"
                    "以下为文书写作相关参考信息，请以顾问身份自然融入回复，不要提及'文库''资料'等词。\n"
                    + essay_ctx
                )
    except Exception:
        logger.warning("load_essay_context failed", exc_info=True)

    # ====================================================================
    # 2. 判断用户意图：选校相关 vs 通用问答
    # ====================================================================
    # 优先按最新一条消息判断——如果用户刚问的是文书/签证，就不走选校推荐
    NON_RECOMMEND_KEYWORDS = [
        "文书","PS","个人陈述","简历","CV","推荐信","推荐人",
        "写作","怎么写","怎么写好","如何写","怎么写好",
        "签证","F-1","Tier 4","I-20","面签","签证材料",
    ]
    if any(k in last_user for k in NON_RECOMMEND_KEYWORDS):
        is_recommend_intent = False
    else:
        all_user_text = " ".join(m["content"] for m in user_msgs)
        if any(e in all_user_text for e in RECOMMEND_EXCLUDE):
            is_recommend_intent = False
        else:
            # 强信号：含任一即视为选校意图
            strong_hit = any(k in all_user_text for k in STRONG_RECOMMEND_KEYWORDS)
            # 弱信号：需要至少命中 2 个
            weak_hits = sum(1 for k in WEAK_RECOMMEND_KEYWORDS if k in all_user_text)
            is_recommend_intent = strong_hit or weak_hits >= 2

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
                # 把结构化结果透传给前端，用于渲染 PathwaySection 等结构化卡片
                recommend_payload = result
            except Exception:
                logger.warning("load_recommend_context failed", exc_info=True)
    else:
        # --- 通用模式（文书、签证等）：通用信息收集 ---
        parts.append(GENERIC_GATHERING_INSTRUCTION)

    return "\n".join(parts), recommend_payload


async def call_llm(messages: list[dict], stream: bool = False) -> tuple[str, dict | None] | StreamingResponse:
    provider = settings.LLM_PROVIDER
    api_key = settings.LLM_API_KEY
    base_url = settings.LLM_BASE_URL
    model = settings.LLM_MODEL

    if not api_key:
        return "抱歉，AI 对话功能尚未配置。请联系管理员设置 LLM_API_KEY。", None

    system_msg, recommend_payload = load_context_from_history(messages)

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
        "max_tokens": 4096,
        "stream": stream,
    }

    if stream:
        return _stream_response(url, headers, payload, recommend_payload)

    fallback_model = settings.LLM_FALLBACK_MODEL
    attempted_models = [model]

    for attempt in range(2):
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
            resp = await client.post(url, json=payload, headers=headers)

        if resp.is_success:
            data = resp.json()
            return data["choices"][0]["message"]["content"], recommend_payload

        # 非成功响应 — 检查是否需要切备用模型
        if attempt == 0 and fallback_model and resp.status_code in (401, 402, 429, 500, 502, 503):
            logger.warning(
                "Primary model %s failed (HTTP %d), falling back to %s",
                model, resp.status_code, fallback_model,
            )
            payload["model"] = fallback_model
            attempted_models.append(fallback_model)
            continue

        resp.raise_for_status()

    # 不应到达此处
    raise RuntimeError(f"All models failed: {attempted_models}")


def _stream_response(url: str, headers: dict, payload: dict, recommend_payload: dict | None = None) -> StreamingResponse:
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
                # 在 [DONE] 之前下发结构化推荐结果（含 pathway_suggestions），
                # 前端 streamChat 通过 onRecommendPayload 回调接收并挂到 assistant 消息上
                if recommend_payload is not None:
                    yield f"data: {json.dumps({'recommend_payload': recommend_payload})}\n\n"
                yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


async def chat(messages: list[dict], stream: bool = False) -> dict[str, Any] | StreamingResponse:
    if not settings.LLM_API_KEY:
        return {
            "reply": "抱歉，AI 对话功能尚未配置。请联系管理员设置 LLM_API_KEY。",
            "messages": messages + [
                {"role": "assistant", "content": "抱歉，AI 对话功能尚未配置。请联系管理员设置 LLM_API_KEY。"}
            ],
            "recommend_payload": None,
        }

    if stream:
        return await call_llm(messages, stream=True)

    result = await call_llm(messages, stream=False)
    # call_llm 非流式返回 (content_str, recommend_payload)
    reply, recommend_payload = result
    return {
        "reply": reply,
        "messages": messages + [{"role": "assistant", "content": reply}],
        "recommend_payload": recommend_payload,
    }
