# DataPilot AI - Data Retention Policy

## Overview

DataPilot AI implements an automated cleanup and retention system to manage temporary uploads, processing results, and job metadata. This ensures efficient storage usage, protects user privacy, and maintains system performance.

## Default Retention Policy

### Retention Period

- **Default TTL**: 24 hours (`JOB_TTL_HOURS=24`)
- **Minimum TTL**: 1 hour (configurable via `MIN_TTL_HOURS`)

All temporary data older than the configured TTL is automatically removed, including:

1. **Upload Files**: Files uploaded by users under `uploads/{jobId}/`
2. **Result Files**: Processing results under `results/{jobId}.json` and `results/{jobId}_error.json`
3. **Redis Job Keys**: Job metadata stored in Redis as `job:{jobId}`

### Why Temporary Retention?

1. **Privacy**: User data is automatically removed after processing
2. **Storage Cost**: Prevents unbounded storage growth
3. **Compliance**: Supports data minimization principles
4. **Performance**: Keeps the system lean and responsive

## Cleanup Schedule

The cleanup job runs automatically on a scheduled basis:

- **Default Schedule**: Daily at 03:00 UTC
- **Configurable**: Set `CLEANER_CRON_SCHEDULE` environment variable (cron format)

Example schedules:
```bash
# Daily at 3 AM UTC (default)
CLEANER_CRON_SCHEDULE="0 3 * * *"

# Every 6 hours
CLEANER_CRON_SCHEDULE="0 */6 * * *"

# Twice daily (3 AM and 3 PM UTC)
CLEANER_CRON_SCHEDULE="0 3,15 * * *"
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Retention Configuration
JOB_TTL_HOURS=24                              # How long to keep data
MIN_TTL_HOURS=1                               # Minimum allowed TTL (safety)
BLOB_PATH_PREFIXES="uploads/,results/"        # Paths to clean (safety)

# Cleanup Schedule
CLEANER_CRON_SCHEDULE="0 3 * * *"            # When to run (cron format)
CLEANER_DRY_RUN=true                          # Dry-run mode (safety)
CLEANER_LOG_LEVEL=INFO                        # Logging verbosity
CLEANER_MAX_DELETE_BATCH=500                  # Max items per run

# Audit Trail
CLEANER_AUDIT_BLOB_PATH="maintenance/cleaner_runs/"  # Audit log location
```

### Changing the Retention Period

To change how long data is kept:

1. Edit `.env` file:
   ```bash
   JOB_TTL_HOURS=48  # Keep data for 48 hours instead of 24
   ```

2. Restart the worker/scheduler:
   ```bash
   # Restart your application
   ```

**Note**: The minimum TTL is 1 hour by default. To allow shorter retention:

```bash
MIN_TTL_HOURS=0.5  # Allow 30-minute retention
JOB_TTL_HOURS=1    # Set 1-hour retention
```

### Changing the Cleanup Schedule

To change when cleanup runs:

1. Edit `.env` file:
   ```bash
   CLEANER_CRON_SCHEDULE="0 */12 * * *"  # Run every 12 hours
   ```

2. Update your scheduler configuration (platform-specific)

## Dry-Run Mode

### Safety First

By default, the cleaner runs in **dry-run mode** to prevent accidental data loss:

- **Dry-run**: Logs what *would* be deleted without actually deleting
- **Audit logs**: Created for every run showing what would happen

### Enabling Destructive Deletion

⚠️ **Warning**: This will permanently delete data!

To enable actual deletion:

1. Edit `.env` file:
   ```bash
   CLEANER_DRY_RUN=false
   ```

2. Restart the scheduler

3. Monitor the first few runs carefully via audit logs

**Best Practice**: Run in dry-run mode for at least 7 days to verify correct behavior before enabling destructive deletion.

## Audit Trail

### Audit Logs Location

Every cleanup run creates an audit log at:
```
{STORAGE_ROOT}/maintenance/cleaner_runs/cleaner_{timestamp}.json
```

Example: `tmp_uploads/maintenance/cleaner_runs/cleaner_20251206_030000.json`

### Audit Log Format

```json
{
  "runId": "cleaner_20251206_030000",
  "startedAt": "2025-12-06T03:00:00Z",
  "completedAt": "2025-12-06T03:00:15Z",
  "dryRun": true,
  "ttlHours": 24,
  "totalBlobsScanned": 150,
  "deletedBlobs": 45,
  "totalKeysScanned": 100,
  "deletedKeys": 30,
  "skipped": ["job:xyz (no timestamp)"],
  "errors": []
}
```

### Viewing Audit Logs

```bash
# List recent audit logs
ls tmp_uploads/maintenance/cleaner_runs/

# View latest audit log
cat tmp_uploads/maintenance/cleaner_runs/cleaner_*.json | tail -1 | python -m json.tool
```

## Manual Cleanup

### Running Cleanup Manually

You can run the cleanup process manually:

```bash
# Dry-run mode (safe)
python -m src.maintenance.cron_entry

# With custom TTL
JOB_TTL_HOURS=12 python -m src.maintenance.cron_entry

# Destructive mode (careful!)
CLEANER_DRY_RUN=false python -m src.maintenance.cron_entry
```

### Interactive Confirmation (Local Only)

