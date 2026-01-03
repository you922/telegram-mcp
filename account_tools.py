#!/usr/bin/env python3
"""
账号管理 MCP 工具
供 AI 调用的管理工具接口
"""
from fastmcp import Context
from fastmcp.annotations import ToolAnnotations
import json
from typing import Optional

# 导入管理模块
from account_manager import account_manager
from proxy_manager import proxy_manager
from health_monitor import health_monitor
from stats_tracker import stats_tracker
from batch_operations import batch_operations


def create_mcp_server():
    """创建账号管理 MCP 服务器"""
    from fastmcp import MCP

    mcp = MCP("account-management")

    # ============ 账号管理工具 ============

    @mcp.tool(annotations=ToolAnnotations(
        title="列出所有账号",
        description="获取所有账号的列表和状态信息，包括用户名、用户号、在线状态、使用次数等",
        category="account"
    ))
    async def list_accounts() -> str:
        """
        列出所有账号

        Returns:
            JSON格式的账号列表
        """
        accounts = account_manager.list_accounts()
        return json.dumps({
            "success": True,
            "accounts": accounts,
            "total": len(accounts)
        }, ensure_ascii=False, indent=2)

    @mcp.tool(annotations=ToolAnnotations(
        title="生成登录二维码",
        description="为指定账号ID生成登录二维码。二维码有效期为120秒，过期后可使用refresh_qr_code刷新",
        category="account"
    ))
    async def generate_qr_code(account_id: str) -> str:
        """
        生成二维码用于登录新账号

        Args:
            account_id: 账号ID（如：account2, account3）

        Returns:
            包含二维码图片(base64)和登录URL的JSON
        """
        proxy = proxy_manager.get_proxy_for_account(account_id)
        result = await account_manager.generate_qr_code(account_id, proxy)
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool(annotations=ToolAnnotations(
        title="检查二维码登录状态",
        description="检查指定账号的二维码登录状态和剩余时间",
        category="account"
    ))
    async def check_qr_status(account_id: str) -> str:
        """
        检查二维码登录状态

        Args:
            account_id: 账号ID

        Returns:
            包含状态(waiting/success/timeout/failed)和剩余时间的JSON
        """
        result = account_manager.check_qr_status(account_id)
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool(annotations=ToolAnnotations(
        title="刷新二维码",
        description="刷新指定账号的二维码，生成新的登录链接",
        category="account"
    ))
    async def refresh_qr_code(account_id: str) -> str:
        """
        刷新二维码

        Args:
            account_id: 账号ID

        Returns:
            新的二维码信息
        """
        proxy = proxy_manager.get_proxy_for_account(account_id)
        result = await account_manager.refresh_qr_code(account_id, proxy)
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool(annotations=ToolAnnotations(
        title="删除账号",
        description="删除指定的账号（无法删除default账号）",
        category="account"
    ))
    async def delete_account(account_id: str) -> str:
        """
        删除账号

        Args:
            account_id: 账号ID

        Returns:
            操作结果
        """
        success = await account_manager.remove_account(account_id)
        return json.dumps({
            "success": success,
            "message": "账号已删除" if success else "删除失败"
        }, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="使用Session添加账号",
        description="使用Session字符串导入已有账号",
        category="account"
    ))
    async def add_account_with_session(
        account_id: str,
        session_string: str,
        phone: str = None,
        username: str = None
    ) -> str:
        """
        使用Session字符串添加账号

        Args:
            account_id: 账号ID
            session_string: Session字符串
            phone: 手机号（可选）
            username: 用户名（可选）

        Returns:
            操作结果
        """
        success = await account_manager.add_account_with_session(
            account_id, session_string, phone, username
        )
        return json.dumps({
            "success": success,
            "message": "账号添加成功" if success else "添加失败"
        }, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="导出Session",
        description="导出指定账号的Session字符串",
        category="account"
    ))
    async def export_session(account_id: str) -> str:
        """
        导出Session字符串

        Args:
            account_id: 账号ID

        Returns:
            Session字符串
        """
        session = account_manager.export_session(account_id)
        if session:
            return json.dumps({
                "success": True,
                "account_id": account_id,
                "session_string": session
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "success": False,
                "error": "账号不存在"
            }, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="批量导入账号",
        description="批量导入多个账号，使用Session字符串",
        category="account"
    ))
    async def batch_import_accounts(accounts_json: str) -> str:
        """
        批量导入账号

        Args:
            accounts_json: JSON格式的账号数据
                [{"account_id": "...", "session_string": "...", "phone": "..."}, ...]

        Returns:
            导入结果统计
        """
        try:
            accounts_data = json.loads(accounts_json)
            result = await account_manager.batch_import(accounts_data)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False)

    # ============ 代理管理工具 ============

    @mcp.tool(annotations=ToolAnnotations(
        title="列出所有代理",
        description="获取全局代理和所有账号独立代理的列表",
        category="proxy"
    ))
    async def list_proxies() -> str:
        """
        列出所有代理

        Returns:
            代理列表JSON
        """
        proxies = proxy_manager.list_proxies()
        return json.dumps({
            "success": True,
            **proxies
        }, ensure_ascii=False, indent=2)

    @mcp.tool(annotations=ToolAnnotations(
        title="添加代理",
        description="添加一个新的代理配置",
        category="proxy"
    ))
    async def add_proxy(
        proxy_id: str,
        protocol: str,
        host: str,
        port: int,
        username: str = None,
        password: str = None
    ) -> str:
        """
        添加代理

        Args:
            proxy_id: 代理ID
            protocol: 协议 (socks5/http/https/socks4)
            host: 主机地址
            port: 端口
            username: 用户名（可选）
            password: 密码（可选）

        Returns:
            操作结果
        """
        success = proxy_manager.add_proxy(
            proxy_id, protocol, host, port, username, password
        )
        return json.dumps({
            "success": success,
            "message": "代理添加成功" if success else "代理协议不支持"
        }, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="删除代理",
        description="删除指定的代理配置",
        category="proxy"
    ))
    async def delete_proxy(proxy_id: str) -> str:
        """
        删除代理

        Args:
            proxy_id: 代理ID

        Returns:
            操作结果
        """
        success = proxy_manager.delete_proxy(proxy_id)
        return json.dumps({
            "success": success,
            "message": "代理已删除" if success else "代理不存在"
        }, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="设置全局代理",
        description="设置全局代理，所有账号默认使用此代理",
        category="proxy"
    ))
    async def set_global_proxy(
        protocol: str,
        host: str,
        port: int,
        username: str = None,
        password: str = None
    ) -> str:
        """
        设置全局代理

        Args:
            protocol: 协议 (socks5/http/https/socks4)
            host: 主机地址
            port: 端口
            username: 用户名（可选）
            password: 密码（可选）

        Returns:
            操作结果
        """
        success = proxy_manager.set_global_proxy(protocol, host, port, username, password)
        return json.dumps({
            "success": success,
            "message": "全局代理设置成功" if success else "代理协议不支持"
        }, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="移除全局代理",
        description="移除全局代理设置",
        category="proxy"
    ))
    async def remove_global_proxy() -> str:
        """
        移除全局代理

        Returns:
            操作结果
        """
        success = proxy_manager.remove_global_proxy()
        return json.dumps({
            "success": success,
            "message": "全局代理已移除"
        }, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="为账号分配代理",
        description="为指定账号分配独立的代理",
        category="proxy"
    ))
    async def assign_proxy_to_account(account_id: str, proxy_id: str) -> str:
        """
        为账号分配代理

        Args:
            account_id: 账号ID
            proxy_id: 代理ID

        Returns:
            操作结果
        """
        success = proxy_manager.assign_proxy_to_account(account_id, proxy_id)
        return json.dumps({
            "success": success,
            "message": "代理分配成功" if success else "代理不存在"
        }, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="取消账号代理",
        description="取消账号的独立代理分配",
        category="proxy"
    ))
    async def unassign_proxy_from_account(account_id: str, proxy_id: str) -> str:
        """
        取消账号代理分配

        Args:
            account_id: 账号ID
            proxy_id: 代理ID

        Returns:
            操作结果
        """
        success = proxy_manager.unassign_proxy_from_account(account_id, proxy_id)
        return json.dumps({
            "success": success,
            "message": "代理分配已取消" if success else "代理不存在"
        }, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="测试代理",
        description="测试指定或所有代理的连接状态和响应时间",
        category="proxy"
    ))
    async def test_proxy(proxy_id: str = None) -> str:
        """
        测试代理

        Args:
            proxy_id: 代理ID，None表示测试所有代理

        Returns:
            测试结果
        """
        if proxy_id:
            if proxy_id not in proxy_manager.proxies:
                return json.dumps({"success": False, "error": "代理不存在"}, ensure_ascii=False)
            result = await proxy_manager.test_proxy(proxy_manager.proxies[proxy_id])
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            result = await proxy_manager.test_all_proxies()
            return json.dumps(result, ensure_ascii=False, indent=2)

    # ============ 健康监控工具 ============

    @mcp.tool(annotations=ToolAnnotations(
        title="获取健康报告",
        description="获取所有账号或指定账号的健康报告",
        category="health"
    ))
    async def get_health_report(account_id: str = None) -> str:
        """
        获取健康报告

        Args:
            account_id: 账号ID，None表示获取所有账号

        Returns:
            健康报告JSON
        """
        report = health_monitor.get_health_report(account_id)
        return json.dumps(report, ensure_ascii=False, indent=2)

    @mcp.tool(annotations=ToolAnnotations(
        title="检查账号健康",
        description="检查指定账号的健康状态",
        category="health"
    ))
    async def check_account_health(account_id: str) -> str:
        """
        检查账号健康状态

        Args:
            account_id: 账号ID

        Returns:
            健康状态
        """
        result = await health_monitor.check_account_health(account_id)
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool(annotations=ToolAnnotations(
        title="获取高风险账号",
        description="获取所有高风险和中风险的账号列表",
        category="health"
    ))
    async def get_risk_accounts() -> str:
        """
        获取高风险账号列表

        Returns:
            高风险账号列表
        """
        accounts = health_monitor.get_risk_accounts()
        return json.dumps({
            "success": True,
            "risk_accounts": accounts,
            "total": len(accounts)
        }, ensure_ascii=False, indent=2)

    # ============ 统计工具 ============

    @mcp.tool(annotations=ToolAnnotations(
        title="获取账号统计",
        description="获取指定账号的详细统计数据",
        category="stats"
    ))
    async def get_account_stats(account_id: str) -> str:
        """
        获取账号统计

        Args:
            account_id: 账号ID

        Returns:
            统计数据JSON
        """
        stats = stats_tracker.get_account_stats(account_id)
        return json.dumps({
            "success": True,
            "account_id": account_id,
            "stats": stats
        }, ensure_ascii=False, indent=2)

    @mcp.tool(annotations=ToolAnnotations(
        title="获取每日统计",
        description="获取指定日期的所有账号统计",
        category="stats"
    ))
    async def get_daily_stats(date: str = None) -> str:
        """
        获取每日统计

        Args:
            date: 日期 (YYYY-MM-DD)，None表示今天

        Returns:
            每日统计JSON
        """
        stats = stats_tracker.get_daily_stats(date)
        return json.dumps({
            "success": True,
            "date": date or "today",
            "stats": stats
        }, ensure_ascii=False, indent=2)

    @mcp.tool(annotations=ToolAnnotations(
        title="获取每周统计",
        description="获取指定周的所有账号统计",
        category="stats"
    ))
    async def get_weekly_stats(week: str = None) -> str:
        """
        获取每周统计

        Args:
            week: 周标识 (YYYY-WWW)，None表示本周

        Returns:
            每周统计JSON
        """
        stats = stats_tracker.get_weekly_stats(week)
        return json.dumps({
            "success": True,
            "week": week or "current",
            "stats": stats
        }, ensure_ascii=False, indent=2)

    @mcp.tool(annotations=ToolAnnotations(
        title="获取最活跃账号",
        description="获取按使用次数或消息数排序的最活跃账号",
        category="stats"
    ))
    async def get_top_accounts(by: str = "uses", limit: int = 10, period: str = "all") -> str:
        """
        获取最活跃账号

        Args:
            by: 排序依据 (uses/messages)
            limit: 返回数量
            period: 时间范围 (all/today/week)

        Returns:
            最活跃账号列表
        """
        result = stats_tracker.get_top_accounts(by, limit, period)
        return json.dumps({
            "success": True,
            "top_accounts": result
        }, ensure_ascii=False, indent=2)

    @mcp.tool(annotations=ToolAnnotations(
        title="获取活跃度趋势",
        description="获取指定账号最近几天的活跃度趋势",
        category="stats"
    ))
    async def get_activity_trend(account_id: str, days: int = 7) -> str:
        """
        获取活跃度趋势

        Args:
            account_id: 账号ID
            days: 天数

        Returns:
            活跃度趋势数据
        """
        trend = stats_tracker.get_activity_trend(account_id, days)
        return json.dumps({
            "success": True,
            "account_id": account_id,
            "trend": trend
        }, ensure_ascii=False, indent=2)

    @mcp.tool(annotations=ToolAnnotations(
        title="获取统计摘要",
        description="获取整体统计摘要，包括总使用量、今日数据等",
        category="stats"
    ))
    async def get_stats_summary() -> str:
        """
        获取统计摘要

        Returns:
            统计摘要JSON
        """
        summary = stats_tracker.get_summary()
        return json.dumps({
            "success": True,
            "summary": summary
        }, ensure_ascii=False, indent=2)

    # ============ 批量操作工具 ============

    @mcp.tool(annotations=ToolAnnotations(
        title="批量发送消息",
        description="使用多个账号向指定聊天发送消息，自动延迟防止封号",
        category="batch"
    ))
    async def batch_send_message(
        chat_id: str,
        message: str,
        account_ids: str = None,
        delay: float = 2.0
    ) -> str:
        """
        批量发送消息

        Args:
            chat_id: 目标聊天ID
            message: 消息内容
            account_ids: 账号ID列表(JSON数组)，None表示全部账号
            delay: 操作间隔（秒），默认2秒

        Returns:
            批量发送结果
        """
        import json as json_mod
        try:
            ids = json_mod.loads(account_ids) if account_ids else None
            result = await batch_operations.batch_send_message(
                chat_id=chat_id,
                message=message,
                account_ids=ids,
                delay=delay
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="批量发送模板消息",
        description="使用多个账号批量发送模板消息，支持变量替换",
        category="batch"
    ))
    async def batch_send_template(
        chat_id: str,
        template_id: str,
        account_ids: str = None,
        template_vars: str = None,
        delay: float = 2.0
    ) -> str:
        """
        批量发送模板消息

        Args:
            chat_id: 目标聊天ID
            template_id: 模板ID
            account_ids: 账号ID列表(JSON数组)，None表示全部账号
            template_vars: 模板变量(JSON对象)，可选
            delay: 操作间隔（秒），默认2秒

        Returns:
            批量发送结果
        """
        import json as json_mod
        try:
            ids = json_mod.loads(account_ids) if account_ids else None
            vars_dict = json_mod.loads(template_vars) if template_vars else {}
            result = await batch_operations.batch_send_template(
                chat_id=chat_id,
                template_id=template_id,
                account_ids=ids,
                template_vars=vars_dict,
                delay=delay
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="批量检查账号健康",
        description="批量检查多个账号的健康状态",
        category="batch"
    ))
    async def batch_check_health(account_ids: str = None) -> str:
        """
        批量检查账号健康状态

        Args:
            account_ids: 账号ID列表(JSON数组)，None表示全部账号

        Returns:
            健康检查结果
        """
        import json as json_mod
        try:
            ids = json_mod.loads(account_ids) if account_ids else None
            result = await batch_operations.batch_check_health(ids)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="批量导出Session",
        description="批量导出多个账号的Session字符串",
        category="batch"
    ))
    async def batch_export_sessions(account_ids: str = None) -> str:
        """
        批量导出Session

        Args:
            account_ids: 账号ID列表(JSON数组)，None表示全部账号

        Returns:
            Session数据
        """
        import json as json_mod
        try:
            ids = json_mod.loads(account_ids) if account_ids else None
            result = await batch_operations.batch_export_sessions(ids)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="批量删除账号",
        description="批量删除多个账号",
        category="batch"
    ))
    async def batch_delete_accounts(account_ids: str) -> str:
        """
        批量删除账号

        Args:
            account_ids: 账号ID列表(JSON数组)

        Returns:
            删除结果
        """
        import json as json_mod
        try:
            ids = json_mod.loads(account_ids)
            result = await batch_operations.batch_delete_accounts(ids)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @mcp.tool(annotations=ToolAnnotations(
        title="批量获取对话列表",
        description="批量获取多个账号的对话列表",
        category="batch"
    ))
    async def batch_get_dialogs(account_ids: str = None, limit: int = 20) -> str:
        """
        批量获取对话列表

        Args:
            account_ids: 账号ID列表(JSON数组)，None表示全部账号
            limit: 每个账号获取的数量

        Returns:
            对话列表
        """
        import json as json_mod
        try:
            ids = json_mod.loads(account_ids) if account_ids else None
            result = await batch_operations.batch_get_dialogs(ids, limit)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    return mcp


# 创建MCP服务器实例
mcp_server = create_mcp_server()


if __name__ == "__main__":
    # 运行MCP服务器
    import asyncio
    mcp_server.run()
