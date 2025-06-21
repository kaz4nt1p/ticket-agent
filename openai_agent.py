import os
import httpx
import json
from dotenv import load_dotenv
from app.llm_config import get_parser_llm
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

PROMPT = """
Ты – AI-ассистент по поиску авиабилетов.

⦿ Твоя цель: из сообщения пользователя выделить ▸ from (город/аэропорт вылета) ▸ to (город/аэропорт назначения) ▸ date ▸ transfers (количество пересадок)
   – date может быть:
     • одна точная дата → формат \"YYYY-MM-DD\"
     • диапазон → объект { \"from\": \"YYYY-MM-DD\", \"to\": \"YYYY-MM-DD\" }
     • неизвестна → строка \"any\"
   – transfers может быть:
     • 0 — только прямые рейсы (без пересадок)
     • any — любые пересадки

⦿ Если параметра нет **в явном виде**, делай так:
   1) проверь последние сообщения (память чата) и возьми последнее валидное значение;
   2) проверь профиль пользователя (ключ *home_city*) – если есть, подставь в from;
   3) если всё ещё пусто – верни \"any\" **и добавь ключ \"need_clarify\": [\"from\"] / [\"to\"] / [\"date\"] / [\"transfers\"]**.

⦿ Формат ответа – СТРОГО JSON **одной строкой**:
{
  \"from\": \"<город|IATA|any>\",
  \"to\": \"<город|IATA|any>\",
  \"date\": \"<строка или объект диапазона>\",
  \"transfers\": <0|"any">,
  \"need_clarify\": []
}

⦿ Никаких пояснений, лишних слов и перевода строк.

⦿ Примеры
-----------
User: \"Хочу в Челябинск 8 августа без пересадок\"
→ {\"from\":\"any\",\"to\":\"Челябинск\",\"date\":\"2025-08-08\",\"transfers\":0,\"need_clarify\":[]}

User: \"Москва Бангкок 15.07.2025\"
→ {\"from\":\"Москва\",\"to\":\"Бангкок\",\"date\":\"2025-07-15\",\"transfers\":\"any\",\"need_clarify\":[]}

User: \"Билеты в Сочи?\"
→ {\"from\":\"any\",\"to\":\"Сочи\",\"date\":\"any\",\"transfers\":\"any\",\"need_clarify\":[\"from\",\"date\"]}

User: \"во второй половине августа в Сочи без пересадок\"
→ {\"from\":\"any\",\"to\":\"Сочи\",\"date\":{\"from\":\"2025-08-16\",\"to\":\"2025-08-31\"},\"transfers\":0,\"need_clarify\":[\"from\"]}
"""

PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["user_text"],
    template=PROMPT + "\nUser: {user_text}"
)

def build_openai_messages(user_text: str, history: list[str] = None):
    messages = [
        {"role": "system", "content": PROMPT}
    ]
    if history:
        for msg in history:
            messages.append({"role": "user", "content": msg})
    messages.append({"role": "user", "content": user_text})
    return messages

async def extract_flight_query(user_text: str, history: list[str] = None) -> dict:
    llm = get_parser_llm()
    chain = LLMChain(llm=llm, prompt=PROMPT_TEMPLATE)
    try:
        answer = chain.run(user_text=user_text)
        print(f"[LLM RAW ANSWER] {answer}")
        parsed = json.loads(answer)
    except Exception as e:
        print(f"[LLM PARSE ERROR] {e}")
        parsed = {"from": "any", "to": "any", "date": "any", "need_clarify": ["from", "to", "date"]}
    return parsed

# Пример использования:
# import asyncio
# print(asyncio.run(extract_flight_query("есть ли билеты в Бали завтра?")))
