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
- Persists to `~/Library/Preferences/photo-bomb/config.json` immediately
  on every `set()` / `update()`. No batching, no atomic write.
- Schema is the `Config.defaults` dict (`api_endpoint`, `api_key`,
  `model_name`). Loaded keys are merged on top of defaults so unknown
  legacy keys are tolerated and forward-compatible.
- API key is stored **plaintext**. macOS Keychain is not used.

### `core/photos_library.py`

- **Singleton** via `get_photos_library() -> PhotosLibrary`.
- Real PyObjC backend on Darwin; deterministic stub fallback elsewhere
  (or if `import Photos` fails). `is_available` is the canonical guard.
- Public surface: `is_available`, `is_authorized`, `authorization_status`,
  `request_authorization`, `get_albums`, `get_photos_for_album`,
  `create_album`, `find_or_create_album`, `delete_album`,
  `add_photos_to_album`, `remove_photos_from_album`,
  `move_photos_to_album`. See [photo-access.md](photo-access.md).
- `find_or_create_album(name)` is the primitive used by manual
  categorization in `MainWindow._on_categorize_clicked` - returns the
  first user album whose `localizedTitle()` matches `name`, creating it
  if absent.
- Subclasses `QObject` for signal support: `photos_loaded(list)`,
  `albums_loaded(list)`, `error_occurred(str)`.

### `core/api_client.py`

- **Not a singleton.** `APISettingsDialog` constructs one for the
  "Test Connection" health check. Configure with `.configure(endpoint,
  key, model)` after construction.
- `endpoint_url` is the **base URL** (e.g. `https://api.openai.com/v1`).
  The client appends `/models` for the health check and `/chat/completions`
  for analysis. Storing the full chat-completions URL in config will
  produce 404s.
- See [api-settings.md](api-settings.md) for the exact request body and
  the latin1-encoding bug in `analyze_photo` (Phase-2 fix).

### `ui/main_window.py`

- Hub for everything. Constructs widgets, owns the splitter, instantiates
  dialogs lazily.
- On `__init__`, calls `library.request_authorization()`; on success,
  populates `AlbumSidebar` from `library.get_albums()`.
- `_on_categorize_clicked` maps the button label to a Photos album name
  via `_CATEGORY_ALBUMS`, calls `library.find_or_create_album(name)`,
  then `library.add_photos_to_album([selected_id], album["identifier"])`,
  then refreshes the sidebar so counts update.
- `show_api_settings` calls `APISettingsDialog.load_settings(config.config)`
  before `exec()` and `dialog.save_to_config(config)` on Accept.
- All callbacks are sync; long-running work must move to a `QThread`.
- Status bar created via `_create_status_bar`; do not call `statusBar()`
  before `__init__` finishes or you'll get an empty default one.

### `ui/album_sidebar.py`

- Pure presentational widget. Emits `album_selected(identifier)` and
  `create_album_requested(name)`; the parent (`MainWindow`) handles
  Photos calls and re-feeds via `set_albums(albums)`.
- Album dict shape is exactly what `PhotosLibrary.get_albums()` returns -
  `{"name", "count", "identifier"}`.

### `ui/photo_grid.py`

- Pagination is **prev/next buttons**, not infinite scroll.
  `batch_size` defaults to 100, controlled by
  `batch_requested(offset, limit)` signal.
- `add_photo_item(photo_id, filename, thumbnail_path)` appends a tile
  using a per-call `_next_index` counter; `clear()` resets it.
- Renders `thumbnail_path` via `QPixmap` (scaled to a 200-px square,
  aspect ratio preserved). Falls back to filename text if the path is
  missing.
- `set_total_count(total)` lets the parent feed the album-wide count so
  the paginator knows when to disable Next.

### `utils/resources.py`

- Single entry point for bundled-asset paths. Uses
  `importlib.resources.files("photo_bomb.assets")` and walks
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
| `AlbumSidebar` | `album_selected(str)` | `MainWindow._on_album_changed` |
| `AlbumSidebar` | `create_album_requested(str)` | `MainWindow._on_create_album` |
| `PhotoGridWidget` | `batch_requested(int, int)` | `MainWindow._load_photo_batch` |
| `PhotoGridWidget` | `photo_selected(str)` | `MainWindow._on_photo_selected` |

`PhotosLibrary` declares `photos_loaded`, `albums_loaded`, and
`error_occurred` for future async use; the synchronous methods emit them
but no UI listens yet.

## Configuration storage

- Path: `~/Library/Preferences/photo-bomb/config.json`
- Same path in dev and bundled (no `sys.frozen` branch).
- `Config._load_config` swallows `JSONDecodeError` and `IOError` and
  silently falls back to defaults. Corrupt config is not surfaced to UI.
- Defaults are limited to `api_endpoint`, `api_key`, `model_name`.

## Asset packaging path

```
src/photo_bomb/assets/                     <-- sub-package (has __init__.py)
src/photo_bomb/assets/icons/               <-- sub-package
src/photo_bomb/assets/icons/icon.svg       <-- checked in
src/photo_bomb/assets/icons/icon.icns      <-- generated, gitignored

PyInstaller spec datas: (assets dir, "photo_bomb/assets")
  -> ends up at <bundle>/Contents/Resources/photo_bomb/assets/
  -> importlib.resources finds it identically to dev mode
```

## Things that are deliberately not done

- App sandbox (incompatible with ad-hoc signing + Photos TCC).
- Notarization (no Apple Developer ID; see top-level README rationale).
- Universal2 binary (arm64 only; spec hardcodes `target_arch="arm64"`).
- Async I/O / `asyncio` integration (Qt event loop only).
- Keychain for the API key (plaintext JSON).
- AI analysis end-to-end (Phase 2; see [features.md](features.md)).
