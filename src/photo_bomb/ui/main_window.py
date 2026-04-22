"""
Main window: album sidebar + photo grid + Memories/Todo/Research toolbar.

Categorization is implemented by moving the selected `PHAsset` into a
matching Apple Photos album (auto-created on first use). Apple Photos is the
sole source of truth - this app does not maintain a sidecar database.
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from photo_bomb.core.config import get_config
from photo_bomb.core.photos_library import get_photos_library
from photo_bomb.ui.album_sidebar import AlbumSidebar
from photo_bomb.ui.api_settings_dialog import APISettingsDialog
from photo_bomb.ui.photo_grid import PhotoGridWidget


# Button label -> Photos album name. Albums are created on first use; the
# label and the album name are intentionally identical so users can find
# them in Apple Photos without translation.
_CATEGORY_ALBUMS = {
    "Memories": "Memories",
    "Todo": "Todo",
    "Research": "Research",
}


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Photo Bomb")
        self.resize(1200, 800)

        self.selected_photo_id: Optional[str] = None
        self.current_album_id: Optional[str] = None

        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.splitter)
        self.setCentralWidget(central)

        self._bootstrap_library()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _create_status_bar(self) -> None:
        status = QStatusBar(self)
        status.showMessage("Ready")
        self.setStatusBar(status)

    def _create_menu_bar(self) -> None:
        menubar = QMenuBar(self)

        file_menu = menubar.addMenu("&File")
        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self.show_api_settings)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        menubar.addMenu("&Edit")
        menubar.addMenu("&View")
        menubar.addMenu("&Help")

        self.setMenuBar(menubar)

    def _create_central_widget(self) -> None:
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.album_sidebar = AlbumSidebar()
        self.album_sidebar.album_selected.connect(self._on_album_changed)
        self.album_sidebar.create_album_requested.connect(self._on_create_album)

        self.content_stack = QStackedWidget()

        self.photo_grid = PhotoGridWidget()
        self.photo_grid.batch_requested.connect(self._load_photo_batch)
        self.photo_grid.photo_selected.connect(self._on_photo_selected)
        self.content_stack.addWidget(self.photo_grid)

        self.single_view_label = QLabel("Select a photo to view")
        self.single_view_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.single_view_label.setStyleSheet(
            """
            QLabel {
                background-color: #f0f0f0;
                font-size: 18px;
                color: #666;
            }
            """
        )
        self.content_stack.addWidget(self.single_view_label)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        categorize_bar = QWidget()
        categorize_layout = QHBoxLayout(categorize_bar)
        categorize_layout.setContentsMargins(10, 5, 10, 5)

        categorize_label = QLabel("Move selected photo to:")
        self.memories_button = QPushButton("Memories")
        self.todo_button = QPushButton("Todo")
        self.research_button = QPushButton("Research")

        for btn in (self.memories_button, self.todo_button, self.research_button):
            btn.clicked.connect(self._on_categorize_clicked)
            btn.setEnabled(False)

        categorize_layout.addWidget(categorize_label)
        categorize_layout.addWidget(self.memories_button)
        categorize_layout.addWidget(self.todo_button)
        categorize_layout.addWidget(self.research_button)
        categorize_layout.addStretch()

        right_layout.addWidget(categorize_bar)
        right_layout.addWidget(self.content_stack)

        self.splitter.addWidget(self.album_sidebar)
        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([360, 840])

    # ------------------------------------------------------------------
    # Library bootstrap + album population
    # ------------------------------------------------------------------

    def _bootstrap_library(self) -> None:
        library = get_photos_library()
        if not library.is_available:
            self.statusBar().showMessage(
                "Photos library not available on this platform - showing sample data."
            )
            self._refresh_albums()
            return

        status = library.request_authorization()
        if library.is_authorized:
            self._refresh_albums()
            self.statusBar().showMessage("Photos library connected.")
        else:
            self.statusBar().showMessage(
                f"Photos access not granted (status: {status}). "
                "Grant access in System Settings > Privacy & Security > Photos."
            )

    def _refresh_albums(self) -> None:
        albums = get_photos_library().get_albums()
        self.album_sidebar.set_albums(albums)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_album_changed(self, identifier: str) -> None:
        self.current_album_id = identifier
        name = next(
            (a["name"] for a in self.album_sidebar.albums if a["identifier"] == identifier),
            identifier,
        )
        self.statusBar().showMessage(f"Viewing: {name}")
        self.content_stack.setCurrentIndex(0)
        self.photo_grid.load_photos(0, self.photo_grid.batch_size)

    def _on_create_album(self, name: str) -> None:
        library = get_photos_library()
        album = library.create_album(name)
        if album is None:
            self.statusBar().showMessage(f"Failed to create album '{name}'.")
            return
        self._refresh_albums()
        self.statusBar().showMessage(f"Created album '{name}'.")

    def _load_photo_batch(self, offset: int, limit: int) -> None:
        if not self.current_album_id:
            self.photo_grid.clear()
            return

        library = get_photos_library()
        photos = library.get_photos_for_album(
            self.current_album_id, offset, limit
        )
        total = next(
            (a.get("count", 0) for a in self.album_sidebar.albums
             if a["identifier"] == self.current_album_id),
            0,
        )

        self.photo_grid.clear()
        self.photo_grid.set_total_count(total)
        for photo in photos:
            self.photo_grid.add_photo_item(
                photo["identifier"],
                photo.get("filename", ""),
                photo.get("thumbnail_path"),
            )

    def _on_photo_selected(self, photo_id: str) -> None:
        self.selected_photo_id = photo_id
        self.content_stack.setCurrentIndex(0)

        for btn in (self.memories_button, self.todo_button, self.research_button):
            btn.setEnabled(True)

        self.statusBar().showMessage(f"Selected: {photo_id}")

    def _on_categorize_clicked(self) -> None:
        if not self.selected_photo_id:
            return

        sender = self.sender()
        button_label = sender.text() if hasattr(sender, "text") else ""
        category = _CATEGORY_ALBUMS.get(button_label)
        if category is None:
            return

        library = get_photos_library()
        album = library.find_or_create_album(category)
        if album is None:
            self.statusBar().showMessage(
                f"Could not open or create '{category}' album."
            )
            return

        if not library.add_photos_to_album(
            [self.selected_photo_id], album["identifier"]
        ):
            self.statusBar().showMessage(
                f"Failed to add photo to '{category}'."
            )
            return

        self._refresh_albums()
        self.statusBar().showMessage(f"Moved to {category}.")

    # ------------------------------------------------------------------
    # Settings dialog
    # ------------------------------------------------------------------

    def show_api_settings(self) -> None:
        config = get_config()
        dialog = APISettingsDialog(self)
        dialog.load_settings(config.config)
        if dialog.exec() == dialog.DialogCode.Accepted:
            dialog.save_to_config(config)
            self.statusBar().showMessage("API settings saved.")
