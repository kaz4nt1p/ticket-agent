# Flight Tracker Bot

Telegram бот для поиска авиабилетов с использованием Aviasales API и OpenAI для обработки естественного языка.

## 🚀 Быстрый запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
Создайте файл `.env` в корне проекта:
```env
TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
AVIASALES_TOKEN=your_aviasales_token
REDIS_URL=redis://localhost:6379
```

### 3. Запуск сервера
```bash
# Автоматический запуск (рекомендуется)
./start_server.sh

# Или вручную:
python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Настройка webhook
```bash
python3 scripts/set_webhook.py https://flytrackerbot.loca.lt/tg/webhook
```

## 📁 Структура проекта

```
src/
├── core/           # Основная логика бота
│   ├── bot.py     # Telegram webhook handler
│   ├── openai_agent.py  # AI для парсинга запросов
│   ├── conversation_state.py  # Управление состоянием диалога
│   └── dialog_memory.py  # Память диалогов
├── services/       # Внешние сервисы
│   ├── aviasales_search.py  # Поиск билетов
│   ├── redis_client.py  # Redis клиент
│   └── extract_params.py  # Извлечение параметров
├── config/         # Конфигурация
│   └── llm_config.py  # Настройки OpenAI
└── main.py         # FastAPI приложение

scripts/            # Утилиты
├── set_webhook.py  # Настройка webhook
└── reset_webhook.py  # Сброс webhook

tests/              # Тесты
```

## 🤖 Использование бота

Бот понимает естественный язык и может извлекать параметры поиска из текста:

### Примеры запросов:
- `Москва Нячанг 25.07.2025`
- `Из Москвы в Бангкок в июле`
- `Билеты Москва - Санкт-Петербург на завтра`
- `Поиск рейсов Москва Челябинск без пересадок`

### Параметры поиска:
- **Откуда** (`from`): город отправления
- **Куда** (`to`): город назначения  
- **Дата** (`date`): дата вылета
- **Пересадки** (`transfers`): количество пересадок

## 🔧 Управление

### Просмотр статуса webhook:
```bash
python3 scripts/set_webhook.py
```

### Сброс webhook:
```bash
python3 scripts/reset_webhook.py
```

### Остановка сервера:
```bash
pkill -f uvicorn
pkill -f localtunnel
```

## 📊 API Endpoints

- `GET /` - Главная страница
- `POST /tg/webhook` - Telegram webhook
- `GET /docs` - Swagger документация
- `GET /health` - Проверка здоровья сервера

## 🧪 Тестирование

```bash
# Запуск тестов
python3 -m pytest tests/

# Тестирование AI агента
python3 tests/test_agent.py

# Тестирование состояния диалога
python3 tests/test_conversation.py
```

## 🔍 Отладка

Логи сервера показывают:
- Входящие сообщения от Telegram
- Состояние диалога
- Результаты парсинга AI
- Поиск билетов
- Ошибки и предупреждения

## 📝 Требования

- Python 3.9+
- Redis сервер
- Telegram Bot Token
- OpenAI API Key
- Aviasales API Token

## 🚨 Известные проблемы

- Предупреждения о LibreSSL (не критично)
- Deprecation warnings от LangChain (будет исправлено в будущих версиях)
