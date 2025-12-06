#!/bin/bash
# Usage: ./scripts/inspect_redis.sh <jobId>

if [ -z "$1" ]; then
  echo "Usage: $0 <jobId>"
  exit 1
fi

redis-cli GET "job:$1"
