from src.services.redis_client import redis_client
import json

MEMORY_TTL = 60 * 60 * 24  # 1 день

# Сохраняет новое сообщение в историю диалога пользователя (ограничение k)
def save_message_to_memory(chat_id: int, message: str, k: int = 10):
    key = f"dialog:{chat_id}"
    redis_client.lpush(key, message)
    redis_client.ltrim(key, 0, k - 1)
    redis_client.expire(key, MEMORY_TTL)

# Получает последние k сообщений пользователя
def get_memory(chat_id: int, k: int = 10):
    key = f"dialog:{chat_id}"
    messages = redis_client.lrange(key, 0, k - 1)
    if isinstance(messages, list):
        return list(reversed(messages))
    return messages
