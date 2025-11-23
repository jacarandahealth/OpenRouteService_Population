"""
Configuration management module.
Loads configuration from config.yaml with environment variable overrides.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()


def _load_yaml_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = PROJECT_ROOT / "config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config or {}


def _get_env_override(key_path: str, default: Any = None) -> Optional[str]:
    """
    Get environment variable override.
    Converts nested keys like 'ors.base_url' to 'ORS_BASE_URL'.
    """
    env_key = key_path.upper().replace('.', '_')
    return os.getenv(env_key, default)


def _resolve_path(path_str: str) -> Path:
    """
    Resolve file path - supports both relative (to project root) and absolute paths.
    """
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _apply_env_overrides(config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """
    Recursively apply environment variable overrides to configuration.
    Environment variables should be uppercase with underscores (e.g., ORS_BASE_URL).
    """
    result = {}
    
    for key, value in config.items():
        full_key = f"{prefix}_{key}" if prefix else key
        env_key = full_key.upper().replace('.', '_')
        
        if isinstance(value, dict):
            result[key] = _apply_env_overrides(value, full_key)
        else:
            # Check for environment variable override
            env_value = os.getenv(env_key)
            if env_value is not None:
                # Try to convert to appropriate type
                if isinstance(value, bool):
                    result[key] = env_value.lower() in ('true', '1', 'yes')
                elif isinstance(value, int):
                    try:
                        result[key] = int(env_value)
                    except ValueError:
                        result[key] = value
                elif isinstance(value, float):
                    try:
                        result[key] = float(env_value)
                    except ValueError:
                        result[key] = value
                elif isinstance(value, list):
                    # For lists, split by comma
                    result[key] = [item.strip() for item in env_value.split(',')]
                else:
                    result[key] = env_value
            else:
                result[key] = value
    
    return result


class Config:
    """Configuration class that loads from YAML and environment variables."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration from file and environment variables."""
        self._config = _load_yaml_config(config_path)
        self._config = _apply_env_overrides(self._config)
        self._resolve_paths()
    
    def _resolve_paths(self):
        """Resolve all file paths in the configuration."""
        if 'files' in self._config:
            for key in ['input_file', 'output_csv', 'output_map']:
                if key in self._config['files']:
                    self._config['files'][key] = str(_resolve_path(self._config['files'][key]))
        
        if 'logging' in self._config and 'file' in self._config['logging']:
            log_file = _resolve_path(self._config['logging']['file'])
            # Create logs directory if it doesn't exist
            log_file.parent.mkdir(parents=True, exist_ok=True)
            self._config['logging']['file'] = str(log_file)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation (e.g., 'ors.base_url').
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    @property
    def ors_base_url(self) -> str:
        """Get ORS base URL."""
        return self.get('ors.base_url', 'http://localhost:8080/ors')
    
    @property
    def ors_health_url(self) -> str:
        """Get ORS health check URL."""
        return self.get('ors.health_url', f"{self.ors_base_url}/v2/health")
    
    @property
    def ors_api_key(self) -> str:
        """Get ORS API key."""
        return self.get('ors.api_key', 'dummy_key')
    
    @property
    def ors_timeout(self) -> int:
        """Get ORS request timeout in seconds."""
        return self.get('ors.timeout', 30)
    
    @property
    def ors_retry_attempts(self) -> int:
        """Get number of retry attempts for ORS requests."""
        return self.get('ors.retry_attempts', 3)
    
    @property
    def ors_retry_delay(self) -> float:
        """Get initial retry delay in seconds."""
        return self.get('ors.retry_delay', 1.0)
    
    @property
    def input_file(self) -> str:
        """Get input Excel file path."""
        return self.get('files.input_file', 'KMHFR_MNCH_Facilities_Only.xlsx')
    
    @property
    def output_csv(self) -> str:
        """Get output CSV file path."""
        return self.get('files.output_csv', 'population_analysis_results.csv')
    
    @property
    def output_map(self) -> str:
        """Get output map HTML file path."""
        return self.get('files.output_map', 'isochrone_map.html')
    
    @property
    def range_seconds(self):
        """Get isochrone range(s) in seconds. Returns list if multiple ranges, int if single."""
        value = self.get('analysis.range_seconds', [900, 1800, 2700])
        # Handle backward compatibility - if single value, convert to list
        if isinstance(value, int):
            return [value]
        return value
    
    @property
    def target_levels(self) -> list:
        """Get target facility levels."""
        return self.get('analysis.target_levels', ['4', '5', '6'])
    
    @property
    def sleep_between_requests(self) -> float:
        """Get sleep time between requests in seconds."""
        return self.get('analysis.sleep_between_requests', 0.5)
    
    @property
    def gee_dataset(self) -> str:
        """Get GEE dataset name."""
        return self.get('gee.dataset', 'WorldPop/GP/100m/pop')
    
    @property
    def gee_scale(self) -> int:
        """Get GEE scale in meters."""
        return self.get('gee.scale', 100)
    
    @property
    def gee_max_pixels(self) -> int:
        """Get GEE max pixels."""
        return self.get('gee.max_pixels', 1000000000)
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.get('logging.level', 'INFO')
    
    @property
    def log_file(self) -> str:
        """Get log file path."""
        return self.get('logging.file', 'logs/analysis.log')
    
    @property
    def log_console_level(self) -> str:
        """Get console logging level."""
        return self.get('logging.console_level', 'INFO')
    
    @property
    def log_file_level(self) -> str:
        """Get file logging level."""
        return self.get('logging.file_level', 'DEBUG')
    
    @property
    def log_format(self) -> str:
        """Get log format string."""
        return self.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @property
    def log_date_format(self) -> str:
        """Get log date format string."""
        return self.get('logging.date_format', '%Y-%m-%d %H:%M:%S')
    
    @property
    def map_center_lat(self) -> float:
        """Get map center latitude."""
        return self.get('map.center_lat', 0.0236)
    
    @property
    def map_center_lon(self) -> float:
        """Get map center longitude."""
        return self.get('map.center_lon', 37.9062)
    
    @property
    def map_zoom_start(self) -> int:
        """Get map initial zoom level."""
        return self.get('map.zoom_start', 6)
    
    @property
    def map_isochrone_color(self) -> str:
        """Get default isochrone color for map (used if isochrone_colors not specified)."""
        return self.get('map.isochrone_color', 'blue')
    
    @property
    def map_isochrone_colors(self) -> dict:
        """Get color mapping for different time ranges (in minutes)."""
        colors = self.get('map.isochrone_colors', {})
        if not colors:
            # Default colors if not specified
            colors = {
                15: '#ff0000',  # Red
                30: '#ff8800',  # Orange
                45: '#ffaa00'   # Yellow/Amber
            }
        # Convert string keys to int if needed
        return {int(k) if isinstance(k, str) and k.isdigit() else k: v for k, v in colors.items()}
    
    @property
    def map_isochrone_opacity(self) -> float:
        """Get isochrone opacity for map."""
        return self.get('map.isochrone_opacity', 0.3)


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config(config_path: Optional[Path] = None) -> Config:
    """Get or create global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance

