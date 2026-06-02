"""Unit tests for stats_tracker module."""
import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestStatsTracker:
    """Tests for the StatsTracker class."""

    def _make_tracker(self, tmp_dir):
        """Create a StatsTracker that uses a temporary directory."""
        stats_file = os.path.join(tmp_dir, "stats.json")
        with patch("stats_tracker.STATS_FILE", stats_file), \
             patch("stats_tracker.ACCOUNTS_DIR", tmp_dir):
            from stats_tracker import StatsTracker
            tracker = StatsTracker()

            def patched_save():
                os.makedirs(tmp_dir, exist_ok=True)
                with open(stats_file, 'w', encoding='utf-8') as f:
                    json.dump(tracker.stats, f, ensure_ascii=False, indent=2)

            tracker._save_stats = patched_save
            return tracker

    def test_init_empty(self, tmp_path):
        """StatsTracker starts with empty stats when no file exists."""
        tracker = self._make_tracker(str(tmp_path))
        assert tracker.stats == {}

    def test_init_account_stats(self, tmp_path):
        """init_account_stats creates default structure."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.init_account_stats("acc1")

        assert "acc1" in tracker.stats
        s = tracker.stats["acc1"]
        assert s["total_uses"] == 0
        assert s["total_messages_sent"] == 0
        assert s["daily"] == {}
        assert s["weekly"] == {}
        assert s["first_use"] is not None
        assert s["last_use"] is None

    def test_init_account_stats_idempotent(self, tmp_path):
        """init_account_stats does not overwrite existing data."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.init_account_stats("acc1")
        tracker.stats["acc1"]["total_uses"] = 42

        tracker.init_account_stats("acc1")
        assert tracker.stats["acc1"]["total_uses"] == 42

    def test_record_use(self, tmp_path):
        """record_use increments total_uses and daily/weekly counts."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_use("acc1")

        s = tracker.stats["acc1"]
        assert s["total_uses"] == 1
        assert s["last_use"] is not None

        today = datetime.now().strftime("%Y-%m-%d")
        assert today in s["daily"]
        assert s["daily"][today]["uses"] == 1

    def test_record_use_multiple(self, tmp_path):
        """record_use accumulates counts correctly."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_use("acc1")
        tracker.record_use("acc1")
        tracker.record_use("acc1")

        assert tracker.stats["acc1"]["total_uses"] == 3

        today = datetime.now().strftime("%Y-%m-%d")
        assert tracker.stats["acc1"]["daily"][today]["uses"] == 3

    def test_record_message_sent(self, tmp_path):
        """record_message_sent increments message counters."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_message_sent("acc1", count=5)

        s = tracker.stats["acc1"]
        assert s["total_messages_sent"] == 5

        today = datetime.now().strftime("%Y-%m-%d")
        assert s["daily"][today]["messages"] == 5

    def test_record_message_sent_accumulates(self, tmp_path):
        """record_message_sent accumulates over multiple calls."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_message_sent("acc1", count=3)
        tracker.record_message_sent("acc1", count=7)

        assert tracker.stats["acc1"]["total_messages_sent"] == 10

    def test_get_account_stats_existing(self, tmp_path):
        """get_account_stats returns stats for existing account."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_use("acc1")

        stats = tracker.get_account_stats("acc1")
        assert stats["total_uses"] == 1

    def test_get_account_stats_nonexistent(self, tmp_path):
        """get_account_stats returns empty dict for unknown account."""
        tracker = self._make_tracker(str(tmp_path))
        assert tracker.get_account_stats("nonexistent") == {}

    def test_get_daily_stats_today(self, tmp_path):
        """get_daily_stats returns today's stats by default."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_use("acc1")
        tracker.record_message_sent("acc2", count=3)

        daily = tracker.get_daily_stats()
        assert "acc1" in daily
        assert daily["acc1"]["uses"] == 1
        assert "acc2" in daily
        assert daily["acc2"]["messages"] == 3

    def test_get_daily_stats_specific_date(self, tmp_path):
        """get_daily_stats filters by specified date."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_use("acc1")

        # Query a different date
        result = tracker.get_daily_stats("2020-01-01")
        assert result == {}

    def test_get_weekly_stats(self, tmp_path):
        """get_weekly_stats returns this week's stats by default."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_use("acc1")

        weekly = tracker.get_weekly_stats()
        assert "acc1" in weekly
        assert weekly["acc1"]["uses"] == 1

    def test_get_top_accounts_by_uses(self, tmp_path):
        """get_top_accounts sorts by total uses."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_use("low")
        tracker.record_use("high")
        tracker.record_use("high")
        tracker.record_use("high")

        top = tracker.get_top_accounts(by="uses", limit=10, period="all")
        assert top[0]["account_id"] == "high"
        assert top[0]["value"] == 3
        assert top[1]["account_id"] == "low"
        assert top[1]["value"] == 1

    def test_get_top_accounts_by_messages(self, tmp_path):
        """get_top_accounts sorts by messages when specified."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_message_sent("acc1", count=100)
        tracker.record_message_sent("acc2", count=5)

        top = tracker.get_top_accounts(by="messages", limit=10, period="all")
        assert top[0]["account_id"] == "acc1"
        assert top[0]["value"] == 100

    def test_get_top_accounts_limited(self, tmp_path):
        """get_top_accounts respects the limit parameter."""
        tracker = self._make_tracker(str(tmp_path))
        for i in range(20):
            tracker.record_use(f"acc{i}")

        top = tracker.get_top_accounts(limit=5)
        assert len(top) == 5

    def test_get_top_accounts_today_period(self, tmp_path):
        """get_top_accounts with period='today' uses daily stats."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_use("acc1")
        tracker.record_use("acc1")

        top = tracker.get_top_accounts(by="uses", period="today")
        assert top[0]["account_id"] == "acc1"
        assert top[0]["value"] == 2

    def test_get_activity_trend(self, tmp_path):
        """get_activity_trend returns daily data for specified days."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_use("acc1")

        trend = tracker.get_activity_trend("acc1", days=7)
        assert len(trend) == 7

        # Today should have uses=1
        today = datetime.now().strftime("%Y-%m-%d")
        today_entry = next(e for e in trend if e["date"] == today)
        assert today_entry["uses"] == 1

    def test_get_activity_trend_nonexistent(self, tmp_path):
        """get_activity_trend returns empty list for unknown account."""
        tracker = self._make_tracker(str(tmp_path))
        assert tracker.get_activity_trend("nonexistent") == []

    def test_get_summary(self, tmp_path):
        """get_summary returns aggregate summary across all accounts."""
        tracker = self._make_tracker(str(tmp_path))
        tracker.record_use("acc1")
        tracker.record_use("acc2")
        tracker.record_message_sent("acc1", count=10)

        summary = tracker.get_summary()
        assert summary["total_accounts"] == 2
        assert summary["total_uses"] == 2
        assert summary["total_messages_sent"] == 10
        assert summary["today_uses"] == 2
        assert summary["today_messages"] == 10
        assert "most_active" in summary
        assert "last_updated" in summary

    def test_load_from_existing_file(self, tmp_path):
        """StatsTracker loads from existing file."""
        stats_file = os.path.join(str(tmp_path), "stats.json")
        data = {
            "acc1": {
                "total_uses": 42,
                "total_messages_sent": 100,
                "daily": {},
                "weekly": {},
                "first_use": "2024-01-01",
                "last_use": "2024-06-01"
            }
        }
        with open(stats_file, 'w') as f:
            json.dump(data, f)

        with patch("stats_tracker.STATS_FILE", stats_file), \
             patch("stats_tracker.ACCOUNTS_DIR", str(tmp_path)):
            from stats_tracker import StatsTracker
            tracker = StatsTracker()
            assert tracker.stats["acc1"]["total_uses"] == 42
