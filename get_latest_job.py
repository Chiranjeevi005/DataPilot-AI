import redis
import json

r = redis.from_url('redis://localhost:6379/0')
keys = r.keys('job:*')

if not keys:
    print("No jobs found in Redis")
    exit()

# Get the most recent job
latest_key = max(keys)
latest_data = json.loads(r.get(latest_key))
job_id = latest_key.decode().replace('job:', '')

print(f"\n=== Latest Job ===")
print(f"Job ID: {job_id}")
print(f"Status: {latest_data.get('status')}")
print(f"File: {latest_data.get('fileName', 'N/A')}")
print(f"Created: {latest_data.get('createdAt', 'N/A')}")

if latest_data.get('status') == 'completed':
    print(f"\n✅ Job is COMPLETED!")
    print(f"\nNavigate to: http://localhost:3003/results?jobId={job_id}")
    print(f"\nOr copy this URL to your browser:")
    print(f"http://localhost:3003/results?jobId={job_id}")
elif latest_data.get('status') == 'processing':
    print(f"\n⏳ Job is still PROCESSING...")
    print(f"Started: {latest_data.get('startedAt', 'N/A')}")
elif latest_data.get('status') == 'failed':
    print(f"\n❌ Job FAILED!")
    print(f"Error: {latest_data.get('error', 'N/A')}")
    print(f"Message: {latest_data.get('errorMessage', 'N/A')}")
else:
    print(f"\n⏸️  Job is in status: {latest_data.get('status')}")
