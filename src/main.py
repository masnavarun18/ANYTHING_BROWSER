"""
ANYTHING BROWSER - Main Desktop Entry Point
"""

import sys
import os

# Ensure src module resolution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from src.browser_window import BrowserMainWindow


def main():
    """
    Main application entry point.
    """
    # Enable High DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("ANYTHING BROWSER")
    app.setOrganizationName("AnythingBrowser")

    window = BrowserMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
