import os
import json
import logging
import redis
from datetime import datetime

logger = logging.getLogger(__name__)

def get_redis_client():
    """Create and return a Redis client."""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Auto-upgrade to TLS for Upstash if scheme is redis://
    if 'upstash.io' in redis_url and redis_url.startswith('redis://'):
        redis_url = redis_url.replace('redis://', 'rediss://', 1)
        
    # For Upstash/Production, we might need to ignore cert warnings if using self-signed (unlikely for Upstash but safe)
    # But usually standard SSL verification works for Upstash.
    return redis.from_url(redis_url)

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
