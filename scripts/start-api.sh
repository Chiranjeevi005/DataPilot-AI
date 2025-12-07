#!/bin/bash
# Start backend API (Gunicorn)
# Usage: ./scripts/start-api.sh

# Ensure we are in project root
cd "$(dirname "$0")/.."

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

PORT="${PORT:-5328}"
echo "Starting DataPilot API on port $PORT..."

# Run Gunicorn
# -w 4: 4 workers
# --access-logfile - : Log to stdout
exec gunicorn -w 4 -b 0.0.0.0:$PORT --access-logfile - src.server:app
