"""Entry point for the J-Mate PySide6 desktop frontend."""

from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.theme import apply_theme


def main() -> int:
    """Create the Qt application and show the main window."""
    app = QApplication(sys.argv)
    app.setApplicationName("J-Mate")
    app.setOrganizationName("J-Mate Desktop")

    base_font = QFont("Microsoft YaHei")
    base_font.setPointSize(10)
    app.setFont(base_font)

    apply_theme(app)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
