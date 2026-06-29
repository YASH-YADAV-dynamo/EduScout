"""All Supabase queries for the `study_plans` table."""
from __future__ import annotations

from app.database.db import get_client


def insert_plan(user_id: int, title: str) -> dict:
    sb = get_client()
    resp = sb.table("study_plans").insert({
        "user_id": user_id,
        "title": title,
        "status": "active",
    }).execute()
    return resp.data[0]


def get_plan_by_id(plan_id: int) -> dict | None:
    sb = get_client()
    resp = sb.table("study_plans").select(
        "id, user_id, title, status"
    ).eq("id", plan_id).execute()
    return resp.data[0] if resp.data else None


def list_plans_by_user(user_id: int) -> list[dict]:
    sb = get_client()
    resp = sb.table("study_plans").select(
        "id, user_id, title, status"
    ).eq("user_id", user_id).order("id", desc=True).execute()
    return resp.data or []


def update_plan_status(plan_id: int, status: str) -> None:
    sb = get_client()
    sb.table("study_plans").update({"status": status}).eq("id", plan_id).execute()
