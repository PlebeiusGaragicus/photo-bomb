# Implementation Status

Honest per-subsystem status. **Most user-visible "features" are scaffolding,
not working software.** This is a POC that compiles, signs, and ships; the
behavior behind the buttons is largely placeholder.

Legend: **real** = functional end-to-end - **partial** = wired but limited
- **stub** = present but unwired or returns fake data.

| Subsystem | Status | Where | Notes |
|-----------|--------|-------|-------|
| App lifecycle (`QApplication`, exit, `--version`) | real | `main.py` | `--version` exits before constructing `QApplication`; smoke-tested in build script |
| Config persistence | real | `core/config.py` | Singleton, writes JSON on every set; plaintext API key |
| Bundled-asset lookup | real | `utils/resources.py` | `importlib.resources`-based; works in dev + frozen |
| Macos `.app` packaging | real | `packaging/`, `scripts/build_macos.sh` | Ad-hoc signed, hardened runtime, Photos usage strings in `Info.plist` |
| GitHub Releases automation | real | `.github/workflows/release.yml` | Triggers on `v*` tags, attaches DMG |
| Main window shell, menu bar, splitter | real | `ui/main_window.py` | UI renders; most actions are stubs |
| API settings dialog | partial | `ui/api_settings_dialog.py` | Inputs work; **does not load from or save to `Config`** (TODO comments in `MainWindow.show_api_settings`) |
| API health check | partial | `core/api_client.py::check_connection` | Hits `/models` then `/chat/completions`; returns first 5 model names |
| API single-photo analysis | partial | `core/api_client.py::analyze_photo` | **Bug:** image bytes are `.decode('latin1')`'d into the data URL instead of base64-encoded. Real endpoints will reject this. |
| Photos library access | stub | `core/photos_library.py` | Returns hardcoded sample albums and 10 fake photo dicts. No PyObjC calls yet. See [photo-access.md](photo-access.md) |
| Photo grid pagination | partial | `ui/photo_grid.py` | Prev/Next buttons emit `batch_requested`; `add_photo_item` has a row-position bug that places every thumbnail at row 0 |
| Photo selection | partial | `ui/photo_grid.py` -> `main_window` | Click triggers `photo_selected`; selected view is a placeholder `QLabel` |
| Manual categorization buttons | partial | `ui/main_window.py::_on_categorize_clicked` | Constructs an unused `CategoryBadge` then writes to status bar. Category is **not persisted anywhere.** |
| `CategorizationSystem` | stub | `core/categorization.py` | Class is complete but **never instantiated** by `ui/`. Dead code. |
| `AlbumSystem` | stub | `core/album_system.py` | Same: class is complete but never instantiated. Dead code. |
| `PhotoAnalysisEngine` | stub | `core/analysis_engine.py` | Same; additionally `_get_photo_data` always returns `None`. |
| Batch analysis dialog | partial | `ui/batch_analysis_dialog.py` | `AnalysisWorker` thread + signals are real, but `MainWindow._on_analyze_clicked` calls `dialog.show()` without ever calling `start_analysis`, so it opens an idle dialog |
| Album sidebar widget | stub | `ui/album_sidebar.py` | Defined but `MainWindow` uses an inline `QListWidget` instead. Two album UIs in the codebase. |
| TCC / Photos permission flow | stub | - | `Info.plist` strings are in place via the spec; `request_authorization` returns `"authorized"` without calling PyObjC |

## Minimum work to get to a working slice

1. Replace `core/photos_library.py` with real PyObjC calls; preserve the
   public method signatures so the UI doesn't change.
2. Wire `APISettingsDialog` to `Config` (load on open, save on accept).
3. Fix the `latin1` bug in `api_client.analyze_photo` - use
   `base64.b64encode(photo_data).decode("ascii")`.
4. Either delete `analysis_engine`, `categorization`, `album_system`, or
   instantiate them in `MainWindow.__init__` and route the existing UI
   actions through them. Pick one; do not leave both code paths.
5. Fix the `add_photo_item` row math in `photo_grid.py`.
