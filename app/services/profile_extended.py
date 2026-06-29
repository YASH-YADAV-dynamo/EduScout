from typing import Any

from app.query import profiles as q

# Re-export constants used by profile.py
PROFILE_COLUMNS = q.PROFILE_COLUMNS
JSON_FIELDS = q.JSON_FIELDS
BOOL_FIELDS = q.BOOL_FIELDS


def get_full_profile(plan_id: int) -> dict | None:
    return q.get_profile(plan_id)


def patch_profile(plan_id: int, **fields: Any) -> dict:
    """Merge partial profile updates; inserts if row doesn't exist yet."""
    return q.upsert_profile(plan_id, fields)


def set_profile_completeness(plan_id: int, pct: float) -> None:
    q.set_profile_completeness(plan_id, pct)
