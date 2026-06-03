"""Header bar matching the source HTML title area."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class HeaderBar(QFrame):
    """Top brand area with window-style controls and settings button."""

    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()
    settings_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("HeaderBar")
        self._build_ui()

    user_requested = Signal()

    def _build_ui(self) -> None:
        """Create logo, title, subtitle, and action controls."""
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 12)
        root.setSpacing(8)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        logo = QLabel("✦")
        logo.setObjectName("LogoIcon")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        user_btn = QPushButton()
        user_btn.setObjectName("UserButton")
        user_btn.setFixedSize(36, 36)
        user_btn.clicked.connect(self.user_requested.emit)

        title = QLabel("AI 办公助手 · J-Mate")
        title.setObjectName("AppTitle")

        badge = QLabel("桌面智能版")
        badge.setObjectName("Badge")

        title_row.addWidget(logo)
        title_row.addWidget(user_btn)
        title_row.addWidget(title)
        title_row.addWidget(badge)
        title_row.addStretch(1)
        title_row.addWidget(self._icon_button("−", "最小化", self.minimize_requested))
        title_row.addWidget(self._icon_button("□", "窗口缩放", self.maximize_requested))
        title_row.addWidget(self._icon_button("×", "关闭", self.close_requested, close=True))

        sub_row = QHBoxLayout()
        sub_row.setSpacing(16)
        for item in ("⚡ 自然语言指令", "🎯 一键选择 Skills", "💬 高效办公流"):
            label = QLabel(item)
            label.setObjectName("SubText")
            sub_row.addWidget(label)
        sub_row.addStretch(1)
        sub_row.addWidget(self._settings_button())

        root.addLayout(title_row)
        root.addLayout(sub_row)

    def _settings_button(self) -> QPushButton:
        """Create the gear button used to open settings."""
        button = QPushButton("...")
        button.setObjectName("SettingsButton")
        button.setToolTip("打开设置")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(self.settings_requested.emit)
        return button

    @staticmethod
    def _icon_button(text: str, tooltip: str, signal: Signal, close: bool = False) -> QPushButton:
        """Create one window control button."""
        button = QPushButton(text)
        button.setObjectName("CloseWindowButton" if close else "WindowButton")
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(signal.emit)
        return button
