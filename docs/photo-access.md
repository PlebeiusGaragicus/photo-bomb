# Photo Access

macOS Photos framework integration using PyObjC.

## Overview

Photo Boss uses **PyObjC** to access the native macOS Photos.framework, enabling:
- Reading photos from the user's library
- Listing albums
- Getting photo metadata (filename, creation date)
- Future: Creating/deleting albums, moving photos

## Current Implementation Status

⚠️ **Placeholder Implementation**

The current `photos_library.py` provides a clean interface but uses placeholder data for testing. Full PyObjC integration requires:

1. Requesting Photos library access
2. Enumerating albums and photos
3. Loading photo data as bytes

## Access Flow

```
User Action (e.g., select album)
  ↓
PhotosLibrary.get_photos_for_album(album_id, offset, limit)
  ↓
Photos.framework → PyObjC bridge
  ↓
Return photo list with metadata
```

## API Reference

### PhotosLibrary Class

**File**: `src/core/photos_library.py`

```python
class PhotosLibrary:
    """Wrapper for macOS Photos framework."""
    
    def request_authorization() -> str:
        """
        Request access to Photos library.
        
        Returns: Authorization status string
        """
    
    def get_albums() -> List[dict]:
        """
        Get all albums in the library.
        
        Returns: List of album dicts with 'id', 'name'
        """
    
    def get_photos_for_album(album_id: str, offset: int = 0, limit: int = 100) -> List[dict]:
        """
        Get photos from a specific album.
        
        Args:
            album_id: Album identifier
            offset: Pagination offset
            limit: Maximum photos to return (max 100)
            
        Returns: List of photo dicts with 'identifier', 'filename', 'creation_date'
        """
```

## Authorization Flow

### Step 1: Request Access
```python
from Photos import PHAuthorizationStatus

status =PhotosLibrary.request_authorization()
if status == PHAuthorizationStatus.Authorized:
    # Proceed with library access
else:
    # Show error, explain why access is needed
```

### Step 2: Enumerate Albums
```python
albums = photos_lib.get_albums()
for album in albums:
    print(f"{album['name']} - {len(album['photos'])} photos")
```

### Step 3: Load Photos
```python
photos = photos_lib.get_photos_for_album("album_id", offset=0, limit=50)
for photo in photos:
    print(f"{photo['filename']} (created {photo['creation_date']})")
```

## Future Implementation Plan

1. **Phase 1**: Full PyObjC integration for read-only operations
   - Enumerate all albums
   - Retrieve photo metadata and thumbnails

2. **Phase 2**: Write operations
   - Create new albums
   - Move photos between albums
   - Delete albums (only the album, not actual photos)

3. **Phase 3**: Optimizations
   - Batch loading with pagination
   - Thumbnail caching
   - Background threading for large libraries

## Error Handling

Common errors and solutions:
- **Authorization denied**: Show dialog explaining required permissions
- **Library unavailable**: Check Photos app is accessible
- **Photo load failed**: Retry with reduced batch size
