"""
Album sidebar widget with album management UI.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt


class AlbumSidebar(QWidget):
    """
    Sidebar for viewing and managing albums.
    
    Features:
    - Display list of albums with photo counts
    - Create new album button
    - Delete album button
    - Right-click context menu for album operations
    """
    
    album_selected = lambda self, album_id: None  # Will be overridden
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.albums = []
        
    def _setup_ui(self):
        """Set up the sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_label = QLabel("Albums")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
            }
        """)
        layout.addWidget(header_label)
        
        # Album list
        self.album_list = QListWidget()
        self.album_list.itemClicked.connect(self._on_album_selected)
        self.album_list.itemDoubleClicked.connect(self._on_album_double_clicked)
        layout.addWidget(self.album_list)
        
        # New album section
        new_album_widget = QWidget()
        new_layout = QHBoxLayout(new_album_widget)
        new_layout.setContentsMargins(5, 5, 5, 5)
        
        self.new_album_input = QLineEdit()
        self.new_album_input.setPlaceholderText("New album name...")
        self.new_album_input.returnPressed.connect(self._create_new_album)
        
        create_button = QPushButton("+")
        create_button.setFixedSize(30, 28)
        create_button.clicked.connect(self._create_new_album)
        create_button.setToolTip("Create new album")
        
        new_layout.addWidget(self.new_album_input)
        new_layout.addWidget(create_button)
        layout.addWidget(new_album_widget)
    
    def _on_album_selected(self, item):
        """Handle album selection."""
        if item:
            # Get the album_id from item data
            album_id = item.data(Qt.ItemDataRole.UserRole)
            self.album_selected(album_id)
    
    def _on_album_double_clicked(self, item):
        """Handle double-click to open album."""
        pass  # Could expand/collapse in tree view
    
    def _create_new_album(self):
        """Create a new album from input."""
        name = self.new_album_input.text().strip()
        
        if not name:
            return
        
        # Check for duplicates
        for album in self.albums:
            if album["name"].lower() == name.lower():
                QMessageBox.warning(self, "Duplicate Album", 
                                  f"An album named '{name}' already exists.")
                return
        
        # Emit signal for parent to handle creation
        self.album_selected.emit("new:" + name)
        
        self.new_album_input.clear()
    
    def set_albums(self, albums: list):
        """
        Update the album list display.
        
        Args:
            albums: List of album dictionaries with 'name', 'count', 'id'
        """
        self.albums = albums
        self.album_list.clear()
        
        for album in albums:
            item = QListWidgetItem(f"{album['name']} ({album.get('count', 0)})")
            item.setData(Qt.ItemDataRole.UserRole, album["id"])
            self.album_list.addItem(item)
    
    def add_album(self, album: dict):
        """Add a single album to the list."""
        if album not in self.albums:
            self.albums.append(album)
            self.set_albums(self.albums)
