from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..models.chat import ChatRequest
from ..services.chat import chat

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat_endpoint(request: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    if request.stream:
        result = await chat(messages, stream=True)
        if isinstance(result, StreamingResponse):
            return result

    try:
        result = await chat(messages, stream=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result