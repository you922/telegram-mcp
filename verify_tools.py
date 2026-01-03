#!/usr/bin/env python3
"""
验证所有 Telegram MCP 工具是否能正常操作
"""
import asyncio
import json
import sys

# 导入主模块
from main import (
    get_client, get_chats, get_me, get_contacts, search_public_chats,
    get_messages, search_messages, get_participants, get_admins,
    get_invite_link, get_user_status, get_chat, get_active_sessions,
    get_pinned_messages, get_chat_photos, get_history, get_topics,
    search_media, filter_messages
)

async def test_tool(name, func, *args, **kwargs):
    """测试单个工具"""
    try:
        result = await func(*args, **kwargs)
        data = json.loads(result) if isinstance(result, str) else result
        if data.get("success") or "error" not in str(data).lower():
            return True, "OK"
        else:
            return False, data.get("error", "Unknown error")
    except Exception as e:
        return False, str(e)

async def main():
    print("=" * 60)
    print("🔍 Telegram MCP 工具验证测试")
    print("=" * 60)
    
    # 首先测试连接
    print("\n📡 测试 Telegram 连接...")
    try:
        client = await get_client()
        if client and client.is_connected():
            print("✅ Telegram 连接成功")
        else:
            print("❌ Telegram 连接失败")
            return
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        return

    results = []
    
    # 只读测试（不会修改任何数据）
    tests = [
        ("get_me", get_me),
        ("get_chats", get_chats, 1, 10),
        ("get_contacts", get_contacts),
        ("get_active_sessions", get_active_sessions),
    ]
    
    print("\n🧪 执行只读测试...\n")
    
    for test in tests:
        name = test[0]
        func = test[1]
        args = test[2:] if len(test) > 2 else ()
        
        success, msg = await test_tool(name, func, *args)
        status = "✅" if success else "❌"
        results.append((name, success, msg))
        
        if success:
            print(f"{status} {name}")
        else:
            print(f"{status} {name}: {msg}")

    # 需要 chat_id 的测试
    print("\n📬 获取聊天列表用于后续测试...")
    try:
        chats_result = await get_chats(1, 5)
        chats_data = json.loads(chats_result)
        if chats_data.get("success") and chats_data.get("chats"):
            test_chat = chats_data["chats"][0]
            chat_id = test_chat.get("id")
            chat_title = test_chat.get("title", "Unknown")
            print(f"   使用聊天: {chat_title} (ID: {chat_id})")
            
            # 测试需要 chat_id 的工具
            chat_tests = [
                ("get_chat", get_chat, chat_id),
                ("get_messages", get_messages, chat_id, 5),
                ("get_history", get_history, chat_id, 5),
                ("get_pinned_messages", get_pinned_messages, chat_id),
            ]
            
            print("\n🧪 执行聊天相关测试...\n")
            
            for test in chat_tests:
                name = test[0]
                func = test[1]
                args = test[2:]
                
                success, msg = await test_tool(name, func, *args)
                status = "✅" if success else "❌"
                results.append((name, success, msg))
                
                if success:
                    print(f"{status} {name}")
                else:
                    print(f"{status} {name}: {msg}")
        else:
            print("   ⚠️ 无法获取聊天列表")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 搜索测试
    print("\n🔎 搜索功能测试...\n")
    search_tests = [
        ("search_public_chats", search_public_chats, "telegram", 5),
        ("search_contacts", lambda q: __import__('main').search_contacts(q), "test"),
    ]
    
    for test in search_tests:
        name = test[0]
        func = test[1]
        args = test[2:]
        
        try:
            if name == "search_contacts":
                from main import search_contacts
                success, msg = await test_tool(name, search_contacts, "test")
            else:
                success, msg = await test_tool(name, func, *args)
            status = "✅" if success else "❌"
            results.append((name, success, msg))
            
            if success:
                print(f"{status} {name}")
            else:
                print(f"{status} {name}: {msg}")
        except Exception as e:
            print(f"❌ {name}: {e}")
            results.append((name, False, str(e)))

    # 统计结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    failed = sum(1 for _, success, _ in results if not success)
    total = len(results)
    
    print(f"\n✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {failed}/{total}")
    
    if failed > 0:
        print("\n❌ 失败的测试:")
        for name, success, msg in results:
            if not success:
                print(f"   - {name}: {msg}")
    
    print("\n" + "=" * 60)
    print("📋 工具分类统计 (共117个)")
    print("=" * 60)
    print("""
📬 聊天管理: get_chats, search_public_chats, get_chat, join_chat, leave_chat
📝 消息操作: send_message, get_messages, reply_message, edit_message, delete_message, forward_message
📌 置顶操作: pin_message, unpin_message, get_pinned_messages
👥 联系人: get_contacts, search_contacts, add_contact, delete_contact, block_user, unblock_user
👨‍👩‍👧‍👦 群组管理: create_group, get_participants, get_admins, invite_to_chat, promote_admin, ban_user
📷 媒体文件: send_photo, send_video, send_document, send_voice, send_audio, download_media
🎭 个人资料: get_me, update_profile, get_user_status
🔔 通知设置: mute_chat, unmute_chat
📊 投票: create_poll
📍 位置: send_location
📇 联系人卡片: send_contact
📢 频道: create_channel, edit_channel, get_channel_stats
📂 归档: archive_chat, unarchive_chat
🔗 链接: get_invite_link
💬 话题: create_topic, get_topics, edit_topic, delete_topic
🔐 私密聊天: create_secret_chat, close_secret_chat
⏱️ 定时: schedule_message
😀 反应: send_reaction, get_message_reactions
🔍 搜索: search_messages, search_media, filter_messages
📱 会话: get_active_sessions, terminate_session
""")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
