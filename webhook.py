from fastapi import APIRouter, Request
import logging

router = APIRouter()

@router.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    logging.info(f"Received webhook: {data}")
    # Здесь добавьте обработку входящих сообщений от Telegram
    return {"ok": True}
