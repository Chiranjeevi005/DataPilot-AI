"""
Health check endpoint for DataPilot AI.
Checks Redis, Blob storage, and Worker heartbeat status.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Ensure src is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Try imports
try:
    from flask import Blueprint, jsonify
    from src.lib.queue import get_redis_client
    from src.observability import log_info, log_error, generate_request_id
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'src'))
    from lib.queue import get_redis_client
    from observability import log_info, log_error, generate_request_id

# Initialize Blueprint
health_bp = Blueprint('health', __name__)

COMPONENT = "health_check"

def check_redis():
    """
    Check Redis connectivity.
    
    Returns:
        tuple: (status, details)
    """
    try:
        r = get_redis_client()
        
        # Test set/get
        test_key = "health:test"
        test_value = "ok"
        r.set(test_key, test_value, ex=10)  # 10 second expiry
        result = r.get(test_key)
        
        if result and result.decode('utf-8') == test_value:
            return "ok", {"message": "Redis is healthy"}
        else:
            return "error", {"message": "Redis set/get test failed"}
            
    except Exception as e:
        return "error", {"message": f"Redis error: {str(e)}"}

def check_blob():
    """
    Check blob storage connectivity.
    
    Returns:
        tuple: (status, details)
    """
    try:
        blob_enabled = os.getenv('BLOB_ENABLED', 'false').lower() == 'true'
        
        if not blob_enabled:
            return "ok", {"message": "Blob storage disabled (local mode)"}
        
        # Try to list blob prefix
        try:
            from src.lib import storage
        except ImportError:
            from lib import storage
        
        # Check if we can access blob storage
        # This is a simple check - we don't actually list files to avoid performance issues
        # In production, you might want to do a lightweight operation
        blob_key = os.getenv('BLOB_KEY')
        if not blob_key:
            return "error", {"message": "BLOB_KEY not configured"}
        
        return "ok", {"message": "Blob storage configured"}
        
    except Exception as e:
        return "error", {"message": f"Blob storage error: {str(e)}"}

def check_worker():
    """
    Check worker heartbeat status.
    
    Returns:
        tuple: (status, details)
    """
    try:
        r = get_redis_client()
        
        # Read worker heartbeat
        heartbeat_key = "worker:heartbeat"
        heartbeat_str = r.get(heartbeat_key)
        
        if not heartbeat_str:
            return "stale", {"message": "No worker heartbeat found"}
        
        # Parse timestamp
        heartbeat_timestamp = heartbeat_str.decode('utf-8')
        heartbeat_dt = datetime.fromisoformat(heartbeat_timestamp.replace('Z', '+00:00'))
        
        # Check if heartbeat is recent
        max_age_seconds = int(os.getenv('HEALTH_WORKER_MAX_AGE_SECONDS', '60'))
        now = datetime.utcnow()
        age_seconds = (now - heartbeat_dt.replace(tzinfo=None)).total_seconds()
        
        if age_seconds > max_age_seconds:
            return "stale", {
                "message": f"Worker heartbeat is stale (age: {age_seconds:.1f}s)",
                "lastHeartbeat": heartbeat_timestamp,
                "ageSeconds": age_seconds
            }
        
        return "ok", {
            "message": "Worker is healthy",
            "lastHeartbeat": heartbeat_timestamp,
            "ageSeconds": age_seconds
        }
        
    except Exception as e:
        return "error", {"message": f"Worker heartbeat check error: {str(e)}"}

@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with overall status and component statuses
    """
    request_id = generate_request_id()
    
    log_info(COMPONENT, "Health check requested", request_id=request_id, step="start")
    
    try:
        # Check all components
        redis_status, redis_details = check_redis()
        blob_status, blob_details = check_blob()
        worker_status, worker_details = check_worker()
        
        # Determine overall status
        if redis_status == "error" or blob_status == "error":
            overall_status = "error"
        elif worker_status == "stale":
            overall_status = "degraded"
        else:
            overall_status = "ok"
        
        response = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "requestId": request_id,
            "components": {
                "redis": {
                    "status": redis_status,
                    "details": redis_details
                },
                "blob": {
                    "status": blob_status,
                    "details": blob_details
                },
                "worker": {
                    "status": worker_status,
                    "details": worker_details
                }
            }
        }
        
        log_info(COMPONENT, "Health check completed", request_id=request_id, 
                step="complete", overallStatus=overall_status)
        
        # Return appropriate HTTP status code
        if overall_status == "ok":
            return jsonify(response), 200
        elif overall_status == "degraded":
            return jsonify(response), 200  # Still return 200 for degraded
        else:
            return jsonify(response), 503  # Service Unavailable
            
    except Exception as e:
        log_error(COMPONENT, f"Health check error: {e}", request_id=request_id, 
                 step="error")
        
        return jsonify({
            "status": "error",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "requestId": request_id,
            "error": str(e)
        }), 500


