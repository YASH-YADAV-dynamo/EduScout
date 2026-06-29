"""All Supabase queries for the `onboarding_stages` table."""
from __future__ import annotations

from app.database.db import get_client


def upsert_stage(plan_id: int, stage: int, completed_at: str, data_snapshot_json: str) -> None:
    sb = get_client()
    sb.table("onboarding_stages").upsert({
        "plan_id": plan_id,
        "stage": stage,
        "completed_at": completed_at,
        "data_snapshot_json": data_snapshot_json,
    }, on_conflict="plan_id,stage").execute()


def list_stages_for_plan(plan_id: int) -> list[dict]:
    sb = get_client()
    resp = sb.table("onboarding_stages").select(
        "stage, completed_at"
    ).eq("plan_id", plan_id).order("stage").execute()
    return resp.data or []
