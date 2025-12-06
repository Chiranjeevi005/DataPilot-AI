# DataPilot AI - Deployment Guide

## Quick Start

Deploy DataPilot AI to Antigravity in 3 steps:

```bash
# 1. Set secrets
export OPENROUTER_API_KEY="sk-or-v1-your-key"
export REDIS_URL="redis://your-redis:6379/0"

# 2. Deploy
./scripts/deploy_antigravity.sh

# 3. Verify
./scripts/verify_deploy.sh
./scripts/run_smoke_tests.sh
```

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Process](#deployment-process)
4. [Verification](#verification)
5. [Smoke Testing](#smoke-testing)
6. [Monitoring](#monitoring)
7. [Rollback](#rollback)
8. [CI/CD Integration](#cicd-integration)
9. [Troubleshooting](#troubleshooting)

---

## Overview

DataPilot AI is deployed to Antigravity as a multi-service application:

- **API Service**: Serverless endpoints for upload, job status, cancellation, and health checks
- **Worker Service**: Background job processor that handles data analysis and LLM insights
- **Scheduled Jobs**: Daily cleanup job for expired data and Redis keys
- **Infrastructure**: Redis for job queue, Blob storage for files, OpenRouter for LLM

---

## Prerequisites

### Required Tools

- **Antigravity CLI** (v1.0+) or API access
- **Git** for version control
- **Bash** for running scripts
- **Python 3.11+** for local validation

### Required Accounts

- **OpenRouter Account**: Get API key from [openrouter.ai](https://openrouter.ai/)
  - Model: `deepseek/deepseek-r1`
  - Temperature: `0.0` (deterministic)
- **Antigravity Account**: Access to project and deployment permissions

### Required Secrets

Set these in Antigravity Secret Manager:

1. `OPENROUTER_API_KEY` - OpenRouter API key for LLM calls
2. `REDIS_URL` - Redis connection string
3. `BLOB_KEY` - Blob storage credentials (if using external storage)
4. `SENTRY_DSN` - Sentry DSN for error tracking (optional)

---

## Deployment Process

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd datapilot-ai
```

### Step 2: Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Validate installation
python -m py_compile src/worker.py
```

### Step 3: Configure Secrets

**Option A: Via Antigravity CLI**

```bash
antigravity secrets set OPENROUTER_API_KEY
antigravity secrets set REDIS_URL
antigravity secrets set BLOB_KEY  # Optional
antigravity secrets set SENTRY_DSN  # Optional
```

**Option B: Via Environment Variables (for deployment script)**

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
export REDIS_URL="redis://your-redis:6379/0"
export BLOB_KEY="your-blob-key"
export SENTRY_DSN="https://your-sentry-dsn"
```

### Step 4: Run Deployment Script

```bash
cd scripts
./deploy_antigravity.sh
```

**What happens:**

1. ✅ Validates environment variables
2. ✅ Validates project structure
3. ✅ Creates deployment tag
4. ✅ Sets secrets in Antigravity
5. ✅ Deploys services (API, Worker, Cleaner)
6. ✅ Waits for deployment to complete

**Expected output:**

```
[INFO] =========================================
[INFO] DataPilot AI - Antigravity Deployment
[INFO] =========================================
[INFO] Validating required environment variables...
[INFO]   ✓ OPENROUTER_API_KEY is set (sk-o****...)
[INFO]   ✓ REDIS_URL is set (redi****...)
[INFO] All required environment variables are set ✓
[INFO] Deployment completed successfully! ✓
```

---

## Verification

### Automated Verification

```bash
./scripts/verify_deploy.sh
```

**Checks performed:**

- ✅ API is reachable
- ✅ Health endpoint returns `status: ok`
- ✅ Redis connection is healthy
- ✅ Blob storage is accessible
- ✅ Worker heartbeat is recent

### Manual Verification

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

---

## Smoke Testing

### Running Smoke Tests

```bash
./scripts/run_smoke_tests.sh
```

### Tests Performed

| Test | Description | Expected Result |
|------|-------------|-----------------|
| **A: Upload and Process** | Uploads CSV, waits for completion, validates result.json | Job completes with valid schema |
| **B: Frontend Render** | Validates result payload structure | Chart specs and insights present |
| **C: LLM Integration** | Verifies LLM calls to OpenRouter | Insights generated (not fallback) |
| **D: Cancel Flow** | Uploads and cancels job | Job transitions to `cancelled` |
| **E: Error Handling** | Tests LLM failure fallback | Job completes with fallback insights |
| **F: Timeout** | Tests job timeout enforcement | Job fails with `timeout` error |

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
  "tests": [...]
}
```

---

## Monitoring

### Logs

```bash
# View worker logs
antigravity logs --service worker --follow

# View API logs
antigravity logs --service api --follow

# Filter by job ID
antigravity logs --service worker --filter "jobId=job_abc123"
```

### Metrics

**Key metrics to monitor:**

- `jobs_received_total` - Total jobs received
- `jobs_completed_total` - Total jobs completed
- `jobs_failed_total` - Total jobs failed
- `job_processing_duration_seconds` - Job processing time
- `llm_call_duration_seconds` - LLM call latency

**Query metrics:**

```bash
# Job completion rate
antigravity metrics query "jobs_completed_total / jobs_received_total"

# Average processing time
antigravity metrics query "avg(job_processing_duration_seconds)"
```

### Alerts

Configured alerts:

- **High Failure Rate**: > 10% jobs failing
- **Worker Down**: Heartbeat age > 120 seconds
- **LLM Circuit Open**: Circuit breaker triggered

---

## Rollback

### When to Rollback

Rollback if:

- ❌ Smoke tests fail
- ❌ Health checks fail
- ❌ Error rate > 10%
- ❌ Worker not responding
- ❌ Critical bug discovered

### Rollback Procedure

```bash
cd scripts
./rollback_antigravity.sh
```

**What happens:**

1. Prompts for confirmation
2. Retrieves previous deployment tag
3. Checks out previous version
4. Deploys previous version
5. Verifies rollback

**Force rollback (no confirmation):**

```bash
FORCE_ROLLBACK=1 ./rollback_antigravity.sh
```

**Rollback to specific version:**

```bash
ROLLBACK_VERSION=deploy_20241206_100000 ./rollback_antigravity.sh
```

---

## CI/CD Integration

### GitHub Actions

A complete GitHub Actions workflow is provided in `.github/workflows/deploy.yml`.

**Features:**

- ✅ Automated deployment on push to `main` or `staging`
- ✅ Python syntax validation
- ✅ Smoke tests after deployment
- ✅ Automatic rollback on failure
- ✅ Slack notifications
- ✅ Artifact uploads (smoke test reports)

**Required GitHub Secrets:**

- `OPENROUTER_API_KEY`
- `REDIS_URL`
- `BLOB_KEY`
- `SENTRY_DSN`
- `ANTIGRAVITY_API_ENDPOINT`
- `ANTIGRAVITY_API_KEY`
- `SLACK_WEBHOOK_URL`

### Manual CI/CD

Use the CI/CD integration script:

```bash
./scripts/ci_deploy.sh
```

**Environment variables:**

- `AUTO_ROLLBACK_ON_SMOKE_FAIL=true` - Auto-rollback on smoke test failure
- `SMOKE_TEST_ON_DEPLOY=true` - Run smoke tests after deployment

---

## Troubleshooting

### Common Issues

#### Deployment fails with "Missing required environment variables"

**Solution:**

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key"
export REDIS_URL="redis://your-redis:6379/0"
./scripts/deploy_antigravity.sh
```

#### Health check returns "worker: stale"

**Solution:**

```bash
antigravity services restart worker
antigravity logs --service worker --tail 50
```

#### Smoke tests fail

**Solution:**

```bash
# Check logs
antigravity logs --service worker --tail 100
antigravity logs --service api --tail 100

# Rollback if needed
./scripts/rollback_antigravity.sh
```

### Detailed Troubleshooting

See [docs/troubleshooting.md](./troubleshooting.md) for comprehensive troubleshooting guide.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Antigravity Platform                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  API Service │  │    Worker    │  │   Cleaner    │     │
│  │  (Serverless)│  │  (Persistent)│  │  (Scheduled) │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         ├──────────────────┼──────────────────┤              │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼───────┐    │
│  │                    Redis Queue                      │    │
│  │  - Job metadata (job:*)                             │    │
│  │  - Job queue (data_jobs)                            │    │
│  │  - Worker heartbeat                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Blob Storage                        │   │
│  │  - Uploads (uploads/)                                │   │
│  │  - Results (results/)                                │   │
│  │  - Maintenance logs (maintenance/)                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
                    ┌──────────────────┐
                    │   OpenRouter     │
                    │ (deepseek-r1)    │
                    └──────────────────┘
```

---

## Environment Variables Reference

See `.env.example` for complete list. Key deployment variables:

```bash
# Required Secrets
OPENROUTER_API_KEY=sk-or-v1-your-key
REDIS_URL=redis://your-redis:6379/0
BLOB_KEY=your-blob-key  # Optional
SENTRY_DSN=https://your-sentry-dsn  # Optional

# LLM Configuration
LLM_MODEL=deepseek/deepseek-r1
LLM_BASE_URL=https://openrouter.ai/api/v1

# Job Configuration
JOB_TTL_HOURS=24
JOB_TIMEOUT_SECONDS=600
CLIENT_MAX_WAIT_SECONDS=600
MAX_UPLOAD_SIZE_BYTES=20971520

# Worker Configuration
WORKER_POLL_INTERVAL=1
WORKER_HEARTBEAT_INTERVAL=30

# Deployment Configuration
ANTIGRAVITY_API_ENDPOINT=https://api.antigravity.io
ANTIGRAVITY_API_KEY=your-api-key
API_BASE_URL=http://localhost:5328
```

---

## Documentation

- **[Deployment Runbook](./docs/deploy_runbook.md)** - Detailed deployment procedures
- **[Troubleshooting Guide](./docs/troubleshooting.md)** - Common issues and solutions
- **[Deployment Checklist](./docs/deployment_checklist.md)** - Pre/post-deployment checklist
- **[Observability Guide](./docs/observability.md)** - Logging and monitoring
- **[Retention Policy](./docs/retention_policy.md)** - Data cleanup and retention

---

## Support

For deployment issues:

1. Check [troubleshooting guide](./docs/troubleshooting.md)
2. Review logs: `antigravity logs --service <service>`
3. Check metrics: `antigravity metrics dashboard`
4. Contact DevOps team

---

**Last Updated**: 2025-12-06
**Version**: 1.0
