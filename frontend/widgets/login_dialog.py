"""登录弹窗。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from app.state import AppState
from app.theme_tokens import tokens_for_theme
from services.auth_service import AuthService


class LoginDialog(QDialog):
    """启动时显示的 JMate 登录卡片。"""

    def __init__(self, state: AppState, parent=None, auth_service: AuthService | None = None) -> None:
        super().__init__(parent)
        self.state = state
        self.auth_service = auth_service or AuthService()
        self.setWindowTitle("AI办公助手登录")
        self.setObjectName("LoginDialog")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self._apply_responsive_metrics(parent)
        self.setProperty("theme", self.state.theme)
        self.state.theme_changed.connect(lambda value: self.setProperty("theme", value))
        self.state.theme_changed.connect(self._apply_theme)
        self._build_ui()
        self._apply_theme(self.state.theme)

    def _apply_responsive_metrics(self, parent) -> None:
        """按父窗口或屏幕比例计算登录卡片尺寸和字体。"""
        if parent is not None:
            base_width = max(parent.width(), 900)
            base_height = max(parent.height(), 620)
        else:
            screen = QApplication.primaryScreen()
            available = screen.availableGeometry() if screen is not None else None
            base_width = available.width() if available is not None else 1100
            base_height = available.height() if available is not None else 760

        width = max(420, min(560, int(base_width * 0.42)))
        height = max(360, min(470, int(base_height * 0.50)))
        self.setFixedSize(width, height)

        scale = min(width / 420, height / 360)
        self._metrics = {
            "margin_x": int(22 * scale),
            "margin_top": int(18 * scale),
            "margin_bottom": int(22 * scale),
            "spacing": int(10 * scale),
            "close": int(32 * scale),
            "title_font": int(21 * scale),
            "label_font": int(14 * scale),
            "input_font": int(14 * scale),
            "error_font": int(13 * scale),
            "button_font": int(16 * scale),
            "input_height": int(40 * scale),
            "button_height": int(44 * scale),
            "radius": int(12 * scale),
            "card_radius": int(20 * scale),
            "input_padding_y": int(5 * scale),
            "input_padding_x": int(12 * scale),
        }

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            self._metrics["margin_x"],
            self._metrics["margin_top"],
            self._metrics["margin_x"],
            self._metrics["margin_bottom"],
        )
        layout.setSpacing(self._metrics["spacing"])

        top = QHBoxLayout()
        top.addStretch(1)
        close_button = QPushButton("×")
        close_button.setObjectName("LoginCloseButton")
        close_button.setFixedSize(self._metrics["close"], self._metrics["close"])
        close_button.setToolTip("退出程序")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.reject)
        top.addWidget(close_button)

        title = QLabel("AI办公助手登录")
        title.setObjectName("LoginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.member_id = QLineEdit()
        self.member_id.setObjectName("LoginInput")
        self.member_id.setMinimumHeight(self._metrics["input_height"])
        self.member_id.setMaxLength(8)
        self.member_id.setPlaceholderText("固定8位，例如：12345678")
        self.member_id.textChanged.connect(self._normalize_member_id)
        self.member_id.returnPressed.connect(self._do_login)

        self.password = QLineEdit()
        self.password.setObjectName("LoginInput")
        self.password.setMinimumHeight(self._metrics["input_height"])
        self.password.setPlaceholderText("可不填写")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.returnPressed.connect(self._do_login)

        self.remember = QCheckBox("保持登录")
        self.remember.setObjectName("LoginRemember")
        self.remember.setChecked(True)

        self.error_label = QLabel("")
        self.error_label.setObjectName("LoginError")
        self.error_label.setWordWrap(True)

        login_button = QPushButton("登录")
        login_button.setObjectName("LoginButton")
        login_button.setMinimumHeight(self._metrics["button_height"])
        login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        login_button.clicked.connect(self._do_login)

        layout.addLayout(top)
        layout.addWidget(title)
        layout.addWidget(self._field_label("社员号"))
        layout.addWidget(self.member_id)
        layout.addWidget(self._field_label("密码"))
        layout.addWidget(self.password)
        layout.addWidget(self.remember)
        layout.addWidget(self.error_label)
        layout.addWidget(login_button)

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("LoginLabel")
        return label

    def _normalize_member_id(self, value: str) -> None:
        digits = "".join(ch for ch in value if ch.isdigit())[:8]
        if digits != value:
            self.member_id.setText(digits)
        if self.error_label.text():
            self.error_label.setText("")

    def _do_login(self) -> None:
        member_id = self.member_id.text().strip()
        if len(member_id) != 8 or not member_id.isdigit():
            self.error_label.setText("社员号格式不正确，请输入8位数字。")
            self.member_id.setFocus()
            return

        response = self.auth_service.login(username=member_id, password=self.password.text())
        if not response.success:
            self.error_label.setText(response.message or "登录失败，请重试。")
            return

        self.state.user_name = response.user_name or member_id
        self.state.logged_in = True
        self.accept()

    def _apply_theme(self, theme: str) -> None:
        token = tokens_for_theme(theme).login_dialog
        self.setStyleSheet(f"""
        QDialog#LoginDialog {{
            background: {token.background};
            border: 1px solid #cddff7;
            border-radius: {self._metrics["card_radius"]}px;
        }}
        QLabel#LoginTitle {{
            color: {token.title};
            font-size: {self._metrics["title_font"]}px;
            font-weight: 700;
        }}
        QLabel#LoginLabel, QCheckBox#LoginRemember {{
            color: {token.text};
            font-size: {self._metrics["label_font"]}px;
        }}
        QLabel#LoginError {{
            color: {token.error};
            font-size: {self._metrics["error_font"]}px;
            min-height: {int(self._metrics["error_font"] * 1.6)}px;
        }}
        QLineEdit#LoginInput {{
            color: {token.text};
            border: 1px solid #bfd5f6;
            border-radius: {self._metrics["radius"]}px;
            padding: {self._metrics["input_padding_y"]}px {self._metrics["input_padding_x"]}px;
            background: #ffffff;
            font-size: {self._metrics["input_font"]}px;
        }}
        QPushButton#LoginButton {{
            background: #1E6DFF;
            color: #ffffff;
            border: none;
            border-radius: {self._metrics["radius"]}px;
            min-height: {self._metrics["button_height"]}px;
            font-size: {self._metrics["button_font"]}px;
            font-weight: 700;
        }}
        QPushButton#LoginCloseButton {{
            background: transparent;
            color: #2d5a94;
            border: none;
            border-radius: {int(self._metrics["radius"] * 0.8)}px;
            font-size: {self._metrics["title_font"]}px;
        }}
        QPushButton#LoginCloseButton:hover {{
            background: rgba(225, 59, 59, 0.16);
            color: #b42318;
        }}
        """)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
