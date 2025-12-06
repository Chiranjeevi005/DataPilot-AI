# DataPilot AI - Observability Layer

## Overview

The observability layer provides comprehensive monitoring, logging, and debugging capabilities for DataPilot AI. It covers structured JSON logging, centralized error reporting, metrics emission, health checks, and developer-friendly debugging tools.

## Architecture

### Components

1. **Structured Logger** (`src/observability/logger.py`)
   - JSON-formatted logs with consistent schema
   - PII masking for sensitive data
   - Optional Sentry integration for error tracking
   - Component-based logging with request/job context

2. **Metrics Collector** (`src/observability/metrics.py`)
   - Counter metrics (jobs processed, failures, etc.)
   - Histogram metrics (processing time, latency)
   - Automatic snapshot persistence to blob/local storage
   - Percentile calculations (p50, p95, p99)

3. **Context Tracker** (`src/observability/context.py`)
   - Request ID generation and tracking
   - Job lifecycle timing with monotonic timers
   - Thread-safe context management

4. **Health Check Endpoint** (`src/api/health/route.py`)
   - Redis connectivity check
   - Blob storage validation
   - Worker heartbeat monitoring
   - Component-level status reporting

## Log Format

All logs follow a structured JSON format:

```json
{
  "timestamp": "2025-12-06T12:00:00Z",
  "level": "INFO",
  "component": "worker",
  "jobId": "job_abc123",
  "step": "eda",
  "message": "EDA completed",
  "requestId": "req_xyz789",
  "extra": {
    "qualityScore": 85,
    "rows": 1000
  }
}
```

### Required Fields

- **timestamp**: UTC ISO-8601 timestamp
- **level**: Log level (INFO, WARNING, ERROR)
- **component**: Module/service name
- **message**: Human-readable log message

### Optional Fields

- **jobId**: Job identifier (for job-related logs)
- **step**: Processing step (e.g., "dequeue", "parse", "eda", "llm")
- **requestId**: Request identifier (for API requests)
- **extra**: Additional context (key-value pairs)

## Example Log Lines

### Worker Job Processing

```json
{"timestamp":"2025-12-06T12:00:00Z","level":"INFO","component":"worker","jobId":"job_abc123","step":"dequeue","message":"Job dequeued from queue","extra":{"fileName":"sales_data.csv"}}
{"timestamp":"2025-12-06T12:00:01Z","level":"INFO","component":"process_job","jobId":"job_abc123","step":"start","message":"Job started","extra":{"fileUrl":"blob://uploads/job_abc123/sales_data.csv","fileName":"sales_data.csv"}}
{"timestamp":"2025-12-06T12:00:02Z","level":"INFO","component":"process_job","jobId":"job_abc123","step":"read_blob","message":"File accessed successfully","extra":{"localPath":"/tmp/datapilot/downloads/20251206_120002/sales_data.csv"}}
{"timestamp":"2025-12-06T12:00:03Z","level":"INFO","component":"process_job","jobId":"job_abc123","step":"parse","message":"File type detected","extra":{"fileType":"csv"}}
{"timestamp":"2025-12-06T12:00:05Z","level":"INFO","component":"process_job","jobId":"job_abc123","step":"parse","message":"DataFrame parsed successfully","extra":{"rows":1000,"cols":15}}
{"timestamp":"2025-12-06T12:00:06Z","level":"INFO","component":"process_job","jobId":"job_abc123","step":"eda","message":"Running EDA"}
{"timestamp":"2025-12-06T12:00:08Z","level":"INFO","component":"process_job","jobId":"job_abc123","step":"eda","message":"EDA completed","extra":{"qualityScore":85}}
{"timestamp":"2025-12-06T12:00:09Z","level":"INFO","component":"process_job","jobId":"job_abc123","step":"llm","message":"Running LLM for insights"}
{"timestamp":"2025-12-06T12:00:15Z","level":"INFO","component":"process_job","jobId":"job_abc123","step":"llm","message":"LLM insights generated"}
{"timestamp":"2025-12-06T12:00:16Z","level":"INFO","component":"process_job","jobId":"job_abc123","step":"write_result","message":"Writing result.json"}
{"timestamp":"2025-12-06T12:00:17Z","level":"INFO","component":"process_job","jobId":"job_abc123","step":"write_result","message":"Result saved to blob","extra":{"resultUrl":"blob://results/job_abc123/result.json"}}
{"timestamp":"2025-12-06T12:00:17Z","level":"INFO","component":"process_job","jobId":"job_abc123","step":"completed","message":"Job completed successfully","extra":{"resultUrl":"blob://results/job_abc123/result.json","durationSeconds":15.3}}
```

