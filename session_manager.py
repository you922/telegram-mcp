"""
Telegram Session Manager
管理 Telegram 会话的加载、保存和验证
"""
import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "2040"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "b18441a1ff607e10a989891a5462e627")
SESSION_FILE = os.getenv("SESSION_FILE", ".telegram_session")
USER_DATA_FILE = ".telegram_user_data.json"


class SessionManager:
    """管理 Telegram 会话"""

    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self.session_string: Optional[str] = None
        self.user_data: Optional[Dict[str, Any]] = None
        self._is_connected = False

    def load_session(self) -> Optional[str]:
        """从文件加载 session"""
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                return f.read().strip()
        return None

    def save_session(self, session_string: str) -> None:
        """保存 session 到文件"""
        with open(SESSION_FILE, "w") as f:
            f.write(session_string)
        self.session_string = session_string

    def load_user_data(self) -> Optional[Dict[str, Any]]:
        """加载用户数据"""
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, "r") as f:
                self.user_data = json.load(f)
                return self.user_data
        return None

    def save_user_data(self, user_data: Dict[str, Any]) -> None:
        """保存用户数据"""
        with open(USER_DATA_FILE, "w") as f:
            json.dump(user_data, f, indent=2, default=str)
        self.user_data = user_data

    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        session = self.load_session()
        return session is not None and len(session) > 0

    async def create_client(self, session_string: Optional[str] = None) -> TelegramClient:
        """创建 TelegramClient"""
        if session_string:
            self.session_string = session_string
            self.save_session(session_string)

        if not self.session_string:
            self.session_string = self.load_session()

        if not self.session_string:
            raise ValueError("No session available. Please login first.")

        self.client = TelegramClient(
            StringSession(self.session_string),
            API_ID,
            API_HASH
        )
        return self.client

    async def get_client(self) -> TelegramClient:
        """获取已连接的 client"""
        if not self.client:
            self.client = await self.create_client()

        if not self._is_connected:
            await self.client.connect()
            self._is_connected = True

        return self.client

    async def verify_session(self) -> bool:
        """验证 session 是否有效"""
        try:
            client = await self.get_client()
            await client.get_me()
            return True
        except Exception as e:
            print(f"Session verification failed: {e}")
            return False

    async def disconnect(self) -> None:
        """断开连接"""
        if self.client and self._is_connected:
            await self.client.disconnect()
            self._is_connected = False

    def clear_session(self) -> None:
        """清除保存的 session"""
        self.session_string = None
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        if os.path.exists(USER_DATA_FILE):
            os.remove(USER_DATA_FILE)
        self.user_data = None


# 全局 session manager 实例
session_manager = SessionManager()


async def get_authenticated_client() -> TelegramClient:
    """获取已认证的 client（供 MCP 工具使用）"""
    return await session_manager.get_client()


async def ensure_connected() -> TelegramClient:
    """确保 client 已连接"""
    client = await get_authenticated_client()
    if not session_manager._is_connected:
        await client.connect()
        session_manager._is_connected = True
    return client
