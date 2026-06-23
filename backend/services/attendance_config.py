"""考勤相关系统账号配置读写服务。"""

from __future__ import annotations

import json
import ntpath
import shutil
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .crypto_service import decrypt_text, encrypt_text

CONFIG_FILE_NAME = ".attendance-config.json"

# 密码写入 JSON 文件时的加密开关：True 保存密文，False 保存明文。
ENCRYPT_PASSWORD_ON_SAVE = False


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
    """返回当前用户文档目录。"""
    return str(Path.home() / "Documents")


def normalize_windows_path(path_value: str) -> str:
    """把输出目录统一为 Windows 反斜杠路径。

    Python 内存中的路径使用单个反斜杠；写入 JSON 后会按 JSON 规范显示为
    `D:\\xxx\\ss`，从而保证配置文件中的路径格式一致。
    """
    value = str(path_value or "").strip()
    if not value:
        return ""
    return ntpath.normpath(value.replace("/", "\\"))


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
    """读取项目随包携带的唯一默认配置模板。"""
    path = default_config_path()
    if not path.exists():
        raise AttendanceConfigError(f"缺少默认配置模板：{path}")
    return _read_json(path)


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
    merged["common"]["outputDir"] = normalize_windows_path(
        str(merged["common"].get("outputDir", ""))
    )
    return merged


def ensure_user_config_exists() -> Path:
    """用户目录没有配置时，从默认模板部署一份过去。"""
    target = user_config_path()
    if target.exists():
        return target

    # 首次启动时直接复制当前默认模板。
    source = default_config_path()
    if not source.exists():
        raise AttendanceConfigError(f"缺少默认配置模板：{source}")
    shutil.copyfile(source, target)
    config = _ensure_sections(_read_json(target))
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
    """按照代码级开关保存密码，并返回运行时使用的明文配置。"""
    prepared = _ensure_sections(config)
    stored_config = (
        encrypt_passwords(prepared)
        if ENCRYPT_PASSWORD_ON_SAVE
        else decrypt_passwords(prepared)
    )
    path = user_config_path()
    _write_json(path, stored_config)
    return decrypt_passwords(stored_config)


def build_login_config(member_id: str, current_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """根据登录社员号生成三套系统账号默认值。"""
    member_id = member_id.strip()
    if len(member_id) != 8 or not member_id.isdigit():
        raise AttendanceConfigError("社员号格式不正确，请输入 8 位数字")

    config = _ensure_sections(current_config or {})
    pjmn_username = build_pjmn_username(member_id)

    # 禀议系统：账号使用登录社员号，初始密码保持为空。
    config["evection"]["username"] = member_id
    config["evection"]["password"] = ""

    # PJCOST：账号去掉社员号倒数第 2 位，密码与派生账号一致。
    config["pjmn"]["username"] = pjmn_username
    config["pjmn"]["password"] = pjmn_username

    # 考勤系统：账号和密码都使用登录社员号。
    config["attendance"]["username"] = member_id
    config["attendance"]["password"] = member_id

    return config
