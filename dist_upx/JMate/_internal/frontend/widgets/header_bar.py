"""顶部栏"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Signal, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.constants import HEADER_BADGE, HEADER_SUBTITLES, HEADER_TITLE


class LogoIcon(QFrame):
    """绘制与 HTML 设计稿一致的 J-Mate 标题图标。"""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("LogoIcon")
        self.setFixedSize(36, 36)

    def paintEvent(self, event) -> None:
        """绘制蓝色圆角底和白色星芒图标，避免系统字体差异导致 logo 变形。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1E6DFF"))
        painter.drawRoundedRect(rect, 14, 14)

        pen = QPen(QColor("#ffffff"), 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        center = QPointF(18, 18)
        rays = (
            (QPointF(18, 5), QPointF(18, 10)),
            (QPointF(18, 26), QPointF(18, 31)),
            (QPointF(5, 18), QPointF(10, 18)),
            (QPointF(26, 18), QPointF(31, 18)),
            (QPointF(9, 9), QPointF(12.5, 12.5)),
            (QPointF(23.5, 23.5), QPointF(27, 27)),
            (QPointF(9, 27), QPointF(12.5, 23.5)),
            (QPointF(23.5, 12.5), QPointF(27, 9)),
        )
        for start, end in rays:
            painter.drawLine(start, end)
        painter.drawEllipse(center, 3, 3)


class HeaderBar(QFrame):
    """Top brand area with window-style controls and settings button."""

    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()
    settings_requested = Signal()
    skills_enabled_changed = Signal(bool)

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

        logo = LogoIcon()

        user_btn = QPushButton()
        user_btn.setObjectName("UserButton")
        user_btn.setFixedSize(36, 36)
        user_btn.clicked.connect(self.user_requested.emit)

        title = QLabel(HEADER_TITLE)
        title.setObjectName("AppTitle")

        badge = QLabel(HEADER_BADGE)
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
        for item in HEADER_SUBTITLES:
            label = QLabel(item)
            label.setObjectName("SubText")
            sub_row.addWidget(label)
        sub_row.addStretch(1)
        self.skills_toggle = QCheckBox("启用 Skills")
        self.skills_toggle.setObjectName("SkillsMasterToggle")
        self.skills_toggle.setChecked(True)
        self.skills_toggle.setFixedHeight(23)
        self.skills_toggle.toggled.connect(self.skills_enabled_changed.emit)
        sub_row.addWidget(self.skills_toggle)
        sub_row.addWidget(self._settings_button())

        root.addLayout(title_row)
        root.addLayout(sub_row)

    def set_skills_enabled(self, enabled: bool) -> None:
        """Update the header skills switch without re-emitting toggled."""
        self.skills_toggle.blockSignals(True)
        self.skills_toggle.setChecked(enabled)
        self.skills_toggle.blockSignals(False)

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
