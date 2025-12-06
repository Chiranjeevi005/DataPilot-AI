
import requests
import time
import os
import json
import sys

# Configuration
BASE_URL = 'http://localhost:5328'
FILE_PATH = os.path.join('dev-samples', 'sales_demo.csv')

def run_verification():
    print(f"--- Starting End-to-End Verification ---")
    print(f"Target file: {FILE_PATH}")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ Error: File not found at {FILE_PATH}")
        return

    # 1. Upload
    print(f"\n1. Uploading file...")
    try:
        with open(FILE_PATH, 'rb') as f:
            files = {'file': (os.path.basename(FILE_PATH), f, 'text/csv')}
            res = requests.post(f"{BASE_URL}/api/upload", files=files)
            
        if res.status_code != 200:
            print(f"❌ Upload failed: {res.status_code} - {res.text}")
            return
            
        data = res.json()
        job_id = data.get('jobId')
        print(f"✅ Upload successful. Job ID: {job_id}")
        
    except Exception as e:
        print(f"❌ Connection error during upload: {e}")
        print("Ensure the backend server is running on port 5328")
        return

    # 2. Poll Status
    print(f"\n2. Waiting for processing (DeepSeek R1)...")
    start_time = time.time()
    while True:
        try:
            res = requests.get(f"{BASE_URL}/api/job-status/{job_id}")
            status_data = res.json()
            status = status_data.get('status')
            
            elapsed = time.time() - start_time
            sys.stdout.write(f"\r   Status: {status} ({elapsed:.1f}s)")
            sys.stdout.flush()
            
            if status == 'completed':
                print("\n✅ Job completed!")
                break
            elif status == 'failed':
                print(f"\n❌ Job failed! Error: {status_data.get('errorMessage')}")
                return
            
            if elapsed > 60:
                print("\n❌ Timeout waiting for job to complete.")
                return
                
            time.sleep(2)
        except Exception as e:
            print(f"\n❌ Error polling status: {e}")
            return

    # 3. Fetch Results
    print(f"\n3. Fetching results...")
    try:
        res = requests.get(f"{BASE_URL}/api/results/{job_id}")
        if res.status_code != 200:
            print(f"❌ Failed to get results: {res.status_code}")
            return
            
        results = res.json()
    except Exception as e:
        print(f"❌ Error fetching results: {e}")
        return

    # 4. Validate Content
    print(f"\n--- Verification Report ---")
    
    # KPIs
    kpis = results.get('kpis', {})
    row_count = kpis.get('rowCount', 0)
    print(f"📊 Dataset Rows: {row_count}")
    if row_count > 0:
        print(f"✅ Data Parsing: SUCCESS")
    else:
        print(f"❌ Data Parsing: FAILED (0 rows)")

    # Insights (LLM Check)
    insights = results.get('analystInsights', [])
    summary = results.get('businessSummary', [])
    
    print(f"🧠 Analyst Insights: {len(insights)} generated")
    print(f"📝 Business Summary: {len(summary)} points")
    
    if len(insights) > 0 or len(summary) > 0:
        print(f"✅ AI Insights (DeepSeek): SUCCESS")
        print("\nSample Insight:")
        if insights:
            print(f" - \"{insights[0].get('text')}\"")
        elif summary:
             print(f" - \"{summary[0]}\"")
    else:
        print(f"⚠️ AI Insights: WARNING (No insights returned)")
        print(f"Issues: {results.get('issues', [])}")

    print(f"\n---------------------------------------------")
    print(f"Result: {'READY FOR REAL WORLD USE' if row_count > 0 and (len(insights) > 0 or len(summary) > 0) else 'NEEDS ATTENTION'}")

if __name__ == "__main__":
    run_verification()
