"""
Retry and backoff utilities for DataPilot AI.

Provides exponential backoff with jitter for transient failures.
"""
import time
import random
import logging
from typing import Callable, Tuple, Any, Optional

logger = logging.getLogger(__name__)

# Default retry exceptions (can be extended)
DEFAULT_RETRY_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    IOError,
)


def retry_with_backoff(
    fn: Callable,
    attempts: int = 3,
    initial_delay: float = 0.5,
    factor: float = 2.0,
    max_delay: float = 10.0,
    retry_exceptions: Tuple = DEFAULT_RETRY_EXCEPTIONS,
    operation_name: str = "operation"
) -> Any:
    """
    Retry a function with exponential backoff and jitter.
    
    Args:
        fn: Function to retry (should be a callable with no args, or use lambda)
        attempts: Maximum number of attempts (default 3)
        initial_delay: Initial delay in seconds (default 0.5)
        factor: Backoff multiplier (default 2.0)
        max_delay: Maximum delay in seconds (default 10.0)
        retry_exceptions: Tuple of exceptions to retry on
        operation_name: Name for logging purposes
    
    Returns:
        Result of fn() if successful
        
    Raises:
        Last exception if all attempts fail
        
    Algorithm:
        delay = min(max_delay, initial_delay * factor ** (attempt-1))
        delay *= random.uniform(0.9, 1.1)  # jitter
    """
    last_exception = None
    
    for attempt in range(1, attempts + 1):
        try:
            logger.info(f"{operation_name}: Attempt {attempt}/{attempts}")
            result = fn()
            
            if attempt > 1:
                logger.info(f"{operation_name}: Succeeded on attempt {attempt}")
            
            return result
            
        except retry_exceptions as e:
            last_exception = e
            
            if attempt == attempts:
                logger.error(f"{operation_name}: Failed after {attempts} attempts: {e}")
                raise
            
            # Calculate delay with exponential backoff
            delay = min(max_delay, initial_delay * (factor ** (attempt - 1)))
            
            # Apply jitter (±10%)
            delay *= random.uniform(0.9, 1.1)
            
            logger.warning(
                f"{operation_name}: Attempt {attempt} failed with {type(e).__name__}: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            
            time.sleep(delay)
            
        except Exception as e:
            # Non-retryable exception
            logger.error(f"{operation_name}: Non-retryable error: {type(e).__name__}: {e}")
            raise
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError(f"{operation_name}: Unexpected retry loop exit")


def retry_http_call(
    fn: Callable,
    attempts: int = 3,
    initial_delay: float = 0.5,
    factor: float = 2.0,
    max_delay: float = 10.0,
    operation_name: str = "HTTP call"
) -> Any:
    """
    Retry HTTP calls with special handling for HTTP status codes.
    
    Retries on:
    - 5xx errors (server errors)
    - 429 (rate limit)
    - Network errors
    
    Does NOT retry on:
    - 4xx errors (except 429)
    - Unless it's a possible transient auth issue (401/403) - retry once
    
    Args:
        fn: Function that makes HTTP call and may raise exceptions
        attempts: Maximum attempts
        initial_delay: Initial backoff delay
        factor: Backoff factor
        max_delay: Maximum backoff delay
        operation_name: Name for logging
        
    Returns:
        Result of fn()
    """
    last_exception = None
    
    for attempt in range(1, attempts + 1):
        try:
            logger.info(f"{operation_name}: Attempt {attempt}/{attempts}")
            result = fn()
            
            if attempt > 1:
                logger.info(f"{operation_name}: Succeeded on attempt {attempt}")
            
            return result
            
        except Exception as e:
            last_exception = e
            should_retry = False
            
            # Check if it's an HTTP error with status code
            status_code = None
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                status_code = e.response.status_code
            
            if status_code:
                # Retry on 5xx, 429
                if status_code >= 500 or status_code == 429:
                    should_retry = True
                # Retry once on possible transient auth issues
                elif status_code in (401, 403) and attempt == 1:
                    should_retry = True
                    logger.warning(f"{operation_name}: Auth error, retrying once in case of transient issue")
            else:
                # Network/connection errors - retry
                if isinstance(e, (ConnectionError, TimeoutError, IOError)):
                    should_retry = True
            
            if not should_retry or attempt == attempts:
                logger.error(f"{operation_name}: Failed after {attempt} attempts: {e}")
                raise
            
            # Calculate delay with exponential backoff
            delay = min(max_delay, initial_delay * (factor ** (attempt - 1)))
            delay *= random.uniform(0.9, 1.1)  # jitter
            
            logger.warning(
                f"{operation_name}: Attempt {attempt} failed (status={status_code}). "
                f"Retrying in {delay:.2f}s..."
            )
            
            time.sleep(delay)
    
    if last_exception:
        raise last_exception
    raise RuntimeError(f"{operation_name}: Unexpected retry loop exit")
