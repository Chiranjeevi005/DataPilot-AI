import sys
import os
import json
import logging
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

from jobs.process_job import process_job
from unittest.mock import MagicMock

logging.basicConfig(level=logging.INFO)

def manual_run(job_id):
    # Construct paths
    # Windows path friendliness
    base_dir = os.path.join(os.getcwd(), 'tmp_uploads', job_id)
    files = os.listdir(base_dir)
    csv_files = [f for f in files if f.endswith('.csv')]
    
    if not csv_files:
        print(f"No CSV found in {base_dir}")
        return

    filename = csv_files[0]
    file_path = os.path.join(base_dir, filename)
    file_url = Path(file_path).as_uri()
    
    print(f"Processing {filename} at {file_url}")
    
    # Mock Redis
    redis_mock = MagicMock()
    redis_mock.get.return_value = json.dumps({"status": "submitted"})
    
    payload = {
        "jobId": job_id,
        "fileUrl": file_url,
        "fileName": filename
    }
    
    try:
        process_job(redis_mock, payload)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manual_run_job.py <jobId>")
        sys.exit(1)
    manual_run(sys.argv[1])
