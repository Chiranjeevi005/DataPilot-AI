"""
LLM Client with Few-Shot Prompt Support

Responsibilities:
- Encapsulate calls to OpenRouter/DeepSeek R1
- Use prompt_manager to build few-shot prompts
- Implement retry logic with structural repair attempts
- Integrate insight_validator for output validation
- Fall back to deterministic templates on failure
- Audit logging (prompt hash, model, duration, validation outcome)
"""

import os
import json
import logging
import time
from typing import Dict, Any, Optional
import openai

try:
    from .prompt_manager import build_prompt, get_prompt_hash
    from .insight_validator import validate_and_normalize
    from .fallback_generator import generate_fallback_insights
    from .retry import retry_http_call
except ImportError:
    from prompt_manager import build_prompt, get_prompt_hash
    from insight_validator import validate_and_normalize
    from fallback_generator import generate_fallback_insights
    from retry import retry_http_call

logger = logging.getLogger(__name__)

# Configuration from env
LLM_RETRY_ATTEMPTS = int(os.getenv('LLM_RETRY_ATTEMPTS', '2'))
RETRY_INITIAL_DELAY = float(os.getenv('RETRY_INITIAL_DELAY', '0.5'))
RETRY_FACTOR = float(os.getenv('RETRY_FACTOR', '2.0'))
RETRY_MAX_DELAY = float(os.getenv('RETRY_MAX_DELAY', '10'))
DEFAULT_MODEL = "deepseek/deepseek-r1"
FEWSHOT_DEFAULT_COUNT = int(os.getenv('FEWSHOT_DEFAULT_COUNT', '3'))

# Circuit Breaker Configuration
LLM_CIRCUIT_THRESHOLD = int(os.getenv('LLM_CIRCUIT_THRESHOLD', '5'))
LLM_CIRCUIT_WINDOW = int(os.getenv('LLM_CIRCUIT_WINDOW', '300'))  # seconds
LLM_CIRCUIT_COOLDOWN = int(os.getenv('LLM_CIRCUIT_COOLDOWN', '600'))  # seconds

# Circuit Breaker State (in-memory)
_circuit_breaker_state = {
    'failures': [],
    'is_open': False,
    'opened_at': None
}


def _check_circuit_breaker() -> bool:
    """Check if circuit breaker is open."""
    current_time = time.time()
    
    if _circuit_breaker_state['is_open']:
        if _circuit_breaker_state['opened_at'] and \
           (current_time - _circuit_breaker_state['opened_at']) >= LLM_CIRCUIT_COOLDOWN:
            logger.info("Circuit breaker cooldown complete. Closing circuit.")
            _circuit_breaker_state['is_open'] = False
            _circuit_breaker_state['opened_at'] = None
            _circuit_breaker_state['failures'] = []
            return False
        else:
            logger.warning("Circuit breaker is OPEN. Using fallback.")
            return True
    
    # Clean old failures outside window
    window_start = current_time - LLM_CIRCUIT_WINDOW
    _circuit_breaker_state['failures'] = [
        ts for ts in _circuit_breaker_state['failures'] if ts >= window_start
    ]
    
    # Check threshold
    if len(_circuit_breaker_state['failures']) >= LLM_CIRCUIT_THRESHOLD:
        logger.error(
            f"Circuit breaker OPENING: {len(_circuit_breaker_state['failures'])} failures "
            f"within {LLM_CIRCUIT_WINDOW}s (threshold: {LLM_CIRCUIT_THRESHOLD})"
        )
        _circuit_breaker_state['is_open'] = True
        _circuit_breaker_state['opened_at'] = current_time
        return True
    
    return False


def _record_llm_failure():
    """Record LLM failure for circuit breaker."""
    _circuit_breaker_state['failures'].append(time.time())
    logger.debug(f"Recorded LLM failure. Total in window: {len(_circuit_breaker_state['failures'])}")


