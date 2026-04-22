# Implementation Status

Honest per-subsystem status. Phase 1 has shipped a real end-to-end slice on
top of the PyObjC Photos backend; AI analysis is intentionally deferred.

Legend: **real** = functional end-to-end - **partial** = wired but limited
- **stub** = present but unwired or returns fake data.

| Subsystem | Status | Where | Notes |
|-----------|--------|-------|-------|
| App lifecycle (`QApplication`, exit, `--version`) | real | `main.py` | `--version` exits before constructing `QApplication`; smoke-tested in build script |
| Config persistence | real | `core/config.py` | Singleton, writes JSON on every set; plaintext API key. Defaults: `api_endpoint`, `api_key`, `model_name` only |
| Bundled-asset lookup | real | `utils/resources.py` | `importlib.resources`-based; works in dev + frozen |
| macOS `.app` packaging | real | `packaging/`, `scripts/build_macos.sh` | Ad-hoc signed, hardened runtime, Photos usage strings in `Info.plist` |
| GitHub Releases automation | real | `.github/workflows/release.yml` | Triggers on `v*` tags, attaches DMG |
| Main window shell, menu bar, splitter | real | `ui/main_window.py` | Sidebar + grid + categorize toolbar all wired to `PhotosLibrary` |
| Photos library access | real | `core/photos_library.py` | PyObjC-backed `PHAssetCollection` enumeration, `PHAsset` fetch, disk-cached 256-px thumbnails, `performChangesAndWait_error_` mutations. See [photo-access.md](photo-access.md) |
| TCC / Photos permission flow | real | `core/photos_library.py::request_authorization` | `PHPhotoLibrary.requestAuthorizationForAccessLevel_handler_` (read+write); blocks on `threading.Event` |
| Album sidebar | real | `ui/album_sidebar.py` | `pyqtSignal` based; populated from `library.get_albums()`; "+" button creates a real Photos album |
| Photo grid + thumbnails | real | `ui/photo_grid.py` | Renders `thumbnail_path` via `QPixmap`; per-call index counter for grid math; prev/next pagination wired against album count |
| Photo selection | real | `ui/photo_grid.py` -> `main_window` | Click on tile selects; toolbar buttons enable on selection |
| Manual categorization | real | `ui/main_window.py::_on_categorize_clicked` | Calls `library.find_or_create_album(name)` then `library.add_photos_to_album([id], album_identifier)`. Apple Photos is the persistence layer |
| API settings dialog | real | `ui/api_settings_dialog.py` + `MainWindow.show_api_settings` | Loads from `Config` on open; saves on accept; persists to `~/Library/Preferences/photo-bomb/config.json` |
| API health check | partial | `core/api_client.py::check_connection` | Hits `/models` then `/chat/completions`; returns first 5 model names |
| API single-photo analysis | partial | `core/api_client.py::analyze_photo` | **Bug:** image bytes are `.decode('latin1')`'d into the data URL instead of base64-encoded. Real endpoints will reject this. Out of scope for Phase 1 - re-introduce when AI analysis is wired |

## Removed in Phase 1

These modules used to exist as dead code and have been deleted to keep one
canonical implementation per concept:

- `core/categorization.py` - `CategorizationSystem`. Categorization now
  means "move asset into an Apple Photos album" - Apple Photos is the
  truth, no sidecar dict.
- `core/album_system.py` - `AlbumSystem`. The real
  `Photos.framework`-backed `PhotosLibrary` owns every operation it
  pretended to provide.
- `core/analysis_engine.py` - `PhotoAnalysisEngine`. Was unreachable
  (`_get_photo_data` always returned `None`). Out of scope for Phase 1.
- `ui/category_badge.py` - `CategoryBadge`. With album-as-truth there's
  no badge to render in the current UI.
- `ui/batch_analysis_dialog.py` - `BatchAnalysisDialog` and
  `AnalysisWorker`. Removed alongside the "Analyze Selected Photos"
  button.

## Phase 2 (next steps, intentionally deferred)

1. Wire AI analysis end-to-end:
   - Fix `analyze_photo`: `base64.b64encode(photo_data).decode("ascii")`.
   - Sniff MIME from `photo_data` instead of hardcoding `image/jpeg`.
   - Add a `PhotosLibrary.get_image_data(photo_id, target=PHImageManagerMaximumSize)`
     helper that returns raw bytes (no thumbnail cache) for the analyzer.
   - Re-introduce a small `BatchAnalysisDialog` and run analysis in a
     `QThread`, then call `library.add_photos_to_album` to file the
     result.
2. macOS Keychain integration for `api_key` (today: plaintext JSON).
3. `PHPhotoLibraryChangeObserver` for live sidebar refresh when the user
   edits Photos in another app.
4. Single source of truth for the category set (currently
   `_CATEGORY_ALBUMS` in `ui/main_window.py` and the prompt strings in
   `core/api_client.py::analyze_photo` will both reference categories;
   consolidate when analysis is re-introduced).
