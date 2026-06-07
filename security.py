#!/usr/bin/env python3
"""安全工具模块：鉴权、脱敏、Session 加密、路径沙箱。"""
import base64
import hashlib
import hmac
import os
import re
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Header, HTTPException, Request, WebSocket, status

SECRET_KEY_FILE = Path(os.getenv("TELEGRAM_MCP_SECRET_KEY_FILE", "~/.config/telegram-mcp/secret_key")).expanduser()
ADMIN_TOKEN = os.getenv("TELEGRAM_MCP_ADMIN_TOKEN", "").strip()
ALLOW_NO_AUTH_LOCALHOST = os.getenv("TELEGRAM_MCP_ALLOW_NO_AUTH_LOCALHOST", "1") == "1"
SESSION_PREFIX = "enc:v1:"
ALLOWED_FILE_DIR = Path(os.getenv("TELEGRAM_MCP_ALLOWED_FILE_DIR", "./telegram_files")).resolve()
EXPORT_DIR = Path(os.getenv("TELEGRAM_MCP_EXPORT_DIR", "./exports")).resolve()


def _load_secret_material() -> bytes:
    env_secret = os.getenv("TELEGRAM_MCP_SECRET_KEY", "").strip()
    if env_secret:
        return env_secret.encode("utf-8")

    SECRET_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if SECRET_KEY_FILE.exists():
        return SECRET_KEY_FILE.read_bytes().strip()

    secret = base64.urlsafe_b64encode(os.urandom(32))
    SECRET_KEY_FILE.write_bytes(secret)
    try:
        os.chmod(SECRET_KEY_FILE, 0o600)
    except OSError:
        pass
    return secret


def _fernet() -> Fernet:
    material = _load_secret_material()
    key = base64.urlsafe_b64encode(hashlib.sha256(material).digest())
    return Fernet(key)


def encrypt_session(session_string: str) -> str:
    if not session_string or session_string.startswith(SESSION_PREFIX):
        return session_string
    token = _fernet().encrypt(session_string.encode("utf-8")).decode("utf-8")
    return SESSION_PREFIX + token


def decrypt_session(session_string: str) -> str:
    if not session_string or not session_string.startswith(SESSION_PREFIX):
        return session_string
    token = session_string[len(SESSION_PREFIX):]
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Session 解密失败，请确认 TELEGRAM_MCP_SECRET_KEY 是否正确") from exc


def mask_phone(phone: Optional[str]) -> str:
    if not phone:
        return "N/A"
    text = str(phone)
    if len(text) <= 4:
        return "****"
    return text[:3] + "****" + text[-4:]


def mask_secret(value: Optional[str], keep: int = 4) -> str:
    if not value:
        return ""
    text = str(value)
    if len(text) <= keep * 2:
        return "***"
    return f"{text[:keep]}...{text[-keep:]}"


def sanitize_log_text(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"tg://login\?token=[^\s'\"]+", "tg://login?token=<redacted>", text)
    text = re.sub(r"([+]?\d[\d\s\-()]{6,}\d)", lambda m: mask_phone(m.group(1)), text)
    text = re.sub(r"(session_string|api_hash|password|token)\s*[:=]\s*[^\s,}]+", r"\1=<redacted>", text, flags=re.I)
    return text


def is_local_client(host: Optional[str]) -> bool:
    return host in {"127.0.0.1", "::1", "localhost"}


def require_admin_token(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None),
):
    if not ADMIN_TOKEN:
        client_host = request.client.host if request.client else None
        if ALLOW_NO_AUTH_LOCALHOST and is_local_client(client_host):
            return True
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未设置 TELEGRAM_MCP_ADMIN_TOKEN，非本机 Web API 已锁定。请设置管理员 Token 后重启。",
        )

    token = x_admin_token or ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if not token or not hmac.compare_digest(token, ADMIN_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="管理员 Token 无效")
    return True


async def require_websocket_token(websocket: WebSocket) -> None:
    if not ADMIN_TOKEN:
        client_host = websocket.client.host if websocket.client else None
        if ALLOW_NO_AUTH_LOCALHOST and is_local_client(client_host):
            return
        await websocket.close(code=1008, reason="TELEGRAM_MCP_ADMIN_TOKEN required")
        raise RuntimeError("admin token required")

    token = websocket.query_params.get("token") or websocket.headers.get("x-admin-token") or ""
    authorization = websocket.headers.get("authorization") or ""
    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if not token or not hmac.compare_digest(token, ADMIN_TOKEN):
        await websocket.close(code=1008, reason="invalid admin token")
        raise RuntimeError("invalid admin token")


def validate_file_path(path: str, *, must_exist: bool = False, base_dir: Optional[Path] = None) -> str:
    if not path:
        raise ValueError("文件路径不能为空")
    base = (base_dir or ALLOWED_FILE_DIR).resolve()
    base.mkdir(parents=True, exist_ok=True)
    resolved = Path(path).expanduser().resolve()
    if base not in resolved.parents and resolved != base:
        raise ValueError(f"文件路径必须位于允许目录内: {base}")
    if must_exist and not resolved.exists():
        raise ValueError(f"文件不存在: {resolved}")
    return str(resolved)


def validate_export_path(path: Optional[str], default_name: str) -> str:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    target = Path(path).expanduser().resolve() if path else (EXPORT_DIR / default_name).resolve()
    if EXPORT_DIR not in target.parents and target != EXPORT_DIR:
        raise ValueError(f"导出路径必须位于允许目录内: {EXPORT_DIR}")
    return str(target)
