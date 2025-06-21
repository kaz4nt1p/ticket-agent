import json
import hashlib
from typing import Dict, List, Optional, Any
from src.services.redis_client import redis_client

# Примитивный кэш для результатов поиска рейсов (можно заменить на Redis)
class FlightCacheTool:
    """Кэш для результатов поиска рейсов в Redis"""
    
    CACHE_TTL = 60 * 60 * 2  # 2 часа
    CACHE_PREFIX = "flight_cache:"
    
    def __init__(self):
        self.name = "FlightCacheTool"
        self.description = "Кэширует результаты поиска рейсов в Redis."
    
    def _generate_key(self, params: Dict[str, Any]) -> str:
        """Генерирует ключ кэша на основе параметров поиска"""
        # Сортируем параметры для стабильного ключа
        sorted_params = sorted(params.items())
        params_str = json.dumps(sorted_params, sort_keys=True)
        hash_obj = hashlib.md5(params_str.encode())
        return f"{self.CACHE_PREFIX}{hash_obj.hexdigest()}"
    
    def get(self, params: Dict[str, Any]) -> Optional[List[Dict]]:
        """Получает кэшированные рейсы"""
        try:
            key = self._generate_key(params)
            cached_data = redis_client.get(key)
            
            if cached_data:
                if isinstance(cached_data, bytes):
                    return json.loads(cached_data.decode('utf-8'))
                elif isinstance(cached_data, str):
                    return json.loads(cached_data)
            
            return None
        except Exception as e:
            print(f"[CACHE ERROR] Failed to get cached flights: {e}")
            return None
    
    def save(self, params: Dict[str, Any], flights: List[Dict]) -> bool:
        """Сохраняет рейсы в кэш"""
        try:
            key = self._generate_key(params)
            flights_json = json.dumps(flights, ensure_ascii=False)
            
            redis_client.setex(key, self.CACHE_TTL, flights_json)
            print(f"[CACHE] Saved {len(flights)} flights for key: {key[:20]}...")
            return True
        except Exception as e:
            print(f"[CACHE ERROR] Failed to save flights: {e}")
            return False
    
    def clear(self, params: Dict[str, Any]) -> bool:
        """Очищает кэш для конкретных параметров"""
        try:
            key = self._generate_key(params)
            redis_client.delete(key)
            print(f"[CACHE] Cleared cache for key: {key[:20]}...")
            return True
        except Exception as e:
            print(f"[CACHE ERROR] Failed to clear cache: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Очищает весь кэш рейсов"""
        try:
            pattern = f"{self.CACHE_PREFIX}*"
            keys = redis_client.keys(pattern)
            
            if keys:
                redis_client.delete(*keys)
                print(f"[CACHE] Cleared {len(keys)} cached flight entries")
            else:
                print("[CACHE] No cached flights found")
            
            return True
        except Exception as e:
            print(f"[CACHE ERROR] Failed to clear all cache: {e}")
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
            print(f"[CACHE ERROR] Failed to get stats: {e}")
            return {"error": str(e)}
    
    def __call__(self, params: Dict[str, Any]) -> Optional[List[Dict]]:
        """Совместимость с интерфейсом агента"""
        return self.get(params)

# Глобальный экземпляр кэша
flight_cache = FlightCacheTool()
