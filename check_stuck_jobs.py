import redis
import json

r = redis.from_url('redis://localhost:6379/0')

# Check queue
queue_len = r.llen('data_jobs')
print(f"Jobs in queue: {queue_len}\n")

# Check for processing jobs
keys = r.keys('job:*')
processing_jobs = []
pending_jobs = []

for key in keys:
    data = json.loads(r.get(key))
    status = data.get('status')
    if status == 'processing':
        processing_jobs.append((key.decode(), data))
    elif status in ['pending', 'submitted']:
        pending_jobs.append((key.decode(), data))

print(f"Processing jobs: {len(processing_jobs)}")
for job_id, data in processing_jobs:
    print(f"  - {job_id}: started at {data.get('startedAt', 'N/A')}")

print(f"\nPending/Submitted jobs: {len(pending_jobs)}")
for job_id, data in pending_jobs:
    print(f"  - {job_id}: created at {data.get('createdAt', 'N/A')}")

# Get the most recent job
if keys:
    latest_key = max(keys)
    latest_data = json.loads(r.get(latest_key))
    print(f"\nMost recent job: {latest_key.decode()}")
    print(f"  Status: {latest_data.get('status')}")
    print(f"  File: {latest_data.get('fileName', 'N/A')}")
    print(f"  Created: {latest_data.get('createdAt', 'N/A')}")
    if latest_data.get('status') == 'completed':
        print(f"  Result URL: {latest_data.get('resultUrl', 'N/A')}")
