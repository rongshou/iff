from pydantic import BaseModel, Field
from typing import Any, Optional


class FavoriteRequest(BaseModel):
    """收藏院校的请求体。school_name 为必填，其余字段均为可选元数据。"""
    school_name: str = Field(..., min_length=1)
    country: Optional[str] = None
    qs_rank: Optional[int] = None
    usnews_rank: Optional[int] = None
    match_level: Optional[str] = None
    gpa_median: Optional[float] = None
    matched_cases: Optional[int] = None
    toefl_req: Optional[str] = None
    meets_toefl: Optional[int] = None


class FavoriteResponse(BaseModel):
    """收藏院校的响应模型。"""
    id: int
    auth_code: str
    school_name: str
    country: Optional[str] = None
    qs_rank: Optional[int] = None
    usnews_rank: Optional[int] = None
    match_level: Optional[str] = None
    gpa_median: Optional[float] = None
    matched_cases: Optional[int] = None
    toefl_req: Optional[str] = None
    meets_toefl: Optional[int] = None
    created_at: str
