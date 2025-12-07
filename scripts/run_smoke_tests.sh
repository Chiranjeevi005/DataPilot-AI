#!/bin/bash
# Wrapper to run smoke tests
# Usage: ./scripts/run_smoke_tests.sh <API_HOST> <FRONTEND_HOST>

API_HOST=$1
FRONTEND_HOST=$2

if [ -z "$API_HOST" ]; then
    echo "Usage: $0 <API_HOST> [FRONTEND_HOST]"
    exit 1
fi

./scripts/verify_render.sh "$API_HOST"

if [ ! -z "$FRONTEND_HOST" ]; then
    echo "Checking Frontend at $FRONTEND_HOST..."
    if curl -s "$FRONTEND_HOST" | grep -q "DataPilot"; then
        echo "PASS: Frontend reachable."
    else
        echo "FAIL: Frontend check failed."
        exit 1
    fi
fi
