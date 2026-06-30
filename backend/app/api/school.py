from fastapi import APIRouter

from ..services.school_abbrev import UNIVERSITY_ABBREVIATIONS

router = APIRouter(prefix="/api/school", tags=["school"])


@router.get("/abbreviations")
async def get_abbreviations():
    """返回全称 → 简称列表的映射，供前端动态加载。"""
    return {
        "abbreviations": UNIVERSITY_ABBREVIATIONS,
        "total": len(UNIVERSITY_ABBREVIATIONS),
    }
