#!/usr/bin/env python3
"""
代理管理核心模块
支持全局代理和独立代理，真实生效
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp


ACCOUNTS_DIR = "./accounts"
PROXIES_FILE = os.path.join(ACCOUNTS_DIR, "proxies.json")


class ProxyManager:
    """代理管理器"""

    def __init__(self):
        self.proxies: Dict[str, Dict] = {}  # 代理配置
        self.global_proxy: Optional[Dict] = None  # 全局代理
        self.proxy_stats: Dict[str, Dict] = {}  # 代理统计
        self._load_proxies()

    def _load_proxies(self):
        """加载代理配置"""
        if os.path.exists(PROXIES_FILE):
            with open(PROXIES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.global_proxy = data.get("global")
                self.proxies = data.get("proxies", {})
                self.proxy_stats = data.get("stats", {})

    def _save_proxies(self):
        """保存代理配置"""
        os.makedirs(ACCOUNTS_DIR, exist_ok=True)
        with open(PROXIES_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "global": self.global_proxy,
                "proxies": self.proxies,
                "stats": self.proxy_stats
            }, f, ensure_ascii=False, indent=2)

    def list_proxies(self) -> Dict:
        """
        列出所有代理

        Returns:
            {
                "global": 全局代理配置,
                "proxies": 账号独立代理列表,
                "stats": 代理统计信息
            }
        """
        return {
            "global": self.global_proxy,
            "proxies": self.proxies,
            "stats": self.proxy_stats
        }

    def add_proxy(
        self,
        proxy_id: str,
        protocol: str,
        host: str,
        port: int,
        username: str = None,
        password: str = None
    ) -> bool:
        """
        添加代理

        Args:
            proxy_id: 代理ID
            protocol: 协议 (socks5, http, https, socks4)
            host: 主机地址
            port: 端口
            username: 用户名
            password: 密码

        Returns:
            是否成功
        """
        if protocol.lower() not in ["socks5", "http", "https", "socks4"]:
            return False

        self.proxies[proxy_id] = {
            "proxy_id": proxy_id,
            "protocol": protocol.lower(),
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "created_at": datetime.now().isoformat()
        }

        # 初始化统计
        if proxy_id not in self.proxy_stats:
            self.proxy_stats[proxy_id] = {
                "success_count": 0,
                "fail_count": 0,
                "avg_response_time": 0,
                "last_test": None
            }

        self._save_proxies()
        return True

    def delete_proxy(self, proxy_id: str) -> bool:
        """
        删除代理

        Args:
            proxy_id: 代理ID

        Returns:
            是否成功
        """
        if proxy_id not in self.proxies:
            return False

        del self.proxies[proxy_id]

        # 清除相关账号的代理引用
        # (实际使用时会从 account_manager 读取)

        self._save_proxies()
        return True

    def set_global_proxy(
        self,
        protocol: str,
        host: str,
        port: int,
        username: str = None,
        password: str = None
    ) -> bool:
        """
        设置全局代理

        Args:
            protocol: 协议
            host: 主机
            port: 端口
            username: 用户名
            password: 密码

        Returns:
            是否成功
        """
        if protocol.lower() not in ["socks5", "http", "https", "socks4"]:
            return False

        self.global_proxy = {
            "protocol": protocol.lower(),
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "updated_at": datetime.now().isoformat()
        }

        self._save_proxies()
        return True

    def remove_global_proxy(self) -> bool:
        """
        移除全局代理

        Returns:
            是否成功
        """
        self.global_proxy = None
        self._save_proxies()
        return True

    def assign_proxy_to_account(self, account_id: str, proxy_id: str) -> bool:
        """
        为账号分配代理

        Args:
            account_id: 账号ID
            proxy_id: 代理ID

        Returns:
            是否成功
        """
        if proxy_id not in self.proxies:
            return False

        # 这个关联关系应该存储在账号配置中
        # 但为了统一管理，我们也在代理配置中记录
        if "assigned_to" not in self.proxies[proxy_id]:
            self.proxies[proxy_id]["assigned_to"] = []

        if account_id not in self.proxies[proxy_id]["assigned_to"]:
            self.proxies[proxy_id]["assigned_to"].append(account_id)

        self._save_proxies()
        return True

    def unassign_proxy_from_account(self, account_id: str, proxy_id: str) -> bool:
        """
        取消账号的代理分配

        Args:
            account_id: 账号ID
            proxy_id: 代理ID

        Returns:
            是否成功
        """
        if proxy_id not in self.proxies:
            return False

        if "assigned_to" in self.proxies[proxy_id]:
            if account_id in self.proxies[proxy_id]["assigned_to"]:
                self.proxies[proxy_id]["assigned_to"].remove(account_id)

        self._save_proxies()
        return True

    def to_telethon_format(self, proxy_config: Dict) -> Dict:
        """
        转换为 Telethon 代理格式

        智能处理各种代理配置组合：
        - 有用户名和密码
        - 只有密码
        - 只有用户名
        - 都没有

        Args:
            proxy_config: 代理配置

        Returns:
            Telethon 格式的代理配置
        """
        protocol = proxy_config.get("protocol", "socks5")
        host = proxy_config.get('host')
        port = proxy_config.get('port')
        username = proxy_config.get('username')
        password = proxy_config.get('password')

        # 基础配置
        config = {
            'proxy_type': protocol,
            'addr': host,
            'port': port
        }

        # 根据不同协议添加认证信息
        if protocol == "socks5":
            config['rdns'] = True
            # SOCKS5 支持：有用户名+密码、只有密码、都没有
            if username or password:
                config['username'] = username or ''
                config['password'] = password or ''

        elif protocol == "http" or protocol == "https":
            # HTTP/HTTPS 支持：有用户名+密码
            if username and password:
                config['username'] = username
                config['password'] = password

        elif protocol == "socks4":
            # SOCKS4 只支持用户名，不支持密码
            if username:
                config['username'] = username

        return config

    def get_global_proxy(self) -> Optional[Dict]:
        """
        获取全局代理配置（Telethon格式）

        Returns:
            Telethon 格式的代理配置，如果无全局代理则返回 None
        """
        if self.global_proxy and self.global_proxy.get("host") and self.global_proxy.get("port"):
            return self.to_telethon_format(self.global_proxy)
        return None

    def get_proxy(self, proxy_id: str) -> Optional[Dict]:
        """
        获取指定代理配置（Telethon格式）

        Args:
            proxy_id: 代理ID

        Returns:
            Telethon 格式的代理配置，如果代理不存在则返回 None
        """
        if proxy_id in self.proxies:
            proxy_config = self.proxies[proxy_id]
            if proxy_config.get("host") and proxy_config.get("port"):
                return self.to_telethon_format(proxy_config)
        return None

    def get_proxy_for_account(self, account_id: str) -> Optional[Dict]:
        """
        获取账号的代理配置（Telethon格式）

        Args:
            account_id: 账号ID

        Returns:
            Telethon 格式的代理配置
        """
        # 1. 先检查账号是否有独立代理
        for proxy_id, proxy_config in self.proxies.items():
            if "assigned_to" in proxy_config:
                if account_id in proxy_config["assigned_to"]:
                    # 验证代理配置有效
                    if proxy_config.get("host") and proxy_config.get("port"):
                        return self.to_telethon_format(proxy_config)

        # 2. 使用全局代理（必须有有效的host和port）
        if self.global_proxy and self.global_proxy.get("host") and self.global_proxy.get("port"):
            return self.to_telethon_format(self.global_proxy)

        # 3. 无代理
        return None

    async def test_proxy(self, proxy_config: Dict, timeout: int = 10) -> Dict:
        """
        测试代理连接

        Args:
            proxy_config: 代理配置
            timeout: 超时时间（秒）

        Returns:
            {
                "success": True/False,
                "response_time": 响应时间(ms),
                "error": 错误信息
            }
        """
        start_time = datetime.now()

        try:
            # 构建代理URL
            protocol = proxy_config.get("protocol", "http")
            host = proxy_config.get("host")
            port = proxy_config.get("port")
            username = proxy_config.get("username")
            password = proxy_config.get("password")

            if username and password:
                proxy_url = f"{protocol}://{username}:{password}@{host}:{port}"
            else:
                proxy_url = f"{protocol}://{host}:{port}"

            # 测试连接（访问Google）
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://www.google.com",
                    proxy=proxy_url,
                    timeout=timeout
                ) as response:
                    if response.status == 200:
                        elapsed = (datetime.now() - start_time).total_seconds() * 1000
                        return {
                            "success": True,
                            "response_time": elapsed,
                            "status_code": response.status
                        }

            return {"success": False, "error": f"HTTP {response.status}"}

        except asyncio.TimeoutError:
            return {"success": False, "error": "连接超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_all_proxies(self) -> Dict:
        """
        测试所有代理

        Returns:
            {
                "global": 全局代理测试结果,
                "proxies": 独立代理测试结果列表
            }
        """
        results = {"global": None, "proxies": {}}

        # 测试全局代理
        if self.global_proxy:
            results["global"] = await self.test_proxy(self.global_proxy)
            self._update_proxy_stats("global", results["global"])

        # 测试独立代理
        for proxy_id, proxy_config in self.proxies.items():
            result = await self.test_proxy(proxy_config)
            results["proxies"][proxy_id] = result
            self._update_proxy_stats(proxy_id, result)

        self._save_proxies()
        return results

    def _update_proxy_stats(self, proxy_id: str, test_result: Dict):
        """更新代理统计信息"""
        if proxy_id not in self.proxy_stats:
            self.proxy_stats[proxy_id] = {
                "success_count": 0,
                "fail_count": 0,
                "avg_response_time": 0,
                "last_test": None
            }

        stats = self.proxy_stats[proxy_id]

        if test_result.get("success"):
            stats["success_count"] += 1
            # 更新平均响应时间
            response_time = test_result.get("response_time", 0)
            if stats["avg_response_time"] == 0:
                stats["avg_response_time"] = response_time
            else:
                stats["avg_response_time"] = (stats["avg_response_time"] + response_time) / 2
        else:
            stats["fail_count"] += 1

        stats["last_test"] = datetime.now().isoformat()


# 全局实例
proxy_manager = ProxyManager()
