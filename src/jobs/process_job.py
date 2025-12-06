import json
import time
import logging
import os
import io
import traceback
from datetime import datetime

# Adjust import based on how the worker is run. 
try:
    from lib import storage, analysis, pdf_extractor, json_normalize_helper, llm_client
except ImportError:
    # Fallback for relative imports if needed
    from ..lib import storage, analysis, pdf_extractor, json_normalize_helper, llm_client

logger = logging.getLogger(__name__)

def process_job(redis_client, job_payload):
    """
    Process a single job: update status, download, parse, analyze, save result, finish.
    Implements cancellation checking and timeout enforcement.
    """
    job_id = job_payload.get('jobId')
    file_url = job_payload.get('fileUrl')
    file_name = job_payload.get('fileName')

    if not job_id:
        logger.error("Job missing jobId, cannot process")
        return

    logger.info(f"Starting processing for job {job_id} (file: {file_url})")
    redis_key = f"job:{job_id}"
    
    # Track start time for timeout enforcement
    from datetime import datetime
    start_time = datetime.utcnow()

    try:
        # Check for cancellation before starting
        if _is_job_cancelled(redis_client, redis_key):
            logger.info(f"Job {job_id} was cancelled. Exiting.")
            return
        
        # 1. Update status to processing
        _update_job_status(redis_client, redis_key, 'processing', start_time=start_time)
        
        # 2. Download/Ensure local file
        try:
            local_path = storage.ensure_local_path(file_url)
        except Exception as e:
            raise Exception(f"Failed to access file: {str(e)}")

        # 3. Detect type and parse
        file_type = analysis.detect_file_type(file_name or local_path)
        logger.info(f"Detected file type: {file_type}")
        
        df = None
        text_extract = None
        issues = []
        
        try:
            if file_type == 'pdf':
                # PDF Extraction
                candidate_dfs = pdf_extractor.extract_tables_from_pdf(local_path)
                if candidate_dfs:
                     # Pick best
                     best_df = max(candidate_dfs, key=pdf_extractor.score_table)
                     score = pdf_extractor.score_table(best_df)
                     logger.info(f"Selected best PDF table with score {score}")
                     if score > 0:
                         df = best_df
                     else:
                         logger.info("PDF table found but score is 0. Treating as non-tabular.")
                
                if df is None:
                    # Text fallback
                    text_extract = pdf_extractor.extract_text_from_pdf(local_path)
                    issues.append({"type":"non_tabular_pdf","message":"No high-quality tables detected; text_extract provided."})

            elif file_type == 'json':
                # JSON Normalization
                with open(local_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                df = json_normalize_helper.normalize_json_to_df(json_data)
                
                if df is None:
                    # Fallback sample
                    # Re-read or just use json_data
                    sample_str = json.dumps(json_data, indent=2)
                    text_extract = sample_str[:1000]
                    issues.append("Non-tabular JSON content detected. Could not parse into rows.")
            
            else:
                # Standard Parsing (CSV, XLSX, basic JSON fallback)
                try:
                    df = analysis.parse_dataset(local_path, file_type)
                except ValueError as ve:
                    if file_type == 'json' and "JSON must be a list" in str(ve):
                         # Should have been handled above if we trust our new helper, 
                         # but analysis.parse_dataset isn't used for JSON if we enter the block above?
                         # Wait, if I changed the logic to use json_normalize_helper for 'json', 
                         # then analysis.parse_dataset won't be called for 'json' unless I fallback?
                         # The 'if file_type == 'json'' block above handles it.
                         # exact match logic.
                         pass
                    raise ve

        except Exception as e:
            logger.error(f"Error during parsing/extraction: {e}")
            # If we haven't set text_extract, maybe set error as issue
            issues.append(f"Parsing error: {str(e)}")
        
        # Check for cancellation and timeout after parsing
        if _is_job_cancelled(redis_client, redis_key):
            logger.info(f"Job {job_id} was cancelled during parsing.")
            return
        
        if _check_timeout(redis_client, redis_key, start_time, job_id):
            logger.warning(f"Job {job_id} timed out during parsing.")
            return
            
        # Check if we have a DataFrame to process
        if df is None or df.empty:
             if text_extract is None:
                 text_extract = "No content extracted."
             
             result_url = _save_non_tabular_result(job_id, file_name, file_type, text_extract, issues)
             _complete_job(redis_client, redis_key, result_url)
             return

        logger.info(f"Parsed DataFrame: {df.shape}")
        
        # Check again before analysis
        if _is_job_cancelled(redis_client, redis_key):
            logger.info(f"Job {job_id} was cancelled before analysis.")
            return
        
        # 4. Analysis
        schema = analysis.generate_schema(df)
        kpis = analysis.compute_kpis(df, schema)
        preview = analysis.generate_cleaned_preview(df)
        chart_specs = analysis.generate_chart_specs(df, schema)
        quality_score = analysis.compute_quality_score(df, schema, kpis)
        
        # Phase 6: LLM Insights
        logger.info("Generating LLM insights...")
        insights_data = llm_client.generate_insights(
            file_info={"name": file_name, "type": file_type}, 
            schema=schema, 
            kpis=kpis, 
            preview=preview
        )
        
        # Gap 2: Flattened Structure (Gap Fixing)
        # insights_data is now normalized by llm_client to contain:
        # { "analystInsights": [...], "businessSummary": [...], "issues": [...] }
        
        analyst_insights = insights_data.get("analystInsights", [])
        business_summary = insights_data.get("businessSummary", [])
        
        if "issues" in insights_data:
             for issue in insights_data["issues"]:
                  issues.append(f"LLM: {issue}")

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
            "kpis": kpis, 
            "cleanedPreview": preview,
            "analystInsights": analyst_insights,
            "businessSummary": business_summary,
            "chartSpecs": chart_specs,
            "qualityScore": quality_score,
            "issues": issues, 
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
        
        # Check if job was cancelled during processing
        if _is_job_cancelled(redis_client, redis_key):
            logger.info(f"Job {job_id} was cancelled during processing.")
            return
        
        # Save error.json and fail the job
        _fail_job_with_error_json(redis_client, redis_key, job_id, str(e), "processing_error")
        # Don't re-raise - let worker continue

def _is_job_cancelled(redis_client, key):
    """Check if job has been cancelled."""
    try:
        data = _get_job_data(redis_client, key)
        return data.get('status') == 'cancelled'
    except:
        return False

def _check_timeout(redis_client, key, start_time, job_id):
    """
    Check if job has exceeded timeout.
    Returns True if timed out (and updates job status), False otherwise.
    """
    try:
        data = _get_job_data(redis_client, key)
        timeout_at_str = data.get('timeoutAt')
        
        if not timeout_at_str:
            return False
        
        from datetime import datetime
        timeout_at = datetime.fromisoformat(timeout_at_str.replace('Z', '+00:00'))
        now = datetime.utcnow()
        
        if now > timeout_at.replace(tzinfo=None):
            logger.warning(f"Job {job_id} has timed out")
            _fail_job_with_error_json(
                redis_client, key, job_id,
                "Job exceeded maximum processing time",
                "timeout"
            )
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking timeout: {e}")
        return False

def _update_job_status(redis_client, key, status, start_time=None):
    current = _get_job_data(redis_client, key)
    current['status'] = status
    current['updatedAt'] = datetime.utcnow().isoformat() + "Z"
    
    if start_time and status == 'processing':
        current['startedAt'] = start_time.isoformat() + "Z"
    
    redis_client.set(key, json.dumps(current))

def _complete_job(redis_client, key, result_url):
    current = _get_job_data(redis_client, key)
    current['status'] = 'completed'
    current['resultUrl'] = result_url
    current['updatedAt'] = datetime.utcnow().isoformat() + "Z"
    redis_client.set(key, json.dumps(current))

def _fail_job(redis_client, key, error_msg):
    """Simple fail without error.json (for backwards compatibility)"""
    current = _get_job_data(redis_client, key)
    current['status'] = 'failed'
    current['error'] = 'processing_error'
    current['errorMessage'] = error_msg
    current['updatedAt'] = datetime.utcnow().isoformat() + "Z"
    redis_client.set(key, json.dumps(current))

def _fail_job_with_error_json(redis_client, key, job_id, error_message, error_code):
    """
    Fail job and save error.json to blob storage.
    
    Args:
        redis_client: Redis client
        key: Job Redis key
        job_id: Job ID
        error_message: Human-readable error message
        error_code: Short error code (e.g., 'timeout', 'blob_upload_failed', etc.)
    """
    try:
        # Create error.json
        error_data = {
            "jobId": job_id,
            "status": "failed",
            "error": error_code,
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Save error.json to blob
        error_json_str = json.dumps(error_data, indent=2)
        error_stream = io.BytesIO(error_json_str.encode('utf-8'))
        
        try:
            error_url = storage.save_file_to_blob(error_stream, "error.json", job_id)
        except Exception as e:
            logger.error(f"Failed to save error.json for job {job_id}: {e}")
            error_url = None
        
        # Update job status
        current = _get_job_data(redis_client, key)
        current['status'] = 'failed'
        current['error'] = error_code
        current['errorMessage'] = error_message
        current['updatedAt'] = datetime.utcnow().isoformat() + "Z"
        
        if error_url:
            current['resultUrl'] = error_url
        
        redis_client.set(key, json.dumps(current))
        
        logger.info(f"Job {job_id} failed with error: {error_code}")
        
    except Exception as e:
        logger.error(f"Error in _fail_job_with_error_json: {e}")
        # Fallback to simple fail
        _fail_job(redis_client, key, error_message)

def _get_job_data(redis_client, key):
    data_str = redis_client.get(key)
    if data_str:
        return json.loads(data_str)
    return {}

def _save_non_tabular_result(job_id, file_name, file_type, text_extract, issues):
    # Construct result for non-tabular
    result_data = {
        "jobId": job_id,
        "fileInfo": { "name": file_name, "type": file_type, "rows": 0, "cols": 0 },
        "schema": [],
        "kpis": {"rowCount":0, "colCount":0, "missingCount":0},
        "cleanedPreview": [],
        "chartSpecs": [],
        "qualityScore": 0,
        "issues": issues if issues else ["Non-tabular content."],
        "text_extract": text_extract,
        "processedAt": datetime.utcnow().isoformat() + "Z"
    }
    
    result_json_str = json.dumps(result_data, indent=2)
    result_stream = io.BytesIO(result_json_str.encode('utf-8'))
    return storage.save_file_to_blob(result_stream, "result.json", job_id)
