"""
登录弹窗。
这个窗口只负责收集用户名和密码，并把登录请求交给前端 AuthService。
认证规则、第三方 API、Microsoft 登录等后续都应该放到后端服务里，
不要直接写在 UI 控件中。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app.state import AppState
from app.theme_tokens import LOGIN_DIALOG_SIZE, tokens_for_theme
from services.auth_service import AuthService
from widgets.login_feedback_dialog import LoginFeedbackDialog


class LoginDialog(QDialog):
    """前端登录界面，调用 AuthService 完成认证。"""

    def __init__(self, state: AppState, parent=None, auth_service: AuthService | None = None) -> None:
        super().__init__(parent)
        self.state = state
        self.auth_service = auth_service or AuthService()
        self.setWindowTitle("登录")
        self.setObjectName("LoginDialog")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(*LOGIN_DIALOG_SIZE)

        # 主题只影响显示，不参与登录业务逻辑。
        self.setProperty("theme", self.state.theme)
        self.state.theme_changed.connect(lambda value: self.setProperty("theme", value))
        self.state.theme_changed.connect(self._apply_theme)
        self._apply_theme(self.state.theme)
        self._build_ui()

    def _build_ui(self) -> None:
        """创建登录表单和操作按钮。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel("登录")
        title.setObjectName("LoginTitle")
        close_button = QPushButton("关闭")
        close_button.setObjectName("CloseSettingsButton")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.reject)
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(close_button)
        layout.addLayout(top)

        form = QFormLayout()
        self.username = QLineEdit()
        self.username.setPlaceholderText("用户名")
        self.password = QLineEdit()
        self.password.setPlaceholderText("密码")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow(QLabel("用户名"), self.username)
        form.addRow(QLabel("密码"), self.password)

        self.error_label = QLabel("")
        self.error_label.setObjectName("LoginError")
        self.error_label.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("登录")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self._do_login)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

    def _do_login(self) -> None:
        """调用登录接口，并根据返回结果更新前端状态。"""
        response = self.auth_service.login(
            username=self.username.text().strip(),
            password=self.password.text(),
        )
        if not response.success:
            message = response.message or "用户名或密码不正确，请重新输入。"
            self.error_label.setText(message)
            LoginFeedbackDialog(
                state=self.state,
                title="登录失败",
                message=message,
                success=False,
                parent=self,
            ).exec()
            return

        # 前端只保存展示所需的登录状态；真正 token/第三方会话由后端管理。
        self.state.user_name = response.user_name
        self.state.logged_in = True
        LoginFeedbackDialog(
            state=self.state,
            title="登录成功",
            message=f"欢迎回来，{response.user_name or '用户'}。",
            success=True,
            parent=self,
        ).exec()
        self.accept()

    def _apply_theme(self, theme: str) -> None:
        """应用登录弹窗的浅色/深色样式。"""
        token = tokens_for_theme(theme).login_dialog

        qss = f"""
        QDialog#LoginDialog {{
            background: {token.background};
        }}
        QLabel#LoginTitle {{
            color: {token.title};
            font-size: 16px;
            font-weight: 600;
        }}
        QLabel#LoginError {{
            color: {token.error};
            min-height: 18px;
        }}
        QLineEdit {{
            color: {token.text};
        }}
        """
        self.setStyleSheet(qss)

    def keyPressEvent(self, event) -> None:
        """Esc 关闭登录弹窗。"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
