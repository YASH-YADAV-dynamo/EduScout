import httpx

from app.config import settings
from app.query import college_subscriptions as cs_q
from app.services.link import get_channels_for_user
from app.services.task import get_overdue_tasks, get_upcoming_tasks
from app.services.user import get_user


async def send_whatsapp_message(phone: str, text: str) -> bool:
    if not settings.whatsapp_token or not settings.whatsapp_phone_id:
        return False
    url = f"https://graph.facebook.com/v21.0/{settings.whatsapp_phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": text},
    }
    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.is_success


async def send_telegram_message(chat_id: str, text: str) -> bool:
    if not settings.telegram_bot_token:
        return False
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json={"chat_id": chat_id, "text": text})
        return response.is_success


async def notify_user(user_id: int, message: str) -> None:
    channels = get_channels_for_user(user_id)
    for channel in channels:
        if channel["channel_type"] == "whatsapp":
            await send_whatsapp_message(channel["external_id"], message)
        elif channel["channel_type"] == "telegram":
            await send_telegram_message(channel["external_id"], message)


def _format_task_message(prefix: str, task: dict) -> str:
    due = task.get("due_date") or "no date"
    return f"{prefix}: {task['title']} (due {due}) — plan: {task['plan_title']}"


async def send_college_notification(user: dict, college: dict, event_type: str) -> None:
    msg = (
        f"🔔 Study Abroad Update\n\n"
        f"🏫 {college.get('university_name')} — {college.get('program_name') or ''}\n"
    )
    if event_type == "deadline_approaching":
        msg += f"⏰ Application deadline approaching: {college.get('deadline')}\n"
    elif event_type == "deadline_today":
        msg += f"🚨 Application deadline is TODAY: {college.get('deadline')}\n"
    if college.get("match_score") is not None:
        msg += f"\n📊 Your match score: {college.get('match_score')}%"
    for channel in user.get("channels", []):
        if channel["channel_type"] == "telegram":
            await send_telegram_message(channel["external_id"], msg)
        elif channel["channel_type"] == "whatsapp":
            await send_whatsapp_message(channel["external_id"], msg)


async def run_notification_job() -> None:
    upcoming = get_upcoming_tasks(within_days=3)
    for task in upcoming:
        await notify_user(
            task["user_id"],
            _format_task_message("Upcoming deadline", task),
        )

    overdue = get_overdue_tasks()
    for task in overdue:
        await notify_user(
            task["user_id"],
            _format_task_message("Overdue task", task),
        )

    # College deadline notifications — uses direct query (no raw SQL JOIN)
    rows = cs_q.get_subscriptions_with_deadlines()
    for row in rows:
        user = get_user(row["user_id"])
        if not user:
            continue
        channels = get_channels_for_user(row["user_id"])
        if not channels:
            continue
        user_with_channels = {**user, "channels": channels}
        await send_college_notification(user_with_channels, row, "deadline_approaching")

    # Keyword-based task nudges
    for task in upcoming + overdue:
        title = task["title"].lower()
        if "scholarship" in title:
            await notify_user(task["user_id"], f"Scholarship reminder: {task['title']}")
        if "visa" in title:
            await notify_user(task["user_id"], f"Visa reminder: {task['title']}")
