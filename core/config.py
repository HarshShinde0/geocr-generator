"""
Configuration management for GeoCroissant Generator.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml


class Config:
    """Configuration handler for GeoCroissant generation."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration.
        
        Args:
            config_dict: Optional configuration dictionary
        """
        self.config = config_dict or self._default_config()
    
    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "dataset": {
                "version": "1.0",
                "license": "Unknown",
                "conformsTo": [
                    "http://mlcommons.org/croissant/1.1",
                    "http://mlcommons.org/croissant/geo/1.0"
                ]
            },
            "extraction": {
                "compute_statistics": True,
                "extract_spectral_metadata": True,
                "detect_sensor": True
            },
            "output": {
                "save_metadata_cache": True,
                "indent": 2
            }
        }
    
    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration YAML file
            
        Returns:
            Config instance
        """
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls(config_dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
