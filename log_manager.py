#!/usr/bin/env python3
"""
操作日志管理模块
持久化存储所有操作日志
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from collections import deque


ACCOUNTS_DIR = "./accounts"
LOG_FILE = os.path.join(ACCOUNTS_DIR, "logs.json")
MAX_LOGS = 1000  # 最多保留1000条日志


class LogManager:
    """操作日志管理器"""

    def __init__(self):
        self.logs: List[Dict] = []
        self._load_logs()

    def _load_logs(self):
        """加载日志"""
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    self.logs = json.load(f)
            except:
                self.logs = []

    def _save_logs(self):
        """保存日志"""
        os.makedirs(ACCOUNTS_DIR, exist_ok=True)
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)

    def add_log(self, action: str, account: str, detail: str = "", level: str = "info") -> None:
        """
        添加日志

        Args:
            action: 操作类型 (登录, 删除, 发送, 等)
            account: 账号ID
            detail: 详细信息
            level: 日志级别 (info, warning, error, success)
        """
        now_iso = datetime.now().isoformat()
        log = {
            "time": now_iso,
            "timestamp": now_iso,  # 前端使用的字段名
            "action": action,
            "account": account,
            "detail": detail,
            "level": level
        }

        self.logs.append(log)

        # 限制日志数量
        if len(self.logs) > MAX_LOGS:
            self.logs = self.logs[-MAX_LOGS:]

        self._save_logs()

    def get_logs(self, limit: int = 100, account: str = None, action: str = None) -> List[Dict]:
        """
        获取日志

        Args:
            limit: 返回数量
            account: 筛选账号
            action: 筛选操作类型

        Returns:
            日志列表（倒序）
        """
        logs = self.logs

        # 筛选
        if account:
            logs = [log for log in logs if log.get("account") == account]
        if action:
            logs = [log for log in logs if log.get("action") == action]

        # 倒序并限制数量（返回最新的记录）
        return list(reversed(logs))[:limit]

    def clear_logs(self, before: str = None) -> int:
        """
        清空日志

        Args:
            before: 清空指定时间之前的日志

        Returns:
            清空的数量
        """
        if before:
            old_count = len(self.logs)
            self.logs = [
                log for log in self.logs
                if log.get("time", "") >= before
            ]
            cleared = old_count - len(self.logs)
        else:
            cleared = len(self.logs)
            self.logs = []

        self._save_logs()
        return cleared

    def get_stats(self) -> Dict:
        """获取日志统计"""
        stats = {
            "total": len(self.logs),
            "by_action": {},
            "by_level": {},
            "by_account": {},
            "recent": self.get_logs(10)
        }

        for log in self.logs:
            # 按操作类型统计
            action = log.get("action", "unknown")
            stats["by_action"][action] = stats["by_action"].get(action, 0) + 1

            # 按级别统计
            level = log.get("level", "info")
            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

            # 按账号统计
            account = log.get("account", "system")
            stats["by_account"][account] = stats["by_account"].get(account, 0) + 1

        return stats


# 全局实例
log_manager = LogManager()
