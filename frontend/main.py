"""Entry point for the J-Mate PySide6 desktop frontend."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.constants import APP_NAME, APP_ORGANIZATION
from app.main_window import MainWindow
from app.theme import apply_theme
from backend.services.azure_agent import start_initialize_azure_agent_async
from backend.services.hub_agent import start_initialize_hub_agent_async


def configure_logging() -> None:
    """配置 JMate 日志：同时输出到后台控制台和本地日志文件。"""
    runtime_root = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else REPO_ROOT
    log_dir = runtime_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "jmate.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
        force=True,
    )


def main() -> int:
    """Create the Qt application and show the main window."""
    configure_logging()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION)

    base_font = QFont("Microsoft YaHei")
    base_font.setPointSize(10)
    app.setFont(base_font)

    apply_theme(app)

    # 程序启动时分别在后台初始化普通 Azure Agent 和带 Skills 的智能体，
    # 避免网络连接、身份认证及 Skill 扫描阻塞桌面窗口显示。
    start_initialize_hub_agent_async()
    start_initialize_azure_agent_async()


    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
