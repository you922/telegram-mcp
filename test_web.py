#!/usr/bin/env python3
"""
测试 Telegram Web 页面结构
"""
import asyncio
from playwright.async_api import async_playwright


async def test_telegram_web():
    print("启动浏览器...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()

        print("导航到 Telegram Web...")
        await page.goto('https://web.telegram.org/k/', wait_until='networkidle')

        print("\n等待 5 秒查看页面...")
        await asyncio.sleep(5)

        # 获取页面 HTML
        html = await page.content()

        # 保存到文件
        with open('/tmp/telegram_web.html', 'w') as f:
            f.write(html)

        print("✅ 页面 HTML 已保存到 /tmp/telegram_web.html")

        # 尝试查找 QR 登录按钮
        print("\n查找 QR 登录按钮...")

        # 尝试多种选择器
        selectors = [
            'button[aria-label*="QR"]',
            'button[aria-label*="qr"]',
            '.login-qr-btn',
            'button.qr-login',
            'button[class*="qr"]',
            'button[class*="QR"]',
            'svg[class*="qr"]',
            'div[class*="qr"]',
            'canvas[class*="qr"]',
        ]

        for selector in selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    print(f"✅ 找到: {selector}")
                    text = await elem.inner_text()
                    print(f"   文本: {text}")
            except Exception as e:
                pass

        # 获取所有按钮
        print("\n所有按钮:")
        buttons = await page.query_selector_all('button')
        for i, btn in enumerate(buttons[:10]):
            try:
                text = await btn.inner_text()
                aria_label = await btn.get_attribute('aria-label')
                class_name = await btn.get_attribute('class')
                print(f"  [{i}] 文本={text[:30] if text else ''}, aria-label={aria_label}, class={class_name}")
            except:
                pass

        print("\n按回车关闭浏览器...")
        input()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_telegram_web())
