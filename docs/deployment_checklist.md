# DataPilot AI - Deployment Checklist

## Overview

This checklist ensures all steps are completed for a successful deployment to Antigravity.

---

## Pre-Deployment Checklist

### Code & Configuration

- [ ] All code changes committed and pushed to repository
- [ ] `antigravity.yml` reviewed and updated (if needed)
- [ ] `.env.example` updated with new environment variables (if any)
- [ ] `requirements.txt` updated with new dependencies (if any)
- [ ] All Python files pass syntax validation (`python -m py_compile`)
- [ ] No secrets or credentials in code or configuration files
- [ ] Git branch is correct (main for production, staging for staging)

### Testing

- [ ] All unit tests pass locally
- [ ] Integration tests pass locally
- [ ] Manual testing completed for new features
- [ ] Edge cases tested (large files, invalid inputs, etc.)
- [ ] Performance testing completed (if applicable)

### Documentation

- [ ] README.md updated (if needed)
- [ ] API documentation updated (if endpoints changed)
- [ ] Deployment runbook reviewed
- [ ] Troubleshooting guide reviewed
- [ ] CHANGELOG.md updated with new version

### Secrets & Environment

- [ ] `OPENROUTER_API_KEY` set in Antigravity Secret Manager
- [ ] `REDIS_URL` set in Antigravity Secret Manager
- [ ] `BLOB_KEY` set in Antigravity Secret Manager (if using external storage)
- [ ] `SENTRY_DSN` set in Antigravity Secret Manager (if using Sentry)
- [ ] All required environment variables configured in `antigravity.yml`
- [ ] Secrets verified with `antigravity secrets list`

### Infrastructure

- [ ] Redis instance is running and accessible
- [ ] Blob storage is configured and accessible
- [ ] Network policies allow traffic to OpenRouter API
- [ ] Service accounts have correct permissions
- [ ] Resource limits (memory, CPU) are appropriate

---

## Deployment Checklist

### Step 1: Pre-Deployment Validation

- [ ] Run `python -m py_compile src/worker.py`
- [ ] Run `python -m py_compile src/api/upload/route.py`
- [ ] Verify all required files exist:
  - [ ] `antigravity.yml`
  - [ ] `requirements.txt`
  - [ ] `src/worker.py`
  - [ ] `src/api/upload/route.py`
  - [ ] `src/api/health/route.py`
  - [ ] `src/api/cancel/route.py`

