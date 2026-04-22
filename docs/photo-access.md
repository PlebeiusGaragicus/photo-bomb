# Photos Access

`core/photos_library.py` is a **stub** that returns hardcoded sample data.
PyObjC is declared as a dependency on Darwin but never imported. This doc
is the spec for the real port.

## Current public surface

```python
from photo_boss.core.photos_library import get_photos_library  # singleton

lib = get_photos_library()
lib.is_available           # True on Darwin, False otherwise
lib.is_authorized          # always False until request_authorization()
lib.authorization_status   # "not_determined" | "authorized" | "not_available"
lib.request_authorization()                          # -> status string
lib.get_albums()                                     # -> list[dict]
lib.get_photos_for_album(album_id, offset=0, limit=100)  # -> list[dict]
lib.create_album(name)                               # -> dict | None
lib.delete_album(album_id)                           # -> bool
lib.add_photos_to_album(photo_ids, album_id)         # -> bool
lib.remove_photos_from_album(photo_ids, album_id)    # -> bool
lib.move_photos_to_album(photo_ids, target_album_id) # -> bool
```

Signals (declared, not connected anywhere):
`photos_loaded(list)`, `albums_loaded(list)`, `error_occurred(str)`.

Dict shapes returned by the stubs (the real impl must preserve these or
update every caller in `ui/main_window.py`):

```python
album = {"name": str, "count": int, "identifier": str}
photo = {
    "identifier": str,
    "filename": str,
    "date": str,                          # ISO 8601
    "thumbnail_path": str | None,
    "dimensions": {"width": int, "height": int},
}
```

## What a real PyObjC port has to do

1. **Authorization.** Call
   `PHPhotoLibrary.requestAuthorizationForAccessLevel_handler_` (10.15+)
   with `PHAccessLevelReadWrite`. Map the resulting `PHAuthorizationStatus`
   enum to the strings above. Note: the handler fires on a non-main
   thread - marshal back to Qt via a `pyqtSignal` or
   `QMetaObject.invokeMethod`.
2. **Albums.** `PHAssetCollection.fetchAssetCollectionsWithType_subtype_options_`
   for both user albums (`PHAssetCollectionTypeAlbum`) and smart albums
   (`PHAssetCollectionTypeSmartAlbum`). Wrap each `PHAssetCollection` in
   the dict shape above; use `localIdentifier` as `identifier`.
3. **Photos.** Per-album:
   `PHAsset.fetchAssetsInAssetCollection_options_` with a
   `PHFetchOptions` configured for `creationDate` sort. Honor `offset`
   and `limit` by slicing the returned `PHFetchResult` (it's lazy, so
   slicing is cheap).
4. **Pixel data.** Use `PHImageManager.defaultManager` -
   `requestImageForAsset_targetSize_contentMode_options_resultHandler_`.
   For analysis, request `PHImageManagerMaximumSize` with
   `PHImageRequestOptionsDeliveryModeHighQualityFormat` and
   `synchronous=False`. The result handler will fire multiple times if
   you ask for non-degraded only - filter on the `PHImageResultIsDegradedKey`
   in the `info` dict.
5. **Album mutation.** Wrap in
   `PHPhotoLibrary.sharedPhotoLibrary().performChangesAndWait_error_`.
   Use `PHAssetCollectionChangeRequest` and
   `PHAssetChangeRequest`. Mutations require `PHAccessLevelReadWrite`.

## Permissions infrastructure already in place

You don't need to touch packaging to get TCC to work; this is already done:

- `Info.plist` declares `NSPhotoLibraryUsageDescription` and
  `NSPhotoLibraryAddUsageDescription` (set in
  `packaging/photo_boss.spec`). Without these, `request_authorization`
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
tccutil reset Photos com.photoboss.app
```

## Testing without a real implementation

The stub is deliberately testable: `get_photos_library()` works on any
platform and returns deterministic samples. UI work that doesn't depend
on real photo bytes can run on macOS, Linux, or CI without changes.
`is_available` is the canonical platform guard.
