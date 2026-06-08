"""后端 mock 回复规则。

这个模块只保存演示阶段的固定回复和匹配规则，不依赖 PySide6。
后续接入真实 Agent 时，可以删除或替换这里，而不影响前端组件。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MockReplyRule:
    """一条 mock 回复规则。

    skill_id 用于匹配用户当前激活的技能，keywords 用于在未选技能时按输入文本兜底匹配。
    """

    skill_id: str
    keywords: tuple[str, ...]
    reply: str


# 演示回复规则：当前只是固定文本，后续可以替换成真实 Agent 的工具调用或 API 结果。
MOCK_REPLY_RULES = (
    MockReplyRule(
        skill_id="email",
        keywords=("考勤",),
        reply=(
            "⏰ 月末考勤助手\n"
            "已为你生成考勤核对示例：本月出勤记录待确认，异常打卡 2 条，"
            "建议先核对外勤和补卡记录。"
        ),
    ),
    MockReplyRule(
        skill_id="summary",
        keywords=("休假", "请假"),
        reply=(
            "📄 休假申请助手\n"
            "示例申请已生成：申请人、休假类型、起止时间与交接说明已预留字段，"
            "可以继续补充具体日期。"
        ),
    ),
    MockReplyRule(
        skill_id="schedule",
        keywords=("加班",),
        reply=(
            "⏱ 加班申请助手\n"
            "已生成加班申请草稿：加班事由、预计时长、项目关联和审批备注均为前端占位展示。"
        ),
    ),
    MockReplyRule(
        skill_id="report",
        keywords=("填写", "周报"),
        reply=(
            "📊 智能考勤填写\n"
            "【本周重点工作】\n"
            "1. 完成需求分析与技术方案设计，输出文档 2 份\n"
            "2. 修复线上故障 3 处，优化接口响应速度 12%\n"
            "3. 协同跨部门推进项目里程碑\n"
            "【下周计划】核心功能开发与联调、用户反馈收集与迭代规划。"
        ),
    ),
)


def match_mock_reply(text: str, active_skill_id: str | None, active_skill_name: str) -> str:
    """根据技能 id 和输入文本返回一条演示回复。

    这里保留 mock 行为只是为了前端调试时有稳定输出；真实业务接入后应替换为 Agent 调用。
    """
    for rule in MOCK_REPLY_RULES:
        if active_skill_id == rule.skill_id or any(keyword in text for keyword in rule.keywords):
            return rule.reply

    return (
        f"✅ J-Mate 办公智能引擎（当前技能：{active_skill_name}）\n"
        f"已收到你的指令：“{text}”。这里是后端 mock 回复，尚未调用真实模型或智能体。"
    )

