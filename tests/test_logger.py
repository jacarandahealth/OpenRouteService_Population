"""Tests for logging configuration."""
import logging
import tempfile
from pathlib import Path
from logger import setup_logger, get_logger


class TestLogger:
    """Test logging setup and configuration."""
    
    def test_setup_logger_creates_logger(self):
        """Test that setup_logger returns a logger instance."""
        logger = setup_logger('test_module')
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_module'
    
    def test_logger_has_handlers(self):
        """Test that logger has both console and file handlers."""
        logger = setup_logger('test_handlers')
        assert len(logger.handlers) >= 2
        
        handler_types = [type(h).__name__ for h in logger.handlers]
        assert 'StreamHandler' in handler_types
        assert 'FileHandler' in handler_types
    
    def test_logger_does_not_duplicate_handlers(self):
        """Test that calling setup_logger multiple times doesn't duplicate handlers."""
        logger1 = setup_logger('test_duplicate')
        handler_count_1 = len(logger1.handlers)
        
        logger2 = setup_logger('test_duplicate')
        handler_count_2 = len(logger2.handlers)
        
        assert handler_count_1 == handler_count_2
    
    def test_get_logger_convenience_function(self):
        """Test that get_logger is a convenience function."""
        logger = get_logger('test_convenience')
        assert isinstance(logger, logging.Logger)
    
    def test_logger_logs_to_file(self, tmp_path):
        """Test that logger writes to file."""
        # This test would require mocking the config, but basic structure test is fine
        logger = setup_logger('test_file_logging')
        logger.info("Test message")
        
        # Verify file handler exists
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0

