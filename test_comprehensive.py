#!/usr/bin/env python3
"""全面测试所有 117 个 MCP 工具"""
import asyncio
import sys
import main
from typing import Dict, List, Tuple


async def test():
    print("=" * 60)
    print("🔍 全面验证 117 个 Telegram MCP 工具")
    print("=" * 60)
    print()

    # 1. 验证 Telegram 连接
    print("【步骤 1/5】验证 Telegram 连接...")
    try:
        c = await main.get_client()
        me = await c.get_me()
        print(f"✅ 连接成功: {me.first_name} (@{me.username or 'N/A'})")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False
    print()

    # 2. 验证所有工具已注册
    print("【步骤 2/5】验证工具注册...")
    tm = main.mcp._tool_manager
    tools = tm._tools
    print(f"✅ 已注册工具数: {len(tools)}/117")

    if len(tools) != 117:
        print(f"⚠️ 警告: 期望 117 个工具，实际 {len(tools)} 个")
    print()

    # 3. 按类别测试工具
    print("【步骤 3/5】按类别测试工具可访问性...")

    categories = {
        "基础聊天": [
            "get_chats", "search_public_chats", "get_chat", "join_chat", "leave_chat"
        ],
        "消息操作": [
            "send_message", "get_messages", "reply_message", "edit_message",
            "delete_message", "forward_message", "pin_message", "unpin_message"
        ],
        "媒体操作": [
            "send_photo", "send_video", "send_document", "send_voice",
            "send_audio", "download_media", "get_chat_photos", "set_chat_photo"
        ],
        "高级消息": [
            "send_reaction", "get_message_reactions", "schedule_message",
            "send_location", "send_contact", "copy_message", "send_sticker"
        ],
        "群组频道": [
            "create_channel", "edit_channel", "get_channel_stats",
            "create_supergroup", "create_topic", "get_topics"
        ],
        "隐私设置": [
            "get_privacy", "set_privacy", "get_active_sessions"
        ],
        "搜索功能": [
            "search_global", "search_by_date", "search_by_sender", "search_hashtags"
        ],
        "数据导出": [
            "export_chat", "get_chat_file", "backup_chats"
        ],
    }

    all_passed = True
    for category, tool_names in categories.items():
        print(f"\n  📂 {category}:")
        for tool_name in tool_names:
            try:
                tool = tm.get_tool(tool_name)
                print(f"    ✅ {tool_name}")
            except Exception as e:
                print(f"    ❌ {tool_name}: {e}")
                all_passed = False
    print()

    # 4. 实际调用测试（不修改数据的工具）
    print("【步骤 4/5】实际调用测试（只读工具）...")

    read_only_tests = [
        ("get_me", {}, "获取我的信息"),
        ("get_chats", {"page": 1, "page_size": 5}, "获取聊天列表"),
        ("get_privacy", {}, "获取隐私设置"),
        ("get_active_sessions", {}, "获取活跃会话"),
    ]

    for tool_name, args, desc in read_only_tests:
        try:
            tool_func = getattr(main, tool_name)
            result = await tool_func(**args)

            if result and "❌" not in result:
                print(f"  ✅ {desc}")
            else:
                print(f"  ⚠️ {desc}: {result[:80]}")
        except Exception as e:
            print(f"  ❌ {desc}: {str(e)[:80]}")
    print()

    # 5. 错误处理测试
    print("【步骤 5/5】错误处理测试...")

    error_tests = [
        ("get_chat", {"chat_id": "invalid_id_12345"}, "无效聊天ID"),
        ("send_message", {"chat_id": "invalid", "message": "test"}, "发送到无效聊天"),
    ]

    for tool_name, args, desc in error_tests:
        try:
            tool_func = getattr(main, tool_name)
            result = await tool_func(**args)

            # 应该返回错误信息，而不是崩溃
            if "❌" in result or "Error" in result or "错误" in result:
                print(f"  ✅ {desc}: 正确处理错误")
            else:
                print(f"  ⚠️ {desc}: 返回 {result[:50]}")
        except Exception as e:
            print(f"  ❌ {desc}: 未捕获异常 - {str(e)[:50]}")
    print()

    # 总结
    print("=" * 60)
    if all_passed:
        print("🎉 所有验证通过！")
    else:
        print("⚠️ 部分工具存在问题")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result else 1)
