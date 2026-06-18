"""Main window that recreates the HTML app container layout."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QStackedLayout, QVBoxLayout, QWidget, QPushButton

from app.constants import FOOTER_TEXT, WINDOW_TITLE
from app.state import AppState
from app.theme_tokens import (
    FONT_POINT_SIZES,
    USER_POPUP_BASE_SIZE,
    USER_POPUP_MAX_SIZE,
    USER_POPUP_MIN_SIZE,
    WINDOW_INITIAL_SIZE,
    WINDOW_MINIMUM_SIZE,
    tokens_for_theme,
)
from views.chat_view import ChatView
from widgets.header_bar import HeaderBar
from widgets.settings_dialog import SettingsDialog
from widgets.login_dialog import LoginDialog
from widgets.user_popup import UserPopup


class MainWindow(QMainWindow):
    """Top-level J-Mate desktop window."""

    def __init__(self) -> None:
        super().__init__()
        self.state = AppState()

        self.setWindowTitle(WINDOW_TITLE)
        self.resize(*WINDOW_INITIAL_SIZE)
        self.setMinimumSize(*WINDOW_MINIMUM_SIZE)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._drag_position: QPoint | None = None
        self._load_attendance_config_on_startup()

        self.header = HeaderBar()
        self.chat_view = ChatView(self.state)
        self.user_popup: UserPopup | None = None
        self.app_card = self._create_app_card()
        self.root = QWidget()
        # bottom-left login anchor button
        from PySide6.QtWidgets import QPushButton

        self.login_anchor = QPushButton("", self)
        self.login_anchor.setObjectName("LoginAnchor")
        # circular avatar button — size computed dynamically in _position_anchors
        self.login_anchor.setFixedSize(self.state.anchor_min_size, self.state.anchor_min_size)
        self.login_anchor.clicked.connect(self._handle_user_request)
        self.login_anchor.setProperty("theme", self.state.theme)
        self.state.theme_changed.connect(self._apply_login_anchor_theme)
        # update anchor display when login state or user name changes
        self.state.user_name_changed.connect(lambda v: self._update_login_anchor())
        self.state.logged_in_changed.connect(lambda v: self._update_login_anchor())
        self._update_login_anchor()
        # react when anchor sizing config changes
        self.state.anchor_config_changed.connect(self._position_anchors)

        self.root_stack = QStackedLayout()
        self.root_stack.setContentsMargins(0, 0, 0, 0)
        self.root_stack.addWidget(self.app_card)

        self.root.setObjectName("Root")
        self.root.setLayout(self.root_stack)
        self.setCentralWidget(self.root)

        self._connect_signals()
        # React to state changes so views update automatically.
        self.state.theme_changed.connect(self.apply_visual_settings)
        self.state.font_size_changed.connect(self.apply_visual_settings)
        self.state.enter_to_send_changed.connect(self.chat_view.refresh_from_state)
        self.state.skills_enabled_changed.connect(self.header.set_skills_enabled)
        self.state.skills_enabled_changed.connect(self.chat_view.refresh_from_state)
        self.state.enabled_skill_ids_changed.connect(self.chat_view.refresh_from_state)
        self.state.active_skill_changed.connect(self.chat_view.refresh_from_state)
        self.apply_visual_settings()
        QTimer.singleShot(0, self._show_initial_login)

    def _create_app_card(self) -> QWidget:
        """Build the glass-like main app container."""
        card = QWidget()
        card.setObjectName("AppContainer")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.chat_view, stretch=1)

        footer = QLabel(FOOTER_TEXT)
        footer.setObjectName("Footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
        return card

    def _connect_signals(self) -> None:
        """Wire header buttons to frontend-only window interactions."""
        self.header.settings_requested.connect(self._open_settings)
        self.header.skills_enabled_changed.connect(self._set_skills_enabled)
        self.header.user_requested.connect(self._handle_user_request)
        self.header.minimize_requested.connect(self._toggle_content_minimized)
        self.header.maximize_requested.connect(self._toggle_maximized)
        self.header.close_requested.connect(QApplication.quit)

        # hide header user button if present (we use bottom-left anchor)
        btn = self.header.findChild(QPushButton, "UserButton")
        if btn:
            btn.hide()
        # position anchor
        self._position_anchors()

    def _load_attendance_config_on_startup(self) -> None:
        """启动时读取用户目录配置，有有效账号则直接进入已登录状态。"""
        try:
            from backend.services.attendance_config import load_config

            result = load_config()
        except Exception:
            return
        self.state.attendance_config = result.config
        if not result.requires_login:
            username = str(result.config.get("attendance", {}).get("username", "")).strip()
            self.state.user_name = username
            self.state.logged_in = True

    def _set_skills_enabled(self, enabled: bool) -> None:
        """Toggle global Skills mode from the header switch."""
        self.state.skills_enabled = enabled
        message = (
            "已启用 Skills，将按设置中勾选的技能优先处理。"
            if enabled
            else "已关闭 Skills，将仅使用通用智能模式。"
        )
        self.chat_view._add_message("assistant", message)

    def _show_initial_login(self) -> None:
        """Show login on startup until the user signs in."""
        if not self.state.logged_in:
            self._handle_user_request()
    def _open_settings(self) -> None:
        """Open the settings dialog and refresh visible skill chips afterward."""
        dialog = SettingsDialog(self.state, self)
        dialog.settings_changed.connect(self.chat_view.refresh_from_state)
        dialog.settings_changed.connect(self.apply_visual_settings)
        if hasattr(dialog, "logout_requested"):
            dialog.logout_requested.connect(self._logout_to_login)
        dialog.exec()
        self.apply_visual_settings()
        self.chat_view.refresh_from_state()

    def _logout_to_login(self) -> None:
        """Return to the startup login card from Settings."""
        self.state.logged_in = False
        self.state.user_name = None
        self._show_initial_login()

    def _handle_user_request(self) -> None:
        """Show login dialog if not logged in, otherwise show user popup."""
        if not self.state.logged_in:
            dlg = LoginDialog(self.state, self)
            dlg.setProperty("theme", self.state.theme)
            self.state.theme_changed.connect(lambda v: dlg.setProperty("theme", v))
            if dlg.exec():
                self.chat_view.input_bar.input.setFocus()
        else:
            self._toggle_user_popup()

    def _toggle_user_popup(self) -> None:
        """Toggle the user popup from the bottom-left login anchor."""
        if self.user_popup is not None and self.user_popup.isVisible():
            self.user_popup.hide()
            return
        self._show_user_popup()

    def _show_user_popup(self) -> None:
        if self.user_popup is None:
            self.user_popup = UserPopup(self.state, self)
            self.user_popup.setProperty("theme", self.state.theme)
            self.state.theme_changed.connect(lambda v: self.user_popup.setProperty("theme", v))
        anchor_geo = self.login_anchor.geometry()
        margin_x = max(18, int(self.width() * (24 / 1100)))
        margin_y = max(16, int(self.height() * (28 / 760)))
        gap = max(8, int(self.height() * (8 / 760)))

        popup_w = min(
            max(int(self.width() * (USER_POPUP_BASE_SIZE[0] / WINDOW_INITIAL_SIZE[0])), USER_POPUP_MIN_SIZE[0]),
            USER_POPUP_MAX_SIZE[0],
        )
        popup_h = min(
            max(int(self.height() * (USER_POPUP_BASE_SIZE[1] / WINDOW_INITIAL_SIZE[1])), USER_POPUP_MIN_SIZE[1]),
            USER_POPUP_MAX_SIZE[1],
        )
        self.user_popup.setFixedSize(popup_w, popup_h)

        x = max(margin_x, anchor_geo.x())
        y = anchor_geo.y() - popup_h - gap
        if y < margin_y:
            y = anchor_geo.y() + anchor_geo.height() + gap

        x = min(x, self.width() - popup_w - margin_x)
        y = min(y, self.height() - popup_h - margin_y)
        x = max(margin_x, x)
        y = max(margin_y, y)

        self.user_popup.setGeometry(x, y, popup_w, popup_h)
        self.user_popup.show()
        self.user_popup.raise_()
        self.user_popup.setFocus()

    def moveEvent(self, event) -> None:
        """Reposition floating anchors when the main window is moved."""
        super().moveEvent(event)
        self._position_anchors()

    def _position_anchors(self) -> None:
        """Position and scale anchors relative to current window size.

        Anchor size is computed from width/height ratios derived earlier:
        - width_ratio = 38 / 1100
        - height_ratio = 38 / 760
        The computed size is clamped to reasonable min/max to avoid extremes.
        """
        geo = self.geometry()
        win_w = geo.width()
        win_h = geo.height()

        # ratios come from AppState (derived from reference window)
        width_ratio = self.state.anchor_width_ratio
        height_ratio = self.state.anchor_height_ratio

        size_w = int(win_w * width_ratio)
        size_h = int(win_h * height_ratio)
        # choose the smaller to keep anchor square and not overflow
        size = max(self.state.anchor_min_size, min(size_w, size_h))
        # clamp to an upper bound for large screens
        size = min(size, self.state.anchor_max_size)

        self.login_anchor.setFixedSize(size, size)

        # update inline style for radius and font-size to match computed size
        radius = max(1, size // 2)
        font_pt = max(8, int(size * self.state.anchor_font_ratio))
        self._style_login_anchor(radius, font_pt)

        x = 24
        y = self.height() - size - 28
        self.login_anchor.move(x, y)
        self.login_anchor.raise_()

    def _apply_login_anchor_theme(self, theme: str) -> None:
        """Refresh the login anchor when the app theme changes."""
        self.login_anchor.setProperty("theme", theme)
        self._position_anchors()

    def _style_login_anchor(self, radius: int, font_pt: int) -> None:
        """Apply size and theme colors for the bottom-left login anchor."""
        token = tokens_for_theme(self.state.theme).login_anchor

        self.login_anchor.setStyleSheet(f"""
        QPushButton#LoginAnchor {{
            background: {token.background};
            border: 1px solid {token.border};
            border-radius: {radius}px;
            color: {token.text};
            font-weight: 700;
            font-size: {font_pt}pt;
            text-align: center;
        }}
        QPushButton#LoginAnchor:hover {{
            background: {token.hover_background};
        }}
        """)

    def _update_login_anchor(self) -> None:
        """Update the circular anchor to show initial or default icon."""
        if self.state.logged_in and self.state.user_name:
            initial = self.state.user_name.strip()[0].upper()
            self.login_anchor.setText(initial)
        else:
            # use a person glyph as placeholder
            self.login_anchor.setText("\u672a")
        # ensure styling re-applies
        self.login_anchor.style().unpolish(self.login_anchor)
        self.login_anchor.style().polish(self.login_anchor)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_anchors()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # ensure anchor is positioned and visible after window is shown
        self._position_anchors()
        if hasattr(self, "login_anchor"):
            self.login_anchor.show()
            self.login_anchor.raise_()

    def _toggle_content_minimized(self) -> None:
        """Minimize the frameless desktop window."""
        self.showMinimized()

    def _toggle_maximized(self) -> None:
        """Toggle the native window between normal and maximized size."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def apply_visual_settings(self) -> None:
        """Apply runtime theme and font-size settings to the visible UI."""
        app = QApplication.instance()
        if app is not None:
            font = QFont("Microsoft YaHei")
            font.setPointSize(FONT_POINT_SIZES.get(self.state.font_size, FONT_POINT_SIZES["medium"]))
            app.setFont(font)

        for widget in (self.root, self.app_card, self.header, self.chat_view):
            widget.setProperty("theme", self.state.theme)
            widget.setProperty("fontMode", self.state.font_size)
            self._refresh_style(widget)

    def _refresh_style(self, widget: QWidget) -> None:
        """Repolish a widget and its children after dynamic property changes."""
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        for child in widget.findChildren(QWidget):
            child.style().unpolish(child)
            child.style().polish(child)

    def mousePressEvent(self, event) -> None:
        """Allow dragging the frameless window from the header area."""
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= self.header.height():
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Move the frameless window while dragging the header."""
        if self._drag_position is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """End frameless-window dragging."""
        self._drag_position = None
        super().mouseReleaseEvent(event)
