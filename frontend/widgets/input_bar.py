"""输入自然语言指令区域"""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout


class RoundedInputWrapper(QFrame):
    """Paint the input container as a stable rounded capsule.

    说明（外观相关）:
    - 该控件在 `paintEvent` 中使用 QPainter 绘制一个圆角胶囊式背景与边框，保证在不同平台下外观稳定，
      不依赖于 QSS 的裁剪行为。
    - 样式表中通过 `#InputWrapper` 选择器可以覆盖背景和边框颜色（参见 resources/styles/app.qss）。
    """

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("InputWrapper")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, 32, 32)

        # 检测主题（向上遍历父控件查找 theme 属性）
        theme = "default"
        parent = self.parent()
        while parent is not None:
            t = parent.property("theme")
            if t is not None:
                theme = t
                break
            parent = parent.parent()

        if theme == "dark":
            # 暗色主题下使用深色背景与较暗边框，保持与 app.qss 中暗色配色一致
            painter.fillPath(path, QColor("#17253c"))
            painter.setPen(QPen(QColor("#304d79"), 1))
        else:
            painter.fillPath(path, QColor("#ffffff"))
            painter.setPen(QPen(QColor("#cddff7"), 1))

        painter.drawPath(path)


class CapsuleButton(QPushButton):
    """A self-painted capsule button so clear/send match the HTML version.

    说明（外观与交互）:
    - 此按钮手动绘制圆角胶囊形背景、边框与文字颜色，以便主/次按钮在 hover 时颜色一致。
    - `primary` 参数决定主按钮（发送）和次按钮（清空）的配色方案。
    - QSS 中仍可通过 `#SendButton` / `#ClearButton` 选择器调整额外样式，但绘制逻辑保证基础视觉一致性。
    """

    def __init__(self, text: str, *, primary: bool) -> None:
        super().__init__(text)
        self.primary = primary
        self._hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        # 绘制圆角胶囊按钮：根据是否为主按钮、hover 状态以及当前主题来选择填充、边框和文字颜色
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect().adjusted(1, 1, -1, -1)
        radius = rect.height() / 2
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # 检测主题（向上遍历父控件查找 theme 属性）
        theme = "default"
        parent = self.parent()
        while parent is not None:
            t = parent.property("theme")
            if t is not None:
                theme = t
                break
            parent = parent.parent()

        # 主题关联的颜色选择：暗色主题下使用更深的背景和浅色文字
        if self.primary:
            if theme == "dark":
                fill = QColor("#1E6DFF") if not self._hovered else QColor("#0f5be0")
                border = fill
                text_color = QColor("#ffffff")
            else:
                fill = QColor("#0f5be0" if self._hovered else "#1E6DFF")
                border = fill
                text_color = QColor("#ffffff")
        else:
            if theme == "dark":
                fill = QColor("#17253c") if not self._hovered else QColor("#1e3149")
                border = QColor("#304d79")
                text_color = QColor("#d9e7ff")
            else:
                fill = QColor("#eff3fc" if self._hovered else "#ffffff")
                border = QColor("#bfdbfe")
                text_color = QColor("#4870a2")

        painter.fillPath(path, fill)
        painter.setPen(QPen(border, 1))
        painter.drawPath(path)
        painter.setPen(text_color)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())


class CommandTextEdit(QTextEdit):
    """Text edit that can emit submit on Enter."""

    submit_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.enter_to_send = True
        # 文本编辑器外观与交互
        # - `objectName` 对应 QSS 中的 `#NaturalInput`，用于颜色/字体等样式控制
        # - 占位文本给出示例，引导用户输入自然语言指令
        # - 固定高度（46px）与设计稿一致，保证与按钮行对齐
        self.setObjectName("NaturalInput")
        self.setPlaceholderText("例如：查询我的今日考勤")
        self.setFixedHeight(46)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Support Enter or Ctrl+Enter sending based on settings."""
        enter_pressed = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        if enter_pressed:
            if self.enter_to_send and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.submit_requested.emit()
                return
            if not self.enter_to_send and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.submit_requested.emit()
                return
        super().keyPressEvent(event)


class InputBar(QFrame):
    """Bottom input card with send, clear, and quick examples."""

    send_requested = Signal(str)
    clear_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("InputArea")
        self.input = CommandTextEdit()
        self._build_ui()

    def _build_ui(self) -> None:
        """Create input wrapper, buttons, and example hints."""
        # 根垂直布局：包含输入区域（圆角 wrapper）与下方的示例快捷词行
        root = QVBoxLayout(self)
        # 边距和间距控制与设计稿一致，保证输入区与窗口边缘间隔
        root.setContentsMargins(28, 16, 28, 24)
        root.setSpacing(10)

        # 圆角输入器容器：绘制背景与内边距，内部使用水平布局放置文本域和按钮
        wrapper = RoundedInputWrapper()
        wrapper_layout = QHBoxLayout(wrapper)
        # 内边距微调确保文本域与按钮有适当间隔
        wrapper_layout.setContentsMargins(22, 6, 6, 6)
        wrapper_layout.setSpacing(8)

        # 清空按钮（次按钮），使用自绘 CapsuleButton，以便与发送按钮样式一致
        clear_button = CapsuleButton("清空", primary=False)
        clear_button.setObjectName("ClearButton")
        clear_button.setFixedSize(78, 44)
        clear_button.clicked.connect(self.clear_requested.emit)

        # 发送按钮（主按钮），带箭头符号，与设计中的主色一致
        send_button = CapsuleButton("➤ 发送", primary=True)
        send_button.setObjectName("SendButton")
        send_button.setFixedSize(78, 44)
        send_button.clicked.connect(self._emit_send)
        self.input.submit_requested.connect(self._emit_send)

        # 布局顺序：文本域占满剩余空间，按钮靠右排列
        wrapper_layout.addWidget(self.input, stretch=1)
        wrapper_layout.addWidget(clear_button)
        wrapper_layout.addWidget(send_button)

        # 示例提示行（居中/靠右显示），提示文本可点击以快速填充到输入框
        hints = QHBoxLayout()
        hints.setSpacing(14)
        hints.addStretch(1)
        examples = (
            ("📌 查询今日考勤", "📌 查询我今天的考勤记录，包含上班时间、下班时间与是否迟到"),
            ("📄 查询休假制度", "📄 请说明公司休假制度，包括年假、病假和调休规则"),
            ("📅 预定会议", "📅 帮我预定明天下午3点与产品团队的会议，议题为Q2规划"),
            ("📧 发送邮件", "📧 帮我发送邮件给项目组，通知本周迭代进度与下周计划"),
        )
        for text, value in examples:
            label = QLabel(text)
            # `ExampleHint` 在 QSS 中定义了链接样式（下划线、颜色），并在 hover 时显示可点击感
            label.setObjectName("ExampleHint")
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.mousePressEvent = lambda event, value=value: self._fill_example(value)
            hints.addWidget(label)
        hints.addStretch(1)

        root.addWidget(wrapper)
        root.addLayout(hints)

    def set_enter_to_send(self, enabled: bool) -> None:
        """Update keyboard sending behavior."""
        self.input.enter_to_send = enabled

    def _emit_send(self) -> None:
        """Emit non-empty input text."""
        text = self.input.toPlainText().strip()
        if not text:
            self.input.setPlaceholderText("请输入自然语言指令...")
            return
        self.input.clear()
        self.send_requested.emit(text)

    def _fill_example(self, text: str) -> None:
        """Fill a quick example into the input box."""
        self.input.setPlainText(text)
        self.input.setFocus()
