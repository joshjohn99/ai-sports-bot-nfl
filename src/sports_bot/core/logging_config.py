"""
Logging configuration for the sports bot.
"""

import logging
import sys
from typing import Optional

def setup_logging(
    log_level: str = "INFO",
    app_name: Optional[str] = None
) -> logging.Logger:
    """Set up logging configuration.
    
    Args:
        log_level: Logging level (default: INFO)
        app_name: Application name for logger (default: sports_bot)
        
    Returns:
        Configured logger
    """
    # Set default app name
    if not app_name:
        app_name = "sports_bot"
    
    # Create logger
    logger = logging.getLogger(app_name)
    
    # Set level
    level = getattr(logging, log_level.upper())
    logger.setLevel(level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger

def log_exception(logger: logging.Logger, exc: Exception, context: dict = None):
    """
    Log an exception with additional context.
    
    Args:
        logger: Logger instance
        exc: Exception to log
        context: Additional context dictionary
    """
    error_details = {
        'exception_type': exc.__class__.__name__,
        'exception_message': str(exc),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if context:
        error_details.update(context)
    
    logger.error(
        f"Exception occurred: {exc.__class__.__name__}",
        extra={'error_details': error_details},
        exc_info=True
    )

# Example usage:
# logger = setup_logging(
#     log_level="DEBUG",
#     log_dir="/path/to/logs",
#     app_name="sports_bot"
# ) 