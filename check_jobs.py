import redis
import json
from datetime import datetime

r = redis.from_url('redis://localhost:6379/0')
keys = r.keys('job:*')
print(f'\n=== Found {len(keys)} jobs in Redis ===\n')

# Get the 5 most recent jobs
for key in sorted(keys, reverse=True)[:5]:
    job_id = key.decode()
    data = json.loads(r.get(key))
    status = data.get('status', 'unknown')
    created = data.get('createdAt', 'N/A')
    updated = data.get('updatedAt', 'N/A')
    
    print(f"Job: {job_id}")
    print(f"  Status: {status}")
    print(f"  Created: {created}")
    print(f"  Updated: {updated}")
    
    if status == 'processing':
        print(f"  ⚠️  Job is stuck in processing!")
        started = data.get('startedAt', 'N/A')
        print(f"  Started: {started}")
    
    if status == 'failed':
        print(f"  ❌ Error: {data.get('error', 'N/A')}")
        print(f"  Message: {data.get('errorMessage', 'N/A')}")
    
    print()

# Check queue
queue_len = r.llen('data_jobs')
print(f"Jobs in queue: {queue_len}")
