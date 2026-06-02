"""
Standardized JSON response helpers.

Previously, `json.dumps({"success": ..., ...}, ensure_ascii=False, indent=2)`
was repeated in nearly every function in account_tools.py and elsewhere.
"""
import json
from typing import Any


def success_response(message: str = None, **extra: Any) -> str:
    """Build a JSON success response string."""
    data: dict[str, Any] = {"success": True}
    if message is not None:
        data["message"] = message
    data.update(extra)
    return json.dumps(data, ensure_ascii=False, indent=2)


def error_response(error: str, **extra: Any) -> str:
    """Build a JSON error response string."""
    data: dict[str, Any] = {"success": False, "error": error}
    data.update(extra)
    return json.dumps(data, ensure_ascii=False, indent=2)


def json_response(data: Any) -> str:
    """Serialize arbitrary data to a JSON string."""
    return json.dumps(data, ensure_ascii=False, indent=2)
