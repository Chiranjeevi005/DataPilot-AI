#!/bin/bash
set -e

# Configuration
API_URL="http://localhost:5328"
FILE="dev-samples/sales_demo.csv"

# Check if file exists
if [ ! -f "$FILE" ]; then
    echo "Error: $FILE not found!"
    exit 1
fi

echo "------------------------------------------------"
echo "Starting Phase 4 End-to-End Test"
echo "Uploading $FILE to $API_URL/api/upload"
echo "------------------------------------------------"

# Upload file
UPLOAD_RES=$(curl -s -X POST -F "file=@$FILE" "$API_URL/api/upload")
echo "Upload Response: $UPLOAD_RES"

JOB_ID=$(echo "$UPLOAD_RES" | jq -r '.jobId')

if [ "$JOB_ID" == "null" ] || [ -z "$JOB_ID" ]; then
    echo "Upload failed!"
    exit 1
fi

echo "Job Enqueued: $JOB_ID"
echo "Polling status..."

# Poll Status
STATUS="queued"
RESULT_URL=""

while [[ "$STATUS" == "queued" || "$STATUS" == "processing" ]]; do
    sleep 2
    STATUS_RES=$(curl -s "$API_URL/api/job-status/$JOB_ID")
    STATUS=$(echo "$STATUS_RES" | jq -r '.status')
    echo "Status: $STATUS"
    
    if [[ "$STATUS" == "failed" ]]; then
        echo "Job failed!"
        echo "$STATUS_RES" | jq
        exit 1
    fi
done

echo "------------------------------------------------"
echo "Job Completed!"
RESULT_URL=$(echo "$STATUS_RES" | jq -r '.resultUrl')
echo "Result URL: $RESULT_URL"

# Validation
echo "Validating Result JSON..."

# Fetch result content (handles file:// or http:// locally via python for portability)
python3 -c "
import sys, urllib.request, json
url = '$RESULT_URL'
try:
    with urllib.request.urlopen(url) as response:
        content = response.read()
        data = json.loads(content)
        
        required_keys = ['schema', 'kpis', 'chartSpecs', 'cleanedPreview', 'qualityScore']
        missing = [k for k in required_keys if k not in data]
        
        if missing:
            print(f'FAILED: result.json missing keys: {missing}')
            sys.exit(1)
            
        print('SUCCESS: result.json structure valid.')
        
        print(f'Quality Score: {data.get(\"qualityScore\")}')
        print(f'Rows Processed: {data.get(\"kpis\", {}).get(\"rowCount\")}')
        
        # Verify schema inference
        schema = data.get('schema', [])
        print(f'Columns detected: {len(schema)}')
        
        # Verify date detection (we expect one datetime)
        date_cols = [c for c in schema if c[\"inferred_type\"] in (\"datetime\", \"date\")]
        if not date_cols:
            print('WARNING: No date column detected!')
        else:
            print(f'Date columns: {[c[\"name\"] for c in date_cols]}')
            
        # Verify charts
        charts = data.get('chartSpecs', [])
        print(f'Charts generated: {len(charts)}')
        if len(charts) == 0:
            print('WARNING: No charts generated!')
            
except Exception as e:
    print(f'Error reading/validating result: {e}')
    sys.exit(1)
"

echo "------------------------------------------------"
echo "Test Passed Successfully"
