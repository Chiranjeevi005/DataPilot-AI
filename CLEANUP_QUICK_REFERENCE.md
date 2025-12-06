# ✅ DataPilot AI - Cleanup/Retention Subsystem - Quick Reference

## 🎯 What It Does

Automatically removes temporary uploads, results, and Redis job keys older than a configurable TTL (default: 24 hours).

## 🚀 Quick Start

### 1. Test in Dry-Run Mode (Safe)

```bash
# Create test data
python scripts/test_cleaner_create_fake_data.py

# Run cleaner (won't actually delete)
python -m src.maintenance.cron_entry

# Check audit log
type tmp_uploads\maintenance\cleaner_runs\cleaner_*.json
```

### 2. Enable Destructive Mode (Careful!)

```bash
# Edit .env
CLEANER_DRY_RUN=false

# Run cleaner
python -m src.maintenance.cron_entry
```

### 3. Run Full Test Suite

```bash
# Run all tests
pwsh scripts/test_cleaner_run.sh
pwsh scripts/test_cleaner_edgecases.sh
```

## 📋 Configuration (.env)

```bash
# How long to keep data (hours)
JOB_TTL_HOURS=24

# Dry-run mode (true = safe, false = destructive)
CLEANER_DRY_RUN=true

# When to run (cron format)
CLEANER_CRON_SCHEDULE="0 3 * * *"

# Max items to delete per run
CLEANER_MAX_DELETE_BATCH=500

# Minimum allowed TTL (safety)
MIN_TTL_HOURS=1

# Paths to clean (safety)
BLOB_PATH_PREFIXES="uploads/,results/"
```

## 🔍 Health Check

```bash
python -m src.maintenance.health_check
```

Returns:
- ✅ Redis connectivity
- ✅ Blob permissions
- ✅ Last cleaner run status

## 📊 What Gets Cleaned

| Type | Path | Description |
|------|------|-------------|
| **Uploads** | `uploads/{jobId}/*` | User-uploaded files |
| **Results** | `results/{jobId}.json` | Processing results |
| **Errors** | `results/{jobId}_error.json` | Error files |
| **Redis Keys** | `job:{jobId}` | Job metadata |

## 🛡️ Safety Features

1. ✅ **Dry-Run Default** - Won't delete unless explicitly enabled
2. ✅ **Minimum TTL** - Prevents TTL < 1 hour
3. ✅ **Path Validation** - Requires correct prefixes
4. ✅ **Batch Limits** - Max 500 items per run
5. ✅ **Error Isolation** - Continues on failures
6. ✅ **Idempotent** - Safe to run multiple times

## 📝 Audit Logs

Every run creates: `tmp_uploads/maintenance/cleaner_runs/cleaner_{timestamp}.json`

Example:
```json
{
  "runId": "cleaner_20251206_030000",
  "dryRun": true,
  "ttlHours": 24,
  "totalBlobsScanned": 150,
  "deletedBlobs": 45,
  "totalKeysScanned": 100,
  "deletedKeys": 30,
  "errors": []
}
```

## 🧪 Test Coverage

- ✅ Dry-run doesn't delete data
- ✅ Destructive mode deletes old data only
- ✅ Recent data preserved
- ✅ Redis keys cleaned
- ✅ Audit logs created
- ✅ TTL validation
- ✅ Prefix validation
- ✅ Batch limits
- ✅ Error handling

## 📚 Documentation

- **Complete Guide**: `docs/retention_policy.md`
- **Scheduled Jobs**: `docs/scheduled_jobs.md`
- **README Section**: Search for "Cleanup & Retention Subsystem"

## ⚙️ Scheduled Job Setup

### Antigravity Platform

```yaml
scheduled_jobs:
  - name: datapilot-cleanup
    schedule: "0 3 * * *"
    command: python -m src.maintenance.cron_entry
    runtime: python3.11
```

### Cron (Linux/Mac)

```bash
0 3 * * * cd /path/to/datapilot-ai && python -m src.maintenance.cron_entry
```

### Windows Task Scheduler

1. Create Basic Task: "DataPilot AI Cleanup"
2. Trigger: Daily at 3:00 AM
3. Action: `python -m src.maintenance.cron_entry`

## 🔧 Troubleshooting

### No Data Being Deleted?

1. Check `CLEANER_DRY_RUN=false` in `.env`
2. Verify data is older than `JOB_TTL_HOURS`
3. Review audit logs

### Permission Errors?

1. Check storage directory permissions
2. Verify Redis connectivity
3. Run health check

### Too Much Being Deleted?

1. Increase `JOB_TTL_HOURS`
2. Check system clock (UTC)
3. Review audit logs

## 📞 Support

Run health check first:
```bash
python -m src.maintenance.health_check
```

Check recent audit logs:
```bash
dir tmp_uploads\maintenance\cleaner_runs
```

## ✨ Best Practices

1. 🧪 **Test first** - Run in dry-run mode for 7 days
2. 📊 **Monitor** - Review audit logs regularly
3. ⏰ **Schedule wisely** - Run during off-peak hours
4. 🚨 **Alert** - Set up monitoring for failures
5. 📝 **Document** - Keep track of TTL changes

---

**Status**: ✅ Production Ready  
**Version**: 1.0  
**Last Updated**: 2025-12-06
