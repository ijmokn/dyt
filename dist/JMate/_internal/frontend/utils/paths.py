# """Resource path helpers.
#
# Handles normal filesystem layout and PyInstaller (_MEIPASS) runtime.
# """
#
# from __future__ import annotations
#
# import sys
# from pathlib import Path
#
#
# PROJECT_ROOT = Path(__file__).resolve().parents[1]
# # When packaged with PyInstaller, bundled files are extracted to sys._MEIPASS.
# if getattr(sys, "_MEIPASS", None):
#     RESOURCES_DIR = Path(sys._MEIPASS) / "resources"
# else:
#     RESOURCES_DIR = PROJECT_ROOT / "resources"
#
#
# def resource_path(*parts: str) -> Path:
#     """Return an absolute path under the resources directory."""
#     return RESOURCES_DIR.joinpath(*parts)
"""Resource path helpers.

Handles normal filesystem layout and PyInstaller (_MEIPASS) runtime.
"""

from __future__ import annotations

import sys
from pathlib import Path


# frontend/utils/paths.py
# parents[1] = frontend
FRONTEND_ROOT = Path(__file__).resolve().parents[1]

if getattr(sys, "_MEIPASS", None):
    # 打包后资源在 _internal/frontend/resources
    RESOURCES_DIR = Path(sys._MEIPASS) / "frontend" / "resources"
else:
    # 开发环境资源在 frontend/resources
    RESOURCES_DIR = FRONTEND_ROOT / "resources"


def resource_path(*parts: str) -> Path:
    """Return an absolute path under the resources directory."""
    return RESOURCES_DIR.joinpath(*parts)