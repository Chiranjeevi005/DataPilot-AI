#!/bin/bash
# Set secrets in Render
# Usage: ./scripts/render_set_secret.sh <SERVICE_NAME> <KEY> <VALUE>

SERVICE=$1
KEY=$2
VALUE=$3

if [ -z "$VALUE" ]; then
    echo "Usage: $0 <SERVICE_NAME> <KEY> <VALUE>"
    echo "Example: $0 api-service OPENROUTER_API_KEY sk-..."
    exit 1
fi

render secrets set "$KEY" "$VALUE" --service "$SERVICE"
echo "Set $KEY for $SERVICE"
