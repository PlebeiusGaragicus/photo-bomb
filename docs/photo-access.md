# Photos Access

`core/photos_library.py` is a real PyObjC-backed wrapper around macOS
`Photos.framework`. On non-Darwin platforms (or when the PyObjC bridge fails
to import) it transparently falls back to deterministic stub data so the UI
remains exercisable everywhere.

## Public surface

```python
from photo_bomb.core.photos_library import get_photos_library  # singleton

lib = get_photos_library()
lib.is_available           # True iff the real Photos backend loaded
lib.is_authorized          # True for "authorized" or "limited"
lib.authorization_status   # "not_determined" | "authorized" | "limited"
                           #  | "denied" | "restricted" | "not_available"
lib.request_authorization()                          # -> status string (sync)
lib.get_albums()                                     # -> list[dict]
lib.get_photos_for_album(album_id, offset=0, limit=100)  # -> list[dict]
lib.create_album(name)                               # -> dict | None
lib.find_or_create_album(name)                       # -> dict | None
lib.delete_album(album_id)                           # -> bool
lib.add_photos_to_album(photo_ids, album_id)         # -> bool
lib.remove_photos_from_album(photo_ids, album_id)    # -> bool
lib.move_photos_to_album(photo_ids, target_album_id) # -> bool
```

Signals (declared, emitted by the corresponding methods, not yet wired into
the UI): `photos_loaded(list)`, `albums_loaded(list)`, `error_occurred(str)`.

Dict shapes:

```python
album = {"name": str, "count": int, "identifier": str}
photo = {
    "identifier": str,                    # PHAsset.localIdentifier
    "filename": str,
    "date": str,                          # ISO 8601, UTC
    "thumbnail_path": str | None,         # path to a cached 256-px JPEG
    "dimensions": {"width": int, "height": int},
}
```

`identifier` for albums returned by `get_albums()` is the
`PHAssetCollection.localIdentifier`. `get_photos_for_album` also accepts the
legacy strings hard-coded in `ui/main_window.py` -
`"all_photos" | "favorites" | "recent" | "selfies"` - and maps them to the
matching `PHAssetCollectionSubtypeSmartAlbum*` so the existing UI keeps
working without modification.

## Implementation notes

1. **Authorization.** `request_authorization()` is synchronous: it calls
   `PHPhotoLibrary.requestAuthorizationForAccessLevel_handler_` with
   `PHAccessLevelReadWrite` and blocks on a `threading.Event` until the TCC
   handler fires (60s ceiling). The handler runs off-main-thread; only the
   final status string is returned to the caller.
2. **Albums.** Both `PHAssetCollectionTypeSmartAlbum` and
   `PHAssetCollectionTypeAlbum` are enumerated. Per-album `count` is the
   image-only asset count (smart albums and user albums alike).
3. **Photos.** `PHAsset.fetchAssetsInAssetCollection_options_` with a
   `PHFetchOptions` that filters `mediaType == PHAssetMediaTypeImage` and
   sorts by `creationDate` descending. Pagination uses `objectAtIndex_` over
   the lazy `PHFetchResult`, so `offset`/`limit` is cheap.
4. **Thumbnails.** A 256x256 aspect-fill thumbnail is requested
   synchronously per asset via `PHImageManager.defaultManager()`,
   high-quality delivery, network access allowed. The result handler skips
   the degraded callback (`PHImageResultIsDegradedKey`). The image is
   written as JPEG (quality 0.85) to
   `~/Library/Caches/photo-bomb/thumbs/<sanitized-localIdentifier>.jpg` and
   cached on disk - subsequent calls for the same asset are a stat.
5. **Mutations.** All write paths (`create_album`, `delete_album`,
   `add/remove/move_photos_*`) wrap `PHAssetCollectionChangeRequest` /
   `PHAssetChangeRequest` calls in
   `PHPhotoLibrary.sharedPhotoLibrary().performChangesAndWait_error_`. They
   require `PHAccessLevelReadWrite`. `move_photos_to_album` adds to the
   target collection and removes from every other user album currently
   containing the assets - smart albums are untouched.
6. **`find_or_create_album(name)`.** Iterates `get_albums()` for an exact
   `name` match and returns it; otherwise calls `create_album(name)`.
   This is the primitive the UI's "categorize" buttons use to lazily
   provision the `Memories` / `Todo` / `Research` albums on first use.

## Permissions infrastructure

Already in place (don't change unless packaging changes):

- `Info.plist` declares `NSPhotoLibraryUsageDescription` and
  `NSPhotoLibraryAddUsageDescription` (set in
  `packaging/photo_bomb.spec`). Without these, `request_authorization`
  crashes the process via TCC violation.
- `entitlements.plist` declares
  `com.apple.security.personal-information.photos-library`.
- The bundle is **ad-hoc signed** (`codesign --sign -`), giving it a
  stable identity that TCC keys the user's Photos permission against.
  Unsigned builds will re-prompt on every launch - or be killed before
  first prompt on Apple Silicon.

After a code change that alters the binary's signature, macOS may revoke
the user's previously-granted Photos permission. During development,
reset with:

```bash
tccutil reset Photos com.photobomb.app
```

When running directly from source (`python -m photo_bomb`), TCC keys the
permission against the Python interpreter rather than the app bundle, so
expect a re-prompt the first time a fresh interpreter calls
`request_authorization`.

## Off-Mac fallback

`is_available` returns `False` when:

- `sys.platform != "darwin"`, or
- the PyObjC `Photos` bridge failed to import.

In that mode every method returns the same deterministic sample data the
old stub returned (4 placeholder albums; up to 10 synthetic photos with
`thumbnail_path: None`). A single warning is logged at first
`get_photos_library()` call. UI work that doesn't depend on real photo
bytes can run on macOS, Linux, or CI without changes.

## Out of scope

These are intentionally not implemented yet:

- `PHPhotoLibraryChangeObserver` for live updates when the user edits
  Photos in another app.
- iCloud-only assets that need an opt-in network download for the full
  pixel data (thumbnail requests already pass `networkAccessAllowed=True`).
- Video assets - the fetch predicate filters to `PHAssetMediaTypeImage`.
