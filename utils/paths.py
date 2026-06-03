"""Resource path helpers.

Handles normal filesystem layout and PyInstaller (_MEIPASS) runtime.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# When packaged with PyInstaller, bundled files are extracted to sys._MEIPASS.
if getattr(sys, "_MEIPASS", None):
    RESOURCES_DIR = Path(sys._MEIPASS) / "resources"
else:
    RESOURCES_DIR = PROJECT_ROOT / "resources"


def resource_path(*parts: str) -> Path:
    """Return an absolute path under the resources directory."""
    return RESOURCES_DIR.joinpath(*parts)
