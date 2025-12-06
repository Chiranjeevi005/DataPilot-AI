#!/bin/bash
# Wrapper to run reprocess_job.py
if [ -z "$1" ]; then
  echo "Usage: ./reprocess_job.sh <jobId>"
  exit 1
fi

export PYTHONPATH="src:$PYTHONPATH"
python scripts/reprocess_job.py "$1"
