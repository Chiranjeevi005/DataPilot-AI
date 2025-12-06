#!/bin/bash
# Test Phase 7: Job Timeout
# Tests server-side timeout enforcement

echo "=== Phase 7 Test: Job Timeout ==="
echo ""

# Check if Redis is running
echo "Checking Redis connection..."
redis-cli ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Redis is not running. Please start Redis first."
    exit 1
fi
echo "✓ Redis is running"
echo ""

# Set short timeout for testing
export JOB_TIMEOUT_SECONDS=10
export SIMULATED_SLOW_PROCESSING_SECONDS=15

echo "Configuration:"
echo "  JOB_TIMEOUT_SECONDS=$JOB_TIMEOUT_SECONDS"
echo "  SIMULATED_SLOW_PROCESSING_SECONDS=$SIMULATED_SLOW_PROCESSING_SECONDS"
echo ""
echo "Note: Job should timeout after 10 seconds, but processing would take 15 seconds"
echo ""

# Create test file
TEST_FILE="tmp_uploads/test_timeout.csv"
mkdir -p tmp_uploads
cat > "$TEST_FILE" << EOF
date,revenue,cost
2024-01-01,1000,500
2024-01-02,1200,600
2024-01-03,1100,550
2024-01-04,1300,650
2024-01-05,1250,625
EOF

echo "Created test file: $TEST_FILE"
echo ""

# Upload file
echo "Uploading file..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:5328/api/upload \
  -F "file=@$TEST_FILE")

JOB_ID=$(echo $JOB_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('jobId', ''))" 2>/dev/null)

if [ -z "$JOB_ID" ]; then
    echo "✗ Upload failed"
    echo "Response: $JOB_RESPONSE"
    exit 1
fi

echo "✓ Upload succeeded"
echo "  Job ID: $JOB_ID"
echo ""

# Check initial status
echo "Checking initial status..."
STATUS_RESPONSE=$(curl -s http://localhost:5328/api/job-status/$JOB_ID)
STATUS=$(echo $STATUS_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
TIMEOUT_AT=$(echo $STATUS_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('timeoutAt', ''))" 2>/dev/null)

echo "  Status: $STATUS"
echo "  Timeout at: $TIMEOUT_AT"
echo ""

# Monitor status over time
echo "Monitoring job status (checking every 3 seconds)..."
for i in {1..6}; do
    sleep 3
    
    STATUS_RESPONSE=$(curl -s http://localhost:5328/api/job-status/$JOB_ID)
    STATUS=$(echo $STATUS_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
    ERROR=$(echo $STATUS_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('error', ''))" 2>/dev/null)
    ERROR_MSG=$(echo $STATUS_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('errorMessage', ''))" 2>/dev/null)
    
    echo "  [${i}] Status: $STATUS"
    
    if [ "$STATUS" = "failed" ]; then
        echo "      Error: $ERROR"
        echo "      Message: $ERROR_MSG"
        
        if [ "$ERROR" = "timeout" ]; then
            echo ""
            echo "✓ Job correctly timed out"
            
            # Check for error.json
            RESULT_URL=$(echo $STATUS_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('resultUrl', ''))" 2>/dev/null)
            if [ ! -z "$RESULT_URL" ]; then
                echo "  Result URL (error.json): $RESULT_URL"
                
                if [[ $RESULT_URL == file://* ]]; then
                    FILE_PATH=$(echo $RESULT_URL | sed 's|file://||' | sed 's|^/||')
                    
                    if [ -f "$FILE_PATH" ]; then
                        echo ""
                        echo "error.json contents:"
                        cat "$FILE_PATH" | python -m json.tool 2>/dev/null || cat "$FILE_PATH"
                    fi
                fi
            fi
            
            break
        else
            echo "⚠ Job failed but not with timeout error"
        fi
        break
    elif [ "$STATUS" = "completed" ]; then
        echo ""
        echo "⚠ Job completed (timeout may not have been enforced)"
        break
    fi
done

echo ""

# Test 2: Check timeout enforcement by job-status endpoint
echo "Test 2: Timeout enforcement by job-status endpoint"
echo ""

# Create another job with short timeout
export JOB_TIMEOUT_SECONDS=5
export SIMULATED_SLOW_PROCESSING_SECONDS=0  # Don't slow down worker

TEST_FILE2="tmp_uploads/test_timeout2.csv"
cat > "$TEST_FILE2" << EOF
a,b,c
1,2,3
4,5,6
EOF

echo "Uploading file with 5-second timeout..."
JOB_RESPONSE2=$(curl -s -X POST http://localhost:5328/api/upload \
  -F "file=@$TEST_FILE2")

JOB_ID2=$(echo $JOB_RESPONSE2 | python -c "import sys, json; print(json.load(sys.stdin).get('jobId', ''))" 2>/dev/null)

if [ ! -z "$JOB_ID2" ]; then
    echo "✓ Upload succeeded: $JOB_ID2"
    
    # Manually set job to processing and wait past timeout
    echo "Simulating stuck processing job..."
    redis-cli SET "job:$JOB_ID2" "{\"jobId\":\"$JOB_ID2\",\"status\":\"processing\",\"timeoutAt\":\"$(date -u -d '+5 seconds' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v+5S +%Y-%m-%dT%H:%M:%SZ 2>/dev/null)\"}" > /dev/null
    
    echo "Waiting 7 seconds for timeout..."
    sleep 7
    
    echo "Checking status (should trigger timeout check)..."
    STATUS_RESPONSE2=$(curl -s http://localhost:5328/api/job-status/$JOB_ID2)
    STATUS2=$(echo $STATUS_RESPONSE2 | python -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
    ERROR2=$(echo $STATUS_RESPONSE2 | python -c "import sys, json; print(json.load(sys.stdin).get('error', ''))" 2>/dev/null)
    
    echo "  Status: $STATUS2"
    echo "  Error: $ERROR2"
    
    if [ "$STATUS2" = "failed" ] && [ "$ERROR2" = "timeout" ]; then
        echo "✓ job-status endpoint correctly enforced timeout"
    else
        echo "⚠ Timeout not enforced by job-status endpoint"
    fi
fi

echo ""

# Reset env
unset JOB_TIMEOUT_SECONDS
unset SIMULATED_SLOW_PROCESSING_SECONDS

echo "=== Test Complete ==="
echo ""
echo "Expected behavior:"
echo "  - Jobs exceeding JOB_TIMEOUT_SECONDS should be marked as failed"
echo "  - Error code should be 'timeout'"
echo "  - error.json should be created in blob storage"
echo "  - job-status endpoint should enforce timeout for stuck jobs"
echo ""
echo "Check worker logs for:"
echo "  'Job {id} has timed out'"
echo "  'Job {id} timed out during parsing/analysis'"
echo ""
