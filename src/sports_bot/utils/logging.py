"""
Logging configuration module.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
APP_LOG = LOGS_DIR / "app.log"
API_LOG = LOGS_DIR / "api.log"
DB_LOG = LOGS_DIR / "database.log"
UPDATE_LOG = LOGS_DIR / "updates.log"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the specified name and configuration.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional specific log file path
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if no handlers exist
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Determine log file based on module
        if not log_file:
            if "api" in name:
                log_file = API_LOG
            elif "database" in name:
                log_file = DB_LOG
            elif "update" in name:
                log_file = UPDATE_LOG
            else:
                log_file = APP_LOG
        
        # File handler (10MB max, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(console_handler)
        
        # Don't propagate to root logger
        logger.propagate = False
    
    return logger

def setup_logging():
    """Set up basic logging configuration."""
    # Create log files if they don't exist
    for log_file in [APP_LOG, API_LOG, DB_LOG, UPDATE_LOG]:
        if not log_file.exists():
            log_file.touch()
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            RotatingFileHandler(
                APP_LOG,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )

def get_api_logger() -> logging.Logger:
    """Get logger for API operations."""
    return get_logger("sports_bot.api", API_LOG)

def get_db_logger() -> logging.Logger:
    """Get logger for database operations."""
    return get_logger("sports_bot.database", DB_LOG)

def get_update_logger() -> logging.Logger:
    """Get logger for update operations."""
    return get_logger("sports_bot.update", UPDATE_LOG) 