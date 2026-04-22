# Photo Bomb - Docs Index

PyQt6 + PyObjC app for macOS (arm64). Distributed as ad-hoc-signed `.app`
inside a `.dmg` from GitHub Releases. **Status:** Phase 1 working slice -
real `Photos.framework` integration, real thumbnails, manual
"categorize" moves the asset into a Photos album. AI analysis is
deferred to Phase 2 (see [features.md](features.md)).

User-facing install / build / release flows live in the top-level
[README](../README.md). These docs are for code-level work in this repo.

## Repo map

| Path | Contents |
|------|----------|
| `src/photo_bomb/main.py` | `QApplication` bootstrap, `--version` flag, top-level exception trap |
| `src/photo_bomb/__main__.py` | Enables `python -m photo_bomb` |
| `src/photo_bomb/ui/` | `QMainWindow`, dialogs, widgets - all `PyQt6` |
| `src/photo_bomb/core/` | Config, Photos wrapper, API client |
| `src/photo_bomb/utils/resources.py` | `importlib.resources` lookup for bundled assets |
| `src/photo_bomb/utils/helpers.py` | `~/Library/Preferences/photo-bomb/` path helpers |
| `src/photo_bomb/assets/` | Sub-package; ships icons via `package-data` glob |
| `packaging/photo_bomb.spec` | PyInstaller spec; sets `Info.plist`, ad-hoc signs |
| `packaging/entitlements.plist` | Hardened-runtime entitlements for ad-hoc sign |
| `packaging/make_icon.sh` | `icon.svg` -> `icon.icns` (idempotent) |
| `scripts/build_macos.sh` | Full local build: venv, deps, icon, PyInstaller, sign, smoke, DMG |
| `.github/workflows/release.yml` | `v*` tag -> `macos-14` build -> GitHub Release |

## Cross-cutting invariants

- **Imports are absolute** under `photo_bomb.*`. No `from .x` relative
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
python -m photo_bomb
photo-bomb --version

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
| How does the app start? | `src/photo_bomb/main.py` |
| Where is config persisted? | `core/config.py` (singleton via `get_config()`) |
| What does the API client actually send? | `core/api_client.py::analyze_photo` |
| Why doesn't AI analysis work end-to-end? | Phase 2 work; `analyze_photo` has a latin1 bug. See [features.md](features.md) "Phase 2" |
| How does "categorize" actually work? | `ui/main_window.py::_on_categorize_clicked` -> `core/photos_library.py::find_or_create_album` + `add_photos_to_album`. See [categorization.md](categorization.md) |
| How do bundled assets get found inside the .app? | `utils/resources.py` |
| Why doesn't Gatekeeper block development builds? | `xattr -cr` step in `scripts/build_macos.sh` |
