"""
Reusable JSON file persistence.

Previously, every manager class (AccountManager, ProxyManager, HealthMonitor,
LogManager, StatsTracker, TemplateManager, TaskScheduler) had near-identical
_load_*() / _save_*() methods. This class centralizes that pattern.
"""
import json
import os
from typing import Any

from shared.config import ACCOUNTS_DIR


class JsonStore:
    """Load and save JSON data to a file under ACCOUNTS_DIR."""

    def __init__(self, filename: str, *, default: Any = None):
        self._path = os.path.join(ACCOUNTS_DIR, filename)
        self._default = default if default is not None else {}

    @property
    def path(self) -> str:
        return self._path

    def load(self) -> Any:
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return self._default_copy()
        return self._default_copy()

    def save(self, data: Any) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _default_copy(self) -> Any:
        if isinstance(self._default, dict):
            return dict(self._default)
        if isinstance(self._default, list):
            return list(self._default)
        return self._default
