"""Small popup shown at bottom-right when user clicks avatar and is logged in."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

from app.state import AppState


class UserPopup(QWidget):
    def __init__(self, state: AppState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self.setObjectName("UserPopup")
        # Use dialog-like frameless window (opaque) so QSS background fills the popup.
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        # Do not set WA_TranslucentBackground — keep background opaque for Settings-like look
        try:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        except Exception:
            pass
        self._build_ui()
        self._apply_state()
        self.state.user_name_changed.connect(lambda v: self._apply_state())
        self.state.theme_changed.connect(lambda v: self.setProperty("theme", v))
        self.setFixedSize(240, 120)
        self.setProperty("theme", self.state.theme)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self.label = QLabel()
        self.logout = QPushButton("退出登录")
        self.logout.clicked.connect(self._logout)
        layout.addWidget(self.label)
        layout.addWidget(self.logout)

    def _apply_state(self) -> None:
        name = self.state.user_name or "未登录"
        self.label.setText(f"用户：{name}")

    def _logout(self) -> None:
        self.state.logged_in = False
        self.state.user_name = None
        self.hide()

    def focusOutEvent(self, event) -> None:
        # hide when focus is lost (click outside)
        self.hide()
        super().focusOutEvent(event)
