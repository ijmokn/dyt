"""前端运行时状态。

这个模块只负责保存桌面界面当前状态，例如主题、字号、启用技能、登录状态等。
技能目录本身放在 shared.skill_catalog 中，避免前端和后端各维护一份技能定义。
"""

from __future__ import annotations

from typing import Optional, Set

from PySide6.QtCore import QObject, Signal

from app.theme_tokens import (
    LOGIN_ANCHOR_FONT_RATIO,
    LOGIN_ANCHOR_HEIGHT_RATIO,
    LOGIN_ANCHOR_MAX_SIZE,
    LOGIN_ANCHOR_MIN_SIZE,
    LOGIN_ANCHOR_WIDTH_RATIO,
)
from shared.skill_catalog import DEFAULT_SKILLS, Skill


class AppState(QObject):
    """前端运行期状态容器。

    这里用 Qt Signal 通知界面刷新，避免各个组件互相直接操作。
    例如设置页修改主题后，只需要更新 state.theme，相关界面会通过信号自行刷新。
    """

    theme_changed = Signal(str)
    font_size_changed = Signal(str)
    enter_to_send_changed = Signal(bool)
    active_skill_changed = Signal(object)
    enabled_skill_ids_changed = Signal(object)
    logged_in_changed = Signal(bool)
    user_name_changed = Signal(object)
    # 登录入口按钮尺寸配置发生变化时发出，用于重新定位左下角入口。
    anchor_config_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._theme: str = "default"
        self._font_size: str = "medium"
        self._enter_to_send: bool = True
        self._active_skill_id: Optional[str] = None
        self._enabled_skill_ids: Set[str] = {skill.id for skill in DEFAULT_SKILLS}
        self._logged_in: bool = False
        self._user_name: Optional[str] = None

        # 左下角登录入口按钮的比例配置，默认值来自 theme_tokens。
        self._anchor_width_ratio: float = LOGIN_ANCHOR_WIDTH_RATIO
        self._anchor_height_ratio: float = LOGIN_ANCHOR_HEIGHT_RATIO
        self._anchor_min_size: int = LOGIN_ANCHOR_MIN_SIZE
        self._anchor_max_size: int = LOGIN_ANCHOR_MAX_SIZE
        self._anchor_font_ratio: float = LOGIN_ANCHOR_FONT_RATIO

    # 登录入口按钮尺寸配置。
    @property
    def anchor_width_ratio(self) -> float:
        return self._anchor_width_ratio

    @anchor_width_ratio.setter
    def anchor_width_ratio(self, v: float) -> None:
        if v != self._anchor_width_ratio:
            self._anchor_width_ratio = float(v)
            self.anchor_config_changed.emit()

    @property
    def anchor_height_ratio(self) -> float:
        return self._anchor_height_ratio

    @anchor_height_ratio.setter
    def anchor_height_ratio(self, v: float) -> None:
        if v != self._anchor_height_ratio:
            self._anchor_height_ratio = float(v)
            self.anchor_config_changed.emit()

    @property
    def anchor_min_size(self) -> int:
        return int(self._anchor_min_size)

    @anchor_min_size.setter
    def anchor_min_size(self, v: int) -> None:
        if v != self._anchor_min_size:
            self._anchor_min_size = int(v)
            self.anchor_config_changed.emit()

    @property
    def anchor_max_size(self) -> int:
        return int(self._anchor_max_size)

    @anchor_max_size.setter
    def anchor_max_size(self, v: int) -> None:
        if v != self._anchor_max_size:
            self._anchor_max_size = int(v)
            self.anchor_config_changed.emit()

    @property
    def anchor_font_ratio(self) -> float:
        return float(self._anchor_font_ratio)

    @anchor_font_ratio.setter
    def anchor_font_ratio(self, v: float) -> None:
        if v != self._anchor_font_ratio:
            self._anchor_font_ratio = float(v)
            self.anchor_config_changed.emit()

    # theme
    @property
    def theme(self) -> str:
        return self._theme

    @theme.setter
    def theme(self, value: str) -> None:
        if value != self._theme:
            self._theme = value
            self.theme_changed.emit(value)

    # font_size
    @property
    def font_size(self) -> str:
        return self._font_size

    @font_size.setter
    def font_size(self, value: str) -> None:
        if value != self._font_size:
            self._font_size = value
            self.font_size_changed.emit(value)

    # enter_to_send
    @property
    def enter_to_send(self) -> bool:
        return self._enter_to_send

    @enter_to_send.setter
    def enter_to_send(self, value: bool) -> None:
        if value != self._enter_to_send:
            self._enter_to_send = value
            self.enter_to_send_changed.emit(value)

    # active skill
    @property
    def active_skill_id(self) -> Optional[str]:
        return self._active_skill_id

    @active_skill_id.setter
    def active_skill_id(self, value: Optional[str]) -> None:
        if value != self._active_skill_id:
            self._active_skill_id = value
            self.active_skill_changed.emit(value)

    # enabled skills
    @property
    def enabled_skill_ids(self) -> Set[str]:
        return set(self._enabled_skill_ids)

    @enabled_skill_ids.setter
    def enabled_skill_ids(self, value: Set[str]) -> None:
        if set(value) != self._enabled_skill_ids:
            self._enabled_skill_ids = set(value)
            self.enabled_skill_ids_changed.emit(self.enabled_skill_ids)

    # login state
    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @logged_in.setter
    def logged_in(self, value: bool) -> None:
        if value != self._logged_in:
            self._logged_in = value
            self.logged_in_changed.emit(value)

    @property
    def user_name(self) -> Optional[str]:
        return self._user_name

    @user_name.setter
    def user_name(self, value: Optional[str]) -> None:
        if value != self._user_name:
            self._user_name = value
            self.user_name_changed.emit(value)

    def enabled_skills(self) -> list[Skill]:
        """返回当前应该显示在主界面技能栏中的技能列表。"""
        return [skill for skill in DEFAULT_SKILLS if skill.id in self._enabled_skill_ids]

    def active_skill_name(self) -> str:
        """返回当前激活技能名称；没有激活技能时返回通用助手名称。"""
        for skill in DEFAULT_SKILLS:
            if skill.id == self._active_skill_id:
                return skill.name
        return "通用助手"
