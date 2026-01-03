#!/usr/bin/env python3
"""
Telegram QR Code Login with Web Interface
使用 Telethon 的 qr_login + Flask Web 界面
"""
import os
import asyncio
import webbrowser
import threading
import time
from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
from telethon import TelegramClient
from telethon.sessions import StringSession
import qrcode
from io import BytesIO
import base64

# 内置公开凭据
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_FILE = ".telegram_session"

app = Flask(__name__)
CORS(app)

# 全局变量
qr_login_instance = None
login_status = {"waiting": True, "success": False, "error": None, "user": None}

# HTML 模板
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram MCP - QR 登录</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 450px;
            width: 100%;
            text-align: center;
        }
        .logo {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #0088cc 0%, #005f8f 100%);
            border-radius: 20px;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .logo svg {
            width: 45px;
            height: 45px;
            fill: white;
        }
        h1 { color: #333; margin-bottom: 10px; font-size: 24px; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; }
        .status {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .status.loading { background: #fff3cd; color: #856404; }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        .qr-container {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            min-height: 280px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .qr-image {
            max-width: 250px;
            border-radius: 10px;
            border: 3px solid #0088cc;
        }
        .steps {
            text-align: left;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .steps h3 { color: #333; margin-bottom: 15px; font-size: 16px; }
        .steps ol {
            padding-left: 20px;
            color: #555;
            font-size: 14px;
            line-height: 1.8;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #0088cc;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .footer { margin-top: 20px; color: #999; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.11.03-1.93 1.23-5.46 3.62-.51.35-.98.52-1.4.51-.46-.01-1.35-.26-2.01-.48-.81-.27-1.44-.41-1.38-.87.03-.24.37-.48 1.02-.74 3.98-1.73 6.64-2.87 7.97-3.43 3.79-1.57 4.57-1.84 5.08-1.85.11 0 .37.03.54.17.14.11.18.26.2.43-.01.06.01.24 0 .38z"/></svg>
        </div>
        <h1>Telegram MCP - QR 登录</h1>
        <p class="subtitle">扫码登录后，AI 就可以操作你的 Telegram</p>

        <div id="status" class="status loading">
            <div class="spinner"></div>
            <p style="margin-top: 10px;">正在生成二维码...</p>
        </div>

        <div id="qrContainer" class="qr-container">
            <div class="spinner"></div>
        </div>

        <div class="steps">
            <h3>📱 登录步骤</h3>
            <ol>
                <li>打开手机 Telegram</li>
                <li>点击 <strong>设置</strong> → <strong>设备</strong> → <strong>扫描二维码</strong></li>
                <li>扫描上方二维码</li>
                <li>确认登录</li>
            </ol>
        </div>

        <p class="footer">登录成功后，可以关闭此窗口</p>
    </div>

    <script>
        let checkInterval;

        function showSuccess(user) {
            document.getElementById('status').className = 'status success';
            document.getElementById('status').innerHTML = `
                <strong>✅ 登录成功！</strong><br>
                欢迎, ${user.first_name} ${user.last_name || ''}<br>
                <small>现在可以关闭此窗口，返回 Claude Code 使用</small>
            `;
            document.getElementById('qrContainer').innerHTML = '';
        }

        function showError(error) {
            document.getElementById('status').className = 'status error';
            document.getElementById('status').innerHTML = `<strong>❌ 登录失败</strong><br>${error}`;
        }

        async function loadQRCode() {
            try {
                const response = await fetch('/api/qr');
                const data = await response.json();

                if (data.qr) {
                    document.getElementById('status').innerHTML = '<strong>⏳ 请扫描二维码</strong><br>等待手机扫码确认...';
                    document.getElementById('status').className = 'status loading';

                    document.getElementById('qrContainer').innerHTML = `
                        <img src="${data.qr}" class="qr-image" alt="QR Code">
                    `;

                    // 开始轮询登录状态
                    if (!checkInterval) {
                        checkInterval = setInterval(checkLoginStatus, 2000);
                    }
                } else if (data.error) {
                    showError(data.error);
                }
            } catch (e) {
                console.error('QR load failed:', e);
                setTimeout(loadQRCode, 2000);
            }
        }

        async function checkLoginStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();

                if (data.success) {
                    clearInterval(checkInterval);
                    showSuccess(data.user);
                } else if (data.error) {
                    clearInterval(checkInterval);
                    showError(data.error);
                }
            } catch (e) {
                console.error('Status check failed:', e);
            }
        }

        // 页面加载后开始
        loadQRCode();
    </script>
</body>
</html>
"""


async def do_qr_login():
    """执行 QR 登录"""
    global qr_login_instance, login_status

    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()

        # QR 登录
        qr_login = await client.qr_login()

        # 生成 QR Code 图片
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_login.url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # 转换为 base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        # 保存到全局变量供 API 使用
        qr_login_instance = {
            'client': client,
            'qr_login': qr_login,
            'qr_data': f"data:image/png;base64,{img_base64}"
        }

        print("✅ QR Code 已生成，等待扫码...")

        # 等待登录完成（在后台）- 最多等待 120 秒
        try:
            await asyncio.wait_for(qr_login.wait(), timeout=120)
        except asyncio.TimeoutError:
            print("⏱️ QR 码等待超时")
            login_status = {
                "waiting": False,
                "success": False,
                "error": "QR 码超时，请刷新页面重试",
                "user": None
            }
            await client.disconnect()
            return
        except Exception as e:
            print(f"❌ QR 等待错误: {e}")
            login_status = {
                "waiting": False,
                "success": False,
                "error": str(e),
                "user": None
            }
            await client.disconnect()
            return

        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"✅ 登录成功: {me.first_name}")

            # 保存 session
            session_string = client.session.save()
            with open(SESSION_FILE, "w") as f:
                f.write(session_string)

            login_status = {
                "waiting": False,
                "success": True,
                "error": None,
                "user": {
                    "first_name": me.first_name,
                    "last_name": me.last_name,
                    "username": me.username,
                    "id": me.id
                }
            }

        await client.disconnect()

    except Exception as e:
        print(f"❌ 登录失败: {e}")
        login_status = {
            "waiting": False,
            "success": False,
            "error": str(e),
            "user": None
        }


@app.route('/')
def index():
    return render_template_string(LOGIN_HTML)


@app.route('/api/qr')
def get_qr():
    global qr_login_instance

    if qr_login_instance and 'qr_data' in qr_login_instance:
        return jsonify({"qr": qr_login_instance['qr_data']})
    else:
        return jsonify({"waiting": True})


@app.route('/api/status')
def check_status():
    return jsonify(login_status)


def run_login_server(port: int = 5679):
    """运行登录服务器"""
    print(f"🌐 登录服务器已启动: http://localhost:{port}")
    print("📱 请在浏览器中扫码登录 Telegram")

    # 在后台启动 QR 登录
    def start_qr_login():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(do_qr_login())

    threading.Thread(target=start_qr_login, daemon=True).start()

    # 延迟打开浏览器
    def open_browser():
        time.sleep(2)
        webbrowser.open(f'http://localhost:{port}')

    threading.Thread(target=open_browser, daemon=True).start()

    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    run_login_server()
