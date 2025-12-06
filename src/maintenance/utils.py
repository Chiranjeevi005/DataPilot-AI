"""
Utility functions for blob and Redis operations in the cleanup subsystem.

Provides helpers for listing and deleting blobs and Redis keys with retry logic.
"""
import os
import logging
import json
from typing import Iterator, Tuple, Optional, NamedTuple
from datetime import datetime
from pathlib import Path
import redis

# Import retry utilities from existing lib
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class BlobMeta(NamedTuple):
    """Metadata for a blob object."""
    filename: str
    path: str
    last_modified: datetime
    size: int


def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    return redis.from_url(redis_url, decode_responses=True)


def list_blobs(prefix: str) -> Iterator[BlobMeta]:
    """
    List blobs under the given prefix.
    
    Since we're using local file storage (not actual blob storage),
    this scans the local storage directory.
    
    Args:
        prefix: Path prefix (e.g., 'uploads/', 'results/')
        
    Yields:
        BlobMeta objects for each file found
    """
    # Determine base storage directory
    base_dir = os.getenv('LOCAL_STORAGE_ROOT')
    if not base_dir:
        if os.name == 'nt':
            base_dir = os.path.join(os.getcwd(), 'tmp_uploads')
        else:
            base_dir = '/tmp/uploads'
    
    # Construct full search path
    search_path = os.path.join(base_dir, prefix.rstrip('/'))
    
    logger.info(f"Listing blobs under prefix '{prefix}' at {search_path}")
    
    if not os.path.exists(search_path):
        logger.warning(f"Path does not exist: {search_path}")
        return
    
    # Walk directory tree
    for root, dirs, files in os.walk(search_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            
            try:
                stat = os.stat(file_path)
                last_modified = datetime.fromtimestamp(stat.st_mtime)
                size = stat.st_size
                
                # Get relative path from base_dir
                rel_path = os.path.relpath(file_path, base_dir)
                
                yield BlobMeta(
                    filename=filename,
                    path=rel_path,
                    last_modified=last_modified,
                    size=size
                )
            except (OSError, IOError) as e:
                logger.warning(f"Failed to stat file {file_path}: {e}")
                continue


def delete_blob(path: str) -> bool:
    """
    Delete a blob at the given path.
    
    Args:
        path: Relative path from storage root
        
    Returns:
        True if deletion succeeded, False otherwise
    """
    # Determine base storage directory
    base_dir = os.getenv('LOCAL_STORAGE_ROOT')
    if not base_dir:
        if os.name == 'nt':
            base_dir = os.path.join(os.getcwd(), 'tmp_uploads')
        else:
            base_dir = '/tmp/uploads'
    
    full_path = os.path.join(base_dir, path)
    
    def _delete_operation():
        """Inner function for retry wrapper."""
        if not os.path.exists(full_path):
            logger.info(f"Blob already deleted or doesn't exist: {path}")
            return True
        
        os.remove(full_path)
        logger.info(f"Deleted blob: {path}")
        return True
    
    try:
        return retry_with_backoff(
            _delete_operation,
            attempts=3,
            initial_delay=0.5,
            factor=2.0,
            max_delay=10.0,
            retry_exceptions=(IOError, OSError, PermissionError),
            operation_name=f"Delete blob {path}"
        )
    except Exception as e:
        logger.error(f"Failed to delete blob {path} after retries: {e}")
        return False


def list_redis_job_keys(pattern: str = 'job:*') -> Iterator[Tuple[str, dict]]:
    """
    List Redis job keys matching the pattern.
    
    Args:
        pattern: Redis key pattern (default: 'job:*')
        
    Yields:
        Tuples of (jobId, jobJson dict)
    """
    try:
        r = get_redis_client()
        
        # Scan for keys matching pattern
        for key in r.scan_iter(match=pattern, count=100):
            try:
                # Get the job data
                job_data_str = r.get(key)
                
                if not job_data_str:
                    logger.warning(f"Key {key} exists but has no value")
                    continue
                
                # Parse JSON
                job_data = json.loads(job_data_str)
                
                # Extract jobId from key (format: job:{jobId})
                job_id = key.split(':', 1)[1] if ':' in key else key
                
                yield (job_id, job_data)
                
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to parse job data for key {key}: {e}")
                continue
                
    except redis.RedisError as e:
        logger.error(f"Redis error while listing keys: {e}")
        raise


def delete_redis_key(key: str) -> bool:
    """
    Delete a Redis key.
    
    Args:
        key: Redis key to delete
        
    Returns:
        True if deletion succeeded, False otherwise
    """
    def _delete_operation():
        """Inner function for retry wrapper."""
        r = get_redis_client()
        result = r.delete(key)
        
        if result == 0:
            logger.info(f"Redis key already deleted or doesn't exist: {key}")
        else:
            logger.info(f"Deleted Redis key: {key}")
        
        return True
    
    try:
        return retry_with_backoff(
            _delete_operation,
            attempts=3,
            initial_delay=0.5,
            factor=2.0,
            max_delay=10.0,
            retry_exceptions=(redis.RedisError, ConnectionError),
            operation_name=f"Delete Redis key {key}"
        )
    except Exception as e:
        logger.error(f"Failed to delete Redis key {key} after retries: {e}")
        return False


def parse_job_timestamps(job_json: dict) -> Optional[datetime]:
    """
    Parse job timestamps from job JSON data.
    
    Prefers updatedAt, falls back to createdAt.
    
    Args:
        job_json: Job data dictionary
        
    Returns:
        datetime object or None if no valid timestamp found
    """
    # Try updatedAt first
    timestamp_str = job_json.get('updatedAt') or job_json.get('createdAt')
    
    if not timestamp_str:
        return None
    
    try:
        # Handle ISO format with or without 'Z' suffix
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1]
        
        # Parse ISO format
        return datetime.fromisoformat(timestamp_str)
        
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
        return None
