"""
Scheduled job entry point for DataPilot AI cleanup subsystem.

This module is invoked by the Antigravity scheduler to run periodic cleanup.
"""
import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from maintenance.cleaner import run_cleaner

# Configure logging
LOG_LEVEL = os.getenv('CLEANER_LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def save_audit_log(summary: dict) -> None:
    """
    Save cleanup run summary to audit blob.
    
    Args:
        summary: Cleanup summary dictionary
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
        
        # Create audit directory
        audit_dir = os.path.join(base_dir, audit_base.strip('/'))
        os.makedirs(audit_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        audit_file = os.path.join(audit_dir, f'cleaner_{timestamp}.json')
        
        # Add run metadata
        audit_data = {
            'runId': f'cleaner_{timestamp}',
            **summary
        }
        
        # Write audit file
        with open(audit_file, 'w') as f:
            json.dump(audit_data, f, indent=2)
        
        logger.info(f"Saved audit log to {audit_file}")
        
    except Exception as e:
        logger.error(f"Failed to save audit log: {e}")


def main():
    """Main entry point for scheduled cleanup job."""
    logger.info("=" * 80)
    logger.info("DataPilot AI Cleanup Job Starting")
    logger.info("=" * 80)
    
    try:
        # Get configuration from environment
        dry_run_env = os.getenv('CLEANER_DRY_RUN', 'true').lower()
        dry_run = dry_run_env in ('true', '1', 'yes')
        
        # Safety check: default to dry-run for first 7 days unless explicitly disabled
        # This is implemented by checking if CLEANER_DRY_RUN is explicitly set to false
        if dry_run_env not in ('false', '0', 'no'):
            dry_run = True
            logger.warning(
                "Running in DRY RUN mode (default). "
                "Set CLEANER_DRY_RUN=false to enable destructive deletion."
            )
        
        # Run cleaner
        logger.info(f"Running cleaner (dry_run={dry_run})")
        summary = run_cleaner(dry_run=dry_run)
        
        # Log summary
        logger.info("Cleanup Summary:")
        logger.info(f"  Dry Run: {summary['dryRun']}")
        logger.info(f"  TTL Hours: {summary['ttlHours']}")
        logger.info(f"  Blobs Scanned: {summary['totalBlobsScanned']}")
        logger.info(f"  Blobs Deleted: {summary['deletedBlobs']}")
        logger.info(f"  Redis Keys Scanned: {summary['totalKeysScanned']}")
        logger.info(f"  Redis Keys Deleted: {summary['deletedKeys']}")
        logger.info(f"  Errors: {len(summary['errors'])}")
        
        if summary['errors']:
            logger.error("Errors encountered:")
            for error in summary['errors']:
                logger.error(f"  - {error}")
        
        # Save audit log
        save_audit_log(summary)
        
        # Log structured JSON summary for monitoring
        structured_log = {
            'runId': f"cleaner_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'startedAt': summary['startedAt'],
            'completedAt': summary['completedAt'],
            'deletedBlobs': summary['deletedBlobs'],
            'deletedKeys': summary['deletedKeys'],
            'errors': summary['errors'],
            'dryRun': summary['dryRun']
        }
        logger.info(f"STRUCTURED_SUMMARY: {json.dumps(structured_log)}")
        
        logger.info("=" * 80)
        logger.info("DataPilot AI Cleanup Job Completed Successfully")
        logger.info("=" * 80)
        
        # Exit with error code if there were errors
        if summary['errors']:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Cleanup job failed with exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
