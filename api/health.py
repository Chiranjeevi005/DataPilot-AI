"""
Vercel Serverless Function for /api/health endpoint
"""

import os
import sys

# Ensure the project root and src directory are in the Python path
project_root = os.getcwd()
src_path = os.path.join(project_root, 'src')

for path in [project_root, src_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

from flask import Flask, jsonify
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
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

def handler(event, context):
    """Vercel serverless function handler"""
    from werkzeug.wrappers import Request
    from io import BytesIO
    
    environ = {
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': '/api/health',
        'QUERY_STRING': '',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': BytesIO(b''),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    response_data = []
    def start_response(status, headers):
        response_data.append((status, headers))
    
    app_response = app(environ, start_response)
    
    status_code = int(response_data[0][0].split()[0])
    headers_dict = {k: v for k, v in response_data[0][1]}
    body = b''.join(app_response).decode('utf-8')
    
    return {
        'statusCode': status_code,
        'headers': headers_dict,
        'body': body
    }
