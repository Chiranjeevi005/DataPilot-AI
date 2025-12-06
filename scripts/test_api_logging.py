"""
Test API logging and observability features.
Calls /api/upload and /api/job-status to verify structured logging.
"""

import requests
import json
import time
import sys
import os

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5328')

def test_upload_logging():
    """Test upload endpoint logging."""
    print("=" * 60)
    print("Testing /api/upload endpoint logging...")
    print("=" * 60)
    
    # Create a test file
    test_data = {
        "fileUrl": "test://sample.csv",
        "filename": "test_sample.csv"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/upload",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data.get('jobId')
            print(f"\n✓ Upload successful. Job ID: {job_id}")
            
            # Check if requestId is in response
            if 'requestId' in job_data:
                print(f"✓ Request ID found in response: {job_data['requestId']}")
            else:
                print("⚠ Request ID not found in response (expected for observability)")
            
            return job_id
        else:
            print(f"✗ Upload failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"✗ Error during upload: {e}")
        return None

def test_job_status_logging(job_id):
    """Test job status endpoint logging."""
    print("\n" + "=" * 60)
    print(f"Testing /api/job-status/{job_id} endpoint logging...")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/job-status/{job_id}")
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print(f"\n✓ Job status retrieved successfully")
            return True
        else:
            print(f"✗ Job status failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error during job status check: {e}")
        return False

def test_pii_masking():
    """Test PII masking in logs."""
    print("\n" + "=" * 60)
    print("Testing PII masking...")
    print("=" * 60)
    
    # Upload with PII-like data
    test_data = {
        "fileUrl": "test://user_data_john.doe@example.com.csv",
        "filename": "contact_list_555-123-4567.csv"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/upload",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✓ Upload with PII-like data successful")
            print("⚠ Check logs to verify email and phone are masked")
            print("  Expected: [EMAIL_MASKED] and [PHONE_MASKED]")
            return True
        else:
            print(f"✗ Upload failed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all API logging tests."""
    print("\n" + "=" * 60)
    print("DataPilot AI - API Logging Test Suite")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print("\nNote: Check console/logs for structured JSON log entries")
    print("Expected log format:")
    print(json.dumps({
        "timestamp": "2025-12-06T12:00:00Z",
        "level": "INFO",
        "component": "api_component",
        "requestId": "req_abc123",
        "step": "request_received",
        "message": "Request processed",
        "extra": {}
    }, indent=2))
    print("=" * 60)
    
    # Test upload
    job_id = test_upload_logging()
    
    if job_id:
        # Wait a bit
        time.sleep(1)
        
        # Test job status
        test_job_status_logging(job_id)
    
    # Test PII masking
    test_pii_masking()
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review logs for structured JSON format")
    print("2. Verify requestId is present in all log entries")
    print("3. Verify PII is masked (emails, phones)")
    print("4. Check that step field is populated")
    print("=" * 60)

if __name__ == "__main__":
    main()
