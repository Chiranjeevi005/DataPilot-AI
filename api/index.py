import os
import sys
import json
from datetime import datetime

# Ensure the project root is in sys.path
# Vercel places the project root in the current working directory
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Also add src directory
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import the main Flask app from upload route (this has all the main routes)
from src.api.upload.route import app
from flask import jsonify, request
import logging

logger = logging.getLogger(__name__)

# Health check route
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Vercel deployment"""
    try:
        import uuid
        request_id = str(uuid.uuid4())[:8]
        
        # Basic health check - just verify Redis connectivity
        redis_status = "unknown"
        redis_error = None
        try:
            from src.lib.queue import get_redis_client
            r = get_redis_client()
            test_key = "health:test"
            test_value = "ok"
            r.set(test_key, test_value, ex=10)
            result = r.get(test_key)
            
            redis_status = "ok" if result and result.decode('utf-8') == test_value else "error"
        except Exception as e:
            redis_status = "error"
            redis_error = str(e)
            logger.error(f"Redis health check failed: {e}")
        
        overall_status = "ok" if redis_status == "ok" else "degraded"
        
        response = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "requestId": request_id,
            "components": {
                "redis": {
                    "status": redis_status,
                    "error": redis_error if redis_error else None
                },
                "api": {"status": "ok"}
            }
        }
        
        # Remove None values
        if response["components"]["redis"]["error"] is None:
            del response["components"]["redis"]["error"]
        
        return jsonify(response), 200 if overall_status == "ok" else 503
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "error",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e)
        }), 500

# Cancel job route
@app.route('/api/cancel', methods=['POST'])
def cancel_job():
    """Cancel a job by setting its status to 'cancelled'"""
    try:
        from src.lib.queue import get_redis_client
        
        # Get jobId from query param or JSON body
        job_id = request.args.get('jobId')
        
        if not job_id and request.is_json:
            data = request.get_json()
            job_id = data.get('jobId')
        
        if not job_id:
            return jsonify({"error": "Missing jobId parameter"}), 400
        
        # Get Redis client
        r = get_redis_client()
        job_key = f"job:{job_id}"
        
        # Check if job exists
        job_data_str = r.get(job_key)
        if not job_data_str:
            return jsonify({"error": "Job not found"}), 404
        
        job_data = json.loads(job_data_str)
        current_status = job_data.get('status')
        
        # Don't allow cancellation of already completed or failed jobs
        if current_status in ('completed', 'failed'):
            return jsonify({
                "error": f"Cannot cancel job with status '{current_status}'",
                "jobId": job_id,
                "status": current_status
            }), 400
        
        # Check if already cancelled
        if current_status == 'cancelled':
            return jsonify({
                "jobId": job_id,
                "status": "cancelled",
                "message": "Job was already cancelled",
                "cancelledAt": job_data.get('cancelledAt')
            }), 200
        
        # Set status to cancelled
        timestamp = datetime.utcnow().isoformat() + "Z"
        job_data['status'] = 'cancelled'
        job_data['cancelledAt'] = timestamp
        job_data['updatedAt'] = timestamp
        
        # Update Redis
        r.set(job_key, json.dumps(job_data))
        
        logger.info(f"Job {job_id} cancelled successfully")
        
        return jsonify({
            "jobId": job_id,
            "status": "cancelled",
            "cancelledAt": timestamp
        }), 200
        
    except Exception as e:
        logger.error(f"Error cancelling job: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

# This is the handler that Vercel will use
# Vercel looks for either 'app' or 'handler'
handler = app

# Also export as 'app' for compatibility
# The Flask app is already imported and configured above
