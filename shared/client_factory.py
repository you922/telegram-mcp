"""
TelegramClient creation utility.

Previously, `TelegramClient(StringSession(s), API_ID, API_HASH)` was repeated
in main.py, account_manager.py, session_manager.py, login.py, qr_login.py,
and qr_web_login.py.
"""
from telethon import TelegramClient
from telethon.sessions import StringSession

from shared.config import API_ID, API_HASH


def create_telegram_client(session_string: str = "") -> TelegramClient:
    """Create a TelegramClient with the shared API credentials.

    Args:
        session_string: An existing session string, or empty for a new session.
    """
    return TelegramClient(StringSession(session_string), API_ID, API_HASH)
