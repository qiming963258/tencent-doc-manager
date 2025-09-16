#!/usr/bin/env python3
"""诊断登录问题"""

import asyncio
from playwright.async_api import async_playwright
import json

async def diagnose_login():
    """诊断登录问题"""
    async with async_playwright() as p:
        # 启动浏览器 - 可见模式
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("1. 尝试直接访问腾讯文档...")
        try:
            # 直接访问，不加载Cookie
            await page.goto('https://docs.qq.com', timeout=30000)
            print("成功访问腾讯文档主页")
            
            # 等待页面完全加载
            await page.wait_for_timeout(3000)
            
            # 检查页面元素
            login_btn = await page.query_selector('button:has-text("登录")')
            if login_btn:
                print("🔍 发现登录按钮 - 当前未登录状态")
            else:
                print("🔍 未发现明显的登录按钮")
                
            # 检查页面title
            title = await page.title()
            print(f"📄 页面标题: {title}")
            
            # 检查是否有导入按钮或其他功能按钮
            import_btn = await page.query_selector('.desktop-import-button-pc, button:has-text("导入")')
            if import_btn:
                print("🔍 发现导入按钮")
            
            print("\n2. 尝试加载Cookie...")
            # 读取Cookie配置
            with open('config/cookies.json', 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
                cookies_str = cookie_data.get('cookie_string', '')
            
            if not cookies_str:
                print("❌ Cookie配置为空")
                return
                
            # 解析并添加cookies
            cookie_list = []
            for cookie_pair in cookies_str.split(';'):
                if '=' in cookie_pair:
                    name, value = cookie_pair.strip().split('=', 1)
                    for domain in ['.qq.com', '.docs.qq.com']:
                        cookie_list.append({
                            'name': name.strip(),
                            'value': value.strip(),
                            'domain': domain,
                            'path': '/',
                            'httpOnly': False,
                            'secure': True,
                            'sameSite': 'None'
                        })
            
            print(f"📝 准备添加 {len(cookie_list)} 个Cookie")
            await page.context.add_cookies(cookie_list)
            print("✅ Cookie已添加")
            
            print("\n3. 刷新页面应用Cookie...")
            await page.reload(wait_until='domcontentloaded')
            await page.wait_for_timeout(3000)
            print("✅ 页面刷新完成")
            
            # 再次检查登录状态
            login_btn_after = await page.query_selector('button:has-text("登录")')
            if login_btn_after:
                print("⚠️ 刷新后仍显示未登录状态")
            else:
                print("✅ 可能已成功登录")
                
            # 检查用户信息
            user_info = await page.query_selector('.user-info, [class*="avatar"], [class*="user-name"]')
            if user_info:
                print("✅ 发现用户信息元素")
            
            print("\n等待10秒观察页面状态...")
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"❌ 访问失败: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(diagnose_login())