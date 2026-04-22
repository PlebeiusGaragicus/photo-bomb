# Photo Boss - Docs Index

PyQt6 + PyObjC app for macOS (arm64). Distributed as ad-hoc-signed `.app`
inside a `.dmg` from GitHub Releases. **Status: proof-of-concept** - the
packaging, UI shell, and config layer are real; Photos integration and
analysis are stubs (see [features.md](features.md)).

User-facing install / build / release flows live in the top-level
[README](../README.md). These docs are for code-level work in this repo.

## Repo map

| Path | Contents |
|------|----------|
| `src/photo_boss/main.py` | `QApplication` bootstrap, `--version` flag, top-level exception trap |
| `src/photo_boss/__main__.py` | Enables `python -m photo_boss` |
| `src/photo_boss/ui/` | `QMainWindow`, dialogs, widgets - all `PyQt6` |
| `src/photo_boss/core/` | Config, Photos wrapper, API client, dead-code engines |
| `src/photo_boss/utils/resources.py` | `importlib.resources` lookup for bundled assets |
| `src/photo_boss/utils/helpers.py` | `~/Library/Preferences/photo-boss/` path helpers |
| `src/photo_boss/assets/` | Sub-package; ships icons via `package-data` glob |
| `packaging/photo_boss.spec` | PyInstaller spec; sets `Info.plist`, ad-hoc signs |
| `packaging/entitlements.plist` | Hardened-runtime entitlements for ad-hoc sign |
| `packaging/make_icon.sh` | `icon.svg` -> `icon.icns` (idempotent) |
| `scripts/build_macos.sh` | Full local build: venv, deps, icon, PyInstaller, sign, smoke, DMG |
| `.github/workflows/release.yml` | `v*` tag -> `macos-14` build -> GitHub Release |

## Cross-cutting invariants

- **Imports are absolute** under `photo_boss.*`. No `from .x` relative
  imports anywhere; PyInstaller's frozen importer used to choke on the
  try/except hybrids that previously existed here. Keep them absolute.
- **Singletons** (mutable global state) live behind factory functions:
  `core.config.get_config()` and `core.photos_library.get_photos_library()`.
  Construct directly only in tests.
- **Assets** are looked up via `utils.resources.get_resource_path("...")`,
  never via `__file__` arithmetic and never via `sys._MEIPASS`. The helper
  uses `importlib.resources.files()` which works identically in dev,
  installed, and frozen modes.
- **macOS-only code paths** must be guarded:
  `os.uname().sysname == "Darwin"` (see `core.photos_library.is_available`).
  PyObjC is a conditional dep (`platform_system=='Darwin'` in
  `pyproject.toml`).
- **Qt version is PyQt6**: `QAction` lives in `QtGui`, not `QtWidgets`.
  Don't add `PyQt5`/`PySide*` - they're in PyInstaller's `excludes`.

## Common commands

```bash
# Run from source (after pip install -e .)
python -m photo_boss
photo-boss --version

# Build the .app + .dmg locally (Apple Silicon only)
./scripts/build_macos.sh
SKIP_DMG=1 ./scripts/build_macos.sh        # .app only
SKIP_VENV=1 ./scripts/build_macos.sh       # reuse current Python

# Regenerate icon.icns from icon.svg
./packaging/make_icon.sh

# Cut a release
git tag v0.2.0 && git push --tags          # workflow does the rest
```

## Where to look first

| Question | File |
|----------|------|
| How does the app start? | `src/photo_boss/main.py` |
| Where is config persisted? | `core/config.py` (singleton via `get_config()`) |
| What does the API client actually send? | `core/api_client.py::analyze_photo` |
| Why doesn't analysis work end-to-end? | `core/analysis_engine.py::_get_photo_data` (returns `None`) |
| Why are albums always "All Photos / Favorites / Recent / Selfies"? | `core/photos_library.py::get_albums` (hardcoded sample data) |
| How do bundled assets get found inside the .app? | `utils/resources.py` |
| Why doesn't Gatekeeper block development builds? | `xattr -cr` step in `scripts/build_macos.sh` |
