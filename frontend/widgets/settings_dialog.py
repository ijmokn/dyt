"""设置页面"""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
)

from app.state import AppState
from shared.skill_catalog import DEFAULT_SKILLS


class ArrowComboBox(QPushButton):
    """A compact dropdown-looking button with a always-visible arrow."""

    current_changed = Signal()

    def __init__(self, options: dict[str, str], current_value: str) -> None:
        super().__init__()
        self.options = options
        self.values = list(options.keys())
        self.current_value = current_value if current_value in options else self.values[0]
        self.setObjectName("ArrowComboBox")
        self.setFixedWidth(190)
        self.setFixedHeight(38)
        self.setFlat(True)
        self.clicked.connect(self._show_menu)

    def currentData(self) -> str:
        """Return the selected option value."""
        return self.current_value

    def _show_menu(self) -> None:
        """Show a dropdown menu with all available options."""
        menu = QMenu(self)
        menu.setObjectName("ArrowComboMenu")
        for value in self.values:
            action = menu.addAction(self.options[value])
            action.setCheckable(True)
            action.setChecked(value == self.current_value)
            action.triggered.connect(lambda checked=False, selected=value: self._select(selected))
        menu.exec(self.mapToGlobal(self.rect().bottomLeft()))

    def _select(self, value: str) -> None:
        """Select one value from the dropdown menu."""
        self.current_value = value
        self.update()
        self.current_changed.emit()

    def paintEvent(self, event) -> None:
        """Draw text on the left and a line-style arrow on the right."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)

        # Detect theme by walking up parents for a widget property 'theme'.
        theme = "default"
        parent = self.parent()
        while parent is not None:
            t = parent.property("theme")
            if t is not None:
                theme = t
                break
            parent = parent.parent()

        if theme == "dark":
            fill_col = QColor("#17253c")
            border_col = QColor("#304d79")
            text_col = QColor("#cfe6ff")
        else:
            fill_col = QColor("#ffffff")
            border_col = QColor("#c3d8f7")
            text_col = QColor("#174381")

        painter.fillPath(path, fill_col)
        painter.setPen(QPen(border_col, 1))
        painter.drawPath(path)

        painter.setPen(text_col)
        text_rect = self.rect().adjusted(12, 0, -42, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.options[self.current_value])

        pen = QPen(text_col, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        center_x = self.width() - 26
        center_y = self.height() // 2 + 1
        painter.drawLine(center_x - 5, center_y - 3, center_x, center_y + 3)
        painter.drawLine(center_x, center_y + 3, center_x + 5, center_y - 3)


THEME_OPTIONS = {
    "default": "商务蓝",
    "light": "简洁浅色",
    "dark": "夜间深色",
}

FONT_OPTIONS = {
    "small": "紧凑",
    "medium": "标准",
    "large": "舒适",
}


class UnsavedSettingsDialog(QDialog):
    """未保存设置提示弹窗。

    设置页支持即时预览，因此关闭前需要提醒用户：当前预览内容还没有保存。
    """

    def __init__(self, theme: str, parent=None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.setObjectName("UnsavedSettingsDialog")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(380, 178)
        self._build_ui()
        self._apply_theme()

    def _build_ui(self) -> None:
        """创建提示文案和操作按钮。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(12)

        title = QLabel("提示")
        title.setObjectName("UnsavedTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        message = QLabel("尚未保存设置，关闭后将放弃当前修改。")
        message.setObjectName("UnsavedMessage")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)

        buttons = QHBoxLayout()
        back_button = QPushButton("返回设置")
        back_button.setObjectName("UnsavedSecondaryButton")
        close_button = QPushButton("继续关闭")
        close_button.setObjectName("UnsavedPrimaryButton")
        back_button.clicked.connect(self.reject)
        close_button.clicked.connect(self.accept)
        buttons.addStretch(1)
        buttons.addWidget(back_button)
        buttons.addWidget(close_button)
        buttons.addStretch(1)

        layout.addWidget(title)
        layout.addWidget(message)
        layout.addStretch(1)
        layout.addLayout(buttons)

    def _apply_theme(self) -> None:
        """让提示弹窗跟随当前设置页主题。"""
        if self.theme == "dark":
            bg = "#0f2234"
            title_color = "#cfe6ff"
            text_color = "#cfe6ff"
            secondary_bg = "#17253c"
            secondary_border = "#304d79"
        else:
            bg = "#ffffff"
            title_color = "#174381"
            text_color = "#12283b"
            secondary_bg = "#ffffff"
            secondary_border = "#c3d8f7"

        self.setStyleSheet(f"""
        QDialog#UnsavedSettingsDialog {{
            background: {bg};
            border-radius: 14px;
        }}
        QLabel#UnsavedTitle {{
            color: {title_color};
            font-size: 18px;
            font-weight: 700;
        }}
        QLabel#UnsavedMessage {{
            color: {text_color};
            font-size: 13px;
        }}
        QPushButton#UnsavedPrimaryButton {{
            background: #1E6DFF;
            color: #ffffff;
            border: none;
            border-radius: 16px;
            min-width: 88px;
            min-height: 32px;
            font-weight: 700;
        }}
        QPushButton#UnsavedSecondaryButton {{
            background: {secondary_bg};
            color: {title_color};
            border: 1px solid {secondary_border};
            border-radius: 16px;
            min-width: 88px;
            min-height: 32px;
            font-weight: 700;
        }}
        """)


