"""
Category/tag badges for photo categorization.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal


class CategoryBadge(QFrame):
    """
    Visual badge for showing photo category/timestamp.
    Color-coded for different categories.
    """
    
    category_changed = pyqtSignal(str)  # new_category
    
    COLORS = {
        "memories": {"bg": "#4CAF50", "text": "#FFFFFF"},
        "todo": {"bg": "#FF9800", "text": "#FFFFFF"},
        "research": {"bg": "#2196F3", "text": "#FFFFFF"}
    }
    
    def __init__(self, category: str = None, parent=None):
        super().__init__(parent)
        self.category = category or "memories"
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the badge UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Category label
        self.label = QLabel(self.category.capitalize())
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS[self.category]['text']};
                font-weight: bold;
                background-color: {self.COLORS[self.category]['bg']};
                padding: 4px 8px;
                border-radius: 12px;
            }}
        """)
        layout.addWidget(self.label)
        
        # Category change button (popup menu in full implementation)
        self.change_button = QPushButton("▼")
        self.change_button.setFixedSize(20, 20)
        self.change_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
            }
        """)
        layout.addWidget(self.change_button)
    
    def set_category(self, category: str):
        """Update the badge category."""
        if category in self.COLORS:
            self.category = category
            self.label.setText(category.capitalize())
            self.label.setStyleSheet(f"""
                QLabel {{
                    color: {self.COLORS[category]['text']};
                    font-weight: bold;
                    background-color: {self.COLORS[category]['bg']};
                    padding: 4px 8px;
                    border-radius: 12px;
                }}
            """)
