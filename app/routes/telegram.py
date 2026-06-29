import re

from fastapi import APIRouter, Request

from app.services.college_subscriptions import list_subscriptions
from app.services.link import get_user_by_chat_id, save_linked_channel
from app.services.notifications import send_telegram_message
from app.services.user import get_user_by_esid

router = APIRouter(prefix="/telegram", tags=["telegram"])


def is_esid_format(text: str) -> bool:
    return bool(re.match(r"^[A-Z]{2}\d{4,}$", text.strip().upper()))


async def handle_esid_link(chat_id: str, esid: str) -> None:
    user = get_user_by_esid(esid)
    if not user:
        await send_telegram_message(
            chat_id,
            f"❌ ESID '{esid}' not found. Please check and try again.",
        )
        return

    save_linked_channel(user["id"], "telegram", str(chat_id))
    subs = list_subscriptions(user["id"])
    sub_list = "\n".join([f"📌 {s['university_name']}" for s in subs]) or "(none yet)"
    score = user.get("overall_score") or 0

    await send_telegram_message(
        chat_id,
        f"✅ Linked successfully!\n\n"
        f"👤 {user['name']} · ESID: {user['esid']}\n"
        f"📊 Profile Score: {score}/100\n\n"
        f"🏫 Your college subscriptions:\n{sub_list}\n\n"
        f"You'll receive deadline reminders and updates here automatically.",
    )


@router.post("/webhook")
async def telegram_webhook(request: Request):
    payload = await request.json()
    message = payload.get("message") or payload.get("edited_message")
    if not message:
        return {"status": "ok"}

    chat_id = str(message["chat"]["id"])
    text = (message.get("text") or "").strip()

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        esid = parts[1].strip().upper() if len(parts) > 1 else None
        if esid:
            await handle_esid_link(chat_id, esid)
        else:
            await send_telegram_message(
                chat_id,
                "Welcome to Study Abroad Agent! 🎓\n"
                "Please send your ESID (e.g. AB1234) to link your account.",
            )
    elif is_esid_format(text):
        await handle_esid_link(chat_id, text.upper())
    elif text.upper().startswith("/link"):
        from app.services.link import redeem_link_code

        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await send_telegram_message(chat_id, "Usage: /link YOUR_CODE")
            return {"status": "ok"}
        result = redeem_link_code(parts[1], "telegram", chat_id)
        if result:
            await send_telegram_message(chat_id, "Telegram linked successfully.")
        else:
            await send_telegram_message(chat_id, "Invalid or expired link code.")
    else:
        user = get_user_by_chat_id(chat_id)
        if user:
            subs = list_subscriptions(user["id"])
            sub_list = "\n".join([f"📌 {s['university_name']}" for s in subs]) or "(none yet)"
            await send_telegram_message(
                chat_id,
                f"Hi {user['name']}! Your subscribed colleges:\n{sub_list}\n\n"
                f"I'll notify you about deadlines and updates automatically.",
            )
        else:
            await send_telegram_message(
                chat_id,
                "Please send your ESID to link your account. "
                "Find it in your Study Abroad Agent chat on ChatGPT.",
            )
    return {"status": "ok"}
