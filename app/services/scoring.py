"""Deterministic candidate and match scoring (no LLM)."""

from typing import Any


PAPER_TIER_MAP = {"A*": 25, "A": 20, "B": 14, "C": 8, "unranked": 4, "none": 0, "na": 0}


def _institution_weight(tier: str | None) -> float:
    weights = {"top_50": 1.2, "51_200": 1.1, "201_500": 1.0, "500_plus": 0.9, "not_ranked": 0.85}
    return weights.get(tier or "", 1.0)


def generate_candidate_score(profile: dict) -> dict:
    """Compute profile strength across dimensions (0–100 each, overall weighted)."""
    cgpa = float(profile.get("cgpa") or 0)
    tier = profile.get("institution_tier") or "not_ranked"
    academic = min(100, cgpa * 10 * _institution_weight(tier)) if cgpa else 0

    exams = profile.get("exams") or {}
    if isinstance(profile.get("exams_json"), str):
        import json
        try:
            exams = json.loads(profile["exams_json"])
        except json.JSONDecodeError:
            exams = {}

    ielts = float(exams.get("ielts_overall") or exams.get("ielts_expected") or 0)
    toefl = int(exams.get("toefl_total") or 0)
    if ielts >= 7.5:
        language = 95
    elif ielts >= 7.0:
        language = 85
    elif ielts >= 6.5:
        language = 75
    elif ielts >= 6.0:
        language = 60
    elif toefl >= 100:
        language = 85
    elif toefl >= 90:
        language = 70
    elif ielts > 0 or toefl > 0:
        language = 50
    else:
        language = 0

    research_data = profile.get("research") or {}
    tier_key = (research_data.get("conference_tier") or "none").replace("*", "*")
    if tier_key not in PAPER_TIER_MAP:
        tier_key = "none" if not research_data.get("has_papers") else "unranked"
    research = PAPER_TIER_MAP.get(tier_key, 0) * 3.2  # scale to ~100
    if research_data.get("research_lab_months", 0) >= 12:
        research = min(100, research + 15)
    research = min(100, research)

    work_data = profile.get("work") or {}
    jobs = work_data.get("jobs") or []
    internships = work_data.get("internships") or []
    months = sum(j.get("months", 0) for j in jobs + internships)
    professional = min(100, months * 2.5) if months else 0

    extras = profile.get("extracurriculars") or {}
    leadership = 20 if extras.get("leadership_roles") else 0
    awards = 15 if extras.get("awards") else 0
    projects = 15 if extras.get("open_source_or_projects") else 0
    extracurricular = min(100, leadership + awards + projects + 30 if extras else 0)

    overall = round(
        academic * 0.30 + language * 0.15 + research * 0.25 + professional * 0.20 + extracurricular * 0.10,
        1,
    )
    return {
        "academic": round(academic, 1),
        "research": round(research, 1),
        "professional": round(professional, 1),
        "language": round(language, 1),
        "extracurricular": round(extracurricular, 1),
        "overall": overall,
    }


def match_score(candidate: dict, program: dict) -> dict:
    """Score candidate vs program requirements. Returns total, tier, breakdown."""
    scores: dict[str, int] = {}

    cand_gpa = float(candidate.get("cgpa") or 0)
    median_gpa = float(program.get("median_gpa") or program.get("min_gpa") or 3.0)
    min_gpa = float(program.get("min_gpa") or median_gpa - 0.3)
    if cand_gpa >= median_gpa:
        scores["gpa"] = 25
    elif cand_gpa >= min_gpa:
        scores["gpa"] = 15
    else:
        scores["gpa"] = 0

    exams = candidate.get("exams") or {}
    ielts = float(exams.get("ielts_overall") or exams.get("ielts_expected") or 0)
    ielts_min = float(program.get("ielts_min") or 6.5)
    if ielts >= ielts_min + 0.5:
        scores["language"] = 20
    elif ielts >= ielts_min:
        scores["language"] = 12
    else:
        scores["language"] = 0 if ielts > 0 else 8

    research_data = candidate.get("research") or {}
    tier = research_data.get("conference_tier") or "none"
    scores["research"] = PAPER_TIER_MAP.get(tier, 0)

    budget = float(candidate.get("budget_usd") or candidate.get("budget") or 0)
    tuition = float(program.get("annual_tuition") or program.get("tuition_usd") or 0)
    if tuition and budget >= tuition:
        scores["budget"] = 15
    elif program.get("has_funding"):
        scores["budget"] = 12
    elif tuition == 0:
        scores["budget"] = 10
    else:
        scores["budget"] = 0

    prefs = candidate.get("preferred_countries") or []
    if isinstance(candidate.get("preferred_countries_json"), str):
        import json
        try:
            prefs = json.loads(candidate["preferred_countries_json"])
        except json.JSONDecodeError:
            prefs = []
    pref_score = 0
    if program.get("country") in prefs:
        pref_score += 5
    if program.get("post_study_visa_available"):
        pref_score += 5
    if program.get("campus_type") == candidate.get("campus_type"):
        pref_score += 5
    scores["preferences"] = pref_score

    total = sum(scores.values())
    tier_label = "reach" if total < 55 else ("target" if total < 78 else "safety")
    return {"total": total, "tier": tier_label, "breakdown": scores}
