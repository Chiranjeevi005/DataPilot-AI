#!/bin/bash
# run from project root

BASE_URL="http://localhost:5328"
FILE="./dev-samples/sales_demo.csv"

# Check if file exists
if [ ! -f "$FILE" ]; then
    echo "Error: $FILE not found. Please ensure you are in project root."
    exit 1
fi

echo "1. Uploading file..."
RESPONSE=$(curl -s -X POST -F "file=@$FILE" "$BASE_URL/api/upload")
echo "Response: $RESPONSE"

# Extract Job ID using Python
JOB_ID=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('jobId', ''))")

if [ -z "$JOB_ID" ]; then
    echo "Error: Could not get Job ID."
    exit 1
fi

echo "Job ID: $JOB_ID"
echo "2. Polling status..."

STATUS="submitted"
MAX_RETRIES=30
COUNT=0

while [ "$STATUS" != "completed" ] && [ "$STATUS" != "failed" ]; do
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "Timeout waiting for job completion."
        exit 1
    fi

    sleep 1
    COUNT=$((COUNT+1))

    # Poll Redis
    JOB_JSON=$(redis-cli GET "job:$JOB_ID")
    if [ -z "$JOB_JSON" ]; then
        echo "Job key not found in Redis yet..."
        continue
    fi

    # Parse Status
    STATUS=$(echo "$JOB_JSON" | python -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))")
    echo "Step $COUNT: Status = $STATUS"
done

echo "3. Job Finished with status: $STATUS"
echo "Full result:"
echo "$JOB_JSON" | python -m json.tool

if [ "$STATUS" == "completed" ]; then
    RESULT_URL=$(echo "$JOB_JSON" | python -c "import sys, json; print(json.load(sys.stdin).get('resultUrl', ''))")
    echo "------------------------------------------------"
    echo "SUCCESS: Result available at $RESULT_URL"
    echo "------------------------------------------------"
else
    echo "FAILURE: Job did not complete successfully."
    exit 1
fi
