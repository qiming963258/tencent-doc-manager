#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档上传工具 - 完全自动化版本
解决文件选择器卡住问题
"""

import asyncio
import os
import argparse
from playwright.async_api import async_playwright


async def upload_file_directly(file_path, cookies, headless=False):
    """直接上传文件，避免文件选择器问题"""
    
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
        
        # 访问主页
        print("访问腾讯文档主页...")
        await page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)
        
        # 监听文件选择器，在点击按钮前设置
        print("设置文件选择器监听...")
        
        # 创建一个Promise来等待文件选择器
        file_chooser_promise = None
        
        def setup_file_chooser_listener():
            nonlocal file_chooser_promise
            file_chooser_promise = page.wait_for_event('filechooser')
        
        # 查找并点击导入按钮  
        print("查找导入按钮...")
        import_selectors = [
            'button.desktop-import-button-pc',
            '.desktop-import-button-pc', 
            'button:has-text("导入")',
            '[class*="import-button"]',
            '[class*="desktop-import"]'
        ]
        
        import_btn = None
        for selector in import_selectors:
            import_btn = await page.query_selector(selector)
            if import_btn:
                print(f"找到导入按钮: {selector}")
                break
                
        if not import_btn:
            print("未找到导入按钮")
            return False
        
        # 同时设置文件选择器监听和点击按钮
        print("同时设置文件选择器监听和点击按钮...")
        
        # 创建文件选择器监听任务
        file_chooser_task = asyncio.create_task(page.wait_for_event('filechooser', timeout=15000))
        
        # 等待一小段时间确保监听器设置完成
        await page.wait_for_timeout(500)
        
        print("点击导入按钮...")
        await import_btn.click()
        
        # 等待可能的菜单出现
        await page.wait_for_timeout(2000)
        
        # 检查是否出现了子菜单或对话框
        print("检查是否出现子菜单...")
        submenu_selectors = [
            'text="本地文件"',
            'text="从电脑上传"', 
            'text="上传文件"',
            'li:has-text("本地文件")',
            'li:has-text("从电脑上传")',
            '.menu-item:has-text("本地文件")'
        ]
        
        for selector in submenu_selectors:
            try:
                submenu = await page.query_selector(selector)
                if submenu:
                    print(f"找到子菜单选项: {selector}")
                    await submenu.click()
                    print("点击了子菜单选项")
                    await page.wait_for_timeout(1000)
                    break
            except Exception as e:
                print(f"子菜单选择器 {selector} 失败: {e}")
                continue
        
        # 等待文件选择器出现
        try:
            print("等待文件选择器...")
            file_chooser = await file_chooser_task
            
            print(f"设置文件: {file_path}")
            await file_chooser.set_files(file_path)
            print("文件已选择")
            
            # 等待对话框
            await page.wait_for_timeout(3000)
            
            # 查找确定按钮
            print("查找确定按钮...")
            confirm_selectors = [
                'div.dui-button-container:has-text("确定")',
                '.dui-button-container:has-text("确定")',
                'button:has-text("确定")'
            ]
            
            for selector in confirm_selectors:
                confirm_btn = await page.query_selector(selector)
                if confirm_btn:
                    print(f"找到确定按钮: {selector}")
                    await confirm_btn.click()
                    print("已点击确定按钮")
                    break
            else:
                # 使用回车键
                print("使用回车键确认...")
                await page.keyboard.press('Enter')
            
            # 等待上传完成
            print("等待上传完成...")
            await page.wait_for_timeout(10000)
            
            print("上传成功完成!")
            return True
            
        except asyncio.TimeoutError:
            print("文件选择器等待超时")
            return False
        except Exception as e:
            print(f"文件选择器处理失败: {e}")
            return False
        
    except Exception as e:
        print(f"上传失败: {e}")
        return False
    finally:
        await browser.close()
        await playwright.stop()


async def main():
    parser = argparse.ArgumentParser(description='腾讯文档直接上传工具')
    parser.add_argument('file_path', help='要上传的文件路径')
    parser.add_argument('-c', '--cookies', required=True, help='登录Cookie')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口')
    
    args = parser.parse_args()
    
    success = await upload_file_directly(
        args.file_path, 
        args.cookies, 
        headless=not args.visible
    )
    
    if success:
        print("[成功] 文件上传完成")
    else:
        print("[失败] 文件上传失败")


if __name__ == "__main__":
    asyncio.run(main())