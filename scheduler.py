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

from shared.config import ACCOUNTS_DIR
from shared.json_store import JsonStore

SCHEDULE_FILE = os.path.join(ACCOUNTS_DIR, "schedules.json")


class TaskScheduler:
    """定时任务调度器"""

    def __init__(self):
        self.schedules: Dict[str, Dict] = {}
        self.running = False
        self._store = JsonStore("schedules.json")
        self._load_schedules()

        # 主任务执行器 - 引用 main.py 中的发送功能
        self._send_message_func = None

    def _load_schedules(self):
        """加载定时任务配置"""
        data = self._store.load()
        self.schedules = data.get("schedules", {})

    def _save_schedules(self):
        """保存定时任务配置"""
        self._store.save({
            "schedules": self.schedules,
            "updated_at": datetime.now().isoformat()
        })

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
        enabled: bool = True,
        # 新参数
        execute_time: Dict = None,
        repeat: str = None,
        friend_ids: List = None,
        stranger_usernames: List = None,
        interval: int = 2000,
        auto_dedup: bool = True,
        validate_usernames: bool = True,
        **kwargs  # 忽略其他未知参数
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
            "fail_count": 0,
            # 新字段
            "execute_time": execute_time,
            "repeat": repeat,
            "friend_ids": friend_ids or [],
            "stranger_usernames": stranger_usernames or [],
            "interval": interval,
            "auto_dedup": auto_dedup,
            "validate_usernames": validate_usernames
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
            message = schedule.get("message", "")
            
            # 获取发送目标
            friend_ids = schedule.get("friend_ids", [])
            stranger_usernames = schedule.get("stranger_usernames", [])
            interval = schedule.get("interval", 2000)  # 毫秒
            
            # 兼容 accounts 和 account_ids 字段
            accounts = schedule.get("accounts") or schedule.get("account_ids")

            # 如果没有指定账号，使用全部账号
            if not accounts:
                accounts = list(account_manager.accounts.keys())

            results = []
            
            # 使用第一个账号发送（通常定时任务只选一个账号）
            account_id = accounts[0] if accounts else None
            if not account_id:
                log_manager.add_log("定时任务", "system", "没有可用账号", "error")
                return False

            try:
                # 获取客户端
                client = await account_manager.get_client(account_id)
                if not client:
                    log_manager.add_log("定时任务", account_id, "获取客户端失败", "error")
                    return False

                # 合并发送目标
                targets = []
                for fid in friend_ids:
                    targets.append({"type": "id", "value": fid})
                for username in stranger_usernames:
                    targets.append({"type": "username", "value": username})
                
                # 如果没有指定目标，发送到 Saved Messages
                if not targets:
                    targets = [{"type": "id", "value": "me"}]
                
                success_count = 0
                fail_count = 0
                
                for i, target in enumerate(targets):
                    try:
                        # 获取目标实体
                        target_value = target["value"]
                        entity = await client.get_entity(target_value)
                        
                        # 发送消息
                        # ai_execute 暂时和 send_message 一样（AI优化需要用户自己调用MCP）
                        await client.send_message(entity, message)
                        success_count += 1
                        
                        log_manager.add_log("定时任务", account_id, 
                            f"发送成功: {target_value}", "success")
                        
                        # 发送间隔（除了最后一条）
                        if i < len(targets) - 1:
                            await asyncio.sleep(interval / 1000)
                            
                    except Exception as e:
                        fail_count += 1
                        log_manager.add_log("定时任务", account_id, 
                            f"发送失败 {target_value}: {str(e)}", "error")
                
                results.append({
                    "account": account_id, 
                    "success": success_count > 0,
                    "sent": success_count,
                    "failed": fail_count
                })
                
                log_manager.add_log("定时任务", account_id, 
                    f"执行完成: {schedule['name']} (成功{success_count}/失败{fail_count})", 
                    "success" if fail_count == 0 else "warning")

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
                
                # 重新加载配置（支持动态添加任务）
                self._load_schedules()

                for schedule_id, schedule in list(self.schedules.items()):
                    # 检查是否启用
                    if not schedule.get("enabled", True):
                        continue

                    # 检查执行时间
                    execute_time = schedule.get("execute_time")
                    repeat = schedule.get("repeat", "once")
                    last_run = schedule.get("last_run")
                    
                    should_execute = False
                    
                    if execute_time:
                        # 新格式：精确时间
                        target_time = datetime(
                            execute_time.get("year", now.year),
                            execute_time.get("month", now.month),
                            execute_time.get("day", now.day),
                            execute_time.get("hour", 0),
                            execute_time.get("minute", 0),
                            execute_time.get("second", 0)
                        )
                        
                        # 检查是否应该执行
                        time_diff = (now - target_time).total_seconds()
                        
                        if repeat == "once":
                            # 仅一次：到时间且未执行过
                            if 0 <= time_diff < 30 and not last_run:
                                should_execute = True
                        elif repeat == "daily":
                            # 每天：检查时分秒是否匹配
                            if (now.hour == execute_time.get("hour", 0) and 
                                now.minute == execute_time.get("minute", 0) and
                                abs(now.second - execute_time.get("second", 0)) < 10):
                                # 检查今天是否已执行
                                if last_run:
                                    last_run_time = datetime.fromisoformat(last_run)
                                    if last_run_time.date() < now.date():
                                        should_execute = True
                                else:
                                    should_execute = True
                        elif repeat == "weekly":
                            # 每周：检查星期几+时分秒
                            if (now.weekday() == target_time.weekday() and
                                now.hour == execute_time.get("hour", 0) and
                                now.minute == execute_time.get("minute", 0)):
                                if last_run:
                                    last_run_time = datetime.fromisoformat(last_run)
                                    if (now - last_run_time).days >= 7:
                                        should_execute = True
                                else:
                                    should_execute = True
                        elif repeat == "workday":
                            # 工作日：周一到周五
                            if (now.weekday() < 5 and  # 0-4是周一到周五
                                now.hour == execute_time.get("hour", 0) and
                                now.minute == execute_time.get("minute", 0)):
                                if last_run:
                                    last_run_time = datetime.fromisoformat(last_run)
                                    if last_run_time.date() < now.date():
                                        should_execute = True
                                else:
                                    should_execute = True
                    else:
                        # 旧格式：cron
                        next_run = schedule.get("next_run", "")
                        if next_run:
                            next_time = datetime.fromisoformat(next_run)
                            if 0 <= (now - next_time).total_seconds() < 30:
                                should_execute = True
                    
                    if should_execute:
                        # AI执行类型的任务不自动执行，等待AI通过MCP处理
                        if schedule.get("action") == "ai_execute":
                            print(f"⏰ AI任务已就绪，等待AI润色: {schedule['name']}")
                            log_manager.add_log("定时任务", "system", f"AI任务就绪，等待润色: {schedule['name']}", "info")
                            # 不执行，让AI通过get_pending_ai_tasks获取并润色后执行
                        else:
                            print(f"⏰ 执行定时任务: {schedule['name']}")
                            log_manager.add_log("定时任务", "system", f"开始执行: {schedule['name']}", "info")
                            await self._execute_schedule(schedule)

                # 每10秒检查一次（更精确）
                await asyncio.sleep(10)

            except Exception as e:
                print(f"调度器错误: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(10)

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
