import secrets
from datetime import datetime, timedelta, timezone

from app.query import links as q
from app.services.user import get_user_by_public_id


def generate_link_code(user_id: int, ttl_hours: int = 24) -> dict:
    code = secrets.token_hex(4).upper()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=ttl_hours)).isoformat()
    q.insert_link_code(user_id, code, expires_at)
    return {"user_id": user_id, "code": code, "expires_at": expires_at}


def redeem_link_code(code: str, channel_type: str, external_id: str) -> dict | None:
    normalized = code.strip().upper()

    # Public-ID shortcut (ESC-XXXXXX format)
    if normalized.startswith("ESC-"):
        user = get_user_by_public_id(normalized)
        if not user:
            return None
        q.upsert_linked_channel(user["id"], channel_type, external_id)
        return {
            "user_id": user["id"],
            "public_id": user["public_id"],
            "channel_type": channel_type,
            "external_id": external_id,
        }

    # Legacy SAA- prefix (backwards compat)
    if normalized.startswith("SAA-"):
        user = get_user_by_public_id(normalized)
        if not user:
            return None
        q.upsert_linked_channel(user["id"], channel_type, external_id)
        return {
            "user_id": user["id"],
            "public_id": user["public_id"],
            "channel_type": channel_type,
            "external_id": external_id,
        }

    # Time-limited OTP code
    now = datetime.now(timezone.utc).isoformat()
    row = q.get_valid_link_code(normalized, now)
    if not row:
        return None

    user_id = row["user_id"]
    q.mark_link_code_used(row["id"])
    q.upsert_linked_channel(user_id, channel_type, external_id)
    return {"user_id": user_id, "channel_type": channel_type, "external_id": external_id}


def get_channels_for_user(user_id: int) -> list[dict]:
    return q.get_channels_for_user(user_id)


def save_linked_channel(user_id: int, channel_type: str, external_id: str) -> None:
    q.upsert_linked_channel(user_id, channel_type, external_id)


def get_user_by_chat_id(chat_id: str, channel_type: str = "telegram") -> dict | None:
    return q.get_user_by_channel(channel_type, str(chat_id))
