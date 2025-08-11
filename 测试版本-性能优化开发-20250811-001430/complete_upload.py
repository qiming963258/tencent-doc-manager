#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档上传工具 - 完整流程版本
处理"选择上传方式窗口"
"""

import asyncio
import os
import argparse
from playwright.async_api import async_playwright


async def complete_upload_flow(file_path, cookies, headless=False):
    """完整的上传流程，包括选择上传方式窗口"""
    
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
        
        # 点击导入按钮
        print("查找并点击导入按钮...")
        import_btn = await page.query_selector('button.desktop-import-button-pc')
        
        if not import_btn:
            print("错误: 未找到导入按钮")
            return False
        
        await import_btn.click()
        print("已点击导入按钮")
        
        # 等待可能出现的选择上传方式窗口
        await page.wait_for_timeout(3000)
        
        # 查找并点击"本地文件"或类似的选项（如果有的话）
        print("查找本地文件上传选项...")
        local_options = [
            'text="本地文件"',
            'text="从电脑上传"',
            'text="上传文件"',
            'text="导入文件"',
            'text="文件上传"',
            '[class*="local"]',
            '[class*="file"]'
        ]
        
        local_option_clicked = False
        for selector in local_options:
            try:
                option = await page.query_selector(selector)
                if option:
                    print(f"找到本地文件选项: {selector}")
                    await option.click()
                    print("点击了本地文件选项")
                    local_option_clicked = True
                    await page.wait_for_timeout(2000)
                    break
            except Exception as e:
                continue
        
        if not local_option_clicked:
            print("未找到本地文件选项，直接进行文件选择...")
        
        # 现在设置文件选择器监听
        print("设置文件选择器监听...")
        
        # 方法1: 直接监听文件选择器
        try:
            file_chooser_promise = page.wait_for_event('filechooser', timeout=15000)
            
            # 如果还没有触发文件选择器，再次点击导入按钮
            if not local_option_clicked:
                print("再次点击导入按钮触发文件选择器...")
                await import_btn.click()
                await page.wait_for_timeout(1000)
            
            print("等待文件选择器...")
            file_chooser = await file_chooser_promise
            
            # 选择文件
            print(f"选择文件: {file_path}")
            await file_chooser.set_files(file_path)
            print("文件已选择")
            
        except asyncio.TimeoutError:
            print("文件选择器超时，尝试查找隐藏的文件输入...")
            
            # 方法2: 查找隐藏的文件输入元素
            file_inputs = await page.query_selector_all('input[type="file"]')
            print(f"找到 {len(file_inputs)} 个文件输入元素")
            
            if file_inputs:
                try:
                    await file_inputs[0].set_input_files(file_path)
                    print("通过文件输入元素设置了文件")
                except Exception as e:
                    print(f"设置文件输入失败: {e}")
                    return False
            else:
                print("没有找到任何文件输入元素")
                return False
        
        # 等待上传对话框出现
        await page.wait_for_timeout(3000)
        
        # 在弹出的选择上传方式窗口中选择确定
        print("查找并点击确定按钮...")
        
        confirm_selectors = [
            'div.dui-button-container:has-text("确定")',
            '.dui-button-container:has-text("确定")',
            'div[data-dui-1-23-0="dui-button-container"]:has-text("确定")',
            'button:has-text("确定")',
            '.dui-button:has-text("确定")'
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
                print(f"确定按钮选择器 {selector} 失败: {e}")
                continue
        
        if not confirm_clicked:
            print("未找到确定按钮，尝试键盘确认...")
            await page.keyboard.press('Enter')
            print("使用回车键确认")
        
        # 等待上传完成
        print("等待上传完成...")
        
        upload_success = False
        for i in range(60):  # 等待最多60秒
            try:
                # 检查上传状态
                status = await page.evaluate('''() => {
                    const bodyText = document.body.textContent;
                    return {
                        complete: bodyText.includes('上传完成') || 
                                bodyText.includes('导入完成') || 
                                bodyText.includes('导入成功'),
                        uploading: bodyText.includes('上传中') || 
                                 bodyText.includes('正在上传'),
                        error: bodyText.includes('上传失败') || 
                             bodyText.includes('导入失败'),
                        docCount: document.querySelectorAll('[class*="doc-item"], [class*="file-item"]').length
                    };
                }''')
                
                if status['complete']:
                    print("检测到上传完成标识")
                    upload_success = True
                    break
                elif status['error']:
                    print("检测到上传错误")
                    break
                elif status['docCount'] > 0 and i > 10:
                    print("检测到文档列表更新")
                    upload_success = True
                    break
                elif status['uploading']:
                    if i % 5 == 0:
                        print(f"正在上传中... ({i}秒)")
                else:
                    if i % 10 == 0 and i > 0:
                        print(f"等待上传完成... ({i}秒)")
                
                await page.wait_for_timeout(1000)
                
            except Exception as e:
                print(f"上传状态检查异常: {e}")
                continue
        
        if upload_success:
            print("文件上传成功!")
            return True
        else:
            print("上传超时或失败")
            
            # 最后检查一次
            final_check = await page.evaluate('''() => {
                return {
                    bodyText: document.body.textContent.slice(-500),
                    docElements: document.querySelectorAll('[class*="doc"], [class*="file"]').length
                };
            }''')
            
            print(f"最终检查: 文档元素数量 {final_check['docElements']}")
            return final_check['docElements'] > 0
        
    except Exception as e:
        print(f"上传过程异常: {e}")
        return False
    finally:
        await browser.close()
        await playwright.stop()


async def main():
    parser = argparse.ArgumentParser(description='腾讯文档完整上传流程工具')
    parser.add_argument('file_path', help='要上传的文件路径')
    parser.add_argument('-c', '--cookies', required=True, help='登录Cookie')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口')
    
    args = parser.parse_args()
    
    success = await complete_upload_flow(
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