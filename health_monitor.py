#!/usr/bin/env python3
"""
健康监控模块
监控账号健康度、代理响应时间、风险评估
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from account_manager import account_manager
from proxy_manager import proxy_manager


ACCOUNTS_DIR = "./accounts"
HEALTH_FILE = os.path.join(ACCOUNTS_DIR, "health.json")


class HealthMonitor:
    """健康监控器"""

    def __init__(self):
        self.health_data: Dict = {}
        self._load_health()
        self._monitoring = False

    def _load_health(self):
        """加载健康数据"""
        if os.path.exists(HEALTH_FILE):
            with open(HEALTH_FILE, 'r', encoding='utf-8') as f:
                self.health_data = json.load(f)

    def _save_health(self):
        """保存健康数据"""
        os.makedirs(ACCOUNTS_DIR, exist_ok=True)
        with open(HEALTH_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.health_data, f, ensure_ascii=False, indent=2)

    def init_account_health(self, account_id: str):
        """初始化账号健康数据"""
        if account_id not in self.health_data:
            self.health_data[account_id] = {
                "login_fail_count": 0,
                "login_success_count": 0,
                "message_success_count": 0,
                "message_fail_count": 0,
                "last_login_fail": None,
                "last_message_fail": None,
                "consecutive_fails": 0,
                "risk_level": "low",  # low, medium, high
                "banned": False,
                "proxy_response_time": 0,
                "last_check": None
            }
            self._save_health()

    def record_login_success(self, account_id: str):
        """记录登录成功"""
        self.init_account_health(account_id)
        self.health_data[account_id]["login_success_count"] += 1
        self.health_data[account_id]["consecutive_fails"] = 0
        self.health_data[account_id]["last_check"] = datetime.now().isoformat()
        self._update_risk_level(account_id)
        self._save_health()

    def record_login_failure(self, account_id: str, error: str = None):
        """记录登录失败"""
        self.init_account_health(account_id)
        self.health_data[account_id]["login_fail_count"] += 1
        self.health_data[account_id]["last_login_fail"] = {
            "time": datetime.now().isoformat(),
            "error": error
        }
        self.health_data[account_id]["consecutive_fails"] += 1
        self.health_data[account_id]["last_check"] = datetime.now().isoformat()
        self._update_risk_level(account_id)
        self._save_health()

    def record_message_success(self, account_id: str):
        """记录消息发送成功"""
        self.init_account_health(account_id)
        self.health_data[account_id]["message_success_count"] += 1
        self.health_data[account_id]["consecutive_fails"] = 0
        self.health_data[account_id]["last_check"] = datetime.now().isoformat()
        self._update_risk_level(account_id)
        self._save_health()

    def record_message_failure(self, account_id: str, error: str = None):
        """记录消息发送失败"""
        self.init_account_health(account_id)
        self.health_data[account_id]["message_fail_count"] += 1
        self.health_data[account_id]["last_message_fail"] = {
            "time": datetime.now().isoformat(),
            "error": error
        }
        self.health_data[account_id]["consecutive_fails"] += 1
        self.health_data[account_id]["last_check"] = datetime.now().isoformat()
        self._update_risk_level(account_id)
        self._save_health()

    def record_proxy_response_time(self, account_id: str, response_time: float):
        """记录代理响应时间"""
        self.init_account_health(account_id)

        # 更新平均响应时间
        current = self.health_data[account_id]["proxy_response_time"]
        if current == 0:
            self.health_data[account_id]["proxy_response_time"] = response_time
        else:
            self.health_data[account_id]["proxy_response_time"] = (current + response_time) / 2

        self.health_data[account_id]["last_check"] = datetime.now().isoformat()
        self._save_health()

    def _update_risk_level(self, account_id: str):
        """更新风险等级"""
        health = self.health_data[account_id]

        consecutive_fails = health.get("consecutive_fails", 0)
        login_fail_rate = 0
        total_login = health.get("login_success_count", 0) + health.get("login_fail_count", 0)
        if total_login > 0:
            login_fail_rate = health.get("login_fail_count", 0) / total_login

        # 风险评估逻辑
        if consecutive_fails >= 5 or login_fail_rate >= 0.8:
            health["risk_level"] = "high"
        elif consecutive_fails >= 2 or login_fail_rate >= 0.5:
            health["risk_level"] = "medium"
        else:
            health["risk_level"] = "low"

        # 检查是否被封号
        error_str = str(health.get("last_login_fail", {})).lower() + str(health.get("last_message_fail", {})).lower()
        if any(keyword in error_str for keyword in ["banned", "deactivated", "flood", "restricted"]):
            health["banned"] = True
            health["risk_level"] = "high"

    def get_health_report(self, account_id: str = None) -> Dict:
        """
        获取健康报告

        Args:
            account_id: 账号ID，None表示获取所有账号

        Returns:
            健康报告
        """
        if account_id:
            return self.health_data.get(account_id, {})

        # 获取高风险账号列表
        risk_accounts = self.get_risk_accounts()

        return {
            "total_accounts": len(account_manager.accounts),
            "online_accounts": sum(1 for a in account_manager.list_accounts() if a["status"] == "online"),
            "offline_accounts": sum(1 for a in account_manager.list_accounts() if a["status"] == "offline"),
            "high_risk": sum(1 for h in self.health_data.values() if h.get("risk_level") == "high"),
            "medium_risk": sum(1 for h in self.health_data.values() if h.get("risk_level") == "medium"),
            "low_risk": sum(1 for h in self.health_data.values() if h.get("risk_level") == "low"),
            "banned": sum(1 for h in self.health_data.values() if h.get("banned")),
            "risk_accounts": risk_accounts,  # 前端需要的字段
            "details": self.health_data
        }

    async def check_account_health(self, account_id: str) -> Dict:
        """
        检查账号健康状态

        Args:
            account_id: 账号ID

        Returns:
            健康状态
        """
        try:
            client = await account_manager.get_client(account_id)
            if not client:
                self.record_login_failure(account_id, "无法获取客户端")
                return {"status": "unhealthy", "error": "无法连接"}

            if not await client.is_user_authorized():
                self.record_login_failure(account_id, "未授权")
                return {"status": "unhealthy", "error": "未授权"}

            # 测试发送消息能力（获取me）
            me = await client.get_me()

            # 记录成功
            self.record_login_success(account_id)

            # 检查代理响应时间
            proxy = proxy_manager.get_proxy_for_account(account_id)
            if proxy:
                # 转换回原始格式用于测试
                proxy_for_test = None
                if proxy_manager.global_proxy and proxy_manager.global_proxy.get("host"):
                    proxy_for_test = proxy_manager.global_proxy
                else:
                    # 查找账号关联的独立代理
                    for proxy_id, proxy_config in proxy_manager.proxies.items():
                        if "assigned_to" in proxy_config and account_id in proxy_config["assigned_to"]:
                            proxy_for_test = proxy_config
                            break

                if proxy_for_test:
                    result = await proxy_manager.test_proxy(proxy_for_test)
                    if result.get("success"):
                        self.record_proxy_response_time(account_id, result.get("response_time", 0))

            return {
                "status": "healthy",
                "account_id": account_id,
                "username": me.username,
                "phone": me.phone,
                "risk_level": self.health_data.get(account_id, {}).get("risk_level", "low")
            }

        except Exception as e:
            self.record_login_failure(account_id, str(e))
            return {"status": "unhealthy", "error": str(e)}

    async def start_monitoring(self, interval: int = 60):
        """
        启动后台监控

        Args:
            interval: 检查间隔（秒）
        """
        if self._monitoring:
            return

        self._monitoring = True

        async def monitor_loop():
            while self._monitoring:
                for account_id in account_manager.accounts.keys():
                    await self.check_account_health(account_id)
                await asyncio.sleep(interval)

        asyncio.create_task(monitor_loop())

    def stop_monitoring(self):
        """停止监控"""
        self._monitoring = False

    def get_risk_accounts(self) -> List[str]:
        """获取高风险账号列表"""
        return [
            acc_id for acc_id, health in self.health_data.items()
            if health.get("risk_level") in ["medium", "high"] or health.get("banned")
        ]


# 全局实例
health_monitor = HealthMonitor()
