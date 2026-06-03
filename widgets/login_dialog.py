"""Simple login dialog (frontend-only).

If user submits, it sets `state.logged_in = True` and `state.user_name`.
This is a stub — replace with real authentication later.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QLabel, QVBoxLayout

from app.state import AppState


class LoginDialog(QDialog):
    def __init__(self, state: AppState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self.setWindowTitle("登录")
        self.setObjectName("LoginDialog")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(440, 260)
        # theme binding
        self.setProperty("theme", self.state.theme)
        self.state.theme_changed.connect(lambda v: self.setProperty("theme", v))
        self.state.theme_changed.connect(self._apply_theme)
        # apply initial theme
        self._apply_theme(self.state.theme)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # top title and close button (reuse CloseSettingsButton QSS)
        from PySide6.QtWidgets import QHBoxLayout, QPushButton

        top = QHBoxLayout()
        title = QLabel("登录")
        title.setObjectName("LoginTitle")
        close_button = QPushButton("关闭")
        close_button.setObjectName("CloseSettingsButton")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.reject)
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(close_button)
        layout.addLayout(top)
        form = QFormLayout()
        self.username = QLineEdit()
        self.username.setPlaceholderText("用户名")
        self.password = QLineEdit()
        self.password.setPlaceholderText("密码")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow(QLabel("用户名"), self.username)
        form.addRow(QLabel("密码"), self.password)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._do_login)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def _do_login(self) -> None:
        # stub: accept any non-empty username
        name = self.username.text().strip()
        if not name:
            return
        self.state.user_name = name
        self.state.logged_in = True
        self.accept()

    def _apply_theme(self, theme: str) -> None:
        """Apply compact theme QSS for the login dialog."""
        if theme == "dark":
            dialog_bg = "rgba(19,29,47,0.96)"
            title_color = "#d9e7ff"
            text_color = "#d9e7ff"
        else:
            dialog_bg = "#ffffff"
            title_color = "#174381"
            text_color = "#12283b"

        qss = f"""
        QDialog#LoginDialog {{
            background: {dialog_bg};
        }}
        QLabel#LoginTitle {{
            color: {title_color};
            font-size: 16px;
            font-weight: 600;
        }}
        QLineEdit {{
            color: {text_color};
        }}
        """
        self.setStyleSheet(qss)

    def keyPressEvent(self, event) -> None:
        # allow Esc to close the dialog
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
