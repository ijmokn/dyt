"""考勤相关系统账号配置读写服务。"""

from __future__ import annotations

import json
import shutil
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .crypto_service import decrypt_text, encrypt_text

CONFIG_FILE_NAME = "attendance-config.json"


class AttendanceConfigError(Exception):
    """配置文件读取或写入失败。"""


@dataclass
class AttendanceConfigLoadResult:
    """配置读取结果，供启动流程判断是否需要显示登录页。"""

    config: dict[str, Any]
    path: Path
    requires_login: bool
    error: str | None = None


def _app_root() -> Path:
    """返回源码根目录或 PyInstaller 解包目录。"""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[2]


def default_config_path() -> Path:
    """返回打包内置的默认配置模板路径。"""
    return _app_root() / CONFIG_FILE_NAME


def user_config_path() -> Path:
    """返回当前 Windows 用户目录下的配置文件路径。"""
    return Path.home() / CONFIG_FILE_NAME


def default_output_dir() -> str:
    """返回当前用户文档目录；不存在时退回用户目录。"""
    documents = Path.home() / "Documents"
    return str(documents if documents.exists() else Path.home())


def build_pjmn_username(member_id: str) -> str:
    """PJCOST 账号规则：去掉社员号倒数第 2 位。"""
    if len(member_id) < 2:
        return member_id
    return member_id[:-2] + member_id[-1:]


def _read_json(path: Path) -> dict[str, Any]:
    """读取 JSON 对象。"""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise AttendanceConfigError("配置文件根节点必须是 JSON 对象")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    """写入格式化 JSON。"""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _base_config() -> dict[str, Any]:
    """读取默认模板；模板缺失时使用内置兜底结构。"""
    path = default_config_path()
    if path.exists():
        return _read_json(path)

    return {
        "version": "1.0",
        "attendance": {
            "username": "",
            "password": "",
            "url": "http://adacodalian.ajis-group.com.cn/AdacoWeb/login",
        },
        "pjmn": {
            "username": "",
            "password": "",
            "url": "http://172.20.151.1/pjmn/",
        },
        "evection": {
            "username": "",
            "password": "",
            "url": "http://ajis-dlserver/EVECTION",
        },
        "common": {
            "outputDir": "",
            "waitMs": 7000,
            "position": "",
        },
    }


def _ensure_sections(config: dict[str, Any]) -> dict[str, Any]:
    """补齐缺失节点，并给 outputDir 填当前用户文档目录。"""
    merged = deepcopy(_base_config())
    for section in ("attendance", "pjmn", "evection", "common"):
        if isinstance(config.get(section), dict):
            merged[section].update(config[section])
    if isinstance(config.get("version"), str):
        merged["version"] = config["version"]
    if not merged["common"].get("outputDir"):
        merged["common"]["outputDir"] = default_output_dir()
    return merged


def ensure_user_config_exists() -> Path:
    """用户目录没有配置时，从默认模板部署一份过去。"""
    target = user_config_path()
    if target.exists():
        return target

    source = default_config_path()
    if source.exists():
        shutil.copyfile(source, target)
        config = _ensure_sections(_read_json(target))
    else:
        config = _ensure_sections({})
    _write_json(target, config)
    return target


def decrypt_passwords(config: dict[str, Any]) -> dict[str, Any]:
    """返回密码已解密的配置副本，供程序运行时使用。"""
    data = deepcopy(config)
    for section in ("attendance", "pjmn", "evection"):
        data[section]["password"] = decrypt_text(str(data[section].get("password", "")))
    return data


def encrypt_passwords(config: dict[str, Any]) -> dict[str, Any]:
    """返回密码已加密的配置副本，供写入文件使用。"""
    data = _ensure_sections(config)
    for section in ("attendance", "pjmn", "evection"):
        data[section]["password"] = encrypt_text(str(data[section].get("password", "")))
    return data


def load_config() -> AttendanceConfigLoadResult:
    """读取用户配置；格式错误或账号为空时标记为需要登录。"""
    path = ensure_user_config_exists()
    try:
        config = _ensure_sections(_read_json(path))
        runtime_config = decrypt_passwords(config)
    except Exception as exc:
        return AttendanceConfigLoadResult(config=_ensure_sections({}), path=path, requires_login=True, error=str(exc))

    username = str(runtime_config["attendance"].get("username", "")).strip()
    return AttendanceConfigLoadResult(
        config=runtime_config,
        path=path,
        requires_login=not bool(username),
        error=None,
    )


def save_config(config: dict[str, Any]) -> dict[str, Any]:
    """保存配置到用户目录，文件中密码为密文，返回运行时明文配置。"""
    encrypted = encrypt_passwords(config)
    path = user_config_path()
    _write_json(path, encrypted)
    return decrypt_passwords(encrypted)


def build_login_config(member_id: str, current_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """根据登录社员号生成三套系统账号默认值。"""
    member_id = member_id.strip()
    if len(member_id) != 8 or not member_id.isdigit():
        raise AttendanceConfigError("社员号格式不正确，请输入 8 位数字")

    config = _ensure_sections(current_config or {})
    pjmn_username = build_pjmn_username(member_id)

    config["evection"]["username"] = member_id
    config["evection"]["password"] = "12345678"

    config["pjmn"]["username"] = pjmn_username
    config["pjmn"]["password"] = pjmn_username

    config["attendance"]["username"] = member_id
    config["attendance"]["password"] = member_id

    return config
