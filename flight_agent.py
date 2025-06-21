# Удалены все импорты и функции, связанные с LLM, LangChain и Tool
# Оставлен только парсер фраз, если потребуется для интеграции с OpenAI API
import re
from datetime import datetime, timedelta

# Функция для парсинга естественных фраз

def parse_flight_query(text: str):
    """
    Примитивный парсер для выделения направления и даты из естественной фразы.
    """
    # Примеры: "есть ли билеты в Тбилиси завтра?", "проверь вылет в Бангкок на следующей неделе"
    to_city = None
    date = None
    # Поиск города назначения
    match = re.search(r'в ([А-Яа-яA-Za-z\- ]+)', text)
    if match:
        to_city = match.group(1).strip().split()[0]
    # Поиск даты
    if 'завтра' in text:
        date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    elif 'сегодня' in text:
        date = datetime.now().strftime('%Y-%m-%d')
    elif 'на следующей неделе' in text:
        date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    else:
        # Попробовать найти дату в формате дд.мм.гггг
        match = re.search(r'(\d{1,2}\.\d{1,2}\.\d{4})', text)
        if match:
            date = datetime.strptime(match.group(1), '%d.%m.%Y').strftime('%Y-%m-%d')
    return to_city, date

# Здесь будет интеграция с OpenAI API для агента
