"""
Logging system for TermSage.

This module provides a centralized, thread-safe logging system.
"""

import os
import sys
import logging
import threading
from typing import Optional, Dict, Any

# Global lock for logger initialization
_logger_lock = threading.RLock()
_logger_initialized = False
_logger: Optional[logging.Logger] = None


def setup_logger(
    config_dir: str,
    level: str = "INFO",
    file_enabled: bool = True,
    console_enabled: bool = True,
) -> logging.Logger:
    """
    Set up and configure the TermSage logger.

    Args:
        config_dir: Directory to store log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        file_enabled: Whether to log to a file
        console_enabled: Whether to log to the console

    Returns:
        Configured logger instance
    """
    global _logger, _logger_initialized
    
    with _logger_lock:
        if _logger_initialized and _logger is not None:
            return _logger
            
        # Create logger
        logger = logging.getLogger("termsage")
        logger.setLevel(getattr(logging, level.upper()))
        logger.propagate = False  # Don't propagate to parent loggers
        
        # Clear any existing handlers
        if logger.handlers:
            logger.handlers.clear()
            
        # Create formatters
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        # Add console handler if enabled
        if console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
        # Add file handler if enabled
        if file_enabled:
            log_dir = os.path.join(config_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, "termsage.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        _logger = logger
        _logger_initialized = True
        return logger


def get_logger() -> logging.Logger:
    """
    Get the TermSage logger instance.
    
    Returns:
        Logger instance (or a default logger if not initialized)
    """
    global _logger
    
    with _logger_lock:
        if _logger is None:
            # Return a default logger that only logs to console
            default_logger = logging.getLogger("termsage_default")
            
            if not default_logger.handlers:
                default_logger.setLevel(logging.INFO)
                handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
                default_logger.addHandler(handler)
                
            return default_logger
            
        return _logger


def update_logger_config(config: Dict[str, Any]) -> None:
    """
    Update logger configuration based on settings.
    
    Args:
        config: Configuration dictionary containing logging settings
    """
    global _logger
    
    with _logger_lock:
        if _logger is None:
            return
            
        # Update log level
        if "level" in config:
            level = config.get("level", "INFO")
            _logger.setLevel(getattr(logging, level.upper()))
            
        # Update handlers
        for handler in _logger.handlers:
            if isinstance(handler, logging.FileHandler) and "file_enabled" in config:
                if not config.get("file_enabled", True):
                    _logger.removeHandler(handler)
                    
            if isinstance(handler, logging.StreamHandler) and "console_enabled" in config:
                if not config.get("console_enabled", True):
                    _logger.removeHandler(handler) 