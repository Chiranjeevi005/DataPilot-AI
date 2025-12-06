# Phase 7 Quick Reference

## New API Endpoints

### Cancel Job
```bash
POST /api/cancel?jobId=<id>
```

**Request (Query Param)**:
```bash
curl -X POST "http://localhost:5328/api/cancel?jobId=job_abc123"
```

**Request (JSON Body)**:
```bash
curl -X POST http://localhost:5328/api/cancel \
  -H "Content-Type: application/json" \
  -d '{"jobId": "job_abc123"}'
```

**Response (Success)**:
```json
{
  "jobId": "job_abc123",
  "status": "cancelled",
  "cancelledAt": "2025-12-06T10:30:00Z"
}
```

**Response (Already Cancelled)**:
```json
{
  "jobId": "job_abc123",
  "status": "cancelled",
  "message": "Job was already cancelled",
  "cancelledAt": "2025-12-06T10:25:00Z"
}
```

**Response (Cannot Cancel)**:
```json
{
  "error": "Cannot cancel job with status 'completed'",
  "jobId": "job_abc123",
  "status": "completed"
}
```

## Enhanced Job Status Response

### GET /api/job-status/<job_id>

**Response Fields**:
```json
{
  "jobId": "job_abc123",
  "status": "processing|completed|failed|cancelled|submitted",
  "progress": 0.5,
  "resultUrl": "file:///path/to/result.json",
  "error": "timeout|processing_error|blob_upload_failed|worker_shutdown",
  "errorMessage": "Human-readable error description",
  "createdAt": "2025-12-06T10:00:00Z",
  "updatedAt": "2025-12-06T10:05:00Z",
  "cancelledAt": "2025-12-06T10:03:00Z"
}
```

**Status Values**:
- `submitted` - Job queued, not yet processing
- `processing` - Worker is processing
- `completed` - Successfully completed
- `failed` - Failed (check `error` and `errorMessage`)
- `cancelled` - Cancelled by user

**Error Codes**:
- `timeout` - Job exceeded JOB_TIMEOUT_SECONDS
- `processing_error` - General processing failure
- `blob_upload_failed` - Storage operation failed after retries
- `worker_shutdown` - Worker terminated during processing
- `llm_failure_fallback` - LLM failed, fallback used (in issues field)

## Error.json Structure

When a job fails, `error.json` is saved to blob storage:

```json
{
  "jobId": "job_abc123",
  "status": "failed",
  "error": "timeout",
  "message": "Job exceeded maximum processing time",
  "timestamp": "2025-12-06T10:30:00Z"
}
```

Access via `resultUrl` field in job status.

## Configuration Quick Reference

### Essential Variables
```bash
# Timeouts
JOB_TIMEOUT_SECONDS=600              # Server-side job timeout (10 min)
CLIENT_MAX_WAIT_SECONDS=600          # Client polling timeout (10 min)

# LLM
OPENROUTER_API_KEY=sk-or-...         # OpenRouter API key
LLM_MODEL=deepseek/deepseek-r1       # Model identifier
LLM_RETRY_ATTEMPTS=2                 # LLM retry attempts

# Retry/Backoff
BLOB_RETRY_ATTEMPTS=3                # Blob operation retries
RETRY_INITIAL_DELAY=0.5              # Initial delay (seconds)
RETRY_FACTOR=2.0                     # Backoff multiplier
RETRY_MAX_DELAY=10                   # Max delay (seconds)

# Circuit Breaker
LLM_CIRCUIT_THRESHOLD=5              # Failures to open circuit
LLM_CIRCUIT_WINDOW=300               # Window (5 min)
LLM_CIRCUIT_COOLDOWN=600             # Cooldown (10 min)
```

## Client Polling Example

### JavaScript/TypeScript
```javascript
async function pollJobStatus(jobId, maxWaitMs = 600000) {
  const delays = [1000, 2000, 4000, 8000, 15000]; // ms
  let attempt = 0;
  const startTime = Date.now();
  
  while (Date.now() - startTime < maxWaitMs) {
    const response = await fetch(`/api/job-status/${jobId}`);
    const data = await response.json();
    
    // Terminal states
    if (['completed', 'failed', 'cancelled'].includes(data.status)) {
      return data;
    }
    
    // Exponential backoff
    const delay = delays[Math.min(attempt, delays.length - 1)];
    await new Promise(resolve => setTimeout(resolve, delay));
    attempt++;
  }
  
  throw new Error('Job polling timeout');
}
```

### Python
```python
import time
import requests

def poll_job_status(job_id, max_wait_seconds=600):
    delays = [1, 2, 4, 8, 15]  # seconds
    attempt = 0
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        response = requests.get(f'http://localhost:5328/api/job-status/{job_id}')
        data = response.json()
        
        # Terminal states
        if data['status'] in ['completed', 'failed', 'cancelled']:
            return data
        
        # Exponential backoff
        delay = delays[min(attempt, len(delays) - 1)]
        time.sleep(delay)
        attempt += 1
    
    raise TimeoutError('Job polling timeout')
```

