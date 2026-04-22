# Architecture

Module contracts and cross-module conventions. Status of each subsystem
(real / partial / stub) lives in [features.md](features.md); this doc
describes intended boundaries and what's actually wired up.

## Layering

```
ui/  -->  core/  -->  utils/
```

UI may import from `core` and `utils`. `core` may import from `utils`.
Nothing imports from `ui`. No back-edges. There is currently no enforcement
beyond convention.

## Module contracts

### `core/config.py`

- **Singleton.** Always access via `get_config() -> Config`. Never call
  `Config()` outside tests.
- Persists to `~/Library/Preferences/photo-boss/config.json` immediately
  on every `set()` / `update()`. No batching, no atomic write.
- Schema is the `Config.defaults` dict. Loaded keys are merged on top of
  defaults so adding new keys is forward-compatible.
- API key is stored **plaintext**. macOS Keychain is not used.

### `core/photos_library.py`

- **Singleton** via `get_photos_library() -> PhotosLibrary`.
- `is_available` checks `os.uname().sysname == "Darwin"`. There is no
  PyObjC import yet; the entire module is platform-agnostic placeholder.
- All `get_*` and mutation methods return hardcoded sample data and emit
  the corresponding signal. See [photo-access.md](photo-access.md) for
  the real PyObjC port surface.
- Subclasses `QObject` for signal support: `photos_loaded(list)`,
  `albums_loaded(list)`, `error_occurred(str)`.

### `core/api_client.py`

- **Not a singleton.** `MainWindow` and `APISettingsDialog` each construct
  their own `VisionAPIClient()`. Configure with `.configure(endpoint, key,
  model)` after construction.
- `endpoint_url` is the **base URL** (e.g. `https://api.openai.com/v1`).
  The client appends `/models` for the health check and `/chat/completions`
  for analysis. Storing the full chat-completions URL in config will
  produce 404s.
- See [api-settings.md](api-settings.md) for the exact request body and
  the latin1-encoding bug in `analyze_photo`.

### `core/analysis_engine.py`, `core/categorization.py`, `core/album_system.py`

- **Dead code.** These classes are well-formed but **never instantiated
  anywhere in `ui/`**. The UI does its own ad-hoc categorization and
  triggers the batch dialog with hardcoded photo IDs.
- If you wire them up, note that none of them is a singleton; pick a
  layer (probably `MainWindow.__init__`) to own the instances and pass
  them into widgets.
- `analysis_engine._get_photo_data` is unconditionally `return None`, so
  even if wired, no analysis would run.

### `ui/main_window.py`

- Hub for everything. Constructs widgets, owns the splitter, instantiates
  dialogs lazily.
- All callbacks are sync; long-running work must move to a `QThread`
  (`batch_analysis_dialog.AnalysisWorker` is the only example).
- Status bar created via `_create_status_bar`; do not call `statusBar()`
  before `__init__` finishes or you'll get an empty default one.

### `ui/photo_grid.py`

- Pagination is **prev/next buttons**, not infinite scroll (older docs
  claimed otherwise). `batch_size` defaults to 100, controlled by
  `batch_requested(offset, limit)` signal.
- `add_photo_item` has a row-position bug (`row // 4` always 0 because
  `row` is always 0). Fix before this widget shows real data.

### `utils/resources.py`

- Single entry point for bundled-asset paths. Uses
  `importlib.resources.files("photo_boss.assets")` and walks
  forward-slash-separated subpaths as sub-package names.
- Works in dev, installed wheel, and PyInstaller bundle without branching.
  **Do not** reintroduce a `sys._MEIPASS` check.
- Subdirectories of `assets/` must be Python sub-packages (have an
  `__init__.py`) for `importlib.resources` to traverse them. `assets/` and
  `assets/icons/` are already configured this way.

## Qt signal flow

Real signals currently emitted somewhere AND connected somewhere:

| Emitter | Signal | Receiver |
|---------|--------|----------|
| `PhotoGridWidget` | `batch_requested(int, int)` | `MainWindow._load_photo_batch` |
| `PhotoGridWidget` | `photo_selected(str)` | `MainWindow._on_photo_selected` |
| `AnalysisWorker` (QThread) | `progress(int)` | `BatchAnalysisDialog._on_progress` |
| `AnalysisWorker` | `complete(list)` | `BatchAnalysisDialog._on_complete` |

Defined but never connected (dead): all signals on `PhotosLibrary`,
`VisionAPIClient`, `PhotoAnalysisEngine`, `CategorizationSystem`,
`AlbumSystem`, `AlbumSidebar.album_selected`, `CategoryBadge.category_changed`.

## Configuration storage

- Path: `~/Library/Preferences/photo-boss/config.json`
- Same path in dev and bundled (no `sys.frozen` branch).
- `Config._load_config` swallows `JSONDecodeError` and `IOError` and
  silently falls back to defaults. Corrupt config is not surfaced to UI.
- Defaults include `batch_size: 100` and `categories: ["memories",
  "todo", "research"]`.

## Asset packaging path

```
src/photo_boss/assets/                     <-- sub-package (has __init__.py)
src/photo_boss/assets/icons/               <-- sub-package
src/photo_boss/assets/icons/icon.svg       <-- checked in
src/photo_boss/assets/icons/icon.icns      <-- generated, gitignored

PyInstaller spec datas: (assets dir, "photo_boss/assets")
  -> ends up at <bundle>/Contents/Resources/photo_boss/assets/
  -> importlib.resources finds it identically to dev mode
```

## Things that are deliberately not done

- App sandbox (incompatible with ad-hoc signing + Photos TCC).
- Notarization (no Apple Developer ID; see top-level README rationale).
- Universal2 binary (arm64 only; spec hardcodes `target_arch="arm64"`).
- Async I/O / `asyncio` integration (Qt event loop only).
- Keychain for the API key (plaintext JSON).
