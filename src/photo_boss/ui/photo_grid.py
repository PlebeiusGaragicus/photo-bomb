"""
Photo grid view for displaying photos with pagination.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QScrollArea,
    QWidget, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap


class PhotoGridWidget(QFrame):
    """
    Grid view for displaying photos with pagination controls.
    Loads at most 100 photos at a time.
    """
    
    photo_selected = pyqtSignal(str)  # photo_id
    batch_requested = pyqtSignal(int, int)  # offset, limit
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PhotoGridWidget")
        self.photos = []
        self.current_offset = 0
        self.batch_size = 100
        self.total_count = 0
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the grid view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Photo grid container with scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Grid container
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area)
        
        # Pagination controls
        pagination_widget = QWidget()
        pagination_layout = QHBoxLayout(pagination_widget)
        pagination_layout.setContentsMargins(5, 5, 5, 5)
        
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(lambda: self._navigate(-1))
        self.prev_button.setEnabled(False)
        
        self.page_label = QLabel("Page 0-10 of 0")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(lambda: self._navigate(1))
        
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        
        layout.addWidget(pagination_widget)
    
    def _navigate(self, direction: int):
        """Navigate to next/previous page."""
        if direction < 0 and self.current_offset > 0:
            new_offset = max(0, self.current_offset - self.batch_size)
            self.load_photos(new_offset, self.batch_size)
        elif direction > 0:
            new_offset = self.current_offset + self.batch_size
            if new_offset < self.total_count:
                self.load_photos(new_offset, self.batch_size)
    
    def load_photos(self, offset: int = 0, limit: int = 100):
        """
        Load photos with pagination.
        
        Args:
            offset: Starting position
            limit: Maximum number of photos (max 100)
        """
        # Limit to max batch size
        limit = min(limit, self.batch_size)
        self.current_offset = offset
        
        # Emit signal for parent to load actual photo data
        self.batch_requested.emit(offset, limit)
        
        # Update pagination controls (will be set by parent)
        self._update_pagination()
    
    def _update_pagination(self):
        """Update pagination UI controls."""
        start = self.current_offset + 1
        end = min(self.current_offset + len(self.photos), self.total_count)
        self.page_label.setText(f"Photos {start}-{end} of {self.total_count}")
        
        self.prev_button.setEnabled(self.current_offset > 0)
    
    def add_photo_item(self, photo_id: str, filename: str):
        """
        Add a photo thumbnail to the grid.
        
        Args:
            photo_id: Unique identifier for the photo
            filename: Display name
        """
        # Find next empty position in grid
        row = len(self.grid_layout.itemAtPosition(0, 0)) if self.grid_layout.count() == 0 else 0
        
        item_widget = QWidget()
        item_layout = QVBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 5, 5, 5)
        
        # Placeholder for thumbnail
        thumb_label = QLabel(f"Thumbnail\n{filename}")
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setStyleSheet("""
            QLabel {
                background-color: #e0e0e0;
                border: 2px solid #cccccc;
                border-radius: 5px;
                min-height: 150px;
            }
        """)
        
        def select_photo():
            self.photo_selected.emit(photo_id)
        
        thumb_label.mousePressEvent = lambda e: select_photo()
        thumb_label.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Photo info
        info_label = QLabel(filename)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("QLabel { font-size: 10px; color: #666; }")
        
        item_layout.addWidget(thumb_label)
        item_layout.addWidget(info_label)
        
        self.grid_layout.addWidget(item_widget, row // 4, row % 4)
    
    def clear(self):
        """Clear all photos from the grid."""
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.photos.clear()
