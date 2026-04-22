"""
Photos Framework integration using PyObjC for macOS.

Provides access to the user's Photos library: authorization, album/asset
enumeration, on-disk-cached thumbnails, and album mutations. Falls back to a
deterministic stub when run on a non-Darwin platform or when PyObjC isn't
importable, so the UI is exercisable everywhere.

Public surface, dict shapes, and the `get_photos_library()` singleton are
intentionally identical to the previous stub - see `docs/photo-access.md`.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------

_IS_DARWIN = sys.platform == "darwin"

# Symbols populated only when the real backend loads successfully.
_PHOTOS_AVAILABLE = False
_PHOTOS_IMPORT_ERROR: Optional[str] = None

if _IS_DARWIN:
    try:
        from Foundation import NSPredicate, NSSortDescriptor
        from Photos import (
            PHAccessLevelReadWrite,
            PHAsset,
            PHAssetCollection,
            PHAssetCollectionChangeRequest,
            PHAssetCollectionSubtypeAny,
            PHAssetCollectionSubtypeSmartAlbumFavorites,
            PHAssetCollectionSubtypeSmartAlbumRecentlyAdded,
            PHAssetCollectionSubtypeSmartAlbumSelfPortraits,
            PHAssetCollectionSubtypeSmartAlbumUserLibrary,
            PHAssetCollectionTypeAlbum,
            PHAssetCollectionTypeSmartAlbum,
            PHAssetMediaTypeImage,
            PHAuthorizationStatusAuthorized,
            PHAuthorizationStatusDenied,
            PHAuthorizationStatusLimited,
            PHAuthorizationStatusNotDetermined,
            PHAuthorizationStatusRestricted,
            PHFetchOptions,
            PHImageManager,
            PHImageRequestOptions,
            PHImageRequestOptionsDeliveryModeHighQualityFormat,
            PHImageRequestOptionsResizeModeFast,
            PHImageResultIsDegradedKey,
            PHPhotoLibrary,
        )

        _PHOTOS_AVAILABLE = True
    except Exception as exc:  # pragma: no cover - import-time only
        _PHOTOS_IMPORT_ERROR = repr(exc)
        logger.warning(
            "PyObjC Photos bridge unavailable; falling back to stub data: %s", exc
        )


# Cache directory for generated thumbnails (one JPEG per asset, keyed by
# localIdentifier). Lives under ~/Library/Caches/photo-bomb/thumbs.
_THUMB_CACHE_DIR = Path.home() / "Library" / "Caches" / "photo-bomb" / "thumbs"


def _safe_filename(identifier: str) -> str:
    """Photos `localIdentifier` contains '/' - sanitize for the FS."""
    return identifier.replace("/", "_").replace(":", "_")


# Legacy album IDs hard-coded in `ui/main_window.py`. Map them to the
# corresponding `PHAssetCollectionSubtype` so the existing UI keeps working
# without modification (see plan: "no UI changes needed").
_LEGACY_ALBUM_MAP: Dict[str, Any] = {}
if _PHOTOS_AVAILABLE:
    _LEGACY_ALBUM_MAP = {
        "all_photos": PHAssetCollectionSubtypeSmartAlbumUserLibrary,
        "favorites": PHAssetCollectionSubtypeSmartAlbumFavorites,
        "recent": PHAssetCollectionSubtypeSmartAlbumRecentlyAdded,
        "selfies": PHAssetCollectionSubtypeSmartAlbumSelfPortraits,
    }


# ---------------------------------------------------------------------------
# PhotosLibrary
# ---------------------------------------------------------------------------


class PhotosLibrary(QObject):
    """
    Wrapper around macOS Photos.framework.

    On non-Darwin platforms (or when PyObjC import failed), every method
    returns the same deterministic sample data the previous stub returned, so
    UI development off-Mac still works.
    """

    photos_loaded = pyqtSignal(list)
    albums_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._authorization_status = "not_determined"
        self._albums: List[Dict[str, Any]] = []
        self._photos: List[Dict[str, Any]] = []

        if self.is_available:
            self._authorization_status = self._map_status(
                PHPhotoLibrary.authorizationStatusForAccessLevel_(
                    PHAccessLevelReadWrite
                )
            )

    # ------------------------------------------------------------------
    # Capability flags
    # ------------------------------------------------------------------

    @property
    def is_available(self) -> bool:
        """True when the real Photos backend is usable."""
        return _PHOTOS_AVAILABLE

    @property
    def is_authorized(self) -> bool:
        return self._authorization_status in ("authorized", "limited")

    @property
    def authorization_status(self) -> str:
        return self._authorization_status

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------

    def request_authorization(self) -> str:
        """
        Synchronously prompt for Photos access (read+write) and return the
        resulting status string.

        The TCC handler fires on a background thread; we block here on a
        threading.Event so callers (UI code) get a simple sync return.
        """
        if not self.is_available:
            self._authorization_status = "not_available"
            return "not_available"

        current = PHPhotoLibrary.authorizationStatusForAccessLevel_(
            PHAccessLevelReadWrite
        )
        if current != PHAuthorizationStatusNotDetermined:
            self._authorization_status = self._map_status(current)
            return self._authorization_status

        done = threading.Event()
        result: Dict[str, int] = {}

        def _handler(status: int) -> None:
            result["status"] = status
            done.set()

        PHPhotoLibrary.requestAuthorizationForAccessLevel_handler_(
            PHAccessLevelReadWrite, _handler
        )
        # macOS TCC will block until the user dismisses the dialog. A 60s
        # ceiling avoids deadlock if the prompt is somehow suppressed.
        done.wait(timeout=60)

        status = result.get("status", PHAuthorizationStatusNotDetermined)
        self._authorization_status = self._map_status(status)
        return self._authorization_status

    @staticmethod
    def _map_status(status: int) -> str:
        if status == PHAuthorizationStatusAuthorized:
            return "authorized"
        if status == PHAuthorizationStatusLimited:
            return "limited"
        if status == PHAuthorizationStatusDenied:
            return "denied"
        if status == PHAuthorizationStatusRestricted:
            return "restricted"
        return "not_determined"

    # ------------------------------------------------------------------
    # Albums
    # ------------------------------------------------------------------

    def get_albums(self) -> List[Dict[str, Any]]:
        """Enumerate user + smart albums as `{name, count, identifier}` dicts."""
        if not self.is_available:
            return self._stub_albums()

        if not self._ensure_authorized():
            return []

        try:
            albums: List[Dict[str, Any]] = []
            for coll_type in (
                PHAssetCollectionTypeSmartAlbum,
                PHAssetCollectionTypeAlbum,
            ):
                fetch = PHAssetCollection.fetchAssetCollectionsWithType_subtype_options_(
                    coll_type, PHAssetCollectionSubtypeAny, None
                )
                for i in range(fetch.count()):
                    coll = fetch.objectAtIndex_(i)
                    name = coll.localizedTitle() or "(untitled)"
                    assets = PHAsset.fetchAssetsInAssetCollection_options_(
                        coll, self._image_only_options()
                    )
                    albums.append(
                        {
                            "name": str(name),
                            "count": int(assets.count()),
                            "identifier": str(coll.localIdentifier()),
                        }
                    )
        except Exception as exc:
            logger.exception("get_albums failed")
            self.error_occurred.emit(f"Failed to enumerate albums: {exc}")
            return []

        self._albums = albums
        self.albums_loaded.emit(albums)
        return albums

    # ------------------------------------------------------------------
    # Photos
    # ------------------------------------------------------------------

    def get_photos_for_album(
        self, album_id: str, offset: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch up to `limit` photos starting at `offset` from `album_id`.

        `album_id` may be either a `PHAssetCollection.localIdentifier` (real
        backend) or one of the legacy strings hard-coded in the UI:
        `all_photos`, `favorites`, `recent`, `selfies`.
        """
        if not self.is_available:
            return self._stub_photos(limit)

        if not self._ensure_authorized():
            return []

        try:
            collection = self._resolve_collection(album_id)
            if collection is None:
                self.error_occurred.emit(f"Album not found: {album_id}")
                return []

            fetch = PHAsset.fetchAssetsInAssetCollection_options_(
                collection, self._image_only_options(sort_descending=True)
            )

            total = fetch.count()
            end = min(offset + limit, total)
            results: List[Dict[str, Any]] = []
            for i in range(offset, end):
                asset = fetch.objectAtIndex_(i)
                results.append(self._asset_to_dict(asset))
        except Exception as exc:
            logger.exception("get_photos_for_album failed")
            self.error_occurred.emit(f"Failed to load photos: {exc}")
            return []

        self._photos = results
        self.photos_loaded.emit(results)
        return results

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def create_album(self, name: str) -> Optional[Dict[str, Any]]:
        if not self.is_available:
            return self._stub_create_album(name)
        if not self._ensure_authorized():
            return None

        created_id_box: Dict[str, str] = {}

        def _changes() -> None:
            req = PHAssetCollectionChangeRequest.creationRequestForAssetCollectionWithTitle_(
                name
            )
            placeholder = req.placeholderForCreatedAssetCollection()
            created_id_box["id"] = str(placeholder.localIdentifier())

        if not self._perform_changes(_changes, "create_album"):
            return None

        new_id = created_id_box.get("id", "")
        return {"name": name, "count": 0, "identifier": new_id}

    def find_or_create_album(self, name: str) -> Optional[Dict[str, Any]]:
        """Return the first user album matching `name`, creating it if absent."""
        for album in self.get_albums():
            if album["name"] == name:
                return album
        return self.create_album(name)

    def delete_album(self, album_id: str) -> bool:
        if not self.is_available:
            return self._stub_delete_album(album_id)
        if not self._ensure_authorized():
            return False

        coll = self._resolve_collection(album_id)
        if coll is None:
            return False

        def _changes() -> None:
            PHAssetCollectionChangeRequest.deleteAssetCollections_([coll])

        return self._perform_changes(_changes, "delete_album")

    def add_photos_to_album(
        self, photo_ids: List[str], album_id: str
    ) -> bool:
        if not self.is_available:
            return True
        if not self._ensure_authorized() or not photo_ids:
            return False

        coll = self._resolve_collection(album_id)
        assets = self._resolve_assets(photo_ids)
        if coll is None or assets is None:
            return False

        def _changes() -> None:
            req = PHAssetCollectionChangeRequest.changeRequestForAssetCollection_(
                coll
            )
            req.addAssets_(assets)

        return self._perform_changes(_changes, "add_photos_to_album")

    def remove_photos_from_album(
        self, photo_ids: List[str], album_id: str
    ) -> bool:
        if not self.is_available:
            return True
        if not self._ensure_authorized() or not photo_ids:
            return False

        coll = self._resolve_collection(album_id)
        assets = self._resolve_assets(photo_ids)
        if coll is None or assets is None:
            return False

        def _changes() -> None:
            req = PHAssetCollectionChangeRequest.changeRequestForAssetCollection_(
                coll
            )
            req.removeAssets_(assets)

        return self._perform_changes(_changes, "remove_photos_from_album")

    def move_photos_to_album(
        self, photo_ids: List[str], target_album_id: str
    ) -> bool:
        """
        Add the given assets to `target_album_id` and remove them from every
        other user album that currently contains them. Smart albums are
        immutable and skipped.
        """
        if not self.is_available:
            return True
        if not self._ensure_authorized() or not photo_ids:
            return False

        target = self._resolve_collection(target_album_id)
        assets = self._resolve_assets(photo_ids)
        if target is None or assets is None:
            return False

        # Find every user album that contains at least one of the source
        # assets, so we can pull them out in the same change block.
        source_albums: List[Any] = []
        try:
            user_albums = (
                PHAssetCollection.fetchAssetCollectionsWithType_subtype_options_(
                    PHAssetCollectionTypeAlbum,
                    PHAssetCollectionSubtypeAny,
                    None,
                )
            )
            id_set = set(photo_ids)
            for i in range(user_albums.count()):
                coll = user_albums.objectAtIndex_(i)
                if str(coll.localIdentifier()) == target_album_id:
                    continue
                contained = PHAsset.fetchAssetsInAssetCollection_options_(
                    coll, None
                )
                for j in range(contained.count()):
                    if str(contained.objectAtIndex_(j).localIdentifier()) in id_set:
                        source_albums.append(coll)
                        break
        except Exception:
            logger.exception("move_photos_to_album: source-album scan failed")

        def _changes() -> None:
            add_req = (
                PHAssetCollectionChangeRequest.changeRequestForAssetCollection_(
                    target
                )
            )
            add_req.addAssets_(assets)
            for coll in source_albums:
                rm_req = (
                    PHAssetCollectionChangeRequest.changeRequestForAssetCollection_(
                        coll
                    )
                )
                rm_req.removeAssets_(assets)

        return self._perform_changes(_changes, "move_photos_to_album")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_authorized(self) -> bool:
        if not self.is_authorized:
            # Lazy prompt the first time someone actually needs data.
            self.request_authorization()
        if not self.is_authorized:
            self.error_occurred.emit(
                f"Photos access not granted (status: {self._authorization_status})"
            )
            return False
        return True

    @staticmethod
    def _image_only_options(sort_descending: bool = False) -> Any:
        opts = PHFetchOptions.alloc().init()
        opts.setPredicate_(
            NSPredicate.predicateWithFormat_(
                "mediaType == %d", PHAssetMediaTypeImage
            )
        )
        opts.setSortDescriptors_(
            [
                NSSortDescriptor.sortDescriptorWithKey_ascending_(
                    "creationDate", not sort_descending
                )
            ]
        )
        return opts

    def _resolve_collection(self, album_id: str) -> Any:
        """Map a UI/legacy album_id or a real localIdentifier to a PHAssetCollection."""
        if album_id in _LEGACY_ALBUM_MAP:
            subtype = _LEGACY_ALBUM_MAP[album_id]
            fetch = PHAssetCollection.fetchAssetCollectionsWithType_subtype_options_(
                PHAssetCollectionTypeSmartAlbum, subtype, None
            )
            if fetch.count() == 0:
                return None
            return fetch.objectAtIndex_(0)

        fetch = PHAssetCollection.fetchAssetCollectionsWithLocalIdentifiers_options_(
            [album_id], None
        )
        if fetch.count() == 0:
            return None
        return fetch.objectAtIndex_(0)

    @staticmethod
    def _resolve_assets(photo_ids: List[str]) -> Any:
        fetch = PHAsset.fetchAssetsWithLocalIdentifiers_options_(photo_ids, None)
        if fetch.count() == 0:
            return None
        return fetch

    def _asset_to_dict(self, asset: Any) -> Dict[str, Any]:
        identifier = str(asset.localIdentifier())
        try:
            filename = str(asset.valueForKey_("filename") or "")
        except Exception:
            filename = ""
        try:
            date_obj = asset.creationDate()
            iso = (
                date_obj.descriptionWithCalendarFormat_timeZone_locale_(
                    "%Y-%m-%dT%H:%M:%SZ", None, None
                )
                if date_obj is not None
                else ""
            )
        except Exception:
            iso = ""

        return {
            "identifier": identifier,
            "filename": filename,
            "date": str(iso),
            "thumbnail_path": self._thumbnail_for(asset),
            "dimensions": {
                "width": int(asset.pixelWidth()),
                "height": int(asset.pixelHeight()),
            },
        }

    def _perform_changes(self, block, label: str) -> bool:
        try:
            success, error = (
                PHPhotoLibrary.sharedPhotoLibrary().performChangesAndWait_error_(
                    block, None
                )
            )
        except Exception as exc:
            logger.exception("%s: performChanges raised", label)
            self.error_occurred.emit(f"{label} failed: {exc}")
            return False
        if not success:
            msg = (
                str(error.localizedDescription())
                if error is not None
                else "unknown error"
            )
            logger.error("%s failed: %s", label, msg)
            self.error_occurred.emit(f"{label} failed: {msg}")
            return False
        return True

    # ------------------------------------------------------------------
    # Thumbnails
    # ------------------------------------------------------------------

    def _thumbnail_for(self, asset: Any) -> Optional[str]:
        """
        Return a filesystem path to a 256-px JPEG thumbnail for `asset`,
        generating and caching it on first request. Returns None on failure.
        """
        identifier = str(asset.localIdentifier())
        cache_path = _THUMB_CACHE_DIR / f"{_safe_filename(identifier)}.jpg"
        if cache_path.exists():
            return str(cache_path)

        try:
            _THUMB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning("thumb cache mkdir failed: %s", exc)
            return None

        opts = PHImageRequestOptions.alloc().init()
        opts.setSynchronous_(True)
        opts.setNetworkAccessAllowed_(True)
        opts.setDeliveryMode_(PHImageRequestOptionsDeliveryModeHighQualityFormat)
        opts.setResizeMode_(PHImageRequestOptionsResizeModeFast)

        captured: Dict[str, Any] = {}

        def _handler(image, info):
            if image is None:
                return
            if info is not None:
                degraded = info.objectForKey_(PHImageResultIsDegradedKey)
                if degraded is not None and bool(degraded):
                    return
            captured["image"] = image

        # 256 logical points square. Photos picks the closest cached size.
        from Quartz import CGSize  # local import - tiny

        target = CGSize(256.0, 256.0)
        PHImageManager.defaultManager().requestImageForAsset_targetSize_contentMode_options_resultHandler_(
            asset, target, 1, opts, _handler  # contentMode 1 == aspectFill
        )

        image = captured.get("image")
        if image is None:
            return None

        if not self._write_jpeg(image, cache_path):
            return None
        return str(cache_path)

    @staticmethod
    def _write_jpeg(ns_image: Any, path: Path) -> bool:
        """Persist an `NSImage` to `path` as JPEG via ImageIO."""
        try:
            tiff = ns_image.TIFFRepresentation()
            if tiff is None:
                return False
            from AppKit import NSBitmapImageRep, NSBitmapImageFileTypeJPEG

            rep = NSBitmapImageRep.imageRepWithData_(tiff)
            if rep is None:
                return False
            data = rep.representationUsingType_properties_(
                NSBitmapImageFileTypeJPEG, {"NSImageCompressionFactor": 0.85}
            )
            if data is None:
                return False
            return bool(data.writeToFile_atomically_(str(path), True))
        except Exception:
            logger.exception("thumbnail write failed")
            return False

    # ------------------------------------------------------------------
    # Stub fallbacks (non-Darwin / no PyObjC)
    # ------------------------------------------------------------------

    def _stub_albums(self) -> List[Dict[str, Any]]:
        sample = [
            {"name": "All Photos", "count": 0, "identifier": "all_photos"},
            {"name": "Favorites", "count": 0, "identifier": "favorites"},
            {"name": "Recent", "count": 0, "identifier": "recent"},
            {"name": "Selfies", "count": 0, "identifier": "selfies"},
        ]
        self._albums = sample
        self.albums_loaded.emit(sample)
        return sample

    def _stub_photos(self, limit: int) -> List[Dict[str, Any]]:
        sample = [
            {
                "identifier": f"photo_{i}",
                "filename": f"image_{i}.jpg",
                "date": f"2024-01-{(i % 28) + 1:02d}T12:00:00Z",
                "thumbnail_path": None,
                "dimensions": {"width": 1920, "height": 1080},
            }
            for i in range(min(limit, 10))
        ]
        self._photos = sample
        self.photos_loaded.emit(sample)
        return sample

    def _stub_create_album(self, name: str) -> Dict[str, Any]:
        new_album = {
            "name": name,
            "count": 0,
            "identifier": f"album_{len(self._albums)}",
        }
        self._albums.append(new_album)
        return new_album

    def _stub_delete_album(self, album_id: str) -> bool:
        for album in list(self._albums):
            if album["identifier"] == album_id:
                self._albums.remove(album)
                return True
        return False


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_photos_library: Optional[PhotosLibrary] = None


def get_photos_library() -> PhotosLibrary:
    """Get or create the global photos library instance."""
    global _photos_library
    if _photos_library is None:
        if _IS_DARWIN and not _PHOTOS_AVAILABLE:
            logger.warning(
                "Running on Darwin but PyObjC Photos bridge failed to import "
                "(%s); using stub data.",
                _PHOTOS_IMPORT_ERROR,
            )
        _photos_library = PhotosLibrary()
    return _photos_library
