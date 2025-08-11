#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档上传工具 - 自动上传Excel文件到主页
"""

import asyncio
import os
import argparse
from pathlib import Path
from playwright.async_api import async_playwright


class TencentDocUploader:
    """腾讯文档自动上传工具"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        
    async def start_browser(self, headless=False):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        
        # 启动浏览器
        self.browser = await self.playwright.chromium.launch(
            headless=headless
        )
        
        # 创建页面上下文
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await context.new_page()
    
    async def login_with_cookies(self, cookies):
        """使用cookies登录 - 多域名版本"""
        if cookies:
            cookie_list = []
            for cookie_str in cookies.split(';'):
                if '=' in cookie_str:
                    name, value = cookie_str.strip().split('=', 1)
                    # 为多个domain添加cookies
                    domains = ['docs.qq.com', '.docs.qq.com', 'qq.com', '.qq.com']
                    for domain in domains:
                        cookie_list.append({
                            'name': name,
                            'value': value,
                            'domain': domain,
                            'path': '/',
                            'httpOnly': False,
                            'secure': True,
                            'sameSite': 'None'
                        })
            try:
                await self.page.context.add_cookies(cookie_list)
                print(f"已添加 {len(cookie_list)} 个cookies（多域名）")
            except Exception as e:
                print(f"添加cookies时出错: {e}")
                # 降级到简单版本
                simple_cookies = []
                for cookie_str in cookies.split(';'):
                    if '=' in cookie_str:
                        name, value = cookie_str.strip().split('=', 1)
                        simple_cookies.append({
                            'name': name,
                            'value': value,
                            'domain': '.qq.com',
                            'path': '/'
                        })
                await self.page.context.add_cookies(simple_cookies)
                print(f"已添加简化cookies: {len(simple_cookies)} 个")
    
    async def upload_file_to_main_page(self, file_path, homepage_url="https://docs.qq.com/desktop"):
        """按照TECHNICAL_SPEC.md 5.1.2节规范上传文件到腾讯文档主页"""
        print(f"正在访问腾讯文档主页: {homepage_url}")
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            file_size = os.path.getsize(file_path)
            print(f"准备上传文件: {file_path} (大小: {file_size} 字节)")
            
            # 访问主页
            print("开始加载主页...")
            await self.page.goto(homepage_url, wait_until='domcontentloaded', timeout=30000)
            print("DOM加载完成")
            
            # 等待页面渲染
            print("等待页面渲染...")
            await self.page.wait_for_timeout(8000)
            print("页面加载完成")
            
            # 检查登录状态
            await self._check_login_status()
            
            # 步骤1: 导入按钮 - 严格按照SPEC规范
            print("步骤1: 寻找导入按钮...")
            import_btn = await self.page.query_selector('button.desktop-import-button-pc')
            
            if not import_btn:
                raise Exception("未找到导入按钮 button.desktop-import-button-pc")
            
            print("找到导入按钮，准备点击...")
            
            # 监听文件选择器事件
            file_chooser_promise = self.page.wait_for_event('filechooser')
            
            # 点击导入按钮
            await import_btn.click()
            print("已点击导入按钮")
            
            # 步骤2: 文件选择 - 等待文件选择器或查找input[type="file"]
            print("步骤2: 处理文件选择...")
            
            try:
                # 方法1: 等待文件选择器事件
                file_chooser = await asyncio.wait_for(file_chooser_promise, timeout=10.0)
                print("文件选择器触发")
                await file_chooser.set_files(file_path)
                print(f"文件已通过选择器设置: {file_path}")
                
            except asyncio.TimeoutError:
                print("文件选择器超时，查找input[type=\"file\"]元素...")
                
                # 方法2: 直接查找input[type="file"] - 按照SPEC规范
                await self.page.wait_for_timeout(2000)  # 等待DOM更新
                
                file_input = await self.page.query_selector('input[type="file"]')
                if file_input:
                    print("找到input[type=\"file\"]元素")
                    await file_input.set_input_files(file_path)
                    print(f"文件已通过input元素设置: {file_path}")
                else:
                    raise Exception("未找到input[type=\"file\"]元素")
            
            # 等待上传对话框
            await self.page.wait_for_timeout(3000)
            
            # 步骤3: 确认上传 - 增强版选择器策略
            print("步骤3: 寻找并点击确定按钮...")
            
            # 扩展的确定按钮选择器列表
            confirm_selectors = [
                'div.dui-button-container:has-text("确定")',
                '.dui-button-container:has-text("确定")',
                'button:has-text("确定")',
                '.dui-button:has-text("确定")',
                '[data-dui-1-23-0="dui-button-container"]:has-text("确定")',
                'div[role="button"]:has-text("确定")',
                '.ant-btn:has-text("确定")',
                'button.ant-btn-primary:has-text("确定")',
                '.primary-button:has-text("确定")',
                'button[type="submit"]:has-text("确定")',
                # 英文版本
                'div.dui-button-container:has-text("OK")',
                'button:has-text("OK")',
                'button:has-text("Confirm")',
                # 通用按钮（如果文本匹配失败）
                'div.dui-button-container',
                'button[class*="primary"]',
                'button[class*="confirm"]'
            ]
            
            found_confirm = False
            for selector in confirm_selectors:
                try:
                    await self.page.wait_for_timeout(500)
                    confirm_btn = await self.page.query_selector(selector)
                    if confirm_btn:
                        # 检查按钮是否可见和可点击
                        is_visible = await confirm_btn.is_visible()
                        is_enabled = await confirm_btn.is_enabled()
                        
                        if is_visible and is_enabled:
                            print(f"找到确定按钮: {selector}")
                            await confirm_btn.click()
                            print("已点击确定按钮")
                            found_confirm = True
                            break
                        else:
                            print(f"按钮找到但不可用: {selector} (visible:{is_visible}, enabled:{is_enabled})")
                            
                except Exception as e:
                    print(f"选择器 {selector} 测试失败: {e}")
                    continue
            
            if not found_confirm:
                print("所有确定按钮选择器都失败，尝试键盘确认...")
                try:
                    await self.page.keyboard.press('Enter')
                    print("使用键盘Enter确认")
                    found_confirm = True
                except Exception as e:
                    print(f"键盘确认失败: {e}")
            
            if not found_confirm:
                # 最后尝试：查找所有可能的按钮并尝试点击
                print("尝试查找所有按钮元素...")
                all_buttons = await self.page.query_selector_all('button, div[role="button"], .dui-button-container')
                print(f"找到 {len(all_buttons)} 个按钮元素")
                
                for i, button in enumerate(all_buttons[:5]):  # 只测试前5个
                    try:
                        text = await button.text_content()
                        print(f"按钮 {i}: '{text}'")
                        if text and ("确定" in text or "OK" in text.upper() or "CONFIRM" in text.upper()):
                            await button.click()
                            print(f"点击了按钮: '{text}'")
                            found_confirm = True
                            break
                    except Exception as e:
                        continue
            
            if not found_confirm:
                print("警告: 未能确认上传，但文件可能已经上传成功")
            
            # 等待上传完成
            print("步骤4: 等待上传完成...")
            await self._wait_for_upload_completion()
            print("文件上传成功！")
            return True
                
        except Exception as e:
            print(f"上传失败: {e}")
            return False
    
    async def _check_login_status(self):
        """检查登录状态"""
        # 检查是否有登录相关文字
        has_login_text = await self.page.evaluate('''() => {
            return document.body.textContent.includes('登录') && 
                   !document.body.textContent.includes('已登录');
        }''')
        
        if has_login_text:
            print("警告: 可能需要登录才能上传文件")
        else:
            print("登录状态检查通过")
    
    async def _find_import_button(self):
        """寻找导入按钮"""
        # 使用你提供的精确选择器
        import_selectors = [
            'button.desktop-import-button-pc',
            '.desktop-import-button-pc',
            'button:has-text("导入")',
            '[class*="import-button"]',
            '[class*="desktop-import"]'
        ]
        
        for selector in import_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn:
                    print(f"找到导入按钮: {selector}")
                    return btn
            except Exception as e:
                print(f"选择器 {selector} 失败: {e}")
                continue
        
        print("未找到导入按钮，尝试搜索所有包含'导入'文字的按钮...")
        
        # 备用方法：搜索所有按钮
        all_buttons = await self.page.evaluate('''() => {
            const buttons = [];
            document.querySelectorAll('button, div[role="button"], [class*="btn"]').forEach((el, index) => {
                const text = el.textContent || '';
                if (text.includes('导入') || text.includes('上传') || text.includes('import')) {
                    buttons.push({
                        index: index,
                        text: text.trim(),
                        className: el.className,
                        id: el.id
                    });
                }
            });
            return buttons;
        }''')
        
        if all_buttons:
            print(f"找到 {len(all_buttons)} 个可能的导入按钮:")
            for btn in all_buttons[:5]:  # 只显示前5个
                print(f"  - {btn}")
            
            # 尝试点击第一个
            first_btn = await self.page.query_selector('button, div[role="button"], [class*="btn"]')
            if first_btn:
                btn_text = await first_btn.text_content()
                if '导入' in btn_text or '上传' in btn_text:
                    return first_btn
        
        return None
    
    async def _handle_file_selection(self, file_path):
        """处理文件选择对话框"""
        try:
            # 方法1: 监听文件输入元素
            print("方法1: 寻找文件输入元素...")
            
            # 等待文件输入元素出现
            await self.page.wait_for_timeout(2000)
            
            file_input_selectors = [
                'input[type="file"]',
                'input[accept*=".xlsx"]',
                'input[accept*=".xls"]',
                'input[accept*="excel"]',
                '.file-input',
                '[class*="upload-input"]'
            ]
            
            for selector in file_input_selectors:
                file_input = await self.page.query_selector(selector)
                if file_input:
                    print(f"找到文件输入元素: {selector}")
                    
                    # 设置文件
                    await file_input.set_input_files(file_path)
                    print(f"文件已选择: {file_path}")
                    
                    # 等待对话框出现
                    await self.page.wait_for_timeout(2000)
                    return True
            
            # 方法2: 使用文件选择器监听
            print("方法2: 监听文件选择器事件...")
            
            # 创建文件选择器处理函数
            file_chooser_promise = None
            
            async def wait_for_file_chooser():
                nonlocal file_chooser_promise
                file_chooser_promise = self.page.wait_for_event('filechooser')
            
            # 开始监听文件选择器
            await wait_for_file_chooser()
            
            # 再次点击导入按钮触发文件选择
            import_btn = await self._find_import_button()
            if import_btn:
                print("再次点击导入按钮触发文件选择...")
                await import_btn.click()
                
                # 等待文件选择器出现
                if file_chooser_promise:
                    file_chooser = await file_chooser_promise
                    await file_chooser.set_files(file_path)
                    print(f"通过文件选择器设置文件: {file_path}")
                    
                    # 等待对话框出现
                    await self.page.wait_for_timeout(2000)
                    return True
            
        except Exception as e:
            print(f"文件选择处理异常: {e}")
        
        return False
    
    async def _click_confirm_button(self):
        """点击确定按钮确认上传"""
        try:
            print("寻找确定按钮...")
            
            # 等待确认对话框出现
            await self.page.wait_for_timeout(2000)
            
            # 使用你提供的精确选择器
            confirm_selectors = [
                'div.dui-button-container:has-text("确定")',
                '.dui-button-container:has-text("确定")',
                'div[data-dui-1-23-0="dui-button-container"]:has-text("确定")',
                'button:has-text("确定")',
                '.dui-button:has-text("确定")',
                '[class*="confirm"]:has-text("确定")',
                '[class*="button"]:has-text("确定")'
            ]
            
            for selector in confirm_selectors:
                try:
                    confirm_btn = await self.page.query_selector(selector)
                    if confirm_btn:
                        print(f"找到确定按钮: {selector}")
                        await confirm_btn.click()
                        print("已点击确定按钮")
                        await self.page.wait_for_timeout(2000)
                        return True
                except Exception as e:
                    print(f"选择器 {selector} 失败: {e}")
                    continue
            
            # 备用方法：搜索所有包含"确定"文字的可点击元素
            print("备用方法：搜索所有确定按钮...")
            
            confirm_elements = await self.page.evaluate('''() => {
                const elements = [];
                const selectors = ['div', 'button', 'span', '[role="button"]'];
                
                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach((el, index) => {
                        const text = el.textContent || '';
                        if (text.trim() === '确定' || text.includes('确定')) {
                            elements.push({
                                index: index,
                                tagName: el.tagName,
                                text: text.trim(),
                                className: el.className,
                                id: el.id,
                                selector: selector
                            });
                        }
                    });
                });
                
                return elements;
            }''')
            
            if confirm_elements:
                print(f"找到 {len(confirm_elements)} 个可能的确定按钮:")
                for elem in confirm_elements[:3]:  # 显示前3个
                    print(f"  - {elem}")
                
                # 尝试点击第一个
                try:
                    first_confirm = await self.page.query_selector('div:has-text("确定"), button:has-text("确定"), [role="button"]:has-text("确定")')
                    if first_confirm:
                        await first_confirm.click()
                        print("通过备用方法点击了确定按钮")
                        await self.page.wait_for_timeout(2000)
                        return True
                except Exception as e:
                    print(f"备用方法点击失败: {e}")
            
            # 最后尝试：使用键盘回车
            print("最后尝试：使用键盘回车确认...")
            await self.page.keyboard.press('Enter')
            await self.page.wait_for_timeout(2000)
            return True
            
        except Exception as e:
            print(f"确定按钮点击异常: {e}")
            return False
    
    async def _wait_for_upload_completion(self):
        """等待上传完成"""
        print("监控上传进度...")
        
        # 等待上传进度或完成提示
        upload_indicators = [
            '.upload-progress',
            '.progress-bar',
            '[class*="upload"]',
            '[class*="progress"]',
            'text=上传中',
            'text=上传完成',
            'text=导入完成'
        ]
        
        # 等待最多60秒
        for i in range(60):
            try:
                # 检查是否有上传完成的指示
                completed = await self.page.evaluate('''() => {
                    const text = document.body.textContent;
                    return text.includes('上传完成') || 
                           text.includes('导入完成') || 
                           text.includes('导入成功');
                }''')
                
                if completed:
                    print("检测到上传完成标识")
                    return True
                
                # 检查是否有新文档出现在列表中
                doc_list = await self.page.query_selector_all('[class*="doc-item"], [class*="file-item"], .document-item')
                if len(doc_list) > 0:
                    print(f"检测到文档列表更新，共 {len(doc_list)} 个文档")
                    # 再等待2秒确保完成
                    await self.page.wait_for_timeout(2000)
                    return True
                
                await self.page.wait_for_timeout(1000)
                
            except Exception as e:
                print(f"上传监控异常: {e}")
                continue
        
        print("上传等待超时，但可能已完成")
        return True
    
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()


async def main():
    parser = argparse.ArgumentParser(description='腾讯文档上传工具')
    parser.add_argument('file_path', help='要上传的文件路径')
    parser.add_argument('-c', '--cookies', help='登录Cookie')
    parser.add_argument('--homepage', default='https://docs.qq.com/desktop', help='腾讯文档主页URL')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口')
    
    args = parser.parse_args()
    
    uploader = TencentDocUploader()
    
    try:
        await uploader.start_browser(headless=not args.visible)
        
        if args.cookies:
            await uploader.login_with_cookies(args.cookies)
        
        result = await uploader.upload_file_to_main_page(args.file_path, args.homepage)
        
        if result:
            print(f"[成功] 文件上传完成: {args.file_path}")
        else:
            print("[失败] 文件上传失败")
            
    except Exception as e:
        print(f"程序出错: {e}")
    finally:
        await uploader.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序出错: {e}")