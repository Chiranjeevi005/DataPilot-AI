import redis
import json
from datetime import datetime

r = redis.from_url('redis://localhost:6379/0')

job_id = "job_20251206_225232_0241"
job_key = f"job:{job_id}"

# Get current job data
data = json.loads(r.get(job_key))

print(f"Current status: {data.get('status')}")
print(f"Started: {data.get('startedAt')}")

# Mark as failed due to timeout
data['status'] = 'failed'
data['error'] = 'timeout'
data['errorMessage'] = 'Job exceeded processing time limit (LLM call took too long)'
data['updatedAt'] = datetime.utcnow().isoformat() + "Z"

r.set(job_key, json.dumps(data))

print(f"\n✅ Job marked as failed")
print(f"You can now navigate to: http://localhost:3003/results?jobId={job_id}")
print(f"Or upload a new file to test the fixed flow")
