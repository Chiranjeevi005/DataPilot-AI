#!/bin/bash
# Verify Render Deployment (Smoke Test)
# Usage: ./scripts/verify_render.sh <HOST_URL>
# Example: ./scripts/verify_render.sh https://api-service.onrender.com

HOST=$1

if [ -z "$HOST" ]; then
    echo "Usage: $0 <HOST_URL>"
    echo "Example: $0 https://datapilot-api.onrender.com"
    exit 1
fi

echo "Starting Smoke Test against $HOST..."

# 1. Health Check
echo "[1/4] Checking Health..."
HEALTH_STATUS=$(curl -s "$HOST/api/health" | grep "ok")
if [[ -z "$HEALTH_STATUS" ]]; then
    echo "FAIL: Health check failed."
    curl -s "$HOST/api/health"
    exit 1
else
    echo "PASS: Health check ok."
fi

# 2. Upload Test (simulated)
# We need a small CSV file.
echo "[2/4] Testing Upload..."
TEST_FILE="dev-samples/sales_demo.csv"
if [ ! -f "$TEST_FILE" ]; then
    echo "Warning: $TEST_FILE not found, skipping upload test."
else
    UPLOAD_RES=$(curl -s -X POST -F "file=@$TEST_FILE" "$HOST/api/upload")
    JOB_ID=$(echo $UPLOAD_RES | grep -o '"jobId":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$JOB_ID" ]; then
        echo "FAIL: Upload failed. Response: $UPLOAD_RES"
        exit 1
    else
        echo "PASS: Upload successful. Job ID: $JOB_ID"
        
        # 3. Poll Status
        echo "[3/4] Polling Job Status..."
        STATUS="processing"
        ATTEMPTS=0
        MAX_ATTEMPTS=30
        
        while [[ "$STATUS" == "processing" || "$STATUS" == "submitted" ]] && [[ $ATTEMPTS -lt $MAX_ATTEMPTS ]]; do
            sleep 2
            STATUS_RES=$(curl -s "$HOST/api/job-status/$JOB_ID")
            STATUS=$(echo $STATUS_RES | grep -o '"status":"[^"]*' | cut -d'"' -f4)
            echo "Status: $STATUS"
            ATTEMPTS=$((ATTEMPTS+1))
        done
        
        if [[ "$STATUS" == "completed" ]]; then
            echo "PASS: Job completed."
            
            # 4. Fetch Results
            echo "[4/4] Fetching Results..."
            RESULTS=$(curl -s "$HOST/api/results/$JOB_ID")
            # Simple check for KPIs key
            if echo "$RESULTS" | grep -q "kpis"; then
                echo "PASS: Results contain KPIs."
                echo "SMOKE TEST PASSED!"
                mkdir -p reports
                echo "$RESULTS" > "reports/smoke_report_$(date +%s).json"
            else
                echo "FAIL: Results missing KPIs."
                echo "Sample: ${RESULTS:0:100}..."
                exit 1
            fi
        else
            echo "FAIL: Job did not complete. Final status: $STATUS"
            exit 1
        fi
    fi
fi
