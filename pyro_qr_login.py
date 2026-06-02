#!/usr/bin/env python3
"""
Telegram QR Code Login with Pyrogram
Pyrogram 对 QR 登录支持更好
"""
import os
import asyncio
from pyrogram import Client

from shared.config import API_ID, API_HASH, SESSION_FILE


async def main():
    print("\n" + "="*50)
    print("📱 Telegram MCP - QR Code Login (Pyrogram)")
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

    # 创建 Pyrogram 客户端 (使用字符串session)
    client = Client(
        "telegram_qr_login",
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True
    )

    # 启动客户端
    await client.connect()

    try:
        # QR 登录 - Pyrogram 的方式
        qr_code = await client.sign_in_with_qr_code()

        # 显示 QR Code
        try:
            import qrcode

            # 生成 QR Code 图片
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_code.url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # 保存到临时文件
            img.save("/tmp/telegram_pyro_qr.png")
            print(f"✅ QR Code 已保存到: /tmp/telegram_pyro_qr.png")
            print(f"   已自动打开预览\n")

            # 在 macOS 上用预览打开
            os.system("open /tmp/telegram_pyro_qr.png 2>/dev/null")

        except Exception as e:
            print(f"QR Code 生成失败: {e}")
            print(f"URL: {qr_code.url}\n")

        # 等待用户扫码
        print("⏳ 等待扫码... (最多等待 120 秒)")
        print("   手机 Telegram: 设置 → 设备 → 扫描二维码\n")

        # 等待登录完成
        try:
            # sign_in_with_qr_code 返回的对象需要等待
            await asyncio.wait_for(qr_code.wait(), timeout=120)

            if await client.is_user_authorized():
                me = await client.get_me()
                print(f"\n✅ 登录成功!")
                print(f"   姓名: {me.first_name} {me.last_name or ''}")
                print(f"   用户名: @{me.username if me.username else 'N/A'}")
                print(f"   ID: {me.id}")

                # 获取并保存 session string
                session_string = client.export_session_string()
                with open(SESSION_FILE, "w") as f:
                    f.write(session_string)

                print(f"\n✅ Session 已保存到 {SESSION_FILE}")
                print("   现在可以启动 MCP 服务器: python main.py")

        except asyncio.TimeoutError:
            print("\n❌ 登录超时，请重试")

    except Exception as e:
        print(f"\n❌ 登录失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
