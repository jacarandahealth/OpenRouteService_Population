"""
Logging configuration module.
Sets up structured logging with console and file handlers.
"""
import logging
import sys
from pathlib import Path
from config import get_config


def setup_logger(name: str = None) -> logging.Logger:
    """
    Set up and return a logger with console and file handlers.
    
    Args:
        name: Logger name (typically __name__). If None, uses root logger.
    
    Returns:
        Configured logger instance.
    """
    config = get_config()
    
    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    formatter = logging.Formatter(
        fmt=config.log_format,
        datefmt=config.log_date_format
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.log_console_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_file_path = Path(config.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(getattr(logging, config.log_file_level.upper(), logging.DEBUG))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance. Convenience function that calls setup_logger.
    
    Args:
        name: Logger name (typically __name__).
    
    Returns:
        Configured logger instance.
    """
    return setup_logger(name)

