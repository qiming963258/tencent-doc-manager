#!/usr/bin/env python3
"""改进的登录测试 - 使用enterprise_download_system的成功经验"""

import asyncio
from playwright.async_api import async_playwright
import json

async def test_improved_login():
    """测试改进的登录方法"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized', '--no-sandbox']
        )
        context = await browser.new_context(
            accept_downloads=True
        )
        page = await context.new_page()
        
        print("="*50)
        print("腾讯文档改进登录测试")
        print("="*50)
        
        # 读取Cookie配置
        print("\n1. 读取Cookie配置...")
        with open('config/cookies.json', 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)
            cookies_str = cookie_data.get('cookie_string', '')
        
        if not cookies_str:
            print("错误：Cookie配置为空")
            return
        
        # 使用改进的Cookie解析方法
        print("\n2. 解析Cookie（改进方法）...")
        cookie_list = []
        for cookie_pair in cookies_str.split('; '):  # 使用'; '而不是';'
            if '=' in cookie_pair:
                name, value = cookie_pair.strip().split('=', 1)
                cookie_list.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.docs.qq.com',  # 只使用.docs.qq.com
                    'path': '/'
                })
        
        print(f"解析出 {len(cookie_list)} 个Cookie")
        
        # 添加Cookie
        print("\n3. 添加Cookie到浏览器...")
        await context.add_cookies(cookie_list)
        print("Cookie已添加")
        
        # 直接访问桌面页面（关键改进）
        print("\n4. 直接访问腾讯文档桌面页面...")
        try:
            await page.goto('https://docs.qq.com/desktop/', 
                          wait_until='domcontentloaded', 
                          timeout=30000)
            print("桌面页面加载完成")
        except Exception as e:
            print(f"页面加载失败: {e}")
        
        # 等待页面完全加载
        print("\n5. 等待页面完全加载（5秒）...")
        await page.wait_for_timeout(5000)
        
        # 检查页面状态
        print("\n6. 验证登录状态...")
        title = await page.title()
        print(f"页面标题: {title}")
        
        # 检查是否有登录按钮
        login_btn = await page.query_selector('button:has-text("登录")')
        if login_btn:
            print("状态: 未登录（发现登录按钮）")
        else:
            print("状态: 可能已登录（未发现登录按钮）")
        
        # 检查是否有导入按钮或其他功能按钮
        import_btn = await page.query_selector('.desktop-import-button-pc, button:has-text("导入")')
        if import_btn:
            print("发现导入按钮 - 登录成功！")
        
        # 检查是否有文档元素
        doc_elements = await page.query_selector_all('a[href*="/doc/"]')
        if doc_elements:
            print(f"找到 {len(doc_elements)} 个文档")
        
        # 检查用户信息
        user_info = await page.query_selector('.user-info, [class*="avatar"], [class*="user-name"]')
        if user_info:
            print("发现用户信息元素 - 登录成功！")
        
        print("\n等待30秒供观察...")
        await page.wait_for_timeout(30000)
        
        await browser.close()
        print("\n测试完成")

if __name__ == "__main__":
    asyncio.run(test_improved_login())