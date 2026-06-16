"""前端主题与尺寸 token。

集中管理 Python 代码里需要动态拼接 QSS 的颜色、圆角和基础尺寸。
QSS 文件仍然负责大部分静态样式；只有登录弹窗、用户弹窗、登录入口这类
需要根据运行时主题即时更新的控件，从这里读取 token。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoginAnchorTokens:
    """左下角登录入口按钮的主题颜色。"""

    background: str
    border: str
    text: str
    hover_background: str


@dataclass(frozen=True)
class LoginDialogTokens:
    """登录弹窗的主题颜色。"""

    background: str
    title: str
    text: str
    error: str


@dataclass(frozen=True)
class UserPopupTokens:
    """登录后用户信息弹窗的主题颜色。"""

    background: str
    border: str
    text: str
    button_background: str
    button_border: str


@dataclass(frozen=True)
class ThemeTokens:
    """一个主题下所有 Python 动态样式 token。"""

    login_anchor: LoginAnchorTokens
    login_dialog: LoginDialogTokens
    user_popup: UserPopupTokens


# 窗口与控件基础尺寸。数值保持现有界面不变，只把散落的硬编码集中起来。
WINDOW_INITIAL_SIZE = (1100, 760)
WINDOW_MINIMUM_SIZE = (900, 620)
LOGIN_DIALOG_SIZE = (420, 330)
LOGIN_FEEDBACK_DIALOG_SIZE = (360, 180)
USER_POPUP_BASE_SIZE = (240, 120)
USER_POPUP_MIN_SIZE = (220, 112)
USER_POPUP_MAX_SIZE = (320, 160)

# 左下角登录入口按钮比例，来源于 1100x760 参考窗口中的 38x38 按钮。
LOGIN_ANCHOR_BASE_SIZE = 38
LOGIN_ANCHOR_WIDTH_RATIO = LOGIN_ANCHOR_BASE_SIZE / WINDOW_INITIAL_SIZE[0]
LOGIN_ANCHOR_HEIGHT_RATIO = LOGIN_ANCHOR_BASE_SIZE / WINDOW_INITIAL_SIZE[1]
LOGIN_ANCHOR_MIN_SIZE = 28
LOGIN_ANCHOR_MAX_SIZE = 56
LOGIN_ANCHOR_FONT_RATIO = 0.28

# 应用字号档位，设置页修改字号后由 MainWindow 统一应用到 QApplication。
FONT_POINT_SIZES = {
    "small": 9,
    "medium": 10,
    "large": 12,
}


LIGHT_THEME = ThemeTokens(
    login_anchor=LoginAnchorTokens(
        background="#ffffff",
        border="#d4e3fb",
        text="#163a73",
        hover_background="#eff6ff",
    ),
    login_dialog=LoginDialogTokens(
        background="#ffffff",
        title="#174381",
        text="#12283b",
        error="#b42318",
    ),
    user_popup=UserPopupTokens(
        background="#ffffff",
        border="#d4e3fb",
        text="#12283b",
        button_background="#ffffff",
        button_border="#e5e7eb",
    ),
)


DARK_THEME = ThemeTokens(
    login_anchor=LoginAnchorTokens(
        background="rgba(19,29,47,0.96)",
        border="rgba(85,120,177,0.34)",
        text="#d9e7ff",
        hover_background="rgba(30,109,255,0.22)",
    ),
    login_dialog=LoginDialogTokens(
        background="rgba(19,29,47,0.96)",
        title="#d9e7ff",
        text="#d9e7ff",
        error="#ffb4ab",
    ),
    user_popup=UserPopupTokens(
        background="rgba(19,29,47,0.96)",
        border="rgba(85,120,177,0.34)",
        text="#d9e7ff",
        button_background="rgba(25,39,63,0.96)",
        button_border="rgba(85,120,177,0.42)",
    ),
)


def tokens_for_theme(theme: str) -> ThemeTokens:
    """根据当前主题名称返回对应 token。

    当前只有 dark 使用深色 token；default/light/business 等浅色主题共用浅色 token。
    """
    if theme == "dark":
        return DARK_THEME
    return LIGHT_THEME
