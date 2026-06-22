import json
import httpx
from ..core.config import settings
from ..core.database import get_db
from .news_knowledge import search_articles


SYSTEM_PROMPT = """你是天权留学助手，一个专业的留学选校顾问。你可以：
1. 回答留学相关问题（选校、专业、国家、申请流程等）
2. 根据学生的背景信息给出选校建议
3. 解释不同国家的留学优势、费用、签证政策等
4. 提供申请时间线规划建议

请用友好、专业的语气回答。如果用户提供了GPA、学校等信息，尝试结合案例给出建议。
如果提供了相关文章参考，可以引用文章内容，但不要给出原文链接。"""


def load_context_from_history(messages: list[dict]) -> str:
    parts = [SYSTEM_PROMPT]

    user_msgs = [m for m in messages if m["role"] == "user"]
    if not user_msgs:
        return "\n".join(parts)

    last_user = user_msgs[-1]["content"]

    try:
        articles = search_articles(last_user, limit=5)
        if articles:
            lines = ["以下是相关留学文章，供你参考（可以引用文章内容，但不要给出链接）："]
            for a in articles:
                if a["description"]:
                    lines.append(f"- {a['title']}（{a['category']}）：{a['description']}")
                else:
                    lines.append(f"- {a['title']}（{a['category']}）")
            parts.append("\n".join(lines))
    except Exception:
        pass

    keywords = ["GPA", "gpa", "均分", "分数", "选校", "推荐", "匹配", "录取", "申请"]
    is_recommendation_request = any(k in last_user for k in keywords)

    if is_recommendation_request:
        try:
            with get_db() as conn:
                hint = _query_study_advice(conn, last_user)
                if hint:
                    parts.append(hint)
        except Exception:
            pass

    return "\n".join(parts)


def _query_study_advice(conn, user_input: str) -> str | None:
    import re

    gpa_match = re.search(r"(?:GPA|gpa|均分)\s*[:：]?\s*(\d+\.?\d*)", user_input)
    country_match = re.search(
        r"(英国|美国|澳洲|加拿大|香港|新加坡|日本|德国|法国|新西兰|爱尔兰|荷兰|瑞典|丹麦|芬兰|挪威|比利时|瑞士|意大利|西班牙|韩国|马来西亚)",
        user_input,
    )
    level_match = re.search(r"(本科|硕士|博士|博士)", user_input)
    major_match = re.search(r"(?:专业|方向)\s*[:：]?\s*(\S+)", user_input)

    if not gpa_match:
        return None

    gpa = float(gpa_match.group(1))
    country = country_match.group(1) if country_match else None
    level = level_match.group(1) if level_match else "硕士"
    major = major_match.group(1) if major_match else None

    sql = """
        SELECT DISTINCT university, country, admitted_major, gpa_score, gpa_format
        FROM cases
        WHERE gpa_score BETWEEN ? AND ? AND study_level = ?
    """
    params: list = [gpa - 0.3, gpa + 0.3, level]

    if country:
        sql += " AND country = ?"
        params.append(country)
    if major:
        sql += " AND (admitted_major LIKE ? OR original_major LIKE ?)"
        params.extend([f"%{major}%", f"%{major}%"])

    sql += " ORDER BY gpa_score DESC LIMIT 10"

    try:
        rows = conn.execute(sql, params).fetchall()
    except Exception:
        return None

    if not rows:
        return None

    lines = ["以下是数据库中部分匹配案例，供你参考："]
    for r in rows:
        lines.append(f"- {r[0]}({r[1]}) {r[2]}, GPA {r[3]}({r[4]})")
    return "\n".join(lines)


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
        "max_tokens": 2048,
        "stream": stream,
    }

    if stream:
        return _stream_response(url, headers, payload)

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _stream_response(url: str, headers: dict, payload: dict):
    from fastapi.responses import StreamingResponse

    async def generate():
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
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