"""Main J-Mate conversation view."""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from app.constants import CLEAR_MESSAGE, ERROR_MESSAGE, LOADING_MESSAGE, WELCOME_MESSAGE
from app.state import AppState
from frontend.services.chat_service import ChatService
from widgets.input_bar import InputBar
from widgets.message_bubble import MessageBubble


class ChatView(QWidget):
    """Conversation stream and input area."""

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self.chat_service = ChatService()
        self.setObjectName("ChatView")
        self._build_ui()
        self.refresh_from_state()
        self._show_welcome()

    def _build_ui(self) -> None:
        """Compose the conversation area and input area."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

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

        layout.addWidget(self.scroll_area, stretch=1)
        layout.addWidget(self.input_bar)

    def refresh_from_state(self) -> None:
        """Refresh input behavior and visual theme from shared state."""
        self.input_bar.set_enter_to_send(self.state.enter_to_send)
        self.input_bar.set_skills_enabled(self.state.skills_enabled)
        self.setProperty("theme", self.state.theme)
        self.style().unpolish(self)
        self.style().polish(self)

    def _show_welcome(self) -> None:
        """Add the default assistant greeting."""
        self._add_message("assistant", WELCOME_MESSAGE)

    def _handle_send(self, text: str) -> None:
        """Append user message and ask the service for a reply."""
        self._add_message("user", text)
        self._add_message("assistant", LOADING_MESSAGE)

        def _on_reply(reply_text: str) -> None:
            QTimer.singleShot(0, lambda: self._replace_last_assistant_message(reply_text))

        def _on_error(exc: Exception) -> None:
            QTimer.singleShot(0, lambda: self._replace_last_assistant_message(ERROR_MESSAGE))

        active_skill_id = self.state.active_skill_id if self.state.skills_enabled else None
        active_skill_name = self.state.active_skill_name() if self.state.skills_enabled else "通用助手"
        self.chat_service.get_reply_async(text, active_skill_id, active_skill_name, _on_reply, _on_error)

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
