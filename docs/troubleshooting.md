# DataPilot AI - Troubleshooting Guide

## Overview

This guide provides solutions to common issues encountered when deploying and running DataPilot AI on Antigravity.

## Table of Contents

1. [Deployment Issues](#deployment-issues)
2. [API Issues](#api-issues)
3. [Worker Issues](#worker-issues)
4. [Redis Issues](#redis-issues)
5. [Blob Storage Issues](#blob-storage-issues)
6. [LLM Integration Issues](#llm-integration-issues)
7. [Job Processing Issues](#job-processing-issues)
8. [Performance Issues](#performance-issues)
9. [Monitoring & Logging Issues](#monitoring--logging-issues)

---

## Deployment Issues

### Issue: Deployment Script Fails with "Missing required environment variables"

**Symptoms**:
```
[ERROR] Missing required environment variables:
[ERROR]   - OPENROUTER_API_KEY
```

**Cause**: Required secrets not set in environment.

**Solution**:
```bash
# Set required environment variables
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
export REDIS_URL="redis://your-redis:6379/0"

# Or load from .env file
source .env

# Then retry deployment
./scripts/deploy_antigravity.sh
```

---

### Issue: Deployment Hangs at "Waiting for deployment to complete"

**Symptoms**:
```
[INFO] Waiting for deployment to complete...
[INFO] Waiting... (60/300 seconds)
[INFO] Waiting... (120/300 seconds)
...
```

**Cause**: Services not starting properly.

**Solution**:

1. **Check service status**:
   ```bash
   antigravity services status api
   antigravity services status worker
   ```

2. **Check logs for errors**:
   ```bash
   antigravity logs --service api --tail 50
   antigravity logs --service worker --tail 50
   ```

3. **Common issues**:
   - Missing secrets → Set via `antigravity secrets set`
   - Redis not available → Check Redis service status
   - Python syntax errors → Validate with `python -m py_compile src/worker.py`

4. **Restart services**:
   ```bash
   antigravity services restart api
   antigravity services restart worker
   ```

---

### Issue: "Antigravity CLI not found"

**Symptoms**:
```
[ERROR] Neither Antigravity CLI nor API credentials found.
```

**Cause**: Antigravity CLI not installed or not in PATH.

**Solution**:

1. **Install Antigravity CLI**:
   ```bash
   # Follow Antigravity installation instructions
   curl -sSL https://install.antigravity.io | sh
   ```

2. **Or use API credentials**:
   ```bash
   export ANTIGRAVITY_API_ENDPOINT="https://api.antigravity.io"
   export ANTIGRAVITY_API_KEY="your-api-key"
   ```

---

## API Issues

### Issue: API Returns 500 Internal Server Error

**Symptoms**:
```bash
curl http://localhost:5328/api/upload
# Returns: 500 Internal Server Error
```

**Cause**: API service crashed or misconfigured.

**Solution**:

1. **Check API logs**:
   ```bash
   antigravity logs --service api --tail 100
   ```

2. **Look for common errors**:
   - `ModuleNotFoundError` → Missing dependencies
   - `redis.exceptions.ConnectionError` → Redis not reachable
   - `KeyError: 'OPENROUTER_API_KEY'` → Secret not set

3. **Verify secrets are set**:
   ```bash
   antigravity secrets list
   ```

4. **Restart API service**:
   ```bash
   antigravity services restart api
   ```

---

### Issue: Upload Endpoint Returns 413 Payload Too Large

**Symptoms**:
```bash
curl -F "file=@large_file.csv" http://localhost:5328/api/upload
# Returns: 413 Payload Too Large
```

**Cause**: File exceeds `MAX_UPLOAD_SIZE_BYTES`.

**Solution**:

1. **Check current limit**:
   ```bash
   antigravity config get MAX_UPLOAD_SIZE_BYTES
   # Default: 20971520 (20 MB)
   ```

2. **Increase limit** (if appropriate):
   ```bash
   antigravity config set MAX_UPLOAD_SIZE_BYTES 52428800  # 50 MB
   ```

3. **Or compress file before upload**:
   ```bash
   gzip large_file.csv
   curl -F "file=@large_file.csv.gz" http://localhost:5328/api/upload
   ```

---

### Issue: Health Endpoint Returns "worker: stale"

**Symptoms**:
```json
{
  "status": "degraded",
  "worker": "stale",
  "workerLastHeartbeat": "2025-12-06T10:00:00Z"
}
```

**Cause**: Worker not updating heartbeat (crashed or stuck).

**Solution**:

1. **Check worker status**:
   ```bash
   antigravity services status worker
   ```

2. **Check worker logs**:
   ```bash
   antigravity logs --service worker --tail 100
   ```

3. **Restart worker**:
   ```bash
   antigravity services restart worker
   ```

4. **If worker keeps crashing**, check for:
   - Redis connection issues
   - Memory limits exceeded
   - Unhandled exceptions in job processing

---

## Worker Issues

### Issue: Worker Not Processing Jobs

**Symptoms**:
- Jobs stuck in `submitted` status
- Worker logs show "Listening for jobs..." but no processing

**Cause**: Worker not dequeuing from Redis or jobs not being enqueued.

**Solution**:

1. **Check Redis queue**:
   ```bash
   redis-cli -u "$REDIS_URL" LLEN data_jobs
   # Should show number of pending jobs
   ```

2. **Check worker logs**:
   ```bash
   antigravity logs --service worker --tail 50 --follow
   ```

3. **Manually inspect job**:
   ```bash
   redis-cli -u "$REDIS_URL" LRANGE data_jobs 0 0
   ```

4. **Verify worker is running**:
   ```bash
   antigravity services status worker
   ```

5. **Restart worker**:
   ```bash
   antigravity services restart worker
   ```

---

### Issue: Worker Crashes with "Out of Memory"

**Symptoms**:
```
[ERROR] MemoryError: Unable to allocate array
```

**Cause**: Worker processing large files exceeds memory limit.

**Solution**:

1. **Increase worker memory** in `antigravity.yml`:
   ```yaml
   services:
     - name: worker
       resources:
         memory: 2048  # Increase from 1024 to 2048 MB
   ```

2. **Redeploy**:
   ```bash
   ./scripts/deploy_antigravity.sh
   ```

3. **Or enable streaming for large files**:
   - Ensure `STREAM_THRESHOLD_BYTES` is set appropriately
   - Use `CHUNKSIZE_ROWS` for chunked processing

---

### Issue: Worker Stuck Processing Same Job

**Symptoms**:
- Job status stays `processing` indefinitely
- Worker logs show same job ID repeatedly

**Cause**: Job processing logic stuck in infinite loop or waiting indefinitely.

**Solution**:

1. **Cancel the stuck job**:
   ```bash
   curl -X POST "http://localhost:5328/api/cancel?jobId=job_stuck123"
   ```

2. **Restart worker**:
   ```bash
   antigravity services restart worker
   ```

3. **Check for timeout configuration**:
   ```bash
   antigravity config get JOB_TIMEOUT_SECONDS
   # Should be set (e.g., 600)
   ```

4. **Review job processing code** for blocking operations:
   - LLM calls without timeout
   - File downloads without timeout
   - Infinite loops

---

## Redis Issues

### Issue: "Redis connection refused"

**Symptoms**:
```
[ERROR] Failed to connect to Redis: Connection refused
```

**Cause**: Redis service not running or incorrect URL.

**Solution**:

1. **Check Redis service status**:
   ```bash
   antigravity services status redis
   ```

2. **Verify Redis URL**:
   ```bash
   antigravity secrets get REDIS_URL
   # Should be: redis://host:6379/0
   ```

3. **Test Redis connection**:
   ```bash
   redis-cli -u "$REDIS_URL" PING
   # Should return: PONG
   ```

4. **Restart Redis** (if managed by Antigravity):
   ```bash
   antigravity services restart redis
   ```

5. **If using external Redis**, verify:
   - Network connectivity
   - Firewall rules
   - Authentication credentials

---

### Issue: "Redis timeout"

**Symptoms**:
```
[ERROR] Redis timeout: Command timed out after 5 seconds
```

**Cause**: Redis overloaded or network latency.

**Solution**:

1. **Check Redis memory usage**:
   ```bash
   redis-cli -u "$REDIS_URL" INFO memory
   ```

2. **Check Redis slow log**:
   ```bash
   redis-cli -u "$REDIS_URL" SLOWLOG GET 10
   ```

3. **Increase Redis memory** (if needed):
   ```yaml
   dependencies:
     - name: redis
       memory: 512  # Increase from 256
   ```

4. **Clear old jobs** (if TTL not working):
   ```bash
   # Run cleaner manually
   python src/maintenance/cleaner.py --dry-run=false
   ```

---

## Blob Storage Issues

### Issue: "Blob upload failed after retries"

**Symptoms**:
```
[ERROR] Blob upload failed after 3 attempts
```

**Cause**: Blob storage service unavailable or credentials invalid.

**Solution**:

1. **Check blob storage status**:
   ```bash
   antigravity services status blob
   ```

2. **Verify blob credentials**:
   ```bash
   antigravity secrets get BLOB_KEY
   ```

3. **Test blob access**:
   ```bash
   # Upload test file
   echo "test" > /tmp/test.txt
   antigravity blob upload /tmp/test.txt uploads/test.txt
   
   # Download test file
   antigravity blob download uploads/test.txt /tmp/test_download.txt
   ```

4. **Check blob permissions**:
   - Worker service account should have `blob:read`, `blob:write`, `blob:list`

5. **Fallback to local storage** (temporary):
   ```bash
   antigravity config set BLOB_ENABLED false
   ```

---

### Issue: "Result file not found"

**Symptoms**:
```
[ERROR] Failed to fetch result.json: File not found
```

**Cause**: Result file not uploaded to blob storage or incorrect path.

**Solution**:

1. **Check worker logs** for upload errors:
   ```bash
   antigravity logs --service worker --filter "blob_upload"
   ```

2. **List blob files**:
   ```bash
   antigravity blob list results/
   ```

3. **Verify result URL** in job metadata:
   ```bash
   redis-cli -u "$REDIS_URL" GET "job:job_abc123"
   # Check "resultUrl" field
   ```

4. **Check blob path prefixes**:
   ```bash
   antigravity config get BLOB_PATH_PREFIXES
   # Should include: uploads/,results/
   ```

---

## LLM Integration Issues

### Issue: "LLM circuit breaker OPEN"

**Symptoms**:
```
[WARN] LLM circuit breaker is OPEN. Using fallback insights.
```

**Cause**: Too many consecutive LLM failures triggered circuit breaker.

**Solution**:

1. **Check OpenRouter API status**:
   ```bash
   curl https://openrouter.ai/api/v1/models
   ```

2. **Verify API key**:
   ```bash
   antigravity secrets get OPENROUTER_API_KEY
   # Ensure it starts with "sk-or-v1-"
   ```

3. **Check circuit breaker config**:
   ```bash
   antigravity config get LLM_CIRCUIT_THRESHOLD  # Default: 5
   antigravity config get LLM_CIRCUIT_COOLDOWN   # Default: 600 (10 min)
   ```

4. **Wait for cooldown** (circuit auto-closes after cooldown period)

5. **Or manually reset circuit** (if available):
   ```bash
   redis-cli -u "$REDIS_URL" DEL "llm:circuit_breaker:failures"
   ```

6. **Restart worker** to reset circuit state:
   ```bash
   antigravity services restart worker
   ```

---

### Issue: "LLM call failed: 401 Unauthorized"

**Symptoms**:
```
[ERROR] LLM call failed: 401 Unauthorized
```

**Cause**: Invalid or expired OpenRouter API key.

**Solution**:

1. **Verify API key** is correct:
   ```bash
   # Test API key directly
   curl https://openrouter.ai/api/v1/models \
     -H "Authorization: Bearer $OPENROUTER_API_KEY"
   ```

2. **Update API key**:
   ```bash
   antigravity secrets set OPENROUTER_API_KEY --value "sk-or-v1-new-key"
   ```

3. **Restart worker**:
   ```bash
   antigravity services restart worker
   ```

---

### Issue: "LLM call failed: 429 Rate Limit Exceeded"

**Symptoms**:
```
[ERROR] LLM call failed: 429 Too Many Requests
```

**Cause**: Exceeded OpenRouter rate limits.

**Solution**:

1. **Check OpenRouter account limits**:
   - Visit https://openrouter.ai/dashboard

2. **Reduce concurrent jobs**:
   ```yaml
   services:
     - name: worker
       instances: 1  # Reduce from higher number
   ```

3. **Increase retry delay**:
   ```bash
   antigravity config set RETRY_INITIAL_DELAY 2.0  # Increase from 0.5
   antigravity config set RETRY_MAX_DELAY 30       # Increase from 10
   ```

4. **Enable circuit breaker** to prevent cascading failures:
   ```bash
   antigravity config set LLM_CIRCUIT_THRESHOLD 3  # Lower threshold
   ```

---

### Issue: "LLM returned invalid JSON"

**Symptoms**:
```
[ERROR] Failed to parse LLM response as JSON
```

**Cause**: LLM returned malformed JSON or non-JSON text.

**Solution**:

1. **Check worker logs** for raw LLM response:
   ```bash
   antigravity logs --service worker --filter "llm_response"
   ```

2. **Verify prompt** is clear and includes JSON schema:
   - Check `prompts/system_prompt.txt`
   - Ensure few-shot examples are valid JSON

3. **Retry logic** should handle this automatically:
   - Check `LLM_RETRY_ATTEMPTS` is set (default: 2)

4. **Fallback** should be used if retries fail:
   - Verify `fallback_generator.py` is working

5. **If persistent**, consider:
   - Switching to a different model
   - Adjusting temperature (should be 0.0 for deterministic output)

---

## Job Processing Issues

### Issue: Job Stuck in "submitted" Status

**Symptoms**:
- Job status never changes from `submitted`
- No worker logs for this job

**Cause**: Job not enqueued to Redis or worker not running.

**Solution**:

1. **Check if job is in Redis queue**:
   ```bash
   redis-cli -u "$REDIS_URL" LRANGE data_jobs 0 -1
   # Should show job payload
   ```

2. **Check worker is running**:
   ```bash
   antigravity services status worker
   antigravity logs --service worker --tail 20
   ```

3. **Manually enqueue job** (if missing):
   ```bash
   redis-cli -u "$REDIS_URL" LPUSH data_jobs '{"jobId":"job_abc123",...}'
   ```

4. **Restart worker**:
   ```bash
   antigravity services restart worker
   ```

---

### Issue: Job Fails with "timeout"

**Symptoms**:
```json
{
  "status": "failed",
  "error": "timeout",
  "message": "Job exceeded maximum processing time"
}
```

**Cause**: Job processing took longer than `JOB_TIMEOUT_SECONDS`.

**Solution**:

1. **Check timeout configuration**:
   ```bash
   antigravity config get JOB_TIMEOUT_SECONDS
   # Default: 600 (10 minutes)
   ```

2. **Increase timeout** (if appropriate):
   ```bash
   antigravity config set JOB_TIMEOUT_SECONDS 1200  # 20 minutes
   ```

3. **Optimize processing**:
   - Enable streaming for large files
   - Reduce LLM call latency
   - Optimize data processing logic

4. **Check for stuck operations**:
   - LLM calls hanging
   - File downloads hanging
   - Database queries hanging

---

### Issue: Job Fails with "processing_error"

**Symptoms**:
```json
{
  "status": "failed",
  "error": "processing_error",
  "message": "Error processing file: ..."
}
```

**Cause**: Unhandled exception during job processing.

**Solution**:

1. **Check worker logs** for stack trace:
   ```bash
   antigravity logs --service worker --filter "job_abc123"
   ```

2. **Common causes**:
   - Unsupported file format
   - Corrupted file
   - Missing columns in CSV
   - Invalid JSON structure

3. **Reproduce locally**:
   ```bash
   python scripts/manual_run_job.py job_abc123
   ```

4. **Fix and redeploy**:
   - Update error handling in `src/jobs/process_job.py`
   - Add validation for edge cases

---

## Performance Issues

### Issue: Jobs Taking Too Long to Process

**Symptoms**:
- Jobs taking > 2 minutes for small files
- High `job_processing_duration_seconds` metric

**Cause**: Slow LLM calls, inefficient data processing, or resource constraints.

**Solution**:

1. **Profile job processing**:
   ```bash
   antigravity logs --service worker --filter "duration_ms"
   ```

2. **Check LLM call latency**:
   ```bash
   antigravity metrics query "avg(llm_call_duration_seconds)"
   # Should be < 10 seconds
   ```

3. **Optimize LLM calls**:
   - Use `temperature=0.0` for faster responses
   - Reduce few-shot examples count
   - Use smaller model (if acceptable)

4. **Optimize data processing**:
   - Enable streaming for large files
   - Reduce `CHUNKSIZE_ROWS` if memory-bound
   - Increase `CHUNKSIZE_ROWS` if CPU-bound

5. **Scale worker resources**:
   ```yaml
   services:
     - name: worker
       resources:
         memory: 2048
         cpu: 2
   ```

---

### Issue: High API Latency

**Symptoms**:
- Upload endpoint taking > 5 seconds
- High `api_response_time` metric

**Cause**: Slow blob uploads, Redis latency, or API resource constraints.

**Solution**:

1. **Profile API requests**:
   ```bash
   antigravity logs --service api --filter "duration_ms"
   ```

2. **Check blob upload latency**:
   ```bash
   antigravity metrics query "avg(blob_operation_duration_seconds)"
   ```

3. **Check Redis latency**:
   ```bash
   redis-cli -u "$REDIS_URL" --latency
   ```

4. **Scale API resources**:
   ```yaml
   services:
     - name: api
       scaling:
         min: 2  # Increase from 1
         max: 20
   ```

---

## Monitoring & Logging Issues

### Issue: Logs Not Appearing

**Symptoms**:
```bash
antigravity logs --service worker
# Returns: No logs found
```

**Cause**: Logging not configured or logs not being shipped.

**Solution**:

1. **Check logging configuration** in `antigravity.yml`:
   ```yaml
   logging:
     level: INFO
     format: json
     destinations:
       - type: stdout
       - type: antigravity_logs
   ```

2. **Verify service is running**:
   ```bash
   antigravity services status worker
   ```

3. **Check local logs** (if available):
   ```bash
   # On worker instance
   tail -f /var/log/datapilot/worker.log
   ```

4. **Enable debug logging** (temporarily):
   ```bash
   antigravity config set DEBUG true
   antigravity config set OBSERVABILITY_LOG_LEVEL DEBUG
   ```

---

### Issue: Metrics Not Updating

**Symptoms**:
- Metrics dashboard shows stale data
- `antigravity metrics query` returns empty

**Cause**: Metrics not being emitted or not being collected.

**Solution**:

1. **Check metrics configuration**:
   ```bash
   antigravity config get METRICS_AUTO_FLUSH
   # Should be: true
   ```

2. **Verify metrics are being emitted**:
   ```bash
   antigravity logs --service worker --filter "metric"
   ```

3. **Check metrics snapshot**:
   ```bash
   cat metrics/metrics_snapshot.json
   ```

4. **Restart services**:
   ```bash
   antigravity services restart worker
   antigravity services restart api
   ```

---

## Emergency Procedures

### Complete System Failure

If all services are down:

1. **Check Antigravity platform status**:
   ```bash
   antigravity status
   ```

2. **Rollback to last known good deployment**:
   ```bash
   cd scripts
   FORCE_ROLLBACK=1 ./rollback_antigravity.sh
   ```

3. **If rollback fails**, deploy from scratch:
   ```bash
   git checkout <last-known-good-tag>
   ./scripts/deploy_antigravity.sh
   ```

4. **Contact Antigravity support** if platform issue

---

### Data Loss Prevention

If critical data is at risk:

1. **Backup Redis immediately**:
   ```bash
   redis-cli -u "$REDIS_URL" SAVE
   redis-cli -u "$REDIS_URL" BGSAVE
   ```

2. **Backup blob storage**:
   ```bash
   antigravity blob sync results/ /backup/results/
   ```

3. **Export job metadata**:
   ```bash
   redis-cli -u "$REDIS_URL" KEYS "job:*" | xargs redis-cli -u "$REDIS_URL" MGET > jobs_backup.json
   ```

---

## Getting Help

If you cannot resolve an issue:

1. **Collect diagnostic information**:
   ```bash
   # Service status
   antigravity services status --all > diagnostic.txt
   
   # Recent logs
   antigravity logs --service api --tail 200 >> diagnostic.txt
   antigravity logs --service worker --tail 200 >> diagnostic.txt
   
   # Configuration
   antigravity config list >> diagnostic.txt
   
   # Metrics
   antigravity metrics query "jobs_failed_total" >> diagnostic.txt
   ```

2. **Check documentation**:
   - `docs/deploy_runbook.md`
   - `docs/observability.md`
   - `README.md`

3. **Contact support**:
   - Include diagnostic information
   - Describe symptoms and steps to reproduce
   - Mention any recent changes

---

**Last Updated**: 2025-12-06
**Version**: 1.0
