"""Unit tests for proxy_manager module."""
import json
import os
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestProxyManager:
    """Tests for the ProxyManager class."""

    def _make_manager(self, tmp_dir):
        """Create a ProxyManager that uses a temporary directory."""
        proxies_file = os.path.join(tmp_dir, "proxies.json")
        with patch("proxy_manager.PROXIES_FILE", proxies_file), \
             patch("proxy_manager.ACCOUNTS_DIR", tmp_dir):
            from proxy_manager import ProxyManager
            mgr = ProxyManager()

            def patched_save():
                os.makedirs(tmp_dir, exist_ok=True)
                with open(proxies_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "global": mgr.global_proxy,
                        "proxies": mgr.proxies,
                        "stats": mgr.proxy_stats
                    }, f, ensure_ascii=False, indent=2)

            mgr._save_proxies = patched_save
            return mgr

    def test_init_empty(self, tmp_path):
        """ProxyManager initializes with empty state when no file exists."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.proxies == {}
        assert mgr.global_proxy is None
        assert mgr.proxy_stats == {}

    def test_add_proxy_valid(self, tmp_path):
        """add_proxy creates a proxy entry with valid protocol."""
        mgr = self._make_manager(str(tmp_path))
        result = mgr.add_proxy("p1", "socks5", "1.2.3.4", 1080, "user", "pass")

        assert result is True
        assert "p1" in mgr.proxies
        p = mgr.proxies["p1"]
        assert p["protocol"] == "socks5"
        assert p["host"] == "1.2.3.4"
        assert p["port"] == 1080
        assert p["username"] == "user"
        assert p["password"] == "pass"

    def test_add_proxy_all_protocols(self, tmp_path):
        """add_proxy accepts all valid protocols."""
        mgr = self._make_manager(str(tmp_path))
        for proto in ["socks5", "http", "https", "socks4"]:
            result = mgr.add_proxy(f"p_{proto}", proto, "host", 8080)
            assert result is True

    def test_add_proxy_invalid_protocol(self, tmp_path):
        """add_proxy rejects invalid protocols."""
        mgr = self._make_manager(str(tmp_path))
        result = mgr.add_proxy("p1", "ftp", "host", 21)
        assert result is False
        assert "p1" not in mgr.proxies

    def test_add_proxy_normalizes_protocol_case(self, tmp_path):
        """add_proxy normalizes protocol to lowercase."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_proxy("p1", "SOCKS5", "host", 1080)
        assert mgr.proxies["p1"]["protocol"] == "socks5"

    def test_add_proxy_initializes_stats(self, tmp_path):
        """add_proxy creates a stats entry for the new proxy."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_proxy("p1", "socks5", "host", 1080)

        assert "p1" in mgr.proxy_stats
        assert mgr.proxy_stats["p1"]["success_count"] == 0
        assert mgr.proxy_stats["p1"]["fail_count"] == 0

    def test_delete_proxy_existing(self, tmp_path):
        """delete_proxy removes an existing proxy."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_proxy("p1", "socks5", "host", 1080)

        result = mgr.delete_proxy("p1")
        assert result is True
        assert "p1" not in mgr.proxies

    def test_delete_proxy_nonexistent(self, tmp_path):
        """delete_proxy returns False for missing proxies."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.delete_proxy("nope") is False

    def test_set_global_proxy(self, tmp_path):
        """set_global_proxy sets the global proxy configuration."""
        mgr = self._make_manager(str(tmp_path))
        result = mgr.set_global_proxy("http", "proxy.example.com", 3128, "u", "p")

        assert result is True
        assert mgr.global_proxy is not None
        assert mgr.global_proxy["protocol"] == "http"
        assert mgr.global_proxy["host"] == "proxy.example.com"
        assert mgr.global_proxy["port"] == 3128

    def test_set_global_proxy_invalid_protocol(self, tmp_path):
        """set_global_proxy rejects invalid protocols."""
        mgr = self._make_manager(str(tmp_path))
        result = mgr.set_global_proxy("ftp", "host", 21)
        assert result is False
        assert mgr.global_proxy is None

    def test_remove_global_proxy(self, tmp_path):
        """remove_global_proxy clears the global proxy."""
        mgr = self._make_manager(str(tmp_path))
        mgr.set_global_proxy("socks5", "host", 1080)
        assert mgr.global_proxy is not None

        result = mgr.remove_global_proxy()
        assert result is True
        assert mgr.global_proxy is None

    def test_assign_proxy_to_account(self, tmp_path):
        """assign_proxy_to_account links an account to a proxy."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_proxy("p1", "socks5", "host", 1080)

        result = mgr.assign_proxy_to_account("acc1", "p1")
        assert result is True
        assert "acc1" in mgr.proxies["p1"]["assigned_to"]

    def test_assign_proxy_to_account_nonexistent_proxy(self, tmp_path):
        """assign_proxy_to_account fails for nonexistent proxy."""
        mgr = self._make_manager(str(tmp_path))
        result = mgr.assign_proxy_to_account("acc1", "nope")
        assert result is False

    def test_assign_proxy_idempotent(self, tmp_path):
        """assign_proxy_to_account doesn't duplicate assignments."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_proxy("p1", "socks5", "host", 1080)

        mgr.assign_proxy_to_account("acc1", "p1")
        mgr.assign_proxy_to_account("acc1", "p1")

        assert mgr.proxies["p1"]["assigned_to"].count("acc1") == 1

    def test_unassign_proxy_from_account(self, tmp_path):
        """unassign_proxy_from_account removes account from proxy assignment."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_proxy("p1", "socks5", "host", 1080)
        mgr.assign_proxy_to_account("acc1", "p1")

        result = mgr.unassign_proxy_from_account("acc1", "p1")
        assert result is True
        assert "acc1" not in mgr.proxies["p1"]["assigned_to"]

    def test_unassign_proxy_nonexistent_proxy(self, tmp_path):
        """unassign_proxy_from_account returns False for missing proxy."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.unassign_proxy_from_account("acc1", "nope") is False

    def test_to_telethon_format_socks5_with_auth(self, tmp_path):
        """to_telethon_format converts socks5 proxy with auth correctly."""
        mgr = self._make_manager(str(tmp_path))
        config = {
            "protocol": "socks5",
            "host": "1.2.3.4",
            "port": 1080,
            "username": "user",
            "password": "pass"
        }
        result = mgr.to_telethon_format(config)
        assert result["proxy_type"] == "socks5"
        assert result["addr"] == "1.2.3.4"
        assert result["port"] == 1080
        assert result["rdns"] is True
        assert result["username"] == "user"
        assert result["password"] == "pass"

    def test_to_telethon_format_socks5_no_auth(self, tmp_path):
        """to_telethon_format converts socks5 proxy without auth."""
        mgr = self._make_manager(str(tmp_path))
        config = {
            "protocol": "socks5",
            "host": "1.2.3.4",
            "port": 1080,
            "username": None,
            "password": None
        }
        result = mgr.to_telethon_format(config)
        assert result["proxy_type"] == "socks5"
        assert result["rdns"] is True
        assert "username" not in result

    def test_to_telethon_format_http_with_auth(self, tmp_path):
        """to_telethon_format converts http proxy with auth."""
        mgr = self._make_manager(str(tmp_path))
        config = {
            "protocol": "http",
            "host": "proxy.com",
            "port": 3128,
            "username": "u",
            "password": "p"
        }
        result = mgr.to_telethon_format(config)
        assert result["proxy_type"] == "http"
        assert result["username"] == "u"
        assert result["password"] == "p"

    def test_to_telethon_format_http_no_auth(self, tmp_path):
        """to_telethon_format converts http proxy without auth (no username/password fields)."""
        mgr = self._make_manager(str(tmp_path))
        config = {
            "protocol": "http",
            "host": "proxy.com",
            "port": 3128,
            "username": None,
            "password": None
        }
        result = mgr.to_telethon_format(config)
        assert result["proxy_type"] == "http"
        assert "username" not in result
        assert "password" not in result

    def test_to_telethon_format_socks4(self, tmp_path):
        """to_telethon_format converts socks4 with username only."""
        mgr = self._make_manager(str(tmp_path))
        config = {
            "protocol": "socks4",
            "host": "host",
            "port": 1080,
            "username": "user",
            "password": None
        }
        result = mgr.to_telethon_format(config)
        assert result["proxy_type"] == "socks4"
        assert result["username"] == "user"
        assert "password" not in result

    def test_get_global_proxy_telethon(self, tmp_path):
        """get_global_proxy returns Telethon-formatted global proxy."""
        mgr = self._make_manager(str(tmp_path))
        mgr.set_global_proxy("socks5", "1.2.3.4", 1080)

        result = mgr.get_global_proxy()
        assert result is not None
        assert result["proxy_type"] == "socks5"
        assert result["addr"] == "1.2.3.4"

    def test_get_global_proxy_none(self, tmp_path):
        """get_global_proxy returns None when no global proxy set."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.get_global_proxy() is None

    def test_get_proxy_existing(self, tmp_path):
        """get_proxy returns Telethon-formatted proxy for existing ID."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_proxy("p1", "http", "host", 8080)

        result = mgr.get_proxy("p1")
        assert result is not None
        assert result["proxy_type"] == "http"

    def test_get_proxy_nonexistent(self, tmp_path):
        """get_proxy returns None for missing proxy ID."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.get_proxy("nope") is None

    def test_get_proxy_for_account_with_assigned(self, tmp_path):
        """get_proxy_for_account returns assigned proxy over global."""
        mgr = self._make_manager(str(tmp_path))
        mgr.set_global_proxy("http", "global.host", 3128)
        mgr.add_proxy("p1", "socks5", "specific.host", 1080)
        mgr.assign_proxy_to_account("acc1", "p1")

        result = mgr.get_proxy_for_account("acc1")
        assert result["addr"] == "specific.host"

    def test_get_proxy_for_account_falls_back_to_global(self, tmp_path):
        """get_proxy_for_account returns global proxy when no specific assigned."""
        mgr = self._make_manager(str(tmp_path))
        mgr.set_global_proxy("http", "global.host", 3128)

        result = mgr.get_proxy_for_account("acc1")
        assert result["addr"] == "global.host"

    def test_get_proxy_for_account_no_proxy(self, tmp_path):
        """get_proxy_for_account returns None when no proxies configured."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.get_proxy_for_account("acc1") is None

    def test_list_proxies(self, tmp_path):
        """list_proxies returns all proxy info."""
        mgr = self._make_manager(str(tmp_path))
        mgr.set_global_proxy("http", "h", 80)
        mgr.add_proxy("p1", "socks5", "h2", 1080)

        result = mgr.list_proxies()
        assert result["global"] is not None
        assert "p1" in result["proxies"]
        assert "stats" in result

    def test_load_from_existing_file(self, tmp_path):
        """ProxyManager loads from existing file."""
        proxies_file = os.path.join(str(tmp_path), "proxies.json")
        data = {
            "global": {"protocol": "http", "host": "g.com", "port": 80},
            "proxies": {
                "p1": {"proxy_id": "p1", "protocol": "socks5", "host": "h", "port": 1080}
            },
            "stats": {"p1": {"success_count": 5, "fail_count": 1}}
        }
        with open(proxies_file, 'w') as f:
            json.dump(data, f)

        with patch("proxy_manager.PROXIES_FILE", proxies_file), \
             patch("proxy_manager.ACCOUNTS_DIR", str(tmp_path)):
            from proxy_manager import ProxyManager
            mgr = ProxyManager()
            assert mgr.global_proxy["host"] == "g.com"
            assert "p1" in mgr.proxies
            assert mgr.proxy_stats["p1"]["success_count"] == 5
