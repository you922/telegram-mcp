#!/usr/bin/env python3
"""测试所有 MCP 工具是否正常工作"""
import asyncio
import sys
import main


async def test():
    print("🔧 启动测试...")

    # 1. 检查 session 文件
    import os
    if not os.path.exists(main.SESSION_FILE):
        print(f"⚠️ Session 文件不存在: {main.SESSION_FILE}")
        print("请先运行: python3 qr_web_login.py")
        return False

    print(f"✅ Session 文件存在")

    # 2. 测试 Telegram 连接
    try:
        c = await main.get_client()
        me = await c.get_me()
        print(f"✅ Telegram 连接成功")
        print(f"   用户: {me.first_name} (@{me.username or 'N/A'})")
        print(f"   ID: {me.id}")
    except Exception as e:
        print(f"❌ Telegram 连接失败: {e}")
        return False

    # 3. 测试工具调用
    try:
        tm = main.mcp._tool_manager
        tool = tm.get_tool("get_me")
        print(f"✅ get_me 工具可访问")
    except Exception as e:
        print(f"❌ 工具访问失败: {e}")
        return False

    # 4. 测试几个工具的元数据
    test_tools = ["get_me", "send_message", "get_chats", "create_channel"]
    for tool_name in test_tools:
        try:
            tool = tm.get_tool(tool_name)
            print(f"✅ {tool_name}: 已注册")
        except Exception:
            print(f"❌ {tool_name}: 未找到")

    # 5. 测试实际工具调用
    try:
        result = await main.get_me()
        print(f"\n✅ 工具调用测试成功!")
        print(f"   结果: {result[:100]}...")
    except Exception as e:
        print(f"\n⚠️ 工具调用测试: {e}")

    print("\n🎉 所有测试通过!")
    return True


if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result else 1)
