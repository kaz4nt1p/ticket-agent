#!/bin/bash

# Скрипт для восстановления FlyTracker Bot

set -e

BACKUP_DIR="./backups"
BACKUP_DATE=${1:-latest}
TEMP_DIR="/tmp/flytracker_restore_$RANDOM"
mkdir -p "$TEMP_DIR"

if [ "$BACKUP_DATE" = "latest" ]; then
    BACKUP_DATE=$(ls -1 $BACKUP_DIR | grep redis_backup | sort | tail -n 1 | sed 's/redis_backup_\(.*\)\.rdb\.gz/\1/')
fi

echo "🔄 Восстановление FlyTracker Bot за $BACKUP_DATE"
echo "================================================"

# Восстановление Redis
echo "🔴 Восстановление Redis..."
REDIS_BACKUP="$BACKUP_DIR/redis_backup_$BACKUP_DATE.rdb.gz"
if [ -f "$REDIS_BACKUP" ]; then
    # Запуск Redis
    docker-compose up -d redis
    
    # Ожидание запуска Redis
    echo "⏳ Ожидание запуска Redis..."
    sleep 5
    
    # Восстановление данных
    gunzip -c "$REDIS_BACKUP" > /tmp/restore.rdb
    docker cp /tmp/restore.rdb flytracker_redis:/data/dump.rdb
    docker-compose restart redis
    rm /tmp/restore.rdb
    echo "✅ Redis восстановлен"
else
    echo "⚠️ Redis бэкап не найден"
fi

# Восстановление конфигурации
echo "⚙️ Восстановление конфигурации..."
CONFIG_BACKUP="$BACKUP_DIR/config_backup_$BACKUP_DATE.tar.gz"
if [ -f "$CONFIG_BACKUP" ]; then
    # Создание бэкапа текущей конфигурации
    echo "💾 Создание бэкапа текущей конфигурации..."
    tar -czf "config_backup_before_restore_$(date +%Y%m%d_%H%M%S).tar.gz" \
        .env docker/ scripts/ requirements.txt pyproject.toml \
        --exclude='*.log' --exclude='*.pyc' --exclude='__pycache__' 2>/dev/null || true
    
    # Восстановление конфигурации
    tar -xzf "$CONFIG_BACKUP" -C .
    echo "✅ Конфигурация восстановлена"
else
    echo "⚠️ Конфигурационный бэкап не найден"
fi

# Очистка временных файлов
rm -rf "$TEMP_DIR"

# Запуск приложения
echo "🚀 Запуск приложения..."
docker-compose up -d

# Ожидание запуска
echo "⏳ Ожидание запуска сервисов..."
sleep 30

# Проверка восстановления
echo "🔍 Проверка восстановления..."

# Проверка Redis
if docker-compose exec redis redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis работает"
    KEY_COUNT=$(docker-compose exec -T redis redis-cli DBSIZE)
    echo "🔑 Ключей в Redis: $KEY_COUNT"
else
    echo "❌ Redis не отвечает"
fi

# Проверка приложения
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Приложение работает"
fi

echo ""
echo "🎉 Восстановление завершено!"
echo "================================================"
echo "📅 Восстановлено из бэкапа: $BACKUP_DATE"
echo "🕐 Время восстановления: $(date)"
echo ""
echo "💡 Следующие шаги:"
echo "   - Проверьте логи: docker-compose logs -f"
echo "   - Протестируйте бота"
echo "   - Настройте вебхук: docker-compose exec app python scripts/set_production_webhook.py"
echo ""
echo "⚠️  Если что-то пошло не так, используйте бэкап конфигурации:"
echo "   config_backup_before_restore_*.tar.gz" 