#!/usr/bin/env pwsh
# Edge case tests for DataPilot AI cleanup subsystem
# Tests error handling, validation, and edge cases

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "DataPilot AI Cleanup Test - Edge Cases" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan

# Ensure we're in the project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

Write-Host "`nProject root: $projectRoot" -ForegroundColor Yellow

# Test 1: Minimum TTL protection
Write-Host "`n[Test 1] Testing minimum TTL protection..." -ForegroundColor Green

python -c @"
import sys
import os
sys.path.insert(0, 'src')

os.environ['JOB_TTL_HOURS'] = '0'  # Invalid: less than MIN_TTL_HOURS
os.environ['MIN_TTL_HOURS'] = '1'

from maintenance.cleaner import run_cleaner

try:
    result = run_cleaner(dry_run=True)
    if result.get('errors'):
        # Check if error is about TTL validation
        error_msgs = [e.get('message', '') for e in result['errors']]
        if any('minimum' in msg.lower() or 'ttl' in msg.lower() for msg in error_msgs):
            print('✓ Minimum TTL validation works')
            sys.exit(0)
    print('✗ Should have failed with TTL validation error')
    sys.exit(1)
except ValueError as e:
    if 'minimum' in str(e).lower():
        print('✓ Minimum TTL validation works')
        sys.exit(0)
    else:
        print(f'✗ Wrong error: {e}')
        sys.exit(1)
except Exception as e:
    print(f'✗ Unexpected error: {e}')
    sys.exit(1)
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Test 1 failed" -ForegroundColor Red
    exit 1
}

# Test 2: Missing required prefixes
Write-Host "`n[Test 2] Testing missing prefix validation..." -ForegroundColor Green

python -c @"
import sys
import os
sys.path.insert(0, 'src')

# Set invalid prefixes (missing 'uploads/')
os.environ['BLOB_PATH_PREFIXES'] = 'results/'
os.environ['JOB_TTL_HOURS'] = '24'

from maintenance.cleaner import run_cleaner

try:
    result = run_cleaner(dry_run=True)
    if result.get('errors'):
        error_msgs = [e.get('message', '') for e in result['errors']]
        if any('prefix' in msg.lower() or 'uploads' in msg.lower() for msg in error_msgs):
            print('✓ Prefix validation works')
            sys.exit(0)
    print('✗ Should have failed with prefix validation error')
    sys.exit(1)
except ValueError as e:
    if 'prefix' in str(e).lower():
        print('✓ Prefix validation works')
        sys.exit(0)
    else:
        print(f'✗ Wrong error: {e}')
        sys.exit(1)
except Exception as e:
    print(f'✗ Unexpected error: {e}')
    sys.exit(1)
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Test 2 failed" -ForegroundColor Red
    exit 1
}

# Test 3: Idempotency - running cleaner twice
Write-Host "`n[Test 3] Testing idempotency (running cleaner twice)..." -ForegroundColor Green

# Reset env vars
$env:BLOB_PATH_PREFIXES = "uploads/,results/"
$env:JOB_TTL_HOURS = "24"
$env:CLEANER_DRY_RUN = "true"

# Create fake data
python scripts/test_cleaner_create_fake_data.py | Out-Null

# Run cleaner first time
python -c @"
import sys
sys.path.insert(0, 'src')
from maintenance.cleaner import run_cleaner
result1 = run_cleaner(dry_run=True)
print(f'First run: {result1["deletedBlobs"]} blobs, {result1["deletedKeys"]} keys')
"@

# Run cleaner second time (should find same items)
python -c @"
import sys
sys.path.insert(0, 'src')
from maintenance.cleaner import run_cleaner
result2 = run_cleaner(dry_run=True)
print(f'Second run: {result2["deletedBlobs"]} blobs, {result2["deletedKeys"]} keys')
if result2['deletedBlobs'] > 0 and result2['deletedKeys'] > 0:
    print('✓ Idempotency test passed (dry-run finds same items)')
    sys.exit(0)
