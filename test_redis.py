
import redis
import os
import sys

try:
    r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    r.ping()
    print("Redis is RUNNING")
except Exception as e:
    print(f"Redis is DOWN: {e}")
