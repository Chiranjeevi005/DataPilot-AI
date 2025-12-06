#!/bin/bash
# Test Phase 7: LLM Failure and Fallback
# Tests LLM retry logic and deterministic fallback

echo "=== Phase 7 Test: LLM Failure and Fallback ==="
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

# Save current API key
ORIGINAL_KEY=$OPENROUTER_API_KEY

# Test 1: Invalid API Key (should trigger fallback)
echo "Test 1: Invalid API Key (should trigger fallback)"
export OPENROUTER_API_KEY="invalid_key_test"
export LLM_RETRY_ATTEMPTS=2
export RETRY_INITIAL_DELAY=0.5

echo "Configuration:"
echo "  OPENROUTER_API_KEY=invalid_key_test"
echo "  LLM_RETRY_ATTEMPTS=$LLM_RETRY_ATTEMPTS"
echo ""

# Create test file
TEST_FILE="tmp_uploads/test_llm_fail.csv"
mkdir -p tmp_uploads
cat > "$TEST_FILE" << EOF
date,revenue,cost,profit
2024-01-01,1000,500,500
2024-01-02,1200,600,600
2024-01-03,1100,550,550
2024-01-04,1300,650,650
2024-01-05,1250,625,625
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

# Wait for processing
echo "Waiting for job to process (with LLM failure expected)..."
sleep 8

# Check result
echo "Checking job status..."
STATUS_RESPONSE=$(curl -s http://localhost:5328/api/job-status/$JOB_ID)
STATUS=$(echo $STATUS_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
RESULT_URL=$(echo $STATUS_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('resultUrl', ''))" 2>/dev/null)

echo "  Status: $STATUS"
echo "  Result URL: $RESULT_URL"
echo ""

if [ "$STATUS" = "completed" ] && [ ! -z "$RESULT_URL" ]; then
    echo "✓ Job completed with fallback"
    
    # Check result.json for fallback indicators
    if [[ $RESULT_URL == file://* ]]; then
        FILE_PATH=$(echo $RESULT_URL | sed 's|file://||' | sed 's|^/||')
        
        if [ -f "$FILE_PATH" ]; then
            echo ""
            echo "Checking result.json for fallback indicators..."
            
            # Check for businessSummary with fallback message
            FALLBACK_MSG=$(cat "$FILE_PATH" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('businessSummary', [])[0] if data.get('businessSummary') else '')" 2>/dev/null)
            
            if [[ $FALLBACK_MSG == *"not available"* ]] || [[ $FALLBACK_MSG == *"Automated insights"* ]]; then
                echo "✓ Fallback message found in businessSummary"
                echo "  Message: $FALLBACK_MSG"
            else
                echo "⚠ Unexpected businessSummary content"
            fi
            
            # Check for issues field
            ISSUES=$(cat "$FILE_PATH" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('issues', []))" 2>/dev/null)
            if [[ $ISSUES == *"llm"* ]] || [[ $ISSUES == *"LLM"* ]]; then
                echo "✓ LLM failure noted in issues"
                echo "  Issues: $ISSUES"
            fi
        fi
    fi
else
    echo "✗ Unexpected status: $STATUS"
fi

echo ""

# Test 2: Missing API Key
echo "Test 2: Missing API Key (should trigger fallback)"
unset OPENROUTER_API_KEY

TEST_FILE2="tmp_uploads/test_llm_fail2.csv"
cat > "$TEST_FILE2" << EOF
product,sales,quantity
A,1000,10
B,2000,20
C,1500,15
EOF

echo "Uploading second test file..."
JOB_RESPONSE2=$(curl -s -X POST http://localhost:5328/api/upload \
  -F "file=@$TEST_FILE2")

JOB_ID2=$(echo $JOB_RESPONSE2 | python -c "import sys, json; print(json.load(sys.stdin).get('jobId', ''))" 2>/dev/null)

if [ ! -z "$JOB_ID2" ]; then
    echo "✓ Upload succeeded: $JOB_ID2"
    sleep 8
    
    STATUS2=$(curl -s http://localhost:5328/api/job-status/$JOB_ID2 | python -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
    echo "  Status: $STATUS2"
    
    if [ "$STATUS2" = "completed" ]; then
        echo "✓ Job completed with fallback (missing API key)"
    fi
fi

echo ""

# Restore original API key
export OPENROUTER_API_KEY=$ORIGINAL_KEY

echo "=== Test Complete ==="
echo ""
echo "Expected behavior:"
echo "  - LLM calls should retry 2 times"
echo "  - After retries fail, deterministic fallback is used"
echo "  - Job completes with status='completed'"
echo "  - result.json contains fallback businessSummary"
echo "  - issues array contains LLM failure indicator"
echo ""
echo "Check worker logs for:"
echo "  'LLM call (deepseek/deepseek-r1): Attempt 1/2'"
echo "  'LLM call (deepseek/deepseek-r1): Attempt 2/2'"
echo "  'LLM failed after 2 attempts'"
echo ""
