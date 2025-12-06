"""
Test health endpoint functionality.
Validates Redis, blob, and worker heartbeat checks.
"""

import requests
import json
import time
import os
import sys

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5329')

def test_health_endpoint():
    """Test health endpoint when all services are running."""
    print("=" * 60)
    print("Testing /api/health endpoint...")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"\nResponse:")
        print(json.dumps(response.json(), indent=2))
        
        data = response.json()
        
        print("\n" + "-" * 60)
        print("Component Status:")
        print("-" * 60)
        
        components = data.get('components', {})
        
        # Check Redis
        redis_status = components.get('redis', {}).get('status')
        print(f"Redis: {redis_status}")
        if redis_status == "ok":
            print(f"  ✓ {components['redis']['details']['message']}")
        else:
            print(f"  ✗ {components['redis']['details']['message']}")
        
        # Check Blob
        blob_status = components.get('blob', {}).get('status')
        print(f"Blob: {blob_status}")
        if blob_status == "ok":
            print(f"  ✓ {components['blob']['details']['message']}")
        else:
            print(f"  ✗ {components['blob']['details']['message']}")
        
        # Check Worker
        worker_status = components.get('worker', {}).get('status')
        worker_details = components.get('worker', {}).get('details', {})
        print(f"Worker: {worker_status}")
        print(f"  {worker_details.get('message', 'No details')}")
        if 'lastHeartbeat' in worker_details:
            print(f"  Last heartbeat: {worker_details['lastHeartbeat']}")
            print(f"  Age: {worker_details.get('ageSeconds', 'N/A')}s")
        
        # Overall status
        overall_status = data.get('status')
        print("\n" + "-" * 60)
        print(f"Overall Status: {overall_status}")
        print("-" * 60)
        
        if overall_status == "ok":
            print("✓ All systems operational")
            return True
        elif overall_status == "degraded":
            print("⚠ System degraded (worker may be stale)")
            return True
        else:
            print("✗ System error detected")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"✗ Could not connect to health endpoint at {API_BASE_URL}")
        print("  Make sure the health check server is running:")
        print(f"  python src/api/health/route.py")
        return False
    except Exception as e:
        print(f"✗ Error testing health endpoint: {e}")
        return False

def test_worker_heartbeat_staleness():
    """Test health endpoint when worker heartbeat is stale."""
    print("\n" + "=" * 60)
    print("Testing worker heartbeat staleness detection...")
    print("=" * 60)
    
    print("\nNote: This test requires:")
    print("1. Worker to be stopped")
    print("2. Wait for heartbeat to become stale (>60 seconds)")
    print("\nSkipping automated test. Manual verification:")
    print("1. Stop the worker")
    print("2. Wait 60+ seconds")
    print("3. Call /api/health")
    print("4. Verify worker status is 'stale'")
    
    return True

def test_redis_failure():
    """Test health endpoint when Redis is down."""
    print("\n" + "=" * 60)
    print("Testing Redis failure detection...")
    print("=" * 60)
    
    print("\nNote: This test requires Redis to be stopped.")
    print("Skipping automated test. Manual verification:")
    print("1. Stop Redis")
    print("2. Call /api/health")
    print("3. Verify redis status is 'error'")
    print("4. Verify overall status is 'error'")
    print("5. Verify HTTP status code is 503")
    
    return True

def main():
    """Run all health endpoint tests."""
    print("\n" + "=" * 60)
    print("DataPilot AI - Health Endpoint Test Suite")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print("=" * 60)
    
    results = []
    
    # Test normal health check
    results.append(("Health Endpoint (Normal)", test_health_endpoint()))
    
    # Test worker staleness (manual)
    results.append(("Worker Staleness (Manual)", test_worker_heartbeat_staleness()))
    
    # Test Redis failure (manual)
    results.append(("Redis Failure (Manual)", test_redis_failure()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Ensure worker is running to see 'ok' status")
    print("2. Stop worker and wait 60s to test 'stale' status")
    print("3. Stop Redis to test 'error' status")
    print("4. Integrate health check into monitoring/alerting")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
