# Для работы с Telegram Bot API
from fastapi import FastAPI, Request
import httpx
import os
from typing import Optional, Tuple
from dotenv import load_dotenv
from openai_agent import extract_flight_query
from datetime import datetime, timedelta
import re
from flight_cache import get_flight_from_cache, set_flight_to_cache
from dialog_memory import save_message_to_memory, get_memory

app = FastAPI()

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
AVIASALES_TOKEN = os.getenv("AVIASALES_TOKEN")

async def search_top_flights(origin: str, destination: str, date: str = None, currency: str = "rub", transfers: str = "any") -> str:
    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
    headers = {}
    all_flights = []
    # Обработка диапазона дат или списка дат
    date_list = []
    # --- Исправление: поддержка dict для диапазона дат ---
    if isinstance(date, dict) and "from" in date and "to" in date:
        date = f"{date['from']} - {date['to']}"
    if date and date != "any":
        # Диапазон дат: 2025-08-07 - 2025-08-10
        match = re.match(r"(\d{4}-\d{2}-\d{2})\s*-\s*(\d{4}-\d{2}-\d{2})", date)
        if match:
            start = datetime.strptime(match.group(1), "%Y-%m-%d")
            end = datetime.strptime(match.group(2), "%Y-%m-%d")
            delta = (end - start).days
            date_list = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta + 1)]
        else:
            # Список дат через запятую: 2025-08-07,2025-08-10
            date_list = [d.strip() for d in re.split(r",|;| ", date) if re.match(r"\d{4}-\d{2}-\d{2}", d.strip())]
            if not date_list and re.match(r"\d{4}-\d{2}", date):
                # Только месяц: 2025-08
                date_list = [f"{date}-{str(day).zfill(2)}" for day in range(1, 32)]
            if not date_list:
                date_list = [date]
    else:
        date_list = [None]
    for d in date_list:
        params = {
            "origin": origin,
            "destination": destination,
            "one_way": "true",
            "currency": currency,
            "token": AVIASALES_TOKEN,
            "limit": 5,
            "sorting": "price"
        }
        if d:
            params["departure_at"] = d
        # Добавляем direct=true, если нужны только прямые рейсы
        if transfers == 0 or transfers == "0":
            params["direct"] = "true"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, headers=headers)
                data = resp.json()
                # Логируем только найденные рейсы по направлению Москва–Нячанг
                if origin == "MOW" and destination == "NHA":
                    print(f"[DEBUG] Aviasales raw data for {d}: {data.get('data')}")
                # Убираем неинформативный огромный лог
                # print(f"[AVIASALES] Response for {d}:", data)
                if data.get("success") and data.get("data"):
                    all_flights.extend(data["data"])
        except Exception as e:
            print(f"[ERROR] Ошибка при поиске билетов на дату {d}: {e}")
    if not all_flights:
        return "Билеты не найдены."
    # --- Новая логика фильтрации по пересадкам ---
    original_flights = all_flights.copy()
    if transfers == 0 or transfers == "0":
        all_flights = [f for f in all_flights if f.get("transfers", 0) == 0]
        if not all_flights:
            # Нет прямых рейсов, но есть с пересадками
            if original_flights:
                # Показываем варианты с пересадками с явным предупреждением
                # Оставляем только уникальные рейсы по дате
                seen = set()
                unique_flights = []
                for f in original_flights:
                    key = (f.get("departure_at"), f.get("origin"), f.get("destination"))
                    if key not in seen:
                        seen.add(key)
                        unique_flights.append(f)
                unique_flights.sort(key=lambda x: x.get("price", 999999))
                flights = unique_flights[:5]
                result = ["Прямых рейсов не найдено на выбранные даты, вот варианты с пересадками:"]
                for idx, flight in enumerate(flights, 1):
                    price = flight.get("price")
                    airline = flight.get("airline", "-")
                    depart = flight.get("departure_at", "-")[:10]
                    origin_airport = flight.get("origin_airport", origin)
                    dest_airport = flight.get("destination_airport", destination)
                    link = flight.get("link", "")
                    transfers = flight.get("transfers", 0)
                    result.append(
                        f"{idx}. {origin} ({origin_airport}) - {destination} ({dest_airport}) от {price} {currency.upper()} (https://www.aviasales.com{link})\n- Дата вылета: {depart} и другие.\n- {airline}, {transfers} пересадки\n- Сравнить цены: Trip.com (https://l.katus.ai/cRCYBF)\n"
                    )
                return "\n".join(result)
            else:
                return "Билеты не найдены."
    # Оставляем только уникальные рейсы по дате
    seen = set()
    unique_flights = []
    for f in all_flights:
        key = (f.get("departure_at"), f.get("origin"), f.get("destination"))
        if key not in seen:
            seen.add(key)
            unique_flights.append(f)
    # Сортируем по цене
    unique_flights.sort(key=lambda x: x.get("price", 999999))
    flights = unique_flights[:5]
    result = [f"Вот самые дешевые авиабилеты из {origin} в {destination} на выбранные даты:"]
    for idx, flight in enumerate(flights, 1):
        price = flight.get("price")
        airline = flight.get("airline", "-")
        depart = flight.get("departure_at", "-")[:10]
        origin_airport = flight.get("origin_airport", origin)
        dest_airport = flight.get("destination_airport", destination)
        link = flight.get("link", "")
        transfers = flight.get("transfers", 0)
        result.append(
            f"{idx}. {origin} ({origin_airport}) - {destination} ({dest_airport}) от {price} {currency.upper()} (https://www.aviasales.com{link})\n- Дата вылета: {depart} и другие.\n- {airline}, {transfers} пересадки\n- Сравнить цены: Trip.com (https://l.katus.ai/cRCYBF)\n"
        )
    return "\n".join(result)

