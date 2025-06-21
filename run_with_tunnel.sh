#!/bin/zsh
# Автоматический запуск LocalTunnel, FastAPI и обновление webhook Telegram

# === НАСТРОЙКИ ===
TELEGRAM_TOKEN="7312663176:AAFAj3-8r5D2fQsC8bqDzJqdXb1bBmtR1uQ"  # <-- ВСТАВЛЕН ВАШ ТОКЕН
PORT=8000
WEBHOOK_PATH="/tg/webhook"

# === ЗАПУСК LOCALSERVER ===
# Убиваем процесс, если порт занят
kill -9 $(lsof -ti :$PORT) 2>/dev/null

# Запускаем FastAPI сервер в фоне
uvicorn main:app --host 0.0.0.0 --port $PORT &
SERVER_PID=$!
sleep 2

echo "[INFO] FastAPI server запущен (PID $SERVER_PID) на порту $PORT"

# Запускаем LocalTunnel и получаем URL
LT_URL=$(lt --port $PORT | grep -oE 'https://[a-zA-Z0-9\-]+\.loca\.lt' | head -1 &)
sleep 5
LT_URL=$(ps aux | grep 'lt --port' | grep -oE 'https://[a-zA-Z0-9\-]+\.loca\.lt' | head -1)

if [[ -z "$LT_URL" ]]; then
  echo "[ERROR] Не удалось получить URL LocalTunnel."
  kill $SERVER_PID
  exit 1
fi

echo "[INFO] LocalTunnel URL: $LT_URL"

# Устанавливаем webhook Telegram
WEBHOOK_URL="$LT_URL$WEBHOOK_PATH"
SET_WEBHOOK_URL="https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook?url=$WEBHOOK_URL"

curl -s "$SET_WEBHOOK_URL"
echo "[INFO] Webhook Telegram установлен на: $WEBHOOK_URL"

echo "[INFO] Всё готово! Не закрывайте этот терминал, чтобы туннель и сервер работали."
wait $SERVER_PID
