"""
Vercel Serverless Function for /api/upload
Pure Python implementation without Flask wrapper
"""

from http.server import BaseHTTPRequestHandler
import os
import sys
import json
from datetime import datetime
from io import BytesIO

# Add paths
project_root = os.getcwd()
src_path = os.path.join(project_root, 'src')
for path in [project_root, src_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for file upload"""
        try:
            # Import here to avoid cold start issues
            from src.lib.utils import (
                generate_job_id,
                validate_file_extension,
                current_timestamp_iso,
                get_max_upload_size
            )
            from src.lib.storage import save_file_to_blob
            from src.lib.queue import get_redis_client, create_job_key, enqueue_job
            
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            max_size = get_max_upload_size()
            
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
            
            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')
            
            if 'multipart/form-data' in content_type:
                # Extract boundary
                boundary = content_type.split('boundary=')[1].encode()
                
                # Parse multipart data
                parts = body.split(b'--' + boundary)
                
                file_data = None
                filename = None
                
                for part in parts:
                    if b'Content-Disposition' in part:
                        if b'filename=' in part:
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
                
                # Save file
                file_url = save_file_to_blob(BytesIO(file_data), filename, job_id)
                
                # Create job in Redis
                timestamp = current_timestamp_iso()
                job_timeout_seconds = int(os.getenv('JOB_TIMEOUT_SECONDS', '600'))
                timeout_dt = datetime.utcnow()
                from datetime import timedelta
                timeout_dt = timeout_dt + timedelta(seconds=job_timeout_seconds)
                timeout_at = timeout_dt.isoformat() + "Z"
                
                job_data = {
                    "jobId": job_id,
                    "status": "submitted",
                    "fileUrl": file_url,
                    "fileName": filename,
                    "createdAt": timestamp,
                    "timeoutAt": timeout_at
                }
                
                r = get_redis_client()
                create_job_key(r, job_id, job_data)
                
                queue_payload = {
                    "jobId": job_id,
                    "fileUrl": file_url,
                    "fileName": filename
                }
                enqueue_job(r, queue_payload)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "jobId": job_id,
                    "status": "submitted"
                }).encode())
                
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "Invalid content type. Expected multipart/form-data"
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
