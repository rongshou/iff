from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException

from ..models.user import RecommendRequest
from ..models.recommend import RecommendResult
from ..services.recommend import run

router = APIRouter(prefix="/api", tags=["recommend"])


@router.post("/recommend", response_model=RecommendResult)
def recommend(request: RecommendRequest):
    try:
        result = run(request.model_dump())
        tz = timezone(timedelta(hours=8))
        result["generated_at"] = datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S+08:00")
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "name": "天权留学选校推荐引擎",
    }