### API Request

```json
{"timestamp":"2025-12-06T12:00:00Z","level":"INFO","component":"upload_api","requestId":"req_xyz789","step":"request_received","message":"Upload request received","extra":{"fileName":"data.csv","contentLength":50000}}
{"timestamp":"2025-12-06T12:00:01Z","level":"INFO","component":"upload_api","requestId":"req_xyz789","step":"validation","message":"File validated successfully"}
{"timestamp":"2025-12-06T12:00:02Z","level":"INFO","component":"upload_api","requestId":"req_xyz789","step":"storage","message":"File saved to blob","extra":{"fileUrl":"blob://uploads/job_abc123/data.csv"}}
{"timestamp":"2025-12-06T12:00:02Z","level":"INFO","component":"upload_api","requestId":"req_xyz789","step":"queue","message":"Job enqueued","extra":{"jobId":"job_abc123"}}
```

### Error with Stack Trace

```json
{
  "timestamp": "2025-12-06T12:00:00Z",
  "level": "ERROR",
  "component": "process_job",
  "jobId": "job_abc123",
  "step": "llm",
  "message": "Error processing job",
  "extra": {
    "errorName": "ConnectionError",
    "errorMessage": "Failed to connect to LLM API",
    "stackTrace": "Traceback (most recent call last):\n  File \"process_job.py\", line 150, in process_job\n    insights_data = llm_client.generate_insights(...)\n  ..."
  }
}
```

## Metrics

### Supported Metrics

#### Counters

- `jobs_received_total`: Total jobs dequeued from queue
- `jobs_completed_total`: Total jobs completed successfully
- `jobs_failed_total`: Total jobs that failed
- `llm_failures_total`: Total LLM API failures
- `blob_failures_total`: Total blob storage failures

#### Histograms

- `avg_processing_time_seconds`: Job processing duration (with percentiles)

### Metrics Snapshot Format

```json
{
  "timestamp": "2025-12-06T12:00:00Z",
  "counters": {
    "jobs_received_total": 150,
    "jobs_completed_total": 142,
    "jobs_failed_total": 8,
    "llm_failures_total": 3,
    "blob_failures_total": 1
  },
  "histograms": {
    "avg_processing_time_seconds": {
      "count": 142,
      "sum": 2130.5,
      "avg": 15.0,
      "min": 5.2,
      "max": 45.8,
      "p50": 14.3,
      "p95": 28.7,
      "p99": 42.1
    }
  }
}
```

### Metrics Persistence

Metrics are automatically flushed to storage:

- **Local Mode**: Saved to `metrics/metrics_snapshot.json`
- **Blob Mode**: Saved to blob storage at `metrics/metrics_snapshot_YYYYMMDD_HHMMSS.json`
- **Flush Interval**: Configurable via `METRICS_FLUSH_INTERVAL` (default: 10 jobs)

## Health Check Endpoint

### Endpoint

```
GET /api/health
```

### Response Format

```json
{
  "status": "ok",
  "timestamp": "2025-12-06T12:00:00Z",
  "requestId": "req_health_abc123",
  "components": {
    "redis": {
      "status": "ok",
      "details": {
        "message": "Redis is healthy"
      }
    },
    "blob": {
      "status": "ok",
      "details": {
        "message": "Blob storage configured"
      }
    },
    "worker": {
      "status": "ok",
      "details": {
        "message": "Worker is healthy",
        "lastHeartbeat": "2025-12-06T11:59:55Z",
        "ageSeconds": 5.2
      }
    }
  }
}
```

