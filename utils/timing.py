"""Performance timing utilities."""

import time
import logging
from functools import wraps
from typing import Callable, Any


def timing_decorator(logger: logging.Logger) -> Callable:
    """Decorator to measure and log function execution time.
    
    Args:
        logger: Logger instance to use for logging
        
    Returns:
        Decorator function
        
    Example:
        @timing_decorator(logger)
        def expensive_function():
            # ... code ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"{func.__name__} completed in {duration:.3f}s",
                    extra={"duration_seconds": duration, "function": func.__name__},
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {duration:.3f}s: {e}",
                    extra={"duration_seconds": duration, "function": func.__name__},
                )
                raise

        return wrapper

    return decorator


class Timer:
    """Context manager for timing code blocks.
    
    Example:
        with Timer() as t:
            # ... expensive code ...
        print(f"Took {t.elapsed}s")
    """

    def __init__(self):
        """Initialize timer."""
        self.start: float = 0.0
        self.end: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self):
        """Start timer."""
        self.start = time.time()
        return self

    def __exit__(self, *args):
        """Stop timer and calculate elapsed time."""
        self.end = time.time()
        self.elapsed = self.end - self.start

