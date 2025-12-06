import os
import sys
import logging
import json

# Ensure src is in python path so we can import lib
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Try imports
try:
    from flask import Flask, request, jsonify
    from src.lib.utils import (
        generate_job_id,
        validate_file_extension,
        validate_file_size,
        current_timestamp_iso,
        get_max_upload_size
    )
    from src.lib.storage import save_file_to_blob, save_file_to_tmp
    from src.lib.queue import get_redis_client, create_job_key, enqueue_job
except ImportError:
    # Fallback for when running from different contexts or if src is not a package
    # This is a bit hacky but ensures it works in the "Antigravity" context if paths are weird
    sys.path.append(os.path.join(os.getcwd(), 'src'))
    from lib.utils import (
        generate_job_id,
        validate_file_extension,
        validate_file_size,
        current_timestamp_iso,
        get_max_upload_size
    )
    from lib.storage import save_file_to_blob, save_file_to_tmp
    from lib.queue import get_redis_client, create_job_key, enqueue_job

# Initialize Flask app
app = Flask(__name__)

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/upload', methods=['POST'])
def upload_handler():
    try:
        content_length = request.content_length
        max_size = get_max_upload_size()
        
        if content_length and content_length > max_size:
             return jsonify({
                "error": "File too large",
                "maxBytes": max_size
            }), 413

        job_id = generate_job_id()
        file_url = None
        filename = None
        
        # Handle JSON (URL based)
        if request.is_json:
            data = request.get_json()
            file_url_input = data.get('fileUrl')
            filename_input = data.get('filename')
            
            if not file_url_input or not filename_input:
                return jsonify({"error": "Missing fileUrl or filename in JSON body"}), 400
                
            if not validate_file_extension(filename_input):
                 return jsonify({"error": "Invalid file extension. Allowed: csv, xlsx, xls, json, pdf"}), 400
            
            # TODO: Validate URL or download validation? 
            # For now, we trust the URL provided by frontend/blob flow, 
            # but we update the job with this info.
            filename = filename_input
            file_url = file_url_input
            
        # Handle Multipart (Binary)
        elif 'file' in request.files:
            file_obj = request.files['file']
            filename = file_obj.filename
            
            if not filename or filename == '':
                return jsonify({"error": "No filename provided"}), 400

            if not validate_file_extension(filename):
                return jsonify({"error": "Invalid file extension. Allowed: csv, xlsx, xls, json, pdf"}), 400
                
            # Double check size if not caught by content-length (e.g. chunked)
            # We can rely on Flask or check stream, but for simplicity:
            # Note: request.files saves to spooled temp file.
            
            # Save file
            # If BLOB_ENABLED, this calls save_to_blob, else save_to_tmp
            try:
                # We need to pass the stream.
                file_url = save_file_to_blob(file_obj.stream, filename, job_id)
            except Exception as e:
                logger.error(f"Storage error: {e}")
                return jsonify({"error": "Failed to save file"}), 500

        else:
            return jsonify({"error": "No file part or JSON body found"}), 400

        # Success - Update Redis
        timestamp = current_timestamp_iso()
        
        # Calculate timeout
        job_timeout_seconds = int(os.getenv('JOB_TIMEOUT_SECONDS', '600'))
        from datetime import datetime, timedelta
        timeout_dt = datetime.utcnow() + timedelta(seconds=job_timeout_seconds)
        timeout_at = timeout_dt.isoformat() + "Z"
        
        job_data = {
            "jobId": job_id,
            "status": "submitted",
            "fileUrl": file_url,
            "fileName": filename,
            "createdAt": timestamp,
            "timeoutAt": timeout_at
        }
        
        try:
            r = get_redis_client()
            create_job_key(r, job_id, job_data)
            
            # Enqueue minimal metadata
            # "The enqueued item should contain at least { jobId, fileUrl, fileName }"
            queue_payload = {
                "jobId": job_id,
                "fileUrl": file_url,
                "fileName": filename
            }
            enqueue_job(r, queue_payload)
        except Exception as e:
            logger.error(f"Redis error: {e}")
            return jsonify({"error": "Failed to queue job"}), 500

        return jsonify({
            "jobId": job_id,
            "status": "submitted"
        }), 200

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/api/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    try:
        from datetime import datetime
        
        r = get_redis_client()
        job_key = f"job:{job_id}"
        data_str = r.get(job_key)
        
        if not data_str:
            return jsonify({"error": "Job not found"}), 404
            
        data = json.loads(data_str)
        
        # Check for timeout if job is still processing
        if data.get('status') == 'processing':
            timeout_at_str = data.get('timeoutAt')
            if timeout_at_str:
                try:
                    timeout_at = datetime.fromisoformat(timeout_at_str.replace('Z', '+00:00'))
                    now = datetime.utcnow()
                    
                    if now > timeout_at.replace(tzinfo=None):
                        # Job has timed out
                        logger.warning(f"Job {job_id} has timed out")
                        data['status'] = 'failed'
                        data['error'] = 'timeout'
                        data['errorMessage'] = 'Job exceeded maximum processing time'
                        data['updatedAt'] = datetime.utcnow().isoformat() + "Z"
                        
                        # Update Redis
                        r.set(job_key, json.dumps(data))
                except Exception as e:
                    logger.error(f"Error parsing timeout: {e}")
        
        # Return job data with standard fields
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
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error fetching status for {job_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

# Security (Placeholder)
# To add API Key auth:
# @app.before_request
# def check_api_key():
#     key = request.headers.get('X-API-KEY')
#     if key != os.getenv('API_KEY'):
#         return jsonify({"error": "Unauthorized"}), 401


if __name__ == "__main__":
    # Dev server behavior
    port = int(os.environ.get('PORT', 5328)) # Using 5328 default for python backend often used in nextjs
    print(f"Starting dev server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
