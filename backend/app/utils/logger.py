"""
Logging configuration for JobAlign AI Backend
"""

import logging
import sys
import os
import io
from datetime import datetime
from typing import Optional

def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Get a configured logger instance"""
    
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with UTF-8 encoding (Windows-safe)
    stream = sys.stdout
    try:
        # Wrap stdout to force UTF-8 and avoid cp1252 encode errors on Windows
        if hasattr(sys.stdout, "buffer"):
            stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        stream = sys.stdout
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler (optional)
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.FileHandler(
        f'logs/jobalign_{datetime.now().strftime("%Y%m%d")}.log', encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def log_user_activity(
    logger: logging.Logger,
    user_id: Optional[int],
    action: str,
    details: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Log user activity for audit trail"""
    log_data = {
        "user_id": user_id,
        "action": action,
        "details": details,
        "metadata": metadata,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"User Activity: {log_data}")

def log_api_call(
    logger: logging.Logger,
    endpoint: str,
    method: str,
    user_id: Optional[int],
    status_code: int,
    response_time: float,
    error: Optional[str] = None
):
    """Log API call details"""
    log_data = {
        "endpoint": endpoint,
        "method": method,
        "user_id": user_id,
        "status_code": status_code,
        "response_time_ms": round(response_time * 1000, 2),
        "error": error,
        "timestamp": datetime.now().isoformat()
    }
    
    if status_code >= 400:
        logger.warning(f"API Call Error: {log_data}")
    else:
        logger.info(f"API Call: {log_data}")
