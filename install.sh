#!/bin/bash

# 🚀 Автоматический установщик FlyTracker Bot
# Этот скрипт автоматически установит и настроит бота на сервере

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Параметры по умолчанию
REPO_URL=""
TELEGRAM_TOKEN=""
AVIASALES_TOKEN=""
DOMAIN=""
AUTO_MODE=false

# Функции для вывода
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

# Показать справку
show_help() {
    echo "🚀 Автоматический установщик FlyTracker Bot"
    echo "=========================================="
    echo
    echo "Использование:"
    echo "  $0 [опции]"
    echo
    echo "Опции:"
    echo "  -r, --repo URL        URL Git репозитория"
    echo "  -t, --telegram TOKEN  Telegram Bot Token"
    echo "  -a, --aviasales TOKEN Aviasales API Token"
    echo "  -d, --domain DOMAIN   Домен или IP сервера"
    echo "  --auto                Автоматический режим (без запросов)"
    echo "  -h, --help            Показать эту справку"
    echo
    echo "Примеры:"
    echo "  # Полная автоматическая установка"
    echo "  $0 -r https://github.com/user/flytracker-bot.git \\"
    echo "     -t 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz \\"
    echo "     -a your_aviasales_token \\"
    echo "     -d flytracker.duckdns.org --auto"
    echo
    echo "  # Интерактивная установка"
    echo "  $0 -r https://github.com/user/flytracker-bot.git"
    echo
    echo "  # Установка с IP адресом"
    echo "  $0 -r https://github.com/user/flytracker-bot.git \\"
    echo "     -t 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz \\"
    echo "     -a your_aviasales_token \\"
    echo "     -d 123.456.789.123 --auto"
}

# Парсинг аргументов командной строки
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -r|--repo)
                REPO_URL="$2"
                shift 2
                ;;
            -t|--telegram)
                TELEGRAM_TOKEN="$2"
                shift 2
                ;;
            -a|--aviasales)
                AVIASALES_TOKEN="$2"
                shift 2
                ;;
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            --auto)
                AUTO_MODE=true
                shift
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
}

# Проверка root прав
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "Не запускайте скрипт от root пользователя!"
        exit 1
    fi
}

# Определение ОС
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "Не удалось определить ОС"
        exit 1
    fi
    log_info "Обнаружена ОС: $OS $VER"
}

# Установка Docker
install_docker() {
    log_info "Установка Docker..."
    
    if command -v docker &> /dev/null; then
        log_success "Docker уже установлен"
        return
    fi
    
    case $OS in
        *"Ubuntu"*|*"Debian"*)
            sudo apt update
            sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt update
            sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        *"CentOS"*|*"Red Hat"*)
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        *)
            log_error "Неподдерживаемая ОС: $OS"
            exit 1
            ;;
    esac
    
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    
    log_success "Docker установлен"
}

# Установка Git
install_git() {
    log_info "Установка Git..."
    
    if command -v git &> /dev/null; then
        log_success "Git уже установлен"
        return
    fi
    
    case $OS in
        *"Ubuntu"*|*"Debian"*)
            sudo apt install -y git
            ;;
        *"CentOS"*|*"Red Hat"*)
            sudo yum install -y git
            ;;
    esac
    
    log_success "Git установлен"
}

# Клонирование проекта
clone_project() {
    log_info "Клонирование проекта..."
    
    if [ -z "$REPO_URL" ]; then
        if [ "$AUTO_MODE" = true ]; then
            log_error "URL репозитория не указан. Используйте -r или --repo"
            exit 1
        fi
        
        log_info "Введите URL вашего Git репозитория:"
        read -p "URL: " REPO_URL
    fi
    
    if [ -d "fastapi-template" ]; then
        log_warning "Директория fastapi-template уже существует"
        if [ "$AUTO_MODE" = true ]; then
            rm -rf fastapi-template
            log_info "Существующая директория удалена"
        else
            read -p "Удалить существующую директорию? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -rf fastapi-template
            else
                log_error "Установка прервана"
                exit 1
            fi
        fi
    fi
    
    git clone $REPO_URL fastapi-template
    cd fastapi-template
    
    log_success "Проект клонирован"
}

