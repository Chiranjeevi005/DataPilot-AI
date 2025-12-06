"""
Request and job context tracking for DataPilot AI.
Provides request ID generation and job lifecycle timing.
"""

import uuid
import time
import threading
from datetime import datetime
from typing import Dict, Optional
from contextvars import ContextVar

# Context variables for request tracking
_request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
_job_timers: Dict[str, float] = {}
_timers_lock = threading.Lock()

def generate_request_id() -> str:
    """
    Generate a unique request ID.
    
    Returns:
        UUID-based request ID
    """
    request_id = f"req_{uuid.uuid4().hex[:16]}"
    _request_id_var.set(request_id)
    return request_id

def get_request_id() -> Optional[str]:
    """
    Get current request ID from context.
    
    Returns:
        Request ID or None if not set
    """
    return _request_id_var.get()

def set_request_id(request_id: str):
    """
    Set request ID in context.
    
    Args:
        request_id: Request ID to set
    """
    _request_id_var.set(request_id)

def get_request_context() -> Dict[str, str]:
    """
    Get current request context.
    
    Returns:
        Dictionary with request context (requestId, timestamp)
    """
    return {
        "requestId": get_request_id() or "unknown",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def on_job_start(job_id: str) -> float:
    """
    Mark job start time using monotonic timer.
    
    Args:
        job_id: Job ID
        
    Returns:
        Start time (monotonic)
    """
    start_time = time.monotonic()
    with _timers_lock:
        _job_timers[job_id] = start_time
    return start_time

def on_job_end(job_id: str) -> Optional[float]:
    """
    Mark job end time and calculate duration.
    
    Args:
        job_id: Job ID
        
    Returns:
        Duration in seconds, or None if job was not started
    """
    end_time = time.monotonic()
    
    with _timers_lock:
        start_time = _job_timers.pop(job_id, None)
    
    if start_time is None:
        return None
    
    duration = end_time - start_time
    return duration

def get_job_duration(job_id: str) -> Optional[float]:
    """
    Get current job duration (for in-progress jobs).
    
    Args:
        job_id: Job ID
        
    Returns:
        Duration in seconds since start, or None if job was not started
    """
    current_time = time.monotonic()
    
    with _timers_lock:
        start_time = _job_timers.get(job_id)
    
    if start_time is None:
        return None
    
    duration = current_time - start_time
    return duration

def clear_job_timer(job_id: str):
    """
    Clear job timer (useful for cleanup).
    
    Args:
        job_id: Job ID
    """
    with _timers_lock:
        _job_timers.pop(job_id, None)