async def get_iata_code(city_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Пытается получить IATA-код города через Aviasales API. Если найден город — возвращает его код, имя и страну. Если страна — возвращает код самого популярного города страны."""
    url = "https://autocomplete.travelpayouts.com/places2"
    params = {"term": city_name, "locale": "ru", "types[]": "city"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            print(f"[IATA] Autocomplete response for '{city_name}':", data)
            if data and isinstance(data, list):
                # Пробуем найти точное совпадение по названию города
                for item in data:
                    if item.get("name", "").lower() == city_name.lower():
                        print(f"[IATA] Точное совпадение: {item.get('name')} -> {item.get('code')}")
                        return item.get("code"), item.get("name"), item.get("country_name")
                # Если не найдено точного совпадения, ищем по стране
                # Берём первый город из списка и возвращаем его код
                if data:
                    first_city = data[0]
                    print(f"[IATA] Нет точного совпадения, беру первый город страны: {first_city.get('name')} ({first_city.get('country_name')}) -> {first_city.get('code')}")
                    return first_city.get("code"), first_city.get("name"), first_city.get("country_name")
                else:
                    print(f"[IATA] Нет результатов для '{city_name}'")
    except Exception as e:
        print(f"[IATA ERROR] {e}")
    return None, None, None

# SYSTEM_PROMPT: Сначала вызывай flight_cache. Если вернулся null — AviasalesSearchTool, потом flight_cache с новым списком.

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        print("[WEBHOOK] Incoming data:", data)
        chat_id = data.get("message", {}).get("chat", {}).get("id")
        text = data.get("message", {}).get("text", "")
        if chat_id and text:
            # Сохраняем сообщение пользователя в память (контекст)
            save_message_to_memory(chat_id, text, k=10)
            # Получаем историю для передачи в LLM (без текущего сообщения):
            history = get_memory(chat_id, k=10)[:-1] if get_memory(chat_id, k=10) else []
            # --- Новый универсальный режим: обработка любого текста через OpenAI-агента ---
            parsed = await extract_flight_query(text, history=history)
            origin_city = parsed.get("from")
            dest_city = parsed.get("to")
            date = parsed.get("date")
            transfers = parsed.get("transfers", "any")
            # Если хотя бы один из параметров не определён — уточняем только его
            missing = []
            if not origin_city or origin_city == "any":
                missing.append("город вылета")
            if not dest_city or dest_city == "any":
                missing.append("город назначения")
            if missing:
                await send_message(chat_id, f"Пожалуйста, укажите: {', '.join(missing)}.")
                return {"ok": True}
            # --- Автоматическое определение IATA ---
            origin = None
            origin_name = origin_city
            origin_country = None
            if not origin:
                origin, origin_name, origin_country = await get_iata_code(origin_city)
            destination = None
            dest_name = dest_city
            dest_country = None
            if not destination:
                destination, dest_name, dest_country = await get_iata_code(dest_city)
            reply = None
            # --- Исправление: если дата не указана или any, не подставлять дату ---
            date_param = date if (date and date != "any") else None
            if origin and destination:
                reply = await search_top_flights(origin, destination, date_param, transfers=transfers)
            if reply:
                await send_message(chat_id, reply)
            else:
                await send_message(chat_id, "Не удалось найти билеты по вашему запросу.")
            return {"ok": True}
        else:
            print("[WEBHOOK] Нет chat_id или текста в сообщении")
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")
    return {"ok": True}

async def send_message(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            TELEGRAM_API_URL,
            json={"chat_id": chat_id, "text": text}
        )
