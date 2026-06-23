"""本地文件型 Skill 的脚本执行入口。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from agent_framework import FileSkill, FileSkillScript


def subprocess_script_runner(
    skill: FileSkill,
    script: FileSkillScript,
    args: dict[str, Any] | list[str] | None = None,
) -> str:
    """以子进程执行 Skill 脚本，并返回标准输出和错误输出。

    第一阶段保持后端示例的执行方式，方便源码环境验证。PyInstaller
    onefile 模式不能把 JMate.exe 当作 Python 解释器，打包适配将在后续
    步骤单独处理，避免现在影响原有程序。
    """
    script_path = Path(script.full_path)
    if not script_path.is_file():
        return f"错误：未找到 Skill 脚本：{script_path}"

    if args is not None and not isinstance(args, list):
        raise TypeError("文件型 Skill 的脚本参数必须是字符串列表")

    command = [sys.executable, str(script_path)]
    for item in args or []:
        if not isinstance(item, str):
            raise TypeError("文件型 Skill 的每个脚本参数都必须是字符串")
        command.append(item)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=700,
            cwd=str(script_path.parent),
        )
    except subprocess.TimeoutExpired:
        return f"错误：Skill 脚本 {script.name} 执行超时"
    except OSError as exc:
        return f"错误：Skill 脚本 {script.name} 启动失败：{exc}"

    output = result.stdout
    if result.stderr:
        output += f"\n错误输出：\n{result.stderr}"
    if result.returncode != 0:
        output += f"\n脚本退出码：{result.returncode}"
    return output.strip() or "（脚本没有输出）"


# 兼容前一阶段接入时使用的名称，后续代码统一使用后端示例中的名称。
skill_script_runner = subprocess_script_runner