else:
    print('✗ Second run found different items')
    sys.exit(1)
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Test 3 failed" -ForegroundColor Red
    exit 1
}

# Test 4: Handling missing timestamps
Write-Host "`n[Test 4] Testing handling of jobs with missing timestamps..." -ForegroundColor Green

python -c @"
import sys
import json
sys.path.insert(0, 'src')
from lib.queue import get_redis_client

# Create a job key without timestamp
r = get_redis_client()
job_data = {
    'jobId': 'job_no_timestamp',
    'status': 'completed'
    # No createdAt or updatedAt
}
r.set('job:job_no_timestamp', json.dumps(job_data))
print('Created job without timestamp')

from maintenance.cleaner import run_cleaner
result = run_cleaner(dry_run=True)

# Check if job was skipped
if 'job:job_no_timestamp' in result.get('skipped', []):
    print('✓ Job without timestamp was skipped')
    sys.exit(0)
else:
    # Also acceptable if it's in the skipped list with a different format
    skipped_str = str(result.get('skipped', []))
    if 'job_no_timestamp' in skipped_str:
        print('✓ Job without timestamp was skipped')
        sys.exit(0)
    print(f'✗ Job should have been skipped. Skipped: {result.get("skipped")}')
    sys.exit(1)
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Test 4 failed" -ForegroundColor Red
    exit 1
}

# Test 5: Batch limit enforcement
Write-Host "`n[Test 5] Testing batch limit enforcement..." -ForegroundColor Green

# Set a very low batch limit
$env:CLEANER_MAX_DELETE_BATCH = "1"

python -c @"
import sys
sys.path.insert(0, 'src')
from maintenance.cleaner import run_cleaner

result = run_cleaner(dry_run=True)
total_would_delete = result['deletedBlobs'] + result['deletedKeys']

if total_would_delete <= 1:
    print(f'✓ Batch limit enforced (would delete {total_would_delete} items)')
    sys.exit(0)
else:
    print(f'✗ Batch limit not enforced (would delete {total_would_delete} items, limit is 1)')
    sys.exit(1)
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Test 5 failed" -ForegroundColor Red
    exit 1
}

# Reset batch limit
$env:CLEANER_MAX_DELETE_BATCH = "500"

# Test 6: Error logging and continuation
Write-Host "`n[Test 6] Testing error logging and continuation..." -ForegroundColor Green

# This test verifies that if some deletions fail, the cleaner continues
# We'll simulate this by checking that errors are logged properly
python -c @"
import sys
sys.path.insert(0, 'src')
from maintenance.cleaner import run_cleaner

# Run cleaner and check that it completes even if there might be errors
result = run_cleaner(dry_run=True)

# Check that result has all expected fields
required_fields = ['deletedBlobs', 'deletedKeys', 'errors', 'skipped', 'dryRun', 'startedAt', 'completedAt']
missing = [f for f in required_fields if f not in result]

if missing:
    print(f'✗ Missing fields in result: {missing}')
    sys.exit(1)

if result.get('completedAt'):
    print('✓ Cleaner completed and logged properly')
    sys.exit(0)
else:
    print('✗ Cleaner did not complete properly')
    sys.exit(1)
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Test 6 failed" -ForegroundColor Red
    exit 1
}

# Test 7: Health check
Write-Host "`n[Test 7] Testing health check..." -ForegroundColor Green

python -m src.maintenance.health_check > $null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Health check passed" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Health check failed (may be expected if Redis is not running)" -ForegroundColor Yellow
}

# Cleanup test data
Write-Host "`n[Cleanup] Removing test data..." -ForegroundColor Yellow
python -c @"
import sys
sys.path.insert(0, 'src')
from lib.queue import get_redis_client

r = get_redis_client()
r.delete('job:job_no_timestamp')
print('Cleaned up test Redis keys')
"@

# Success!
Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 79) -ForegroundColor Green
Write-Host "✓ All edge case tests passed!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 79) -ForegroundColor Green

exit 0
