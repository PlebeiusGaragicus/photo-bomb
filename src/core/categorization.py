"""
Photo categorization system for managing tags and categories.
"""

from typing import Dict, List, Any
from PyQt6.QtCore import QObject, pyqtSignal


class CategorizationSystem(QObject):
    """
    Manages photo categorization with the three main categories:
    - memories: Personal/family photos, important moments, events
    - todo: Photos containing tasks, instructions, reminders (recipes, lists, diagrams)
    - research: Reference materials, documents, articles
    
    Supports manual tagging and batch operations.
    """
    
    category_changed = pyqtSignal(str, str)  # photo_id, new_category
    
    def __init__(self):
        super().__init__()
        self.categories = ["memories", "todo", "research"]
        self._photo_categories: Dict[str, str] = {}
        self._category_colors = {
            "memories": "#4CAF50",  # Green
            "todo": "#FF9800",      # Orange  
            "research": "#2196F3"   # Blue
        }
    
    def get_categories(self) -> List[str]:
        """Get list of available categories."""
        return self.categories.copy()
    
    def get_category_color(self, category: str) -> str:
        """Get the color associated with a category."""
        return self._category_colors.get(category, "#888888")
    
    def categorize_photo(self, photo_id: str, category: str):
        """
        Assign a category to a photo.
        
        Args:
            photo_id: Photo identifier
            category: Category name (memories, todo, or research)
        """
        if category not in self.categories:
            raise ValueError(f"Invalid category: {category}")
        
        # Only update if different from current category
        current = self._photo_categories.get(photo_id)
        if current != category:
            self._photo_categories[photo_id] = category
            self.category_changed.emit(photo_id, category)
    
    def get_photo_category(self, photo_id: str) -> str:
        """Get the category of a photo."""
        return self._photo_categories.get(photo_id, "memories")  # Default to memories
    
    def batch_categorize(self, photo_ids: List[str], category: str):
        """
        Categorize multiple photos at once.
        
        Args:
            photo_ids: List of photo identifiers
            category: Category to assign
        """
        for photo_id in photo_ids:
            self.categorize_photo(photo_id, category)
    
    def get_photos_by_category(self, category: str) -> List[str]:
        """Get all photos in a specific category."""
        return [
            photo_id 
            for photo_id, cat in self._photo_categories.items() 
            if cat == category
        ]
    
    def clear_photo_category(self, photo_id: str):
        """Clear the category of a photo (reset to default)."""
        current = self._photo_categories.pop(photo_id, None)
        if current is not None:
            self.category_changed.emit(photo_id, "memories")
    
    def get_all_categorization(self) -> Dict[str, str]:
        """Get complete categorization mapping."""
        return self._photo_categories.copy()
    
    def load_from_dict(self, data: Dict[str, Any]):
        """Load categorization data from dictionary."""
        if "photo_categories" in data:
            self._photo_categories = data["photo_categories"]
    
    def save_to_dict(self) -> Dict[str, Any]:
        """Save categorization data to dictionary."""
        return {
            "photo_categories": self._photo_categories
        }
