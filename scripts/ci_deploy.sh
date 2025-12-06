#!/bin/bash
# CI/CD Integration Script for DataPilot AI
# This script is designed to be called from CI/CD pipelines (GitHub Actions, GitLab CI, etc.)

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AUTO_ROLLBACK_ON_SMOKE_FAIL="${AUTO_ROLLBACK_ON_SMOKE_FAIL:-true}"
SMOKE_TEST_ON_DEPLOY="${SMOKE_TEST_ON_DEPLOY:-true}"

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

# Main CI/CD flow
main() {
    log_info "========================================="
    log_info "DataPilot AI - CI/CD Deployment"
    log_info "========================================="
    log_info ""
    log_info "Branch: ${CI_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"
    log_info "Commit: ${CI_COMMIT:-$(git rev-parse --short HEAD)}"
    log_info "Environment: ${ENVIRONMENT:-production}"
    log_info ""
    
    # Step 1: Deploy
    log_info "Step 1: Deploying to Antigravity..."
    if ! ./scripts/deploy_antigravity.sh; then
        log_error "Deployment failed!"
        exit 1
    fi
    
    # Step 2: Verify deployment
    log_info "Step 2: Verifying deployment..."
    if ! ./scripts/verify_deploy.sh; then
        log_error "Deployment verification failed!"
        
        if [ "$AUTO_ROLLBACK_ON_SMOKE_FAIL" = "true" ]; then
            log_warn "Auto-rollback enabled. Rolling back..."
            FORCE_ROLLBACK=1 ./scripts/rollback_antigravity.sh
        fi
        
        exit 1
    fi
    
    # Step 3: Run smoke tests (if enabled)
    if [ "$SMOKE_TEST_ON_DEPLOY" = "true" ]; then
        log_info "Step 3: Running smoke tests..."
        
        if ! ./scripts/run_smoke_tests.sh; then
            log_error "Smoke tests failed!"
            
            if [ "$AUTO_ROLLBACK_ON_SMOKE_FAIL" = "true" ]; then
                log_warn "Auto-rollback enabled. Rolling back..."
                FORCE_ROLLBACK=1 ./scripts/rollback_antigravity.sh
            fi
            
            exit 1
        fi
    else
        log_warn "Smoke tests disabled. Skipping..."
    fi
    
    # Step 4: Success
    log_info ""
    log_info "========================================="
    log_info "CI/CD Deployment Successful! ✓"
    log_info "========================================="
    log_info ""
    log_info "Deployment completed and verified."
    log_info "All smoke tests passed."
    log_info ""
    
    # Optional: Send notification
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"✅ DataPilot AI deployed successfully to ${ENVIRONMENT:-production}\"}"
    fi
}

# Run main function
cd "$PROJECT_ROOT"
main "$@"
