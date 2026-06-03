"""Shared UI state and static frontend data.

This module exposes `DEFAULT_SKILLS` and `AppState`.
`AppState` is a Qt `QObject` that emits signals when key fields change,
so UI components can react without directly polling attributes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Set

from PySide6.QtCore import QObject, Signal


@dataclass(frozen=True)
class Skill:
    """Display data for a skill chip."""

    id: str
    icon: str
    name: str
    description: str
    prompt_hint: str


DEFAULT_SKILLS = [
    Skill("email", "⏰", "月末考勤", "考勤核对与月末统计", "查询考勤"),
    Skill("summary", "📄", "休假申请", "休假制度说明与申请辅助", "休假申请"),
    Skill("schedule", "⏱", "加班申请", "加班安排与申请流程", "加班申请"),
    Skill("report", "📊", "考勤填写", "考勤补录与填写指导", "考勤填写"),
]


class AppState(QObject):
    """Runtime-only state for the frontend demo with change signals.

    Attributes are exposed as Python properties so existing code that reads
    or assigns `state.theme` / `state.active_skill_id` continues to work.
    """

    theme_changed = Signal(str)
    font_size_changed = Signal(str)
    enter_to_send_changed = Signal(bool)
    active_skill_changed = Signal(object)
    enabled_skill_ids_changed = Signal(object)
    logged_in_changed = Signal(bool)
    user_name_changed = Signal(object)
    # emitted when any anchor sizing/configuration changes
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

        # anchor sizing configuration (ratios derived from reference 1100x760 window)
        self._anchor_width_ratio: float = 38 / 1100
        self._anchor_height_ratio: float = 38 / 760
        self._anchor_min_size: int = 28
        self._anchor_max_size: int = 56
        # font size as ratio of anchor size
        self._anchor_font_ratio: float = 0.28

    # Anchor sizing configuration
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
        """Return skill objects that should be visible in the chip row."""
        return [skill for skill in DEFAULT_SKILLS if skill.id in self._enabled_skill_ids]

    def active_skill_name(self) -> str:
        """Return the selected skill name or the generic assistant label."""
        for skill in DEFAULT_SKILLS:
            if skill.id == self._active_skill_id:
                return skill.name
        return "通用助手"
