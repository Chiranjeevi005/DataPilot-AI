#!/bin/bash
# Fetch Render Logs
# Usage: ./scripts/fetch_logs.sh <SERVICE_NAME> [LINES]

SERVICE=$1
LINES=${2:-200}

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <SERVICE_NAME> [LINES]"
    echo "Example: $0 api-service 500"
    exit 1
fi

echo "Fetching last $LINES lines for $SERVICE..."
render logs "$SERVICE" --num "$LINES"
