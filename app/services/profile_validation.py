"""Section 7 validation gates before university search."""

import json

from app.services.profile_extended import get_full_profile

REQUIRED_FOR_SEARCH = [
    ("target_degree", "Ask target degree (MS / PhD / MBA / MEng / other)"),
    ("target_field", "Ask target field/specialization"),
    ("cgpa", "Ask GPA/CGPA (must be > 0)"),
    ("language_test", "Ask IELTS/TOEFL actual or expected score"),
    ("budget_usd", "Ask annual tuition budget in USD"),
    ("preferred_countries", "Ask target countries (list)"),
    ("target_intake", "Ask target intake term"),
]

COMPLETENESS_FIELDS = [
    "degree", "major", "cgpa", "target_degree", "target_field",
    "target_intake", "budget_usd", "preferred_countries", "exams",
]


def _has_language_test(profile: dict) -> bool:
    exams = profile.get("exams") or {}
    ielts = float(exams.get("ielts_overall") or exams.get("ielts_expected") or 0)
    toefl = int(exams.get("toefl_total") or 0)
    return ielts > 0 or toefl > 0


def _parse_countries(value) -> list | None:
    if not value:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        stripped = value.strip()
        return [stripped] if stripped else None
    return None


def _get_field(profile: dict, field: str):
    if field == "language_test":
        return _has_language_test(profile)
    if field == "preferred_countries":
        prefs = _parse_countries(profile.get("preferred_countries"))
        if prefs:
            return prefs
        region = profile.get("region")
        return [region] if region else None
    if field == "target_degree":
        return profile.get("target_degree") or profile.get("degree")
    if field == "target_field":
        return profile.get("target_field") or profile.get("major")
    if field == "budget_usd":
        return profile.get("budget_usd") or profile.get("budget")
    return profile.get(field)


def check_profile_ready(plan_id: int) -> dict:
    profile = get_full_profile(plan_id) or {}
    missing = []
    for field, message in REQUIRED_FOR_SEARCH:
        value = _get_field(profile, field)
        if field == "cgpa":
            if not value or float(value) <= 0:
                missing.append({"field": field, "message": message})
        elif field == "budget_usd":
            if not value or float(value) <= 0:
                missing.append({"field": field, "message": message})
        elif field == "language_test":
            if not value:
                missing.append({"field": field, "message": message})
        elif field == "preferred_countries":
            if not value or (isinstance(value, list) and len(value) == 0):
                missing.append({"field": field, "message": message})
        elif not value:
            missing.append({"field": field, "message": message})

    filled = 0
    for f in COMPLETENESS_FIELDS:
        if f == "exams":
            if _has_language_test(profile):
                filled += 1
        elif f == "preferred_countries":
            if _get_field(profile, "preferred_countries"):
                filled += 1
        elif profile.get(f) or (f == "target_degree" and profile.get("degree")):
            filled += 1
    completeness = round(filled / len(COMPLETENESS_FIELDS) * 100, 1)

    return {
        "ready": len(missing) == 0,
        "missing_fields": missing,
        "profile_completeness": completeness,
        "plan_id": plan_id,
    }
