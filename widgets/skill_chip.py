"""Skill chip button."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QPushButton

from app.state import Skill


class SkillChip(QPushButton):
    """A pill-shaped selectable button for one skill."""

    toggled_skill = Signal(str)

    def __init__(self, skill: Skill) -> None:
        super().__init__(f"{skill.icon}  {skill.name}")
        self.skill = skill
        self.setObjectName("SkillChip")
        self.setCheckable(True)
        self.setToolTip(skill.description)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(lambda: self.toggled_skill.emit(skill.id))
