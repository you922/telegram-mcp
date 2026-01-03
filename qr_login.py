#!/usr/bin/env python3
"""
Telegram QR Code Login
使用 Telethon 原生 QR 登录功能
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
    print("📱 Telegram MCP - QR Code Login")
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

    print("正在生成 QR Code...")
    print("请用手机 Telegram 扫描二维码登录\n")

    client = TelegramClient(StringSession(), API_ID, API_HASH)

    # QR 登录
    await client.connect()

    # 使用 QR 登录
    qr_login = await client.qr_login()

    # 显示 QR Code 到终端（使用 ASCII 字符画）
    try:
        import qrcode

        # qr_login 对象有 url 属性
        login_url = qr_login.url

        # 生成 QR Code 图片
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(login_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # 保存到临时文件
        img.save("/tmp/telegram_qr_login.png")
        print(f"✅ QR Code 已保存到: /tmp/telegram_qr_login.png")
        print(f"   请打开此文件并扫描\n")

        # 尝试在 macOS 上用预览打开
        os.system("open /tmp/telegram_qr_login.png 2>/dev/null")

    except Exception as e:
        print(f"QR Code 生成失败: {e}")
        print(f"URL: {qr_login.url}\n")

    # 等待用户扫码
    print("⏳ 等待扫码... (最多等待 120 秒)")
    print("   手机 Telegram: 设置 → 设备 → 扫描二维码\n")

    try:
        # 等待登录完成
        await qr_login.wait()

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

    except TimeoutError:
        print("\n❌ 登录超时，请重试")
    except Exception as e:
        print(f"\n❌ 登录失败: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
