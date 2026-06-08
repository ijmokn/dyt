"""
技能按钮组件。
这个控件只负责把 shared.skill_catalog.Skill 渲染成可点击的技能按钮。
选中/取消后的业务含义由 ChatView 和 AppState 处理。
"""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QPushButton

from shared.skill_catalog import Skill


class SkillChip(QPushButton):
    """主界面顶部的胶囊形技能按钮。"""

    toggled_skill = Signal(str)

    def __init__(self, skill: Skill) -> None:
        super().__init__(f"{skill.icon}  {skill.name}")
        self.skill = skill
        self.setObjectName("SkillChip")
        self.setCheckable(True)
        self.setToolTip(skill.description)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(lambda: self.toggled_skill.emit(skill.id))
