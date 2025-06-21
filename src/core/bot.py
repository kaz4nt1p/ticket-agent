# Для работы с Telegram Bot API
from fastapi import APIRouter, Request
import httpx
import os
from typing import Optional, Tuple, Union
from dotenv import load_dotenv
from src.core.openai_agent import extract_flight_query
from datetime import datetime, timedelta
import re
from src.core.dialog_memory import save_message_to_memory, get_memory
from src.core.conversation_state import get_conversation_state
from src.services.flight_cache import flight_cache

app = APIRouter()

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
AVIASALES_TOKEN = os.getenv("AVIASALES_TOKEN")

async def search_top_flights(origin: str, destination: str, date: Optional[Union[str, dict]] = None, currency: str = "rub", transfers: str = "any") -> str:
    # --- КЭШИРОВАНИЕ ---
    params_for_cache = {
        "origin": origin,
        "destination": destination,
        "date": date,
        "currency": currency,
        "transfers": transfers
    }
    cached = flight_cache.get(params_for_cache)
    if cached:
        print(f"[CACHE] Found flights in Redis for {params_for_cache}")
        all_flights = cached
    else:
        print(f"[CACHE] No flights in Redis for {params_for_cache}, requesting Aviasales API...")
        url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
        headers = {}
        all_flights = []
        date_list = []
        if isinstance(date, dict) and "from" in date and "to" in date:
            date_str = f"{date['from']} - {date['to']}"
        elif isinstance(date, str):
            date_str = date
        else:
            date_str = None
        if date_str and date_str != "any":
            match = re.match(r"(\d{4}-\d{2}-\d{2})\s*-\s*(\d{4}-\d{2}-\d{2})", date_str)
            if match:
                start = datetime.strptime(match.group(1), "%Y-%m-%d")
                end = datetime.strptime(match.group(2), "%Y-%m-%d")
                delta = (end - start).days
                date_list = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta + 1)]
            else:
                date_list = [d.strip() for d in re.split(r",|;| ", date_str) if re.match(r"\d{4}-\d{2}-\d{2}", d.strip())]
                if not date_list and re.match(r"\d{4}-\d{2}", date_str):
                    date_list = [f"{date_str}-{str(day).zfill(2)}" for day in range(1, 32)]
                if not date_list:
                    date_list = [date_str]
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
            if transfers == 0 or transfers == "0":
                params["direct"] = "true"
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, params=params, headers=headers)
                    data = resp.json()
                    if origin == "MOW" and destination == "NHA":
                        print(f"[DEBUG] Aviasales raw data for {d}: {data.get('data')}")
                    if data.get("success") and data.get("data"):
                        all_flights.extend(data["data"])
            except Exception as e:
                print(f"[ERROR] Ошибка при поиске билетов на дату {d}: {e}")
        # --- Сохраняем в кэш ---
        if all_flights:
            flight_cache.save(params_for_cache, all_flights)
            print(f"[CACHE] Saved {len(all_flights)} flights for {params_for_cache}")
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
                
                # Создаем красивый заголовок для рейсов с пересадками
                result = [f"✈️ Найдены билеты {origin} → {destination}"]
                result.append("⚠️ Прямых рейсов нет, показываю варианты с пересадками")
                
                # Добавляем информацию о поиске
                if date:
                    if isinstance(date, dict):
                        date_info = f"{date['from']} - {date['to']}"
                    else:
                        date_info = date
                    result.append(f"📅 Период: {date_info}")
                
                result.append("")  # Пустая строка для разделения
                
                # Форматируем каждый рейс
                for idx, flight in enumerate(flights, 1):
                    price = flight.get("price")
                    airline = flight.get("airline", "-")
                    depart = flight.get("departure_at", "-")[:10]
                    origin_airport = flight.get("origin_airport", origin)
                    dest_airport = flight.get("destination_airport", destination)
                    link = flight.get("link", "")
                    transfers_count = flight.get("transfers", 0)
                    
                    # Форматируем цену с разделителями
                    formatted_price = f"{price:,}".replace(",", " ")
                    
                    # Создаем красивую карточку рейса
                    flight_card = f"🎫 {idx}. {airline}"
                    flight_card += f"\n💰 {formatted_price} {currency.upper()}"
                    flight_card += f"\n🛫 {origin} ({origin_airport}) → {destination} ({dest_airport})"
                    flight_card += f"\n📅 {depart}"
                    flight_card += f"\n🔄 {transfers_count} пересадка"
                    
                    # Добавляем короткую ссылку на Aviasales
                    aviasales_url = f"https://www.aviasales.com{link}"
                    flight_card += f"\n🔗 [Купить билет]({aviasales_url})"
                    
                    result.append(flight_card)
                    result.append("")  # Пустая строка между рейсами
                
                # Добавляем итоговую информацию
                result.append("💡 Совет: Нажмите на ссылку для покупки билета")
                
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
    
    # Создаем красивый заголовок
    result = [f"✈️ Найдены билеты {origin} → {destination}"]
    
    # Добавляем информацию о поиске
    if date:
        if isinstance(date, dict):
            date_info = f"{date['from']} - {date['to']}"
        else:
            date_info = date
        result.append(f"📅 Период: {date_info}")
    
    if transfers == 0:
        result.append("🛫 Тип: Только прямые рейсы")
    
    result.append("")  # Пустая строка для разделения
    
    # Форматируем каждый рейс
    for idx, flight in enumerate(flights, 1):
        price = flight.get("price")
        airline = flight.get("airline", "-")
        depart = flight.get("departure_at", "-")[:10]
        origin_airport = flight.get("origin_airport", origin)
        dest_airport = flight.get("destination_airport", destination)
        link = flight.get("link", "")
        transfers_count = flight.get("transfers", 0)
        
        # Форматируем цену с разделителями
        formatted_price = f"{price:,}".replace(",", " ")
        
        # Создаем красивую карточку рейса
        flight_card = f"🎫 {idx}. {airline}"
        flight_card += f"\n💰 {formatted_price} {currency.upper()}"
        flight_card += f"\n🛫 {origin} ({origin_airport}) → {destination} ({dest_airport})"
        flight_card += f"\n📅 {depart}"
        
        if transfers_count == 0:
            flight_card += "\n✅ Прямой рейс"
        else:
            flight_card += f"\n🔄 {transfers_count} пересадка"
        
        # Добавляем короткую ссылку на Aviasales
        aviasales_url = f"https://www.aviasales.com{link}"
        flight_card += f"\n🔗 [Купить билет]({aviasales_url})"
        
        result.append(flight_card)
        result.append("")  # Пустая строка между рейсами
    
    # Добавляем итоговую информацию
    result.append("💡 Совет: Нажмите на ссылку для покупки билета")
    
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
            
            # Получаем состояние разговора
            conv_state = get_conversation_state(chat_id)
            current_state = conv_state.get_state()
            
            # Проверяем, не является ли это новым запросом (содержит города)
            # Если текущее сообщение содержит города, а состояние уже заполнено - это новый запрос
            if current_state.get("is_complete") and any(city_word in text.lower() for city_word in ["москва", "банкок", "хошимин", "сочи", "париж", "лондон", "нью-йорк"]):
                print("[NEW CONVERSATION] Detected new city request, clearing state")
                conv_state.clear_state()
                current_state = conv_state.get_state()
            
            # Получаем историю для передачи в LLM (только последние 3 сообщения для контекста)
            history = get_memory(chat_id, k=3)
            if not isinstance(history, list):
                history = []
            else:
                history = [msg.decode('utf-8') if isinstance(msg, bytes) else str(msg) for msg in history]
            
            print(f"[CONVERSATION STATE] Current: {current_state}")
            print(f"[HISTORY] {history}")
            
            # --- Обработка через OpenAI-агента с историей ---
            parsed = await extract_flight_query(text, history=history)
            origin_city = parsed.get("from")
            dest_city = parsed.get("to")
            date = parsed.get("date")
            transfers = parsed.get("transfers", "any")
            need_clarify = parsed.get("need_clarify", [])
            
            print(f"[PARSED] from: {origin_city}, to: {dest_city}, date: {date}, transfers: {transfers}")
            print(f"[NEED_CLARIFY] {need_clarify}")
            
            # Обновляем состояние разговора
            new_params = {
                "from": origin_city if origin_city != "any" else None,
                "to": dest_city if dest_city != "any" else None,
                "date": date if date != "any" else None,
                "transfers": transfers
            }
            updated_state = conv_state.update_state(new_params)
            
            print(f"[UPDATED STATE] {updated_state}")
            
            # Проверяем, есть ли все необходимые параметры
            missing_params = conv_state.get_missing_params()
            
            if missing_params:
                clarification_messages = []
                if "from" in missing_params:
                    clarification_messages.append("📍 Откуда вылетаете?")
                if "to" in missing_params:
                    clarification_messages.append("🎯 Куда летите?")
                if "date" in missing_params:
                    clarification_messages.append("📅 На какую дату нужны билеты?")
                
                clarification_text = "\n".join(clarification_messages)
                await send_message(chat_id, f"❓ Нужна дополнительная информация:\n\n{clarification_text}")
                return {"ok": True}
            
            # Если у нас есть все параметры, ищем билеты
            origin = None
            origin_name = updated_state["from"]
            origin_country = None
            if not origin:
                origin, origin_name, origin_country = await get_iata_code(updated_state["from"])
            
            destination = None
            dest_name = updated_state["to"]
            dest_country = None
            if not destination:
                destination, dest_name, dest_country = await get_iata_code(updated_state["to"])
            
            # Проверяем, что IATA коды найдены
            if not origin:
                await send_message(chat_id, f"❌ Не удалось найти аэропорт для города '{updated_state['from']}'. Пожалуйста, уточните название города.")
                return {"ok": True}
            
            if not destination:
                await send_message(chat_id, f"❌ Не удалось найти аэропорт для города '{updated_state['to']}'. Пожалуйста, уточните название города.")
                return {"ok": True}
            
            # Отправляем сообщение о начале поиска
            search_message = f"🔍 Поиск билетов\n"
            search_message += f"🛫 {origin_name} → {dest_name}"
            
            if updated_state["date"]:
                if isinstance(updated_state["date"], dict):
                    date_info = f"{updated_state['date']['from']} - {updated_state['date']['to']}"
                else:
                    date_info = updated_state["date"]
                search_message += f"\n📅 {date_info}"
            
            if updated_state["transfers"] == 0:
                search_message += "\n✅ Только прямые рейсы"
            
            search_message += "\n\n⏳ Ищу лучшие варианты..."
            
            await send_message(chat_id, search_message)
            
            # --- Поиск билетов ---
            reply = None
            date_param = updated_state["date"] if updated_state["date"] else None
            transfers_param = str(updated_state["transfers"]) if updated_state["transfers"] is not None else "any"
            
            # Если дата указана как конкретный день, но пользователь мог иметь в виду весь месяц
            # Например, "в августе" -> "2025-08-01", но нужно искать весь август
            if date_param and isinstance(date_param, str) and len(date_param) == 10:
                # Проверяем, не является ли это первым днем месяца
                if date_param.endswith("-01"):
                    # Преобразуем в диапазон месяца
                    year_month = date_param[:7]  # "2025-08"
                    from datetime import datetime
                    import calendar
                    
                    # Получаем последний день месяца
                    dt = datetime.strptime(date_param, "%Y-%m-%d")
                    last_day = calendar.monthrange(dt.year, dt.month)[1]
                    date_param = {
                        "from": date_param,
                        "to": f"{year_month}-{last_day:02d}"
                    }
                    print(f"[DATE RANGE] Converting single date to month range: {date_param}")
            
            if origin and destination:
                reply = await search_top_flights(origin, destination, date_param, transfers=transfers_param)
            
            if reply:
                await send_message(chat_id, reply)
                # Очищаем состояние после успешного поиска
                conv_state.clear_state()
                print("[CONVERSATION CLEARED] State cleared after successful search")
            else:
                await send_message(chat_id, "❌ Не удалось найти билеты по вашему запросу.")
            
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
