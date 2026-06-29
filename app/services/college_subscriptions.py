from app.config import settings
from app.query import college_subscriptions as q
from app.services.user import get_user

MAX_SUBSCRIPTIONS = 10


def count_subscriptions(user_id: int) -> int:
    return q.count_subscriptions(user_id)


def add_subscription(user_id: int, university_id: int) -> dict:
    count = count_subscriptions(user_id)
    if count >= MAX_SUBSCRIPTIONS:
        return {"status": "limit_reached", "count": count, "max": MAX_SUBSCRIPTIONS}

    ok = q.insert_subscription(user_id, university_id)
    if not ok:
        return {"status": "already_subscribed", "count": count, "max": MAX_SUBSCRIPTIONS}

    user = get_user(user_id) or {}
    bot = settings.telegram_bot_username or "StudyAbroadAgentBot"
    invite_link = f"https://t.me/{bot}?start={user.get('esid', '')}"

    return {
        "status": "subscribed",
        "esid": user.get("esid"),
        "telegram_invite_link": invite_link,
        "subscribed_count": count + 1,
        "max": MAX_SUBSCRIPTIONS,
    }


def remove_subscription(user_id: int, university_id: int) -> bool:
    return q.delete_subscription(user_id, university_id)


def list_subscriptions(user_id: int) -> list[dict]:
    return q.list_subscriptions_for_user(user_id)


def get_user_subscriptions_with_colleges(user_id: int) -> list[dict]:
    return list_subscriptions(user_id)
