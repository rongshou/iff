from ..core.database import get_db
from ..utils.gpa import normalize_gpa
from ..utils.tier import classify_school_tier
from .case_matcher import match_schools_by_background
from .pathway_service import find_pathway_suggestions


def run(profile: dict) -> dict:
    countries = profile["target_countries"]
    gpa_score = profile["gpa_score"]
    gpa_format = profile["gpa_format"]
    study_level = profile["study_level"]
    target_major = profile.get("target_major")
    original_major = profile.get("original_major")
    undergrad_school = profile.get("undergraduate_school")

    gpa_percent, gpa4 = normalize_gpa(gpa_score, gpa_format, undergrad_school)
    tier, tier_label = classify_school_tier(undergrad_school)

    background = {
        "gpa_percent": gpa_percent,
        "gpa4": gpa4,
        "school_tier": tier,
        "school_tier_label": tier_label,
    }

    with get_db() as conn:
        match_result = match_schools_by_background(
            conn=conn,
            countries=countries,
            gpa_score=gpa_score,
            gpa_format=gpa_format,
            study_level=study_level,
            target_major=target_major,
            original_major=original_major,
            undergrad_school=undergrad_school,
        )

        pathway = find_pathway_suggestions(
            conn=conn,
            study_level=study_level,
            target_countries=countries,
            gpa_percent=gpa_percent,
            school_tier=tier,
            original_major=profile.get("original_major"),
            target_major=profile.get("target_major"),
        )

    total_cases = sum(c["matched_cases"] for c in match_result["by_country"])
    total_schools = sum(c["matched_schools"] for c in match_result["by_country"])

    return {
        "background": background,
        "match_summary": {
            "total_cases": total_cases,
            "total_schools": total_schools,
        },
        "by_country": match_result["by_country"],
        "pathway_suggestions": pathway,
        "generated_at": "",
    }
