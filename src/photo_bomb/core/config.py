"""
Configuration management for Photo Bomb.
Handles storing and loading user settings including API endpoints and credentials.
"""

import json
import os
import sys
from pathlib import Path


class Config:
    """Manages application configuration using JSON file in user's Library/Preferences."""
    
    def __init__(self):
        # Detect if running as bundled app
        self._is_bundled = getattr(sys, 'frozen', False)
        
        # Use macOS-style preferences directory (same path for both dev and bundled)
        self.config_dir = Path.home() / "Library" / "Preferences" / "photo-bomb"
        self.config_file = self.config_dir / "config.json"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration values
        self.defaults = {
            "api_endpoint": "",
            "api_key": "",
            "model_name": "",
            "categories": ["memories", "todo", "research"],
            "batch_size": 100,
            "last_library_path": ""
        }
        
        # Load existing config or use defaults
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from file, return defaults if not found."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure new keys exist
                    config = {**self.defaults, **loaded}
                    return config
            except (json.JSONDecodeError, IOError):
                return self.defaults.copy()
        return self.defaults.copy()
    
    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Set a configuration value and save."""
        self.config[key] = value
        self._save_config()
    
    def update(self, updates: dict):
        """Update multiple configuration values at once."""
        self.config.update(updates)
        self._save_config()
    
    def _save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")
    
    @property
    def api_endpoint(self) -> str:
        return self.get("api_endpoint", "")
    
    @api_endpoint.setter
    def api_endpoint(self, value: str):
        self.set("api_endpoint", value)
    
    @property
    def api_key(self) -> str:
        return self.get("api_key", "")
    
    @api_key.setter
    def api_key(self, value: str):
        self.set("api_key", value)
    
    @property
    def model_name(self) -> str:
        return self.get("model_name", "")
    
    @model_name.setter
    def model_name(self, value: str):
        self.set("model_name", value)
    
    @property
    def categories(self) -> list:
        return self.get("categories", ["memories", "todo", "research"])
    
    @categories.setter
    def categories(self, value: list):
        self.set("categories", value)


# Global config instance
_config_instance = None


def get_config() -> Config:
    """Get or create the global config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