### Status Values

- **ok**: Component is healthy
- **degraded**: System is operational but degraded (e.g., worker heartbeat stale)
- **error**: Component has failed
- **stale**: Worker heartbeat is too old

### HTTP Status Codes

- **200**: System is healthy or degraded
- **503**: System has errors (Service Unavailable)
- **500**: Health check itself failed

## Worker Heartbeat

The worker updates a heartbeat key in Redis every 30 seconds (configurable):

- **Key**: `worker:heartbeat`
- **Value**: UTC ISO-8601 timestamp
- **TTL**: 120 seconds (2 minutes)

The health check endpoint reads this key and verifies it's recent (< 60 seconds old by default).

### How It Works

1. Worker starts background heartbeat thread
2. Thread updates `worker:heartbeat` key every 30 seconds
3. Health endpoint reads key and checks age
4. If age > 60 seconds, worker is considered "stale"

## PII Masking

The logger automatically masks PII in log messages and extra fields:

- **Emails**: `john.doe@example.com` → `[EMAIL_MASKED]`
- **Phone Numbers**: `555-123-4567` → `[PHONE_MASKED]`
- **ID-like Values**: `ABCD12345678` → `[ID_MASKED]`

### Example

Input:
```python
log_info("api", "User uploaded file", email="john.doe@example.com", phone="555-123-4567")
```

Output:
```json
{
  "timestamp": "2025-12-06T12:00:00Z",
  "level": "INFO",
  "component": "api",
  "message": "User uploaded file",
  "extra": {
    "email": "[EMAIL_MASKED]",
    "phone": "[PHONE_MASKED]"
  }
}
```

## Sentry Integration

### Setup

1. Set `SENTRY_DSN` environment variable:
   ```bash
   SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
   ```

2. Install Sentry SDK:
   ```bash
   pip install sentry-sdk
   ```

3. Restart worker/API

### What Gets Sent to Sentry

- All ERROR level logs
- Exceptions with stack traces
- Context: jobId, step, requestId
- PII-masked data

### Disabling Sentry

Simply leave `SENTRY_DSN` empty or unset.

## Debug Mode

Enable debug mode for development:

```bash
DEBUG=true
```

When enabled:
- Logs include full stack traces
- Raw EDA previews are logged
- More verbose logging

**⚠️ Never use DEBUG=true in production!**

## Configuration

### Environment Variables

```bash
# Sentry Integration
SENTRY_DSN=                              # Optional: Sentry DSN for error tracking

# Logging
OBSERVABILITY_LOG_LEVEL=INFO             # Log level: DEBUG, INFO, WARNING, ERROR
DEBUG=false                               # Enable debug mode (never in production!)

# Metrics
METRICS_FLUSH_INTERVAL=10                # Flush metrics every N jobs
METRICS_AUTO_FLUSH=true                  # Auto-flush metrics in background
METRICS_SNAPSHOT_PATH=metrics/metrics_snapshot.json  # Local metrics path

# Worker Heartbeat
WORKER_HEARTBEAT_INTERVAL=30             # Heartbeat update interval (seconds)
HEALTH_WORKER_MAX_AGE_SECONDS=60         # Max heartbeat age before "stale" (seconds)

# Environment
ENVIRONMENT=development                  # Environment name (for Sentry)
```

## Usage Examples

### Logging in Python

```python
from observability import log_info, log_error, log_exception

# Simple log
log_info("my_component", "Processing started")

# Log with job context
log_info("my_component", "File parsed", job_id="job_123", step="parse", rows=1000)

# Log error
log_error("my_component", "Failed to connect", job_id="job_123", step="llm", 
          error="ConnectionError")

# Log exception with stack trace
try:
    risky_operation()
except Exception as e:
    log_exception("my_component", "Operation failed", exc_info=e, 
                  job_id="job_123", step="process")
```

### Emitting Metrics

