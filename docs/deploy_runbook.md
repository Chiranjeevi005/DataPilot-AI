# DataPilot AI - Deployment Runbook

## Overview

This runbook provides step-by-step instructions for deploying DataPilot AI to Antigravity, including secrets management, monitoring, smoke testing, and rollback procedures.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Secrets Configuration](#secrets-configuration)
4. [Deployment Process](#deployment-process)
5. [Verification](#verification)
6. [Smoke Testing](#smoke-testing)
7. [Monitoring](#monitoring)
8. [Rollback](#rollback)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- **Antigravity CLI** (v1.0+) or API access
- **Git** (for deployment tagging)
- **Bash** (for running deployment scripts)
- **curl** (for API testing)
- **Python 3.11+** (for local validation)

### Required Accounts & Keys

- **OpenRouter API Key** - Get from [OpenRouter](https://openrouter.ai/)
  - Model: `deepseek/deepseek-r1`
  - Required for LLM insights generation
- **Redis Instance** - Managed by Antigravity or external
- **Blob Storage** - Antigravity blob storage or compatible service
- **Sentry DSN** (Optional) - For error tracking

### Environment Requirements

- **Antigravity Project** created and configured
- **Service Account** with deployment permissions
- **Network Access** to OpenRouter API (https://openrouter.ai)

---

## Initial Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd datapilot-ai
```

### 2. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (for frontend)
npm install
```

### 3. Validate Project Structure

```bash
# Ensure all required files exist
ls -la antigravity.yml
ls -la src/worker.py
ls -la src/api/upload/route.py
```

### 4. Configure Antigravity CLI

```bash
# Login to Antigravity
antigravity login

# Set project context
antigravity config set project datapilot-ai
antigravity config set environment production
```

---

## Secrets Configuration

### Setting Secrets via Antigravity CLI

**IMPORTANT**: Never commit secrets to version control. Always use Antigravity Secret Manager.

#### 1. Set OpenRouter API Key

```bash
# Interactive (recommended)
antigravity secrets set OPENROUTER_API_KEY

# Or from environment variable
echo "$OPENROUTER_API_KEY" | antigravity secrets set OPENROUTER_API_KEY --stdin
```

**Verify**:
```bash
antigravity secrets list | grep OPENROUTER_API_KEY
```

#### 2. Set Redis URL

```bash
# If using Antigravity-managed Redis
antigravity secrets set REDIS_URL --value "redis://antigravity-redis:6379/0"

# If using external Redis
antigravity secrets set REDIS_URL --value "redis://your-redis-host:6379/0"
```

#### 3. Set Blob Storage Key (if using external storage)

```bash
# For Antigravity blob storage, this is auto-configured
# For external (e.g., AWS S3, Azure Blob)
antigravity secrets set BLOB_KEY --value "your-blob-storage-key"
```

#### 4. Set Sentry DSN (Optional)

```bash
antigravity secrets set SENTRY_DSN --value "https://your-sentry-dsn@sentry.io/project-id"
```

### Setting Secrets via Web Console

1. Navigate to **Antigravity Console** → **Your Project** → **Secrets**
2. Click **Add Secret**
3. Enter key-value pairs:
   - `OPENROUTER_API_KEY`: `sk-or-v1-...`
   - `REDIS_URL`: `redis://...`
   - `BLOB_KEY`: `...` (if needed)
   - `SENTRY_DSN`: `https://...` (optional)
4. Click **Save**

### Verifying Secrets

```bash
# List all secrets (values are masked)
antigravity secrets list

# Expected output:
# OPENROUTER_API_KEY  sk-or****...
# REDIS_URL           redis://****...
# BLOB_KEY            ****...
# SENTRY_DSN          https://****...
```

---

## Deployment Process

### Step 1: Pre-Deployment Checks

```bash
# Ensure you're on the correct branch
git branch

# Pull latest changes
git pull origin main

# Validate Python syntax
python -m py_compile src/worker.py
python -m py_compile src/api/upload/route.py
```

### Step 2: Set Environment Variables

Export required secrets (these will be used by the deployment script):

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
export REDIS_URL="redis://your-redis:6379/0"
export BLOB_KEY="your-blob-key"  # Optional
export SENTRY_DSN="https://your-sentry-dsn"  # Optional
```

**Note**: These are only needed for the deployment script validation. Actual runtime secrets are managed by Antigravity.

### Step 3: Run Deployment Script

```bash
cd scripts
./deploy_antigravity.sh
```

**What the script does**:
1. ✅ Validates required environment variables are set
2. ✅ Validates project structure
3. ✅ Validates Python syntax
4. ✅ Creates deployment tag (e.g., `deploy_20241206_143000`)
5. ✅ Sets secrets in Antigravity Secret Manager
6. ✅ Deploys services (API, Worker, Cleaner)
7. ✅ Waits for deployment to complete

**Expected Output**:
```
[INFO] =========================================
[INFO] DataPilot AI - Antigravity Deployment
[INFO] =========================================
[INFO] Validating required environment variables...
[INFO]   ✓ OPENROUTER_API_KEY is set (sk-o****...)
[INFO]   ✓ REDIS_URL is set (redi****...)
[INFO] All required environment variables are set ✓
[INFO] Validating project structure...
[INFO] Project structure validated ✓
[INFO] Creating deployment tag...
[INFO] Created deployment tag: deploy_20241206_143000
[INFO] Deploying to Antigravity...
[INFO] Deployment initiated via Antigravity CLI ✓
[INFO] =========================================
[INFO] Deployment completed successfully! ✓
[INFO] =========================================
```

### Step 4: Alternative - Manual Deployment

If the script fails, you can deploy manually:

```bash
# Deploy using Antigravity CLI
antigravity deploy --config antigravity.yml --env production --wait

# Or using API
curl -X POST "$ANTIGRAVITY_API_ENDPOINT/deploy" \
  -H "Authorization: Bearer $ANTIGRAVITY_API_KEY" \
  -F "config=@antigravity.yml"
```

---

## Verification

### Step 1: Run Verification Script

```bash
cd scripts
./verify_deploy.sh
```

**What it checks**:
1. ✅ API is reachable
2. ✅ Health endpoint returns `status: ok`
3. ✅ Redis connection is healthy
4. ✅ Blob storage is accessible
5. ✅ Worker heartbeat is recent
6. ✅ No errors in recent logs

**Expected Output**:
```
[INFO] =========================================
[INFO] DataPilot AI - Deployment Verification
[INFO] =========================================
[INFO] Checking if API is reachable...
[INFO]   ✓ API is reachable
[INFO] Checking health endpoint...
[INFO]   ✓ Health status: OK
[INFO]   ✓ Redis: OK
[INFO]   ✓ Blob Storage: ok
[INFO]   ✓ Worker: OK
[INFO] =========================================
[INFO] Deployment verification PASSED ✓
[INFO] =========================================
```

### Step 2: Manual Health Check

```bash
# Check health endpoint
curl http://localhost:5328/api/health

# Expected response:
{
  "status": "ok",
  "timestamp": "2025-12-06T14:30:00Z",
  "redis": "ok",
  "blob": "ok",
  "worker": "ok",
  "workerLastHeartbeat": "2025-12-06T14:29:55Z"
}
```

### Step 3: Check Service Status

```bash
# Check API service
antigravity services status api

# Check worker service
antigravity services status worker

# Check scheduled jobs
antigravity jobs list
```

---

## Smoke Testing

### Running Smoke Tests

```bash
cd scripts
./run_smoke_tests.sh
```

**Tests Performed**:

1. **Test A: Upload and Process**
   - Uploads `sales_demo.csv`
   - Polls job status until `completed`
   - Validates `result.json` schema
   - Checks for required keys: `schema`, `kpis`, `cleanedPreview`, `analystInsights`, `businessSummary`, `chartSpecs`, `qualityScore`

2. **Test B: Frontend Render**
   - Validates result payload structure
   - Checks for chart specs and insights

3. **Test C: LLM Integration**
   - Verifies LLM calls to OpenRouter
   - Checks worker logs for `LLM request started` and `LLM request completed`
   - Validates insights are generated (not fallback)

4. **Test D: Cancel Flow**
   - Uploads job
   - Cancels job mid-processing
   - Verifies status transitions to `cancelled`

5. **Test E: Error Handling**
   - Tests LLM failure fallback
   - Verifies job completes with fallback insights

6. **Test F: Timeout** (Skipped by default)
   - Requires special configuration

**Expected Output**:
```
[INFO] =========================================
[INFO] DataPilot AI - Smoke Test Suite
[INFO] =========================================
[TEST] Running Test A: Upload and Process
[INFO] Uploaded file, got jobId: job_abc123
[INFO] Job job_abc123 status: processing (elapsed: 0s)
[INFO] Job job_abc123 status: completed (elapsed: 5s)
[INFO] All required keys present in result.json
[INFO] ✓ upload_and_process PASSED (5 seconds)
...
[INFO] =========================================
[INFO] Smoke Test Summary
[INFO] =========================================
[INFO] Total Tests: 6
[INFO] Passed: 5
[INFO] Failed: 0
[INFO] All smoke tests PASSED ✓
```

### Smoke Test Report

Reports are saved to `reports/smoke_test_report_<timestamp>.json`:

```json
{
  "timestamp": "2025-12-06T14:35:00Z",
  "summary": {
    "total": 6,
    "passed": 5,
    "failed": 0
  },
  "tests": [
    {
      "name": "upload_and_process",
      "status": "PASS",
      "message": "Job completed successfully with valid result.json",
      "duration": 5
    },
    ...
  ]
}
```

---

## Monitoring

### Logs

#### View Worker Logs

```bash
# Real-time logs
antigravity logs --service worker --follow

# Last 100 lines
antigravity logs --service worker --tail 100

# Filter by job ID
antigravity logs --service worker --filter "jobId=job_abc123"
```

#### View API Logs

```bash
# Real-time logs
antigravity logs --service api --follow

# Last 100 lines
antigravity logs --service api --tail 100
```

### Metrics

#### View Metrics Dashboard

```bash
# Open Antigravity metrics dashboard
antigravity metrics dashboard

# Or access via web console
# https://console.antigravity.io/projects/datapilot-ai/metrics
```

**Key Metrics to Monitor**:

- `jobs_received_total` - Total jobs received
- `jobs_completed_total` - Total jobs completed
- `jobs_failed_total` - Total jobs failed
- `jobs_cancelled_total` - Total jobs cancelled
- `job_processing_duration_seconds` - Job processing time
- `llm_call_duration_seconds` - LLM call latency
- `blob_operation_duration_seconds` - Blob operation latency

#### Query Metrics via CLI

```bash
# Get job completion rate
antigravity metrics query "jobs_completed_total / jobs_received_total"

# Get average processing time
antigravity metrics query "avg(job_processing_duration_seconds)"

# Get LLM call success rate
antigravity metrics query "1 - (llm_failures_total / llm_calls_total)"
```

### Alerts

Alerts are configured in `antigravity.yml`:

- **High Failure Rate**: Triggered when `jobs_failed_total / jobs_received_total > 0.1` (10%)
- **Worker Down**: Triggered when worker heartbeat age > 120 seconds
- **LLM Circuit Open**: Triggered when LLM circuit breaker opens

**View Active Alerts**:
```bash
antigravity alerts list
```

---

## Rollback

### When to Rollback

Rollback if:
- ❌ Smoke tests fail
- ❌ Health checks fail
- ❌ High error rate (>10%)
- ❌ Worker not responding
- ❌ Critical bug discovered

### Automatic Rollback

If smoke tests fail during CI/CD, rollback is triggered automatically.

### Manual Rollback

#### Step 1: Run Rollback Script

```bash
cd scripts
./rollback_antigravity.sh
```

**What it does**:
1. Prompts for confirmation
2. Retrieves previous deployment tag
3. Checks out previous version
4. Deploys previous version
5. Verifies rollback

**Expected Output**:
```
[INFO] =========================================
[INFO] DataPilot AI - Rollback Deployment
[INFO] =========================================
Are you sure you want to rollback? (yes/no): yes
[INFO] Found previous deployment: deploy_20241206_120000
[INFO] Rolling back to tag: deploy_20241206_120000
[INFO] Rollback via CLI successful
[INFO] Verifying rollback...
[INFO] Health check passed ✓
[INFO] =========================================
[INFO] Rollback completed successfully! ✓
[INFO] =========================================
```

#### Step 2: Force Rollback (No Confirmation)

```bash
FORCE_ROLLBACK=1 ./rollback_antigravity.sh
```

#### Step 3: Rollback to Specific Version

```bash
ROLLBACK_VERSION=deploy_20241206_100000 ./rollback_antigravity.sh
```

### Post-Rollback

1. **Verify Health**: Run `./verify_deploy.sh`
2. **Check Logs**: Ensure no errors
3. **Notify Team**: Inform stakeholders of rollback
4. **Investigate**: Determine root cause of failure
5. **Fix and Redeploy**: Address issues and redeploy

---

## Troubleshooting

See [troubleshooting.md](./troubleshooting.md) for detailed troubleshooting guide.

**Quick Checks**:

1. **API not responding**:
   ```bash
   antigravity services restart api
   ```

2. **Worker not processing jobs**:
   ```bash
   antigravity services restart worker
   antigravity logs --service worker --tail 50
   ```

3. **Redis connection issues**:
   ```bash
   antigravity services status redis
   redis-cli -u "$REDIS_URL" PING
   ```

4. **LLM failures**:
   - Verify `OPENROUTER_API_KEY` is set correctly
   - Check OpenRouter API status
   - Review circuit breaker state

5. **Blob storage issues**:
   - Verify `BLOB_KEY` is set (if using external storage)
   - Check blob storage permissions

---

## Expected SLOs

### Performance Targets

- **Job Processing Time**: < 60 seconds (p95) for CSV files < 5MB
- **API Response Time**: < 500ms (p95) for upload endpoint
- **Worker Heartbeat**: Updated every 30 seconds
- **LLM Call Latency**: < 10 seconds (p95)

### Availability Targets

- **API Uptime**: 99.9%
- **Worker Uptime**: 99.5%
- **Job Completion Rate**: > 95%

### Capacity Limits

- **Max Upload Size**: 20 MB
- **Max Concurrent Jobs**: 10 (configurable)
- **Job Timeout**: 600 seconds (10 minutes)
- **Job TTL**: 24 hours

---

## Next Steps

After successful deployment:

1. ✅ Monitor metrics for 24 hours
2. ✅ Set up alerting integrations (Slack, PagerDuty, etc.)
3. ✅ Configure auto-scaling based on load
4. ✅ Set up automated smoke tests in CI/CD
5. ✅ Document any environment-specific configurations
6. ✅ Train team on monitoring and rollback procedures

---

## Support

For issues or questions:

- **Documentation**: See `docs/` directory
- **Logs**: `antigravity logs --service <service>`
- **Metrics**: `antigravity metrics dashboard`
- **Alerts**: `antigravity alerts list`

---

**Last Updated**: 2025-12-06
**Version**: 1.0