## Test Commands

### Run All Phase 7 Tests
```bash
# Blob retry test
./scripts/test_phase7_retry_blob.sh

# LLM failure and fallback
./scripts/test_phase7_llm_fail.sh

# Job cancellation
./scripts/test_phase7_cancel.sh

# Job timeout
./scripts/test_phase7_timeout.sh
```

### Manual Testing

#### Test Cancellation
```bash
# Upload a file
JOB_ID=$(curl -s -X POST http://localhost:5328/api/upload \
  -F "file=@./dev-samples/sales_demo.csv" | \
  python -c "import sys, json; print(json.load(sys.stdin)['jobId'])")

# Cancel it
curl -X POST "http://localhost:5328/api/cancel?jobId=$JOB_ID"

# Check status
curl -s http://localhost:5328/api/job-status/$JOB_ID | python -m json.tool
```

#### Test Timeout
```bash
# Set short timeout
export JOB_TIMEOUT_SECONDS=10
export SIMULATED_SLOW_PROCESSING_SECONDS=20

# Upload and monitor
JOB_ID=$(curl -s -X POST http://localhost:5328/api/upload \
  -F "file=@./dev-samples/sales_demo.csv" | \
  python -c "import sys, json; print(json.load(sys.stdin)['jobId'])")

# Wait and check (should timeout)
sleep 15
curl -s http://localhost:5328/api/job-status/$JOB_ID | python -m json.tool
```

#### Test LLM Fallback
```bash
# Set invalid API key
export OPENROUTER_API_KEY="invalid_key"

# Upload and process
JOB_ID=$(curl -s -X POST http://localhost:5328/api/upload \
  -F "file=@./dev-samples/sales_demo.csv" | \
  python -c "import sys, json; print(json.load(sys.stdin)['jobId'])")

# Wait and check result (should have fallback insights)
sleep 10
curl -s http://localhost:5328/api/job-status/$JOB_ID | python -m json.tool
```

## Monitoring & Debugging

### Key Log Messages

**Retry Attempts**:
```
Save file test.csv for job job_123: Attempt 1/3
LLM call (deepseek/deepseek-r1): Attempt 2/2
Download http://example.com/file: Attempt 3/3
```

**Circuit Breaker**:
```
Circuit breaker OPENING: 5 failures within 300s window (threshold: 5)
Circuit breaker is OPEN. Using fallback.
Circuit breaker cooldown complete. Closing circuit.
```

**Cancellation**:
```
Job job_123 was cancelled before processing. Skipping.
Job job_123 was cancelled during parsing.
Job job_123 was cancelled during processing.
```

**Timeout**:
```
Job job_123 has timed out
Job job_123 timed out during parsing.
```

**Graceful Shutdown**:
```
Received signal 15. Shutting down gracefully...
Marked job job_123 as failed due to shutdown
Worker shutdown complete.
```

### Redis Inspection

```bash
# Check job status
redis-cli GET "job:job_abc123"

# Check queue length
redis-cli LLEN "data_jobs"

# View all job keys
redis-cli KEYS "job:*"
```

## Common Issues & Solutions

### Issue: Jobs timing out too quickly
**Solution**: Increase `JOB_TIMEOUT_SECONDS` in `.env`

### Issue: LLM circuit breaker opening frequently
**Solution**: 
- Check `OPENROUTER_API_KEY` is valid
- Increase `LLM_CIRCUIT_THRESHOLD`
- Check OpenRouter service status

### Issue: Blob operations failing
**Solution**:
- Check disk space
- Verify `tmp_uploads/` directory permissions
- Increase `BLOB_RETRY_ATTEMPTS`

### Issue: Worker not detecting cancellation
**Solution**:
- Ensure Redis is running
- Check worker logs for cancellation check messages
- Verify job status in Redis

### Issue: Error.json not created
**Solution**:
- Check blob storage configuration
- Verify `RESULTS_DIR` permissions
- Check worker logs for storage errors

## Production Checklist

- [ ] Set `OPENROUTER_API_KEY` in production `.env`
- [ ] Configure `JOB_TIMEOUT_SECONDS` for your workload
- [ ] Set up Redis persistence (AOF or RDB)
- [ ] Configure worker auto-restart (systemd/supervisor)
- [ ] Set up log aggregation
- [ ] Monitor circuit breaker state
- [ ] Set up alerts for high failure rates
- [ ] Test graceful shutdown in production
- [ ] Configure blob storage (if using cloud)
- [ ] Set appropriate retry thresholds

## Support

For issues or questions:
1. Check worker logs for detailed error messages
2. Inspect Redis job data: `redis-cli GET "job:<jobId>"`
3. Review `error.json` if job failed
4. Check circuit breaker state in logs
5. Verify environment variables are set correctly
