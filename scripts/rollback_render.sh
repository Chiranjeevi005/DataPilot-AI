#!/bin/bash
# Rollback Render Service
# Usage: ./scripts/rollback_render.sh <SERVICE_NAME>

SERVICE=$1

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <SERVICE_NAME>"
    echo "Example: $0 api-service"
    exit 1
fi

echo "Rolling back $SERVICE..."
render services rollback "$SERVICE"
