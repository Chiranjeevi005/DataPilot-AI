#!/bin/bash
# Rollback DataPilot AI deployment on Antigravity
# This script reverts to the previous successful deployment

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Get previous deployment tag
get_previous_tag() {
    cd "$PROJECT_ROOT"
    
    if [ -f ".last_deploy_tag" ]; then
        local last_tag=$(cat .last_deploy_tag)
        log_info "Last deployment tag: $last_tag"
        
        # Get tag before last
        if command -v git &> /dev/null && [ -d ".git" ]; then
            local tags=$(git tag -l "deploy_*" --sort=-creatordate)
            local previous_tag=$(echo "$tags" | sed -n '2p')
            
            if [ -n "$previous_tag" ]; then
                echo "$previous_tag"
                return 0
            fi
        fi
    fi
    
    log_warn "No previous deployment tag found"
    return 1
}

# Rollback using Antigravity CLI
rollback_cli() {
    local target_tag="$1"
    
    log_info "Rolling back to tag: $target_tag"
    
    cd "$PROJECT_ROOT"
    
    if command -v git &> /dev/null && [ -d ".git" ]; then
        # Checkout previous tag
        git checkout "$target_tag"
        
        # Deploy previous version
        if command -v antigravity &> /dev/null; then
            antigravity deploy \
                --config antigravity.yml \
                --env production \
                --wait
            
            log_info "Rollback completed via Antigravity CLI ✓"
            return 0
        fi
    fi
    
    return 1
}

# Rollback using Antigravity API
rollback_api() {
    local target_version="$1"
    
    log_info "Rolling back to version: $target_version"
    
    if [ -n "$ANTIGRAVITY_API_ENDPOINT" ] && [ -n "$ANTIGRAVITY_API_KEY" ]; then
        curl -X POST "$ANTIGRAVITY_API_ENDPOINT/rollback" \
            -H "Authorization: Bearer $ANTIGRAVITY_API_KEY" \
            -H "Content-Type: application/json" \
            -d "{\"version\": \"$target_version\"}"
        
        log_info "Rollback initiated via Antigravity API ✓"
        return 0
    fi
    
    return 1
}

# Verify rollback
verify_rollback() {
    log_info "Verifying rollback..."
    
    # Wait a bit for services to restart
    sleep 10
    
    # Check health endpoint
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f http://localhost:5328/api/health > /dev/null 2>&1; then
            log_info "Health check passed ✓"
            return 0
        fi
        
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Health check failed after rollback"
    return 1
}

# Main rollback flow
main() {
    log_info "========================================="
    log_info "DataPilot AI - Rollback Deployment"
    log_info "========================================="
    log_info ""
    
    # Confirm rollback
    if [ -z "$FORCE_ROLLBACK" ]; then
        read -p "Are you sure you want to rollback? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log_info "Rollback cancelled."
            exit 0
        fi
    fi
    
    # Get previous tag
    local previous_tag
    if previous_tag=$(get_previous_tag); then
        log_info "Found previous deployment: $previous_tag"
    else
        log_error "Cannot determine previous deployment version"
        log_error "Please specify version manually: ROLLBACK_VERSION=deploy_20241206_120000 $0"
        exit 1
    fi
    
    # Use manual version if specified
    if [ -n "$ROLLBACK_VERSION" ]; then
        previous_tag="$ROLLBACK_VERSION"
        log_info "Using manually specified version: $previous_tag"
    fi
    
    # Attempt rollback via CLI
    if rollback_cli "$previous_tag"; then
        log_info "Rollback via CLI successful"
    # Attempt rollback via API
    elif rollback_api "$previous_tag"; then
        log_info "Rollback via API successful"
    else
        log_error "Rollback failed - neither CLI nor API available"
        exit 1
    fi
    
    # Verify rollback
    if verify_rollback; then
        log_info ""
        log_info "========================================="
        log_info "Rollback completed successfully! ✓"
        log_info "========================================="
        log_info ""
        log_info "Rolled back to: $previous_tag"
        log_info ""
    else
        log_error ""
        log_error "========================================="
        log_error "Rollback verification failed!"
        log_error "========================================="
        log_error ""
        log_error "Please check logs and investigate manually."
        exit 1
    fi
}

# Run main function
main "$@"
