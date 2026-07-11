"""
文书知识库：从 advisor.db 读取文书知识，供 Chat 上下文注入。
"""

from typing import Any
from ..core.database import get_db


# ── 文书类型关键词检测 ─────────────────────────────────

ESSAY_KEYWORDS = [
    "文书", "essay", "PS", "个人陈述", "personal statement",
    "SOP", "statement of purpose", "推荐信", "recommendation",
    "简历", "CV", "resume", "common app", "主文书",
    "补充文书", "supplement", "writing supplement",
    "范文", "sample", "写作", "brainstorm", "头脑风暴",
    "大纲", "outline", "评分", "rubric", "评分标准",
    "why school", "why major", "diversity",
]


def is_essay_query(text: str) -> bool:
    """检测用户问题是否涉及文书相关"""
    text_lower = text.lower()
    for kw in ESSAY_KEYWORDS:
        if kw.lower() in text_lower:
            return True
    return False


# ── 数据库查询 ──────────────────────────────────────────

def get_essay_types() -> list[dict[str, Any]]:
    """获取文书类型列表"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT essay_type FROM essay_samples ORDER BY essay_type"
        ).fetchall()
        return [{"type": r[0]} for r in rows if r[0]]


def get_essay_prompts(limit: int = 10) -> list[dict[str, Any]]:
    """获取文书题目列表"""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT source, prompt_type, prompt_text_cn, word_limit, writing_tips
            FROM essay_prompts
            ORDER BY source, prompt_type
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_essay_samples_by_type(essay_type: str, limit: int = 5) -> list[dict[str, Any]]:
    """按类型获取范文"""
    safe = essay_type.replace("%", r"\%").replace("_", r"\_")
    with get_db() as conn:
        rows = conn.execute("""
            SELECT university, prompt, content, word_count, theme, language
            FROM essay_samples
            WHERE essay_type LIKE ? OR prompt LIKE ?
            ORDER BY id DESC
            LIMIT ?
        """, (f"%{safe}%", f"%{safe}%", limit)).fetchall()
        return [dict(r) for r in rows]


def get_essay_criteria() -> list[dict[str, Any]]:
    """获取文书评分标准"""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT criterion, weight, description, keywords
            FROM essay_criteria
            ORDER BY weight DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_brainstorm_questions(prompt_type: str = "") -> list[dict[str, Any]]:
    """获取头脑风暴问题"""
    with get_db() as conn:
        if prompt_type:
            rows = conn.execute("""
                SELECT prompt_type, question_order, question_cn, purpose
                FROM essay_brainstorm
                WHERE prompt_type LIKE ?
                ORDER BY question_order
            """, (f"%{prompt_type}%",)).fetchall()
        else:
            rows = conn.execute("""
                SELECT prompt_type, question_order, question_cn, purpose
                FROM essay_brainstorm
                ORDER BY prompt_type, question_order
                LIMIT 10
            """).fetchall()
        return [dict(r) for r in rows]


# ── 上下文构建 ──────────────────────────────────────────

def build_essay_context(user_query: str) -> str:
    """构建文书知识的上下文片段（供 Chat system prompt 注入）"""
    if not is_essay_query(user_query):
        return ""

    parts: list[str] = []

    # 检测具体文书类型
    query_lower = user_query.lower()
    detected_type = ""
    for t in ["主文书", "补充文书", "PS", "个人陈述", "推荐信", "简历", "why school", "why major", "diversity"]:
        if t.lower() in query_lower:
            detected_type = t
            break

    # 评分标准（通用知识）
    criteria = get_essay_criteria()
    if criteria:
        criteria_text = "\n".join(
            f"- {c['criterion']}（权重 {c['weight']}%）：{c['description']}"
            for c in criteria
        )
        parts.append(f"【文书评分标准】\n{criteria_text}")

    # 文书题目（当用户提到 Common App 或某类文书时）
    if "common app" in query_lower or "主文书" in query_lower:
        prompts = get_essay_prompts(limit=5)
        if prompts:
            prompts_text = "\n".join(
                f"- {p['source']} / {p['prompt_type']}：{p['prompt_text_cn'][:150]}"
                for p in prompts if p.get("prompt_text_cn")
            )
            parts.append(f"【文书题目参考】\n{prompts_text}")

    # 头脑风暴（当用户提到 brainstorm / 头脑风暴时）
    if "brainstorm" in query_lower or "头脑风暴" in query_lower or "怎么写" in query_lower:
        questions = get_brainstorm_questions(detected_type)
        if questions:
            q_text = "\n".join(
                f"- {q['question_cn']}（目的：{q.get('purpose', '探索写作方向')[:50]}）"
                for q in questions[:5]
            )
            parts.append(f"【头脑风暴问题参考】\n{q_text}")

    # 范文示例（当用户明确要范文或示例时）
    if "范文" in query_lower or "sample" in query_lower or "例子" in query_lower:
        samples = get_essay_samples_by_type(detected_type, limit=3)
        if samples:
            sample_text = "\n".join(
                f"- [{s['university']}] {s.get('prompt', '')[:80]}"
                for s in samples
            )
            parts.append(f"【范文示例】\n以下为相关范文供参考：\n{sample_text}")

    if not parts:
        # 通用文书知识
        types = get_essay_types()
        if types:
            type_list = "、".join(t["type"] for t in types[:10])
            parts.append(f"【文书类型】系统收录的文书类型包括：{type_list}。如需特定类型指导，请说明。")

    return "\n\n".join(parts)
