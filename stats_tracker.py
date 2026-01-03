#!/usr/bin/env python3
"""
统计追踪模块
追踪账号使用量、消息发送量、活跃度分析
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict


ACCOUNTS_DIR = "./accounts"
STATS_FILE = os.path.join(ACCOUNTS_DIR, "stats.json")


class StatsTracker:
    """统计追踪器"""

    def __init__(self):
        self.stats: Dict = {}
        self._load_stats()

    def _load_stats(self):
        """加载统计数据"""
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                self.stats = json.load(f)

    def _save_stats(self):
        """保存统计数据"""
        os.makedirs(ACCOUNTS_DIR, exist_ok=True)
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

    def _get_today(self) -> str:
        """获取今天的日期字符串"""
        return datetime.now().strftime("%Y-%m-%d")

    def _get_week(self) -> str:
        """获取本周的标识"""
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        return week_start.strftime("%Y-W%W")

    def init_account_stats(self, account_id: str):
        """初始化账号统计数据"""
        if account_id not in self.stats:
            self.stats[account_id] = {
                "total_uses": 0,
                "total_messages_sent": 0,
                "daily": {},
                "weekly": {},
                "first_use": datetime.now().isoformat(),
                "last_use": None
            }
            self._save_stats()

    def record_use(self, account_id: str):
        """记录账号使用"""
        self.init_account_stats(account_id)

        today = self._get_today()
        week = self._get_week()

        self.stats[account_id]["total_uses"] += 1
        self.stats[account_id]["last_use"] = datetime.now().isoformat()

        # 每日统计
        if today not in self.stats[account_id]["daily"]:
            self.stats[account_id]["daily"][today] = {"uses": 0, "messages": 0}
        self.stats[account_id]["daily"][today]["uses"] += 1

        # 每周统计
        if week not in self.stats[account_id]["weekly"]:
            self.stats[account_id]["weekly"][week] = {"uses": 0, "messages": 0}
        self.stats[account_id]["weekly"][week]["uses"] += 1

        self._save_stats()

    def record_message_sent(self, account_id: str, count: int = 1):
        """记录消息发送"""
        self.init_account_stats(account_id)

        today = self._get_today()
        week = self._get_week()

        self.stats[account_id]["total_messages_sent"] += count

        # 每日统计
        if today not in self.stats[account_id]["daily"]:
            self.stats[account_id]["daily"][today] = {"uses": 0, "messages": 0}
        self.stats[account_id]["daily"][today]["messages"] += count

        # 每周统计
        if week not in self.stats[account_id]["weekly"]:
            self.stats[account_id]["weekly"][week] = {"uses": 0, "messages": 0}
        self.stats[account_id]["weekly"][week]["messages"] += count

        self._save_stats()

    def get_account_stats(self, account_id: str) -> Dict:
        """
        获取账号统计

        Args:
            account_id: 账号ID

        Returns:
            统计数据
        """
        if account_id not in self.stats:
            return {}

        return self.stats[account_id]

    def get_daily_stats(self, date: str = None) -> Dict:
        """
        获取每日统计

        Args:
            date: 日期 (YYYY-MM-DD)，None表示今天

        Returns:
            {account_id: {uses, messages}}
        """
        if date is None:
            date = self._get_today()

        result = {}
        for account_id, stats in self.stats.items():
            if date in stats.get("daily", {}):
                result[account_id] = stats["daily"][date]

        return result

    def get_weekly_stats(self, week: str = None) -> Dict:
        """
        获取每周统计

        Args:
            week: 周标识 (YYYY-WWW)，None表示本周

        Returns:
            {account_id: {uses, messages}}
        """
        if week is None:
            week = self._get_week()

        result = {}
        for account_id, stats in self.stats.items():
            if week in stats.get("weekly", {}):
                result[account_id] = stats["weekly"][week]

        return result

    def get_top_accounts(self, by: str = "uses", limit: int = 10, period: str = "all") -> List[Dict]:
        """
        获取最活跃账号

        Args:
            by: 排序依据 (uses/messages)
            limit: 返回数量
            period: 时间范围 (all/today/week)

        Returns:
            [{account_id, value}, ...]
        """
        results = []

        for account_id, stats in self.stats.items():
            if period == "all":
                value = stats.get("total_messages_sent" if by == "messages" else "total_uses", 0)
            elif period == "today":
                today = self._get_today()
                value = stats.get("daily", {}).get(today, {}).get(by, 0)
            elif period == "week":
                week = self._get_week()
                value = stats.get("weekly", {}).get(week, {}).get(by, 0)
            else:
                value = 0

            results.append({
                "account_id": account_id,
                "value": value
            })

        # 排序
        results.sort(key=lambda x: x["value"], reverse=True)
        return results[:limit]

    def get_activity_trend(self, account_id: str, days: int = 7) -> List[Dict]:
        """
        获取活跃度趋势

        Args:
            account_id: 账号ID
            days: 天数

        Returns:
            [{date, uses, messages}, ...]
        """
        if account_id not in self.stats:
            return []

        result = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_data = self.stats[account_id].get("daily", {}).get(date, {"uses": 0, "messages": 0})
            result.append({
                "date": date,
                "uses": daily_data.get("uses", 0),
                "messages": daily_data.get("messages", 0)
            })

        return list(reversed(result))

    def get_summary(self) -> Dict:
        """获取总体统计摘要"""
        total_uses = sum(s.get("total_uses", 0) for s in self.stats.values())
        total_messages = sum(s.get("total_messages_sent", 0) for s in self.stats.values())

        today = self._get_today()
        today_uses = 0
        today_messages = 0
        for stats in self.stats.values():
            today_data = stats.get("daily", {}).get(today, {})
            today_uses += today_data.get("uses", 0)
            today_messages += today_data.get("messages", 0)

        return {
            "total_accounts": len(self.stats),
            "total_uses": total_uses,
            "total_messages_sent": total_messages,
            "today_uses": today_uses,
            "today_messages": today_messages,
            "most_active": self.get_top_accounts(by="uses", limit=5, period="today"),
            "last_updated": datetime.now().isoformat()
        }


# 全局实例
stats_tracker = StatsTracker()
