"""
Photo grid view for displaying photos with prev/next pagination.

The grid is purely presentational: it emits `batch_requested` and
`photo_selected` and the parent (`MainWindow`) is responsible for fetching
photos and feeding them back via `add_photo_item`.
"""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


_GRID_COLUMNS = 4
_THUMB_PIXELS = 200


class PhotoGridWidget(QFrame):
    """Grid of photo thumbnails with prev/next pagination controls."""

    photo_selected = pyqtSignal(str)  # photo_id
    batch_requested = pyqtSignal(int, int)  # offset, limit

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PhotoGridWidget")
        self.current_offset = 0
        self.batch_size = 100
        self.total_count = 0
        self._next_index = 0
        self._loaded_count = 0

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)

        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area)

        pagination_widget = QWidget()
        pagination_layout = QHBoxLayout(pagination_widget)
        pagination_layout.setContentsMargins(5, 5, 5, 5)

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(lambda: self._navigate(-1))
        self.prev_button.setEnabled(False)

        self.page_label = QLabel("No photos loaded")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(lambda: self._navigate(1))

        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)

        layout.addWidget(pagination_widget)

    def _navigate(self, direction: int) -> None:
        if direction < 0 and self.current_offset > 0:
            new_offset = max(0, self.current_offset - self.batch_size)
            self.load_photos(new_offset, self.batch_size)
        elif direction > 0:
            new_offset = self.current_offset + self.batch_size
            if self.total_count == 0 or new_offset < self.total_count:
                self.load_photos(new_offset, self.batch_size)

    def load_photos(self, offset: int = 0, limit: int = 100) -> None:
        """Request the parent to populate `[offset, offset+limit)` photos."""
        limit = min(limit, self.batch_size)
        self.current_offset = offset
        self.batch_requested.emit(offset, limit)

    def set_total_count(self, total: int) -> None:
        """Inform the grid of the underlying album size for paginator math."""
        self.total_count = total
        self._update_pagination()

    def add_photo_item(
        self,
        photo_id: str,
        filename: str,
        thumbnail_path: Optional[str] = None,
    ) -> None:
        """Append a single thumbnail tile to the grid."""
        idx = self._next_index
        self._next_index += 1
        self._loaded_count += 1

        item_widget = QWidget()
        item_layout = QVBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 5, 5, 5)

        thumb_label = QLabel()
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setFixedSize(_THUMB_PIXELS, _THUMB_PIXELS)
        thumb_label.setStyleSheet(
            """
            QLabel {
                background-color: #e0e0e0;
                border: 2px solid #cccccc;
                border-radius: 5px;
            }
            """
        )

        pixmap = QPixmap(thumbnail_path) if thumbnail_path else QPixmap()
        if not pixmap.isNull():
            thumb_label.setPixmap(
                pixmap.scaled(
                    _THUMB_PIXELS,
                    _THUMB_PIXELS,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            thumb_label.setText(filename or photo_id)

        thumb_label.setCursor(Qt.CursorShape.PointingHandCursor)
        thumb_label.mousePressEvent = lambda _e, pid=photo_id: self.photo_selected.emit(pid)

        info_label = QLabel(filename)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("QLabel { font-size: 10px; color: #666; }")

        item_layout.addWidget(thumb_label)
        item_layout.addWidget(info_label)

        self.grid_layout.addWidget(
            item_widget, idx // _GRID_COLUMNS, idx % _GRID_COLUMNS
        )
        self._update_pagination()

    def clear(self) -> None:
        """Remove every tile and reset the per-page counters."""
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child is not None and child.widget() is not None:
                child.widget().deleteLater()
        self._next_index = 0
        self._loaded_count = 0
        self._update_pagination()

    def _update_pagination(self) -> None:
        if self.total_count <= 0 and self._loaded_count <= 0:
            self.page_label.setText("No photos")
        else:
            start = self.current_offset + (1 if self._loaded_count else 0)
            end = self.current_offset + self._loaded_count
            total_str = (
                str(self.total_count) if self.total_count > 0 else f"{end}+"
            )
            self.page_label.setText(f"Photos {start}-{end} of {total_str}")

        self.prev_button.setEnabled(self.current_offset > 0)
        if self.total_count > 0:
            self.next_button.setEnabled(
                self.current_offset + self.batch_size < self.total_count
            )
        else:
            self.next_button.setEnabled(self._loaded_count >= self.batch_size)
