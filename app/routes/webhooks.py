"""
Supabase Database Webhooks receiver.

Supabase can call this endpoint on INSERT/UPDATE/DELETE events for any table.
Set up in: Supabase Dashboard → Database → Webhooks → Create new webhook.

Recommended webhooks to configure:
  - Table: tasks,        Events: INSERT UPDATE,  URL: {BASE_URL}/webhooks/supabase
  - Table: universities, Events: INSERT UPDATE,  URL: {BASE_URL}/webhooks/supabase
  - Table: college_subscriptions, Events: INSERT, URL: {BASE_URL}/webhooks/supabase

Each webhook POST body has the shape:
  {
    "type":   "INSERT" | "UPDATE" | "DELETE",
    "table":  "tasks",
    "record": { ...new row... },
    "old_record": { ...old row... } | null,
    "schema": "public"
  }
"""
import hashlib
import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_signature(body: bytes, signature_header: str | None) -> bool:
    """
    Verify the HMAC-SHA256 signature Supabase sends when a webhook secret is set.
    Set SUPABASE_WEBHOOK_SECRET in .env and in the Supabase webhook config.
    Returns True if no secret is configured (dev mode) or signature matches.
    """
    secret = settings.supabase_webhook_secret
    if not secret:
        return True  # dev / unprotected
    if not signature_header:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header.removeprefix("sha256="))


@router.post("/supabase")
async def supabase_webhook(
    request: Request,
    x_supabase_signature: str | None = Header(default=None),
):
    body = await request.body()
    if not _verify_signature(body, x_supabase_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("type", "").upper()
    table = payload.get("table", "")
    record = payload.get("record") or {}
    old_record = payload.get("old_record") or {}

    logger.info("Supabase webhook: %s on %s — id=%s", event_type, table, record.get("id"))

    # Dispatch to handlers
    if table == "tasks":
        await _handle_task_event(event_type, record, old_record)
    elif table == "universities":
        await _handle_university_event(event_type, record, old_record)
    elif table == "college_subscriptions":
        await _handle_subscription_event(event_type, record, old_record)

    return {"ok": True}


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def _handle_task_event(event_type: str, record: dict, old_record: dict) -> None:
    """Notify user when a task transitions to 'overdue' or is created with a near deadline."""
    from app.services.notifications import notify_user

    if event_type not in ("INSERT", "UPDATE"):
        return

    status = record.get("status")
    due_date = record.get("due_date")
    plan_id = record.get("plan_id")
    title = record.get("title", "")

    if not plan_id:
        return

    from app.services.user import get_user_by_plan

    user = get_user_by_plan(plan_id)
    if not user:
        return

    # Notify on status change to overdue
    old_status = old_record.get("status")
    if event_type == "UPDATE" and status == "overdue" and old_status != "overdue":
        await notify_user(user["id"], f"⚠️ Task is now overdue: {title} (was due {due_date})")

    # Notify on new task with a due date
    if event_type == "INSERT" and due_date:
        await notify_user(user["id"], f"📋 New task added: {title} — due {due_date}")


async def _handle_university_event(event_type: str, record: dict, old_record: dict) -> None:
    """Notify user when a university's deadline is set or updated."""
    from app.services.user import get_user_by_plan
    from app.services.notifications import notify_user

    plan_id = record.get("plan_id")
    if not plan_id:
        return

    deadline = record.get("deadline")
    old_deadline = old_record.get("deadline")
    uni_name = record.get("university_name", "a university")

    if not deadline:
        return

    # Only notify if deadline was newly set or changed
    if event_type == "INSERT" or (event_type == "UPDATE" and deadline != old_deadline):
        user = get_user_by_plan(plan_id)
        if user:
            await notify_user(
                user["id"],
                f"🏫 {uni_name} — application deadline set: {deadline}",
            )


async def _handle_subscription_event(event_type: str, record: dict, old_record: dict) -> None:
    """Confirm to user when they subscribe to a new university."""
    from app.services.notifications import notify_user
    from app.services.university import get_university

    if event_type != "INSERT":
        return

    user_id = record.get("user_id")
    university_id = record.get("university_id")
    if not user_id or not university_id:
        return

    uni = get_university(university_id)
    if not uni:
        return

    name = uni.get("university_name", "a university")
    deadline = uni.get("deadline")
    msg = f"✅ Subscribed to {name}"
    if deadline:
        msg += f" — deadline: {deadline}"

    await notify_user(user_id, msg)
