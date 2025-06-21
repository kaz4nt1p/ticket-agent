import json
from redis_client import redis_client

CACHE_TTL = 60 * 30  # 30 минут

def make_flight_cache_key(origin: str, destination: str, date: str) -> str:
    return f"flight:{origin}:{destination}:{date}"

def get_flight_from_cache(origin: str, destination: str, date: str):
    key = make_flight_cache_key(origin, destination, date)
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def set_flight_to_cache(origin: str, destination: str, date: str, flights):
    key = make_flight_cache_key(origin, destination, date)
    redis_client.setex(key, CACHE_TTL, json.dumps(flights))
