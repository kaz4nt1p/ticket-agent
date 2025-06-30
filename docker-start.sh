#!/bin/bash

# Скрипт для быстрого запуска FlyTracker Bot в Docker

echo "🚀 Запуск FlyTracker Bot в Docker..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Создайте файл .env на основе env.example:"
    echo "   cp env.example .env"
    echo "   # Затем отредактируйте .env и добавьте ваши токены"
    exit 1
fi

# Останавливаем существующие контейнеры
echo "🛑 Остановка существующих контейнеров..."
docker-compose down

# Создаем необходимые директории
echo "📁 Создание директорий..."
mkdir -p logs/nginx
mkdir -p data

# Запускаем контейнеры
echo "🐳 Запуск контейнеров..."
docker-compose up -d

# Ждем запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверяем статус
echo "🔍 Проверка статуса сервисов..."
docker-compose ps

# Проверяем health check
echo "🏥 Проверка health check..."
if curl -f http://localhost/health >/dev/null 2>&1; then
    echo "✅ Приложение запущено успешно!"
    echo "🌐 Доступно по адресу: http://localhost"
    echo "🏥 Health check: http://localhost/health"
else
    echo "❌ Health check не прошел. Проверьте логи:"
    echo "   docker-compose logs app"
fi

echo "📋 Полезные команды:"
echo "   docker-compose logs -f app    # Логи приложения"
echo "   docker-compose logs -f nginx  # Логи Nginx"
echo "   docker-compose down           # Остановка"
echo "   docker-compose restart app    # Перезапуск приложения" 