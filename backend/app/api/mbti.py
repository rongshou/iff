from fastapi import APIRouter, Query, HTTPException

from ..core.database import fetch_all, fetch_one

router = APIRouter(prefix="/api/mbti", tags=["mbti"])


@router.get("/types")
def list_mbti_types():
    rows = fetch_all("SELECT mbti_type, mbti_name, learning_style FROM mbti_major_map ORDER BY mbti_type")
    result = []
    for r in rows:
        result.append({
            "type": r["mbti_type"],
            "name": r["mbti_name"],
            "learning_style": r["learning_style"] or "",
        })
    return {"types": result}


@router.get("/majors")
def get_mbti_majors(mbti: str = Query(..., description="MBTI 类型, 如 INTJ")):
    row = fetch_one(
        "SELECT * FROM mbti_major_map WHERE mbti_type = ?", (mbti.upper(),)
    )
    if not row:
        raise HTTPException(404, f"未找到 MBTI 类型: {mbti}")

    return {
        "type": row["mbti_type"],
        "name": row["mbti_name"],
        "top_majors": [m.strip() for m in (row["top_majors"] or "").split(",") if m.strip()],
        "avoid_majors": [m.strip() for m in (row["avoid_majors"] or "").split(",") if m.strip()],
        "learning_style": row["learning_style"] or "",
        "career_path": row["career_path"] or "",
        "study_tips": row["study_tips"] or "",
    }