For local testing with confirmation:

```bash
# This will prompt before deleting
python -c "
from src.maintenance.cleaner import run_cleaner
import sys

response = input('Delete old data? (yes/no): ')
if response.lower() == 'yes':
    result = run_cleaner(dry_run=False)
    print(f'Deleted {result[\"deletedBlobs\"]} blobs, {result[\"deletedKeys\"]} keys')
else:
    print('Cancelled')
"
```

## Health Monitoring

### Health Check Endpoint

Check the cleanup subsystem health:

```bash
python -m src.maintenance.health_check
```

Returns JSON status:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-06T12:00:00Z",
  "checks": {
    "redis": {"ok": true, "message": "Redis connection successful"},
    "blobPermissions": {"ok": true, "message": "Blob listing successful"}
  },
  "lastCleanerRun": {
    "lastRunFile": "cleaner_20251206_030000.json",
    "completedAt": "2025-12-06T03:00:15Z",
    "deletedBlobs": 45,
    "deletedKeys": 30,
    "errors": 0,
    "dryRun": true
  }
}
```

### Monitoring Recommendations

1. **Check health regularly**: Run health check in your monitoring system
2. **Alert on errors**: Set up alerts if `errors > 0` in audit logs
3. **Track deletion counts**: Monitor if deletion counts spike unexpectedly
4. **Verify dry-run status**: Ensure `dryRun` is set as expected

## Data Recovery

### Can Deleted Data Be Recovered?

**No.** Once the cleaner runs in destructive mode (`CLEANER_DRY_RUN=false`), deleted data **cannot be recovered**.

### Prevention Strategies

1. **Use dry-run mode**: Keep `CLEANER_DRY_RUN=true` until confident
2. **Longer TTL**: Increase `JOB_TTL_HOURS` to keep data longer
3. **Backup strategy**: Implement external backups if needed
4. **Monitor audit logs**: Review what's being deleted regularly

### If Data Is Accidentally Deleted

1. **Check audit logs**: Verify what was deleted and when
2. **User notification**: Inform affected users if necessary
3. **Adjust TTL**: Increase retention period to prevent future issues
4. **Review configuration**: Ensure `BLOB_PATH_PREFIXES` is correct

## Safety Features

The cleanup system includes multiple safety guardrails:

### 1. Dry-Run Default
- Defaults to `CLEANER_DRY_RUN=true`
- Must be explicitly disabled for deletion

### 2. Minimum TTL Enforcement
- Prevents TTL less than `MIN_TTL_HOURS`
- Fails fast with clear error message

### 3. Path Prefix Validation
- Requires `uploads/` and `results/` in `BLOB_PATH_PREFIXES`
- Prevents accidental deletion of wrong directories

### 4. Batch Limits
- Maximum `CLEANER_MAX_DELETE_BATCH` items per run
- Prevents runaway deletion

### 5. Error Isolation
- If one deletion fails, others continue
- All errors logged in audit trail

### 6. Idempotency
- Safe to run multiple times
- Already-deleted items are skipped

## Troubleshooting

### Cleaner Not Running

1. Check scheduler is active
2. Verify cron schedule syntax
3. Check logs for errors

### No Data Being Deleted

1. Verify `CLEANER_DRY_RUN=false` if you want actual deletion
2. Check TTL is appropriate (data must be older than TTL)
3. Review audit logs to see what's being scanned

### Too Much Data Being Deleted

1. Increase `JOB_TTL_HOURS`
2. Check system clock is correct (UTC)
3. Review audit logs for unexpected deletions

### Permission Errors

1. Check storage directory permissions
2. Verify Redis connection
3. Run health check: `python -m src.maintenance.health_check`

### Errors in Audit Logs

1. Review error details in audit JSON
2. Check Redis connectivity
3. Verify storage paths exist and are writable
4. Check for file system issues

## Testing

### Running Tests

```bash
# Create fake test data
python scripts/test_cleaner_create_fake_data.py

# Run full test suite
pwsh scripts/test_cleaner_run.sh

# Run edge case tests
pwsh scripts/test_cleaner_edgecases.sh
```

### Test Coverage

Tests verify:
- ✅ Dry-run doesn't delete data
- ✅ Destructive mode deletes old data
- ✅ Recent data is preserved
- ✅ Redis keys are cleaned correctly
- ✅ Audit logs are created
- ✅ TTL validation works
- ✅ Prefix validation works
- ✅ Batch limits are enforced
- ✅ Error handling continues processing

## Best Practices

1. **Start with dry-run**: Always test with `CLEANER_DRY_RUN=true` first
2. **Monitor audit logs**: Review logs regularly for the first week
3. **Set appropriate TTL**: Balance storage costs with user needs
4. **Schedule off-peak**: Run cleanup during low-traffic hours
5. **Alert on errors**: Set up monitoring for cleanup failures
6. **Document changes**: Keep track of TTL and schedule changes
7. **Test before production**: Use test scripts to validate behavior

## Support

For issues or questions about the retention policy:

1. Check audit logs for recent cleanup activity
2. Run health check to verify system status
3. Review this documentation
4. Check application logs for errors
5. Contact system administrators

---

**Last Updated**: 2025-12-06  
**Version**: 1.0
