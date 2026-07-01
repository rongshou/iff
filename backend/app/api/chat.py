import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..models.chat import ChatRequest
from ..services.chat import chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat_endpoint(request: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    if request.stream:
        result = await chat(messages, stream=True)
        if isinstance(result, StreamingResponse):
            return result
        # 回退到非流式结果
        return result

    try:
        result = await chat(messages, stream=False)
    except Exception as e:
        logger.error("chat error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="对话服务异常，请稍后重试")

    return result