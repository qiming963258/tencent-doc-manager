#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档最终自动上传工具
基于成功的手动测试经验
"""

import asyncio
import os
import argparse
from playwright.async_api import async_playwright


async def final_auto_upload(file_path, cookies, headless=False):
    """最终版本的自动上传工具"""
    
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
        
        # 访问腾讯文档主页
        print("访问腾讯文档主页...")
        await page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)
        
        # 记录初始文档数量
        initial_doc_count = await page.evaluate('''() => {
            return document.querySelectorAll('[class*="doc"], [class*="file"], .document-item').length;
        }''')
        print(f"初始文档数量: {initial_doc_count}")
        
        # 点击导入按钮
        print("查找并点击导入按钮...")
        import_btn = await page.query_selector('button.desktop-import-button-pc')
        
        if not import_btn:
            print("错误: 未找到导入按钮")
            return False
        
        # 监听文件选择器事件
        file_chooser_handled = False
        
        def handle_file_chooser(file_chooser):
            nonlocal file_chooser_handled
            if not file_chooser_handled:
                print(f"文件选择器触发，设置文件: {file_path}")
                asyncio.create_task(file_chooser.set_files(file_path))
                file_chooser_handled = True
                print("文件已设置")
        
        page.on('filechooser', handle_file_chooser)
        
        # 点击导入按钮
        await import_btn.click()
        print("已点击导入按钮")
        
        # 等待文件选择器触发
        await page.wait_for_timeout(3000)
        
        if not file_chooser_handled:
            print("文件选择器未触发，尝试查找本地文件选项...")
            
            # 查找本地文件选项
            local_file_options = [
                'text="本地文件"',
                'text="从电脑上传"',
                'text="上传文件"',
                '[class*="local"]',
                '[class*="file"]',
                '[class*="upload"]'
            ]
            
            for option_selector in local_file_options:
                try:
                    option = await page.query_selector(option_selector)
                    if option:
                        print(f"找到本地文件选项: {option_selector}")
                        await option.click()
                        print("点击了本地文件选项")
                        await page.wait_for_timeout(2000)
                        break
                except Exception as e:
                    continue
            
            # 再等待文件选择器
            await page.wait_for_timeout(3000)
        
        if not file_chooser_handled:
            print("尝试直接设置文件输入...")
            # 查找并使用隐藏的文件输入
            file_inputs = await page.query_selector_all('input[type="file"]')
            if file_inputs:
                print(f"找到 {len(file_inputs)} 个文件输入")
                try:
                    await file_inputs[0].set_input_files(file_path)
                    print("通过文件输入设置了文件")
                    file_chooser_handled = True
                except Exception as e:
                    print(f"文件输入设置失败: {e}")
        
        if not file_chooser_handled:
            print("所有文件选择方法都失败")
            return False
        
        # 等待上传对话框并点击确定
        await page.wait_for_timeout(2000)
        
        print("查找确定按钮...")
        confirm_selectors = [
            'div.dui-button-container:has-text("确定")',
            '.dui-button-container:has-text("确定")',
            'button:has-text("确定")',
            '[data-dui-1-23-0="dui-button-container"]:has-text("确定")'
        ]
        
        confirm_clicked = False
        for selector in confirm_selectors:
            try:
                confirm_btn = await page.query_selector(selector)
                if confirm_btn:
                    print(f"找到确定按钮: {selector}")
                    await confirm_btn.click()
                    print("已点击确定按钮")
                    confirm_clicked = True
                    break
            except Exception as e:
                continue
        
        if not confirm_clicked:
            print("未找到确定按钮，使用键盘确认...")
            await page.keyboard.press('Enter')
        
        # 等待上传完成
        print("监控上传进度...")
        
        for i in range(60):  # 最多等待60秒
            try:
                # 检查文档数量变化
                current_doc_count = await page.evaluate('''() => {
                    return document.querySelectorAll('[class*="doc"], [class*="file"], .document-item').length;
                }''')
                
                # 检查上传状态文字
                status_text = await page.evaluate('''() => {
                    const bodyText = document.body.textContent;
                    return {
                        complete: bodyText.includes('上传完成') || bodyText.includes('导入完成'),
                        error: bodyText.includes('上传失败') || bodyText.includes('导入失败'),
                        uploading: bodyText.includes('上传中') || bodyText.includes('正在上传')
                    };
                }''')
                
                if current_doc_count > initial_doc_count:
                    print(f"检测到文档数量增加: {initial_doc_count} -> {current_doc_count}")
                    print("上传成功!")
                    return True
                elif status_text['complete']:
                    print("检测到上传完成文字")
                    return True
                elif status_text['error']:
                    print("检测到上传错误")
                    return False
                elif status_text['uploading'] and i % 5 == 0:
                    print(f"正在上传中... ({i}秒)")
                
                await page.wait_for_timeout(1000)
                
            except Exception as e:
                print(f"监控异常: {e}")
                continue
        
        # 最终检查
        final_doc_count = await page.evaluate('''() => {
            return document.querySelectorAll('[class*="doc"], [class*="file"], .document-item').length;
        }''')
        
        if final_doc_count > initial_doc_count:
            print(f"最终检查: 文档数量增加 {initial_doc_count} -> {final_doc_count}")
            return True
        else:
            print("上传超时或失败")
            return False
        
    except Exception as e:
        print(f"自动上传异常: {e}")
        return False
    finally:
        await browser.close()
        await playwright.stop()


async def main():
    parser = argparse.ArgumentParser(description='腾讯文档最终自动上传工具')
    parser.add_argument('file_path', help='要上传的文件路径')
    parser.add_argument('-c', '--cookies', required=True, help='登录Cookie')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口')
    
    args = parser.parse_args()
    
    print(f"开始自动上传: {args.file_path}")
    
    success = await final_auto_upload(
        args.file_path, 
        args.cookies, 
        headless=not args.visible
    )
    
    if success:
        print("\n[成功] 文件自动上传完成!")
    else:
        print("\n[失败] 文件自动上传失败")


if __name__ == "__main__":
    asyncio.run(main())