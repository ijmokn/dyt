"""配置文件密码加解密工具。"""

from __future__ import annotations

import base64
import hashlib

ENCRYPTED_PREFIX = "enc:"

# 拿到同一套代码和密钥，就可以解密配置文件中的密码。

_SHARED_SECRET = b"JMate attendance config shared secret v1"


def _build_fernet():
    """延迟导入 cryptography，避免程序启动时因为缺依赖直接崩溃。"""
    try:
        from cryptography.fernet import Fernet
    except ModuleNotFoundError as exc:
        raise RuntimeError("缺少 cryptography 依赖，请先执行：pip install cryptography") from exc

    key = base64.urlsafe_b64encode(hashlib.sha256(_SHARED_SECRET).digest())
    return Fernet(key)


def encrypt_text(value: str) -> str:
    """加密文本；空值保持为空，已加密内容不重复加密。"""
    if not value:
        return ""
    if value.startswith(ENCRYPTED_PREFIX):
        return value

    token = _build_fernet().encrypt(value.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTED_PREFIX}{token}"


def decrypt_text(value: str) -> str:
    """解密文本；非 enc: 开头的内容按旧明文兼容处理。"""
    if not value:
        return ""
    if not value.startswith(ENCRYPTED_PREFIX):
        return value

    token = value[len(ENCRYPTED_PREFIX) :]
    return _build_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
