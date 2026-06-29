"""All Supabase queries for the `profiles` table."""
from __future__ import annotations

import json
from typing import Any

from app.database.db import get_client

PROFILE_COLUMNS = (
    "plan_id", "degree", "major", "cgpa", "budget", "budget_range",
    "target_intake", "priority", "region", "resume_url",
    "university_name", "institution_tier", "target_degree", "target_field", "gpa_scale",
    "exams_json", "research_json", "work_json", "extracurriculars_json",
    "budget_usd", "living_budget_usd", "scholarship_seeking", "funding_open",
    "preferred_countries_json", "campus_type", "campus_size", "visa_constraints",
    "post_study_goal", "candidate_score_json", "profile_completeness", "intake_semester",
    "resume_outline_json", "transcript_outline_json", "form_stage_complete",
)

JSON_FIELDS = frozenset({
    "exams_json", "research_json", "work_json", "extracurriculars_json",
    "preferred_countries_json", "candidate_score_json",
    "resume_outline_json", "transcript_outline_json",
})

BOOL_FIELDS = frozenset({"scholarship_seeking", "funding_open"})


def _parse_row(row: dict) -> dict:
    out = dict(row)
    for key in JSON_FIELDS:
        if out.get(key):
            try:
                out[key.replace("_json", "")] = json.loads(out[key])
            except (json.JSONDecodeError, TypeError):
                out[key.replace("_json", "")] = None
    for key in BOOL_FIELDS:
        if key in out and out[key] is not None:
            out[key] = bool(out[key])
    return out


def get_profile(plan_id: int) -> dict | None:
    sb = get_client()
    resp = sb.table("profiles").select(
        ", ".join(PROFILE_COLUMNS)
    ).eq("plan_id", plan_id).execute()
    return _parse_row(resp.data[0]) if resp.data else None


def profile_exists(plan_id: int) -> bool:
    sb = get_client()
    resp = sb.table("profiles").select("plan_id").eq("plan_id", plan_id).execute()
    return bool(resp.data)


def upsert_profile(plan_id: int, fields: dict[str, Any]) -> dict:
    """Insert or update profile with only the provided fields."""
    sb = get_client()
    data: dict[str, Any] = {"plan_id": plan_id}

    for key, value in fields.items():
        if value is None:
            continue
        if key in JSON_FIELDS or key.endswith("_json"):
            col = key if key.endswith("_json") else f"{key}_json"
            data[col] = json.dumps(value) if isinstance(value, (dict, list)) else value
        elif key in BOOL_FIELDS:
            data[key] = 1 if value else 0
        elif key in PROFILE_COLUMNS:
            data[key] = value

    resp = sb.table("profiles").upsert(data).execute()
    return _parse_row(resp.data[0]) if resp.data else get_profile(plan_id) or {"plan_id": plan_id}


def set_profile_completeness(plan_id: int, pct: float) -> None:
    sb = get_client()
    sb.table("profiles").update({"profile_completeness": pct}).eq("plan_id", plan_id).execute()
