#!/bin/bash
# Start Background Worker
# Usage: ./scripts/start-worker.sh

# Ensure we are in project root
cd "$(dirname "$0")/.."

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "Starting DataPilot Worker..."

# exec replaces the shell process, ensuring signals (SIGTERM) reach Python
exec python src/worker.py
