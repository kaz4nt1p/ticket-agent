import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from src.config.llm_config import get_parser_llm
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

PROMPT = """
Ты – AI-ассистент по поиску авиабилетов.

⦿ Твоя цель: из сообщения пользователя выделить ▸ from (город/аэропорт вылета) ▸ to (город/аэропорт назначения) ▸ date ▸ transfers (количество пересадок)
   – date может быть:
     • одна точная дата → формат "YYYY-MM-DD"
     • диапазон → объект {{ "from": "YYYY-MM-DD", "to": "YYYY-MM-DD" }}
     • неизвестна → строка "any"
   – transfers может быть:
     • 0 — только прямые рейсы (без пересадок)
     • any — любые пересадки

⦿ ВАЖНО: Фокусируйся на ТЕКУЩЕМ сообщении пользователя:
   1) Если текущее сообщение содержит города - используй их
   2) Если текущее сообщение содержит дату - используй её
   3) Если текущее сообщение содержит информацию о пересадках - используй её
   4) История используется ТОЛЬКО для контекста, если текущее сообщение неполное

⦿ ПРАВИЛО: Если текущее сообщение содержит новые города - игнорируй старые из истории

⦿ ОСОБОЕ ВНИМАНИЕ на даты:
   • "Июль-Август" → {{"from":"2025-07-01","to":"2025-08-31"}}
   • "Июль" → {{"from":"2025-07-01","to":"2025-07-31"}}
   • "Август" → {{"from":"2025-08-01","to":"2025-08-31"}}
   • "конец августа" → {{"from":"2025-08-16","to":"2025-08-31"}}
   • "начало июля" → {{"from":"2025-07-01","to":"2025-07-15"}}

⦿ Формат ответа – СТРОГО JSON **одной строкой**:
{{
  "from": "<город|IATA|any>",
  "to": "<город|IATA|any>",
  "date": "<строка или объект диапазона>",
  "transfers": <0|"any">,
  "need_clarify": []
}}

⦿ Никаких пояснений, лишних слов и перевода строк.

⦿ Примеры
-----------
История: ["Москва Бангкок", "вторая половина августа"]
Текущее: "москва хошимин"
→ {{"from":"Москва","to":"Хошимин","date":"any","transfers":"any","need_clarify":["date"]}}

История: ["москва хошимин"]
Текущее: "конец августа"
→ {{"from":"Москва","to":"Хошимин","date":{{"from":"2025-08-16","to":"2025-08-31"}},"transfers":"any","need_clarify":[]}}

История: []
Текущее: "Москва Бангкок Июль-Август"
→ {{"from":"Москва","to":"Бангкок","date":{{"from":"2025-07-01","to":"2025-08-31"}},"transfers":"any","need_clarify":[]}}

История: []
Текущее: "Билеты в Сочи?"
→ {{"from":"any","to":"Сочи","date":"any","transfers":"any","need_clarify":["from","date"]}}
"""

PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["history", "user_text"],
    template=PROMPT + "\nИстория: {history}\nТекущее: {user_text}"
)

def build_openai_messages(user_text: str, history: Optional[list[str]] = None):
    messages = [
        {"role": "system", "content": PROMPT}
    ]
    if history:
        for msg in history:
            messages.append({"role": "user", "content": msg})
    messages.append({"role": "user", "content": user_text})
    return messages

async def extract_flight_query(user_text: str, history: Optional[list[str]] = None) -> dict:
    llm = get_parser_llm()
    
    # Format history for the prompt
    history_text = str(history) if history else "[]"
    
    chain = LLMChain(llm=llm, prompt=PROMPT_TEMPLATE)
    try:
        answer = chain.run(history=history_text, user_text=user_text)
        print(f"[LLM RAW ANSWER] {answer}")
        # Clean the answer to extract only JSON
        answer = answer.strip()
        if answer.startswith("→"):
            answer = answer[1:].strip()
        if answer.startswith("→"):
            answer = answer[1:].strip()
        
        parsed = json.loads(answer)
        print(f"[LLM PARSED] {parsed}")
    except Exception as e:
        print(f"[LLM PARSE ERROR] {e}")
        # Fallback parsing for common patterns
        parsed = fallback_parsing(user_text, history)
    
    return parsed

def fallback_parsing(user_text: str, history: Optional[list[str]] = None) -> dict:
    """Fallback parsing when LLM fails"""
    text = user_text.lower().strip()
    
    # Simple pattern matching
    cities = []
    date_patterns = []
    transfers = "any"
    
    # Extract cities (simple approach)
    words = text.split()
    for word in words:
        if len(word) > 2 and word.isalpha():
            cities.append(word)
    
    # Check for transfer preferences
    if "без пересадок" in text or "прямой" in text:
        transfers = 0
    
    # Check for date patterns
    if "завтра" in text:
        from datetime import datetime, timedelta
        tomorrow = datetime.now() + timedelta(days=1)
        date_patterns = [tomorrow.strftime("%Y-%m-%d")]
    elif "сегодня" in text:
        from datetime import datetime
        today = datetime.now()
        date_patterns = [today.strftime("%Y-%m-%d")]
    
    # Determine from/to based on context
    from_city = "any"
    to_city = "any"
    
    if len(cities) >= 2:
        from_city = cities[0]
        to_city = cities[1]
    elif len(cities) == 1:
        to_city = cities[0]
    
    need_clarify = []
    if from_city == "any":
        need_clarify.append("from")
    if to_city == "any":
        need_clarify.append("to")
    if not date_patterns:
        need_clarify.append("date")
    
    return {
        "from": from_city,
        "to": to_city,
        "date": date_patterns[0] if date_patterns else "any",
        "transfers": transfers,
        "need_clarify": need_clarify
    }

# Пример использования:
# import asyncio
# print(asyncio.run(extract_flight_query("есть ли билеты в Бали завтра?")))
