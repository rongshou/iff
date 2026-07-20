import logging

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..models.chat import ChatRequest, ChatResponse, SaveHistoryRequest
from ..services.chat import chat
from ..repositories.chat_repository import save_turn, get_history, delete_history, ensure_table

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
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


# ── 对话历史持久化 ──


@router.post("/history")
def save_chat_history(
    request: SaveHistoryRequest,
    x_auth_code: str = Header(default="", alias="X-Auth-Code"),
):
    """保存一轮对话（用户消息+助手回复）到数据库。"""
    if not x_auth_code:
        raise HTTPException(status_code=401, detail="缺少 X-Auth-Code 请求头")
    try:
        save_turn(
            auth_code=x_auth_code,
            session_id=request.session_id,
            user_message=request.user_message,
            assistant_message=request.assistant_message,
            scene=request.scene,
        )
        return {"ok": True}
    except Exception as e:
        logger.error("save chat history error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="保存对话历史失败")


@router.get("/history")
def get_chat_history(
    x_auth_code: str = Header(default="", alias="X-Auth-Code"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """获取用户的历史对话记录。"""
    if not x_auth_code:
        raise HTTPException(status_code=401, detail="缺少 X-Auth-Code 请求头")
    try:
        sessions = get_history(x_auth_code, limit=limit, offset=offset)
        return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        logger.error("get chat history error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="获取对话历史失败")


@router.delete("/history")
def delete_chat_history(
    x_auth_code: str = Header(default="", alias="X-Auth-Code"),
    session_id: str = Query(default=""),
):
    """删除用户的对话历史。session_id 为空则清空全部。"""
    if not x_auth_code:
        raise HTTPException(status_code=401, detail="缺少 X-Auth-Code 请求头")
    try:
        deleted = delete_history(x_auth_code, session_id=session_id or None)
        return {"ok": True, "deleted": deleted}
    except Exception as e:
        logger.error("delete chat history error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="删除对话历史失败")
