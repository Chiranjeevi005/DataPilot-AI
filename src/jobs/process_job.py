import json
import time
import logging
import os
import io
from datetime import datetime

# Adjust import based on how the worker is run. 
# Assuming running from project root with src in path or similar.
try:
    from lib import storage
except ImportError:
    # Fallback for relative imports if needed
    from ..lib import storage

logger = logging.getLogger(__name__)

def process_job(redis_client, job_payload):
    """
    Process a single job: update status, simulate work, save result, finish.
    """
    job_id = job_payload.get('jobId')
    file_url = job_payload.get('fileUrl')
    file_name = job_payload.get('fileName')

    if not job_id:
        logger.error("Job missing jobId, cannot process")
        return

    logger.info(f"Starting processing for job {job_id} (file: {file_url})")

    try:
        # 1. Update status to processing
        redis_key = f"job:{job_id}"
        
        # We fetch existing to preserve other fields if needed, or just set merge.
        # Redis key should be JSON.
        # We perform a partial update by reading, updating, writing (optimistic)
        # Or just use SET since we own the state transition mostly.
        # The prompt says use HMSET or SET with JSON. The queue.py uses SET with JSON.
        # We'll read, update, set.
        current_data_str = redis_client.get(redis_key)
        if current_data_str:
            current_data = json.loads(current_data_str)
        else:
            current_data = job_payload # fallback
            
        current_data['status'] = 'processing'
        current_data['updatedAt'] = datetime.utcnow().isoformat() + "Z"
        
        redis_client.set(redis_key, json.dumps(current_data))
        
        # 2. Simulate work
        simulated_work_seconds = int(os.getenv('SIMULATED_WORK_SECONDS', '3'))
        if simulated_work_seconds > 0:
            time.sleep(simulated_work_seconds)
            
        # 3. Create mock result
        result_data = {
            "jobId": job_id,
            "fileInfo": { 
                "name": file_name or "unknown", 
                "rows": 100, 
                "cols": 10, 
                "type": "csv" # Inferred
            },
            "kpis": [ 
                { "name": "TotalRows", "value": 100 } 
            ],
            "chartSpecs": [ 
                { 
                    "id": "c1", 
                    "type": "line", 
                    "title": "Demo", 
                    "data": [{"x": 1, "y": 2}], 
                    "xKey": "x", 
                    "yKey": "y"
                } 
            ],
            "analystInsights": [ 
                { "id": "i1", "text": "Demo insight", "evidence": {} } 
            ],
            "processedAt": datetime.utcnow().isoformat() + "Z"
        }
        
        # 4. Save result
        # Convert dict to bytes stream
        result_json_str = json.dumps(result_data, indent=2)
        result_stream = io.BytesIO(result_json_str.encode('utf-8'))
        
        # Use storage helper
        logger.info(f"Saving result for job {job_id}")
        # Note: prompt says "store under results/{jobId}.json".
        # storage.py saves to {base}/{jobId}/{filename}.
        # pass filename="result.json".
        result_url = storage.save_file_to_blob(result_stream, "result.json", job_id)
        
        # 5. Update status to completed
        # Refresh data just in case? Assuming single worker for now.
        # re-read to be safe?
        current_data_str = redis_client.get(redis_key)
        if current_data_str:
            current_data = json.loads(current_data_str)
            
        current_data['status'] = 'completed'
        current_data['resultUrl'] = result_url
        current_data['updatedAt'] = datetime.utcnow().isoformat() + "Z"
        
        redis_client.set(redis_key, json.dumps(current_data))
        
        logger.info(f"Job {job_id} completed. Result: {result_url}")
        return {"jobId": job_id, "status": "completed", "resultUrl": result_url}

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
        # Update status to failed
        try:
            current_data_str = redis_client.get(redis_key)
            if current_data_str:
                current_data = json.loads(current_data_str)
            else:
                current_data = {"jobId": job_id}
            
            current_data['status'] = 'failed'
            current_data['error'] = str(e)
            current_data['updatedAt'] = datetime.utcnow().isoformat() + "Z"
            redis_client.set(redis_key, json.dumps(current_data))
        except Exception as inner_e:
            logger.error(f"Failed to update error status for job {job_id}: {inner_e}")
            
        raise e
