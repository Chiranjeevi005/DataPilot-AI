import os
import json
import logging
import redis
from datetime import datetime

logger = logging.getLogger(__name__)

def get_redis_client():
    """Create and return a Redis client with SSL support for Upstash."""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Upstash Redis requires SSL
    # Convert redis:// to rediss:// for SSL connection
    if 'upstash.io' in redis_url and redis_url.startswith('redis://'):
        redis_url = redis_url.replace('redis://', 'rediss://')
    
    try:
        # Create client with SSL support
        client = redis.from_url(
            redis_url,
            decode_responses=False,  # We handle decoding manually
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        # Test connection
        client.ping()
        return client
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise

def create_job_key(redis_client, job_id: str, data: dict):
    """
    Sets Redis key `job:{jobId}` with JSON content.
    """
    key = f"job:{job_id}"
    
    # Ensure createdAt is present
    if 'createdAt' not in data:
         data['createdAt'] = datetime.utcnow().isoformat() + "Z"

    if 'status' not in data:
        data['status'] = 'submitted'

    payload = json.dumps(data)
    redis_client.set(key, payload)
    
    # Optional TTL
    ttl_hours = os.getenv('JOB_TTL_HOURS')
    if ttl_hours:
        try:
            redis_client.expire(key, int(ttl_hours) * 3600)
        except ValueError:
            pass
            
    logger.info(f"Created job key {key} with status {data.get('status')}")

def enqueue_job(redis_client, job_payload: dict) -> bool:
    """
    Pushes job metadata to Redis list `data_jobs`.
    """
    try:
        queue_name = 'data_jobs'
        payload_str = json.dumps(job_payload)
        redis_client.rpush(queue_name, payload_str)
        logger.info(f"Enqueued job {job_payload.get('jobId')} to {queue_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to enqueue job {job_payload.get('jobId')}: {e}")
        return False
