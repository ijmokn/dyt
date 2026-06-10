"""项目统一启动入口。

开发、调试和后续打包时优先运行这个文件。它负责把 frontend 目录加入导入路径，
然后委托给 PySide6 前端入口启动应用。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


_DLL_DIR_HANDLES = []


def setup_dll_path() -> None:
    """为 PyInstaller 打包后的程序补充 DLL 搜索路径。"""
    if not getattr(sys, "frozen", False):
        return

    exe_dir = Path(sys.executable).resolve().parent
    internal_dir = Path(getattr(sys, "_MEIPASS", exe_dir / "_internal"))
    pyside6_dir = internal_dir / "PySide6"

    for dll_dir in (internal_dir, pyside6_dir):
        if dll_dir.exists():
            handle = os.add_dll_directory(str(dll_dir))
            _DLL_DIR_HANDLES.append(handle)

    # 额外兜底：把 _internal 加到 PATH 前面，防止部分 DLL 加载仍走 PATH
    os.environ["PATH"] = str(internal_dir) + os.pathsep + str(pyside6_dir) + os.pathsep + os.environ.get("PATH", "")


setup_dll_path()


if getattr(sys, "frozen", False):
    ROOT_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent / "_internal"))
else:
    ROOT_DIR = Path(__file__).resolve().parent

FRONTEND_DIR = ROOT_DIR / "frontend"

for path in (ROOT_DIR, FRONTEND_DIR):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from frontend.main import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())