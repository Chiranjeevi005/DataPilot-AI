#!/bin/bash
# Deploy DataPilot AI to Antigravity
# This script validates configuration, pushes code, and deploys services

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

# Validate required environment variables
validate_env() {
    log_info "Validating required environment variables..."
    
    local required_vars=(
        "OPENROUTER_API_KEY"
        "REDIS_URL"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        else
            # Mask secret for logging
            local value="${!var}"
            local masked="${value:0:4}****${value: -4}"
            log_info "  ✓ $var is set ($masked)"
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            log_error "  - $var"
        done
        log_error ""
        log_error "Please set these variables in Antigravity Secret Manager or export them."
        log_error "Example: export OPENROUTER_API_KEY='your-key-here'"
        exit 1
    fi
    
    log_info "All required environment variables are set ✓"
}

# Validate project structure
validate_project() {
    log_info "Validating project structure..."
    
    local required_files=(
        "antigravity.yml"
        "requirements.txt"
        "src/worker.py"
        "src/api/upload/route.py"
        "src/api/health/route.py"
        "src/api/cancel/route.py"
    )
    
    cd "$PROJECT_ROOT"
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    log_info "Project structure validated ✓"
}

# Validate Python syntax
validate_python() {
    log_info "Validating Python syntax..."
    
    cd "$PROJECT_ROOT"
    
    # Check if Python is available
    if ! command -v python &> /dev/null; then
        log_error "Python not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Validate worker.py
    if ! python -m py_compile src/worker.py 2>/dev/null; then
        log_error "Syntax error in src/worker.py"
        exit 1
    fi
    
    log_info "Python syntax validated ✓"
}

# Create deployment tag
create_deployment_tag() {
    log_info "Creating deployment tag..."
    
    cd "$PROJECT_ROOT"
    
    # Get current timestamp
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local tag_name="deploy_${timestamp}"
    
    # Check if git is available and this is a git repo
    if command -v git &> /dev/null && [ -d ".git" ]; then
        # Get current commit hash
        local commit_hash=$(git rev-parse --short HEAD)
        
        # Create tag
        git tag -a "$tag_name" -m "Deployment at $timestamp (commit: $commit_hash)"
        
        log_info "Created deployment tag: $tag_name"
        echo "$tag_name" > .last_deploy_tag
    else
        log_warn "Git not available or not a git repository. Skipping tag creation."
    fi
}

# Deploy to Antigravity
deploy_to_antigravity() {
    log_info "Deploying to Antigravity..."
    
    cd "$PROJECT_ROOT"
    
    # Check if Antigravity CLI is available
    if command -v antigravity &> /dev/null; then
        log_info "Using Antigravity CLI..."
        
        # Deploy using CLI
        antigravity deploy \
            --config antigravity.yml \
            --env production \
            --wait
        
        log_info "Deployment initiated via Antigravity CLI ✓"
        
    elif [ -n "$ANTIGRAVITY_API_ENDPOINT" ] && [ -n "$ANTIGRAVITY_API_KEY" ]; then
        log_info "Using Antigravity API..."
        
        # Create deployment archive
        local archive_name="datapilot-ai-$(date +%Y%m%d_%H%M%S).tar.gz"
        
        tar -czf "/tmp/$archive_name" \
            --exclude='.git' \
            --exclude='.venv' \
            --exclude='node_modules' \
            --exclude='tmp_uploads' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.env' \
            .
        
        log_info "Created deployment archive: $archive_name"
        
        # Upload and deploy via API
        curl -X POST "$ANTIGRAVITY_API_ENDPOINT/deploy" \
            -H "Authorization: Bearer $ANTIGRAVITY_API_KEY" \
            -F "archive=@/tmp/$archive_name" \
            -F "config=@antigravity.yml" \
            -F "environment=production"
        
        # Clean up
        rm "/tmp/$archive_name"
        
        log_info "Deployment initiated via Antigravity API ✓"
        
    else
        log_error "Neither Antigravity CLI nor API credentials found."
        log_error "Please install Antigravity CLI or set ANTIGRAVITY_API_ENDPOINT and ANTIGRAVITY_API_KEY"
        exit 1
    fi
}

# Wait for deployment to complete
wait_for_deployment() {
    log_info "Waiting for deployment to complete..."
    
    local max_wait=300  # 5 minutes
    local elapsed=0
    local interval=10
    
    while [ $elapsed -lt $max_wait ]; do
        # Check health endpoint
        if curl -s -f http://localhost:5328/api/health > /dev/null 2>&1; then
            log_info "Deployment completed successfully ✓"
            return 0
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
        log_info "Waiting... ($elapsed/$max_wait seconds)"
    done
    
    log_error "Deployment timed out after $max_wait seconds"
    return 1
}

# Set secrets in Antigravity
set_secrets() {
    log_info "Setting secrets in Antigravity Secret Manager..."
    
    if command -v antigravity &> /dev/null; then
        # Set OPENROUTER_API_KEY
        if [ -n "$OPENROUTER_API_KEY" ]; then
            echo "$OPENROUTER_API_KEY" | antigravity secrets set OPENROUTER_API_KEY --stdin
            log_info "  ✓ Set OPENROUTER_API_KEY"
        fi
        
        # Set REDIS_URL
        if [ -n "$REDIS_URL" ]; then
            echo "$REDIS_URL" | antigravity secrets set REDIS_URL --stdin
            log_info "  ✓ Set REDIS_URL"
        fi
        
        # Set BLOB_KEY (if provided)
        if [ -n "$BLOB_KEY" ]; then
            echo "$BLOB_KEY" | antigravity secrets set BLOB_KEY --stdin
            log_info "  ✓ Set BLOB_KEY"
        fi
        
        # Set SENTRY_DSN (if provided)
        if [ -n "$SENTRY_DSN" ]; then
            echo "$SENTRY_DSN" | antigravity secrets set SENTRY_DSN --stdin
            log_info "  ✓ Set SENTRY_DSN"
        fi
        
        log_info "Secrets configured ✓"
    else
        log_warn "Antigravity CLI not available. Please set secrets manually via web console."
    fi
}

# Main deployment flow
main() {
    log_info "========================================="
    log_info "DataPilot AI - Antigravity Deployment"
    log_info "========================================="
    log_info ""
    
    # Step 1: Validate environment
    validate_env
    
    # Step 2: Validate project
    validate_project
    
    # Step 3: Validate Python syntax
    validate_python
    
    # Step 4: Create deployment tag
    create_deployment_tag
    
    # Step 5: Set secrets
    set_secrets
    
    # Step 6: Deploy to Antigravity
    deploy_to_antigravity
    
    # Step 7: Wait for deployment
    if wait_for_deployment; then
        log_info ""
        log_info "========================================="
        log_info "Deployment completed successfully! ✓"
        log_info "========================================="
        log_info ""
        log_info "Next steps:"
        log_info "  1. Run verification: ./scripts/verify_deploy.sh"
        log_info "  2. Run smoke tests: ./scripts/run_smoke_tests.sh"
        log_info ""
    else
        log_error ""
        log_error "========================================="
        log_error "Deployment failed!"
        log_error "========================================="
        log_error ""
        log_error "Troubleshooting:"
        log_error "  1. Check logs: antigravity logs --service api"
        log_error "  2. Check worker: antigravity logs --service worker"
        log_error "  3. Rollback: ./scripts/rollback_antigravity.sh"
        log_error ""
        exit 1
    fi
}

# Run main function
main "$@"
