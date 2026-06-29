"""All Supabase queries for the `calendar_events` table."""
from __future__ import annotations

from app.database.db import get_client


def insert_event(plan_id: int, event_id: str, title: str) -> dict:
    sb = get_client()
    resp = sb.table("calendar_events").insert({
        "plan_id": plan_id,
        "event_id": event_id,
        "title": title,
    }).execute()
    return resp.data[0]


def list_events_for_plan(plan_id: int) -> list[dict]:
    sb = get_client()
    resp = sb.table("calendar_events").select(
        "id, plan_id, event_id, title"
    ).eq("plan_id", plan_id).order("id").execute()
    return resp.data or []