```python
from observability import increment, observe

# Increment counter
increment("jobs_received_total")
increment("jobs_completed_total")

# Record histogram value
observe("avg_processing_time_seconds", 15.3)
```

### Job Timing

```python
from observability import on_job_start, on_job_end

# Start timing
on_job_start("job_123")

# ... do work ...

# End timing and get duration
duration = on_job_end("job_123")
print(f"Job took {duration:.2f} seconds")
```

## Testing

### Test Scripts

1. **API Logging Test**
   ```bash
   python scripts/test_api_logging.py
   ```
   - Tests structured logging in API endpoints
   - Validates request ID tracking
   - Verifies PII masking

2. **Worker Metrics Test**
   ```bash
   python scripts/test_worker_metrics.py
   ```
   - Tests counter and histogram metrics
   - Validates percentile calculations
   - Tests metrics persistence

3. **Health Endpoint Test**
   ```bash
   python scripts/test_health_endpoint.py
   ```
   - Tests health check endpoint
   - Validates component status checks
   - Provides manual test instructions

### Running Tests

```bash
# Ensure dependencies are installed
pip install requests

# Run individual tests
python scripts/test_api_logging.py
python scripts/test_worker_metrics.py
python scripts/test_health_endpoint.py

# Check logs for structured JSON output
```

## Deployment Checklist

### Local Development

- [x] Set `OBSERVABILITY_LOG_LEVEL=DEBUG` for verbose logging
- [x] Set `DEBUG=true` for development features
- [x] Leave `SENTRY_DSN` empty (no error tracking needed)
- [x] Use `METRICS_AUTO_FLUSH=true` for automatic metrics

### Production (Antigravity)

- [x] Set `OBSERVABILITY_LOG_LEVEL=INFO` (or WARNING)
- [x] Set `DEBUG=false` (never true in production!)
- [x] Configure `SENTRY_DSN` for error tracking
- [x] Set `ENVIRONMENT=production`
- [x] Ensure `WORKER_HEARTBEAT_INTERVAL=30`
- [x] Monitor `/api/health` endpoint
- [x] Set up alerts for health check failures
- [x] Review metrics snapshots regularly

## Troubleshooting

### No Logs Appearing

1. Check `OBSERVABILITY_LOG_LEVEL` is set correctly
2. Ensure observability module is imported
3. Verify logs are going to stdout/stderr

### Metrics Not Persisting

1. Check `METRICS_AUTO_FLUSH=true`
2. Verify `METRICS_SNAPSHOT_PATH` is writable
3. For blob mode, check `BLOB_ENABLED=true` and `BLOB_KEY` is set
4. Check worker logs for flush errors

### Worker Showing as Stale

1. Verify worker is running
2. Check worker logs for heartbeat updates
3. Verify Redis connectivity
4. Check `WORKER_HEARTBEAT_INTERVAL` and `HEALTH_WORKER_MAX_AGE_SECONDS`

### Sentry Not Receiving Errors

1. Verify `SENTRY_DSN` is set correctly
2. Check `sentry-sdk` is installed
3. Look for Sentry initialization message in logs
4. Verify network connectivity to Sentry

## Best Practices

1. **Always include jobId** in job-related logs
2. **Use step field** to track processing stages
3. **Include context** in extra fields (rows, cols, fileType, etc.)
4. **Log at appropriate levels**:
   - INFO: Normal operations
   - WARNING: Recoverable issues
   - ERROR: Failures requiring attention
5. **Use log_exception** for errors with stack traces
6. **Monitor metrics** regularly for anomalies
7. **Set up alerts** on health check failures
8. **Review Sentry** errors daily in production

## Future Enhancements

- [ ] Distributed tracing with OpenTelemetry
- [ ] Prometheus metrics export
- [ ] Grafana dashboards
- [ ] Log aggregation (ELK stack)
- [ ] Custom alerting rules
- [ ] Performance profiling
- [ ] Request/response logging middleware
- [ ] Audit trail for data access

## Support

For questions or issues with observability:
1. Check this documentation
2. Review test scripts for examples
3. Check worker/API logs for errors
4. Verify configuration in `.env`
