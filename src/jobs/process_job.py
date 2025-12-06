import json
import time
import logging
import os
import io
import traceback
from datetime import datetime

# Adjust import based on how the worker is run. 
try:
    from lib import storage, analysis
except ImportError:
    # Fallback for relative imports if needed
    from ..lib import storage, analysis

logger = logging.getLogger(__name__)

def process_job(redis_client, job_payload):
    """
    Process a single job: update status, download, parse, analyze, save result, finish.
    """
    job_id = job_payload.get('jobId')
    file_url = job_payload.get('fileUrl')
    file_name = job_payload.get('fileName')

    if not job_id:
        logger.error("Job missing jobId, cannot process")
        return

    logger.info(f"Starting processing for job {job_id} (file: {file_url})")
    redis_key = f"job:{job_id}"

    try:
        # 1. Update status to processing
        _update_job_status(redis_client, redis_key, 'processing')
        
        # 2. Download/Ensure local file
        try:
            local_path = storage.ensure_local_path(file_url)
        except Exception as e:
            raise Exception(f"Failed to access file: {str(e)}")

        # 3. Detect type and parse
        file_type = analysis.detect_file_type(file_name or local_path)
        logger.info(f"Detected file type: {file_type}")
        
        try:
            df = analysis.parse_dataset(local_path, file_type)
        except ValueError as ve:
            # Check for non-tabular JSON issue
            if file_type == 'json' and "JSON must be a list" in str(ve):
                # Handle non-tabular JSON
                result_url = _save_non_tabular_result(job_id, file_name, local_path)
                _complete_job(redis_client, redis_key, result_url)
                return
            raise ve
            
        logger.info(f"Parsed DataFrame: {df.shape}")
        
        # 4. Analysis
        schema = analysis.generate_schema(df)
        kpis = analysis.compute_kpis(df, schema)
        preview = analysis.generate_cleaned_preview(df)
        chart_specs = analysis.generate_chart_specs(df, schema)
        quality_score = analysis.compute_quality_score(df, schema, kpis)
        
        # 5. Construct Result
        result_data = {
            "jobId": job_id,
            "fileInfo": { 
                "name": file_name or "unknown", 
                "rows": kpis['rowCount'], 
                "cols": kpis['colCount'], 
                "type": file_type
            },
            "schema": schema,
            "kpis": kpis, # Contains rowCount, colCount, missingCount, numDuplicates, numericStats
            "cleanedPreview": preview,
            "chartSpecs": chart_specs,
            "qualityScore": quality_score,
            "issues": [], # Add specific issues if we tracked them
            "processedAt": datetime.utcnow().isoformat() + "Z"
        }
        
        # 6. Save result
        result_json_str = json.dumps(result_data, indent=2)
        result_stream = io.BytesIO(result_json_str.encode('utf-8'))
        result_url = storage.save_file_to_blob(result_stream, "result.json", job_id)
        
        # 7. Complete
        _complete_job(redis_client, redis_key, result_url)
        
        logger.info(f"Job {job_id} completed successfully. Result: {result_url}")
        
        # Cleanup local download if it was temporary? 
        # storage.ensure_local_path download logic puts it in a timestamped folder.
        # We might want to clean it up. For now, rely on OS or separate cleanup job to avoid deleting if needed for debugging.
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
        _fail_job(redis_client, redis_key, str(e))
        # Don't re-raise if we want the worker to keep running, but worker catches generic exception.
        # Reraise so worker logs it fully if needed
        raise e

def _update_job_status(redis_client, key, status):
    current = _get_job_data(redis_client, key)
    current['status'] = status
    current['updatedAt'] = datetime.utcnow().isoformat() + "Z"
    redis_client.set(key, json.dumps(current))

def _complete_job(redis_client, key, result_url):
    current = _get_job_data(redis_client, key)
    current['status'] = 'completed'
    current['resultUrl'] = result_url
    current['updatedAt'] = datetime.utcnow().isoformat() + "Z"
    redis_client.set(key, json.dumps(current))

def _fail_job(redis_client, key, error_msg):
    current = _get_job_data(redis_client, key)
    current['status'] = 'failed'
    current['error'] = error_msg
    current['updatedAt'] = datetime.utcnow().isoformat() + "Z"
    redis_client.set(key, json.dumps(current))

def _get_job_data(redis_client, key):
    data_str = redis_client.get(key)
    if data_str:
        return json.loads(data_str)
    return {}

def _save_non_tabular_result(job_id, file_name, local_path):
    # Read sample
    try:
        with open(local_path, 'r', encoding='utf-8') as f:
            sample = f.read(1000)
    except:
        sample = "Could not read file."
        
    result_data = {
        "jobId": job_id,
        "fileInfo": { "name": file_name, "type": "json", "rows": 0, "cols": 0 },
        "schema": [],
        "kpis": {"rowCount":0, "colCount":0, "missingCount":0},
        "cleanedPreview": [],
        "chartSpecs": [],
        "qualityScore": 0,
        "issues": ["Non-tabular JSON content detected. Could not parse into rows."],
        "text_extract": sample,
        "processedAt": datetime.utcnow().isoformat() + "Z"
    }
    
    result_json_str = json.dumps(result_data, indent=2)
    result_stream = io.BytesIO(result_json_str.encode('utf-8'))
    return storage.save_file_to_blob(result_stream, "result.json", job_id)