# Настройка переменных окружения
setup_env() {
    log_info "Настройка переменных окружения..."
    
    if [ -f ".env" ]; then
        log_warning "Файл .env уже существует"
        if [ "$AUTO_MODE" = true ]; then
            rm .env
            log_info "Существующий .env файл удален"
        else
            read -p "Перезаписать? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Пропускаем создание .env"
                return
            fi
        fi
    fi
    
    cp env.example .env
    
    # Telegram Bot Token
    if [ -z "$TELEGRAM_TOKEN" ]; then
        if [ "$AUTO_MODE" = true ]; then
            log_error "Telegram токен не указан. Используйте -t или --telegram"
            exit 1
        fi
        read -p "Telegram Bot Token (от @BotFather): " TELEGRAM_TOKEN
    fi
    sed -i "s/your_telegram_bot_token_here/$TELEGRAM_TOKEN/" .env
    
    # Aviasales Token
    if [ -z "$AVIASALES_TOKEN" ]; then
        if [ "$AUTO_MODE" = true ]; then
            log_error "Aviasales токен не указан. Используйте -a или --aviasales"
            exit 1
        fi
        read -p "Aviasales API Token (от travelpayouts.com): " AVIASALES_TOKEN
    fi
    sed -i "s/your_aviasales_token_here/$AVIASALES_TOKEN/" .env
    
    # Domain
    if [ -z "$DOMAIN" ]; then
        if [ "$AUTO_MODE" = true ]; then
            # Попробуем получить IP адрес
            DOMAIN=$(curl -s ifconfig.me)
            log_info "Автоматически определен IP адрес: $DOMAIN"
        else
            read -p "Домен или IP сервера: " DOMAIN
        fi
    fi
    sed -i "s/your-domain.com/$DOMAIN/" .env
    
    log_success "Переменные окружения настроены"
}

# Создание директорий
create_directories() {
    log_info "Создание необходимых директорий..."
    
    mkdir -p logs/nginx
    mkdir -p data
    
    log_success "Директории созданы"
}

# Запуск приложения
start_application() {
    log_info "Запуск приложения..."
    
    # Делаем скрипт исполняемым
    chmod +x docker-start.sh
    
    # Запускаем контейнеры
    ./docker-start.sh
    
    log_success "Приложение запущено"
}

# Настройка webhook
setup_webhook() {
    log_info "Настройка Telegram webhook..."
    
    # Читаем токен из .env
    TELEGRAM_TOKEN=$(grep TELEGRAM_TOKEN .env | cut -d '=' -f2)
    DOMAIN=$(grep DOMAIN .env | cut -d '=' -f2)
    
    if [ -z "$TELEGRAM_TOKEN" ] || [ -z "$DOMAIN" ]; then
        log_error "Не удалось получить токен или домен из .env"
        return
    fi
    
    # Ждем запуска приложения
    log_info "Ожидание запуска приложения..."
    sleep 15
    
    # Устанавливаем webhook
    WEBHOOK_URL="http://$DOMAIN/tg/webhook"
    log_info "Установка webhook: $WEBHOOK_URL"
    
    response=$(curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook" \
         -H "Content-Type: application/json" \
         -d "{\"url\": \"$WEBHOOK_URL\"}")
    
    if echo "$response" | grep -q '"ok":true'; then
        log_success "Webhook настроен успешно"
    else
        log_error "Ошибка настройки webhook: $response"
    fi
}

# Проверка работы
verify_installation() {
    log_info "Проверка установки..."
    
    # Проверяем статус контейнеров
    if docker-compose ps | grep -q "Up"; then
        log_success "Контейнеры запущены"
    else
        log_error "Контейнеры не запущены"
        return 1
    fi
    
    # Проверяем health check
    if curl -f http://localhost/health >/dev/null 2>&1; then
        log_success "Health check прошел"
    else
        log_error "Health check не прошел"
        return 1
    fi
    
    log_success "Установка завершена успешно!"
}

# Показ информации
show_info() {
    echo
    log_success "🎉 FlyTracker Bot успешно установлен!"
    echo
    echo "📋 Информация о установке:"
    echo "   🌐 Приложение: http://localhost"
    echo "   🏥 Health check: http://localhost/health"
    echo "   📁 Директория: $(pwd)"
    echo "   🔗 Webhook: http://$DOMAIN/tg/webhook"
    echo
    echo "📋 Полезные команды:"
    echo "   docker-compose ps                    # Статус контейнеров"
    echo "   docker-compose logs -f app           # Логи приложения"
    echo "   docker-compose restart app           # Перезапуск приложения"
    echo "   docker-compose down                  # Остановка"
    echo "   ./docker-start.sh                    # Запуск"
    echo
    echo "🔧 Управление:"
    echo "   nano .env                           # Редактирование настроек"
    echo "   docker-compose up -d                # Запуск в фоне"
    echo "   docker-compose down                 # Остановка"
    echo
    echo "📞 Поддержка:"
    echo "   docker-compose logs -f app          # Просмотр логов"
    echo "   curl http://localhost/health        # Проверка состояния"
}

# Главная функция
main() {
    echo "🚀 Автоматический установщик FlyTracker Bot"
    echo "=========================================="
    echo
    
    parse_args "$@"
    check_root
    detect_os
    install_docker
    install_git
    clone_project
    setup_env
    create_directories
    start_application
    setup_webhook
    verify_installation
    show_info
}

# Запуск
main "$@" 