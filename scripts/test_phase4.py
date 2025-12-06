import requests
import time
import sys
import json
import os
import urllib.request

API_URL = "http://localhost:5328"
FILE_PATH = "dev-samples/sales_demo.csv"

def run_test():
    if not os.path.exists(FILE_PATH):
        print(f"File {FILE_PATH} not found.")
        sys.exit(1)
        
    print(f"Uploading {FILE_PATH}...")
    try:
        with open(FILE_PATH, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_URL}/api/upload", files=files)
            
        if response.status_code != 200:
            print(f"Upload failed: {response.text}")
            sys.exit(1)
            
        job_data = response.json()
        job_id = job_data.get('jobId')
        print(f"Job ID: {job_id}")
        
    except Exception as e:
        print(f"Upload request failed: {e}")
        sys.exit(1)
        
    # Poll
    status = "queued"
    result_url = None
    
    while status in ["queued", "processing"]:
        time.sleep(2)
        try:
            res = requests.get(f"{API_URL}/api/job-status/{job_id}")
            if res.status_code != 200:
                print(f"Status check failed: {res.status_code} {res.text}")
            
            try:
                data = res.json()
            except:
                print(f"Invalid JSON from status: {res.text}")
                time.sleep(2)
                continue
                
            status = data.get('status')
            print(f"Status: {status}")
            
            if status == 'failed':
                print(f"Job failed: {data.get('error')}")
                sys.exit(1)
            
            if status == 'completed':
                result_url = data.get('resultUrl')
                
        except Exception as e:
            print(f"Polling failed: {e}")
            time.sleep(2)
            
    print(f"Result URL: {result_url}")
    
    # Validate Result
    try:
        # Handle file:// url if local
        if result_url.startswith('file://'):
            file_path = urllib.request.url2pathname(urllib.parse.urlparse(result_url).path)
            # Fix windows path if needed
            if os.name == 'nt' and file_path.startswith('\\') and os.path.exists(file_path[1:]):
                file_path = file_path[1:]
            with open(file_path, 'r', encoding='utf-8') as f:
                result_json = json.load(f)
        else:
            # http
            r = requests.get(result_url)
            result_json = r.json()
            
        # Check keys
        keys = ['schema', 'kpis', 'chartSpecs', 'cleanedPreview', 'qualityScore']
        missing = [k for k in keys if k not in result_json]
        if missing:
             print(f"FAILED: Missing keys: {missing}")
             # Check if it was the old simulated result?
             if 'analystInsights' in result_json:
                 print("Detected OLD simulated result. The worker was likely not restarted.")
             sys.exit(1)
             
        print("SUCCESS: Result JSON valid.")
        print(f"Quality Score: {result_json['qualityScore']}")
        
    except Exception as e:
        print(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
