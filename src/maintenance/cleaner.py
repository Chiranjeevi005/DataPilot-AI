"""
Main cleanup script for DataPilot AI retention subsystem.

Automatically removes temporary uploads and result artifacts older than
a configurable TTL, along with corresponding Redis job keys.
"""
import os
import logging
import json
from typing import Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from .utils import (
    list_blobs,
    delete_blob,
    list_redis_job_keys,
    delete_redis_key,
    parse_job_timestamps,
    BlobMeta
)

logger = logging.getLogger(__name__)

# Configuration from environment
MIN_TTL_HOURS = int(os.getenv('MIN_TTL_HOURS', '1'))
CLEANER_MAX_DELETE_BATCH = int(os.getenv('CLEANER_MAX_DELETE_BATCH', '500'))
BLOB_PATH_PREFIXES = os.getenv('BLOB_PATH_PREFIXES', 'uploads/,results/').split(',')


class CleanupSummary:
    """Summary of cleanup operation."""
    
    def __init__(self):
        self.deleted_blobs = 0
        self.deleted_keys = 0
        self.skipped: List[str] = []
        self.errors: List[dict] = []
        self.dry_run = True
        self.started_at = datetime.utcnow().isoformat() + 'Z'
        self.completed_at = None
        self.ttl_hours = None
        self.total_blobs_scanned = 0
        self.total_keys_scanned = 0
    
    def to_dict(self) -> dict:
        """Convert summary to dictionary."""
        return {
            'deletedBlobs': self.deleted_blobs,
            'deletedKeys': self.deleted_keys,
            'skipped': self.skipped,
            'errors': self.errors,
            'dryRun': self.dry_run,
            'startedAt': self.started_at,
            'completedAt': self.completed_at,
            'ttlHours': self.ttl_hours,
            'totalBlobsScanned': self.total_blobs_scanned,
            'totalKeysScanned': self.total_keys_scanned
        }


