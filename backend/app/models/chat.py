from pydantic import BaseModel, Field
from typing import Any, Optional


class ChatMessageInput(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessageInput] = Field(..., min_length=1)
    stream: bool = False


class ChatResponse(BaseModel):
    reply: str
    messages: list[dict]
    # 选校场景下，profile 完成且推荐引擎成功时下发结构化推荐结果
    # （含 pathway_suggestions），供前端渲染 PathwaySection 等结构化卡片。
    # 非选校场景或推荐未触发时为 None，向后兼容旧 reply-only 调用。
    recommend_payload: Optional[dict[str, Any]] = None


class SaveHistoryRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    scene: str = ""
    user_message: str = Field(..., min_length=1)
    assistant_message: str = Field(..., min_length=1)


class HistorySession(BaseModel):
    session_id: str
    scene: str
    last_time: str
    message_count: int
    messages: list[dict]


class HistoryResponse(BaseModel):
    sessions: list[HistorySession]
    total: int