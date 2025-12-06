import os
import json
import logging
import time
from typing import Dict, Any, Optional
import openai

try:
    from lib.llm import format_enforcer, validator
    from .retry import retry_http_call
except ImportError:
    from lib.llm import format_enforcer, validator
    from retry import retry_http_call

# Initialize logger
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 1
DEFAULT_MODEL = "deepseek/deepseek-r1" # OpenRouter identifier

# Configuration from env
LLM_RETRY_ATTEMPTS = int(os.getenv('LLM_RETRY_ATTEMPTS', '2'))
RETRY_INITIAL_DELAY = float(os.getenv('RETRY_INITIAL_DELAY', '0.5'))
RETRY_FACTOR = float(os.getenv('RETRY_FACTOR', '2.0'))
RETRY_MAX_DELAY = float(os.getenv('RETRY_MAX_DELAY', '10'))

# Circuit Breaker Configuration
LLM_CIRCUIT_THRESHOLD = int(os.getenv('LLM_CIRCUIT_THRESHOLD', '5'))
LLM_CIRCUIT_WINDOW = int(os.getenv('LLM_CIRCUIT_WINDOW', '300'))  # seconds
LLM_CIRCUIT_COOLDOWN = int(os.getenv('LLM_CIRCUIT_COOLDOWN', '600'))  # seconds

# Circuit Breaker State (in-memory, simple implementation)
_circuit_breaker_state = {
    'failures': [],  # List of failure timestamps
    'is_open': False,
    'opened_at': None
}

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

def _check_circuit_breaker() -> bool:
    """
    Check if circuit breaker is open.
    Returns True if circuit is open (should use fallback), False otherwise.
    """
    current_time = time.time()
    
    # Check if circuit is open and cooldown period has passed
    if _circuit_breaker_state['is_open']:
        if _circuit_breaker_state['opened_at'] and \
           (current_time - _circuit_breaker_state['opened_at']) >= LLM_CIRCUIT_COOLDOWN:
            # Cooldown complete, close circuit
            logger.info("Circuit breaker cooldown complete. Closing circuit.")
            _circuit_breaker_state['is_open'] = False
            _circuit_breaker_state['opened_at'] = None
            _circuit_breaker_state['failures'] = []
            return False
        else:
            logger.warning("Circuit breaker is OPEN. Using fallback.")
            return True
    
    # Clean old failures outside the window
    window_start = current_time - LLM_CIRCUIT_WINDOW
    _circuit_breaker_state['failures'] = [
        ts for ts in _circuit_breaker_state['failures'] if ts >= window_start
    ]
    
    # Check if threshold exceeded
    if len(_circuit_breaker_state['failures']) >= LLM_CIRCUIT_THRESHOLD:
        logger.error(
            f"Circuit breaker OPENING: {len(_circuit_breaker_state['failures'])} failures "
            f"within {LLM_CIRCUIT_WINDOW}s window (threshold: {LLM_CIRCUIT_THRESHOLD})"
        )
        _circuit_breaker_state['is_open'] = True
        _circuit_breaker_state['opened_at'] = current_time
        return True
    
    return False

def _record_llm_failure():
    """Record an LLM failure for circuit breaker tracking."""
    _circuit_breaker_state['failures'].append(time.time())
    logger.debug(f"Recorded LLM failure. Total in window: {len(_circuit_breaker_state['failures'])}")

def _record_llm_success():
    """Record an LLM success - reset failure count."""
    if _circuit_breaker_state['failures']:
        logger.debug("LLM success. Clearing failure history.")
        _circuit_breaker_state['failures'] = []


def generate_insights(file_info: Dict, schema: Any, kpis: Dict, preview: Any) -> Dict[str, Any]:
    """
    Generates business insights using OpenRouter (OpenAI SDK) or a Mock LLM.
    Returns a dictionary with 'businessSummary', 'evidence'.
    Implements circuit breaker and retry logic for production resilience.
    """
    start_time = time.time()
    
    # 1. Check Mock Mode
    if os.getenv("LLM_MOCK", "false").lower() == "true":
        logger.info("LLM_MOCK=true, returning canned insights.")
        return _get_mock_response()

    # 2. Check Circuit Breaker
    if _check_circuit_breaker():
        logger.warning("Circuit breaker is open. Using deterministic fallback.")
        return _get_fallback_response("circuit_breaker_open")

    # 3. Configure Client (OpenRouter)
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("LLM_MODEL", DEFAULT_MODEL)
    
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set. Returning fallback.")
        _record_llm_failure()
        return _get_fallback_response("missing_api_key")

    client = openai.OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # 4. Prepare Prompt
    prompt_template = _load_prompt("analyst_prompt.txt")
    if not prompt_template:
        _record_llm_failure()
        return _get_fallback_response("prompt_load_failure")

    prompt = prompt_template.replace("{{FILE_INFO}}", json.dumps(file_info, indent=2))
    prompt = prompt.replace("{{SCHEMA}}", json.dumps(schema, indent=2))
    prompt = prompt.replace("{{KPIS}}", json.dumps(kpis, indent=2))
    prompt = prompt.replace("{{PREVIEW}}", json.dumps(preview, indent=2))
    
    # Enforce detailed JSON format
    prompt = format_enforcer.wrap_prompt(prompt)

    # 5. Make LLM Call with Retry
    def _make_llm_call():
        """Inner function for retry wrapper"""
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
        
        # Parse JSON
        try:
            # Clean and Parse
            result = format_enforcer.enforce_json_format(text_response)
            
            # Validate Data Structure
            normalized_result = validator.validate_llm_result(result)
            
            normalized_result["_meta"] = {
                "model": model_name,
                "latency_seconds": round(latency, 2),
                "timestamp": time.time()
            }
            
            # Success!
            _record_llm_success()
            logger.info(f"LLM call succeeded in {latency:.2f}s")
            return normalized_result
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON Parse Error: {e}")
            raise ValueError(f"Invalid JSON from LLM: {e}")
    
    try:
        # Use retry_http_call wrapper
        return retry_http_call(
            _make_llm_call,
            attempts=LLM_RETRY_ATTEMPTS,
            initial_delay=RETRY_INITIAL_DELAY,
            factor=RETRY_FACTOR,
            max_delay=RETRY_MAX_DELAY,
            operation_name=f"LLM call ({model_name})"
        )
    except Exception as e:
        # All retries failed
        logger.error(f"LLM failed after {LLM_RETRY_ATTEMPTS} attempts: {e}")
        _record_llm_failure()
        return _get_fallback_response(f"llm_failure_fallback: {str(e)}")

# Normalization logic moved to validator.py

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
