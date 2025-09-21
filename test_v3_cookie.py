#!/usr/bin/env python3
"""
测试v3模块的Cookie处理
"""

import json
import asyncio
from playwright.async_api import async_playwright

# 读取Cookie
with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
    cookies = json.load(f)

cookie_str = cookies.get('current_cookies', '')

print(f"📝 原始Cookie长度: {len(cookie_str)}")

# 模拟v3的parse_cookie_string
def parse_cookie_string(cookie_string: str) -> list:
    """解析Cookie字符串"""
    cookies = []

    for cookie_pair in cookie_string.split('; '):
        if '=' in cookie_pair:
            name, value = cookie_pair.strip().split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': '.docs.qq.com',
                'path': '/'
            })

    return cookies

parsed = parse_cookie_string(cookie_str)
print(f"📊 解析出Cookie数量: {len(parsed)}")

# 测试实际添加到浏览器
async def test_add_cookies():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        try:
            # 先导航到域名
            page = await context.new_page()
            await page.goto('https://docs.qq.com')

            # 然后添加cookies
            await context.add_cookies(parsed)

            # 获取所有cookies验证
            all_cookies = await context.cookies()
            print(f"\n✅ 成功添加到浏览器的Cookie数量: {len(all_cookies)}")

            # 显示前3个
            for i, cookie in enumerate(all_cookies[:3]):
                print(f"  {i+1}. {cookie['name']}: {cookie['value'][:20]}...")

        except Exception as e:
            print(f"\n❌ 添加Cookie失败: {e}")

        finally:
            await browser.close()

# 运行测试
asyncio.run(test_add_cookies())