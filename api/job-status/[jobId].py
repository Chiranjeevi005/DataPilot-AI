"""
Vercel Serverless Function for /api/job-status/[jobId]
Self-contained implementation without heavy src/ dependencies
"""

from http.server import BaseHTTPRequestHandler
import os
import json
from datetime import datetime
import redis

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests for job status"""
        try:
            def get_redis_client():
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                if 'upstash.io' in redis_url and redis_url.startswith('redis://'):
                    redis_url = redis_url.replace('redis://', 'rediss://')
                return redis.from_url(redis_url, decode_responses=False, socket_timeout=5)
            
            # Extract job_id from path
            path_parts = self.path.split('/')
            job_id = path_parts[-1].split('?')[0]
            
            if not job_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing job ID"}).encode())
                return
            
            # Get job from Redis
            r = get_redis_client()
            job_key = f"job:{job_id}"
            data_bytes = r.get(job_key)
            
            if not data_bytes:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Job not found"}).encode())
                return
            
            data = json.loads(data_bytes.decode('utf-8'))
            
            # Check for timeout
            if data.get('status') == 'processing':
                timeout_at_str = data.get('timeoutAt')
                if timeout_at_str:
                    try:
                        timeout_at = datetime.fromisoformat(timeout_at_str.replace('Z', '+00:00'))
                        now = datetime.utcnow()
                        
                        if now > timeout_at.replace(tzinfo=None):
                            data['status'] = 'failed'
                            data['error'] = 'timeout'
                            data['errorMessage'] = 'Job exceeded maximum processing time'
                            data['updatedAt'] = datetime.utcnow().isoformat() + "Z"
                            r.set(job_key, json.dumps(data).encode('utf-8'))
                    except:
                        pass
            
            # Return job data
            response = {
                "jobId": job_id,
                "status": data.get('status'),
                "progress": data.get('progress'),
                "resultUrl": data.get('resultUrl'),
                "error": data.get('error'),
                "errorMessage": data.get('errorMessage'),
                "createdAt": data.get('createdAt'),
                "updatedAt": data.get('updatedAt'),
                "cancelledAt": data.get('cancelledAt')
            }
            
            # Remove None values
            response = {k: v for k, v in response.items() if v is not None}
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            import traceback
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Internal Server Error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
