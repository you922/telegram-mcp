#!/usr/bin/env python3
"""
定时任务调度器
支持 cron 表达式和定时执行
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from croniter import croniter

# 导入管理模块
from account_manager import account_manager
from template_manager import template_manager
from log_manager import log_manager


ACCOUNTS_DIR = "./accounts"
SCHEDULE_FILE = os.path.join(ACCOUNTS_DIR, "schedules.json")


class TaskScheduler:
    """定时任务调度器"""

    def __init__(self):
        self.schedules: Dict[str, Dict] = {}
        self.running = False
        self._load_schedules()

        # 主任务执行器 - 引用 main.py 中的发送功能
        self._send_message_func = None

    def _load_schedules(self):
        """加载定时任务配置"""
        if os.path.exists(SCHEDULE_FILE):
            try:
                with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.schedules = data.get("schedules", {})
            except:
                self.schedules = {}

    def _save_schedules(self):
        """保存定时任务配置"""
        os.makedirs(ACCOUNTS_DIR, exist_ok=True)
        with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "schedules": self.schedules,
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

    def set_send_message_function(self, func: Callable):
        """设置发送消息函数（从 main.py 导入）"""
        self._send_message_func = func

    def add_schedule(
        self,
        schedule_id: str,
        name: str,
        cron: str,
        action: str,
        target: str,  # chat_id
        message: str = None,
        template_id: str = None,
        accounts: List[str] = None,
        account_ids: List[str] = None,  # 兼容 dashboard.py 传入的参数名
        enabled: bool = True
    ) -> bool:
        """
        添加定时任务

        Args:
            schedule_id: 任务ID
            name: 任务名称
            cron: cron 表达式 (如 "0 9 * * *" 每天早上9点)
            action: 执行动作 (send_message, send_template)
            target: 目标 (chat_id 或 username)
            message: 消息内容（send_message 时使用）
            template_id: 模板ID（send_template 时使用）
            accounts: 账号列表，None表示全部账号
            enabled: 是否启用

        Returns:
            是否成功
        """
        # 验证 cron 表达式
        try:
            croniter(cron)
        except ValueError as e:
            return False

        # 统一账号列表参数（兼容 account_ids 和 accounts）
        accounts_list = account_ids or accounts

        self.schedules[schedule_id] = {
            "id": schedule_id,
            "schedule_id": schedule_id,  # 前端使用的字段名
            "name": name,
            "cron": cron,
            "action": action,
            "target": target,
            "message": message,
            "template_id": template_id,
            "accounts": accounts_list,
            "account_ids": accounts_list,  # 兼容前端使用的字段名
            "enabled": enabled,
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "lastRun": None,  # 前端使用的字段名（驼峰命名）
            "next_run": self._get_next_run(cron),
            "run_count": 0,
            "fail_count": 0
        }

        self._save_schedules()
        return True

    def _get_next_run(self, cron: str) -> str:
        """获取下次执行时间"""
        try:
            cron_obj = croniter(cron, datetime.now())
            return cron_obj.get_next(datetime).isoformat()
        except:
            return ""

    def remove_schedule(self, schedule_id: str) -> bool:
        """删除定时任务"""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            self._save_schedules()
            return True
        return False

    def delete_schedule(self, schedule_id: str) -> bool:
        """删除定时任务（别名，与 remove_schedule 功能相同）"""
        return self.remove_schedule(schedule_id)

    def get_next_run(self, schedule_id: str) -> Optional[str]:
        """获取指定任务的下次执行时间"""
        schedule = self.get_schedule(schedule_id)
        if schedule:
            return schedule.get("next_run")
        return None

    def toggle_schedule(self, schedule_id: str) -> bool:
        """切换任务状态"""
        if schedule_id in self.schedules:
            self.schedules[schedule_id]["enabled"] = not self.schedules[schedule_id]["enabled"]
            self._save_schedules()
            return True
        return False

    def list_schedules(self) -> List[Dict]:
        """列出所有任务"""
        schedules = []
        for s in self.schedules.values():
            # 确保所有前端需要的字段都存在
            schedule = dict(s)
            # 确保 schedule_id 字段存在
            if "schedule_id" not in schedule and "id" in schedule:
                schedule["schedule_id"] = schedule["id"]
            # 确保 lastRun 字段存在
            if "lastRun" not in schedule and "last_run" in schedule:
                schedule["lastRun"] = schedule["last_run"]
            # 确保 account_ids 字段存在
            if "account_ids" not in schedule and "accounts" in schedule:
                schedule["account_ids"] = schedule["accounts"]
            schedules.append(schedule)
        return schedules

    def get_schedule(self, schedule_id: str) -> Optional[Dict]:
        """获取指定任务"""
        return self.schedules.get(schedule_id)

    async def _execute_schedule(self, schedule: Dict) -> bool:
        """
        执行定时任务

        Args:
            schedule: 任务配置

        Returns:
            是否成功
        """
        try:
            action = schedule["action"]
            target = schedule["target"]
            # 兼容 accounts 和 account_ids 字段
            accounts = schedule.get("accounts") or schedule.get("account_ids")

            # 如果没有指定账号，使用全部账号
            if not accounts:
                accounts = list(account_manager.accounts.keys())

            results = []

            for account_id in accounts:
                try:
                    # 获取客户端
                    client = await account_manager.get_client(account_id)
                    if not client:
                        log_manager.add_log("定时任务", account_id, f"获取客户端失败", "error")
                        continue

                    # 处理特殊 target 值 'all' - 发送到 Saved Messages
                    effective_target = 'me' if target == 'all' else target

                    # 执行动作
                    if action == "send_message":
                        message = schedule.get("message", "")
                        entity = await client.get_entity(effective_target)
                        await client.send_message(entity, message)
                        results.append({"account": account_id, "success": True})

                    elif action == "send_template":
                        template_id = schedule.get("template_id")
                        if template_id:
                            # 渲染模板
                            content = template_manager.render_template(
                                template_id,
                                name=account_id,
                                time=datetime.now().strftime("%H:%M"),
                                date=datetime.now().strftime("%Y-%m-%d")
                            )
                            if content:
                                entity = await client.get_entity(effective_target)
                                await client.send_message(entity, content)
                                results.append({"account": account_id, "success": True})

                    log_manager.add_log("定时任务", account_id, f"执行成功: {schedule['name']}", "success")

                except Exception as e:
                    log_manager.add_log("定时任务", account_id, f"执行失败: {str(e)}", "error")
                    results.append({"account": account_id, "success": False, "error": str(e)})

            # 更新任务统计
            now_iso = datetime.now().isoformat()
            schedule["last_run"] = now_iso
            schedule["lastRun"] = now_iso  # 前端使用的字段名（驼峰命名）
            schedule["run_count"] = schedule.get("run_count", 0) + 1
            schedule["next_run"] = self._get_next_run(schedule["cron"])

            # 检查是否有失败
            if any(not r.get("success") for r in results):
                schedule["fail_count"] = schedule.get("fail_count", 0) + 1

            self._save_schedules()
            return True

        except Exception as e:
            log_manager.add_log("定时任务", "system", f"执行任务 {schedule['name']} 失败: {str(e)}", "error")
            return False

    async def start(self):
        """启动调度器"""
        if self.running:
            return

        self.running = True
        print("📅 定时任务调度器已启动")

        while self.running:
            try:
                now = datetime.now()

                for schedule_id, schedule in self.schedules.items():
                    # 检查是否启用
                    if not schedule.get("enabled", True):
                        continue

                    # 检查是否到达执行时间
                    next_run = schedule.get("next_run", "")
                    if next_run:
                        next_time = datetime.fromisoformat(next_run)
                        # 如果当前时间已经超过或接近下次执行时间（允许1分钟误差）
                        if (now - next_time).total_seconds() >= 0:
                            if (now - next_time).total_seconds() < 60:  # 1分钟内执行
                                # 执行任务
                                print(f"⏰ 执行定时任务: {schedule['name']}")
                                await self._execute_schedule(schedule)

                # 每分钟检查一次
                await asyncio.sleep(60)

            except Exception as e:
                print(f"调度器错误: {e}")
                await asyncio.sleep(60)

    def stop(self):
        """停止调度器"""
        self.running = False
        print("📅 定时任务调度器已停止")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total": len(self.schedules),
            "enabled": sum(1 for s in self.schedules.values() if s.get("enabled", True)),
            "disabled": sum(1 for s in self.schedules.values() if not s.get("enabled", True)),
            "total_runs": sum(s.get("run_count", 0) for s in self.schedules.values()),
            "pending": len([s for s in self.schedules.values() if s.get("enabled", True)])
        }


# 全局实例
task_scheduler = TaskScheduler()
