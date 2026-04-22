"""
Album sidebar widget: lists Photos albums and lets the user create new ones.

The sidebar is purely presentational - it emits signals and the parent
(`MainWindow`) is responsible for talking to `PhotosLibrary`. Album dicts
follow the `PhotosLibrary.get_albums()` shape:
`{"name": str, "count": int, "identifier": str}`.
"""

from typing import List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AlbumSidebar(QWidget):
    """Sidebar widget for browsing and creating Photos albums."""

    album_selected = pyqtSignal(str)  # PHAssetCollection.localIdentifier
    create_album_requested = pyqtSignal(str)  # user-supplied album name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.albums: List[dict] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header_label = QLabel("Albums")
        header_label.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
            }
            """
        )
        layout.addWidget(header_label)

        self.album_list = QListWidget()
        self.album_list.itemClicked.connect(self._on_album_clicked)
        layout.addWidget(self.album_list)

        new_album_widget = QWidget()
        new_layout = QHBoxLayout(new_album_widget)
        new_layout.setContentsMargins(5, 5, 5, 5)

        self.new_album_input = QLineEdit()
        self.new_album_input.setPlaceholderText("New album name...")
        self.new_album_input.returnPressed.connect(self._emit_create)

        create_button = QPushButton("+")
        create_button.setFixedSize(30, 28)
        create_button.clicked.connect(self._emit_create)
        create_button.setToolTip("Create new album")

        new_layout.addWidget(self.new_album_input)
        new_layout.addWidget(create_button)
        layout.addWidget(new_album_widget)

    def set_albums(self, albums: List[dict]) -> None:
        """Replace the displayed album list."""
        self.albums = list(albums)
        self.album_list.clear()
        for album in self.albums:
            item = QListWidgetItem(
                f"{album['name']} ({album.get('count', 0)})"
            )
            item.setData(Qt.ItemDataRole.UserRole, album["identifier"])
            self.album_list.addItem(item)

    def _on_album_clicked(self, item: QListWidgetItem) -> None:
        identifier = item.data(Qt.ItemDataRole.UserRole)
        if identifier:
            self.album_selected.emit(str(identifier))

    def _emit_create(self) -> None:
        name = self.new_album_input.text().strip()
        if not name:
            return
        self.new_album_input.clear()
        self.create_album_requested.emit(name)
