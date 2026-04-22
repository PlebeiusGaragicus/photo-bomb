# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Photo Bomb (macOS arm64, ad-hoc signed).

Run via:
    pyinstaller --noconfirm --clean packaging/photo_bomb.spec

Or, more typically, via the wrapper script:
    ./scripts/build_macos.sh
"""

from pathlib import Path
import sys

# `SPECPATH` is provided by PyInstaller at spec-evaluation time.
SPEC_DIR = Path(SPECPATH).resolve()  # noqa: F821  (provided by PyInstaller)
REPO_ROOT = SPEC_DIR.parent
SRC_DIR = REPO_ROOT / "src"
ASSETS_DIR = SRC_DIR / "photo_bomb" / "assets"
ICON_PATH = ASSETS_DIR / "icons" / "icon.icns"
ENTITLEMENTS = SPEC_DIR / "entitlements.plist"

# Pull __version__ without importing PyQt6 (which the build host does have, but
# this keeps the spec hermetic).
_init = (SRC_DIR / "photo_bomb" / "__init__.py").read_text()
APP_VERSION = next(
    line.split("=", 1)[1].strip().strip('"').strip("'")
    for line in _init.splitlines()
    if line.startswith("__version__")
)

APP_NAME = "Photo Bomb"
BUNDLE_ID = "com.photobomb.app"

# Make `import photo_bomb` resolvable while PyInstaller analyses imports.
sys.path.insert(0, str(SRC_DIR))


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    [str(SRC_DIR / "photo_bomb" / "main.py")],
    pathex=[str(SRC_DIR)],
    binaries=[],
    # Bundle the entire assets/ tree as a sub-package on disk so
    # importlib.resources finds it inside the .app.
    datas=[(str(ASSETS_DIR), "photo_bomb/assets")],
    hiddenimports=[
        "PyQt6.sip",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "test",
        "unittest",
        "pydoc",
        "PyQt5",
        "PySide2",
        "PySide6",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

# ---------------------------------------------------------------------------
# Executable
# ---------------------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
    # Ad-hoc sign every Mach-O PyInstaller emits. Required for the bundle to
    # launch on Apple Silicon at all, and gives the app a stable signing
    # identity that macOS TCC keys Photos permission to.
    codesign_identity="-",
    entitlements_file=str(ENTITLEMENTS) if ENTITLEMENTS.exists() else None,
    icon=str(ICON_PATH) if ICON_PATH.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

# ---------------------------------------------------------------------------
# .app bundle
# ---------------------------------------------------------------------------
app = BUNDLE(
    coll,
    name=f"{APP_NAME}.app",
    icon=str(ICON_PATH) if ICON_PATH.exists() else None,
    bundle_identifier=BUNDLE_ID,
    version=APP_VERSION,
    info_plist={
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundlePackageType": "APPL",
        "LSMinimumSystemVersion": "12.0",
        "LSApplicationCategoryType": "public.app-category.photography",
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": False,
        # *** Mandatory privacy-usage strings ***
        # The Photos framework will refuse to return data and the OS will kill
        # the app on first authorization request if these keys are missing.
        "NSPhotoLibraryUsageDescription":
            "Photo Bomb reads your Photos library to analyze and organize "
            "photos using your configured vision model.",
        "NSPhotoLibraryAddUsageDescription":
            "Photo Bomb creates and modifies albums in your Photos library "
            "to organize categorized photos.",
    },
)
