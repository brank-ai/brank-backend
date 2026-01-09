"""Retry logic with exponential backoff."""

from typing import Type, Tuple, Callable
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: int = 2,
    max_wait: int = 10,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        exceptions: Tuple of exception types to retry on
        
    Returns:
        Retry decorator
        
    Example:
        @retry_with_backoff(max_attempts=3, exceptions=(TimeoutError,))
        def call_external_api():
            # ... code that might timeout ...
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        reraise=True,
    )

