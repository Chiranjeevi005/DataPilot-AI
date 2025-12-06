import sys
import os
import json
import logging
import io

# Modify path to allow imports
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.append(base_path)

# Ensure environment variables are loaded if using python-dotenv?
# We assume env is set or passed.

from lib import storage, llm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reprocess")

def reprocess(job_id):
    logger.info(f"Reprocessing LLM for {job_id}")
    
    # 1. Locate result.json
    path = storage.get_storage_path(job_id, "result.json")
    if not os.path.exists(path):
        logger.error(f"result.json not found at {path}")
        sys.exit(1)
        
    with open(path, 'r', encoding='utf-8') as f:
        result_data = json.load(f)
        
    # 2. Extract Data
    schema = result_data.get('schema')
    kpis = result_data.get('kpis')
    preview = result_data.get('cleanedPreview')
    file_info = result_data.get('fileInfo', {})
    
    if not all([schema, kpis, preview]):
        logger.error("Missing EDA data in result.json")
        sys.exit(1)
        
    # 3. Call LLM
    logger.info("Calling LLM...")
    insights_data = llm_client.generate_insights(
        file_info=file_info,
        schema=schema,
        kpis=kpis,
        preview=preview
    )
    
    result_data['analystInsights'] = {
         "businessSummary": insights_data.get("businessSummary", []),
         "evidence": insights_data.get("evidence", [])
    }
    
    # Update issues
    if "issues" in insights_data:
         # Append unique
         current_issues = set(result_data.get('issues', []))
         for issue in insights_data["issues"]:
              current_issues.add(f"LLM: {issue}")
         result_data['issues'] = list(current_issues)

    # 4. Save
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2)
        
    logger.info(f"Updated result.json for {job_id}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reprocess_job.py <jobId>")
        sys.exit(1)
    reprocess(sys.argv[1])
