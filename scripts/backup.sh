#!/bin/bash

# Скрипт для резервного копирования FlyTracker Bot

set -e

# Конфигурация
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

echo "🔄 Запуск резервного копирования FlyTracker Bot"
echo "================================================"

# Создание директории для бэкапов
mkdir -p "$BACKUP_DIR"

# Проверка, запущен ли Docker Compose
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Docker Compose не запущен. Запустите приложение: docker-compose up -d"
    exit 1
fi

echo "📦 Создание бэкапа от $DATE"

# Бэкап Redis
echo "🔴 Резервное копирование Redis..."
docker-compose exec redis redis-cli BGSAVE
sleep 5  # Ждём завершения сохранения
REDIS_BACKUP="$BACKUP_DIR/redis_backup_$DATE.rdb"
docker cp flytracker_redis:/data/dump.rdb "$REDIS_BACKUP"
gzip "$REDIS_BACKUP"
echo "✅ Redis бэкап создан: ${REDIS_BACKUP}.gz"

# Бэкап конфигурации
echo "⚙️ Резервное копирование конфигурации..."
CONFIG_BACKUP="$BACKUP_DIR/config_backup_$DATE.tar.gz"
tar -czf "$CONFIG_BACKUP" \
    .env \
    docker/ \
    scripts/ \
    requirements.txt \
    pyproject.toml \
    --exclude='*.log' \
    --exclude='*.pyc' \
    --exclude='__pycache__'
echo "✅ Конфигурация сохранена: $CONFIG_BACKUP"

# Создание архива всех бэкапов
echo "📦 Создание полного архива..."
FULL_BACKUP="$BACKUP_DIR/flytracker_full_backup_$DATE.tar.gz"
tar -czf "$FULL_BACKUP" \
    -C "$BACKUP_DIR" \
    "redis_backup_$DATE.rdb.gz" \
    "config_backup_$DATE.tar.gz"
echo "✅ Полный архив создан: $FULL_BACKUP"

# Очистка старых бэкапов
echo "🧹 Очистка старых бэкапов (старше $RETENTION_DAYS дней)..."
find "$BACKUP_DIR" -name "*.gz" -type f -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.sql" -type f -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.rdb" -type f -mtime +$RETENTION_DAYS -delete

# Статистика
echo ""
echo "📊 Статистика бэкапа:"
echo "================================================"
echo "📁 Директория бэкапов: $BACKUP_DIR"
echo "🔴 Redis: $(ls -lh ${REDIS_BACKUP}.gz | awk '{print $5}')"
echo "⚙️ Конфигурация: $(ls -lh $CONFIG_BACKUP | awk '{print $5}')"
echo "📦 Полный архив: $(ls -lh $FULL_BACKUP | awk '{print $5}')"
echo ""
echo "🗂️ Всего файлов в директории: $(ls $BACKUP_DIR | wc -l)"
echo "💾 Общий размер: $(du -sh $BACKUP_DIR | awk '{print $1}')"

# Проверка целостности бэкапов
echo ""
echo "🔍 Проверка целостности бэкапов..."

# Проверка Redis бэкапа
if gunzip -t "${REDIS_BACKUP}.gz" 2>/dev/null; then
    echo "✅ Redis бэкап корректен"
else
    echo "❌ Redis бэкап повреждён"
fi

# Проверка полного архива
if tar -tzf "$FULL_BACKUP" >/dev/null 2>&1; then
    echo "✅ Полный архив корректен"
else
    echo "❌ Полный архив повреждён"
fi

echo ""
echo "🎉 Резервное копирование завершено успешно!"
echo "================================================"
echo "📅 Следующий бэкап будет создан автоматически"
echo "🗑️ Старые бэкапы (старше $RETENTION_DAYS дней) удалены"
echo ""
echo "💡 Полезные команды:"
echo "   - Восстановление: ./scripts/restore.sh $DATE"
echo "   - Просмотр бэкапов: ls -la $BACKUP_DIR"
echo "   - Мониторинг места: df -h $BACKUP_DIR" 