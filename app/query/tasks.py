"""All Supabase queries for the `tasks` table."""
from __future__ import annotations

from datetime import date, timedelta

from app.database.db import get_client


def insert_task(plan_id: int, title: str, due_date: str | None) -> dict:
    sb = get_client()
    data = {"plan_id": plan_id, "title": title, "status": "pending"}
    if due_date:
        data["due_date"] = due_date
    resp = sb.table("tasks").insert(data).execute()
    return resp.data[0]


def get_task_by_id(task_id: int) -> dict | None:
    sb = get_client()
    resp = sb.table("tasks").select(
        "id, plan_id, title, due_date, status"
    ).eq("id", task_id).execute()
    return resp.data[0] if resp.data else None


def list_tasks_by_plan(plan_id: int) -> list[dict]:
    """Return tasks ordered: non-null due_date first (asc), then null, then by id."""
    sb = get_client()
    # Fetch all tasks for the plan and sort in Python (PostgREST nullslast support varies)
    resp = sb.table("tasks").select(
        "id, plan_id, title, due_date, status"
    ).eq("plan_id", plan_id).execute()
    rows = resp.data or []
    return sorted(rows, key=lambda r: (r["due_date"] is None, r["due_date"] or "", r["id"]))


def update_task_status(task_id: int, status: str) -> None:
    sb = get_client()
    sb.table("tasks").update({"status": status}).eq("id", task_id).execute()


def get_upcoming_tasks(within_days: int = 7) -> list[dict]:
    """Pending tasks with due_date in the next N days, with plan title via join."""
    today = date.today()
    end = (today + timedelta(days=within_days)).isoformat()
    today_str = today.isoformat()

    sb = get_client()
    resp = sb.table("tasks").select(
        "id, plan_id, title, due_date, status, study_plans(user_id, title)"
    ).eq("status", "pending").gte("due_date", today_str).lte("due_date", end).not_.is_(
        "due_date", "null"
    ).order("due_date").execute()

    results = []
    for row in (resp.data or []):
        plan = row.pop("study_plans", {}) or {}
        row["user_id"] = plan.get("user_id")
        row["plan_title"] = plan.get("title")
        results.append(row)
    return results


def get_overdue_tasks() -> list[dict]:
    """Pending tasks whose due_date is before today, with plan title via join."""
    today_str = date.today().isoformat()

    sb = get_client()
    resp = sb.table("tasks").select(
        "id, plan_id, title, due_date, status, study_plans(user_id, title)"
    ).eq("status", "pending").lt("due_date", today_str).not_.is_(
        "due_date", "null"
    ).order("due_date").execute()

    results = []
    for row in (resp.data or []):
        plan = row.pop("study_plans", {}) or {}
        row["user_id"] = plan.get("user_id")
        row["plan_title"] = plan.get("title")
        results.append(row)
    return results
