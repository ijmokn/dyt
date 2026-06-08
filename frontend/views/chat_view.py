"""Main J-Mate conversation view."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from app.constants import CLEAR_MESSAGE, ERROR_MESSAGE, LOADING_MESSAGE, WELCOME_MESSAGE
from app.state import AppState
from services.chat_service import ChatService
from widgets.input_bar import InputBar
from widgets.message_bubble import MessageBubble
from widgets.skill_chip import SkillChip


class ChatView(QWidget):
    """Skills row, conversation stream, and input area."""

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self.chat_service = ChatService()
        self.skill_buttons: dict[str, SkillChip] = {}
        self.setObjectName("ChatView")
        self._build_ui()
        self.refresh_from_state()
        self._show_welcome()

    def _build_ui(self) -> None:
        """Compose all sections from the HTML layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        skills_section = QFrame()
        skills_section.setObjectName("SkillsSection")
        skills_layout = QVBoxLayout(skills_section)
        skills_layout.setContentsMargins(28, 16, 28, 8)
        skills_layout.setSpacing(12)

        label = QLabel("🔵 Skills（点击启用）")
        label.setObjectName("SkillsLabel")

        self.skills_grid = QHBoxLayout()
        self.skills_grid.setSpacing(12)
        self.skills_grid.addStretch(1)

        skills_layout.addWidget(label)
        skills_layout.addLayout(self.skills_grid)

        self.messages_widget = QWidget()
        self.messages_widget.setObjectName("MessagesWidget")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(28, 20, 28, 20)
        self.messages_layout.setSpacing(16)
        self.messages_layout.addStretch(1)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("ConversationArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidget(self.messages_widget)

        self.input_bar = InputBar()
        self.input_bar.send_requested.connect(self._handle_send)
        self.input_bar.clear_requested.connect(self._clear_conversation)

        layout.addWidget(skills_section)
        layout.addWidget(self.scroll_area, stretch=1)
        layout.addWidget(self.input_bar)

    def refresh_from_state(self) -> None:
        """Refresh visible skill chips and input behavior from shared state."""
        self.input_bar.set_enter_to_send(self.state.enter_to_send)
        self._render_skill_chips()
        self.setProperty("theme", self.state.theme)
        self.style().unpolish(self)
        self.style().polish(self)

    def _render_skill_chips(self) -> None:
        """Rebuild chip row from enabled skills."""
        while self.skills_grid.count() > 1:
            item = self.skills_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.skill_buttons.clear()
        for skill in self.state.enabled_skills():
            chip = SkillChip(skill)
            chip.setChecked(skill.id == self.state.active_skill_id)
            chip.toggled_skill.connect(self._toggle_skill)
            self.skill_buttons[skill.id] = chip
            self.skills_grid.insertWidget(self.skills_grid.count() - 1, chip)

    def _toggle_skill(self, skill_id: str) -> None:
        """Select or clear the active skill."""
        if self.state.active_skill_id == skill_id:
            self.state.active_skill_id = None
            self._add_message("assistant", "已取消技能选中，将使用通用智能模式。")
        else:
            self.state.active_skill_id = skill_id
            self._add_message("assistant", f"已激活技能：{self.state.active_skill_name()}，您的下一段指令将优先使用此技能。")
        self._render_skill_chips()

    def _show_welcome(self) -> None:
        """Add the default assistant greeting."""
        self._add_message(
            "assistant",
            WELCOME_MESSAGE,
        )

    def _handle_send(self, text: str) -> None:
        """Append user message and a delayed static response."""
        self._add_message("user", text)
        self._add_message("assistant", LOADING_MESSAGE)
        # Use the service layer asynchronously; replace temporary bubble when done.
        def _on_reply(reply_text: str) -> None:
            QTimer.singleShot(0, lambda: self._replace_last_assistant_message(reply_text))

        def _on_error(exc: Exception) -> None:
            QTimer.singleShot(0, lambda: self._replace_last_assistant_message(ERROR_MESSAGE))

        self.chat_service.get_reply_async(text, self.state.active_skill_id, self.state.active_skill_name(), _on_reply, _on_error)

    def _clear_conversation(self) -> None:
        """Clear all bubbles and restore a friendly assistant message."""
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._add_message("assistant", CLEAR_MESSAGE)

    def _add_message(self, role: str, text: str) -> None:
        """Insert one bubble above the bottom stretch."""
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        bubble = MessageBubble(role, text)
        if role == "user":
            row.addStretch(1)
            row.addWidget(bubble, stretch=0)
        else:
            row.addWidget(bubble, stretch=0)
            row.addStretch(1)

        wrapper = QWidget()
        wrapper.setLayout(row)
        insert_at = max(0, self.messages_layout.count() - 1)
        self.messages_layout.insertWidget(insert_at, wrapper)
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _replace_last_assistant_message(self, text: str) -> None:
        """Replace the temporary loading bubble with a static reply."""
        if self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(self.messages_layout.count() - 2)
            if item.widget():
                item.widget().deleteLater()
        self._add_message("assistant", text)

    def _scroll_to_bottom(self) -> None:
        """Keep the newest message visible."""
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())
