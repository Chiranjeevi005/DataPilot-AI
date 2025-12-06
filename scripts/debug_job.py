import redis
import json
import os
import sys

r = redis.Redis(host='localhost', port=6379, db=0)

job_id = "job_20251206_145401_4392"
print(f"Inspecting {job_id}...")

# 1. Check Job Key
key = f"job:{job_id}"
val = r.get(key)
if val:
    print(f"Status in Redis: {json.loads(val)}")
else:
    print("Job key NOT found in Redis.")

# 2. Check Queue
q_len = r.llen("data_jobs")
print(f"Queue 'data_jobs' length: {q_len}")

# 3. Check items in queue (peek)
if q_len > 0:
    items = r.lrange("data_jobs", 0, -1)
    print("Items in queue:")
    for item in items:
        print(f" - {item}")
