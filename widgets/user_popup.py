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
        self.setWindowFlags(Qt.WindowType.Widget)
        # Do not set WA_TranslucentBackground — keep background opaque for Settings-like look
        try:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        except Exception:
            pass
        self._build_ui()
        self._apply_state()
        self.state.user_name_changed.connect(lambda v: self._apply_state())
        self.state.theme_changed.connect(self._apply_theme)
        self.setFixedSize(240, 120)
        self._apply_theme(self.state.theme)

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

    def _apply_theme(self, theme: str) -> None:
        """Keep the user popup visually aligned with the login dialog."""
        self.setProperty("theme", theme)
        if theme == "dark":
            popup_bg = "rgba(19,29,47,0.96)"
            border = "rgba(85,120,177,0.34)"
            text_color = "#d9e7ff"
            button_bg = "rgba(25,39,63,0.96)"
            button_border = "rgba(85,120,177,0.42)"
        else:
            popup_bg = "#ffffff"
            border = "#d4e3fb"
            text_color = "#12283b"
            button_bg = "#ffffff"
            button_border = "#e5e7eb"

        self.setStyleSheet(f"""
        QWidget#UserPopup {{
            background: {popup_bg};
            border: 1px solid {border};
            border-radius: 10px;
        }}
        QWidget#UserPopup QLabel {{
            color: {text_color};
            background: transparent;
            border: none;
        }}
        QWidget#UserPopup QPushButton {{
            background: {button_bg};
            color: {text_color};
            border: 1px solid {button_border};
            border-radius: 4px;
            padding: 4px 10px;
        }}
        """)
        self.style().unpolish(self)
        self.style().polish(self)

    def _logout(self) -> None:
        self.state.logged_in = False
        self.state.user_name = None
        self.hide()

    def focusOutEvent(self, event) -> None:
        # hide when focus is lost (click outside)
        self.hide()
        super().focusOutEvent(event)