def _record_llm_success():
    """Record LLM success - reset failure count."""
    if _circuit_breaker_state['failures']:
        logger.debug("LLM success. Clearing failure history.")
        _circuit_breaker_state['failures'] = []


def _log_llm_audit(job_id: str, prompt_hash: str, model: str, duration: float, 
                   validation_passed: bool, issues: list):
    """
    Log LLM call audit information.
    
    Args:
        job_id: Job identifier
        prompt_hash: SHA-256 hash of prompt (for deduplication, not content)
        model: Model name
        duration: Call duration in seconds
        validation_passed: Whether validation succeeded
        issues: List of validation issues
    """
    audit_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "llm_logs"
    )
    os.makedirs(audit_dir, exist_ok=True)
    
    audit_entry = {
        "timestamp": time.time(),
        "job_id": job_id,
        "prompt_hash": prompt_hash,
        "model": model,
        "duration_seconds": round(duration, 2),
        "validation_passed": validation_passed,
        "issue_count": len(issues),
        "issues": issues[:10]  # Limit to first 10 issues
    }
    
    # Append to daily log file
    from datetime import datetime
    log_file = os.path.join(audit_dir, f"llm_audit_{datetime.utcnow().strftime('%Y%m%d')}.jsonl")
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")


def generate_insights_fewshot(compact_eda: Dict[str, Any], job_id: str = "unknown") -> Dict[str, Any]:
    """
    Generate insights using few-shot prompt approach.
    
    Flow:
    1. Check mock mode
    2. Check circuit breaker
    3. Build few-shot prompt
    4. Call LLM with retry
    5. Validate output
    6. If validation fails, retry with "fix structure" instruction
    7. If still fails, fall back to deterministic template
    
    Args:
        compact_eda: Compact EDA JSON with kpis, schema, cleanedPreview, chartSpecs
        job_id: Job identifier for audit logging
        
    Returns:
        Dictionary with analystInsights, businessSummary, visualActions, metadata, issues
    """
    start_time = time.time()
    
    # 1. Check Mock Mode
    if os.getenv("LLM_MOCK", "false").lower() == "true":
        logger.info("LLM_MOCK=true, returning canned insights.")
        return _get_mock_response()
    
    # 2. Check Circuit Breaker
    if _check_circuit_breaker():
        logger.warning("Circuit breaker is open. Using deterministic fallback.")
        return generate_fallback_insights(compact_eda)
    
    # 3. Configure Client
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("LLM_MODEL", DEFAULT_MODEL)
    
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set. Returning fallback.")
        _record_llm_failure()
        return generate_fallback_insights(compact_eda)
    
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    
    # 4. Build Few-Shot Prompt
    try:
        prompt = build_prompt(compact_eda, shot_count=FEWSHOT_DEFAULT_COUNT)
        prompt_hash = get_prompt_hash(prompt)
        logger.info(f"Built few-shot prompt: {len(prompt)} chars, hash: {prompt_hash}")
    except Exception as e:
        logger.error(f"Failed to build prompt: {e}")
        _record_llm_failure()
        return generate_fallback_insights(compact_eda)
    
    # 5. Make LLM Call with Retry
    def _make_llm_call(fix_structure: bool = False):
        """Inner function for LLM call."""
        final_prompt = prompt
        if fix_structure:
            final_prompt += "\n\nIMPORTANT: Your previous response had structural issues. Please ensure you return ONLY valid JSON matching the exact schema provided, with no markdown formatting."
        
        logger.info(f"Calling LLM ({model_name}){'with fix instruction' if fix_structure else ''}...")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a data analyst. Output valid JSON only."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.0,
            max_tokens=800,
            timeout=30
        )
        
        return response.choices[0].message.content
    
    # First attempt
    try:
        raw_response = retry_http_call(
            _make_llm_call,
            attempts=LLM_RETRY_ATTEMPTS,
            initial_delay=RETRY_INITIAL_DELAY,
            factor=RETRY_FACTOR,
            max_delay=RETRY_MAX_DELAY,
            operation_name=f"LLM call ({model_name})"
        )
        
        # Parse JSON
        try:
            # Remove markdown code blocks if present
            cleaned_text = raw_response.replace("```json", "").replace("```", "").strip()
            raw_output = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error on first attempt: {e}")
            
            # Retry with fix instruction
            logger.info("Retrying with structural fix instruction...")
            raw_response = retry_http_call(
                lambda: _make_llm_call(fix_structure=True),
                attempts=1,
                initial_delay=RETRY_INITIAL_DELAY,
                factor=RETRY_FACTOR,
                max_delay=RETRY_MAX_DELAY,
                operation_name=f"LLM call with fix ({model_name})"
            )
            
            cleaned_text = raw_response.replace("```json", "").replace("```", "").strip()
            raw_output = json.loads(cleaned_text)
        
        # 6. Validate Output
        normalized_output, issues = validate_and_normalize(raw_output, compact_eda)
        
        duration = time.time() - start_time
        validation_passed = normalized_output is not None
        
        # Audit logging
        _log_llm_audit(job_id, prompt_hash, model_name, duration, validation_passed, issues)
        
        if normalized_output:
            # Add metadata
            normalized_output['_meta'] = {
                'model': model_name,
                'latency_seconds': round(duration, 2),
                'timestamp': time.time(),
                'prompt_hash': prompt_hash,
                'validation_issues': len(issues)
            }
            
            _record_llm_success()
            logger.info(f"LLM call succeeded in {duration:.2f}s with {len(issues)} validation issues")
            return normalized_output
        else:
            # Validation failed critically
            logger.error(f"Validation failed critically: {issues}")
            _record_llm_failure()
            return generate_fallback_insights(compact_eda)
    
    except Exception as e:
        # All retries failed
        duration = time.time() - start_time
        logger.error(f"LLM failed after retries: {e}")
        _record_llm_failure()
        
        # Audit logging for failure
        _log_llm_audit(job_id, prompt_hash if 'prompt_hash' in locals() else "unknown", 
                      model_name, duration, False, [str(e)])
        
        return generate_fallback_insights(compact_eda)


