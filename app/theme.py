"""QSS theme loading."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from utils.paths import resource_path


def apply_theme(app: QApplication) -> None:
    """Apply the main application stylesheet."""
    qss_file = resource_path("styles", "app.qss")
    if qss_file.exists():
        app.setStyleSheet(qss_file.read_text(encoding="utf-8"))
