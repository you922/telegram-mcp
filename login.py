#!/usr/bin/env python3
"""
Telegram MCP - 快速登录脚本
使用 Telethon 的交互式登录（手机号+验证码）
"""
import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# 内置公开凭据
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_FILE = ".telegram_session"


async def main():
    print("\n" + "="*50)
    print("📱 Telegram MCP - 登录")
    print("="*50 + "\n")

    # 检查是否已登录
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE) as f:
            existing_session = f.read().strip()
        if existing_session:
            print("✅ 检测到已保存的 session")
            choice = input("是否重新登录? (y/N): ").strip().lower()
            if choice != 'y':
                print("保留现有 session")
                return

    # 开始登录流程
    print("请输入你的 Telegram 手机号（带国家码）")
    print("示例: +8613800138000\n")

    client = TelegramClient(StringSession(), API_ID, API_HASH)

    await client.start()

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"\n✅ 登录成功!")
        print(f"   姓名: {me.first_name} {me.last_name or ''}")
        print(f"   用户名: @{me.username if me.username else 'N/A'}")
        print(f"   ID: {me.id}")

        # 保存 session
        session_string = client.session.save()
        with open(SESSION_FILE, "w") as f:
            f.write(session_string)

        print(f"\n✅ Session 已保存到 {SESSION_FILE}")
        print("   现在可以启动 MCP 服务器: python main.py")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
