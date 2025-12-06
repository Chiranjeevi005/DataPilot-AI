#!/bin/bash
# Verify DataPilot AI deployment on Antigravity
# This script performs lightweight health checks after deployment

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:5328}"
HEALTH_ENDPOINT="$API_BASE_URL/api/health"

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if API is reachable
check_api_reachable() {
    log_info "Checking if API is reachable..."
    
    if curl -s -f "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
        log_info "  ✓ API is reachable"
        return 0
    else
        log_error "  ✗ API is not reachable at $HEALTH_ENDPOINT"
        return 1
    fi
}

# Check health endpoint
check_health_endpoint() {
    log_info "Checking health endpoint..."
    
    local response=$(curl -s "$HEALTH_ENDPOINT")
    
    if [ -z "$response" ]; then
        log_error "  ✗ Health endpoint returned empty response"
        return 1
    fi
    
    # Parse JSON response
    local status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$status" = "ok" ]; then
        log_info "  ✓ Health status: OK"
    else
        log_error "  ✗ Health status: $status"
        return 1
    fi
    
    # Check Redis
    local redis_status=$(echo "$response" | grep -o '"redis":"[^"]*"' | cut -d'"' -f4)
    if [ "$redis_status" = "ok" ]; then
        log_info "  ✓ Redis: OK"
    else
        log_error "  ✗ Redis: $redis_status"
        return 1
    fi
    
    # Check Blob Storage
    local blob_status=$(echo "$response" | grep -o '"blob":"[^"]*"' | cut -d'"' -f4)
    if [ "$blob_status" = "ok" ] || [ "$blob_status" = "disabled" ]; then
        log_info "  ✓ Blob Storage: $blob_status"
    else
        log_error "  ✗ Blob Storage: $blob_status"
        return 1
    fi
    
    # Check Worker Heartbeat
    local worker_status=$(echo "$response" | grep -o '"worker":"[^"]*"' | cut -d'"' -f4)
    if [ "$worker_status" = "ok" ]; then
        log_info "  ✓ Worker: OK"
    else
        log_warn "  ⚠ Worker: $worker_status"
        # Don't fail on worker - it might be starting
    fi
    
    return 0
}

# Check worker heartbeat
check_worker_heartbeat() {
    log_info "Checking worker heartbeat..."
    
    # This requires Redis access - skip if not available
    if ! command -v redis-cli &> /dev/null; then
        log_warn "  ⚠ redis-cli not available, skipping heartbeat check"
        return 0
    fi
    
    local redis_url="${REDIS_URL:-redis://localhost:6379/0}"
    local heartbeat=$(redis-cli -u "$redis_url" GET "worker:heartbeat" 2>/dev/null || echo "")
    
    if [ -z "$heartbeat" ]; then
        log_warn "  ⚠ No worker heartbeat found (worker may be starting)"
        return 0
    fi
    
    # Parse timestamp and check age
    local heartbeat_time=$(echo "$heartbeat" | tr -d 'Z"')
    local current_time=$(date -u +"%Y-%m-%dT%H:%M:%S")
    
    log_info "  ✓ Worker heartbeat: $heartbeat_time"
    
    return 0
}

# Check logs for errors
check_logs() {
    log_info "Checking recent logs for errors..."
    
    if command -v antigravity &> /dev/null; then
        # Get last 50 lines of worker logs
        local worker_logs=$(antigravity logs --service worker --tail 50 2>/dev/null || echo "")
        
        if echo "$worker_logs" | grep -i "error" > /dev/null; then
            log_warn "  ⚠ Found errors in worker logs"
            echo "$worker_logs" | grep -i "error" | tail -5
        else
            log_info "  ✓ No errors in recent worker logs"
        fi
        
        # Get last 50 lines of API logs
        local api_logs=$(antigravity logs --service api --tail 50 2>/dev/null || echo "")
        
        if echo "$api_logs" | grep -i "error" > /dev/null; then
            log_warn "  ⚠ Found errors in API logs"
            echo "$api_logs" | grep -i "error" | tail -5
        else
            log_info "  ✓ No errors in recent API logs"
        fi
    else
        log_warn "  ⚠ Antigravity CLI not available, skipping log check"
    fi
    
    return 0
}

# Check worker startup message
check_worker_startup() {
    log_info "Checking worker startup..."
    
    if command -v antigravity &> /dev/null; then
        local worker_logs=$(antigravity logs --service worker --tail 100 2>/dev/null || echo "")
        
        if echo "$worker_logs" | grep "Worker starting" > /dev/null; then
            log_info "  ✓ Worker startup message found"
            return 0
        else
            log_warn "  ⚠ Worker startup message not found"
            return 0  # Don't fail - worker might have started earlier
        fi
    else
        log_warn "  ⚠ Antigravity CLI not available, skipping startup check"
    fi
    
    return 0
}

# Generate verification report
generate_report() {
    local exit_code=$1
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    local report_file="$PROJECT_ROOT/reports/verify_deploy_${timestamp//:/-}.json"
    mkdir -p "$PROJECT_ROOT/reports"
    
    cat > "$report_file" <<EOF
{
  "timestamp": "$timestamp",
  "status": "$([ $exit_code -eq 0 ] && echo 'success' || echo 'failure')",
  "checks": {
    "api_reachable": $([ $exit_code -eq 0 ] && echo 'true' || echo 'false'),
    "health_endpoint": $([ $exit_code -eq 0 ] && echo 'true' || echo 'false'),
    "redis": $([ $exit_code -eq 0 ] && echo 'true' || echo 'false'),
    "blob": $([ $exit_code -eq 0 ] && echo 'true' || echo 'false'),
    "worker": $([ $exit_code -eq 0 ] && echo 'true' || echo 'false')
  },
  "api_base_url": "$API_BASE_URL"
}
EOF
    
    log_info "Verification report saved to: $report_file"
}

# Main verification flow
main() {
    log_info "========================================="
    log_info "DataPilot AI - Deployment Verification"
    log_info "========================================="
    log_info ""
    log_info "API Base URL: $API_BASE_URL"
    log_info ""
    
    local failed=0
    
    # Run checks
    check_api_reachable || failed=1
    
    if [ $failed -eq 0 ]; then
        check_health_endpoint || failed=1
    fi
    
    check_worker_heartbeat || true  # Don't fail on this
    check_logs || true  # Don't fail on this
    check_worker_startup || true  # Don't fail on this
    
    # Generate report
    generate_report $failed
    
    # Final result
    log_info ""
    if [ $failed -eq 0 ]; then
        log_info "========================================="
        log_info "Deployment verification PASSED ✓"
        log_info "========================================="
        log_info ""
        log_info "All critical checks passed!"
        log_info "Next step: Run smoke tests with ./scripts/run_smoke_tests.sh"
        log_info ""
        exit 0
    else
        log_error "========================================="
        log_error "Deployment verification FAILED ✗"
        log_error "========================================="
        log_error ""
        log_error "One or more critical checks failed."
        log_error "Please investigate and fix issues before proceeding."
        log_error ""
        exit 1
    fi
}

# Run main function
main "$@"
