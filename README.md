# 🛫 FlyTracker Bot

Telegram бот для отслеживания цен на авиабилеты с уведомлениями о снижении цен.

## 🚀 Быстрый запуск

### Автоматическая установка (Рекомендуется)

```bash
# Полная автоматическая установка
curl -fsSL https://raw.githubusercontent.com/your-username/flytracker-bot/main/install.sh | bash -s -- \
  -r https://github.com/your-username/flytracker-bot.git \
  -t 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz \
  -a your_aviasales_token \
  -d flytracker.duckdns.org \
  --auto

# Или интерактивная установка
curl -fsSL https://raw.githubusercontent.com/your-username/flytracker-bot/main/install.sh | bash
```

### Настройка стабильного URL (DuckDNS)

```bash
# Настройте бесплатный домен
./setup-duckdns.sh -s flytracker -t your-duckdns-token
```

### Ручная установка в Docker

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd fastapi-template

# Настройте переменные окружения
cp env.example .env
# Отредактируйте .env: добавьте TELEGRAM_TOKEN и AVIASALES_TOKEN

# Запустите
./docker-start.sh
```

**📖 Подробные инструкции по деплою: [DEPLOY.md](DEPLOY.md)**

## 🐳 Docker Compose

```bash
# Запуск
docker-compose up -d

# Логи
docker-compose logs -f app

# Остановка
docker-compose down
```

## 🔧 Локальная разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск Redis
redis-server

# Запуск приложения
export PYTHONPATH=$(pwd)
python src/main.py
```

## 📋 Функциональность

- 🔍 Поиск авиабилетов через Aviasales API
- 📊 Отслеживание цен на выбранные рейсы
- 🔔 Уведомления о снижении цен
- 📱 Удобный Telegram интерфейс
- 🗑️ Управление подписками

### Команды бота:
- `/start` - начало работы
- `/help` - справка
- `/track` - отслеживание рейса
- `/my_flights` - мои подписки
- `/unsubscribe` - отписаться от всех рейсов

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   FastAPI App   │    │   PostgreSQL    │
│                 │◄──►│                 │◄──►│                 │
│   Webhook       │    │   Scheduler     │    │   Subscriptions │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Redis       │
                       │   Cache/Session │
                       └─────────────────┘
```

## 📊 Мониторинг

```bash
# Health check
curl http://localhost/health

# Логи
docker-compose logs -f app
```

## 🛠️ Разработка

### Структура проекта:
```
src/
├── core/           # Основная логика бота
├── services/       # Сервисы (БД, кэш, API)
├── utils/          # Утилиты
└── main.py         # Точка входа

docker/             # Docker конфигурации
scripts/            # Скрипты развертывания
tests/              # Тесты
```

### Тестирование:
```bash
# Тесты
python -m pytest tests/

# Тесты производительности
python performance_test.py
```

## 📞 Поддержка

При проблемах:
1. Проверьте логи: `docker-compose logs -f app`
2. Убедитесь, что все переменные окружения установлены
3. Проверьте health check: `curl http://localhost/health`

## 📄 Лицензия

MIT License
