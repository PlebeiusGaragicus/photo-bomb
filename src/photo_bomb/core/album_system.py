"""
Album management system for organizing photos.
"""

from typing import Dict, List, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal


class AlbumSystem(QObject):
    """
    Manages photo albums including creation, deletion, and photo organization.
    
    Supports:
    - Reading existing albums from Photos library
    - Creating new albums
    - Moving photos between albums
    - Deleting albums (only copies, not deleting actual photos)
    """
    
    # Signals for UI updates
    album_created = pyqtSignal(dict)  # album info
    album_deleted = pyqtSignal(str)   # album_id
    photo_moved = pyqtSignal(str, str, str)  # photo_id, from_album, to_album
    
    def __init__(self):
        super().__init__()
        self._albums: Dict[str, dict] = {}
        self._photo_albums: Dict[str, List[str]] = {}  # photo_id -> list of album_ids
        self._next_id = 1
    
    @property
    def albums(self) -> List[dict]:
        """Get all albums."""
        return list(self._albums.values())
    
    def get_album_by_name(self, name: str) -> Optional[dict]:
        """Get album by name."""
        for album in self._albums.values():
            if album["name"] == name:
                return album
        return None
    
    def create_album(self, name: str) -> dict:
        """
        Create a new album.
        
        Args:
            name: Name for the new album
            
        Returns: Created album dictionary
        """
        album_id = f"album_{self._next_id}"
        self._next_id += 1
        
        album = {
            "id": album_id,
            "name": name,
            "photo_count": 0,
            "photos": []
        }
        
        self._albums[album_id] = album
        self.album_created.emit(album)
        return album
    
    def delete_album(self, album_id: str) -> bool:
        """
        Delete an album.
        
        Note: This only removes the album, not the actual photos.
        
        Args:
            album_id: ID of the album to delete
            
        Returns: True if successful
        """
        if album_id in self._albums:
            # Remove from all photos' album lists
            for photo_id, albums in self._photo_albums.items():
                if album_id in albums:
                    albums.remove(album_id)
            
            del self._albums[album_id]
            self.album_deleted.emit(album_id)
            return True
        return False
    
    def add_photo_to_album(self, photo_id: str, album_id: str):
        """
        Add a photo to an album.
        
        Args:
            photo_id: Photo identifier
            album_id: Album to add to
        """
        if album_id not in self._albums:
            raise ValueError(f"Album not found: {album_id}")
        
        # Track which albums this photo belongs to
        if photo_id not in self._photo_albums:
            self._photo_albums[photo_id] = []
        
        if album_id not in self._photo_albums[photo_id]:
            self._photo_albums[photo_id].append(album_id)
            self._albums[album_id]["photos"].append(photo_id)
            self._albums[album_id]["photo_count"] += 1
    
    def remove_photo_from_album(self, photo_id: str, album_id: str):
        """
        Remove a photo from an album.
        
        Args:
            photo_id: Photo identifier
            album_id: Album to remove from
        """
        if photo_id in self._photo_albums:
            if album_id in self._photo_albums[photo_id]:
                self._photo_albums[photo_id].remove(album_id)
                if album_id in self._albums:
                    self._albums[album_id]["photos"].remove(photo_id)
                    self._albums[album_id]["photo_count"] -= 1
    
    def move_photo_to_album(self, photo_id: str, from_album_id: str, 
                           to_album_id: str) -> bool:
        """
        Move a photo from one album to another.
        
        Args:
            photo_id: Photo identifier
            from_album_id: Source album
            to_album_id: Destination album
            
        Returns: True if successful
        """
        if from_album_id not in self._albums or to_album_id not in self._albums:
            return False
        
        # Remove from source album
        if photo_id in self._photo_albums.get(from_album_id, []):
            self.remove_photo_from_album(photo_id, from_album_id)
        
        # Add to destination album
        self.add_photo_to_album(photo_id, to_album_id)
        
        self.photo_moved.emit(photo_id, from_album_id, to_album_id)
        return True
    
    def get_album_photos(self, album_id: str) -> List[str]:
        """Get all photo IDs in an album."""
        if album_id in self._albums:
            return self._albums[album_id]["photos"].copy()
        return []
    
    def get_photo_albums(self, photo_id: str) -> List[str]:
        """Get all albums a photo belongs to."""
        return self._photo_albums.get(photo_id, []).copy()
    
    def create_default_albums(self):
        """Create standard default albums."""
        defaults = ["All Photos", "Favorites", "Recent", "Selfies"]
        
        for name in defaults:
            if not self.get_album_by_name(name):
                album = self.create_album(name)
                
                # For 'All Photos', mark it specially
                if name == "All Photos":
                    album["is_system"] = True
