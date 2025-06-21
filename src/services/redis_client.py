from redis import Redis
from dotenv import load_dotenv
import os, logging

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logging.info("✅ Redis connected %s", REDIS_URL)
except Exception as e:
    raise RuntimeError(f"Redis connection error: {e}")