### Step 2: Set Environment Variables

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key"
export REDIS_URL="redis://your-redis:6379/0"
export BLOB_KEY="your-blob-key"  # Optional
export SENTRY_DSN="https://your-sentry-dsn"  # Optional
```

- [ ] Environment variables exported
- [ ] Variables verified with `echo $OPENROUTER_API_KEY` (masked)

### Step 3: Run Deployment Script

```bash
cd scripts
./deploy_antigravity.sh
```

- [ ] Deployment script started
- [ ] No errors during validation phase
- [ ] Deployment tag created
- [ ] Secrets set in Antigravity
- [ ] Services deployed successfully
- [ ] Deployment completed within expected time (< 5 minutes)

### Step 4: Verify Deployment

```bash
./scripts/verify_deploy.sh
```

- [ ] API is reachable
- [ ] Health endpoint returns `status: ok`
- [ ] Redis connection is healthy
- [ ] Blob storage is accessible
- [ ] Worker heartbeat is recent (< 60 seconds old)
- [ ] No errors in recent logs

### Step 5: Run Smoke Tests

```bash
./scripts/run_smoke_tests.sh
```

- [ ] Test A: Upload and Process - **PASSED**
- [ ] Test B: Frontend Render - **PASSED**
- [ ] Test C: LLM Integration - **PASSED**
- [ ] Test D: Cancel Flow - **PASSED**
- [ ] Test E: Error Handling - **PASSED**
- [ ] Test F: Timeout - **PASSED** or **SKIPPED**
- [ ] All smoke tests passed (0 failures)
- [ ] Smoke test report generated in `reports/`

---

## Post-Deployment Checklist

### Monitoring

- [ ] Check metrics dashboard
  - [ ] `jobs_received_total` is incrementing
  - [ ] `jobs_completed_total` is incrementing
  - [ ] `jobs_failed_total` is low (< 5%)
  - [ ] `job_processing_duration_seconds` is acceptable (< 60s p95)
  - [ ] `llm_call_duration_seconds` is acceptable (< 10s p95)

- [ ] Check logs for errors
  ```bash
  antigravity logs --service api --tail 100
  antigravity logs --service worker --tail 100
  ```
  - [ ] No `ERROR` level logs
  - [ ] No `CRITICAL` level logs
  - [ ] Worker startup message present
  - [ ] API startup message present

- [ ] Check alerts
  ```bash
  antigravity alerts list
  ```
  - [ ] No active alerts
  - [ ] Alert rules configured correctly

### Functional Testing

- [ ] Upload a test file via frontend
- [ ] Verify job completes successfully
- [ ] Verify result.json is generated
- [ ] Verify frontend renders results correctly
- [ ] Test job cancellation
- [ ] Test error handling (invalid file)

### Performance Testing

- [ ] Upload small file (< 1 MB) - completes in < 10 seconds
- [ ] Upload medium file (5 MB) - completes in < 30 seconds
- [ ] Upload large file (20 MB) - completes in < 60 seconds
- [ ] API response time < 500ms for upload endpoint
- [ ] Worker processing multiple jobs concurrently (if applicable)

### Documentation & Communication

- [ ] Update deployment log with timestamp and version
- [ ] Notify team of successful deployment
- [ ] Update status page (if applicable)
- [ ] Document any issues encountered during deployment
- [ ] Update runbook with any new learnings

---

## Rollback Checklist

### When to Rollback

Rollback immediately if:

- [ ] Smoke tests fail
- [ ] Health checks fail
- [ ] Error rate > 10%
- [ ] Worker not responding for > 2 minutes
- [ ] Critical bug discovered
- [ ] Data corruption detected

### Rollback Procedure

1. **Initiate Rollback**
   ```bash
   cd scripts
   ./rollback_antigravity.sh
   ```
   - [ ] Rollback script started
   - [ ] Confirmation provided (or `FORCE_ROLLBACK=1`)
   - [ ] Previous deployment tag identified
   - [ ] Rollback completed

2. **Verify Rollback**
   ```bash
   ./scripts/verify_deploy.sh
   ```
   - [ ] Health checks pass
   - [ ] Services are running
   - [ ] No errors in logs

3. **Post-Rollback**
   - [ ] Notify team of rollback
   - [ ] Document reason for rollback
   - [ ] Create incident report
   - [ ] Plan fix and re-deployment

---

## Acceptance Criteria

Deployment is considered successful when:

- ✅ `scripts/deploy_antigravity.sh` runs successfully
- ✅ `scripts/verify_deploy.sh` returns healthy (`/api/health` OK)
- ✅ `scripts/run_smoke_tests.sh` completes with all tests passing
- ✅ Upload returns jobId for sample CSV
- ✅ Worker processes the job and sets status to `completed`
- ✅ `result.json` exists and matches expected schema
- ✅ Frontend (or mock endpoint) renders result payload
- ✅ Logs show LLM call to OpenRouter when `OPENROUTER_API_KEY` is present
- ✅ Artifacts and smoke test report saved to `reports/` with timestamps
- ✅ No active alerts
- ✅ Error rate < 5%
- ✅ All services healthy for 15 minutes post-deployment

---

## Sign-Off

### Deployment Team

- [ ] **Developer**: Code reviewed and tested
  - Name: ________________
  - Date: ________________

- [ ] **DevOps**: Deployment completed and verified
  - Name: ________________
  - Date: ________________

- [ ] **QA**: Smoke tests passed
  - Name: ________________
  - Date: ________________

- [ ] **Product Owner**: Acceptance criteria met
  - Name: ________________
  - Date: ________________

### Deployment Details

- **Version**: ________________
- **Environment**: ________________ (staging/production)
- **Deployment Date**: ________________
- **Deployment Time**: ________________
- **Git Commit**: ________________
- **Deployment Tag**: ________________

### Notes

_Any additional notes or observations:_

---

---

**Last Updated**: 2025-12-06
**Version**: 1.0
