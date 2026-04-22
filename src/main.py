"""
Application entry point for Photo Boss.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.main_window import MainWindow


def main():
    """Main entry point for the application."""
    # Create QApplication before any other Qt objects
    app = QApplication(sys.argv)
    app.setApplicationName("Photo Boss")
    app.setOrganizationName("PhotoBoss")
    
    # Show welcome message
    print(f"Photo Boss v0.1.0 starting...")
    print(f"Configuration directory: {app.applicationDirPath()}")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        QMessageBox.critical(None, "Critical Error", 
                           f"An unexpected error occurred:\n{str(e)}")
        sys.exit(1)
