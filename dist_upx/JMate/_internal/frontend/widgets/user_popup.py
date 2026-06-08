"""用户信息弹窗。

用户登录后点击左下角入口会显示这个弹窗，用于展示当前用户和退出登录。
它是主窗口子控件，不是独立窗口，因此位置和主题都由主窗口状态控制。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

from app.state import AppState
from app.theme_tokens import USER_POPUP_BASE_SIZE, tokens_for_theme


class UserPopup(QWidget):
    """登录后的用户信息面板。"""

    def __init__(self, state: AppState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self.setObjectName("UserPopup")
        # 作为主窗口子控件显示，避免独立 Tool 窗口带来的定位和透明背景问题。
        self.setWindowFlags(Qt.WindowType.Widget)
        try:
            # 保持不透明背景，让 QSS 背景完整填充圆角区域。
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        except Exception:
            pass
        self._build_ui()
        self._apply_state()
        self.state.user_name_changed.connect(lambda v: self._apply_state())
        self.state.theme_changed.connect(self._apply_theme)
        self.setFixedSize(*USER_POPUP_BASE_SIZE)
        self._apply_theme(self.state.theme)

    def _build_ui(self) -> None:
        """创建用户名称和退出登录按钮。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self.label = QLabel()
        self.logout = QPushButton("退出登录")
        self.logout.clicked.connect(self._logout)
        layout.addWidget(self.label)
        layout.addWidget(self.logout)

    def _apply_state(self) -> None:
        """根据当前登录状态刷新用户名称。"""
        name = self.state.user_name or "未登录"
        self.label.setText(f"用户：{name}")

    def _apply_theme(self, theme: str) -> None:
        """根据当前主题刷新弹窗颜色。"""
        self.setProperty("theme", theme)
        token = tokens_for_theme(theme).user_popup

        self.setStyleSheet(f"""
        QWidget#UserPopup {{
            background: {token.background};
            border: 1px solid {token.border};
            border-radius: 10px;
        }}
        QWidget#UserPopup QLabel {{
            color: {token.text};
            background: transparent;
            border: none;
        }}
        QWidget#UserPopup QPushButton {{
            background: {token.button_background};
            color: {token.text};
            border: 1px solid {token.button_border};
            border-radius: 4px;
            padding: 4px 10px;
        }}
        """)
        self.style().unpolish(self)
        self.style().polish(self)

    def _logout(self) -> None:
        """清空前端登录状态并关闭用户弹窗。"""
        self.state.logged_in = False
        self.state.user_name = None
        self.hide()

    def focusOutEvent(self, event) -> None:
        """点击弹窗外部时隐藏弹窗。"""
        self.hide()
        super().focusOutEvent(event)
