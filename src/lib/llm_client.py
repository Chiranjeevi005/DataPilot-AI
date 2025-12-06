import os
import json
import logging
import time
from typing import Dict, Any, Optional
import openai

logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 1
DEFAULT_MODEL = "deepseek/deepseek-r1" # OpenRouter identifier

def _load_prompt(filename: str) -> str:
    """Loads a prompt template from the prompts directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base_dir, "prompts", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load prompt {filename}: {e}")
        return ""

def generate_insights(file_info: Dict, schema: Any, kpis: Dict, preview: Any) -> Dict[str, Any]:
    """
    Generates business insights using OpenRouter (OpenAI SDK) or a Mock LLM.
    Returns a dictionary with 'businessSummary', 'evidence'.
    """
    start_time = time.time()
    
    # 1. Check Mock Mode
    if os.getenv("LLM_MOCK", "false").lower() == "true":
        logger.info("LLM_MOCK=true, returning canned insights.")
        return _get_mock_response()

    # 2. Configure Client (OpenRouter)
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("LLM_MODEL", DEFAULT_MODEL)
    
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set. Returning fallback.")
        return _get_fallback_response("Missing API Key")

    client = openai.OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # 3. Prepare Prompt
    prompt_template = _load_prompt("analyst_prompt.txt")
    if not prompt_template:
        return _get_fallback_response("Prompt load failure")

    prompt = prompt_template.replace("{{FILE_INFO}}", json.dumps(file_info, indent=2))
    prompt = prompt.replace("{{SCHEMA}}", json.dumps(schema, indent=2))
    prompt = prompt.replace("{{KPIS}}", json.dumps(kpis, indent=2))
    prompt = prompt.replace("{{PREVIEW}}", json.dumps(preview, indent=2))

    retries = 0
    last_error = None
    
    while retries <= MAX_RETRIES:
        try:
            logger.info(f"Sending request to LLM ({model_name})...")
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a data analyst. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            latency = time.time() - start_time
            text_response = response.choices[0].message.content
            
            # 4. Parse JSON
            try:
                cleaned_text = text_response.replace("```json", "").replace("```", "").strip()
                result = json.loads(cleaned_text)
                
                # Gap 2: Normalize
                normalized_result = _normalize_insights(result)
                
                normalized_result["_meta"] = {
                    "model": model_name,
                    "latency_seconds": round(latency, 2),
                    "timestamp": time.time()
                }
                return normalized_result

            except json.JSONDecodeError as e:
                logger.warning(f"JSON Parse Error on attempt {retries + 1}: {e}")
                last_error = e

        except Exception as e:
            logger.error(f"LLM API Error on attempt {retries + 1}: {e}")
            last_error = e
        
        retries += 1
        time.sleep(1)

    # 5. Fallback
    logger.error(f"LLM failed after {retries} attempts.")
    return _get_fallback_response(f"LLM Failure: {str(last_error)}")

def _normalize_insights(raw_json: Dict) -> Dict[str, Any]:
    """
    Ensure the output matches the strict schema:
    {
      "analystInsights": [ { "id": "i1", "text": "...", "evidence": {...} } ],
      "businessSummary": [ "...", ... ]
    }
    """
    # 1. Business Summary
    summary = raw_json.get("businessSummary", [])
    if not isinstance(summary, list):
        summary = []
    # Clean strings
    summary = [str(s) for s in summary if s]

    # 2. Insights
    raw_insights = raw_json.get("analystInsights", [])
    if not isinstance(raw_insights, list):
        if isinstance(raw_insights, dict):
            # Try to recover if it returned an object
            raw_insights = [raw_insights]
        else:
            raw_insights = []

    normalized_insights = []
    for idx, item in enumerate(raw_insights):
        if not isinstance(item, dict):
            continue
            
        # Stable ID
        insight_id = f"i{idx+1}"
        text = str(item.get("text", "Insight description missing"))
        
        # Evidence Normalization
        raw_evidence = item.get("evidence", {})
        if not isinstance(raw_evidence, dict):
             raw_evidence = {}
             
        evidence = {
            "aggregates": raw_evidence.get("aggregates", {}),
            "row_indices": raw_evidence.get("row_indices", [])
        }
        
        # Validate row indices are integers
        valid_indices = []
        if isinstance(evidence["row_indices"], list):
            for i in evidence["row_indices"]:
                try:
                    valid_indices.append(int(i))
                except:
                    pass
        evidence["row_indices"] = valid_indices

        normalized_insights.append({
            "id": insight_id,
            "text": text,
            "evidence": evidence
        })

    return {
        "analystInsights": normalized_insights,
        "businessSummary": summary,
        "issues": []
    }

def _get_mock_response() -> Dict[str, Any]:
    return {
        "analystInsights": [
            {
                "id": "i1",
                "text": "Mock Insight 1: Data shows expected mock patterns.",
                "evidence": {
                    "aggregates": {"MockCount": 100},
                    "row_indices": [0, 1]
                }
            }
        ],
        "businessSummary": [
            "Mock Business Summary Point 1",
            "Mock Business Summary Point 2"
        ],
        "_meta": {
            "model": "mock-local",
            "latency_seconds": 0.01
        }
    }

def _get_fallback_response(reason: str) -> Dict[str, Any]:
    return {
        "analystInsights": [],
        "businessSummary": [
            "Automated insights not available.",
            "Please review metadata and charts."
        ],
        "issues": [reason],
        "_meta": {
            "model": "fallback",
            "reason": reason
        }
    }
