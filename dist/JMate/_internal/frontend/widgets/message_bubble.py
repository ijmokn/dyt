"""Chat message bubble."""

from __future__ import annotations

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget


class BubbleFrame(QFrame):
    """Paint a reliable rounded chat bubble without relying on QSS clipping.

    说明（外观相关）:
    - 该类在 `paintEvent` 中使用 QPainter 绘制圆角气泡和一个小尾巴，避免依赖 QSS 的裁剪特性。
    - 通过 `role` 判断是用户气泡还是助理气泡，从而选择不同的填充和边框颜色。
    - `objectName`（见 `MessageBubble`）与 QSS 中的选择器对应，例如 `#UserBubble` / `#AssistantBubble`，QSS 会额外控制一些视觉样式。
    """

    def __init__(self, role: str) -> None:
        super().__init__()
        self.role = role
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:
        """Draw a rounded bubble with the HTML-like small tail corner.

        绘制步骤说明：
        1. 计算气泡的矩形、圆角半径与尾巴尺寸（`radius`, `small`）。
        2. 向上遍历父控件查找 `theme` 属性，根据主题决定助理气泡的背景色（暗色/亮色）。
        3. 使用 QPainterPath 构造圆角矩形路径，并在一侧做出小尾巴（不同 role 的路径略有差异）。
        4. 使用 `painter.fillPath` 填充背景色，再用 `painter.drawPath` 绘制边框。
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(0, 0, -1, -1)
        radius = 24.0
        small = 6.0
        w = float(rect.width())
        h = float(rect.height())
        # Detect theme by walking up parents for a widget property 'theme'.
        # 这里通过查找父控件的 `theme` 属性来决定当前对话是否处于暗黑主题。
        # 这种方法允许在顶层容器（例如 Root 或 ChatView）上设置 theme 属性，子控件自动继承。
        theme = "default"
        parent = self.parent()
        while parent is not None:
            t = parent.property("theme")
            if t is not None:
                theme = t
                break
            parent = parent.parent()

        path = QPainterPath()
        if self.role == "user":
            path.moveTo(radius, 0)
            path.lineTo(w - radius, 0)
            path.quadTo(w, 0, w, radius)
            path.lineTo(w, h - small)
            path.quadTo(w, h, w - small, h)
            path.lineTo(radius, h)
            path.quadTo(0, h, 0, h - radius)
            path.lineTo(0, radius)
            path.quadTo(0, 0, radius, 0)
            # 用户消息气泡：根据主题调整填充与文字颜色，深色模式下使用更深的蓝色
            if theme == "dark":
                fill = QColor("#12314f")
                border = QColor("#1E6DFF")
                text_color = "#ffffff"
            else:
                fill = QColor("#1E6DFF")
                border = QColor("#1E6DFF")
                text_color = "#ffffff"
        else:
            path.moveTo(radius, 0)
            path.lineTo(w - radius, 0)
            path.quadTo(w, 0, w, radius)
            path.lineTo(w, h - radius)
            path.quadTo(w, h, w - radius, h)
            path.lineTo(small, h)
            path.quadTo(0, h, 0, h - small)
            path.lineTo(0, radius)
            path.quadTo(0, 0, radius, 0)
            # 助理消息气泡会根据主题调整：
            # - 暗色主题使用深色填充与较深的边框，保证与整体配色协调；
            # - 亮色主题使用白色填充和浅色边框，以便气泡看起来更接近卡片样式。
            if theme == "dark":
                fill = QColor("#17253c")
                border = QColor("#304d79")
                text_color = "#d9e7ff"
            else:
                fill = QColor("#ffffff")
                border = QColor("#e2edff")
                text_color = "#0f2b3f"

        painter.fillPath(path, fill)
        painter.setPen(QPen(border, 1))
        painter.drawPath(path)

        # Ensure bubble text color follows chosen text color (overrides QSS if needed)
        try:
            label = self.findChild(QLabel, "BubbleText")
            if label is not None:
                label.setStyleSheet(f"color: {text_color};")
        except Exception:
            pass


class MessageBubble(QWidget):
    """Message row with bubble text and metadata."""

    def __init__(self, role: str, content: str) -> None:
        super().__init__()
        # 设置 objectName，QSS 使用这些名字来选择不同消息行的样式（例如文本颜色、内边距等）
        self.setObjectName("UserMessage" if role == "user" else "AssistantMessage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 气泡容器：`BubbleFrame` 负责真实绘制；这里的 `objectName` 对应 QSS 中的 `#UserBubble` / `#AssistantBubble`
        bubble = BubbleFrame(role)
        bubble.setObjectName("UserBubble" if role == "user" else "AssistantBubble")
        bubble_layout = QVBoxLayout(bubble)
        # 内边距决定文本与气泡边缘的间隔（左右 18px，上下 12px），与设计稿保持一致
        bubble_layout.setContentsMargins(18, 12, 18, 12)
        bubble_layout.setSpacing(0)

        # 文本标签：`BubbleText` 在 QSS 中控制字体颜色与行高等样式
        text_label = QLabel(content)
        text_label.setObjectName("BubbleText")
        text_label.setWordWrap(True)
        # 允许通过鼠标选择文字，便于复制
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        # 宽度计算：基于最长行的像素宽度来设置目标宽度，避免过窄或过宽的气泡
        # - `horizontalAdvance` 计算文字像素宽度，+44 为左右内边距与额外空间的保留
        # - 限制在 [120, 860] 之间以保持视觉一致性
        longest_line = max(content.splitlines() or [content], key=len)
        target_width = min(860, max(120, text_label.fontMetrics().horizontalAdvance(longest_line) + 44))
        # 这里对 text_label 的 min/max 宽度做细微限制，避免布局抖动
        text_label.setMinimumWidth(target_width - 36)
        text_label.setMaximumWidth(884)
        bubble_layout.addWidget(text_label)

        # 气泡本身的宽度设置：确保外层气泡稍微比文本宽以保留内边距
        bubble.setMinimumWidth(target_width)
        bubble.setMaximumWidth(920)
        bubble.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        # 元信息（作者名 + 时间）：`MessageMeta` 在 QSS 中使用较小字号和次要颜色显示
        meta_name = "我" if role == "user" else "J-Mate"
        meta = QLabel(f"{meta_name} · {QDateTime.currentDateTime().toString('hh:mm')}")
        meta.setObjectName("MessageMeta")
        # 用户消息将时间靠右显示，助理消息靠左显示，与聊天对齐规则一致
        meta.setAlignment(Qt.AlignmentFlag.AlignRight if role == "user" else Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(bubble)
        layout.addWidget(meta)
        self.setMaximumWidth(940)
