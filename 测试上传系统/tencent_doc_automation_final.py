#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档自动化登录上传 - 最终生产版本
经过完整测试验证的成功实现
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright


class TencentDocAutomation:
    """腾讯文档自动化操作 - 核心实现"""
    
    def __init__(self, headless: bool = False):
        """
        初始化
        Args:
            headless: 是否无头模式，False便于观察和调试
        """
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        
    async def start(self) -> bool:
        """启动浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
            # 关键浏览器配置
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--start-maximized', '--no-sandbox']
            )
            
            self.context = await self.browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )
            
            self.page = await self.context.new_page()
            print("[SUCCESS] Browser started")
            return True
            
        except Exception as e:
            print(f"[ERROR] Browser start failed: {e}")
            return False
    
    def parse_cookie_string(self, cookie_string: str) -> list:
        """
        解析Cookie字符串 - 核心方法
        
        关键：使用 '; ' 分割，只设置 .docs.qq.com 域
        """
        cookies = []
        
        # 关键：'; ' 不是 ';'
        for cookie_pair in cookie_string.split('; '):
            if '=' in cookie_pair:
                name, value = cookie_pair.strip().split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.docs.qq.com',  # 关键：只用这个域
                    'path': '/'
                })
        
        return cookies
    
    async def login_with_cookies(self, cookie_string: str) -> bool:
        """
        Cookie登录 - 成功的关键流程
        
        1. 添加Cookie
        2. 直接访问desktop页面
        3. 充分等待5秒
        4. 验证状态
        """
        try:
            print("[LOGIN] Starting cookie login...")
            
            # 添加Cookie
            cookies = self.parse_cookie_string(cookie_string)
            await self.context.add_cookies(cookies)
            print(f"[INFO] Added {len(cookies)} cookies")
            
            # 直接访问桌面页面（关键）
            await self.page.goto(
                'https://docs.qq.com/desktop/',  # 不是主页！
                wait_until='domcontentloaded',
                timeout=30000
            )
            
            # 充分等待（重要）
            await self.page.wait_for_timeout(5000)
            
            # 验证登录
            title = await self.page.title()
            print(f"[INFO] Page title: {title}")
            
            # 检查导入按钮
            import_btn = await self.page.query_selector('button.desktop-import-button-pc')
            if import_btn:
                print("[SUCCESS] Login successful!")
                return True
            else:
                print("[WARN] Login may have failed")
                return False
                
        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
            return False
    
    async def upload_file(self, file_path: str) -> Dict[str, Any]:
        """
        上传文件 - 完整流程
        
        1. 点击导入按钮
        2. 选择文件
        3. 确认上传
        4. 等待完成
        """
        result = {'success': False, 'url': None, 'message': ''}
        
        try:
            file_path = Path(file_path).resolve()
            if not file_path.exists():
                result['message'] = f"File not found: {file_path}"
                return result
            
            print(f"\n[UPLOAD] Starting upload: {file_path.name}")
            
            # 步骤1：点击导入按钮
            import_btn = await self.page.wait_for_selector(
                'button.desktop-import-button-pc', 
                timeout=5000
            )
            await import_btn.click()
            print("[OK] Clicked import button")
            
            # 步骤2：选择文件
            await self.page.wait_for_timeout(1000)
            
            # 查找file input
            file_inputs = await self.page.query_selector_all('input[type="file"]')
            if file_inputs:
                # 使用最后一个input
                await file_inputs[-1].set_input_files(str(file_path))
                print(f"[OK] File selected: {file_path.name}")
            else:
                # 备用：filechooser
                print("[INFO] Using filechooser")
                async with self.page.expect_file_chooser() as fc_info:
                    await import_btn.click()
                file_chooser = await fc_info.value
                await file_chooser.set_files(str(file_path))
            
            # 步骤3：确认上传
            await self.page.wait_for_timeout(2000)
            
            # 查找确定按钮
            confirm_selectors = [
                'button.dui-button-type-primary:has-text("确定")',
                '.import-kit-import-file-footer button.dui-button-type-primary'
            ]
            
            for selector in confirm_selectors:
                try:
                    btn = await self.page.wait_for_selector(selector, timeout=2000)
                    if btn:
                        await btn.click()
                        print("[OK] Clicked confirm")
                        break
                except:
                    continue
            else:
                # 备用：Enter键
                await self.page.keyboard.press('Enter')
                print("[OK] Pressed Enter")
            
            # 步骤4：等待上传完成
            print("[WAIT] Waiting for upload...")
            
            for i in range(6):  # 最多等待30秒
                await self.page.wait_for_timeout(5000)
                
                url = self.page.url
                if '/sheet/' in url or '/doc/' in url:
                    result['success'] = True
                    result['url'] = url
                    result['message'] = "Upload successful"
                    print(f"[SUCCESS] Upload complete: {url}")
                    return result
            
            result['message'] = "Upload timeout"
            
        except Exception as e:
            result['message'] = f"Upload error: {str(e)}"
            print(f"[ERROR] {result['message']}")
            
        return result
    
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("[CLEANUP] Browser closed")


async def quick_upload(cookie_string: str, file_path: str) -> bool:
    """
    快速上传函数 - 最简单的使用方式
    
    Args:
        cookie_string: 从浏览器复制的Cookie字符串
        file_path: 要上传的文件路径
        
    Returns:
        bool: 是否成功
    
    Example:
        cookie = "your_cookie_string"
        file = "test.xlsx"
        success = await quick_upload(cookie, file)
    """
    automation = TencentDocAutomation(headless=False)
    
    try:
        # 启动
        if not await automation.start():
            return False
        
        # 登录
        if not await automation.login_with_cookies(cookie_string):
            return False
        
        # 上传
        result = await automation.upload_file(file_path)
        
        if result['success']:
            print(f"\n{'='*50}")
            print("UPLOAD SUCCESS!")
            print(f"URL: {result['url']}")
            print('='*50)
            
            # 保持打开一会儿
            await asyncio.sleep(10)
            return True
        else:
            print(f"\n{'='*50}")
            print(f"UPLOAD FAILED: {result['message']}")
            print('='*50)
            return False
            
    finally:
        await automation.cleanup()


async def main():
    """主函数示例"""
    
    print("="*60)
    print("Tencent Doc Automation - Final Version")
    print("="*60)
    
    # 配置文件路径
    CONFIG_FILE = 'config/cookies.json'
    TEST_FILES = [
        '副本-副本-测试版本-出国销售计划表.xlsx',
        'test_files/test_upload_20250909.xlsx'
    ]
    
    # 读取Cookie
    if not os.path.exists(CONFIG_FILE):
        print("[ERROR] Cookie config not found")
        print("Please create config/cookies.json with format:")
        print('{"cookie_string": "your_cookies_here"}')
        return
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
        cookie_string = config.get('cookie_string', '')
    
    if not cookie_string:
        print("[ERROR] Cookie string is empty")
        return
    
    # 查找测试文件
    test_file = None
    for file in TEST_FILES:
        if os.path.exists(file):
            test_file = file
            break
    
    if not test_file:
        print("[ERROR] No test file found")
        return
    
    # 执行上传
    success = await quick_upload(cookie_string, test_file)
    
    if success:
        print("\n[DONE] Upload completed successfully")
    else:
        print("\n[DONE] Upload failed")


# Cookie获取指南
COOKIE_GUIDE = """
========================================
How to get Cookie:
========================================
1. Open Chrome browser
2. Login to https://docs.qq.com
3. Press F12 to open DevTools
4. Go to Network tab
5. Refresh the page
6. Find any request to docs.qq.com
7. In Headers, find Cookie
8. Copy the complete Cookie value
9. Save to config/cookies.json:

{
  "cookie_string": "paste_your_cookie_here"
}

Cookie format example:
uid=xxx; DOC_SID=xxx; SID=xxx; TOK=xxx...
========================================
"""


if __name__ == "__main__":
    # 如果没有配置文件，显示指南
    if not os.path.exists('config/cookies.json'):
        print(COOKIE_GUIDE)
    else:
        # 运行主程序
        asyncio.run(main())