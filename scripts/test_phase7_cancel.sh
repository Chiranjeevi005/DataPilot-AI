#!/bin/bash
# Test Phase 7: Job Cancellation
# Tests job cancellation endpoint and worker behavior

echo "=== Phase 7 Test: Job Cancellation ==="
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

# Create a larger test file to ensure processing takes some time
TEST_FILE="tmp_uploads/test_cancel.csv"
mkdir -p tmp_uploads

echo "Creating test file with more data..."
cat > "$TEST_FILE" << EOF
date,revenue,cost,profit,region,product
EOF

# Add 1000 rows
for i in {1..1000}; do
    echo "2024-01-$(printf "%02d" $((i % 28 + 1))),$(($RANDOM % 5000 + 1000)),$(($RANDOM % 2500 + 500)),$(($RANDOM % 2500)),Region$((i % 5)),Product$((i % 10))" >> "$TEST_FILE"
done

echo "✓ Created test file with 1000 rows"
echo ""

# Test 1: Cancel job before processing
echo "Test 1: Cancel job before processing starts"
echo "Uploading file..."

JOB_RESPONSE=$(curl -s -X POST http://localhost:5328/api/upload \
  -F "file=@$TEST_FILE")

JOB_ID=$(echo $JOB_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('jobId', ''))" 2>/dev/null)

if [ -z "$JOB_ID" ]; then
    echo "✗ Upload failed"
    exit 1
fi

echo "✓ Upload succeeded: $JOB_ID"

# Immediately cancel
echo "Cancelling job immediately..."
CANCEL_RESPONSE=$(curl -s -X POST "http://localhost:5328/api/cancel?jobId=$JOB_ID")
CANCEL_STATUS=$(echo $CANCEL_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)

echo "  Cancel response status: $CANCEL_STATUS"

if [ "$CANCEL_STATUS" = "cancelled" ]; then
    echo "✓ Job cancelled successfully"
else
    echo "✗ Cancellation failed"
    echo "  Response: $CANCEL_RESPONSE"
fi

# Wait a bit and check status
sleep 3
STATUS=$(curl -s http://localhost:5328/api/job-status/$JOB_ID | python -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
echo "  Final status: $STATUS"

if [ "$STATUS" = "cancelled" ]; then
    echo "✓ Job remains cancelled"
else
    echo "⚠ Status changed to: $STATUS"
fi

echo ""

# Test 2: Cancel job during processing (if worker is slow enough)
echo "Test 2: Cancel job during processing"

# Set slow processing for testing
export SIMULATED_SLOW_PROCESSING_SECONDS=5

echo "Uploading second file..."
JOB_RESPONSE2=$(curl -s -X POST http://localhost:5328/api/upload \
  -F "file=@$TEST_FILE")

JOB_ID2=$(echo $JOB_RESPONSE2 | python -c "import sys, json; print(json.load(sys.stdin).get('jobId', ''))" 2>/dev/null)

if [ -z "$JOB_ID2" ]; then
    echo "✗ Upload failed"
else
    echo "✓ Upload succeeded: $JOB_ID2"
    
    # Wait for processing to start
    echo "Waiting for processing to start..."
    sleep 2
    
    # Cancel while processing
    echo "Cancelling job during processing..."
    CANCEL_RESPONSE2=$(curl -s -X POST "http://localhost:5328/api/cancel?jobId=$JOB_ID2")
    CANCEL_STATUS2=$(echo $CANCEL_RESPONSE2 | python -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
    
    echo "  Cancel response: $CANCEL_STATUS2"
    
    # Wait and check final status
    sleep 3
    STATUS2=$(curl -s http://localhost:5328/api/job-status/$JOB_ID2 | python -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
    echo "  Final status: $STATUS2"
    
    if [ "$STATUS2" = "cancelled" ]; then
        echo "✓ Job was cancelled during processing"
    else
        echo "⚠ Job status: $STATUS2 (worker may have completed before cancellation)"
    fi
fi

echo ""

# Test 3: Try to cancel already completed job
echo "Test 3: Try to cancel already completed job"

# Create small file for quick completion
SMALL_FILE="tmp_uploads/test_small.csv"
cat > "$SMALL_FILE" << EOF
a,b
1,2
3,4
EOF

echo "Uploading small file..."
JOB_RESPONSE3=$(curl -s -X POST http://localhost:5328/api/upload \
  -F "file=@$SMALL_FILE")

JOB_ID3=$(echo $JOB_RESPONSE3 | python -c "import sys, json; print(json.load(sys.stdin).get('jobId', ''))" 2>/dev/null)

if [ ! -z "$JOB_ID3" ]; then
    echo "✓ Upload succeeded: $JOB_ID3"
    
    # Wait for completion
    echo "Waiting for job to complete..."
    sleep 5
    
    STATUS3=$(curl -s http://localhost:5328/api/job-status/$JOB_ID3 | python -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
    echo "  Job status: $STATUS3"
    
    if [ "$STATUS3" = "completed" ]; then
        echo "Attempting to cancel completed job..."
        CANCEL_RESPONSE3=$(curl -s -X POST "http://localhost:5328/api/cancel?jobId=$JOB_ID3")
        ERROR=$(echo $CANCEL_RESPONSE3 | python -c "import sys, json; print(json.load(sys.stdin).get('error', ''))" 2>/dev/null)
        
        if [[ $ERROR == *"Cannot cancel"* ]]; then
            echo "✓ Correctly rejected cancellation of completed job"
        else
            echo "⚠ Unexpected response: $CANCEL_RESPONSE3"
        fi
    fi
fi

echo ""

# Reset env
unset SIMULATED_SLOW_PROCESSING_SECONDS

echo "=== Test Complete ==="
echo ""
echo "Expected behavior:"
echo "  - Cancelled jobs should not produce result.json"
echo "  - Worker should detect cancellation and exit gracefully"
echo "  - Cannot cancel already completed/failed jobs"
echo ""
echo "Check worker logs for:"
echo "  'Job {id} was cancelled. Skipping.'"
echo "  'Job {id} was cancelled during processing.'"
echo ""
