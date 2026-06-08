"""技能目录。

描述系统支持哪些技能，不依赖 PySide6，也不包含界面逻辑。
前端用它渲染按钮和设置项，后端或 Agent 层后续也可以用同一批技能 id 做路由。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    """单个技能的展示与路由元数据。

    id 用于前后端协议和后端路由，icon/name/description/prompt_hint 用于前端展示。
    """

    id: str
    icon: str
    name: str
    description: str
    prompt_hint: str


# 默认技能列表：前端设置页、主界面技能按钮和后端 mock 回复都应优先复用这里的 id。
DEFAULT_SKILLS = [
    Skill("email", "⏰", "月末考勤", "考勤核对与月末统计", "查询考勤"),
    Skill("summary", "📄", "休假申请", "休假制度说明与申请辅助", "休假申请"),
    Skill("schedule", "⏱", "加班申请", "加班安排与申请流程", "加班申请"),
    Skill("report", "📊", "考勤填写", "考勤补录与填写指导", "考勤填写"),
]

