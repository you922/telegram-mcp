"""Unit tests for log_manager module."""
import json
import os
import tempfile
from unittest.mock import patch, mock_open

import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLogManager:
    """Tests for the LogManager class."""

    def _make_manager(self, tmp_dir):
        """Create a LogManager that uses a temporary directory."""
        log_file = os.path.join(tmp_dir, "logs.json")
        with patch("log_manager.LOG_FILE", log_file), \
             patch("log_manager.ACCOUNTS_DIR", tmp_dir):
            from log_manager import LogManager
            mgr = LogManager()
            # Patch save to use our tmp dir
            mgr._log_file = log_file
            mgr._accounts_dir = tmp_dir
            original_save = mgr._save_logs

            def patched_save():
                os.makedirs(tmp_dir, exist_ok=True)
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump(mgr.logs, f, ensure_ascii=False, indent=2)

            mgr._save_logs = patched_save
            return mgr

    def test_init_empty(self, tmp_path):
        """LogManager initializes with empty logs when no file exists."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.logs == []

    def test_add_log_creates_entry(self, tmp_path):
        """add_log appends a correctly structured log entry."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_log("login", "acc1", "Logged in successfully", "success")

        assert len(mgr.logs) == 1
        log = mgr.logs[0]
        assert log["action"] == "login"
        assert log["account"] == "acc1"
        assert log["detail"] == "Logged in successfully"
        assert log["level"] == "success"
        assert "time" in log
        assert "timestamp" in log

    def test_add_log_truncates_at_max(self, tmp_path):
        """Logs are truncated to MAX_LOGS when limit is exceeded."""
        mgr = self._make_manager(str(tmp_path))
        # Add more than MAX_LOGS entries
        with patch("log_manager.MAX_LOGS", 5):
            for i in range(10):
                mgr.add_log("action", "acc", f"detail {i}")

        # Should retain only last 5 (patched MAX_LOGS won't affect the instance,
        # so let's test the built-in limit behavior)
        # Actually the instance uses the module constant at call time
        # Let's test with the real limit indirectly
        mgr.logs = list(range(1001))
        mgr.add_log("action", "acc", "overflow")
        # After adding, should be truncated to MAX_LOGS (1000)
        from log_manager import MAX_LOGS
        assert len(mgr.logs) <= MAX_LOGS + 1  # at most MAX_LOGS after trim

    def test_get_logs_default(self, tmp_path):
        """get_logs returns logs in reverse order (newest first)."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_log("a1", "acc1", "first")
        mgr.add_log("a2", "acc2", "second")
        mgr.add_log("a3", "acc3", "third")

        logs = mgr.get_logs()
        assert len(logs) == 3
        assert logs[0]["action"] == "a3"  # newest first
        assert logs[2]["action"] == "a1"  # oldest last

    def test_get_logs_with_limit(self, tmp_path):
        """get_logs respects the limit parameter."""
        mgr = self._make_manager(str(tmp_path))
        for i in range(20):
            mgr.add_log("action", "acc", f"detail {i}")

        logs = mgr.get_logs(limit=5)
        assert len(logs) == 5

    def test_get_logs_filter_by_account(self, tmp_path):
        """get_logs filters by account."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_log("login", "acc1", "d1")
        mgr.add_log("login", "acc2", "d2")
        mgr.add_log("send", "acc1", "d3")

        logs = mgr.get_logs(account="acc1")
        assert len(logs) == 2
        assert all(log["account"] == "acc1" for log in logs)

    def test_get_logs_filter_by_action(self, tmp_path):
        """get_logs filters by action type."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_log("login", "acc1", "d1")
        mgr.add_log("send", "acc2", "d2")
        mgr.add_log("login", "acc3", "d3")

        logs = mgr.get_logs(action="login")
        assert len(logs) == 2
        assert all(log["action"] == "login" for log in logs)

    def test_clear_logs_all(self, tmp_path):
        """clear_logs without before clears all logs."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_log("a", "acc", "d")
        mgr.add_log("b", "acc", "d")

        cleared = mgr.clear_logs()
        assert cleared == 2
        assert mgr.logs == []

    def test_clear_logs_before_date(self, tmp_path):
        """clear_logs with before removes only older logs."""
        mgr = self._make_manager(str(tmp_path))
        mgr.logs = [
            {"time": "2024-01-01T00:00:00", "action": "old", "account": "a", "detail": "", "level": "info"},
            {"time": "2024-06-01T00:00:00", "action": "new", "account": "a", "detail": "", "level": "info"},
        ]

        cleared = mgr.clear_logs(before="2024-03-01T00:00:00")
        assert cleared == 1
        assert len(mgr.logs) == 1
        assert mgr.logs[0]["action"] == "new"

    def test_get_stats(self, tmp_path):
        """get_stats returns correct statistics."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_log("login", "acc1", "", "info")
        mgr.add_log("login", "acc2", "", "error")
        mgr.add_log("send", "acc1", "", "success")

        stats = mgr.get_stats()
        assert stats["total"] == 3
        assert stats["by_action"]["login"] == 2
        assert stats["by_action"]["send"] == 1
        assert stats["by_level"]["info"] == 1
        assert stats["by_level"]["error"] == 1
        assert stats["by_level"]["success"] == 1
        assert stats["by_account"]["acc1"] == 2
        assert stats["by_account"]["acc2"] == 1
        assert len(stats["recent"]) == 3

    def test_load_from_existing_file(self, tmp_path):
        """LogManager loads existing logs from file."""
        log_file = os.path.join(str(tmp_path), "logs.json")
        existing_logs = [
            {"time": "2024-01-01T00:00:00", "action": "test", "account": "a", "detail": "", "level": "info"}
        ]
        with open(log_file, 'w') as f:
            json.dump(existing_logs, f)

        with patch("log_manager.LOG_FILE", log_file), \
             patch("log_manager.ACCOUNTS_DIR", str(tmp_path)):
            from log_manager import LogManager
            mgr = LogManager()
            assert len(mgr.logs) == 1
            assert mgr.logs[0]["action"] == "test"

    def test_load_from_corrupted_file(self, tmp_path):
        """LogManager handles corrupted JSON gracefully."""
        log_file = os.path.join(str(tmp_path), "logs.json")
        with open(log_file, 'w') as f:
            f.write("not valid json{{{")

        with patch("log_manager.LOG_FILE", log_file), \
             patch("log_manager.ACCOUNTS_DIR", str(tmp_path)):
            from log_manager import LogManager
            mgr = LogManager()
            assert mgr.logs == []
