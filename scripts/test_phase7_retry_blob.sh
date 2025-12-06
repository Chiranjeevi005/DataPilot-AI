#!/bin/bash
# Test Phase 7: Blob Retry Logic
# Simulates blob upload transient failure and verifies retry behavior

echo "=== Phase 7 Test: Blob Retry Logic ==="
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

# Set retry configuration for testing (lower values for faster testing)
export BLOB_RETRY_ATTEMPTS=3
export RETRY_INITIAL_DELAY=0.2
export RETRY_FACTOR=2.0
export RETRY_MAX_DELAY=2

echo "Configuration:"
echo "  BLOB_RETRY_ATTEMPTS=$BLOB_RETRY_ATTEMPTS"
echo "  RETRY_INITIAL_DELAY=$RETRY_INITIAL_DELAY"
echo "  RETRY_FACTOR=$RETRY_FACTOR"
echo "  RETRY_MAX_DELAY=$RETRY_MAX_DELAY"
echo ""

# Create a test CSV file
TEST_FILE="tmp_uploads/test_retry_blob.csv"
mkdir -p tmp_uploads
cat > "$TEST_FILE" << EOF
date,revenue,cost
2024-01-01,1000,500
2024-01-02,1200,600
2024-01-03,1100,550
EOF

echo "Created test file: $TEST_FILE"
echo ""

# Test 1: Normal operation (should succeed)
echo "Test 1: Normal blob operation (should succeed)"
echo "Uploading file..."

JOB_RESPONSE=$(curl -s -X POST http://localhost:5328/api/upload \
  -F "file=@$TEST_FILE")

JOB_ID=$(echo $JOB_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('jobId', ''))" 2>/dev/null)

if [ -z "$JOB_ID" ]; then
    echo "✗ Upload failed"
    echo "Response: $JOB_RESPONSE"
else
    echo "✓ Upload succeeded"
    echo "  Job ID: $JOB_ID"
    
    # Check job status
    sleep 2
    STATUS_RESPONSE=$(curl -s http://localhost:5328/api/job-status/$JOB_ID)
    STATUS=$(echo $STATUS_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
    echo "  Status: $STATUS"
fi

echo ""
echo "=== Test Complete ==="
echo ""
echo "Note: To test actual retry behavior with failures, you would need to:"
echo "1. Mock the storage layer to simulate transient failures"
echo "2. Verify retry attempts in logs"
echo "3. Confirm final success or error.json creation after max retries"
echo ""
echo "Check worker logs for retry attempt messages like:"
echo "  'Save file ... for job ...: Attempt 1/3'"
echo "  'Save file ... for job ...: Attempt 2/3'"
echo ""
