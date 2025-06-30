#!/bin/bash

# 🦆 Автоматическая настройка DuckDNS для FlyTracker Bot

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    echo "🦆 Настройка DuckDNS для FlyTracker Bot"
    echo "====================================="
    echo
    echo "Использование:"
    echo "  $0 [опции]"
    echo
    echo "Опции:"
    echo "  -s, --subdomain NAME  Имя поддомена (например: flytracker)"
    echo "  -t, --token TOKEN     DuckDNS токен"
    echo "  -h, --help            Показать эту справку"
    echo
    echo "Пример:"
    echo "  $0 -s flytracker -t your-duckdns-token"
    echo
    echo "Как получить токен:"
    echo "  1. Зайдите на https://www.duckdns.org/"
    echo "  2. Войдите через GitHub/Google"
    echo "  3. Создайте поддомен"
    echo "  4. Скопируйте токен"
}

# Параметры
SUBDOMAIN=""
TOKEN=""

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--subdomain)
            SUBDOMAIN="$2"
            shift 2
            ;;
        -t|--token)
            TOKEN="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Неизвестная опция: $1"
            show_help
            exit 1
            ;;
    esac
done

# Проверка параметров
if [ -z "$SUBDOMAIN" ] || [ -z "$TOKEN" ]; then
    log_error "Необходимо указать поддомен и токен"
    show_help
    exit 1
fi

# Создание домена
DOMAIN="${SUBDOMAIN}.duckdns.org"

log_info "Настройка DuckDNS домена: $DOMAIN"

# Проверка доступности домена
log_info "Проверка доступности домена..."
response=$(curl -s "https://www.duckdns.org/update?domains=$SUBDOMAIN&token=$TOKEN&ip=")

if echo "$response" | grep -q "OK"; then
    log_success "Домен $DOMAIN доступен"
else
    log_error "Ошибка при проверке домена: $response"
    exit 1
fi

# Установка cron для автоматического обновления IP
log_info "Настройка автоматического обновления IP..."

# Создаем скрипт обновления
cat > ~/update-duckdns.sh << EOF
#!/bin/bash
# Автоматическое обновление IP для DuckDNS
curl -s "https://www.duckdns.org/update?domains=$SUBDOMAIN&token=$TOKEN&ip=" > /dev/null
EOF

chmod +x ~/update-duckdns.sh

# Добавляем в crontab (каждые 5 минут)
(crontab -l 2>/dev/null; echo "*/5 * * * * ~/update-duckdns.sh") | crontab -

log_success "Cron настроен для обновления IP каждые 5 минут"

# Обновляем .env файл если он существует
if [ -f ".env" ]; then
    log_info "Обновление .env файла..."
    sed -i "s/DOMAIN=.*/DOMAIN=$DOMAIN/" .env
    log_success ".env файл обновлен"
fi

# Показываем результат
echo
log_success "🎉 DuckDNS настроен успешно!"
echo
echo "📋 Информация:"
echo "   🌐 Домен: $DOMAIN"
echo "   🔗 Webhook URL: http://$DOMAIN/tg/webhook"
echo "   ⏰ Обновление IP: каждые 5 минут"
echo
echo "📋 Следующие шаги:"
echo "   1. Обновите .env файл: DOMAIN=$DOMAIN"
echo "   2. Перезапустите приложение: docker-compose restart app"
echo "   3. Установите webhook:"
echo "      curl -X POST \"https://api.telegram.org/bot<TOKEN>/setWebhook\" \\"
echo "           -H \"Content-Type: application/json\" \\"
echo "           -d '{\"url\": \"http://$DOMAIN/tg/webhook\"}'"
echo
echo "🔧 Управление:"
echo "   ~/update-duckdns.sh    # Ручное обновление IP"
echo "   crontab -l             # Просмотр cron задач"
echo "   crontab -r             # Удаление всех cron задач" 