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
from src.core.bot import get_unsubscribe_buttons

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

CACHE_TTL = 60 * 25  # 25 минут

def get_price_cache_key(from_city, to_city, date, flight_number):
    return f"price_check:{from_city}:{to_city}:{date}:{flight_number}"

async def check_and_notify_price_drop():
    flights = get_tracked_flights()
    print(f"[SCHEDULER] Found {len(flights)} tracked flights")
    for flight in flights:
        chat_id = flight["chat_id"]
        flight_number = flight["flight_number"]
        date = flight["date"]
        from_city = flight["from_city"]
        to_city = flight["to_city"]
        old_price = flight["current_price"]
        subscribed_transfers = flight.get("transfers", None)
        print(f"[SCHEDULER] Checking flight: {from_city}->{to_city} {date} {flight_number}, old_price={old_price}, transfers={subscribed_transfers}")
        cache_key = get_price_cache_key(from_city, to_city, date, flight_number)
        new_price = None
        found_transfers = None
        fresh_link = None
        # Проверяем кэш в Redis
        cached = redis_client.get(cache_key)
        if cached:
            print(f"[CACHE HIT] {cache_key}")
            try:
                if isinstance(cached, (str, bytes)):
                    data = json.loads(cached)
                    new_price = data.get("price")
                    found_transfers = data.get("transfers")
                    print(f"[CACHE] Retrieved price: {new_price}, transfers: {found_transfers}")
                else:
                    print(f"[CACHE ERROR] cached is not str/bytes: {type(cached)}")
                    new_price = None
            except Exception as e:
                print(f"[CACHE ERROR] Failed to parse cached data: {e}")
                new_price = None
        else:
            print(f"[CACHE MISS] {cache_key}")
            url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
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
            print(f"[DEBUG] Aviasales request: url={url}, params={{...}}")
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, params=params)
                    data = resp.json()
                    if data.get("success") and data.get("data"):
                        # Сначала ищем точное совпадение по номеру рейса
                        for f in data["data"]:
                            if (f.get("flight_number") == flight_number or not flight_number) and f.get("departure_at", "")[:10] == date:
                                new_price = f.get("price")
                                found_transfers = f.get("transfers", None)
                                fresh_link = f.get("link", None)
                                print(f"[AVIASALES] Found exact match flight {f.get('flight_number')}, price: {new_price}, transfers: {found_transfers}, link: {fresh_link}")
                                redis_client.setex(cache_key, CACHE_TTL, json.dumps({"price": new_price, "link": fresh_link, "transfers": found_transfers}))
                                break
                        # Если точного совпадения нет, берем первый рейс с подходящей датой
                        if new_price is None:
                            for f in data["data"]:
                                if f.get("departure_at", "")[:10] == date:
                                    new_price = f.get("price")
                                    found_transfers = f.get("transfers", None)
                                    fresh_link = f.get("link", None)
                                    print(f"[AVIASALES] Found flight with same date {f.get('flight_number')}, price: {new_price}, transfers: {found_transfers}, link: {fresh_link}")
                                    redis_client.setex(cache_key, CACHE_TTL, json.dumps({"price": new_price, "link": fresh_link, "transfers": found_transfers}))
                                    break
            except Exception as e:
                print(f"[SCHEDULER ERROR] Unexpected exception: {e}; content={getattr(resp, 'content', None)}")
                data = {}
        print(f"[SCHEDULER] Final comparison: new_price={new_price}, old_price={old_price}, found_transfers={found_transfers}")
        # --- БАГФИКС: Проверка на пересадки ---
        if subscribed_transfers == 0 and (found_transfers is None or found_transfers > 0):
            print(f"[SCHEDULER] Skipping notification: user subscribed to direct flights only, but found flight has stopovers.")
            continue
        if new_price is not None and new_price < old_price:
            print(f"[SCHEDULER] Price drop detected! Sending notification to chat_id={chat_id}")
            update_flight_price(flight["id"], new_price)
            airline = flight.get("airline", "-")
            depart = flight.get("departure_time", "-")[:10] if flight.get("departure_time") else date
            origin_airport = flight.get("from_city", from_city)
            dest_airport = flight.get("to_city", to_city)
            transfers_count = found_transfers if found_transfers is not None else flight.get("transfers", 0)
            # --- Всегда используем свежую ссылку, если она есть ---
            link = fresh_link
            if not link and cached and isinstance(cached, (str, bytes)):
                try:
                    data = json.loads(cached)
                    link = data.get("link")
                except Exception:
                    link = None
            if not link:
                link = ""
            aviasales_url = f"https://www.aviasales.com{link}" if link else None
            formatted_price = f"{new_price:,}".replace(",", " ")
            formatted_old_price = f"{old_price:,}".replace(",", " ")
            # Цена как гиперссылка, если есть ссылка
            if aviasales_url:
                price_md = f"[{formatted_price} RUB]({aviasales_url})"
            else:
                price_md = f"{formatted_price} RUB (ссылка не найдена)"
            flight_card = f"{origin_airport} - {dest_airport} от {price_md}\n- Дата вылета: {depart}\n- {airline}, {transfers_count} пересадки"
            text = f"🔥 Новый билет по вашей подписке! Цены стали ниже.\n\n{flight_card}\n\n💰 {formatted_price} руб. (было {formatted_old_price} руб.)"
            print(f"[SCHEDULER] Sending message: {text[:100]}...")
            await send_telegram_message(chat_id, text, reply_markup=get_unsubscribe_buttons())
            print(f"[SCHEDULER] Message sent successfully to chat_id={chat_id}")
        else:
            print(f"[SCHEDULER] No price drop for this flight")

async def send_telegram_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient() as client:
        await client.post(
            TELEGRAM_API_URL,
            json=payload
        )

def run_async_job():
    # Диагностика памяти перед запуском задачи
    try:
        snapshot1 = tracemalloc.take_snapshot()
        asyncio.run(check_and_notify_price_drop())
        snapshot2 = tracemalloc.take_snapshot()
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        print("[TRACEMALLOC] Top 10 memory changes:")
        for stat in top_stats[:10]:
            print(stat)
    except RuntimeError:
        # Если tracemalloc не запущен, просто выполняем задачу без диагностики
        print("[SCHEDULER] tracemalloc not started, running job without memory diagnostics")
        asyncio.run(check_and_notify_price_drop())

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Каждые 30 минут
    scheduler.add_job(
        run_async_job,
        'interval',
        minutes=30,  # Было hours=3
        id='price_tracker_job',
        replace_existing=True
    )
    scheduler.start()
    print("[SCHEDULER] Started price tracker scheduler (interval: 30 minutes)")

# Для запуска вручную (например, из main.py)
if __name__ == "__main__":
    tracemalloc.start()
    start_scheduler()
    while True:
        time.sleep(60) 