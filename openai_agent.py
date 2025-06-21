import os
import httpx
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

PROMPT = (
    "Ты — AI-ассистент для поиска авиабилетов.\n"
    "Твоя задача: из любого сообщения пользователя выделить город вылета, город назначения и дату (или диапазон дат).\n"
    "Отвечай ТОЛЬКО в формате: from=<город вылета>; to=<город назначения>; date=<дата в формате ГГГГ-ММ-ДД или 'any'>.\n"
    "Если что-то не указано — подставь 'any'.\n"
    "Примеры:\n"
    "Пользователь: есть ли билеты в Бали завтра?\n"
    "Ответ: from=any; to=Денпасар; date=2025-06-20\n"
    "Пользователь: Москва Бангкок 15.07.2025\n"
    "Ответ: from=Москва; to=Бангкок; date=2025-07-15\n"
    "Пользователь: хочу в Сочи\n"
    "Ответ: from=any; to=Сочи; date=any\n"
)

def build_openai_messages(user_text: str):
    return [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": user_text}
    ]

async def extract_flight_query(user_text: str) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": build_openai_messages(user_text),
        "max_tokens": 50,
        "temperature": 0.0
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(OPENAI_API_URL, headers=headers, json=data)
        resp.raise_for_status()
        result = resp.json()
        answer = result["choices"][0]["message"]["content"]
        print(f"[OPENAI RAW ANSWER] {answer}")
        parsed = {}
        for item in answer.split("; "):
            if "=" in item:
                k, v = item.split("=", 1)
                parsed[k.strip()] = v.strip()
        return parsed

# Пример использования:
# import asyncio
# print(asyncio.run(extract_flight_query("есть ли билеты в Бали завтра?")))
