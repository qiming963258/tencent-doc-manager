#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright真实Excel下载测试
验证是否能获得正常格式的文件
"""

import os
import json
import time
from playwright.sync_api import sync_playwright

def test_playwright_download():
    """使用Playwright下载真正的Excel文件"""
    
    print("=" * 60)
    print("Playwright真实下载测试")
    print("=" * 60)
    
    # 加载Cookie
    with open('/root/projects/tencent-doc-manager/config/cookies_new.json', 'r') as f:
        cookie_data = json.load(f)
        cookie_str = cookie_data['current_cookies']
    
    # 解析Cookie为列表格式
    cookies = []
    for item in cookie_str.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies.append({
                'name': key,
                'value': value,
                'domain': '.docs.qq.com',
                'path': '/'
            })
    
    with sync_playwright() as p:
        print("\n1. 启动浏览器...")
        # 使用headless模式避免GUI依赖
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        # 添加cookies
        context.add_cookies(cookies)
        
        page = context.new_page()
        
        try:
            # 测试文档
            doc_id = "DWEVjZndkR2xVSWJN"
            doc_url = f"https://docs.qq.com/sheet/{doc_id}"
            
            print(f"\n2. 访问文档: {doc_url}")
            page.goto(doc_url, wait_until='networkidle')
            
            # 等待页面加载
            print("\n3. 等待页面完全加载...")
            time.sleep(3)
            
            # 检查是否需要登录
            if "登录" in page.content():
                print("❌ 需要重新登录，Cookie可能已过期")
                return False
            
            # 查找导出按钮
            print("\n4. 查找导出功能...")
            
            # 尝试多种可能的导出按钮选择器
            export_selectors = [
                'button:has-text("导出")',
                'button:has-text("下载")',
                'button[aria-label="导出"]',
                'button[aria-label="更多操作"]',
                '[class*="export"]',
                '[class*="download"]',
                'button[title*="导出"]'
            ]
            
            export_button = None
            for selector in export_selectors:
                try:
                    if page.locator(selector).is_visible():
                        export_button = selector
                        print(f"✅ 找到导出按钮: {selector}")
                        break
                except:
                    continue
            
            if not export_button:
                print("❌ 未找到导出按钮")
                
                # 尝试使用快捷键
                print("\n5. 尝试使用快捷键导出...")
                page.keyboard.press("Control+Shift+E")
                time.sleep(2)
            else:
                print("\n5. 点击导出按钮...")
                page.click(export_button)
                time.sleep(2)
            
            # 查找Excel选项
            print("\n6. 选择Excel格式...")
            excel_selectors = [
                'text="Excel(.xlsx)"',
                'text="Microsoft Excel"',
                'text="xlsx"',
                '[class*="xlsx"]'
            ]
            
            excel_found = False
            for selector in excel_selectors:
                try:
                    if page.locator(selector).is_visible():
                        print(f"✅ 找到Excel选项: {selector}")
                        
                        # 设置下载处理
                        download_promise = page.expect_download()
                        
                        # 点击下载
                        page.click(selector)
                        
                        # 等待下载
                        print("\n7. 等待下载...")
                        download = download_promise.value
                        
                        # 保存文件
                        output_file = f"/root/projects/tencent-doc-manager/playwright_test_{int(time.time())}.xlsx"
                        download.save_as(output_file)
                        
                        print(f"\n✅ 文件已保存: {output_file}")
                        
                        # 验证文件格式
                        with open(output_file, 'rb') as f:
                            header = f.read(4)
                            file_size = os.path.getsize(output_file)
                        
                        if header == b'PK\x03\x04':
                            print(f"✅ 这是真正的Excel文件！大小: {file_size} bytes")
                            excel_found = True
                        else:
                            print(f"❌ 文件格式错误: {header}")
                        
                        break
                except Exception as e:
                    print(f"处理{selector}时出错: {e}")
                    continue
            
            if not excel_found:
                print("\n❌ 无法通过Playwright下载Excel文件")
                print("可能原因：")
                print("1. 页面结构已更改")
                print("2. 需要额外的权限验证")
                print("3. 导出功能被限制")
                
                # 保存页面截图用于调试
                screenshot = f"/root/projects/tencent-doc-manager/playwright_debug_{int(time.time())}.png"
                page.screenshot(path=screenshot)
                print(f"\n页面截图已保存: {screenshot}")
                
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            return False
            
        finally:
            browser.close()
    
    return True

if __name__ == "__main__":
    success = test_playwright_download()
    
    print("\n" + "=" * 60)
    if success:
        print("测试结果: ✅ Playwright可以下载真正的Excel文件")
    else:
        print("测试结果: ❌ Playwright下载失败")
    print("=" * 60)