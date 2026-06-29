"""
All Supabase queries for the `users` table.
Direct Supabase client — no SQL string parsing.
"""
from __future__ import annotations

import random
import secrets
import string

from app.database.db import get_client


# ---------------------------------------------------------------------------
# ID generation helpers
# ---------------------------------------------------------------------------

def _make_public_id() -> str:
    for _ in range(10):
        candidate = f"ESC-{secrets.token_hex(3).upper()}"
        sb = get_client()
        resp = sb.table("users").select("id").eq("public_id", candidate).execute()
        if not resp.data:
            return candidate
    return f"ESC-{secrets.token_hex(4).upper()}"


def _generate_esid() -> str:
    sb = get_client()
    letters = "".join(random.choices(string.ascii_uppercase, k=2))
    resp = sb.table("users").select("id", count="exact").like("esid", f"{letters}%").execute()
    count = resp.count or 0
    return f"{letters}{str(count + 1).zfill(4)}"


def _ensure_esid(user_id: int) -> str:
    sb = get_client()
    resp = sb.table("users").select("esid").eq("id", user_id).single().execute()
    if resp.data and resp.data.get("esid"):
        return resp.data["esid"]
    esid = _generate_esid()
    sb.table("users").update({"esid": esid}).eq("id", user_id).execute()
    return esid


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_user_by_email(email: str) -> dict | None:
    sb = get_client()
    resp = sb.table("users").select(
        "id, email, name, public_id, google_sub, esid, overall_score"
    ).eq("email", email).execute()
    return resp.data[0] if resp.data else None


def get_user_by_id(user_id: int) -> dict | None:
    sb = get_client()
    resp = sb.table("users").select(
        "id, email, name, public_id, google_sub, esid, overall_score"
    ).eq("id", user_id).execute()
    return resp.data[0] if resp.data else None


def get_user_by_public_id(public_id: str) -> dict | None:
    sb = get_client()
    resp = sb.table("users").select(
        "id, email, name, public_id, google_sub, esid, overall_score"
    ).eq("public_id", public_id.strip().upper()).execute()
    return resp.data[0] if resp.data else None


def get_user_by_esid(esid: str) -> dict | None:
    sb = get_client()
    resp = sb.table("users").select(
        "id, email, name, public_id, google_sub, esid, overall_score"
    ).eq("esid", esid.strip().upper()).execute()
    return resp.data[0] if resp.data else None


def get_user_by_google_sub(google_sub: str) -> dict | None:
    sb = get_client()
    resp = sb.table("users").select(
        "id, email, name, public_id, google_sub, esid, overall_score"
    ).eq("google_sub", google_sub).execute()
    return resp.data[0] if resp.data else None


def get_user_by_plan_id(plan_id: int) -> dict | None:
    """Fetch user via the study_plans FK join."""
    sb = get_client()
    resp = sb.table("study_plans").select(
        "users(id, email, name, public_id, google_sub, esid, overall_score)"
    ).eq("id", plan_id).execute()
    if resp.data and resp.data[0].get("users"):
        return resp.data[0]["users"]
    return None


def insert_user(email: str, name: str, public_id: str, esid: str, google_sub: str | None = None) -> dict:
    sb = get_client()
    data: dict = {"email": email, "name": name, "public_id": public_id, "esid": esid}
    if google_sub:
        data["google_sub"] = google_sub
    resp = sb.table("users").insert(data).execute()
    return resp.data[0]


def update_user_google_sub(user_id: int, google_sub: str, name: str) -> None:
    sb = get_client()
    sb.table("users").update({"google_sub": google_sub, "name": name}).eq("id", user_id).execute()


def update_user_esid(user_id: int, esid: str) -> None:
    sb = get_client()
    sb.table("users").update({"esid": esid}).eq("id", user_id).execute()


def update_user_public_id(user_id: int, public_id: str) -> None:
    sb = get_client()
    sb.table("users").update({"public_id": public_id}).eq("id", user_id).execute()


def update_overall_score(user_id: int, score: float) -> None:
    sb = get_client()
    sb.table("users").update({"overall_score": score}).eq("id", user_id).execute()


def count_users_with_esid_prefix(prefix: str) -> int:
    """Count users whose esid starts with prefix (for ESID generation)."""
    sb = get_client()
    resp = sb.table("users").select("id", count="exact").like("esid", f"{prefix}%").execute()
    return resp.count or 0
