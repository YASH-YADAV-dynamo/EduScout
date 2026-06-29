from fastapi import APIRouter, HTTPException, Query, Request

from app.config import settings
from app.services.link import redeem_link_code

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    payload = await request.json()
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                phone = message.get("from", "")
                text = message.get("text", {}).get("body", "").strip()
                if text.upper().startswith("LINK "):
                    code = text.split(" ", 1)[1].strip()
                    result = redeem_link_code(code, "whatsapp", phone)
                    if result:
                        await _send_reply(phone, "WhatsApp linked successfully.")
                    else:
                        await _send_reply(phone, "Invalid or expired link code.")
    return {"status": "ok"}


async def _send_reply(phone: str, text: str) -> None:
    from app.services.notifications import send_whatsapp_message

    await send_whatsapp_message(phone, text)
