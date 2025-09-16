#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档文件上传脚本 - 工作版本
基于提供的精确按钮位置信息
"""

import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

class TencentDocUploader:
    """腾讯文档上传器"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.upload_file_path = None
        print("[INIT] Tencent Doc Upload System")
        
    async def start_browser(self, headless=False):
        """启动浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=['--start-maximized', '--no-sandbox']
            )
            
            self.context = await self.browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )
            
            self.page = await self.context.new_page()
            print("[OK] Browser started")
            return True
            
        except Exception as e:
            print(f"[ERROR] Browser start failed: {e}")
            return False
    
    def parse_cookies(self, cookie_string):
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
    
    async def login_with_cookies(self, cookie_string):
        """Cookie登录"""
        try:
            print("\n[STEP 1] Login with cookies")
            
            cookies = self.parse_cookies(cookie_string)
            await self.context.add_cookies(cookies)
            print(f"[INFO] Added {len(cookies)} cookies")
            
            print("[VISIT] https://docs.qq.com/")
            await self.page.goto('https://docs.qq.com/', wait_until='domcontentloaded', timeout=30000)
            
            await self.page.wait_for_timeout(5000)
            
            title = await self.page.title()
            print(f"[INFO] Page title: {title}")
            
            import_btn = await self.page.query_selector('button.desktop-import-button-pc')
            if import_btn:
                print("[OK] Found import button - Login success")
                return True
            else:
                print("[WARN] Import button not found")
                return False
                
        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
            return False
    
    async def click_import_button(self):
        """点击导入按钮"""
        try:
            print("\n[STEP 2] Click import button")
            
            # 尝试多个选择器
            import_selectors = [
                'button.desktop-import-button-pc',
                'nav button:has(i.desktop-icon-import)',
                'button:has-text("导入")'
            ]
            
            for selector in import_selectors:
                try:
                    import_btn = await self.page.wait_for_selector(selector, timeout=3000)
                    if import_btn:
                        print(f"[OK] Found button with: {selector}")
                        await import_btn.click()
                        return True
                except:
                    continue
            
            print("[ERROR] Import button not found")
            return False
            
        except Exception as e:
            print(f"[ERROR] Click import failed: {e}")
            return False
    
    async def select_file(self, file_path):
        """选择文件"""
        try:
            print("\n[STEP 3] Select file")
            
            # 等待文件输入元素
            file_input = await self.page.wait_for_selector('input[type="file"]', timeout=5000)
            
            if file_input:
                # 设置文件
                abs_path = str(Path(file_path).resolve())
                await file_input.set_input_files(abs_path)
                print(f"[OK] File selected: {abs_path}")
                return True
            else:
                print("[ERROR] File input not found")
                return False
                
        except Exception as e:
            print(f"[INFO] Direct file input not found, trying filechooser: {e}")
            
            # 如果没有找到input元素，可能是自定义文件选择器
            # 等待文件选择器事件
            try:
                # 设置文件选择器处理
                async with self.page.expect_file_chooser() as fc_info:
                    # 触发文件选择器（已经在点击导入按钮时触发）
                    pass
                file_chooser = await fc_info.value
                abs_path = str(Path(file_path).resolve())
                await file_chooser.set_files(abs_path)
                print(f"[OK] File selected via chooser: {abs_path}")
                return True
            except Exception as e2:
                print(f"[ERROR] File selection failed: {e2}")
                return False
    
    async def confirm_upload(self):
        """确认上传"""
        try:
            print("\n[STEP 4] Confirm upload")
            
            # 等待弹窗出现
            await self.page.wait_for_timeout(2000)
            
            # 检查弹窗是否出现
            modal_title = await self.page.query_selector('.import-kit-import-modal-title:has-text("导入本地文件")')
            if modal_title:
                print("[OK] Import modal appeared")
            else:
                print("[WARN] Import modal not detected")
            
            # 点击确定按钮
            confirm_selectors = [
                'button.dui-button-type-primary:has-text("确定")',
                '.import-kit-import-file-footer button.dui-button-type-primary',
                'button.dui-button-type-primary .dui-button-container:has-text("确定")'
            ]
            
            for selector in confirm_selectors:
                try:
                    confirm_btn = await self.page.wait_for_selector(selector, timeout=3000)
                    if confirm_btn:
                        await confirm_btn.click()
                        print("[OK] Clicked confirm button")
                        return True
                except:
                    continue
            
            # 如果都失败，尝试Enter键
            print("[INFO] Trying Enter key")
            await self.page.keyboard.press('Enter')
            return True
            
        except Exception as e:
            print(f"[ERROR] Confirm failed: {e}")
            return False
    
    async def upload_file_complete(self, file_path):
        """完整的上传流程"""
        try:
            # 1. 点击导入按钮
            if not await self.click_import_button():
                return False
            
            # 2. 等待一下
            await self.page.wait_for_timeout(1000)
            
            # 3. 准备文件选择
            abs_path = str(Path(file_path).resolve())
            
            # 创建一个Promise来处理文件选择
            await self.page.evaluate('''
                () => {
                    return new Promise((resolve) => {
                        // 监听文件输入变化
                        const observer = new MutationObserver((mutations) => {
                            for (const mutation of mutations) {
                                for (const node of mutation.addedNodes) {
                                    if (node.tagName === 'INPUT' && node.type === 'file') {
                                        resolve(node);
                                        observer.disconnect();
                                    }
                                }
                            }
                        });
                        observer.observe(document.body, { childList: true, subtree: true });
                        
                        // 5秒后超时
                        setTimeout(() => {
                            observer.disconnect();
                            resolve(null);
                        }, 5000);
                    });
                }
            ''')
            
            # 查找所有file input
            file_inputs = await self.page.query_selector_all('input[type="file"]')
            if file_inputs:
                print(f"[INFO] Found {len(file_inputs)} file inputs")
                # 使用最后一个（通常是最新创建的）
                await file_inputs[-1].set_input_files(abs_path)
                print(f"[OK] File set: {file_path}")
            else:
                print("[WARN] No file input found, waiting for filechooser")
                
                # 使用filechooser API
                async with self.page.expect_file_chooser(timeout=10000) as fc_info:
                    # 重新点击导入按钮触发文件选择器
                    import_btn = await self.page.query_selector('button.desktop-import-button-pc')
                    if import_btn:
                        await import_btn.click()
                
                file_chooser = await fc_info.value
                await file_chooser.set_files(abs_path)
                print(f"[OK] File selected via chooser")
            
            # 4. 确认上传
            await self.confirm_upload()
            
            # 5. 等待上传完成
            print("\n[STEP 5] Waiting for upload...")
            await self.page.wait_for_timeout(5000)
            
            # 检查URL变化
            current_url = self.page.url
            if '/sheet/' in current_url or '/doc/' in current_url:
                print("[SUCCESS] File uploaded!")
                print(f"[URL] {current_url}")
                return True
            
            # 再等待一会
            await self.page.wait_for_timeout(5000)
            current_url = self.page.url
            if '/sheet/' in current_url or '/doc/' in current_url:
                print("[SUCCESS] File uploaded!")
                print(f"[URL] {current_url}")
                return True
            
            print("[WARN] Upload may not complete")
            return False
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        print("[CLEANUP] Browser closed")

async def main():
    """主函数"""
    
    print("="*60)
    print("Tencent Doc Upload Script")
    print("="*60)
    
    uploader = TencentDocUploader()
    
    try:
        # 启动浏览器
        if not await uploader.start_browser(headless=False):
            return
        
        # 读取Cookie
        config_file = Path('config/cookies.json')
        if not config_file.exists():
            print("[ERROR] Cookie config not found")
            return
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            cookie_string = config.get('cookie_string', '')
        
        # 登录
        if not await uploader.login_with_cookies(cookie_string):
            print("[ERROR] Login failed")
            return
        
        # 选择文件
        test_files = [
            "副本-副本-测试版本-出国销售计划表.xlsx",
            "test_files/test_upload_20250909.xlsx"
        ]
        
        upload_file = None
        for file in test_files:
            if os.path.exists(file):
                upload_file = file
                break
        
        if not upload_file:
            print("[ERROR] Test file not found")
            return
        
        print(f"\n[FILE] Upload: {upload_file}")
        print(f"[SIZE] {os.path.getsize(upload_file):,} bytes")
        
        # 执行上传
        if await uploader.upload_file_complete(upload_file):
            print("\n" + "="*40)
            print("UPLOAD SUCCESS!")
            print("="*40)
        else:
            print("\n" + "="*40)
            print("UPLOAD FAILED")
            print("="*40)
        
        # 等待观察
        print("\n[WAIT] Keep browser open for 30s...")
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"\n[EXCEPTION] {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await uploader.cleanup()

if __name__ == "__main__":
    asyncio.run(main())