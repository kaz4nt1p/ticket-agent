# 🚀 Деплой FlyTracker Bot

## Быстрый деплой

### 1. Автоматическая установка (Рекомендуется)
```bash
curl -fsSL https://raw.githubusercontent.com/your-username/flytracker-bot/main/install.sh | bash -s -- \
  -r https://github.com/your-username/flytracker-bot.git \
  -t YOUR_TELEGRAM_TOKEN \
  -a YOUR_AVIASALES_TOKEN \
  -d your-domain.duckdns.org \
  --auto
```

### 2. Настройка стабильного URL
```bash
# Получите бесплатный домен на duckdns.org
./setup-duckdns.sh -s your-subdomain -t YOUR_DUCKDNS_TOKEN
```

### 3. Ручная установка
```bash
git clone <repository-url>
cd fastapi-template
cp env.example .env
# Отредактируйте .env
./docker-start.sh
```

## Управление

```bash
# Запуск
docker-compose up -d

# Логи
docker-compose logs -f app

# Остановка
docker-compose down

# Обновление
git pull
docker-compose up -d --build
```

## Резервное копирование

```bash
# Создание бэкапа
./scripts/backup.sh

# Восстановление
./scripts/restore.sh backup_file.sql
```

## Мониторинг

```bash
# Проверка здоровья
curl http://localhost/health

# Управление кэшем
python scripts/cache_manager.py --clear
```

## Переменные окружения

Обязательные в `.env`:
- `TELEGRAM_TOKEN` - токен Telegram бота
- `AVIASALES_TOKEN` - токен API Aviasales
- `WEBHOOK_URL` - URL для webhook (автоматически настраивается) 