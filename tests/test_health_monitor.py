"""Unit tests for health_monitor module."""
import json
import os
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock account_manager and proxy_manager imports used by health_monitor."""
    mock_am = MagicMock()
    mock_am.accounts = {}
    mock_am.list_accounts.return_value = []

    mock_pm = MagicMock()
    mock_pm.get_proxy_for_account.return_value = None

    with patch.dict("sys.modules", {
        "account_manager": MagicMock(account_manager=mock_am),
        "proxy_manager": MagicMock(proxy_manager=mock_pm),
    }):
        yield mock_am, mock_pm


class TestHealthMonitor:
    """Tests for the HealthMonitor class."""

    def _make_monitor(self, tmp_dir):
        """Create a HealthMonitor that uses a temporary directory."""
        health_file = os.path.join(tmp_dir, "health.json")
        with patch("health_monitor.HEALTH_FILE", health_file), \
             patch("health_monitor.ACCOUNTS_DIR", tmp_dir):
            from health_monitor import HealthMonitor
            monitor = HealthMonitor()

            def patched_save():
                os.makedirs(tmp_dir, exist_ok=True)
                with open(health_file, 'w', encoding='utf-8') as f:
                    json.dump(monitor.health_data, f, ensure_ascii=False, indent=2)

            monitor._save_health = patched_save
            return monitor

    def test_init_empty(self, tmp_path):
        """HealthMonitor starts with empty health data."""
        monitor = self._make_monitor(str(tmp_path))
        assert monitor.health_data == {}
        assert monitor._monitoring is False

    def test_init_account_health(self, tmp_path):
        """init_account_health creates default health structure."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.init_account_health("acc1")

        assert "acc1" in monitor.health_data
        h = monitor.health_data["acc1"]
        assert h["login_fail_count"] == 0
        assert h["login_success_count"] == 0
        assert h["message_success_count"] == 0
        assert h["message_fail_count"] == 0
        assert h["consecutive_fails"] == 0
        assert h["risk_level"] == "low"
        assert h["banned"] is False
        assert h["proxy_response_time"] == 0

    def test_init_account_health_idempotent(self, tmp_path):
        """init_account_health does not overwrite existing data."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.init_account_health("acc1")
        monitor.health_data["acc1"]["login_success_count"] = 99

        monitor.init_account_health("acc1")
        assert monitor.health_data["acc1"]["login_success_count"] == 99

    def test_record_login_success(self, tmp_path):
        """record_login_success increments counter and resets consecutive fails."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.init_account_health("acc1")
        monitor.health_data["acc1"]["consecutive_fails"] = 3

        monitor.record_login_success("acc1")

        h = monitor.health_data["acc1"]
        assert h["login_success_count"] == 1
        assert h["consecutive_fails"] == 0
        assert h["last_check"] is not None

    def test_record_login_failure(self, tmp_path):
        """record_login_failure increments counters and tracks error."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.record_login_failure("acc1", "connection timeout")

        h = monitor.health_data["acc1"]
        assert h["login_fail_count"] == 1
        assert h["consecutive_fails"] == 1
        assert h["last_login_fail"]["error"] == "connection timeout"

    def test_record_message_success(self, tmp_path):
        """record_message_success increments counter and resets fails."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.init_account_health("acc1")
        monitor.health_data["acc1"]["consecutive_fails"] = 2

        monitor.record_message_success("acc1")

        h = monitor.health_data["acc1"]
        assert h["message_success_count"] == 1
        assert h["consecutive_fails"] == 0

    def test_record_message_failure(self, tmp_path):
        """record_message_failure increments counters."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.record_message_failure("acc1", "flood wait")

        h = monitor.health_data["acc1"]
        assert h["message_fail_count"] == 1
        assert h["consecutive_fails"] == 1
        assert h["last_message_fail"]["error"] == "flood wait"

    def test_record_proxy_response_time_first(self, tmp_path):
        """record_proxy_response_time sets the value on first call."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.record_proxy_response_time("acc1", 150.0)

        assert monitor.health_data["acc1"]["proxy_response_time"] == 150.0

    def test_record_proxy_response_time_average(self, tmp_path):
        """record_proxy_response_time averages with existing value."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.record_proxy_response_time("acc1", 100.0)
        monitor.record_proxy_response_time("acc1", 200.0)

        # Average of 100 and 200 = 150
        assert monitor.health_data["acc1"]["proxy_response_time"] == 150.0

    def test_risk_level_low(self, tmp_path):
        """Risk level stays low with no failures."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.record_login_success("acc1")
        monitor.record_login_success("acc1")

        assert monitor.health_data["acc1"]["risk_level"] == "low"

    def test_risk_level_medium_consecutive(self, tmp_path):
        """Risk level becomes medium with 2+ consecutive failures and low fail rate."""
        monitor = self._make_monitor(str(tmp_path))
        # Build up successes first to keep fail rate below 0.8
        for _ in range(8):
            monitor.record_login_success("acc1")
        monitor.record_login_failure("acc1", "err")
        monitor.record_login_failure("acc1", "err")

        # consecutive_fails=2, fail_rate=2/10=0.2 → medium
        assert monitor.health_data["acc1"]["risk_level"] == "medium"

    def test_risk_level_high_consecutive(self, tmp_path):
        """Risk level becomes high with 5+ consecutive failures."""
        monitor = self._make_monitor(str(tmp_path))
        for _ in range(5):
            monitor.record_login_failure("acc1", "err")

        assert monitor.health_data["acc1"]["risk_level"] == "high"

    def test_risk_level_high_fail_rate(self, tmp_path):
        """Risk level becomes high with 80%+ login failure rate."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.init_account_health("acc1")
        # Set up: 1 success, 4 failures (80% fail rate)
        monitor.health_data["acc1"]["login_success_count"] = 1
        monitor.health_data["acc1"]["login_fail_count"] = 4
        monitor.health_data["acc1"]["consecutive_fails"] = 1

        # Trigger risk update
        monitor.record_login_failure("acc1", "err")

        assert monitor.health_data["acc1"]["risk_level"] == "high"

    def test_banned_detection(self, tmp_path):
        """Accounts are marked banned when error contains ban keywords."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.record_login_failure("acc1", "User has been banned")

        assert monitor.health_data["acc1"]["banned"] is True
        assert monitor.health_data["acc1"]["risk_level"] == "high"

    def test_banned_detection_deactivated(self, tmp_path):
        """Accounts are marked banned for 'deactivated' errors."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.record_login_failure("acc1", "Account deactivated")

        assert monitor.health_data["acc1"]["banned"] is True

    def test_banned_detection_flood(self, tmp_path):
        """Accounts are marked banned for 'flood' errors."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.record_message_failure("acc1", "FloodWaitError")

        assert monitor.health_data["acc1"]["banned"] is True

    def test_get_risk_accounts(self, tmp_path):
        """get_risk_accounts returns accounts with medium/high risk or banned."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.init_account_health("safe")
        monitor.init_account_health("risky")
        monitor.health_data["risky"]["risk_level"] = "high"

        risks = monitor.get_risk_accounts()
        assert "risky" in risks
        assert "safe" not in risks

    def test_get_health_report_specific_account(self, tmp_path):
        """get_health_report returns data for specific account."""
        monitor = self._make_monitor(str(tmp_path))
        monitor.record_login_success("acc1")

        report = monitor.get_health_report("acc1")
        assert report["login_success_count"] == 1

    def test_get_health_report_nonexistent(self, tmp_path):
        """get_health_report returns empty dict for unknown account."""
        monitor = self._make_monitor(str(tmp_path))
        assert monitor.get_health_report("nope") == {}

    def test_stop_monitoring(self, tmp_path):
        """stop_monitoring sets _monitoring to False."""
        monitor = self._make_monitor(str(tmp_path))
        monitor._monitoring = True
        monitor.stop_monitoring()
        assert monitor._monitoring is False

    def test_load_from_existing_file(self, tmp_path):
        """HealthMonitor loads from existing file."""
        health_file = os.path.join(str(tmp_path), "health.json")
        data = {
            "acc1": {
                "login_fail_count": 3,
                "login_success_count": 10,
                "message_success_count": 50,
                "message_fail_count": 2,
                "consecutive_fails": 0,
                "risk_level": "low",
                "banned": False,
                "proxy_response_time": 120,
                "last_check": "2024-01-01"
            }
        }
        with open(health_file, 'w') as f:
            json.dump(data, f)

        with patch("health_monitor.HEALTH_FILE", health_file), \
             patch("health_monitor.ACCOUNTS_DIR", str(tmp_path)):
            from health_monitor import HealthMonitor
            monitor = HealthMonitor()
            assert monitor.health_data["acc1"]["login_fail_count"] == 3
            assert monitor.health_data["acc1"]["message_success_count"] == 50
