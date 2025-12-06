"""
Create fake data for testing the cleanup subsystem.

This script creates:
- Old blobs under uploads/ and results/ with timestamps older than TTL
- Recent blobs that should NOT be deleted
- Redis job keys with old and recent timestamps
"""
import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lib.queue import get_redis_client


def create_fake_blobs():
    """Create fake blob files with old and recent timestamps."""
    print("Creating fake blob files...")
    
    # Determine base storage directory
    base_dir = os.getenv('LOCAL_STORAGE_ROOT')
    if not base_dir:
        if os.name == 'nt':
            base_dir = os.path.join(os.getcwd(), 'tmp_uploads')
        else:
            base_dir = '/tmp/uploads'
    
    # Get TTL from env
    ttl_hours = int(os.getenv('JOB_TTL_HOURS', '24'))
    
    # Calculate timestamps
    now = datetime.utcnow()
    old_time = now - timedelta(hours=ttl_hours + 2)  # 2 hours older than TTL
    recent_time = now - timedelta(hours=ttl_hours - 2)  # 2 hours newer than TTL
    
    # Create old upload
    old_upload_dir = os.path.join(base_dir, 'uploads', 'job_old')
    os.makedirs(old_upload_dir, exist_ok=True)
    
    old_upload_file = os.path.join(old_upload_dir, 'test_data.csv')
    with open(old_upload_file, 'w') as f:
        f.write("id,name,value\n1,test,100\n")
    
    # Set old timestamp
    old_timestamp = old_time.timestamp()
    os.utime(old_upload_file, (old_timestamp, old_timestamp))
    print(f"  Created old upload: {old_upload_file}")
    
    # Create old result
    old_result_dir = os.path.join(base_dir, 'results')
    os.makedirs(old_result_dir, exist_ok=True)
    
    old_result_file = os.path.join(old_result_dir, 'job_old.json')
    with open(old_result_file, 'w') as f:
        json.dump({'status': 'completed', 'jobId': 'job_old'}, f)
    
    os.utime(old_result_file, (old_timestamp, old_timestamp))
    print(f"  Created old result: {old_result_file}")
    
    # Create recent upload
    recent_upload_dir = os.path.join(base_dir, 'uploads', 'job_recent')
    os.makedirs(recent_upload_dir, exist_ok=True)
    
    recent_upload_file = os.path.join(recent_upload_dir, 'test_data.csv')
    with open(recent_upload_file, 'w') as f:
        f.write("id,name,value\n2,recent,200\n")
    
    recent_timestamp = recent_time.timestamp()
    os.utime(recent_upload_file, (recent_timestamp, recent_timestamp))
    print(f"  Created recent upload: {recent_upload_file}")
    
    # Create recent result
    recent_result_file = os.path.join(old_result_dir, 'job_recent.json')
    with open(recent_result_file, 'w') as f:
        json.dump({'status': 'completed', 'jobId': 'job_recent'}, f)
    
    os.utime(recent_result_file, (recent_timestamp, recent_timestamp))
    print(f"  Created recent result: {recent_result_file}")
    
    print(f"Created blobs with TTL={ttl_hours}h, old_time={old_time.isoformat()}, recent_time={recent_time.isoformat()}")


def create_fake_redis_keys():
    """Create fake Redis job keys with old and recent timestamps."""
    print("\nCreating fake Redis job keys...")
    
    try:
        r = get_redis_client()
        
        # Get TTL from env
        ttl_hours = int(os.getenv('JOB_TTL_HOURS', '24'))
        
        # Calculate timestamps
        now = datetime.utcnow()
        old_time = now - timedelta(hours=ttl_hours + 2)
        recent_time = now - timedelta(hours=ttl_hours - 2)
        
        # Create old job key
        old_job_data = {
            'jobId': 'job_old',
            'status': 'completed',
            'createdAt': old_time.isoformat() + 'Z',
            'updatedAt': old_time.isoformat() + 'Z',
            'fileUrl': 'file:///tmp/uploads/job_old/test_data.csv'
        }
        r.set('job:job_old', json.dumps(old_job_data))
        print(f"  Created old Redis key: job:job_old (timestamp={old_time.isoformat()})")
        
        # Create recent job key
        recent_job_data = {
            'jobId': 'job_recent',
            'status': 'completed',
            'createdAt': recent_time.isoformat() + 'Z',
            'updatedAt': recent_time.isoformat() + 'Z',
            'fileUrl': 'file:///tmp/uploads/job_recent/test_data.csv'
        }
        r.set('job:job_recent', json.dumps(recent_job_data))
        print(f"  Created recent Redis key: job:job_recent (timestamp={recent_time.isoformat()})")
        
        print("Redis keys created successfully")
        
    except Exception as e:
        print(f"ERROR: Failed to create Redis keys: {e}")
        print("Make sure Redis is running!")
        sys.exit(1)


def verify_fake_data():
    """Verify that fake data was created correctly."""
    print("\nVerifying fake data...")
    
    # Check blobs
    base_dir = os.getenv('LOCAL_STORAGE_ROOT')
    if not base_dir:
        if os.name == 'nt':
            base_dir = os.path.join(os.getcwd(), 'tmp_uploads')
        else:
            base_dir = '/tmp/uploads'
    
    expected_files = [
        os.path.join(base_dir, 'uploads', 'job_old', 'test_data.csv'),
        os.path.join(base_dir, 'uploads', 'job_recent', 'test_data.csv'),
        os.path.join(base_dir, 'results', 'job_old.json'),
        os.path.join(base_dir, 'results', 'job_recent.json')
    ]
    
    all_exist = True
    for file_path in expected_files:
        exists = os.path.exists(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False
    
    # Check Redis keys
    try:
        r = get_redis_client()
        
        for key in ['job:job_old', 'job:job_recent']:
            exists = r.exists(key)
            status = "✓" if exists else "✗"
            print(f"  {status} Redis key: {key}")
            if not exists:
                all_exist = False
    except Exception as e:
        print(f"  ✗ Redis check failed: {e}")
        all_exist = False
    
    if all_exist:
        print("\n✓ All fake data created successfully!")
    else:
        print("\n✗ Some fake data is missing!")
        sys.exit(1)


def main():
    """Main entry point."""
    print("=" * 80)
    print("DataPilot AI Cleanup Test - Creating Fake Data")
    print("=" * 80)
    
    create_fake_blobs()
    create_fake_redis_keys()
    verify_fake_data()
    
    print("\n" + "=" * 80)
    print("Fake data creation completed!")
    print("=" * 80)


if __name__ == '__main__':
    main()
