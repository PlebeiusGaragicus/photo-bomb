"""
Main window with photo grid view and categorization UI.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QLabel, QPushButton, QStatusBar, QMenuBar, QMenu,
    QAction, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSlot

# Add parent directory to path for imports
import sys
sys.path.insert(0, "/Users/satoshi/Downloads/PLAN-MODE-TESTS/photo-boss")

from src.ui.photo_grid import PhotoGridWidget
from src.ui.category_badge import CategoryBadge
from src.ui.album_sidebar import AlbumSidebar


class MainWindow(QMainWindow):
    """Main application window with split-pane layout and photo grid."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Boss")
        self.resize(1200, 800)
        
        # Current selection
        self.selected_photo_id = None
        
        # Initialize components
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()
        
        # Apply layout
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.splitter)
        self.setCentralWidget(central)
    
    def show_api_settings(self):
        """Show the API settings dialog."""
        from src.ui.api_settings_dialog import APISettingsDialog
        dialog = APISettingsDialog(self)
        # TODO: Load current config values when implemented
        if dialog.exec() == dialog.DialogCode.Accepted:
            # TODO: Save config when implemented
            self.statusBar().showMessage("API settings saved")
    
    def _create_menu_bar(self):
        """Create application menu bar."""
        menubar = QMenuBar(self)
        
        # File menu
        file_menu = menubar.addMenu("&File")
        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self.show_api_settings)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        self.setMenuBar(menubar)
    
    def _create_central_widget(self):
        """Create the central split-pane widget with photo grid."""
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left sidebar - Album list (using album sidebar for better management)
        self.album_sidebar = QWidget()
        self._setup_album_list()
        
        # Right content area
        self.content_stack = QStackedWidget()
        
        # Photo grid view
        self.photo_grid = PhotoGridWidget()
        self.photo_grid.batch_requested.connect(self._load_photo_batch)
        self.photo_grid.photo_selected.connect(self._on_photo_selected)
        self.content_stack.addWidget(self.photo_grid)
        
        # Placeholder for single photo view
        self.single_view_label = QLabel("Select a photo to view")
        self.single_view_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.single_view_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                font-size: 18px;
                color: #666;
            }
        """)
        self.content_stack.addWidget(self.single_view_label)
        
        # Right side layout (sidebar + content)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Categorization toolbar
        categorize_bar = QWidget()
        categorize_layout = QHBoxLayout(categorize_bar)
        categorize_layout.setContentsMargins(10, 5, 10, 5)
        
        categorize_label = QLabel("Categorize:")
        self.memories_button = QPushButton("Memories")
        self.todo_button = QPushButton("Todo")
        self.research_button = QPushButton("Research")
        
        for btn in [self.memories_button, self.todo_button, self.research_button]:
            btn.clicked.connect(self._on_categorize_clicked)
        
        # Analyze button
        analyze_button = QPushButton("Analyze Selected Photos")
        analyze_button.clicked.connect(self._on_analyze_clicked)
        
        categorize_layout.addWidget(categorize_label)
        categorize_layout.addWidget(self.memories_button)
        categorize_layout.addWidget(self.todo_button)
        categorize_layout.addWidget(self.research_button)
        categorize_layout.addStretch()
        categorize_layout.addWidget(analyze_button)
        
        right_layout.addWidget(categorize_bar)
        right_layout.addWidget(self.content_stack)
        
        # Add widgets to splitter
        self.splitter.addWidget(self.album_sidebar)
        self.splitter.addWidget(right_widget)
        
        # Set initial sizes (30% albums, 70% content)
        self.splitter.setSizes([360, 840])
    
    def _setup_album_list(self):
        """Set up the album sidebar with basic list widget."""
        layout = QVBoxLayout(self.album_sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header_label = QLabel("Albums")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
            }
        """)
        layout.addWidget(header_label)
        
        self.album_list = QListWidget()
        self._populate_albums()
        self.album_list.currentItemChanged.connect(self._on_album_changed)
        layout.addWidget(self.album_list)
    
    def _populate_albums(self):
        """Populate album list with placeholder items."""
        albums = ["All Photos", "Favorites", "Recent", "Selfies"]
        for album in albums:
            item_text = f"{album}"
            self.album_list.addItem(item_text)
    
    def _on_album_changed(self, current, previous):
        """Handle album selection change."""
        if current:
            album_name = current.text()
            self.statusBar().showMessage(f"Viewing: {album_name}")
            # Load photos for this album
            self.photo_grid.load_photos(0, 100)
    
    def _load_photo_batch(self, offset: int, limit: int):
        """Load a batch of photos from the library."""
        from src.core.photos_library import get_photos_library
        
        library = get_photos_library()
        
        # Get current album
        current_item = self.album_list.currentItem()
        album_id = "all_photos"  # default
        
        if current_item:
            album_name = current_item.text()
            album_map = {
                "All Photos": "all_photos",
                "Favorites": "favorites", 
                "Recent": "recent",
                "Selfies": "selfies"
            }
            album_id = album_map.get(album_name, "all_photos")
        
        photos = library.get_photos_for_album(album_id, offset, limit)
        
        # Clear and repopulate grid
        self.photo_grid.clear()
        for photo in photos:
            self.photo_grid.add_photo_item(photo["identifier"], photo["filename"])
    
    def _on_photo_selected(self, photo_id: str):
        """Handle photo selection."""
        self.selected_photo_id = photo_id
        
        # Show single photo view with categorization
        self.content_stack.setCurrentIndex(1)
        
        # Update toolbar state
        self.memories_button.setEnabled(True)
        self.todo_button.setEnabled(True)
        self.research_button.setEnabled(True)
        
        self.statusBar().showMessage(f"Selected: {photo_id}")
    
    def _on_categorize_clicked(self):
        """Handle category button click."""
        if not self.selected_photo_id:
            return
        
        sender = self.sender()
        category = ""
        
        if sender == self.memories_button:
            category = "memories"
        elif sender == self.todo_button:
            category = "todo"
        elif sender == self.research_button:
            category = "research"
        
        # Update photo category
        badge = CategoryBadge(category)
        self.statusBar().showMessage(f"Photo categorized as: {category}")
    
    def _on_analyze_clicked(self):
        """Handle analyze button click."""
        from src.ui.batch_analysis_dialog import BatchAnalysisDialog
        from src.core.api_client import VisionAPIClient
        from src.core.photos_library import get_photos_library
        from src.core.config import get_config
        
        config = get_config()
        
        # Check if API is configured
        if not config.api_endpoint or not config.api_key:
            self.statusBar().showMessage("Error: API not configured. Please set up API settings first.")
            return
        
        # Get selected photos (simplified - would get actual selection in real implementation)
        library = get_photos_library()
        current_item = self.album_list.currentItem()
        album_name = current_item.text() if current_item else "All Photos"
        
        # For demo, just analyze some placeholder photos
        photo_ids = ["photo_1", "photo_2", "photo_3"]  # Would get actual selection
        
        dialog = BatchAnalysisDialog(self)
        dialog.show()
