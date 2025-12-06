#!/usr/bin/env pwsh
# Test script for DataPilot AI cleanup subsystem
# Tests both dry-run and actual deletion modes

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "DataPilot AI Cleanup Test - Running Cleaner" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan

# Ensure we're in the project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

Write-Host "`nProject root: $projectRoot" -ForegroundColor Yellow

# Step 1: Create fake data
Write-Host "`n[Step 1] Creating fake test data..." -ForegroundColor Green
python scripts/test_cleaner_create_fake_data.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to create fake data" -ForegroundColor Red
    exit 1
}

# Step 2: Run cleaner in dry-run mode
Write-Host "`n[Step 2] Running cleaner in DRY RUN mode..." -ForegroundColor Green
$env:CLEANER_DRY_RUN = "true"
python -m src.maintenance.cron_entry
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Dry run failed" -ForegroundColor Red
    exit 1
}

# Step 3: Verify that nothing was actually deleted in dry-run
Write-Host "`n[Step 3] Verifying dry-run didn't delete anything..." -ForegroundColor Green

# Determine base directory
$baseDir = $env:LOCAL_STORAGE_ROOT
if (-not $baseDir) {
    if ($IsWindows -or $env:OS -match "Windows") {
        $baseDir = Join-Path $projectRoot "tmp_uploads"
    } else {
        $baseDir = "/tmp/uploads"
    }
}

$oldUpload = Join-Path $baseDir "uploads\job_old\test_data.csv"
$oldResult = Join-Path $baseDir "results\job_old.json"

if ((Test-Path $oldUpload) -and (Test-Path $oldResult)) {
    Write-Host "  ✓ Old files still exist (dry-run worked correctly)" -ForegroundColor Green
} else {
    Write-Host "  ✗ Old files were deleted in dry-run mode (ERROR!)" -ForegroundColor Red
    exit 1
}

# Step 4: Run cleaner in destructive mode
Write-Host "`n[Step 4] Running cleaner in DESTRUCTIVE mode..." -ForegroundColor Green
$env:CLEANER_DRY_RUN = "false"
python -m src.maintenance.cron_entry
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Destructive run failed" -ForegroundColor Red
    exit 1
}

# Step 5: Verify that old files were deleted
Write-Host "`n[Step 5] Verifying old files were deleted..." -ForegroundColor Green

$oldDeleted = $true
if (Test-Path $oldUpload) {
    Write-Host "  ✗ Old upload still exists: $oldUpload" -ForegroundColor Red
    $oldDeleted = $false
}
if (Test-Path $oldResult) {
    Write-Host "  ✗ Old result still exists: $oldResult" -ForegroundColor Red
    $oldDeleted = $false
}

if ($oldDeleted) {
    Write-Host "  ✓ Old files were deleted" -ForegroundColor Green
} else {
    Write-Host "  ✗ Some old files were not deleted" -ForegroundColor Red
    exit 1
}

# Step 6: Verify that recent files were NOT deleted
Write-Host "`n[Step 6] Verifying recent files were preserved..." -ForegroundColor Green

$recentUpload = Join-Path $baseDir "uploads\job_recent\test_data.csv"
$recentResult = Join-Path $baseDir "results\job_recent.json"

$recentPreserved = $true
if (-not (Test-Path $recentUpload)) {
    Write-Host "  ✗ Recent upload was deleted: $recentUpload" -ForegroundColor Red
    $recentPreserved = $false
}
if (-not (Test-Path $recentResult)) {
    Write-Host "  ✗ Recent result was deleted: $recentResult" -ForegroundColor Red
    $recentPreserved = $false
}

if ($recentPreserved) {
    Write-Host "  ✓ Recent files were preserved" -ForegroundColor Green
} else {
    Write-Host "  ✗ Some recent files were incorrectly deleted" -ForegroundColor Red
    exit 1
}

# Step 7: Verify Redis keys
Write-Host "`n[Step 7] Verifying Redis key cleanup..." -ForegroundColor Green

# Check if old key was deleted and recent key preserved
python -c @"
import sys
sys.path.insert(0, 'src')
from lib.queue import get_redis_client

r = get_redis_client()
old_exists = r.exists('job:job_old')
recent_exists = r.exists('job:job_recent')

if old_exists:
    print('  ✗ Old Redis key still exists')
    sys.exit(1)
else:
    print('  ✓ Old Redis key was deleted')

if recent_exists:
    print('  ✓ Recent Redis key was preserved')
else:
    print('  ✗ Recent Redis key was deleted')
    sys.exit(1)
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Redis key verification failed" -ForegroundColor Red
    exit 1
}

# Step 8: Check audit log
Write-Host "`n[Step 8] Checking audit log..." -ForegroundColor Green

$auditDir = Join-Path $baseDir "maintenance\cleaner_runs"
if (Test-Path $auditDir) {
    $auditFiles = Get-ChildItem -Path $auditDir -Filter "cleaner_*.json" | Sort-Object LastWriteTime -Descending
    if ($auditFiles.Count -gt 0) {
        $latestAudit = $auditFiles[0]
        Write-Host "  ✓ Audit log found: $($latestAudit.Name)" -ForegroundColor Green
        
        # Display audit summary
        $auditContent = Get-Content $latestAudit.FullName | ConvertFrom-Json
        Write-Host "    - Deleted Blobs: $($auditContent.deletedBlobs)" -ForegroundColor Cyan
        Write-Host "    - Deleted Keys: $($auditContent.deletedKeys)" -ForegroundColor Cyan
        Write-Host "    - Errors: $($auditContent.errors.Count)" -ForegroundColor Cyan
    } else {
        Write-Host "  ✗ No audit files found" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ✗ Audit directory not found" -ForegroundColor Red
    exit 1
}

# Success!
Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 79) -ForegroundColor Green
Write-Host "✓ All cleanup tests passed successfully!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 79) -ForegroundColor Green

exit 0
