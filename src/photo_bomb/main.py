"""
Application entry point for Photo Bomb.
"""

import argparse
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from photo_bomb import __app_name__, __version__
from photo_bomb.ui.main_window import MainWindow


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse a small set of CLI flags. Anything else is forwarded to Qt."""
    parser = argparse.ArgumentParser(
        prog="photo-bomb",
        description=f"{__app_name__} - organize your Photos library with vision models.",
        add_help=True,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{__app_name__} {__version__}",
    )
    # parse_known_args lets Qt-specific flags (e.g. -platform) pass through.
    args, _ = parser.parse_known_args(argv)
    return args


def main() -> None:
    """Main entry point for the application."""
    _parse_args(sys.argv[1:])

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationDisplayName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("PhotoBomb")
    app.setOrganizationDomain("photobomb.app")

    print(f"{__app_name__} v{__version__} starting...")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        try:
            QMessageBox.critical(
                None,
                "Critical Error",
                f"An unexpected error occurred:\n{str(e)}",
            )
        except Exception:
            pass
        sys.exit(1)
