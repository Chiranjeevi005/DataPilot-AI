import os
import sys
import logging
import json
from datetime import datetime

# Ensure src is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Try imports
try:
    from flask import Flask, request, jsonify
    from src.lib.queue import get_redis_client
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'src'))
    from lib.queue import get_redis_client

# Initialize Flask app
app = Flask(__name__)

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/cancel', methods=['POST'])
def cancel_job():
    """
    Cancel a job by setting its status to 'cancelled'.
    Accepts jobId via query param or JSON body.
    
    Optional API key authentication (commented out by default).
    """
    try:
        # Optional: API Key Authentication
        # api_key = request.headers.get('X-API-KEY')
        # expected_key = os.getenv('API_KEY')
        # if expected_key and api_key != expected_key:
        #     return jsonify({"error": "Unauthorized"}), 401
        
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
        
        # Atomic update (simple SET - for production, use WATCH/MULTI/EXEC or Lua script)
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


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5328))
    print(f"Starting cancel endpoint on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
