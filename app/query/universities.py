"""All Supabase queries for the `universities` table."""
from __future__ import annotations

import json
from typing import Any

from app.database.db import get_client

UNIVERSITY_SELECT = (
    "id, plan_id, university_name, category, program_name, degree_type, "
    "country, qs_rank, subject_rank, acceptance_rate, tuition_usd, deadline, "
    "funding_notes, match_score, match_breakdown_json, risk_note, research_metadata_json"
)

JSON_FIELDS = ("match_breakdown_json", "research_metadata_json")


def _parse_uni(row: dict) -> dict:
    out = dict(row)
    for key in JSON_FIELDS:
        if out.get(key):
            try:
                out[key.replace("_json", "")] = json.loads(out[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return out


def insert_university(plan_id: int, university_name: str, category: str, extra: dict[str, Any]) -> dict:
    sb = get_client()
    data: dict[str, Any] = {
        "plan_id": plan_id,
        "university_name": university_name,
        "category": category,
    }
    for key, val in extra.items():
        if val is None:
            continue
        if key in JSON_FIELDS and isinstance(val, (dict, list)):
            data[key] = json.dumps(val)
        else:
            data[key] = val

    resp = sb.table("universities").insert(data).execute()
    return _parse_uni(resp.data[0])


def get_university_by_id(university_id: int) -> dict | None:
    sb = get_client()
    resp = sb.table("universities").select(UNIVERSITY_SELECT).eq("id", university_id).execute()
    return _parse_uni(resp.data[0]) if resp.data else None


def list_universities_by_plan(plan_id: int) -> list[dict]:
    sb = get_client()
    resp = sb.table("universities").select(UNIVERSITY_SELECT).eq(
        "plan_id", plan_id
    ).order("category").order("university_name").execute()
    return [_parse_uni(r) for r in (resp.data or [])]


def delete_university(university_id: int) -> bool:
    sb = get_client()
    resp = sb.table("universities").delete().eq("id", university_id).execute()
    return bool(resp.data)
