"""Tests for configuration management."""
import os
import tempfile
import pytest
from pathlib import Path
from config import Config, get_config, _resolve_path, PROJECT_ROOT


class TestConfig:
    """Test configuration loading and environment variable overrides."""
    
    def test_load_config_from_file(self):
        """Test loading configuration from YAML file."""
        config = Config()
        assert config.ors_base_url is not None
        assert config.input_file is not None
        # range_seconds can now be a list or int (backward compatibility)
        range_sec = config.range_seconds
        assert isinstance(range_sec, (list, int))
        if isinstance(range_sec, list):
            assert len(range_sec) > 0
    
    def test_env_override_string(self, monkeypatch):
        """Test environment variable override for string values."""
        monkeypatch.setenv('ORS_BASE_URL', 'http://test-server:8080/ors')
        # Need to reload config
        from config import _config_instance
        import config
        config._config_instance = None
        config_obj = get_config()
        assert config_obj.ors_base_url == 'http://test-server:8080/ors'
    
    def test_env_override_int(self, monkeypatch):
        """Test environment variable override for integer values."""
        monkeypatch.setenv('ORS_TIMEOUT', '60')
        from config import _config_instance
        import config
        config._config_instance = None
        config_obj = get_config()
        assert config_obj.ors_timeout == 60
    
    def test_env_override_list(self, monkeypatch):
        """Test environment variable override for list values."""
        monkeypatch.setenv('ANALYSIS_TARGET_LEVELS', '1,2,3')
        from config import _config_instance
        import config
        config._config_instance = None
        config_obj = get_config()
        assert config_obj.target_levels == ['1', '2', '3']
    
    def test_resolve_relative_path(self):
        """Test resolving relative paths to project root."""
        path = _resolve_path('test_file.xlsx')
        assert path.is_absolute()
        assert path.parent == PROJECT_ROOT
    
    def test_resolve_absolute_path(self):
        """Test that absolute paths are preserved."""
        # On Windows, paths starting with / are converted to C:/, so use a proper absolute path
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            abs_path = Path(f.name)
        
        resolved = _resolve_path(str(abs_path))
        assert resolved == abs_path
        # Clean up
        abs_path.unlink()
    
    def test_config_properties(self):
        """Test all configuration properties return expected types."""
        config = Config()
        
        # String properties
        assert isinstance(config.ors_base_url, str)
        assert isinstance(config.input_file, str)
        assert isinstance(config.output_csv, str)
        assert isinstance(config.output_map, str)
        
        # Integer properties (range_seconds can be list or int)
        assert isinstance(config.range_seconds, (list, int))
        assert isinstance(config.ors_timeout, int)
        assert isinstance(config.ors_retry_attempts, int)
        
        # Float properties
        assert isinstance(config.sleep_between_requests, float)
        # ors_retry_delay can be int or float depending on config
        assert isinstance(config.ors_retry_delay, (int, float))
        
        # List properties
        assert isinstance(config.target_levels, list)
        assert len(config.target_levels) > 0
        
        # Test isochrone colors property
        assert isinstance(config.map_isochrone_colors, dict)
        assert len(config.map_isochrone_colors) > 0
    
    def test_config_with_custom_path(self):
        """Test loading config from custom path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
ors:
  base_url: "http://custom:8080/ors"
analysis:
  range_seconds: 7200
""")
            temp_path = Path(f.name)
        
        try:
            config = Config(config_path=temp_path)
            assert config.ors_base_url == "http://custom:8080/ors"
            # Single int value should be converted to list for backward compatibility
            range_sec = config.range_seconds
            assert isinstance(range_sec, list)
            assert range_sec == [7200]
        finally:
            temp_path.unlink()
    
    def test_config_missing_file(self):
        """Test that missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Config(config_path=Path('/nonexistent/config.yaml'))
    
    def test_get_method_with_dot_notation(self):
        """Test get() method with dot notation."""
        config = Config()
        value = config.get('ors.base_url')
        assert value is not None
        assert isinstance(value, str)
    
    def test_get_method_with_default(self):
        """Test get() method returns default for missing keys."""
        config = Config()
        value = config.get('nonexistent.key', 'default_value')
        assert value == 'default_value'
    
    def test_log_file_directory_creation(self):
        """Test that log file directory is created."""
        config = Config()
        log_file_path = Path(config.log_file)
        assert log_file_path.parent.exists()

