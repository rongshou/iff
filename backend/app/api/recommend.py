import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException

from ..models.user import RecommendRequest
from ..models.recommend import RecommendResult
from ..services.recommend import run

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["recommend"])


@router.post("/recommend", response_model=RecommendResult)
def recommend(request: RecommendRequest):
    try:
        result = run(request.model_dump())
        tz = timezone(timedelta(hours=8))
        result["generated_at"] = datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S+08:00")
        return result
    except ValueError as e:
        logger.warning("recommend validation error: %s", str(e))
        raise HTTPException(status_code=422, detail="输入参数无效，请检查后再试")
    except Exception as e:
        logger.exception("recommend error")
        raise HTTPException(status_code=500, detail="推荐服务异常，请稍后重试")


@router.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "name": "天权留学选校推荐引擎",
    }
