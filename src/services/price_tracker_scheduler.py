from apscheduler.schedulers.background import BackgroundScheduler
from src.services.price_tracker_db import get_tracked_flights, update_flight_price
from src.services.redis_client import redis_client
import httpx
import os
import time
import json
import asyncio

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
AVIASALES_TOKEN = os.getenv("AVIASALES_TOKEN")

CACHE_TTL = 60 * 25  # 25 минут

def get_price_cache_key(from_city, to_city, date, flight_number):
    return f"price_check:{from_city}:{to_city}:{date}:{flight_number}"

async def check_and_notify_price_drop():
    flights = get_tracked_flights()
    for flight in flights:
        chat_id = flight["chat_id"]
        flight_number = flight["flight_number"]
        date = flight["date"]
        from_city = flight["from_city"]
        to_city = flight["to_city"]
        old_price = flight["current_price"]
        cache_key = get_price_cache_key(from_city, to_city, date, flight_number)
        new_price = None
        # Проверяем кэш в Redis
        cached = redis_client.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                new_price = data.get("price")
            except Exception:
                new_price = None
        else:
            # --- Запрос к Aviasales ---
            url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
            params = {
                "origin": from_city,
                "destination": to_city,
                "departure_at": date,
                "one_way": "true",
                "currency": "rub",
                "token": AVIASALES_TOKEN,
                "limit": 5,
                "sorting": "price"
            }
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, params=params)
                    data = await resp.json()
                    if data.get("success") and data.get("data"):
                        for f in data["data"]:
                            if (f.get("flight_number") == flight_number or not flight_number) and f.get("departure_at", "")[:10] == date:
                                new_price = f.get("price")
                                # Кэшируем результат
                                redis_client.setex(cache_key, CACHE_TTL, json.dumps({"price": new_price}))
                                break
            except Exception as e:
                print(f"[SCHEDULER ERROR] {e}")
        if new_price is not None and new_price < old_price:
            update_flight_price(flight["id"], new_price)
            text = f"🔥 Новый билет по вашей подписке! Цены стали ниже. Вот самые дешевые авиабилеты в одну сторону из {from_city} в {to_city} на {date}:\n\n💰 {new_price:,} руб. (было {old_price:,} руб.)"
            await send_telegram_message(chat_id, text)

async def send_telegram_message(chat_id, text):
    async with httpx.AsyncClient() as client:
        await client.post(
            TELEGRAM_API_URL,
            json={"chat_id": chat_id, "text": text}
        )

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Каждые 30 минут
    scheduler.add_job(lambda: asyncio.run(check_and_notify_price_drop()), 'interval', minutes=30)
    scheduler.start()
    print("[SCHEDULER] Started price tracker scheduler")

# Для запуска вручную (например, из main.py)
if __name__ == "__main__":
    start_scheduler()
    while True:
        time.sleep(60) 