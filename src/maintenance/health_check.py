"""
Health check endpoint for DataPilot AI cleanup subsystem.

Verifies Redis connectivity, blob listing permissions, and last successful
cleaner run.
"""
import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from maintenance.utils import get_redis_client, list_blobs

logger = logging.getLogger(__name__)


def check_redis_connectivity() -> dict:
    """
    Check Redis connectivity.
    
    Returns:
        Status dict with 'ok' and optional 'error'
    """
    try:
        r = get_redis_client()
        r.ping()
        return {'ok': True, 'message': 'Redis connection successful'}
    except Exception as e:
        logger.error(f"Redis connectivity check failed: {e}")
        return {'ok': False, 'error': str(e)}


def check_blob_permissions() -> dict:
    """
    Check blob listing permissions.
    
    Returns:
        Status dict with 'ok' and optional 'error'
    """
    try:
        # Try to list blobs in uploads/ prefix
        blob_count = 0
        for _ in list_blobs('uploads/'):
            blob_count += 1
            if blob_count >= 5:  # Just check first few
                break
        
        return {
            'ok': True,
            'message': f'Blob listing successful (found {blob_count} blobs in sample)'
        }
    except Exception as e:
        logger.error(f"Blob permissions check failed: {e}")
        return {'ok': False, 'error': str(e)}


def get_last_cleaner_run() -> Optional[dict]:
    """
    Get information about the last successful cleaner run.
    
    Returns:
        Dict with last run info, or None if no runs found
    """
    try:
        # Determine audit path
        audit_base = os.getenv('CLEANER_AUDIT_BLOB_PATH', 'maintenance/cleaner_runs/')
        
        # Determine base storage directory
        base_dir = os.getenv('LOCAL_STORAGE_ROOT')
        if not base_dir:
            if os.name == 'nt':
                base_dir = os.path.join(os.getcwd(), 'tmp_uploads')
            else:
                base_dir = '/tmp/uploads'
        
        audit_dir = os.path.join(base_dir, audit_base.strip('/'))
        
        if not os.path.exists(audit_dir):
            return None
        
        # Find most recent audit file
        audit_files = sorted(
            [f for f in os.listdir(audit_dir) if f.startswith('cleaner_') and f.endswith('.json')],
            reverse=True
        )
        
        if not audit_files:
            return None
        
        # Read most recent file
        latest_file = os.path.join(audit_dir, audit_files[0])
        with open(latest_file, 'r') as f:
            audit_data = json.load(f)
        
        return {
            'lastRunFile': audit_files[0],
            'completedAt': audit_data.get('completedAt'),
            'deletedBlobs': audit_data.get('deletedBlobs', 0),
            'deletedKeys': audit_data.get('deletedKeys', 0),
            'errors': len(audit_data.get('errors', [])),
            'dryRun': audit_data.get('dryRun', True)
        }
        
    except Exception as e:
        logger.error(f"Failed to get last cleaner run: {e}")
        return None


def run_health_check() -> dict:
    """
    Run comprehensive health check.
    
    Returns:
        Health check status dictionary
    """
    logger.info("Running health check for cleanup subsystem")
    
    # Check Redis
    redis_status = check_redis_connectivity()
    
    # Check blob permissions
    blob_status = check_blob_permissions()
    
    # Get last run info
    last_run = get_last_cleaner_run()
    
    # Determine overall health
    overall_ok = redis_status['ok'] and blob_status['ok']
    
    result = {
        'status': 'healthy' if overall_ok else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'checks': {
            'redis': redis_status,
            'blobPermissions': blob_status
        },
        'lastCleanerRun': last_run
    }
    
    logger.info(f"Health check result: {result['status']}")
    return result


def main():
    """Main entry point for health check script."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run health check
    result = run_health_check()
    
    # Print JSON result
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result['status'] == 'healthy' else 1)


if __name__ == '__main__':
    main()
