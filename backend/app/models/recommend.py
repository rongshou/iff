from pydantic import BaseModel
from typing import Optional


class SchoolMatchItem(BaseModel):
    name: str
    qs_rank: Optional[int] = None
    usnews_rank: Optional[int] = None
    matched_cases: int = 0
    gpa_min: Optional[float] = None
    gpa_max: Optional[float] = None
    gpa_p50: Optional[float] = None
    majors: list[str] = []
    meets_requirement: bool = True
    requirement_value: Optional[float] = None
    admission_chance: str = ""
    admission_score: float = 0.0
    p50_reference: Optional[float] = None


class CountryMatchResult(BaseModel):
    country: str
    matched_cases: int = 0
    matched_schools: int = 0
    schools: list[SchoolMatchItem] = []


class MatchSummary(BaseModel):
    total_cases: int = 0
    total_schools: int = 0


class BackgroundInfo(BaseModel):
    gpa_percent: Optional[float] = None
    gpa4: Optional[float] = None
    school_tier: int = 0
    school_tier_label: str = ""
    gre_score: Optional[int] = None
    toefl_score: Optional[int] = None
    ielts_score: Optional[float] = None


class PathwayProgram(BaseModel):
    provider: str = ""
    program_type: str = ""
    direction: str = ""
    location: str = ""
    duration: str = ""
    intake: str = ""
    academic_req: str = ""
    ielts_req: str = ""
    tuition_note: str = ""


class PathwaySuggestion(BaseModel):
    university: str
    country: str
    qs_rank: Optional[int] = None
    usnews_rank: Optional[int] = None
    programs: list[PathwayProgram] = []
    reason: str = ""


class RecommendResult(BaseModel):
    background: BackgroundInfo
    match_summary: MatchSummary
    by_country: list[CountryMatchResult] = []
    pathway_suggestions: list[PathwaySuggestion] = []
    generated_at: str = ""
