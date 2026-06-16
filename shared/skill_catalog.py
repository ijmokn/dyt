"""技能目录。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    """单个技能的展示与路由元数据。"""

    id: str
    icon: str
    name: str
    description: str
    prompt_hint: str


DEFAULT_SKILLS = [
    Skill("email", "📧", "邮件助手", "邮件起草与润色", "邮件"),
    Skill("summary", "🧾", "内容总结", "纪要提炼与摘要", "总结"),
    Skill("schedule", "📅", "日程安排", "会议与计划安排", "日程"),
    Skill("report", "📊", "周报生成", "周报与汇报整理", "周报"),
    Skill("brainstorm", "💡", "头脑风暴", "创意扩展与方案发散", "创意"),
    Skill("translate", "🌐", "双语翻译", "中英翻译与润色", "翻译"),
]
