import os
from dotenv import load_dotenv
load_dotenv()
from apscheduler.schedulers.background import BackgroundScheduler
from src.services.price_tracker_db import get_tracked_flights, update_flight_price
from src.services.redis_client import redis_client
import httpx
import time
import json
import asyncio
import traceback
import inspect
import tracemalloc

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

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
            print(f"[CACHE HIT] {cache_key}")
            try:
                if isinstance(cached, (str, bytes)):
                    data = json.loads(cached)
                    new_price = data.get("price")
                else:
                    print(f"[CACHE ERROR] cached is not str/bytes: {type(cached)}")
                    new_price = None
            except Exception:
                new_price = None
        else:
            print(f"[CACHE MISS] {cache_key}")
            # --- Запрос к Aviasales ---
            url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
            # print('ENV AVIASALES_TOKEN:', os.getenv('AVIASALES_TOKEN'))  # Удалено для безопасности
            token = os.getenv("AVIASALES_TOKEN")
            params = {
                "origin": from_city,
                "destination": to_city,
                "departure_at": date,
                "one_way": "true",
                "currency": "rub",
                "token": token,
                "limit": 5,
                "sorting": "price"
            }
            print(f"[DEBUG] Aviasales request: url={url}, params={{...}}")  # token не выводим
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, params=params)
                    print(f"[DEBUG] resp type: {type(resp)}; is dict: {isinstance(resp, dict)}; has json: {hasattr(resp, 'json')}")
                    if isinstance(resp, dict):
                        data = resp
                    elif hasattr(resp, 'json') and callable(resp.json):
                        json_result = resp.json()
                        if inspect.isawaitable(json_result):
                            data = await json_result
                        elif isinstance(json_result, dict):
                            data = json_result
                        else:
                            try:
                                data = json_result()
                            except Exception as e:
                                print(f"[SCHEDULER ERROR] Could not call json_result: {e}")
                                data = {}
                    else:
                        print(f"[SCHEDULER ERROR] Unexpected resp type: {type(resp)}")
                        data = {}
                    print(f"[DEBUG] Parsed data: {type(data)} {data if isinstance(data, dict) else str(data)[:200]}")
                    if data.get("success") and data.get("data"):
                        for f in data["data"]:
                            if (f.get("flight_number") == flight_number or not flight_number) and f.get("departure_at", "")[:10] == date:
                                new_price = f.get("price")
                                # Кэшируем результат
                                redis_client.setex(cache_key, CACHE_TTL, json.dumps({"price": new_price}))
                                break
            except Exception as e:
                print(f"[SCHEDULER ERROR] Unexpected exception: {e}; content={getattr(resp, 'content', None)}")
                data = {}
        if new_price is not None and new_price < old_price:
            update_flight_price(flight["id"], new_price)
            # Формируем ссылку и детали рейса, если есть данные
            aviasales_url = None
            airline = flight.get("airline", "-")
            depart = flight.get("departure_time", "-")[:10] if flight.get("departure_time") else date
            origin_airport = flight.get("from_city", from_city)
            dest_airport = flight.get("to_city", to_city)
            transfers_count = flight.get("transfers", 0)
            link = None
            # Пытаемся получить ссылку из кэша Aviasales (если есть)
            if cached and isinstance(cached, (str, bytes)):
                try:
                    data = json.loads(cached)
                    link = data.get("link")
                except Exception:
                    link = None
            if not link:
                link = ""
            aviasales_url = f"https://www.aviasales.com{link}" if link else "https://www.aviasales.com"
            formatted_price = f"{new_price:,}".replace(",", " ")
            formatted_old_price = f"{old_price:,}".replace(",", " ")
            flight_card = f"{origin_airport} - {dest_airport} от [{formatted_price} RUB]({aviasales_url})\n- Дата вылета: {depart}\n- {airline}, {transfers_count} пересадки"
            text = f"🔥 Новый билет по вашей подписке! Цены стали ниже.\n\n{flight_card}\n\n💰 {formatted_price} руб. (было {formatted_old_price} руб.)"
            await send_telegram_message(chat_id, text)

async def send_telegram_message(chat_id, text):
    async with httpx.AsyncClient() as client:
        await client.post(
            TELEGRAM_API_URL,
            json={"chat_id": chat_id, "text": text}
        )

def run_async_job():
    # Диагностика памяти перед запуском задачи
    snapshot1 = tracemalloc.take_snapshot()
    asyncio.run(check_and_notify_price_drop())
    snapshot2 = tracemalloc.take_snapshot()
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    print("[TRACEMALLOC] Top 10 memory changes:")
    for stat in top_stats[:10]:
        print(stat)

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Каждые 3 часа
    scheduler.add_job(
        run_async_job,
        "interval",
        seconds=10800,  # 3 часа
        id="price_tracker_job",
        replace_existing=True,
    )
    scheduler.start()
    print("[SCHEDULER] Started price tracker scheduler (interval: 3 hours)")

# Для запуска вручную (например, из main.py)
if __name__ == "__main__":
    tracemalloc.start()
    start_scheduler()
    while True:
        time.sleep(60) 