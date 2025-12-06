import json
import time
import os
import io
import traceback
from datetime import datetime

try:
    from lib import storage, analysis, pdf_extractor, json_normalize_helper, llm_client
    from lib.analysis.transform_to_ui import transform_to_ui
    from observability import log_info, log_error, log_exception, increment, observe, on_job_start, on_job_end
except ImportError:
    from ..lib import storage, analysis, pdf_extractor, json_normalize_helper, llm_client
    from ..lib.analysis.transform_to_ui import transform_to_ui
    from ..observability import log_info, log_error, log_exception, increment, observe, on_job_start, on_job_end

COMPONENT = "process_job"

def process_job(redis_client, job_payload):
    """
    Process a single job: update status, download, parse, analyze, save result, finish.
    Implements cancellation checking and timeout enforcement.
    """
    job_id = job_payload.get('jobId')
    file_url = job_payload.get('fileUrl')
    file_name = job_payload.get('fileName')

    if not job_id:
        log_error(COMPONENT, "Job missing jobId, cannot process", step="validation")
        return

    log_info(COMPONENT, "Job started", job_id=job_id, step="start", 
             fileUrl=file_url, fileName=file_name)
    
    redis_key = f"job:{job_id}"
    
    # Track start time for timeout enforcement and metrics
    from datetime import datetime
    start_time = datetime.utcnow()
    on_job_start(job_id)

    try:
        # Check for cancellation before starting
        if _is_job_cancelled(redis_client, redis_key):
            log_info(COMPONENT, "Job was cancelled before processing", 
                    job_id=job_id, step="cancelled")
            return
        
        # 1. Update status to processing
        log_info(COMPONENT, "Updating job status to processing", 
                job_id=job_id, step="status_update")
        _update_job_status(redis_client, redis_key, 'processing', start_time=start_time)
        
        # 2. Download/Ensure local file
        log_info(COMPONENT, "Reading blob/file", job_id=job_id, step="read_blob", 
                fileUrl=file_url)
        try:
            local_path = storage.ensure_local_path(file_url)
            log_info(COMPONENT, "File accessed successfully", job_id=job_id, 
                    step="read_blob", localPath=local_path)
        except Exception as e:
            log_error(COMPONENT, f"Failed to access file: {str(e)}", 
                     job_id=job_id, step="read_blob")
            increment("blob_failures_total")
            raise Exception(f"Failed to access file: {str(e)}")

        # 3. Detect type and parse
        file_type = analysis.detect_file_type(file_name or local_path)
        log_info(COMPONENT, "File type detected", job_id=job_id, step="parse", 
                fileType=file_type)
        
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
                     log_info(COMPONENT, "Selected best PDF table", job_id=job_id, 
                             step="parse", score=score, tables=len(candidate_dfs))
                     if score > 0:
                         df = best_df
                     else:
                         log_info(COMPONENT, "PDF table found but score is 0. Treating as non-tabular.", job_id=job_id, step="parse")
                
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
            log_error(COMPONENT, f"Error during parsing/extraction: {e}", 
                     job_id=job_id, step="parse")
            # If we haven't set text_extract, maybe set error as issue
            issues.append(f"Parsing error: {str(e)}")
        
        # Check for cancellation and timeout after parsing
        if _is_job_cancelled(redis_client, redis_key):
            log_info(COMPONENT, "Job was cancelled during parsing", 
                    job_id=job_id, step="cancelled")
            return
        
        if _check_timeout(redis_client, redis_key, start_time, job_id):
            log_error(COMPONENT, "Job timed out during parsing", 
                     job_id=job_id, step="timeout")
            return
            
        # Check if we have a DataFrame to process
        if df is None or df.empty:
             if text_extract is None:
                 text_extract = "No content extracted."
             
             result_url = _save_non_tabular_result(job_id, file_name, file_type, text_extract, issues)
             # Override result_url for local persistence to be web accessible via our API proxy
             result_url = f"/api/results/{job_id}"
             _complete_job(redis_client, redis_key, result_url)
             return

        log_info(COMPONENT, "DataFrame parsed successfully", job_id=job_id, 
                step="parse", rows=df.shape[0], cols=df.shape[1])
        
        # Check again before analysis
        if _is_job_cancelled(redis_client, redis_key):
            log_info(COMPONENT, "Job was cancelled before analysis", 
                    job_id=job_id, step="cancelled")
            return
        
        # 4. Analysis
        log_info(COMPONENT, "Running EDA", job_id=job_id, step="eda")
        schema = analysis.generate_schema(df)
        kpis = analysis.compute_kpis(df, schema)
        preview = analysis.generate_cleaned_preview(df)
        chart_specs = analysis.generate_chart_specs(df, schema)
        quality_score = analysis.compute_quality_score(df, schema, kpis)
        log_info(COMPONENT, "EDA completed", job_id=job_id, step="eda", 
                qualityScore=quality_score)
        
        # Phase 6: LLM Insights
        log_info(COMPONENT, "Running LLM for insights", job_id=job_id, step="llm")
        try:
            insights_data = llm_client.generate_insights(
                file_info={"name": file_name, "type": file_type}, 
                schema=schema, 
                kpis=kpis, 
                preview=preview
            )
            log_info(COMPONENT, "LLM insights generated", job_id=job_id, step="llm")
        except Exception as e:
            log_error(COMPONENT, f"LLM generation failed: {e}", 
                     job_id=job_id, step="llm")
            increment("llm_failures_total")
            # Re-raise to trigger fallback handling
            raise
        
        # 5. Construct Result using Canonical Transformer
        try:
             result_data = transform_to_ui(
                 job_id=job_id,
                 raw_schema=schema,
                 raw_kpis=kpis,
                 cleaned_preview=preview,
                 chart_specs=chart_specs,
                 llm_result=insights_data,
                 quality_score=quality_score
             )
             
             # Add file info (not in generic transformer but needed for specific logic if any? 
             # Actually transform_to_ui covers shared types. 
             # If we need fileInfo in the root, we might need to extend transform_to_ui or add it here.
             # The Interface 'AnalysisResult' in types/analysis.ts DOES NOT have 'fileInfo'.
             # It implies the frontend uses what's in 'kpis' or 'schema'. 
             # However, process_job usually provided 'fileInfo'.
             # Let's check types/analysis.ts again.
             # It does NOT have fileInfo. It has kpis.
             # So we stick to the transformer output.
             pass
        except Exception as e:
             log_error(COMPONENT, f"Transformation failed: {e}", job_id=job_id, step="transform")
             raise e
        
        # 6. Save result
        log_info(COMPONENT, "Writing result.json", job_id=job_id, step="write_result")
        result_json_str = json.dumps(result_data, indent=2)
        result_stream = io.BytesIO(result_json_str.encode('utf-8'))
        try:
            result_url = storage.save_file_to_blob(result_stream, "result.json", job_id)
            log_info(COMPONENT, "Result saved to blob", job_id=job_id, 
                    step="write_result", resultUrl=result_url)
        except Exception as e:
            log_error(COMPONENT, f"Failed to save result: {e}", 
                     job_id=job_id, step="write_result")
            increment("blob_failures_total")
            raise
        
        # 7. Complete
        duration = on_job_end(job_id)
        if duration:
            observe("avg_processing_time_seconds", duration)
            log_info(COMPONENT, "Job completed successfully", job_id=job_id, 
                    step="completed", resultUrl=result_url, durationSeconds=duration)
        else:
            log_info(COMPONENT, "Job completed successfully", job_id=job_id, 
                    step="completed", resultUrl=result_url)
        
        # Override result_url for local persistence to be web accessible via our API proxy
        # In a real cloud deployment with Blob storage, storage.save_file_to_blob would return a valid HTTP URL.
        # But for local dev with file:// return, we must use our proxy.
        result_url = f"/api/results/{job_id}"
        
        _complete_job(redis_client, redis_key, result_url)
        increment("jobs_completed_total")
        
        # Cleanup local download if it was temporary? 
        # storage.ensure_local_path download logic puts it in a timestamped folder.
        # We might want to clean it up. For now, rely on OS or separate cleanup job to avoid deleting if needed for debugging.
        
    except Exception as e:
        log_exception(COMPONENT, "Error processing job", exc_info=e, 
                     job_id=job_id, step="failed")
        
        # Check if job was cancelled during processing
        if _is_job_cancelled(redis_client, redis_key):
            log_info(COMPONENT, "Job was cancelled during processing", 
                    job_id=job_id, step="cancelled")
            return
        
        # Track duration even for failed jobs
        duration = on_job_end(job_id)
        if duration:
            observe("avg_processing_time_seconds", duration)
        
        # Save error.json and fail the job
        _fail_job_with_error_json(redis_client, redis_key, job_id, str(e), "processing_error")
        increment("jobs_failed_total")
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
            log_error(COMPONENT, "Job has timed out", job_id=job_id, step="timeout")
            _fail_job_with_error_json(
                redis_client, key, job_id,
                "Job exceeded maximum processing time",
                "timeout"
            )
            increment("jobs_failed_total")
            return True
        
        return False
    except Exception as e:
        log_error(COMPONENT, f"Error checking timeout: {e}", job_id=job_id, step="timeout")
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
            log_error(COMPONENT, f"Failed to save error.json: {e}", 
                     job_id=job_id, step="error_save")
            increment("blob_failures_total")
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
        
        log_error(COMPONENT, "Job failed", job_id=job_id, step="failed", 
                 errorCode=error_code, errorMessage=error_message)
        
    except Exception as e:
        log_error(COMPONENT, f"Error in _fail_job_with_error_json: {e}", 
                 job_id=job_id, step="error_handling")
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
        "kpis": [
            {"title": "Total Rows", "value": 0, "trend": "neutral"},
            {"title": "Columns", "value": 0, "trend": "neutral"},
            {"title": "Missing Values", "value": 0, "trend": "neutral"},
            {"title": "Duplicates", "value": 0, "trend": "neutral"}
        ],
        "cleanedPreview": [],
        "chartSpecs": [],
        "insights": [],
        "qualityScore": 0,
        "issues": issues if issues else ["Non-tabular content."],
        "text_extract": text_extract,
        "processedAt": datetime.utcnow().isoformat() + "Z"
    }
    
    result_json_str = json.dumps(result_data, indent=2)
    result_stream = io.BytesIO(result_json_str.encode('utf-8'))
    return storage.save_file_to_blob(result_stream, "result.json", job_id)
