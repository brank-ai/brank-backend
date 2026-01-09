"""Structured logging configuration."""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Optional log level override
        
    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)

    if level:
        logger.setLevel(getattr(logging, level.upper()))

    # Add handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context,
) -> None:
    """Log message with structured context.
    
    Args:
        logger: Logger instance
        level: Log level (info, warning, error, etc.)
        message: Log message
        **context: Additional context as keyword arguments
    """
    log_method = getattr(logger, level.lower())
    context_str = " | ".join(f"{k}={v}" for k, v in context.items())
    full_message = f"{message} | {context_str}" if context else message
    log_method(full_message)

