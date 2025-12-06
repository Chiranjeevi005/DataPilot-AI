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
            
        # Check if we have a DataFrame to process
        if df is None or df.empty:
             if text_extract is None:
                 text_extract = "No content extracted."
             
             result_url = _save_non_tabular_result(job_id, file_name, file_type, text_extract, issues)
             _complete_job(redis_client, redis_key, result_url)
             return

        logger.info(f"Parsed DataFrame: {df.shape}")
        
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
