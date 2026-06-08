"""登录结果反馈弹窗。

这个弹窗只负责展示登录成功或登录失败的结果，不处理认证逻辑。
LoginDialog 调用 AuthService 得到结果后，再用这个弹窗给用户一个明确反馈。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

from app.state import AppState
from app.theme_tokens import LOGIN_FEEDBACK_DIALOG_SIZE, tokens_for_theme


class LoginFeedbackDialog(QDialog):
    """登录成功/失败的轻量反馈界面。"""

    def __init__(
        self,
        state: AppState,
        title: str,
        message: str,
        success: bool,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.success = success
        self.setObjectName("LoginFeedbackDialog")
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(*LOGIN_FEEDBACK_DIALOG_SIZE)
        self.setProperty("theme", self.state.theme)
        self.state.theme_changed.connect(self._apply_theme)

        self._build_ui(title, message)
        self._apply_theme(self.state.theme)

    def _build_ui(self, title: str, message: str) -> None:
        """创建结果图标、标题、说明和确认按钮。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(12)

        icon = QLabel("✓" if self.success else "!")
        icon.setObjectName("LoginFeedbackIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setObjectName("LoginFeedbackTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        message_label = QLabel(message)
        message_label.setObjectName("LoginFeedbackMessage")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)

        ok_button = QPushButton("确定")
        ok_button.setObjectName("LoginFeedbackButton")
        ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_button.clicked.connect(self.accept)

        layout.addWidget(icon)
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        layout.addStretch(1)
        layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def _apply_theme(self, theme: str) -> None:
        """根据当前主题刷新反馈弹窗颜色。"""
        token = tokens_for_theme(theme).login_dialog
        accent = "#16a34a" if self.success else token.error

        self.setStyleSheet(f"""
        QDialog#LoginFeedbackDialog {{
            background: {token.background};
            border-radius: 14px;
        }}
        QLabel#LoginFeedbackIcon {{
            color: {accent};
            font-size: 30px;
            font-weight: 800;
        }}
        QLabel#LoginFeedbackTitle {{
            color: {token.title};
            font-size: 18px;
            font-weight: 700;
        }}
        QLabel#LoginFeedbackMessage {{
            color: {token.text};
            font-size: 13px;
        }}
        QPushButton#LoginFeedbackButton {{
            background: #246bfe;
            color: #ffffff;
            border: none;
            border-radius: 16px;
            min-width: 86px;
            min-height: 32px;
            font-weight: 600;
        }}
        QPushButton#LoginFeedbackButton:hover {{
            background: #1d5ee8;
        }}
        """)

