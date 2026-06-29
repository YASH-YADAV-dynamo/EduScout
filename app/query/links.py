"""All Supabase queries for `link_codes` and `linked_channels` tables."""
from __future__ import annotations

from app.database.db import get_client


# ---------------------------------------------------------------------------
# link_codes
# ---------------------------------------------------------------------------

def insert_link_code(user_id: int, code: str, expires_at: str) -> dict:
    sb = get_client()
    resp = sb.table("link_codes").insert({
        "user_id": user_id,
        "code": code,
        "expires_at": expires_at,
        "used": 0,
    }).execute()
    return resp.data[0]


def get_valid_link_code(code: str, now_iso: str) -> dict | None:
    """Return an unused, non-expired link_code row."""
    sb = get_client()
    resp = sb.table("link_codes").select(
        "id, user_id, code, expires_at, used"
    ).eq("code", code).eq("used", 0).gt("expires_at", now_iso).execute()
    return resp.data[0] if resp.data else None


def mark_link_code_used(link_code_id: int) -> None:
    sb = get_client()
    sb.table("link_codes").update({"used": 1}).eq("id", link_code_id).execute()


# ---------------------------------------------------------------------------
# linked_channels
# ---------------------------------------------------------------------------

def upsert_linked_channel(user_id: int, channel_type: str, external_id: str) -> None:
    sb = get_client()
    sb.table("linked_channels").upsert(
        {"user_id": user_id, "channel_type": channel_type, "external_id": external_id},
        on_conflict="channel_type,external_id",
    ).execute()


def get_channels_for_user(user_id: int) -> list[dict]:
    sb = get_client()
    resp = sb.table("linked_channels").select(
        "id, user_id, channel_type, external_id"
    ).eq("user_id", user_id).execute()
    return resp.data or []


def get_user_by_channel(channel_type: str, external_id: str) -> dict | None:
    """Look up the user linked to a given channel (e.g. Telegram chat_id)."""
    sb = get_client()
    resp = sb.table("linked_channels").select(
        "users(id, email, name, public_id, esid, overall_score)"
    ).eq("channel_type", channel_type).eq("external_id", str(external_id)).execute()
    if resp.data and resp.data[0].get("users"):
        return resp.data[0]["users"]
    return None
