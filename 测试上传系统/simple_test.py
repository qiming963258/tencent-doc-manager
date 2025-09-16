#!/usr/bin/env python3
"""简单测试脚本"""

import asyncio
from playwright.async_api import async_playwright
import json

async def simple_test():
    """简单测试"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("正在访问腾讯文档...")
        try:
            await page.goto('https://docs.qq.com', timeout=30000)
            print("访问成功")
            
            await page.wait_for_timeout(5000)
            
            title = await page.title()
            print(f"页面标题: {title}")
            
            # 检查登录按钮
            login_btn = await page.query_selector('button:has-text("登录")')
            if login_btn:
                print("发现登录按钮 - 未登录状态")
                
            print("加载Cookie...")
            with open('config/cookies.json', 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
                cookies_str = cookie_data.get('cookie_string', '')
            
            # 添加cookies
            cookie_list = []
            for cookie_pair in cookies_str.split(';'):
                if '=' in cookie_pair:
                    name, value = cookie_pair.strip().split('=', 1)
                    cookie_list.append({
                        'name': name.strip(),
                        'value': value.strip(),
                        'domain': '.docs.qq.com',
                        'path': '/'
                    })
            
            await page.context.add_cookies(cookie_list)
            print(f"已添加 {len(cookie_list)} 个Cookie")
            
            print("刷新页面...")
            await page.reload()
            await page.wait_for_timeout(5000)
            
            # 检查登录状态
            login_btn_after = await page.query_selector('button:has-text("登录")')
            if login_btn_after:
                print("仍显示未登录")
            else:
                print("可能已登录")
            
            print("等待观察...")
            await page.wait_for_timeout(15000)
            
        except Exception as e:
            print(f"错误: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(simple_test())