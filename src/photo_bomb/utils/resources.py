"""
Resource (asset) lookup for Photo Bomb.

Uses ``importlib.resources`` so the same code path works in three modes:

1. Editable install / running ``python -m photo_bomb`` from the repo
2. ``pip install``-ed wheel
3. PyInstaller-frozen ``.app`` bundle (PyInstaller's hooks treat
   ``importlib.resources`` correctly, so we no longer need to special-case
   ``sys._MEIPASS``)

All assets are stored as a sub-package at ``photo_bomb/assets/``; subdirectories
(e.g. ``icons``) are referenced via dotted package paths.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

ASSETS_PACKAGE = "photo_bomb.assets"


def _resolve(package: str, name: str):
    """Return an ``importlib.resources`` Traversable for ``name`` in ``package``."""
    return resources.files(package).joinpath(name)


def get_resource_path(relative_path: str) -> Path:
    """
    Return an absolute filesystem ``Path`` to a bundled asset.

    ``relative_path`` is interpreted relative to ``photo_bomb/assets/``. Forward
    slashes are accepted and translated to package traversal, e.g.
    ``"icons/icon.icns"`` resolves to ``photo_bomb/assets/icons/icon.icns``.
    """
    parts = [p for p in relative_path.replace("\\", "/").split("/") if p]
    if not parts:
        raise ValueError("relative_path must not be empty")

    # Walk subdirectories as sub-packages so importlib.resources can find them
    # whether they're loose files in dev or zipped inside a frozen bundle.
    package = ASSETS_PACKAGE
    name = parts[-1]
    for sub in parts[:-1]:
        package = f"{package}.{sub}"

    traversable = _resolve(package, name)
    # ``Path(str(...))`` is safe for both real files and PyInstaller's
    # extracted-to-tempdir layout; importlib.resources guarantees the
    # underlying path exists for filesystem-backed loaders.
    return Path(str(traversable))


def asset_exists(relative_path: str) -> bool:
    """Return True if the named asset exists in the bundle."""
    try:
        return get_resource_path(relative_path).exists()
    except (FileNotFoundError, ModuleNotFoundError, ValueError):
        return False


def get_icon_path() -> Path:
    """Return the path to the application icon (.icns preferred, .png fallback)."""
    for candidate in ("icons/icon.icns", "icons/icon.png"):
        if asset_exists(candidate):
            return get_resource_path(candidate)
    raise FileNotFoundError(
        "Application icon not found under photo_bomb/assets/icons/. "
        "Run packaging/make_icon.sh to generate it."
    )
