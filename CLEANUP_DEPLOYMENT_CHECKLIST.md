# DataPilot AI - Cleanup Subsystem Deployment Checklist

## Pre-Deployment Testing

### Local Testing
- [ ] Run `python scripts/test_cleaner_create_fake_data.py` successfully
- [ ] Run `pwsh scripts/test_cleaner_run.sh` - all tests pass
- [ ] Run `pwsh scripts/test_cleaner_edgecases.sh` - all tests pass
- [ ] Run `python -m src.maintenance.health_check` - status is "healthy"
- [ ] Verify audit logs are created in `tmp_uploads/maintenance/cleaner_runs/`
- [ ] Review audit log format and contents

### Configuration Review
- [ ] Copy `.env.example` to `.env` (if not already done)
- [ ] Set `JOB_TTL_HOURS` to appropriate value (default: 24)
- [ ] Verify `CLEANER_DRY_RUN=true` (for initial deployment)
- [ ] Set `CLEANER_CRON_SCHEDULE` to desired schedule (default: "0 3 * * *")
- [ ] Verify `MIN_TTL_HOURS` is appropriate (default: 1)
- [ ] Verify `BLOB_PATH_PREFIXES="uploads/,results/"` is correct
- [ ] Set `CLEANER_LOG_LEVEL` (default: INFO)
- [ ] Set `CLEANER_MAX_DELETE_BATCH` (default: 500)
- [ ] Verify `CLEANER_AUDIT_BLOB_PATH` (default: "maintenance/cleaner_runs/")

## Initial Deployment (Dry-Run Phase)

### Week 1: Dry-Run Mode
- [ ] Deploy with `CLEANER_DRY_RUN=true`
- [ ] Configure scheduled job (see `docs/scheduled_jobs.md`)
- [ ] Verify scheduled job is registered and active
- [ ] Wait for first scheduled run (or trigger manually)
- [ ] Verify audit log is created after first run
- [ ] Review audit log contents:
  - [ ] Check `dryRun: true`
  - [ ] Review `deletedBlobs` count
  - [ ] Review `deletedKeys` count
  - [ ] Verify `errors` array is empty (or minimal)
- [ ] Monitor daily for 7 days
- [ ] Document any issues or unexpected behavior

### Daily Monitoring (Week 1)
- [ ] Day 1: Check audit log, verify counts are reasonable
- [ ] Day 2: Check audit log, compare with Day 1
- [ ] Day 3: Check audit log, verify consistency
- [ ] Day 4: Check audit log, verify no errors
- [ ] Day 5: Check audit log, verify patterns
- [ ] Day 6: Check audit log, verify stability
- [ ] Day 7: Final review, prepare for destructive mode

### Health Check Setup
- [ ] Set up automated health check monitoring
- [ ] Configure alerts for health check failures
- [ ] Test alert delivery
- [ ] Document alert recipients and escalation

## Enabling Destructive Mode

### Pre-Activation Checklist
- [ ] Dry-run mode has been active for at least 7 days
- [ ] All audit logs reviewed and approved
- [ ] Deletion counts are as expected
- [ ] No errors in recent audit logs
- [ ] Team has been notified of activation
- [ ] Rollback plan documented

### Activation
- [ ] Update `.env`: Set `CLEANER_DRY_RUN=false`
- [ ] Restart scheduled job / redeploy
- [ ] Verify configuration change took effect
- [ ] Wait for next scheduled run
- [ ] Monitor first destructive run closely

### Post-Activation Monitoring (Week 2)
- [ ] Day 1: Verify old data was actually deleted
- [ ] Day 1: Verify recent data was preserved
- [ ] Day 1: Check Redis keys were cleaned
- [ ] Day 1: Review audit log for errors
- [ ] Day 2-7: Daily audit log review
- [ ] Week 2: Verify storage usage is decreasing as expected

## Production Monitoring

### Daily Checks
- [ ] Review latest audit log
- [ ] Check for errors in audit log
- [ ] Verify deletion counts are within expected range
- [ ] Check health check status

### Weekly Checks
- [ ] Review all audit logs from past week
- [ ] Analyze deletion trends
- [ ] Verify storage usage trends
- [ ] Review any alerts or incidents
- [ ] Update documentation if needed

### Monthly Checks
- [ ] Review TTL configuration appropriateness
- [ ] Review schedule configuration
- [ ] Analyze long-term deletion trends
- [ ] Review and update alerts if needed
- [ ] Performance review of cleanup subsystem

## Alerting Setup

### Critical Alerts (Immediate Response)
- [ ] Cleanup job fails (exit code != 0)
- [ ] Health check status != "healthy"
- [ ] Errors in audit log > 10
- [ ] No cleanup run in last 48 hours

### Warning Alerts (Review Within 24h)
- [ ] Deletion count spike (>2x average)
- [ ] Deletion count drop (>50% below average)
- [ ] Errors in audit log > 0
- [ ] Health check response time > 5 seconds

### Alert Configuration
- [ ] Configure alert destinations (email, Slack, PagerDuty, etc.)
- [ ] Test each alert type
- [ ] Document alert response procedures
- [ ] Assign alert owners

## Scheduled Job Configuration

### Platform-Specific Setup
- [ ] Choose platform (Antigravity / Cron / Windows Task Scheduler / Kubernetes)
- [ ] Follow setup guide in `docs/scheduled_jobs.md`
- [ ] Configure job with correct schedule
- [ ] Set environment variables
- [ ] Configure IAM/permissions
- [ ] Test manual trigger
- [ ] Verify scheduled execution

### Permissions Verification
- [ ] Blob storage list permission on `uploads/`
- [ ] Blob storage delete permission on `uploads/`
- [ ] Blob storage list permission on `results/`
- [ ] Blob storage delete permission on `results/`
- [ ] Blob storage write permission on `maintenance/cleaner_runs/`
- [ ] Redis read permission on `job:*` keys
- [ ] Redis delete permission on `job:*` keys

## Documentation

### Internal Documentation
- [ ] Document TTL rationale and business requirements
- [ ] Document schedule rationale
- [ ] Document alert response procedures
- [ ] Document rollback procedures
- [ ] Document contact information for cleanup subsystem

### User Communication
- [ ] Inform users of data retention policy
- [ ] Update privacy policy if needed
- [ ] Update terms of service if needed
- [ ] Provide data export options if needed

## Rollback Plan

### If Issues Arise
- [ ] Document rollback procedure:
  1. Set `CLEANER_DRY_RUN=true` in `.env`
  2. Redeploy / restart scheduled job
  3. Verify dry-run mode is active
  4. Investigate issues
  5. Fix issues
  6. Re-test in dry-run mode
  7. Re-enable destructive mode when ready

### Emergency Disable
- [ ] Document emergency disable procedure:
  1. Disable scheduled job
  2. Verify job is no longer running
  3. Investigate issues
  4. Fix issues
  5. Re-enable when ready

## Performance Optimization

### If Cleanup Takes Too Long
- [ ] Reduce `CLEANER_MAX_DELETE_BATCH`
- [ ] Increase cleanup frequency (run more often)
- [ ] Optimize blob listing (if using real blob storage)
- [ ] Consider parallel processing (future enhancement)

### If Storage Not Decreasing
- [ ] Verify `CLEANER_DRY_RUN=false`
- [ ] Check TTL is appropriate
- [ ] Verify data is actually older than TTL
- [ ] Check for errors in audit logs
- [ ] Verify scheduled job is running

## Compliance & Privacy

### Data Retention Compliance
- [ ] Verify TTL meets regulatory requirements
- [ ] Document data retention policy
- [ ] Ensure audit logs are retained appropriately
- [ ] Verify data is actually being deleted

### Privacy Considerations
- [ ] Ensure PII is removed after TTL
- [ ] Verify audit logs don't contain PII
- [ ] Document data deletion process
- [ ] Provide data export options if needed

## Success Criteria

### Week 1 (Dry-Run)
- [ ] ✅ Scheduled job runs daily without errors
- [ ] ✅ Audit logs created for each run
- [ ] ✅ Deletion counts are reasonable and consistent
- [ ] ✅ Health check status is "healthy"
- [ ] ✅ No critical errors in logs

### Week 2 (Destructive Mode)
- [ ] ✅ Old data is actually being deleted
- [ ] ✅ Recent data is preserved
- [ ] ✅ Storage usage is decreasing
- [ ] ✅ No data loss incidents
- [ ] ✅ Audit logs show successful deletions

### Month 1 (Production)
- [ ] ✅ Cleanup runs reliably every day
- [ ] ✅ Storage usage is stable and predictable
- [ ] ✅ No incidents or data loss
- [ ] ✅ Alerts are working correctly
- [ ] ✅ Team is comfortable with the system

## Sign-Off

### Pre-Deployment
- [ ] Developer sign-off: ___________________ Date: ___________
- [ ] QA sign-off: ___________________ Date: ___________
- [ ] DevOps sign-off: ___________________ Date: ___________

### Post-Deployment (Week 1)
- [ ] Dry-run validation: ___________________ Date: ___________
- [ ] Ready for destructive mode: ___________________ Date: ___________

### Post-Deployment (Week 2)
- [ ] Destructive mode validation: ___________________ Date: ___________
- [ ] Production ready: ___________________ Date: ___________

---

**Deployment Status**: ⬜ Not Started | 🟡 In Progress | ✅ Complete

**Current Phase**: _______________________

**Notes**:
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________
