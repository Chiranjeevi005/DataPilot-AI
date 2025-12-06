"""
Structured JSON logger for DataPilot AI.
Provides unified logging with PII masking and optional Sentry integration.
"""

import os
import sys
import json
import logging
import re
import traceback
from datetime import datetime
from typing import Optional, Dict, Any

# Initialize Sentry if SENTRY_DSN is set
SENTRY_DSN = os.getenv('SENTRY_DSN')
SENTRY_ENABLED = False

if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=0.1,  # 10% of transactions
            profiles_sample_rate=0.1,
            environment=os.getenv('ENVIRONMENT', 'development'),
            before_send=lambda event, hint: _mask_pii_in_sentry_event(event),
        )
        SENTRY_ENABLED = True
        print(f"[OBSERVABILITY] Sentry initialized with DSN: {SENTRY_DSN[:20]}...")
    except ImportError:
        print("[OBSERVABILITY] SENTRY_DSN set but sentry-sdk not installed. Install with: pip install sentry-sdk")
    except Exception as e:
        print(f"[OBSERVABILITY] Failed to initialize Sentry: {e}")

# PII Masking Patterns
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b')
ID_PATTERN = re.compile(r'\b[A-Z0-9]{8,}\b')  # Simple ID-like values (8+ alphanumeric)

def _mask_pii(text: str) -> str:
    """
    Mask PII in text using regex patterns.
    
    Args:
        text: Input text that may contain PII
        
    Returns:
        Text with PII masked
    """
    if not isinstance(text, str):
        return text
    
    # Mask emails
    text = EMAIL_PATTERN.sub('[EMAIL_MASKED]', text)
    
    # Mask phone numbers
    text = PHONE_PATTERN.sub('[PHONE_MASKED]', text)
    
    # Mask ID-like values (be conservative to avoid false positives)
    # Only mask if it looks like a standalone ID
    text = ID_PATTERN.sub('[ID_MASKED]', text)
    
    return text