def _get_mock_response() -> Dict[str, Any]:
    """Return mock response for testing."""
    return {
        "analystInsights": [
            {
                "id": "i1",
                "text": "Mock Insight: Data shows expected patterns for testing purposes.",
                "severity": "low",
                "category": "quality",
                "evidence": {
                    "aggregates": {"MockCount": 100},
                    "row_indices": [0, 1],
                    "chart_id": None
                },
                "recommendation": {
                    "who": "analyst",
                    "what": "Review mock data configuration",
                    "priority": "low"
                }
            }
        ],
        "businessSummary": [
            "Mock Business Summary: This is test data generated in mock mode.",
            "Enable real LLM by setting LLM_MOCK=false and providing OPENROUTER_API_KEY."
        ],
        "visualActions": [],
        "metadata": {
            "total_insights": 1,
            "confidence": "low",
            "data_quality_score": 0,
            "analysis_timestamp": ""
        },
        "_meta": {
            "model": "mock-local",
            "latency_seconds": 0.01,
            "timestamp": time.time()
        }
    }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    sample_eda = {
        "kpis": {
            "rowCount": 150,
            "columnCount": 5,
            "missingCells": 3,
            "duplicateRows": 0,
            "numericStats": {
                "Revenue": {"min": 1200, "max": 185000, "mean": 8500, "median": 7200, "std": 15000}
            }
        },
        "schema": [
            {"column": "Date", "type": "date", "missing": 0, "unique": 150}
        ],
        "cleanedPreview": [
            {"Date": "2024-01-15", "Revenue": 7200},
            {"Date": "2024-01-16", "Revenue": 185000}
        ],
        "chartSpecs": [
            {"id": "chart_1", "type": "timeseries", "x": "Date", "y": "Revenue"}
        ]
    }
    
    result = generate_insights_fewshot(sample_eda, job_id="test_123")
    print(json.dumps(result, indent=2))
