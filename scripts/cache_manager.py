#!/usr/bin/env python3
"""
Скрипт для управления кэшем Redis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.flight_cache import flight_cache
from src.services.parse_cache import parse_cache
from src.services.redis_client import redis_client

def show_cache_stats():
    """Показывает статистику всех кэшей"""
    print("📊 Статистика кэшей Redis:")
    print("=" * 50)
    
    # Статистика кэша рейсов
    flight_stats = flight_cache.get_stats()
    print(f"✈️  Кэш рейсов:")
    print(f"   Записей: {flight_stats.get('total_entries', 0)}")
    print(f"   Размер: {flight_stats.get('total_size_bytes', 0)} байт")
    print(f"   TTL: {flight_stats.get('ttl_seconds', 0) // 3600} часов")
    
    # Статистика кэша парсинга
    parse_stats = parse_cache.get_stats()
    print(f"🔍 Кэш парсинга:")
    print(f"   Записей: {parse_stats.get('total_entries', 0)}")
    print(f"   Размер: {parse_stats.get('total_size_bytes', 0)} байт")
    print(f"   TTL: {parse_stats.get('ttl_seconds', 0) // 3600} часов")
    
    # Общая статистика Redis
    try:
        info = redis_client.info()
        print(f"💾 Redis общая статистика:")
        print(f"   Использовано памяти: {info.get('used_memory_human', 'N/A')}")
        print(f"   Подключений: {info.get('connected_clients', 'N/A')}")
        print(f"   Всего ключей: {info.get('db0', {}).get('keys', 'N/A')}")
    except Exception as e:
        print(f"❌ Ошибка получения статистики Redis: {e}")

def clear_flight_cache():
    """Очищает кэш рейсов"""
    print("🗑️  Очистка кэша рейсов...")
    success = flight_cache.clear_all()
    if success:
        print("✅ Кэш рейсов очищен")
    else:
        print("❌ Ошибка очистки кэша рейсов")

def clear_parse_cache():
    """Очищает кэш парсинга"""
    print("🗑️  Очистка кэша парсинга...")
    success = parse_cache.clear_all()
    if success:
        print("✅ Кэш парсинга очищен")
    else:
        print("❌ Ошибка очистки кэша парсинга")

def clear_all_caches():
    """Очищает все кэши"""
    print("🗑️  Очистка всех кэшей...")
    flight_success = flight_cache.clear_all()
    parse_success = parse_cache.clear_all()
    
    if flight_success and parse_success:
        print("✅ Все кэши очищены")
    else:
        print("❌ Ошибка очистки некоторых кэшей")

def show_redis_keys():
    """Показывает все ключи в Redis"""
    try:
        print("🔑 Ключи в Redis:")
        print("=" * 50)
        
        # Получаем все ключи
        all_keys = redis_client.keys("*")
        
        if not all_keys:
            print("📭 Redis пуст")
            return
        
        # Группируем по префиксам
        key_groups = {}
        for key in all_keys:
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            
            prefix = key.split(':')[0] if ':' in key else 'other'
            if prefix not in key_groups:
                key_groups[prefix] = []
            key_groups[prefix].append(key)
        
        # Выводим группы
        for prefix, keys in key_groups.items():
            print(f"📁 {prefix}: {len(keys)} ключей")
            for key in keys[:5]:  # Показываем первые 5
                print(f"   - {key}")
            if len(keys) > 5:
                print(f"   ... и еще {len(keys) - 5} ключей")
            print()
            
    except Exception as e:
        print(f"❌ Ошибка получения ключей: {e}")

def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python scripts/cache_manager.py stats     - Показать статистику")
        print("  python scripts/cache_manager.py keys      - Показать ключи Redis")
        print("  python scripts/cache_manager.py clear-flight  - Очистить кэш рейсов")
        print("  python scripts/cache_manager.py clear-parse   - Очистить кэш парсинга")
        print("  python scripts/cache_manager.py clear-all     - Очистить все кэши")
        return
    
    command = sys.argv[1]
    
    if command == "stats":
        show_cache_stats()
    elif command == "keys":
        show_redis_keys()
    elif command == "clear-flight":
        clear_flight_cache()
    elif command == "clear-parse":
        clear_parse_cache()
    elif command == "clear-all":
        clear_all_caches()
    else:
        print(f"❌ Неизвестная команда: {command}")

if __name__ == "__main__":
    main() 