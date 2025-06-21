import json
import hashlib
from typing import Dict, Optional, Any
from src.services.redis_client import redis_client

class ParseCacheTool:
    """Кэш для результатов парсинга параметров в Redis"""
    
    CACHE_TTL = 60 * 60 * 24  # 24 часа
    CACHE_PREFIX = "parse_cache:"
    
    def __init__(self):
        self.name = "ParseCacheTool"
        self.description = "Кэширует результаты парсинга параметров в Redis."
    
    def _generate_key(self, query: str) -> str:
        """Генерирует ключ кэша на основе запроса"""
        hash_obj = hashlib.md5(query.encode('utf-8'))
        return f"{self.CACHE_PREFIX}{hash_obj.hexdigest()}"
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Получает кэшированные параметры"""
        try:
            key = self._generate_key(query)
            cached_data = redis_client.get(key)
            
            if cached_data:
                if isinstance(cached_data, bytes):
                    return json.loads(cached_data.decode('utf-8'))
                elif isinstance(cached_data, str):
                    return json.loads(cached_data)
            
            return None
        except Exception as e:
            print(f"[PARSE CACHE ERROR] Failed to get cached params: {e}")
            return None
    
    def save(self, query: str, params: Dict[str, Any]) -> bool:
        """Сохраняет параметры в кэш"""
        try:
            key = self._generate_key(query)
            params_json = json.dumps(params, ensure_ascii=False)
            
            redis_client.setex(key, self.CACHE_TTL, params_json)
            print(f"[PARSE CACHE] Saved params for query: {query[:30]}...")
            return True
        except Exception as e:
            print(f"[PARSE CACHE ERROR] Failed to save params: {e}")
            return False
    
    def clear(self, query: str) -> bool:
        """Очищает кэш для конкретного запроса"""
        try:
            key = self._generate_key(query)
            redis_client.delete(key)
            print(f"[PARSE CACHE] Cleared cache for query: {query[:30]}...")
            return True
        except Exception as e:
            print(f"[PARSE CACHE ERROR] Failed to clear cache: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Очищает весь кэш парсинга"""
        try:
            pattern = f"{self.CACHE_PREFIX}*"
            keys = redis_client.keys(pattern)
            
            if keys:
                redis_client.delete(*keys)
                print(f"[PARSE CACHE] Cleared {len(keys)} cached parse entries")
            else:
                print("[PARSE CACHE] No cached parse entries found")
            
            return True
        except Exception as e:
            print(f"[PARSE CACHE ERROR] Failed to clear all cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Получает статистику кэша"""
        try:
            pattern = f"{self.CACHE_PREFIX}*"
            keys = redis_client.keys(pattern)
            
            total_size = 0
            for key in keys:
                size = redis_client.memory_usage(key)
                if size:
                    total_size += size
            
            return {
                "total_entries": len(keys),
                "total_size_bytes": total_size,
                "cache_prefix": self.CACHE_PREFIX,
                "ttl_seconds": self.CACHE_TTL
            }
        except Exception as e:
            print(f"[PARSE CACHE ERROR] Failed to get stats: {e}")
            return {"error": str(e)}
    
    def __call__(self, query: str) -> Optional[Dict[str, Any]]:
        """Совместимость с интерфейсом агента"""
        return self.get(query)

# Глобальный экземпляр кэша
parse_cache = ParseCacheTool()
