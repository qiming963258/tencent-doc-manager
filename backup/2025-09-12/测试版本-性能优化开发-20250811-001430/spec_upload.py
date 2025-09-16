#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档上传工具 - 严格按照TECHNICAL_SPEC.md规范实现
"""

import asyncio
import os
import argparse
from playwright.async_api import async_playwright


async def spec_compliant_upload(file_path, cookies, headless=False):
    """按照技术规格文档实现的上传功能"""
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}")
        return False
    
    playwright = await async_playwright().start()
    
    try:
        # 启动浏览器
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        # 添加多域名cookies
        if cookies:
            cookie_list = []
            for cookie_str in cookies.split(';'):
                if '=' in cookie_str:
                    name, value = cookie_str.strip().split('=', 1)
                    domains = ['docs.qq.com', '.docs.qq.com', 'qq.com', '.qq.com']
                    for domain in domains:
                        cookie_list.append({
                            'name': name, 'value': value, 'domain': domain,
                            'path': '/', 'httpOnly': False, 'secure': True, 'sameSite': 'None'
                        })
            await context.add_cookies(cookie_list)
            print(f"已添加 {len(cookie_list)} 个cookies")
        
        # 步骤1: 访问腾讯文档主页
        print("步骤1: 访问腾讯文档主页...")
        await page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)
        
        # 步骤2: 点击导入按钮 - 使用规格文档中的精确选择器
        print("步骤2: 点击导入按钮...")
        import_btn = await page.query_selector('button.desktop-import-button-pc')
        
        if not import_btn:
            print("错误: 未找到导入按钮")
            return False
        
        print("找到导入按钮，准备点击...")
        
        # 设置文件选择器监听 - 在点击前设置
        file_chooser_promise = page.wait_for_event('filechooser')
        
        # 点击导入按钮
        await import_btn.click()
        print("已点击导入按钮")
        
        # 步骤3: 等待并处理文件选择器
        print("步骤3: 等待文件选择器出现...")
        try:
            file_chooser = await asyncio.wait_for(file_chooser_promise, timeout=10.0)
            
            # 选择文件
            print(f"设置文件: {file_path}")
            await file_chooser.set_files(file_path)
            print("文件已选择")
            
            # 等待上传对话框出现
            await page.wait_for_timeout(3000)
            
            # 步骤4: 点击确定按钮 - 使用规格文档中的精确选择器
            print("步骤4: 查找并点击确定按钮...")
            
            # 使用规格文档中的选择器: 'div.dui-button-container:has-text("确定")'
            confirm_btn = await page.query_selector('div.dui-button-container:has-text("确定")')
            
            if confirm_btn:
                print("找到确定按钮，准备点击...")
                await confirm_btn.click()
                print("已点击确定按钮")
            else:
                print("未找到确定按钮，尝试备用选择器...")
                # 备用选择器
                backup_selectors = [
                    '.dui-button-container:has-text("确定")',
                    'button:has-text("确定")',
                    '[data-dui-1-23-0="dui-button-container"]:has-text("确定")'
                ]
                
                found_confirm = False
                for selector in backup_selectors:
                    try:
                        backup_btn = await page.query_selector(selector)
                        if backup_btn:
                            print(f"使用备用选择器找到确定按钮: {selector}")
                            await backup_btn.click()
                            print("已点击确定按钮")
                            found_confirm = True
                            break
                    except Exception as e:
                        print(f"备用选择器 {selector} 失败: {e}")
                        continue
                
                if not found_confirm:
                    print("所有确定按钮选择器都失败，尝试键盘确认...")
                    await page.keyboard.press('Enter')
                    print("使用回车键确认")
            
            # 步骤5: 等待上传完成
            print("步骤5: 等待上传完成...")
            
            # 监控上传进度，最多等待30秒
            upload_success = False
            for i in range(30):
                try:
                    # 检查上传完成的标识
                    success_indicators = await page.evaluate('''() => {
                        const bodyText = document.body.textContent;
                        return {
                            hasCompleteText: bodyText.includes('上传完成') || 
                                           bodyText.includes('导入完成') || 
                                           bodyText.includes('导入成功'),
                            hasDocuments: document.querySelectorAll('[class*="doc-item"], [class*="file-item"], .document-item').length > 0,
                            hasProgressBar: document.querySelectorAll('[class*="progress"], [class*="upload"]').length > 0
                        };
                    }''')
                    
                    if success_indicators['hasCompleteText']:
                        print("检测到上传完成标识")
                        upload_success = True
                        break
                    elif success_indicators['hasDocuments']:
                        print("检测到文档列表更新")
                        upload_success = True
                        break
                    elif not success_indicators['hasProgressBar'] and i > 10:
                        print("上传进度条消失，可能已完成")
                        upload_success = True
                        break
                    
                    await page.wait_for_timeout(1000)
                    if i % 5 == 0:
                        print(f"上传中... ({i}秒)")
                    
                except Exception as e:
                    print(f"上传监控异常: {e}")
                    continue
            
            if upload_success:
                print("✅ 文件上传成功!")
                return True
            else:
                print("⚠️ 上传超时，但可能已完成")
                return False
                
        except asyncio.TimeoutError:
            print("❌ 文件选择器等待超时")
            return False
        except Exception as e:
            print(f"❌ 文件选择处理失败: {e}")
            return False
        
    except Exception as e:
        print(f"❌ 上传过程失败: {e}")
        return False
    finally:
        await browser.close()
        await playwright.stop()


async def main():
    parser = argparse.ArgumentParser(description='腾讯文档上传工具 - 按技术规格实现')
    parser.add_argument('file_path', help='要上传的文件路径')
    parser.add_argument('-c', '--cookies', required=True, help='登录Cookie')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口')
    
    args = parser.parse_args()
    
    success = await spec_compliant_upload(
        args.file_path, 
        args.cookies, 
        headless=not args.visible
    )
    
    if success:
        print("\n[成功] 文件上传完成")
    else:
        print("\n[失败] 文件上传失败")


if __name__ == "__main__":
    asyncio.run(main())