class SettingsDialog(QDialog):
    """Runtime-only settings modal."""

    settings_changed = Signal()
    logout_requested = Signal()

    def __init__(self, state: AppState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self._capture_saved_state()
        # Expose current theme to allow QSS selectors like #SettingsDialog[theme="dark"]
        self.setProperty("theme", self.state.theme)
        self.state.theme_changed.connect(lambda v: self.setProperty("theme", v))
        # Apply full dialog theme styling whenever theme changes
        self.state.theme_changed.connect(self._apply_theme)
        self.skill_checks: dict[str, QCheckBox] = {}
        self.setWindowTitle("J-Mate 设置")
        self.setObjectName("SettingsDialog")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumWidth(640)
        # 构建 UI：将所有控件分组并布局到对话框中
        # 这里把 UI 构建逻辑单独放在 `_build_ui`，便于维护和测试
        self._build_ui()
        # Ensure initial theme styles are applied
        self._apply_theme(self.state.theme)

    def _build_ui(self) -> None:
        """Create grouped settings controls."""
        # 主垂直布局，负责把各个设置分组从上到下排列
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(12)

        top = QHBoxLayout()
        # 顶部标题栏区域：包含标题文本与右侧的关闭按钮
        # 该区域在截图中用红框标注（顶部白色标题栏），用于显示对话框标题并提供关闭操作
        title = QLabel("设置")
        title.setObjectName("SettingsTitle")
        close_button = QPushButton("关闭")
        close_button.setObjectName("CloseSettingsButton")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.reject)
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(close_button)

        theme_group = self._group("界面主题")
        theme_layout = QGridLayout(theme_group)
        theme_layout.setContentsMargins(14, 14, 14, 14)
        theme_layout.setHorizontalSpacing(16)
        theme_layout.setVerticalSpacing(10)
        theme_title = QLabel("界面主题")
        theme_title.setObjectName("SettingsGroupTitle")

        self.theme_select = ArrowComboBox(THEME_OPTIONS, self.state.theme)
        self.theme_select.current_changed.connect(self._preview_state)

        self.font_select = ArrowComboBox(FONT_OPTIONS, self.state.font_size)
        self.font_select.current_changed.connect(self._preview_state)

        theme_layout.addWidget(theme_title, 0, 0, 1, 2)
        theme_layout.addWidget(QLabel("主题风格"), 1, 0)
        theme_layout.addWidget(self.theme_select, 1, 1)
        theme_layout.addWidget(QLabel("字体大小"), 2, 0)
        theme_layout.addWidget(self.font_select, 2, 1)

        input_group = self._group("输入")
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(14, 14, 14, 14)
        input_title = QLabel("输入行为")
        input_title.setObjectName("SettingsGroupTitle")
        self.enter_toggle = QCheckBox("Enter 直接发送，Shift+Enter 换行")
        self.enter_toggle.setChecked(self.state.enter_to_send)
        self.enter_toggle.toggled.connect(self._preview_state)
        input_layout.addWidget(input_title)
        input_layout.addWidget(self.enter_toggle)

        skill_group = self._group("Skills 显示")
        skill_layout = QGridLayout(skill_group)
        skill_layout.setContentsMargins(14, 14, 14, 14)
        skill_layout.setHorizontalSpacing(12)
        skill_layout.setVerticalSpacing(10)
        skill_layout.setColumnMinimumWidth(0, 320)
        skill_layout.setColumnMinimumWidth(1, 320)
        skill_title = QLabel("Skills 管理")
        skill_title.setObjectName("SettingsGroupTitle")
        skill_layout.addWidget(skill_title, 0, 0, 1, 2)
        for index, skill in enumerate(DEFAULT_SKILLS):
            check = QCheckBox(f"{skill.icon} {skill.name}")
            check.setChecked(skill.id in self.state.enabled_skill_ids)
            check.toggled.connect(self._preview_state)
            self.skill_checks[skill.id] = check
            skill_layout.addWidget(check, index // 2 + 1, index % 2)

        suggestion_group = self._group("可扩展设置建议")
        suggestion_layout = QVBoxLayout(suggestion_group)
        suggestion_layout.setContentsMargins(14, 14, 14, 14)
        suggestion_title = QLabel("可扩展设置建议")
        suggestion_title.setObjectName("SettingsGroupTitle")
        suggestion = QLabel(
            "1. 默认首页技能（进入页面时自动激活）\n"
            "2. 常用示例词维护（自定义快捷提问）\n"
            "3. 对话记录保留天数与一键导出"
        )
        # 建议区域：用于展示可扩展的配置建议文本
        # 截图中中间靠下的文本区域对应此处（带有换行的说明文字）
        suggestion.setObjectName("SettingNote")
        suggestion.setWordWrap(True)
        suggestion_layout.addWidget(suggestion_title)
        suggestion_layout.addWidget(suggestion)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("完成")
        buttons.accepted.connect(self._save_settings)
        logout_button = QPushButton("退出登录")
        logout_button.setObjectName("LogoutSettingsButton")
        logout_button.clicked.connect(self._logout)
        footer_buttons = QHBoxLayout()
        footer_buttons.addStretch(1)
        footer_buttons.addWidget(logout_button)
        footer_buttons.addWidget(buttons)
        # 底部按钮区域：负责确认/完成操作。
        # 在截图中，完成/发送相关按钮位于对话框的右下角，用户点击"完成"会触发 accept()

        # 将所有分组和底部按钮加入主布局，完成对话框的整体排列

        layout.addLayout(top)
        layout.addWidget(theme_group)
        layout.addWidget(input_group)
        layout.addWidget(skill_group)
        layout.addWidget(suggestion_group)
        layout.addLayout(footer_buttons)

    def _logout(self) -> None:
        """退出登录并回到启动登录界面。"""
        self.logout_requested.emit()
        self.accept()

    @staticmethod
    def _group(title: str) -> QFrame:
        """Create a titled settings group frame."""
        frame = QFrame()
        frame.setObjectName("SettingsGroup")
        frame.setProperty("title", title)
        return frame

    def _apply_theme(self, theme: str) -> None:
        """Apply theme-wide QSS to the settings dialog and its children.

        This complements widget-level custom painting (e.g. `ArrowComboBox`)
        by ensuring the whole settings page (backgrounds, labels, buttons,
        checkboxes, group frames) follows dark/light themes consistently.
        """
        if theme == "dark":
            dialog_bg = "#0f2234"
            group_bg = "#17253c"
            group_border = "#304d79"
            title_color = "#cfe6ff"
            text_color = "#cfe6ff"
            note_color = "#a9c9ff"
            button_bg = "#1E6DFF"
            button_fg = "#ffffff"
        else:
            dialog_bg = "#f6f9ff"
            group_bg = "#ffffff"
            group_border = "#e2edff"
            title_color = "#174381"
            text_color = "#12283b"
            note_color = "#4b6ea6"
            button_bg = "#1E6DFF"
            button_fg = "#ffffff"

        qss = f"""
        QDialog#SettingsDialog {{
            background: transparent;
        }}
        QFrame#SettingsGroup {{
            background: {group_bg};
            border: 1px solid {group_border};
            border-radius: 8px;
        }}
        QLabel#SettingsTitle {{
            color: {title_color};
            font-size: 18px;
            font-weight: 600;
        }}
        QLabel#SettingsGroupTitle {{
            color: {title_color};
            font-size: 14px;
            font-weight: 600;
        }}
        QLabel, QCheckBox, QPushButton {{
            color: {text_color};
        }}
        QLabel#SettingNote {{
            color: {note_color};
        }}
        QPushButton#CloseSettingsButton,
        QPushButton#LogoutSettingsButton,
        QDialogButtonBox QPushButton {{
            background: {button_bg};
            color: {button_fg};
            border: 1px solid transparent;
            border-radius: 10px;
            padding: 8px 14px;
            font-weight: 700;
        }}
        QPushButton#LogoutSettingsButton {{
            color: #c03636;
            border: 1px solid #f5c2c2;
            background: #ffffff;
        }}
        QPushButton#CloseSettingsButton:hover,
        QDialogButtonBox QPushButton:hover {{
            background: #0f5fe5;
        }}
        QPushButton#LogoutSettingsButton:hover {{
            background: #fff5f5;
        }}
        QCheckBox {{
            spacing: 8px;
        }}
        """

        self.setStyleSheet(qss)
        self.update()

    def paintEvent(self, event) -> None:
        """Draw the dialog shell with smooth rounded corners."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, 20, 20)

        if self.state.theme == "dark":
            fill = QColor("#0f2234")
            border = QColor("#304d79")
        else:
            fill = QColor("#f6f9ff")
            border = QColor("#d4e3fb")

        painter.fillPath(path, fill)
        painter.setPen(QPen(border, 1))
        painter.drawPath(path)
        super().paintEvent(event)

    def _capture_saved_state(self) -> None:
        """Remember the last explicitly saved settings."""
        self._saved_theme = self.state.theme
        self._saved_font_size = self.state.font_size
        self._saved_enter_to_send = self.state.enter_to_send
        self._saved_enabled_skill_ids = set(self.state.enabled_skill_ids)
        self._saved_active_skill_id = self.state.active_skill_id

    def _has_unsaved_changes(self) -> bool:
        """判断当前控件值是否和上次保存的设置不同。"""
        enabled = {skill_id for skill_id, check in self.skill_checks.items() if check.isChecked()}
        return (
            self.theme_select.currentData() != self._saved_theme
            or self.font_select.currentData() != self._saved_font_size
            or self.enter_toggle.isChecked() != self._saved_enter_to_send
            or enabled != self._saved_enabled_skill_ids
            or self.state.active_skill_id != self._saved_active_skill_id
        )

    def _confirm_discard_unsaved_changes(self) -> bool:
        """关闭设置页前确认是否放弃未保存修改。"""
        if not self._has_unsaved_changes():
            return True
        dialog = UnsavedSettingsDialog(theme=self.state.theme, parent=self)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def _restore_saved_state(self) -> None:
        """Undo live preview changes that were not confirmed."""
        self.state.theme = self._saved_theme
        self.state.font_size = self._saved_font_size
        self.state.enter_to_send = self._saved_enter_to_send
        self.state.enabled_skill_ids = set(self._saved_enabled_skill_ids)
        self.state.active_skill_id = self._saved_active_skill_id
        self.settings_changed.emit()

    def _preview_state(self) -> None:
        """Apply control values immediately as a live preview."""
        self._update_state()

    def _save_settings(self) -> None:
        """Keep current previewed settings and close the dialog."""
        self._update_state()
        self._capture_saved_state()
        super().accept()

    def reject(self) -> None:
        """Close the dialog and discard unconfirmed preview changes."""
        if not self._confirm_discard_unsaved_changes():
            return
        self._restore_saved_state()
        super().reject()

    def closeEvent(self, event) -> None:
        """处理系统关闭事件，确保未保存设置也会触发提示。"""
        if not self._confirm_discard_unsaved_changes():
            event.ignore()
            return
        self._restore_saved_state()
        event.accept()

    def _update_state(self) -> None:
        """Persist control values to in-memory state."""
        self.state.theme = self.theme_select.currentData()
        self.state.font_size = self.font_select.currentData()
        self.state.enter_to_send = self.enter_toggle.isChecked()

        enabled = {skill_id for skill_id, check in self.skill_checks.items() if check.isChecked()}
        # 确保至少有一个技能被启用：如果用户取消了所有技能，则自动选中第一个默认技能
        # 这样可以避免界面在没有任何技能时出现不可用或空白的状态（对应截图底部红框处的技能/输入区域）
        if not enabled:
            first_id = DEFAULT_SKILLS[0].id
            enabled.add(first_id)
            # 程序上同步设置复选框以反映自动选择的默认技能
            self.skill_checks[first_id].setChecked(True)
        self.state.enabled_skill_ids = enabled
        # 如果当前活跃技能已被禁用，则清空活跃技能，避免引用不存在的技能 id
        if self.state.active_skill_id not in enabled:
            self.state.active_skill_id = None
        self.settings_changed.emit()
