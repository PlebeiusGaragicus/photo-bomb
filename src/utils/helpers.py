"""
Utils module for Photo Boss application.

Contains utility functions and helpers used throughout the application.
"""

from pathlib import Path


def get_user_config_dir() -> Path:
    """Get the user's configuration directory."""
    return Path.home() / "Library" / "Preferences" / "photo-boss"


def ensure_config_dir():
    """Ensure the config directory exists."""
    config_dir = get_user_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
