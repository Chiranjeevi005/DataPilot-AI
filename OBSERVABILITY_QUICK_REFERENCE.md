# DataPilot AI - Observability Quick Reference

## 🚀 Quick Start

### 1. Enable Observability (Already Done!)
The observability layer is integrated into worker and APIs.

### 2. Configure Environment
```bash
# Optional: Enable Sentry
SENTRY_DSN=https://your-dsn@sentry.io/project

# Optional: Adjust log level
OBSERVABILITY_LOG_LEVEL=INFO

# Optional: Enable debug mode (dev only!)
DEBUG=false
```

### 3. Run Worker
```bash
python src/worker.py
```

### 4. Check Health
```bash
curl http://localhost:5329/api/health
```

## 📝 Logging

### Import
```python
from observability import log_info, log_error, log_exception
```

### Usage
```python
# Simple log
log_info("my_component", "Processing started")

# With job context
log_info("my_component", "File parsed", 
         job_id="job_123", step="parse", rows=1000)

# Error
log_error("my_component", "Failed", 
          job_id="job_123", step="llm", error="timeout")

# Exception
try:
    risky_operation()
except Exception as e:
    log_exception("my_component", "Failed", 
                  exc_info=e, job_id="job_123")
```

## 📊 Metrics

### Import
```python
from observability import increment, observe
```

### Usage
```python
# Increment counter
increment("jobs_received_total")
increment("jobs_completed_total")

# Record value
observe("avg_processing_time_seconds", 15.3)
```

### Available Metrics
- `jobs_received_total`
- `jobs_completed_total`
- `jobs_failed_total`
- `llm_failures_total`
- `blob_failures_total`
- `avg_processing_time_seconds`

## ⏱️ Job Timing

### Import
```python
from observability import on_job_start, on_job_end
```

### Usage
```python
# Start timer
on_job_start("job_123")

# ... do work ...

# End timer and get duration
duration = on_job_end("job_123")
observe("avg_processing_time_seconds", duration)
```

## 🏥 Health Check

### Endpoint
```bash
GET /api/health
```

### Run Health Server
```bash
python src/api/health/route.py
```

### Check Status
```bash
curl http://localhost:5329/api/health | jq
```

### Response
```json
{
  "status": "ok",
  "components": {
    "redis": {"status": "ok"},
    "blob": {"status": "ok"},
    "worker": {"status": "ok"}
  }
}
```

## 🧪 Testing

```bash
# Test API logging
python scripts/test_api_logging.py

# Test metrics
python scripts/test_worker_metrics.py

# Test health check
python scripts/test_health_endpoint.py
```

## 📋 Log Format

```json
{
  "timestamp": "2025-12-06T12:00:00Z",
  "level": "INFO",
  "component": "worker",
  "jobId": "job_123",
  "step": "parse",
  "message": "File parsed",
  "extra": {"rows": 1000}
}
```

## 🔍 Viewing Logs

### Local
Logs go to stdout. View with:
```bash
python src/worker.py | jq
```

### Filter by job
```bash
python src/worker.py | jq 'select(.jobId == "job_123")'
```

### Filter by step
```bash
python src/worker.py | jq 'select(.step == "llm")'
```

## 📈 Viewing Metrics

### Local File
```bash
cat metrics/metrics_snapshot.json | jq
```

### Blob Storage
Check `metrics/metrics_snapshot_*.json` in blob storage

## 🔒 PII Masking

Automatically masks:
- Emails: `[EMAIL_MASKED]`
- Phones: `[PHONE_MASKED]`
- IDs: `[ID_MASKED]`

## 🐛 Debug Mode

### Enable (dev only!)
```bash
DEBUG=true
```

### Features
- Full stack traces
- Verbose logging
- Raw data previews

**⚠️ Never use in production!**

## 🚨 Sentry

### Setup
```bash
# Install SDK
pip install sentry-sdk

# Configure
SENTRY_DSN=https://your-dsn@sentry.io/project

# Restart worker
python src/worker.py
```

### What's Sent
- All ERROR logs
- Exceptions with stack traces
- Context: jobId, step, requestId
- PII-masked data

## 🔧 Configuration

```bash
# Observability
SENTRY_DSN=                              # Optional
OBSERVABILITY_LOG_LEVEL=INFO             # DEBUG|INFO|WARNING|ERROR
METRICS_FLUSH_INTERVAL=10                # Jobs
METRICS_AUTO_FLUSH=true                  # true|false
DEBUG=false                               # true|false

# Worker Heartbeat
WORKER_HEARTBEAT_INTERVAL=30             # Seconds
HEALTH_WORKER_MAX_AGE_SECONDS=60         # Seconds
```

## 📚 Documentation

Full docs: `docs/observability.md`

## 🎯 Common Tasks

### Check if worker is alive
```bash
curl http://localhost:5329/api/health | jq '.components.worker'
```

### View recent logs for a job
```bash
# Assuming logs are in a file
grep "job_123" worker.log | jq
```

### Check metrics
```bash
cat metrics/metrics_snapshot.json | jq '.counters'
```

### Test PII masking
```python
from observability import log_info
log_info("test", "User: john@example.com, Phone: 555-1234")
# Output: User: [EMAIL_MASKED], Phone: [PHONE_MASKED]
```

## 🆘 Troubleshooting

### No logs appearing
- Check `OBSERVABILITY_LOG_LEVEL`
- Verify observability is imported
- Check stdout/stderr

### Metrics not saving
- Check `METRICS_AUTO_FLUSH=true`
- Verify `METRICS_SNAPSHOT_PATH` is writable
- Check worker logs for errors

### Worker showing as stale
- Verify worker is running
- Check Redis connectivity
- Review `WORKER_HEARTBEAT_INTERVAL`

### Sentry not working
- Verify `SENTRY_DSN` is correct
- Check `sentry-sdk` is installed
- Look for init message in logs

## 💡 Tips

1. **Always include jobId** in job logs
2. **Use step field** to track progress
3. **Log at right level**: INFO for normal, ERROR for failures
4. **Monitor /api/health** regularly
5. **Review metrics** for anomalies
6. **Set up alerts** on health failures
7. **Never enable DEBUG** in production

## 🔗 Quick Links

- Full Documentation: `docs/observability.md`
- Implementation Summary: `OBSERVABILITY_IMPLEMENTATION_COMPLETE.md`
- Test Scripts: `scripts/test_*.py`
- Configuration: `.env.example`
