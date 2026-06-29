"""All Supabase queries for the `college_subscriptions` table."""
from __future__ import annotations

from app.database.db import get_client


def count_subscriptions(user_id: int) -> int:
    sb = get_client()
    resp = sb.table("college_subscriptions").select(
        "id", count="exact"
    ).eq("user_id", user_id).execute()
    return resp.count or 0


def insert_subscription(user_id: int, university_id: int) -> bool:
    """Insert subscription. Returns False if it already exists."""
    sb = get_client()
    try:
        sb.table("college_subscriptions").insert({
            "user_id": user_id,
            "university_id": university_id,
        }).execute()
        return True
    except Exception:
        return False


def delete_subscription(user_id: int, university_id: int) -> bool:
    sb = get_client()
    resp = sb.table("college_subscriptions").delete().eq(
        "user_id", user_id
    ).eq("university_id", university_id).execute()
    return bool(resp.data)


def list_subscriptions_for_user(user_id: int) -> list[dict]:
    """Return subscriptions with joined university fields."""
    sb = get_client()
    resp = sb.table("college_subscriptions").select(
        "id, university_id, subscribed_at, "
        "universities(university_name, program_name, category, deadline, match_score)"
    ).eq("user_id", user_id).order("subscribed_at", desc=True).execute()

    results = []
    for row in (resp.data or []):
        uni = row.pop("universities", {}) or {}
        row.update(uni)
        results.append(row)
    return results


def get_subscriptions_with_deadlines() -> list[dict]:
    """All subscriptions where the university has a non-empty deadline — for notifications."""
    sb = get_client()
    # Fetch all subs, then filter for non-null/non-empty deadline in Python
    resp = sb.table("college_subscriptions").select(
        "user_id, universities(university_name, program_name, deadline, match_score)"
    ).not_.is_("universities.deadline", "null").execute()

    results = []
    for row in (resp.data or []):
        uni = row.pop("universities", {}) or {}
        if not uni.get("deadline"):
            continue
        row.update(uni)
        results.append(row)
    return results
