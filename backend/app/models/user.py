from pydantic import BaseModel, Field, model_validator
from typing import Optional

from ..utils.gpa import GPA_RANGES, GPA_FORMAT_ALIASES
from ..utils.countries import VALID_COUNTRIES, STUDY_LEVELS


class RecommendRequest(BaseModel):
    target_countries: list[str] = Field(..., min_length=1, examples=[["英国"]])
    gpa_score: float = Field(..., examples=[3.5])
    gpa_format: str = Field(..., examples=["4分制"])
    study_level: str = Field(..., examples=["硕士"])
    target_major: Optional[str] = Field(None, examples=["计算机"])
    original_major: Optional[str] = Field(None, examples=["软件工程"])
    undergraduate_school: Optional[str] = Field(None, examples=["清华大学"])
    gre_score: Optional[int] = Field(None, examples=[320])
    toefl_score: Optional[int] = Field(None, examples=[100])
    ielts_score: Optional[float] = Field(None, examples=[7.5])

    @model_validator(mode="after")
    def validate_fields(self):
        fmt = GPA_FORMAT_ALIASES.get(self.gpa_format.strip(), self.gpa_format)
        gpa_range = GPA_RANGES.get(fmt)
        if gpa_range is None:
            raise ValueError(f"不支持的 GPA 格式: {self.gpa_format}")
        lo, hi = gpa_range
        if self.gpa_score < lo or self.gpa_score > hi:
            raise ValueError(f"GPA {self.gpa_score} 超出 {fmt} 范围 [{lo}, {hi}]")
        invalid = [c for c in self.target_countries if c not in VALID_COUNTRIES]
        if invalid:
            raise ValueError(f"不支持的国家/地区: {invalid}")
        if self.study_level not in STUDY_LEVELS:
            raise ValueError(f"不支持的学位阶段: {self.study_level}")
        return self