def validate_configuration(older_than_hours: Optional[int]) -> int:
    """
    Validate cleanup configuration.
    
    Args:
        older_than_hours: TTL in hours, or None to use env var
        
    Returns:
        Validated TTL in hours
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Get TTL from parameter or environment
    if older_than_hours is not None:
        ttl_hours = older_than_hours
    else:
        ttl_hours = int(os.getenv('JOB_TTL_HOURS', '24'))
    
    # Validate minimum TTL
    if ttl_hours < MIN_TTL_HOURS:
        raise ValueError(
            f"TTL ({ttl_hours}h) is less than minimum allowed ({MIN_TTL_HOURS}h). "
            f"Set MIN_TTL_HOURS to override."
        )
    
    # Validate blob path prefixes
    required_prefixes = ['uploads/', 'results/']
    for required in required_prefixes:
        # Normalize prefixes for comparison
        normalized_prefixes = [p.strip().rstrip('/') + '/' for p in BLOB_PATH_PREFIXES]
        
        if required not in normalized_prefixes:
            raise ValueError(
                f"Required prefix '{required}' not found in BLOB_PATH_PREFIXES. "
                f"Current: {BLOB_PATH_PREFIXES}. This is a safety check to prevent "
                f"accidental deletion of wrong directories."
            )
    
    logger.info(f"Configuration validated: TTL={ttl_hours}h, prefixes={BLOB_PATH_PREFIXES}")
    return ttl_hours


def is_blob_old(blob: BlobMeta, cutoff_time: datetime) -> bool:
    """
    Check if a blob is older than the cutoff time.
    
    Args:
        blob: BlobMeta object
        cutoff_time: Cutoff datetime
        
    Returns:
        True if blob should be deleted
    """
    return blob.last_modified < cutoff_time


def cleanup_blobs(
    prefixes: List[str],
    cutoff_time: datetime,
    dry_run: bool,
    summary: CleanupSummary
) -> None:
    """
    Clean up blobs older than cutoff time.
    
    Args:
        prefixes: List of path prefixes to clean
        cutoff_time: Delete blobs older than this
        dry_run: If True, don't actually delete
        summary: CleanupSummary to update
    """
    logger.info(f"Cleaning up blobs with prefixes: {prefixes}")
    
    for prefix in prefixes:
        prefix = prefix.strip()
        if not prefix:
            continue
        
        logger.info(f"Scanning prefix: {prefix}")
        
        try:
            blobs_to_delete = []
            
            # List all blobs under this prefix
            for blob in list_blobs(prefix):
                summary.total_blobs_scanned += 1
                
                if is_blob_old(blob, cutoff_time):
                    blobs_to_delete.append(blob)
                    
                    # Respect batch limit
                    if len(blobs_to_delete) >= CLEANER_MAX_DELETE_BATCH:
                        logger.warning(
                            f"Reached batch limit ({CLEANER_MAX_DELETE_BATCH}). "
                            f"Remaining blobs will be cleaned in next run."
                        )
                        break
            
            logger.info(
                f"Found {len(blobs_to_delete)} blobs to delete under {prefix} "
                f"(scanned {summary.total_blobs_scanned} total)"
            )
            
            # Delete blobs
            for blob in blobs_to_delete:
                if dry_run:
                    logger.info(f"[DRY RUN] Would delete blob: {blob.path}")
                    summary.deleted_blobs += 1
                else:
                    success = delete_blob(blob.path)
                    
                    if success:
                        summary.deleted_blobs += 1
                    else:
                        summary.errors.append({
                            'type': 'blob_deletion_failed',
                            'path': blob.path,
                            'message': 'Failed to delete blob after retries'
                        })
                        
        except Exception as e:
            logger.error(f"Error cleaning prefix {prefix}: {e}")
            summary.errors.append({
                'type': 'blob_scan_failed',
                'prefix': prefix,
                'message': str(e)
            })


def cleanup_redis_keys(
    cutoff_time: datetime,
    dry_run: bool,
    summary: CleanupSummary
) -> None:
    """
    Clean up Redis job keys older than cutoff time.
    
    Args:
        cutoff_time: Delete keys older than this
        dry_run: If True, don't actually delete
        summary: CleanupSummary to update
    """
    logger.info("Cleaning up Redis job keys")
    
    try:
        keys_to_delete = []
        
        # List all job keys
        for job_id, job_data in list_redis_job_keys('job:*'):
            summary.total_keys_scanned += 1
            
            # Parse timestamp
            timestamp = parse_job_timestamps(job_data)
            
            if timestamp is None:
                logger.warning(f"Job {job_id} has no valid timestamp, skipping")
                summary.skipped.append(f"job:{job_id} (no timestamp)")
                continue
            
            # Check if old enough
            if timestamp < cutoff_time:
                keys_to_delete.append(f"job:{job_id}")
                
                # Respect batch limit
                if len(keys_to_delete) >= CLEANER_MAX_DELETE_BATCH:
                    logger.warning(
                        f"Reached batch limit ({CLEANER_MAX_DELETE_BATCH}). "
                        f"Remaining keys will be cleaned in next run."
                    )
                    break
        
        logger.info(
            f"Found {len(keys_to_delete)} Redis keys to delete "
            f"(scanned {summary.total_keys_scanned} total)"
        )
        
        # Delete keys
        for key in keys_to_delete:
            if dry_run:
                logger.info(f"[DRY RUN] Would delete Redis key: {key}")
                summary.deleted_keys += 1
            else:
                success = delete_redis_key(key)
                
                if success:
                    summary.deleted_keys += 1
                else:
                    summary.errors.append({
                        'type': 'redis_deletion_failed',
                        'key': key,
                        'message': 'Failed to delete Redis key after retries'
                    })
                    
    except Exception as e:
        logger.error(f"Error cleaning Redis keys: {e}")
        summary.errors.append({
            'type': 'redis_scan_failed',
            'message': str(e)
        })


def run_cleaner(
    dry_run: bool = True,
    older_than_hours: Optional[int] = None
) -> dict:
    """
    Run the cleanup process.
    
    Args:
        dry_run: If True, only simulate deletions without actually deleting
        older_than_hours: Delete objects older than this many hours.
                         If None, uses JOB_TTL_HOURS from env.
    
    Returns:
        Dictionary with cleanup summary:
        {
            "deletedBlobs": N,
            "deletedKeys": M,
            "skipped": [...],
            "errors": [...],
            "dryRun": true/false,
            "startedAt": "...",
            "completedAt": "...",
            "ttlHours": N
        }
    """
    summary = CleanupSummary()
    summary.dry_run = dry_run
    
    try:
        # Validate configuration
        ttl_hours = validate_configuration(older_than_hours)
        summary.ttl_hours = ttl_hours
        
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=ttl_hours)
        
        logger.info(
            f"Starting cleanup (dry_run={dry_run}, TTL={ttl_hours}h, "
            f"cutoff={cutoff_time.isoformat()})"
        )
        
        # Clean up blobs
        cleanup_blobs(BLOB_PATH_PREFIXES, cutoff_time, dry_run, summary)
        
        # Clean up Redis keys
        cleanup_redis_keys(cutoff_time, dry_run, summary)
        
        # Mark completion
        summary.completed_at = datetime.utcnow().isoformat() + 'Z'
        
        logger.info(
            f"Cleanup completed: deleted {summary.deleted_blobs} blobs, "
            f"{summary.deleted_keys} Redis keys, {len(summary.errors)} errors"
        )
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        summary.errors.append({
            'type': 'cleanup_failed',
            'message': str(e)
        })
        summary.completed_at = datetime.utcnow().isoformat() + 'Z'
    
    return summary.to_dict()