def _mask_pii_in_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively mask PII in dictionary values.
    
    Args:
        data: Dictionary that may contain PII
        
    Returns:
        Dictionary with PII masked
    """
    if not isinstance(data, dict):
        return data
    
    masked = {}
    for key, value in data.items():
        if isinstance(value, str):
            masked[key] = _mask_pii(value)
        elif isinstance(value, dict):
            masked[key] = _mask_pii_in_dict(value)
        elif isinstance(value, list):
            masked[key] = [_mask_pii_in_dict(item) if isinstance(item, dict) else _mask_pii(str(item)) if isinstance(item, str) else item for item in value]
        else:
            masked[key] = value
    
    return masked

def _mask_pii_in_sentry_event(event):
    """
    Mask PII in Sentry events before sending.
    
    Args:
        event: Sentry event dictionary
        
    Returns:
        Masked event
    """
    if 'message' in event:
        event['message'] = _mask_pii(event['message'])
    
    if 'exception' in event and 'values' in event['exception']:
        for exc in event['exception']['values']:
            if 'value' in exc:
                exc['value'] = _mask_pii(exc['value'])
    
    if 'extra' in event:
        event['extra'] = _mask_pii_in_dict(event['extra'])
    
    return event

class StructuredLogger:
    """
    Structured JSON logger that outputs logs in a consistent format.
    
    All log lines include:
    - timestamp (UTC ISO-8601)
    - level (INFO, WARNING, ERROR, etc.)
    - component (module/service name)
    - jobId (optional, for job-related logs)
    - step (optional, processing step)
    - message (log message)
    - extra (optional, additional context)
    """
    
    def __init__(self, component: str):
        """
        Initialize structured logger for a component.
        
        Args:
            component: Name of the component/module
        """
        self.component = component
        self.log_level = os.getenv('OBSERVABILITY_LOG_LEVEL', 'INFO').upper()
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup Python logger with JSON formatting."""
        self.logger = logging.getLogger(self.component)
        self.logger.setLevel(getattr(logging, self.log_level, logging.INFO))
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, self.log_level, logging.INFO))
        
        # No formatter - we'll handle JSON formatting ourselves
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _format_log(
        self,
        level: str,
        message: str,
        job_id: Optional[str] = None,
        step: Optional[str] = None,
        request_id: Optional[str] = None,
        **extra
    ) -> str:
        """
        Format log entry as JSON.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            job_id: Optional job ID
            step: Optional processing step
            request_id: Optional request ID
            **extra: Additional context fields
            
        Returns:
            JSON-formatted log string
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "component": self.component,
            "message": _mask_pii(message),
        }
        
        if job_id:
            log_entry["jobId"] = job_id
        
        if step:
            log_entry["step"] = step
        
        if request_id:
            log_entry["requestId"] = request_id
        
        if extra:
            # Mask PII in extra fields
            log_entry["extra"] = _mask_pii_in_dict(extra)
        
        return json.dumps(log_entry)
    
    def info(
        self,
        message: str,
        job_id: Optional[str] = None,
        step: Optional[str] = None,
        request_id: Optional[str] = None,
        **extra
    ):
        """Log info message."""
        log_str = self._format_log("INFO", message, job_id, step, request_id, **extra)
        self.logger.info(log_str)
    
    def warning(
        self,
        message: str,
        job_id: Optional[str] = None,
        step: Optional[str] = None,
        request_id: Optional[str] = None,
        **extra
    ):
        """Log warning message."""
        log_str = self._format_log("WARNING", message, job_id, step, request_id, **extra)
        self.logger.warning(log_str)
    
    def error(
        self,
        message: str,
        job_id: Optional[str] = None,
        step: Optional[str] = None,
        request_id: Optional[str] = None,
        **extra
    ):
        """Log error message."""
        log_str = self._format_log("ERROR", message, job_id, step, request_id, **extra)
        self.logger.error(log_str)
        
        # Send to Sentry if enabled
        if SENTRY_ENABLED:
            try:
                import sentry_sdk
                with sentry_sdk.push_scope() as scope:
                    if job_id:
                        scope.set_tag("jobId", job_id)
                    if step:
                        scope.set_tag("step", step)
                    if request_id:
                        scope.set_tag("requestId", request_id)
                    if extra:
                        scope.set_context("extra", _mask_pii_in_dict(extra))
                    
                    sentry_sdk.capture_message(message, level='error')
            except Exception as e:
                self.logger.error(f"Failed to send error to Sentry: {e}")
    
    def exception(
        self,
        message: str,
        exc_info: Optional[Exception] = None,
        job_id: Optional[str] = None,
        step: Optional[str] = None,
        request_id: Optional[str] = None,
        **extra
    ):
        """
        Log exception with stack trace.
        
        Args:
            message: Error message
            exc_info: Exception object (if None, uses sys.exc_info())
            job_id: Optional job ID
            step: Optional processing step
            request_id: Optional request ID
            **extra: Additional context
        """
        # Get exception info
        if exc_info is None:
            exc_info = sys.exc_info()[1]
        
        # Add exception details to extra
        exception_extra = extra.copy()
        if exc_info:
            exception_extra["errorName"] = type(exc_info).__name__
            exception_extra["errorMessage"] = str(exc_info)
            exception_extra["stackTrace"] = traceback.format_exc()
        
        log_str = self._format_log("ERROR", message, job_id, step, request_id, **exception_extra)
        self.logger.error(log_str)
        
        # Send to Sentry if enabled
        if SENTRY_ENABLED and exc_info:
            try:
                import sentry_sdk
                with sentry_sdk.push_scope() as scope:
                    if job_id:
                        scope.set_tag("jobId", job_id)
                    if step:
                        scope.set_tag("step", step)
                    if request_id:
                        scope.set_tag("requestId", request_id)
                    if extra:
                        scope.set_context("extra", _mask_pii_in_dict(extra))
                    
                    sentry_sdk.capture_exception(exc_info)
            except Exception as e:
                self.logger.error(f"Failed to send exception to Sentry: {e}")

# Global logger cache
_loggers: Dict[str, StructuredLogger] = {}

def get_logger(component: str) -> StructuredLogger:
    """
    Get or create a structured logger for a component.
    
    Args:
        component: Component/module name
        
    Returns:
        StructuredLogger instance
    """
    if component not in _loggers:
        _loggers[component] = StructuredLogger(component)
    return _loggers[component]

# Convenience functions for default logger
_default_logger = get_logger("datapilot")

def log_info(
    component: str,
    message: str,
    job_id: Optional[str] = None,
    step: Optional[str] = None,
    request_id: Optional[str] = None,
    **extra
):
    """Log info message with component."""
    logger = get_logger(component)
    logger.info(message, job_id=job_id, step=step, request_id=request_id, **extra)

def log_warning(
    component: str,
    message: str,
    job_id: Optional[str] = None,
    step: Optional[str] = None,
    request_id: Optional[str] = None,
    **extra
):
    """Log warning message with component."""
    logger = get_logger(component)
    logger.warning(message, job_id=job_id, step=step, request_id=request_id, **extra)

def log_error(
    component: str,
    message: str,
    job_id: Optional[str] = None,
    step: Optional[str] = None,
    request_id: Optional[str] = None,
    **extra
):
    """Log error message with component."""
    logger = get_logger(component)
    logger.error(message, job_id=job_id, step=step, request_id=request_id, **extra)

def log_exception(
    component: str,
    message: str,
    exc_info: Optional[Exception] = None,
    job_id: Optional[str] = None,
    step: Optional[str] = None,
    request_id: Optional[str] = None,
    **extra
):
    """Log exception with stack trace."""
    logger = get_logger(component)
    logger.exception(message, exc_info=exc_info, job_id=job_id, step=step, request_id=request_id, **extra)
