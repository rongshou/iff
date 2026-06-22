from pydantic import BaseModel, Field
from typing import Optional


class ChatMessageInput(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessageInput] = Field(..., min_length=1)
    stream: bool = False


class ChatResponse(BaseModel):
    reply: str
    messages: list[dict]