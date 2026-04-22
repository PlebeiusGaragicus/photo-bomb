"""
Misc helper utilities.

Resource lookup lives in :mod:`photo_boss.utils.resources`; this module is
limited to user-data paths and other small utilities.
"""

from __future__ import annotations

from pathlib import Path

CONFIG_DIR_NAME = "photo-boss"


def get_user_config_dir() -> Path:
    """Return the user's per-app preferences directory on macOS."""
    return Path.home() / "Library" / "Preferences" / CONFIG_DIR_NAME


def ensure_config_dir() -> Path:
    """Create and return the user's preferences directory."""
    config_dir = get_user_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir
