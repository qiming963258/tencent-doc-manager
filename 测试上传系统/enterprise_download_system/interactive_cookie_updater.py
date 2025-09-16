#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式Cookie更新工具 - 手动登录后自动提取Cookie
"""

import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path

class InteractiveCookieUpdater:
    def __init__(self):
        self.script_files = [
            "windows_compatible_downloader.py",
            "smart_downloader.py", 
            "server_downloader.py",
            "test_download.py",
            "cookie_diagnostic.py"
        ]
        
    async def manual_login_and_extract_cookies(self):
        """启动浏览器供用户手动登录，然后提取Cookie"""
        
        print("\n" + "="*60)
        print("      交互式Cookie获取工具")
        print("  请在打开的浏览器中手动登录腾讯文档")
        print("="*60)
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            print("\n[STEP 1] 打开腾讯文档登录页面...")
            await page.goto('https://docs.qq.com', wait_until='domcontentloaded')
            
            print("\n" + "="*50)
            print("  请在浏览器中完成以下步骤：")
            print("  1. 点击登录按钮") 
            print("  2. 使用QQ或微信登录")
            print("  3. 确保能看到你的文档列表")
            print("  4. 完成后回到终端按Enter键")
            print("="*50)
            
            # 等待用户手动登录
            input("\n按Enter键继续（确保已完成登录）...")
            
            print("\n[STEP 2] 验证登录状态...")
            
            # 测试登录状态
            try:
                await page.goto('https://docs.qq.com/cgi-bin/online_docs/user_info?get_vip_info=1',
                               wait_until='domcontentloaded')
                content = await page.content()
                
                if 'login' in content.lower() or '登录' in content:
                    print("[ERROR] 检测到仍需登录，请确保登录成功后重试")
                    await browser.close()
                    return None
                elif '"uid"' in content and 'guest' not in content.lower():
                    print("[SUCCESS] 登录状态验证成功！")
                else:
                    print("[WARNING] 登录状态不确定，继续提取Cookie...")
                    
            except Exception as e:
                print(f"[WARNING] 状态验证失败: {e}")
                print("继续提取Cookie...")
            
            print("\n[STEP 3] 提取Cookie...")
            
            # 获取所有Cookie
            cookies = await context.cookies()
            
            # 筛选docs.qq.com相关的Cookie
            docs_cookies = [cookie for cookie in cookies if 'docs.qq.com' in cookie.get('domain', '')]
            
            if not docs_cookies:
                print("[ERROR] 未找到docs.qq.com相关的Cookie")
                await browser.close()
                return None
            
            # 转换为cookie字符串格式
            cookie_string = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in docs_cookies])
            
            print(f"\n[SUCCESS] 成功提取到 {len(docs_cookies)} 个Cookie:")
            for cookie in docs_cookies:
                print(f"  - {cookie['name']} = {cookie['value'][:30]}...")
            
            print(f"\n[INFO] Cookie字符串长度: {len(cookie_string)} 字符")
            
            # 保存Cookie到文件
            cookie_data = {
                'cookie_string': cookie_string,
                'cookies_list': docs_cookies,
                'extracted_time': str(asyncio.get_event_loop().time()),
                'domain': 'docs.qq.com'
            }
            
            with open('latest_cookies.json', 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n[SAVED] Cookie已保存到 latest_cookies.json")
            
            # 最终验证
            print(f"\n[STEP 4] 最终验证新Cookie...")
            
            # 创建新的context来测试Cookie
            test_context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            # 设置提取的Cookie
            await test_context.add_cookies(docs_cookies)
            test_page = await test_context.new_page()
            
            try:
                await test_page.goto('https://docs.qq.com/cgi-bin/online_docs/user_info?get_vip_info=1')
                test_content = await test_page.content()
                
                if 'login' not in test_content.lower() and '登录' not in test_content:
                    print("[VERIFIED] 新Cookie验证成功！")
                    verification_result = True
                else:
                    print("[WARNING] 新Cookie验证失败")
                    verification_result = False
                    
            except Exception as e:
                print(f"[ERROR] Cookie验证异常: {e}")
                verification_result = False
            
            await browser.close()
            
            if verification_result:
                return cookie_string
            else:
                return None

    def update_script_cookies(self, new_cookie_string):
        """更新所有脚本文件中的Cookie"""
        
        print(f"\n[UPDATE] 更新脚本文件中的Cookie...")
        
        updated_count = 0
        for script_file in self.script_files:
            script_path = Path(script_file)
            if script_path.exists():
                try:
                    # 读取文件内容
                    with open(script_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 查找Cookie字符串并替换
                    if 'self.cookie_string = "' in content:
                        # 找到Cookie行的开始和结束
                        start_marker = 'self.cookie_string = "'
                        start_pos = content.find(start_marker)
                        
                        if start_pos != -1:
                            start_pos += len(start_marker)
                            end_pos = content.find('"', start_pos)
                            
                            if end_pos != -1:
                                # 替换Cookie
                                new_content = (content[:start_pos] + 
                                             new_cookie_string + 
                                             content[end_pos:])
                                
                                # 写回文件
                                with open(script_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                
                                print(f"[OK] 已更新 {script_file}")
                                updated_count += 1
                            else:
                                print(f"[SKIP] {script_file} - Cookie格式不匹配")
                        else:
                            print(f"[SKIP] {script_file} - 未找到Cookie定义")
                    else:
                        print(f"[SKIP] {script_file} - 无Cookie字段")
                        
                except Exception as e:
                    print(f"[ERROR] 更新 {script_file} 失败: {e}")
            else:
                print(f"[SKIP] {script_file} - 文件不存在")
        
        print(f"\n[RESULT] 成功更新 {updated_count} 个脚本文件")
        return updated_count

    async def run_update_process(self):
        """执行完整的更新流程"""
        
        print("开始交互式Cookie更新流程...")
        
        # 1. 手动登录并提取Cookie
        new_cookie = await self.manual_login_and_extract_cookies()
        
        if not new_cookie:
            print("\n[FAILED] Cookie提取失败，请重试")
            return False
        
        # 2. 更新脚本文件
        updated_count = self.update_script_cookies(new_cookie)
        
        if updated_count > 0:
            print("\n[SUCCESS] Cookie更新完成！")
            print("\n现在你可以运行任何下载脚本:")
            print("  python windows_compatible_downloader.py")
            print("  python smart_downloader.py")
            return True
        else:
            print("\n[WARNING] 虽然提取了Cookie但未能更新脚本文件")
            print("请手动将以下Cookie复制到脚本中:")
            print(f"\n{new_cookie}")
            return False

async def main():
    updater = InteractiveCookieUpdater()
    success = await updater.run_update_process()
    
    if success:
        print("\n" + "="*50)
        print("     Cookie更新成功!")
        print("     现在可以重新运行下载脚本了!")
        print("="*50)
    else:
        print("\n" + "="*50) 
        print("     请手动更新Cookie或重试")
        print("="*50)

if __name__ == "__main__":
    asyncio.run(main())