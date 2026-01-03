"""
Telegram Web Login Server
使用 Playwright 自动化 Telegram Web 登录，支持扫码登录
"""
import os
import asyncio
import json
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
from playwright.async_api import async_playwright, Browser
import qrcode
from io import BytesIO
import base64

from session_manager import session_manager, API_ID, API_HASH, SESSION_FILE

app = Flask(__name__)
CORS(app)

# 全局变量
browser_instance: Optional[Browser] = None
login_page = None
login_success = False
login_error = None
qr_code_data = None

# HTML 模板
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram MCP - 登录</title>
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
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 24px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .status {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .status.loading {
            background: #fff3cd;
            color: #856404;
        }
        .status.success {
            background: #d4edda;
            color: #155724;
        }
        .status.error {
            background: #f8d7da;
            color: #721c24;
        }
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
        .qr-placeholder {
            color: #999;
            font-size: 14px;
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
        .steps h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 16px;
        }
        .steps ol {
            padding-left: 20px;
            color: #555;
            font-size: 14px;
            line-height: 1.8;
        }
        .btn {
            background: linear-gradient(135deg, #0088cc 0%, #005f8f 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,136,204,0.4);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
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
        .hidden { display: none; }
        .footer {
            margin-top: 20px;
            color: #999;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.11.03-1.93 1.23-5.46 3.62-.51.35-.98.52-1.4.51-.46-.01-1.35-.26-2.01-.48-.81-.27-1.44-.41-1.38-.87.03-.24.37-.48 1.02-.74 3.98-1.73 6.64-2.87 7.97-3.43 3.79-1.57 4.57-1.84 5.08-1.85.11 0 .37.03.54.17.14.11.18.26.2.43-.01.06.01.24 0 .38z"/></svg>
        </div>
        <h1>Telegram MCP 登录</h1>
        <p class="subtitle">扫码登录后，AI 就可以操作你的 Telegram</p>

        <div id="status" class="status loading">
            <div class="spinner"></div>
            <p style="margin-top: 10px;">正在准备登录...</p>
        </div>

        <div id="qrContainer" class="qr-container">
            <p class="qr-placeholder">正在生成二维码...</p>
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

        <button id="refreshBtn" class="btn hidden" onclick="refreshQRCode()">
            🔄 刷新二维码
        </button>

        <p class="footer">登录成功后，可以关闭此窗口</p>
    </div>

    <script>
        let checkInterval;

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

        function showSuccess(user) {
            document.getElementById('status').className = 'status success';
            document.getElementById('status').innerHTML = `
                <strong>✅ 登录成功！</strong><br>
                欢迎, ${user.first_name} ${user.last_name || ''}<br>
                <small>现在可以关闭此窗口，返回 Claude Code 使用</small>
            `;
            document.getElementById('qrContainer').innerHTML = '';
            document.getElementById('refreshBtn').classList.add('hidden');
        }

        function showError(error) {
            document.getElementById('status').className = 'status error';
            document.getElementById('status').innerHTML = `<strong>❌ 登录失败</strong><br>${error}`;
            document.getElementById('refreshBtn').classList.remove('hidden');
        }

        async function refreshQRCode() {
            document.getElementById('status').className = 'status loading';
            document.getElementById('status').innerHTML = `
                <div class="spinner"></div>
                <p style="margin-top: 10px;">正在刷新二维码...</p>
            `;
            document.getElementById('refreshBtn').classList.add('hidden');

            try {
                await fetch('/api/refresh', { method: 'POST' });
                loadQRCode();
            } catch (e) {
                showError('刷新失败，请重试');
            }
        }

        async function loadQRCode() {
            try {
                const response = await fetch('/api/qr');
                const data = await response.json();

                if (data.qr) {
                    document.getElementById('qrContainer').innerHTML = `
                        <img src="${data.qr}" class="qr-image" alt="QR Code">
                    `;

                    // 开始轮询登录状态
                    if (!checkInterval) {
                        checkInterval = setInterval(checkLoginStatus, 2000);
                    }
                } else if (data.waiting) {
                    document.getElementById('qrContainer').innerHTML = `
                        <div class="spinner"></div>
                        <p style="margin-top: 10px;">正在等待二维码...</p>
                    `;
                    setTimeout(loadQRCode, 1000);
                } else if (data.success) {
                    showSuccess(data.user);
                } else if (data.error) {
                    showError(data.error);
                }
            } catch (e) {
                console.error('QR load failed:', e);
                setTimeout(loadQRCode, 2000);
            }
        }

        // 页面加载后开始
        loadQRCode();
    </script>
</body>
</html>
"""


class TelegramWebLogin:
    """Telegram Web 登录处理"""

    def __init__(self, port: int = 5678):
        self.port = port
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.login_success = False
        self.login_error = None
        self.user_data = None
        self.session_string = None

    async def start_browser(self):
        """启动无头浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()

    async def close_browser(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def get_qr_code(self) -> Optional[str]:
        """获取登录二维码（base64 图片）"""
        try:
            if not self.page:
                await self.start_browser()

            # 导航到 Telegram Web
            await self.page.goto('https://web.telegram.org/k/', wait_until='networkidle')

            # 等待页面加载
            await asyncio.sleep(2)

            # 查找并点击 "QR Login" 按钮
            try:
                # 尝试多种选择器
                qr_button = await self.page.wait_for_selector(
                    'button[aria-label="QR Login"], .login-qr-btn, button.qr-login',
                    timeout=10000
                )
                if qr_button:
                    await qr_button.click()
            except Exception:
                # 可能已经是 QR 登录页面
                pass

            await asyncio.sleep(2)

            # 查找二维码图片
            qr_img = None
            for _ in range(30):  # 最多等待 30 秒
                try:
                    qr_img = await self.page.query_selector('canvas.qr-qr, img[src*="qr"], canvas')
                    if qr_img:
                        break
                except Exception:
                    pass
                await asyncio.sleep(1)

            if qr_img:
                # 截取二维码区域
                bbox = await qr_img.bounding_box()
                if bbox:
                    # 截图整个页面，裁剪二维码区域
                    screenshot = await self.page.screenshot()
                    from PIL import Image
                    import io

                    img = Image.open(io.BytesIO(screenshot))
                    left = int(bbox['x']) - 10
                    top = int(bbox['y']) - 10
                    right = int(bbox['x'] + bbox['width']) + 10
                    bottom = int(bbox['y'] + bbox['height']) + 10

                    # 确保坐标在图像范围内
                    left = max(0, left)
                    top = max(0, top)
                    right = min(img.width, right)
                    bottom = min(img.height, bottom)

                    qr_img_pil = img.crop((left, top, right, bottom))

                    # 转换为 base64
                    buffer = BytesIO()
                    qr_img_pil.save(buffer, format='PNG')
                    img_base64 = base64.b64encode(buffer.getvalue()).decode()
                    return f"data:image/png;base64,{img_base64}"

            return None
        except Exception as e:
            print(f"Get QR code error: {e}")
            return None

    async def check_login_status(self) -> Dict[str, Any]:
        """检查登录状态"""
        try:
            if not self.page:
                return {"waiting": True}

            # 检查是否已登录
            current_url = self.page.url

            # 如果 URL 改变，可能已登录
            if 'a=' in current_url or '/chat/' in current_url:
                # 尝试获取用户信息
                try:
                    # 从 localStorage 获取用户数据
                    user_data = await self.page.evaluate('''() => {
                        const key = Object.keys(localStorage).find(k => k.includes('user') || k.includes('auth'));
                        return key ? JSON.parse(localStorage[key]) : null;
                    }''')

                    if user_data:
                        self.user_data = user_data
                        self.login_success = True
                        return {"success": True, "user": user_data}
                except Exception:
                    pass

                # 备选方案：从页面获取用户名
                try:
                    name_elem = await self.page.wait_for_selector('.chat-info, .profile-title, .user-name', timeout=5000)
                    if name_elem:
                        name = await name_elem.inner_text()
                        self.user_data = {"first_name": name.split()[0] if name else "User"}
                        self.login_success = True
                        return {"success": True, "user": self.user_data}
                except Exception:
                    pass

            return {"waiting": True}
        except Exception as e:
            return {"error": str(e)}

    async def extract_session(self) -> Optional[str]:
        """提取 session（使用 Telethon 重新授权）"""
        try:
            # 注意：从 Telegram Web 提取 session 并不直接可行
            # 我们需要用户用手机号+验证码的方式重新用 Telethon 登录
            # 但这里我们尝试从 cookies 中获取一些信息

            cookies = await self.context.cookies()
            tg_auth = None

            for cookie in cookies:
                if 'tg' in cookie.get('name', '').lower() or 'auth' in cookie.get('name', '').lower():
                    tg_auth = cookie.get('value')
                    break

            # 由于 Telegram Web 和 MTProto 使用不同的认证方式
            # 我们需要引导用户完成 Telethon 登录
            return None
        except Exception as e:
            print(f"Extract session error: {e}")
            return None


# 全局登录实例
login_instance: Optional[TelegramWebLogin] = None


@app.route('/')
def index():
    """主页"""
    return render_template_string(LOGIN_HTML)


@app.route('/api/qr')
def get_qr():
    """获取二维码"""
    global login_instance

    try:
        if not login_instance:
            login_instance = TelegramWebLogin()

        # 在后台线程中获取二维码
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            qr_data = loop.run_until_complete(login_instance.get_qr_code())

            if qr_data:
                return jsonify({"qr": qr_data})
            else:
                return jsonify({"waiting": True})
        finally:
            loop.close()
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/status')
def check_status():
    """检查登录状态"""
    global login_instance

    try:
        if not login_instance:
            return jsonify({"waiting": True})

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            status = loop.run_until_complete(login_instance.check_login_status())
            return jsonify(status)
        finally:
            loop.close()
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/refresh')
def refresh():
    """刷新二维码"""
    global login_instance

    try:
        if login_instance:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(login_instance.close_browser())
            finally:
                loop.close()

        login_instance = TelegramWebLogin()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})


def run_login_server(port: int = 5678, auto_open: bool = True):
    """运行登录服务器"""
    if auto_open:
        # 延迟打开浏览器，让服务器先启动
        import threading
        def open_browser():
            import time
            time.sleep(1)
            webbrowser.open(f'http://localhost:{port}')
        threading.Thread(target=open_browser, daemon=True).start()

    print(f"🌐 登录服务器已启动: http://localhost:{port}")
    print("📱 请在浏览器中扫码登录 Telegram")

    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    run_login_server()
