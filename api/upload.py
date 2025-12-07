"""
Vercel Serverless Function for /api/upload
Self-contained implementation without heavy src/ dependencies
"""

from http.server import BaseHTTPRequestHandler
import os
import json
from datetime import datetime, timedelta
from io import BytesIO
import uuid
import redis

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for file upload"""
        try:
            # Inline utility functions to avoid heavy src/ imports
            def generate_job_id():
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                random_suffix = str(uuid.uuid4().int)[:4]
                return f"job_{timestamp}_{random_suffix}"
            
            def validate_file_extension(filename):
                allowed = {'.csv', '.xlsx', '.xls', '.json', '.pdf'}
                ext = os.path.splitext(filename.lower())[1]
                return ext in allowed
            
            def get_redis_client():
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                if 'upstash.io' in redis_url and redis_url.startswith('redis://'):
                    redis_url = redis_url.replace('redis://', 'rediss://')
                return redis.from_url(redis_url, decode_responses=False, socket_timeout=5)
            
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            max_size = int(os.getenv('MAX_UPLOAD_SIZE_BYTES', '20971520'))
            
            if content_length > max_size:
                self.send_response(413)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "File too large",
                    "maxBytes": max_size
                }).encode())
                return
            
            # Read the body
            body = self.rfile.read(content_length)
            content_type = self.headers.get('Content-Type', '')
            
            if 'multipart/form-data' not in content_type:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "Invalid content type. Expected multipart/form-data"
                }).encode())
                return
            
            # Extract boundary and parse multipart data
            boundary = content_type.split('boundary=')[1].encode()
            parts = body.split(b'--' + boundary)
            
            file_data = None
            filename = None
            
            for part in parts:
                if b'Content-Disposition' in part and b'filename=' in part:
                    # Extract filename
                    filename_start = part.find(b'filename="') + 10
                    filename_end = part.find(b'"', filename_start)
                    filename = part[filename_start:filename_end].decode('utf-8')
                    
                    # Extract file data
                    data_start = part.find(b'\r\n\r\n') + 4
                    file_data = part[data_start:].rstrip(b'\r\n')
            
            if not filename or not file_data:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No file provided"}).encode())
                return
            
            if not validate_file_extension(filename):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "Invalid file extension. Allowed: csv, xlsx, xls, json, pdf"
                }).encode())
                return
            
            # Generate job ID
            job_id = generate_job_id()
            
            # Save file to /tmp (Vercel's writable directory)
            upload_dir = f"/tmp/uploads/{job_id}"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            file_url = file_path  # Local path for now
            
            # Create job in Redis
            timestamp = datetime.utcnow().isoformat() + "Z"
            timeout_seconds = int(os.getenv('JOB_TIMEOUT_SECONDS', '600'))
            timeout_at = (datetime.utcnow() + timedelta(seconds=timeout_seconds)).isoformat() + "Z"
            
            job_data = {
                "jobId": job_id,
                "status": "submitted",
                "fileUrl": file_url,
                "fileName": filename,
                "createdAt": timestamp,
                "timeoutAt": timeout_at
            }
            
            r = get_redis_client()
            job_key = f"job:{job_id}"
            r.set(job_key, json.dumps(job_data))
            
            # Set TTL
            ttl_hours = int(os.getenv('JOB_TTL_HOURS', '24'))
            r.expire(job_key, ttl_hours * 3600)
            
            # Enqueue job
            queue_payload = {
                "jobId": job_id,
                "fileUrl": file_url,
                "fileName": filename
            }
            r.rpush('data_jobs', json.dumps(queue_payload))
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "jobId": job_id,
                "status": "submitted"
            }).encode())
            
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
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
