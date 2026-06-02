"""
Centralized configuration constants for Telegram MCP.

Previously duplicated across main.py, account_manager.py, session_manager.py,
login.py, qr_login.py, qr_web_login.py, and web_login.py.
"""
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "2040"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "b18441a1ff607e10a989891a5462e627")
SESSION_FILE = os.getenv("SESSION_FILE", ".telegram_session")
ACCOUNTS_DIR = "./accounts"
