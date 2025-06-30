FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание директорий для логов и данных
RUN mkdir -p /app/logs /app/data

# Создание пользователя для безопасности
RUN useradd -m -u 1000 flytracker && \
    chown -R flytracker:flytracker /app
USER flytracker

# Проверка здоровья приложения
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Открытие порта
EXPOSE 8000

# Запуск приложения
CMD ["python", "src/main.py"] 