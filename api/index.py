"""
Vercel Serverless Function Handler for DataPilot AI
This module provides a WSGI-compatible handler for Vercel's Python runtime.
"""

import os
import sys

# Ensure the project root and src directory are in the Python path
project_root = os.getcwd()
src_path = os.path.join(project_root, 'src')

for path in [project_root, src_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import Flask and create the application
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import logging
from datetime import datetime

# Configure logging for serverless environment
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the main Flask app from upload route
from src.api.upload.route import app

# Add health check route
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Vercel deployment"""
    try:
        import uuid
        request_id = str(uuid.uuid4())[:8]
        
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

# Add cancel job route
@app.route('/api/cancel', methods=['POST'])
def cancel_job():
    """Cancel a job by setting its status to 'cancelled'"""
    try:
        from src.lib.queue import get_redis_client
        
        job_id = request.args.get('jobId')
        
        if not job_id and request.is_json:
            data = request.get_json()
            job_id = data.get('jobId')
        
        if not job_id:
            return jsonify({"error": "Missing jobId parameter"}), 400
        
        r = get_redis_client()
        job_key = f"job:{job_id}"
        
        job_data_str = r.get(job_key)
        if not job_data_str:
            return jsonify({"error": "Job not found"}), 404
        
        job_data = json.loads(job_data_str)
        current_status = job_data.get('status')
        
        if current_status in ('completed', 'failed'):
            return jsonify({
                "error": f"Cannot cancel job with status '{current_status}'",
                "jobId": job_id,
                "status": current_status
            }), 400
        
        if current_status == 'cancelled':
            return jsonify({
                "jobId": job_id,
                "status": "cancelled",
                "message": "Job was already cancelled",
                "cancelledAt": job_data.get('cancelledAt')
            }), 200
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        job_data['status'] = 'cancelled'
        job_data['cancelledAt'] = timestamp
        job_data['updatedAt'] = timestamp
        
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

# Vercel serverless function handler
# This is the entry point that Vercel will call
def handler(event, context):
    """
    Vercel serverless function handler.
    Converts Vercel's event/context format to WSGI and calls the Flask app.
    """
    from werkzeug.wrappers import Request, Response
    from io import BytesIO
    
    # Create a WSGI environ from the Vercel event
    environ = {
        'REQUEST_METHOD': event.get('httpMethod', event.get('method', 'GET')),
        'SCRIPT_NAME': '',
        'PATH_INFO': event.get('path', '/'),
        'QUERY_STRING': event.get('queryStringParameters', ''),
        'CONTENT_TYPE': event.get('headers', {}).get('content-type', ''),
        'CONTENT_LENGTH': event.get('headers', {}).get('content-length', '0'),
        'SERVER_NAME': event.get('headers', {}).get('host', 'localhost'),
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': BytesIO(event.get('body', '').encode('utf-8') if isinstance(event.get('body'), str) else event.get('body', b'')),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Add headers to environ
    for key, value in event.get('headers', {}).items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key}'] = value
    
    # Call the Flask app
    response_data = []
    def start_response(status, headers):
        response_data.append((status, headers))
    
    app_response = app(environ, start_response)
    
    # Build the response
    status_code = int(response_data[0][0].split()[0])
    headers_dict = {k: v for k, v in response_data[0][1]}
    body = b''.join(app_response).decode('utf-8')
    
    return {
        'statusCode': status_code,
        'headers': headers_dict,
        'body': body
    }

# For local testing and Vercel's auto-detection
# Vercel will use the 'app' variable if it finds it
__all__ = ['app', 'handler']
