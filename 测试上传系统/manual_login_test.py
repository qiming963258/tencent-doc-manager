#!/usr/bin/env python3
"""手动登录测试"""

import asyncio
from playwright.async_api import async_playwright
import json
import os

async def manual_login_test():
    """手动登录测试"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("打开腾讯文档登录页面...")
        await page.goto('https://docs.qq.com')
        
        print("请在浏览器中手动登录...")
        print("登录完成后，按回车继续...")
        input()
        
        print("获取登录后的Cookie...")
        cookies = await page.context.cookies()
        
        # 转换为字符串格式
        cookie_string = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
        
        # 保存到配置文件
        cookie_data = {
            "cookies": cookies,
            "cookie_string": cookie_string,
            "last_updated": "2025-09-09 23:00:00"
        }
        
        with open('config/cookies.json', 'w', encoding='utf-8') as f:
            json.dump(cookie_data, f, ensure_ascii=False, indent=2)
        
        print("Cookie已保存到config/cookies.json")
        print("现在可以测试文件上传功能")
        
        # 测试上传按钮是否可见
        print("查找导入按钮...")
        import_btn = await page.query_selector('.desktop-import-button-pc, button:has-text("导入")')
        if import_btn:
            print("找到导入按钮!")
            
            # 创建文件输入元素
            await page.evaluate("""
                const input = document.createElement('input');
                input.type = 'file';
                input.style.display = 'none';
                document.body.appendChild(input);
                input.id = 'file-upload-test';
            """)
            
            print("请选择要上传的xlsx文件...")
            
        print("等待30秒观察...")
        await page.wait_for_timeout(30000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(manual_login_test())