"""设置页面"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import QSize, Signal, Qt, QEvent
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
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
        self._attendance_config = self._load_attendance_config()
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
        self._apply_responsive_size(parent)
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

        personal_group = self._group("个人信息")
        personal_layout = QGridLayout(personal_group)
        personal_layout.setContentsMargins(14, 14, 14, 14)
        personal_layout.setHorizontalSpacing(12)
        personal_layout.setVerticalSpacing(8)
        personal_layout.setColumnMinimumWidth(0, self._personal_label_width())
        personal_layout.setColumnStretch(0, 0)
        personal_layout.setColumnStretch(1, 0)
        personal_layout.setColumnStretch(2, 0)
        personal_layout.setColumnStretch(3, 1)
        personal_title = QLabel("个人信息")
        personal_title.setObjectName("SettingsGroupTitle")
        personal_note = QLabel("个人信息仅保存在此设备上，不会上传至任何服务器，请放心使用。")
        personal_note.setObjectName("SettingNote")
        personal_note.setWordWrap(True)

        self.position_input = self._setting_input(self._config_value("common", "position"))
        self.evection_username_input = self._setting_input(self._config_value("evection", "username"))
        self.evection_password_input = self._setting_input(self._config_value("evection", "password"), password=True)
        self._set_short_field_width(self.evection_username_input)
        self._set_short_field_width(self.evection_password_input)
        evection_password_field = self._password_field(self.evection_password_input)
        self.pjmn_username_input = self._setting_input(self._config_value("pjmn", "username"))
        self.pjmn_password_input = self._setting_input(self._config_value("pjmn", "password"), password=True)
        self._set_short_field_width(self.pjmn_username_input)
        self._set_short_field_width(self.pjmn_password_input)
        pjmn_password_field = self._password_field(self.pjmn_password_input)
        self.attendance_username_input = self._setting_input(self._config_value("attendance", "username"))
        self.attendance_password_input = self._setting_input(self._config_value("attendance", "password"), password=True)
        self._set_short_field_width(self.attendance_username_input)
        self._set_short_field_width(self.attendance_password_input)
        attendance_password_field = self._password_field(self.attendance_password_input)
        self.output_dir_input = self._setting_input(self._config_value("common", "outputDir"))
        browse_output_button = QPushButton("选择")
        browse_output_button.setObjectName("BrowseOutputButton")
        browse_output_button.setFixedWidth(58)
        browse_output_button.clicked.connect(self._choose_output_dir)

        personal_layout.addWidget(personal_title, 0, 0, 1, 4)
        personal_layout.addWidget(personal_note, 1, 0, 1, 4)
        self._add_personal_row(personal_layout, 2, "职名", self.position_input)
        self._add_personal_pair_row(
            personal_layout,
            3,
            "禀议系统",
            self.evection_username_input,
            evection_password_field,
        )
        self._add_personal_pair_row(
            personal_layout,
            4,
            "PJCOST系统",
            self.pjmn_username_input,
            pjmn_password_field,
        )
        self._add_personal_pair_row(
            personal_layout,
            5,
            "考勤系统",
            self.attendance_username_input,
            attendance_password_field,
        )
        output_layout = QHBoxLayout()
        output_layout.setSpacing(8)
        output_layout.addWidget(self.output_dir_input, stretch=1)
        output_layout.addWidget(browse_output_button)
        self._add_personal_row(personal_layout, 6, "输出路径", output_layout)

        theme_group = self._group("界面主题")
        theme_layout = QGridLayout(theme_group)
        theme_layout.setContentsMargins(14, 14, 14, 14)
        theme_layout.setHorizontalSpacing(16)
        theme_layout.setVerticalSpacing(10)
        theme_title = QLabel("界面主题")
        theme_title.setObjectName("SettingsGroupTitle")

        self.theme_select = ArrowComboBox(THEME_OPTIONS, self.state.theme)
        self.theme_select.setFixedWidth(self._pair_field_width())
        self.theme_select.current_changed.connect(self._preview_state)

        self.font_select = ArrowComboBox(FONT_OPTIONS, self.state.font_size)
        self.font_select.setFixedWidth(self._pair_field_width())
        self.font_select.current_changed.connect(self._preview_state)

        theme_layout.addWidget(theme_title, 0, 0, 1, 2)
        theme_layout.addWidget(QLabel("主题风格"), 1, 0)
        theme_layout.addWidget(self.theme_select, 1, 1)
        theme_layout.addWidget(QLabel("字体大小"), 2, 0)
        theme_layout.addWidget(self.font_select, 2, 1)
        theme_layout.setColumnMinimumWidth(0, self._personal_label_width())
        theme_layout.setColumnStretch(0, 0)
        theme_layout.setColumnStretch(1, 0)
        theme_layout.setColumnStretch(2, 1)

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
        skill_layout.setColumnStretch(0, 1)
        skill_layout.setColumnStretch(1, 1)
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

        scroll_content = QWidget()
        scroll_content.setObjectName("SettingsScrollContent")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)
        scroll_layout.addWidget(personal_group)
        scroll_layout.addWidget(theme_group)
        scroll_layout.addWidget(input_group)
        scroll_layout.addWidget(skill_group)
        scroll_layout.addWidget(suggestion_group)
        scroll_layout.addStretch(1)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("SettingsScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidget(scroll_content)

        # 将顶部、可滚动内容和底部按钮加入主布局，保持弹窗原尺寸。

        layout.addLayout(top)
        layout.addWidget(scroll_area, stretch=1)
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

    def _apply_responsive_size(self, parent) -> None:
        """根据设置内容宽度反推设置页宽度，避免右侧出现大片空白。"""
        content_width = self._personal_label_width() + 12 + self._pair_field_width()
        chrome_width = 30 * 2 + 14 * 2 + 22
        width = content_width + chrome_width
        if parent is not None:
            height = int(parent.height() * 0.82)
            width = min(width, max(560, parent.width() - 80))
        else:
            height = 620
        height = max(560, min(720, height))
        self.resize(width, height)
        self.setFixedWidth(width)
        self.setMinimumHeight(540)

    def _load_attendance_config(self) -> dict:
        """读取运行时配置；读取失败时使用空配置，避免设置页打不开。"""
        if self.state.attendance_config:
            return deepcopy(self.state.attendance_config)
        try:
            from backend.services.attendance_config import load_config

            result = load_config()
            self.state.attendance_config = result.config
            return deepcopy(result.config)
        except Exception:
            return {
                "version": "1.0",
                "attendance": {"username": "", "password": "", "url": ""},
                "pjmn": {"username": "", "password": "", "url": ""},
                "evection": {"username": "", "password": "", "url": ""},
                "common": {"outputDir": str(Path.home() / "Documents"), "waitMs": 7000, "position": ""},
            }

    def _config_value(self, section: str, key: str) -> str:
        """安全读取配置字段，设置页显示用。"""
        value = self._attendance_config.get(section, {}).get(key, "")
        return "" if value is None else str(value)

    @staticmethod
    def _setting_input(value: str = "", password: bool = False) -> QLineEdit:
        """创建个人信息区域使用的输入框。"""
        line_edit = QLineEdit()
        line_edit.setObjectName("SettingInput")
        line_edit.setText(value)
        line_edit.setMinimumHeight(34)
        line_edit.setMinimumWidth(0)
        if password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        return line_edit

    def _personal_label_width(self) -> int:
        """根据当前字体计算个人信息标签列宽，避免写死大间距。"""
        return self.fontMetrics().horizontalAdvance("PJCOST系统") + 12

    def _short_field_width(self) -> int:
        """根据账号长度场景计算账号/密码框显示宽度，不限制可输入内容。"""
        return self.fontMetrics().horizontalAdvance("0000000000000000") + 72

    def _pair_field_width(self) -> int:
        """账号列和密码列合计宽度，用于单栏字段右侧对齐。"""
        return self._short_field_width() * 2 + 12

    def _set_short_field_width(self, line_edit: QLineEdit) -> None:
        """只缩短账号/密码子框的显示宽度，不限制输入内容长度。"""
        line_edit.setFixedWidth(self._short_field_width())

    def _add_personal_row(self, layout: QGridLayout, row: int, label_text: str, widget_or_layout) -> None:
        """添加单字段个人信息行。"""
        label = QLabel(label_text)
        label.setObjectName("PersonalInfoLabel")
        layout.addWidget(label, row, 0)
        if isinstance(widget_or_layout, QHBoxLayout):
            wrapper = QWidget()
            wrapper.setFixedWidth(self._pair_field_width())
            wrapper.setLayout(widget_or_layout)
            layout.addWidget(wrapper, row, 1, 1, 2, Qt.AlignmentFlag.AlignLeft)
        else:
            widget_or_layout.setFixedWidth(self._pair_field_width())
            layout.addWidget(widget_or_layout, row, 1, 1, 2, Qt.AlignmentFlag.AlignLeft)

    def _add_personal_pair_row(
        self,
        layout: QGridLayout,
        row: int,
        label_text: str,
        account_input: QLineEdit,
        password_input,
    ) -> None:
        """添加账号/密码双字段个人信息行。"""
        label = QLabel(label_text)
        label.setObjectName("PersonalInfoLabel")
        layout.addWidget(label, row, 0)
        layout.addWidget(account_input, row, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(password_input, row, 2, Qt.AlignmentFlag.AlignLeft)

    def _password_field(self, password_input: QLineEdit) -> QWidget:
        """在密码输入框内部右侧放置小眼睛按钮。"""
        password_input.setProperty("passwordField", True)
        password_input.setEchoMode(QLineEdit.EchoMode.Password)

        toggle = QPushButton(password_input)
        toggle.setObjectName("PasswordPeekButton")
        toggle.setIcon(self._eye_icon())
        toggle.setIconSize(QSize(13, 13))
        toggle.setFixedSize(24, 24)
        toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        def _show_password() -> None:
            password_input.setEchoMode(QLineEdit.EchoMode.Normal)

        def _hide_password() -> None:
            password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # 和 HTML 一致：按住小眼睛时显示密码，松开或移出后立即隐藏。
        toggle.pressed.connect(_show_password)
        toggle.released.connect(_hide_password)
        toggle.installEventFilter(self)
        password_input.installEventFilter(self)
        toggle._jmate_password_input = password_input  # type: ignore[attr-defined]
        toggle._jmate_hide_password = _hide_password  # type: ignore[attr-defined]
        password_input._jmate_peek_button = toggle  # type: ignore[attr-defined]
        self._position_password_button(password_input)
        return password_input

    @staticmethod
    def _eye_icon() -> QIcon:
        """绘制灰色小眼睛图标，避免使用彩色 emoji。"""
        pixmap = QPixmap(18, 18)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor("#9aa8bf"), 1.4)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        eye = QPainterPath()
        eye.moveTo(3, 9)
        eye.cubicTo(5.2, 4.9, 12.8, 4.9, 15, 9)
        eye.cubicTo(12.8, 13.1, 5.2, 13.1, 3, 9)
        painter.drawPath(eye)
        painter.drawEllipse(7.0, 7.0, 4.0, 4.0)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def _position_password_button(password_input: QLineEdit) -> None:
        """把小眼睛按钮固定到输入框内部右侧。"""
        button = getattr(password_input, "_jmate_peek_button", None)
        if button is None:
            return
        x = password_input.width() - button.width() - 7
        y = (password_input.height() - button.height()) // 2
        button.move(max(0, x), max(0, y))

    def eventFilter(self, watched, event) -> bool:
        """密码显示按钮移出或失焦时隐藏密码。"""
        if isinstance(watched, QLineEdit) and event.type() == QEvent.Type.Resize:
            self._position_password_button(watched)
        if getattr(watched, "objectName", lambda: "")() == "PasswordPeekButton" and event.type() in (
            QEvent.Type.Leave,
            QEvent.Type.FocusOut,
            QEvent.Type.MouseButtonRelease,
        ):
            hide_password = getattr(watched, "_jmate_hide_password", None)
            if hide_password:
                hide_password()
        return super().eventFilter(watched, event)

    def _choose_output_dir(self) -> None:
        """选择输出路径。"""
        current_dir = self.output_dir_input.text().strip() or str(Path.home() / "Documents")
        selected = QFileDialog.getExistingDirectory(self, "选择输出路径", current_dir)
        if selected:
            self.output_dir_input.setText(selected)

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
        QScrollArea#SettingsScrollArea {{
            background: transparent;
            border: none;
        }}
        QWidget#SettingsScrollContent {{
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
        QLabel#PersonalInfoLabel {{
            color: {text_color};
            font-weight: 400;
        }}
        QLineEdit#SettingInput {{
            background: {group_bg};
            color: {text_color};
            border: 1px solid {group_border};
            border-radius: 10px;
            padding: 6px 8px;
        }}
        QLineEdit#SettingInput:focus {{
            border: 1px solid #1E6DFF;
        }}
        QLineEdit#SettingInput[passwordField="true"] {{
            padding-right: 34px;
        }}
        QPushButton#CloseSettingsButton,
        QPushButton#LogoutSettingsButton,
        QPushButton#BrowseOutputButton,
        QDialogButtonBox QPushButton {{
            background: {button_bg};
            color: {button_fg};
            border: 1px solid transparent;
            border-radius: 10px;
            padding: 8px 14px;
            font-weight: 700;
        }}
        QPushButton#BrowseOutputButton {{
            background: {button_bg};
            color: {button_fg};
            border: 1px solid transparent;
            border-radius: 10px;
            padding: 7px 12px;
            font-weight: 700;
        }}
        QPushButton#PasswordPeekButton {{
            background: transparent;
            color: {note_color};
            border: none;
            border-radius: 0;
            padding: 0;
            font-weight: 400;
        }}
        QPushButton#LogoutSettingsButton {{
            color: #c03636;
            border: 1px solid #f5c2c2;
            background: #ffffff;
        }}
        QPushButton#CloseSettingsButton:hover,
        QPushButton#BrowseOutputButton:hover,
        QDialogButtonBox QPushButton:hover {{
            background: #0f5fe5;
        }}
        QPushButton#PasswordPeekButton:hover {{
            color: {title_color};
            background: transparent;
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
        self._saved_personal_values = self._personal_values()

    def _has_unsaved_changes(self) -> bool:
        """判断当前控件值是否和上次保存的设置不同。"""
        enabled = {skill_id for skill_id, check in self.skill_checks.items() if check.isChecked()}
        return (
            self.theme_select.currentData() != self._saved_theme
            or self.font_select.currentData() != self._saved_font_size
            or self.enter_toggle.isChecked() != self._saved_enter_to_send
            or enabled != self._saved_enabled_skill_ids
            or self.state.active_skill_id != self._saved_active_skill_id
            or self._personal_values() != self._saved_personal_values
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
        try:
            self._save_attendance_config()
        except Exception as exc:
            QMessageBox.warning(self, "保存失败", f"个人信息保存失败：{exc}")
            return
        self._capture_saved_state()
        super().accept()

    def _personal_values(self) -> tuple[str, ...]:
        """返回个人信息控件当前值，用于未保存变更判断。"""
        if not hasattr(self, "position_input"):
            config = self._attendance_config
            return (
                str(config.get("common", {}).get("position", "")),
                str(config.get("evection", {}).get("username", "")),
                str(config.get("evection", {}).get("password", "")),
                str(config.get("pjmn", {}).get("username", "")),
                str(config.get("pjmn", {}).get("password", "")),
                str(config.get("attendance", {}).get("username", "")),
                str(config.get("attendance", {}).get("password", "")),
                str(config.get("common", {}).get("outputDir", "")),
            )
        return (
            self.position_input.text().strip(),
            self.evection_username_input.text().strip(),
            self.evection_password_input.text(),
            self.pjmn_username_input.text().strip(),
            self.pjmn_password_input.text(),
            self.attendance_username_input.text().strip(),
            self.attendance_password_input.text(),
            self.output_dir_input.text().strip(),
        )

    def _save_attendance_config(self) -> None:
        """把个人信息区域写回配置文件，并同步到程序变量。"""
        config = deepcopy(self._attendance_config)
        config.setdefault("common", {})
        config.setdefault("evection", {})
        config.setdefault("pjmn", {})
        config.setdefault("attendance", {})

        config["common"]["position"] = self.position_input.text().strip()
        config["common"]["outputDir"] = self.output_dir_input.text().strip()
        config["evection"]["username"] = self.evection_username_input.text().strip()
        config["evection"]["password"] = self.evection_password_input.text()
        config["pjmn"]["username"] = self.pjmn_username_input.text().strip()
        config["pjmn"]["password"] = self.pjmn_password_input.text()
        config["attendance"]["username"] = self.attendance_username_input.text().strip()
        config["attendance"]["password"] = self.attendance_password_input.text()

        from backend.services.attendance_config import save_config

        runtime_config = save_config(config)
        self._attendance_config = deepcopy(runtime_config)
        self.state.attendance_config = runtime_config

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
