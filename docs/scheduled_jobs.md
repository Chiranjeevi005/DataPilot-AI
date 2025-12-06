# DataPilot AI - Scheduled Jobs Configuration

## Cleanup Job

This configuration defines the scheduled cleanup job for DataPilot AI.

### Job Configuration

**Job Name**: `datapilot-cleanup`

**Schedule**: Daily at 03:00 UTC (configurable via `CLEANER_CRON_SCHEDULE` env var)

**Command**: 
```bash
python -m src.maintenance.cron_entry
```

**Environment Variables Required**:
- `REDIS_URL` - Redis connection string
- `JOB_TTL_HOURS` - Retention period in hours (default: 24)
- `CLEANER_DRY_RUN` - Dry-run mode (default: true)
- `CLEANER_LOG_LEVEL` - Log level (default: INFO)
- `BLOB_PATH_PREFIXES` - Paths to clean (default: "uploads/,results/")
- `MIN_TTL_HOURS` - Minimum TTL (default: 1)
- `CLEANER_AUDIT_BLOB_PATH` - Audit log path (default: "maintenance/cleaner_runs/")
- `CLEANER_MAX_DELETE_BATCH` - Max deletions per run (default: 500)
- `LOCAL_STORAGE_ROOT` - Storage root directory (optional)

### IAM Permissions Required

The scheduled job service account needs:

1. **Blob Storage**:
   - List blobs under `uploads/` and `results/` prefixes
   - Delete blobs under `uploads/` and `results/` prefixes
   - Write to `maintenance/cleaner_runs/` for audit logs

2. **Redis**:
   - Read keys matching pattern `job:*`
   - Delete keys matching pattern `job:*`

### Platform-Specific Configuration

#### For Antigravity Platform

Add to your `antigravity.yaml` or platform configuration:

```yaml
scheduled_jobs:
  - name: datapilot-cleanup
    schedule: "0 3 * * *"  # Daily at 3 AM UTC
    command: python -m src.maintenance.cron_entry
    runtime: python3.11
    timeout: 600  # 10 minutes
    environment:
      REDIS_URL: ${REDIS_URL}
      JOB_TTL_HOURS: "24"
      CLEANER_DRY_RUN: "true"
      CLEANER_LOG_LEVEL: "INFO"
      BLOB_PATH_PREFIXES: "uploads/,results/"
      MIN_TTL_HOURS: "1"
      CLEANER_AUDIT_BLOB_PATH: "maintenance/cleaner_runs/"
      CLEANER_MAX_DELETE_BATCH: "500"
    permissions:
      blob:
        - list:uploads/*
        - delete:uploads/*
        - list:results/*
        - delete:results/*
        - write:maintenance/cleaner_runs/*
      redis:
        - read:job:*
        - delete:job:*
```

#### For Standard Cron (Linux/Mac)

Add to crontab:

```bash
# DataPilot AI Cleanup Job - Daily at 3 AM UTC
0 3 * * * cd /path/to/datapilot-ai && /path/to/python -m src.maintenance.cron_entry >> /var/log/datapilot-cleanup.log 2>&1
```

#### For Windows Task Scheduler

Create a scheduled task:

1. Open Task Scheduler
2. Create Basic Task
3. Name: "DataPilot AI Cleanup"
4. Trigger: Daily at 3:00 AM
5. Action: Start a program
   - Program: `python`
   - Arguments: `-m src.maintenance.cron_entry`
   - Start in: `C:\path\to\datapilot-ai`

#### For Docker/Kubernetes

Add to your deployment:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: datapilot-cleanup
spec:
  schedule: "0 3 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: datapilot-ai:latest
            command: ["python", "-m", "src.maintenance.cron_entry"]
            env:
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: datapilot-secrets
                  key: redis-url
            - name: JOB_TTL_HOURS
              value: "24"
            - name: CLEANER_DRY_RUN
              value: "true"
          restartPolicy: OnFailure
```

### Monitoring

#### Success Criteria

A successful cleanup run should:
- Exit with code 0
- Create an audit log file
- Log structured summary JSON
- Have `completedAt` timestamp in audit log

#### Failure Indicators

Monitor for:
- Non-zero exit code
- Missing audit log files
- Errors in audit log `errors` array
- Missing `completedAt` timestamp
- Health check failures

#### Alerting

Set up alerts for:
- Cleanup job failures (exit code != 0)
- High error count in audit logs (errors > 5)
- No cleanup run in last 48 hours
- Health check status != "healthy"

### Testing the Scheduled Job

Before enabling in production:

1. **Test manually**:
   ```bash
   python -m src.maintenance.cron_entry
   ```

2. **Verify dry-run mode**:
   - Check audit log shows `"dryRun": true`
   - Verify no data was actually deleted

3. **Run test suite**:
   ```bash
   pwsh scripts/test_cleaner_run.sh
   pwsh scripts/test_cleaner_edgecases.sh
   ```

4. **Monitor first production runs**:
   - Keep `CLEANER_DRY_RUN=true` for first week
   - Review audit logs daily
   - Verify deletion counts are as expected

5. **Enable destructive mode**:
   - Set `CLEANER_DRY_RUN=false`
   - Monitor closely for first few runs
   - Verify data is being deleted correctly

### Troubleshooting

#### Job Not Running

1. Check scheduler is active
2. Verify cron syntax
3. Check job logs
4. Verify permissions

#### Job Failing

1. Check exit code and error message
2. Review audit log for errors
3. Run health check
4. Verify environment variables
5. Check Redis connectivity
6. Verify storage permissions

#### Unexpected Deletions

1. Review audit logs
2. Check TTL configuration
3. Verify system clock is correct (UTC)
4. Ensure `BLOB_PATH_PREFIXES` is correct

### Maintenance

#### Regular Tasks

- Review audit logs weekly
- Monitor deletion counts for anomalies
- Verify health check status
- Check storage usage trends

#### When to Adjust

- **Increase TTL**: If users need data longer
- **Decrease TTL**: If storage costs are high
- **Change schedule**: If cleanup interferes with peak usage
- **Adjust batch size**: If cleanup takes too long

---

**Last Updated**: 2025-12-06  
**Version**: 1.0
