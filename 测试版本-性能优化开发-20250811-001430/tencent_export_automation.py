#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档自动导出工具 - 专注于自动化下载
直接模拟用户点击导出按钮，下载官方生成的文件
"""

import asyncio
import os
import time
import argparse
from pathlib import Path
from playwright.async_api import async_playwright


class TencentDocAutoExporter:
    """腾讯文档自动导出工具 - 专注下载自动化"""
    
    def __init__(self, download_dir=None):
        self.browser = None
        self.page = None
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        
    async def start_browser(self, headless=False):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        
        # 创建下载目录
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 启动浏览器，设置下载目录
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            downloads_path=self.download_dir
        )
        
        # 创建页面上下文，设置下载行为
        context = await self.browser.new_context(
            accept_downloads=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await context.new_page()
        
        # 监听下载事件
        self.downloaded_files = []
        self.page.on("download", self._handle_download)
    
    async def _handle_download(self, download):
        """处理下载事件"""
        filename = download.suggested_filename
        filepath = os.path.join(self.download_dir, filename)
        
        print(f"开始下载: {filename}")
        await download.save_as(filepath)
        
        self.downloaded_files.append(filepath)
        print(f"下载完成: {filepath}")
    
    async def login_with_cookies(self, cookies):
        """使用cookies登录"""
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
    
    async def auto_export_document(self, doc_url, export_format="excel"):
        """自动导出文档"""
        print(f"正在访问文档: {doc_url}")
        
        try:
            # 访问页面 - 使用最宽松的加载策略
            print("开始加载页面...")
            await self.page.goto(doc_url, wait_until='domcontentloaded', timeout=30000)
            print("DOM加载完成")
            
            # 简单等待，不依赖网络状态
            print("等待页面渲染...")
            await self.page.wait_for_timeout(8000)
            print("页面加载完成")
            
            # 检查登录状态 - 修正检测逻辑
            readonly_btn = await self.page.query_selector('.readonly-button')
            
            # 更精确的登录检测 - 查找导出菜单按钮作为登录状态指标
            menu_btn = await self.page.query_selector('.titlebar-icon-more')
            has_edit_access = await self.page.query_selector('[class*="edit"]')
            
            # 检查URL中是否包含确认登录的参数
            current_url = self.page.url
            
            print(f"页面状态检测: URL={current_url[:100]}...")
            print(f"只读按钮: {readonly_btn is not None}")
            print(f"菜单按钮: {menu_btn is not None}")
            print(f"编辑元素: {has_edit_access is not None}")
            
            if menu_btn:
                print("成功: 检测到导出菜单，用户已登录，继续导出流程...")
            elif readonly_btn:
                print("信息: 文档为只读模式，但可能仍可导出")
            else:
                print("警告: 未检测到明确的登录/菜单元素，尝试继续...")
            
            # 等待页面完全渲染和所有元素可交互
            print("等待页面元素完全加载...")
            await self.page.wait_for_timeout(5000)
            
            # 等待页面网络请求完成
            try:
                await self.page.wait_for_load_state('networkidle', timeout=10000)
                print("网络请求完成")
            except:
                print("网络等待超时，继续...")
                
            # 额外等待确保交互元素准备就绪
            await self.page.wait_for_timeout(3000)
            
            # 寻找导出按钮的多种可能方式
            export_methods = [
                self._try_menu_export,
                self._try_toolbar_export, 
                self._try_keyboard_shortcut_export,
                self._try_right_click_export
            ]
            
            success = False
            for method in export_methods:
                try:
                    print(f"尝试导出方法: {method.__name__}")
                    if await method(export_format):
                        success = True
                        break
                except Exception as e:
                    print(f"导出方法 {method.__name__} 失败: {e}")
                    continue
            
            if not success:
                raise Exception("所有导出方法都失败了")
            
            # 等待下载完成
            print("等待下载完成...")
            await self._wait_for_download(timeout=30)
            
            if self.downloaded_files:
                print(f"成功下载文件: {self.downloaded_files}")
                return self.downloaded_files
            else:
                raise Exception("未检测到下载的文件")
                
        except Exception as e:
            print(f"自动导出失败: {e}")
            return None
    
    async def _try_menu_export(self, export_format):
        """方法1: 通过菜单导出 - 使用精确的腾讯文档UI选择器"""
        try:
            # 步骤1: 点击三横线菜单按钮
            print("步骤1: 寻找三横线菜单按钮...")
            menu_selectors = [
                '.titlebar-icon.titlebar-icon-more',
                'div.titlebar-icon-more',
                '.titlebar-icon-more',
                '[class*="more"]'
            ]
            
            menu_btn = None
            for selector in menu_selectors:
                menu_btn = await self.page.query_selector(selector)
                if menu_btn:
                    print(f"找到菜单按钮: {selector}")
                    
                    # 检查元素是否可见和可点击
                    is_visible = await menu_btn.is_visible()
                    is_enabled = await menu_btn.is_enabled()
                    print(f"菜单按钮状态: 可见={is_visible}, 可点击={is_enabled}")
                    
                    if is_visible and is_enabled:
                        break
                    else:
                        print("菜单按钮不可用，尝试下一个选择器...")
                        menu_btn = None
            
            if menu_btn:
                print("找到可用的三横线菜单按钮，正在点击...")
                
                # 滚动到元素可见位置
                await menu_btn.scroll_into_view_if_needed()
                await self.page.wait_for_timeout(1000)
                
                # 正常点击
                await menu_btn.click()
                await self.page.wait_for_timeout(2000)  # 等待菜单展开
                
                # 步骤2: 点击"导出为"选项
                print("步骤2: 寻找'导出为'选项...")
                export_as_selectors = [
                    'li.dui-menu-item.dui-menu-submenu.mainmenu-submenu-exportAs',
                    '.mainmenu-submenu-exportAs',
                    'li[role="menuitem"]:has-text("导出为")',
                    'text=导出为'
                ]
                
                export_as_btn = None
                for selector in export_as_selectors:
                    export_as_btn = await self.page.query_selector(selector)
                    if export_as_btn:
                        is_visible = await export_as_btn.is_visible()
                        is_enabled = await export_as_btn.is_enabled()
                        print(f"找到'导出为'选项: {selector}, 可见={is_visible}, 可点击={is_enabled}")
                        
                        if is_visible and is_enabled:
                            break
                        else:
                            export_as_btn = None
                
                if export_as_btn:
                    await export_as_btn.click()
                    await self.page.wait_for_timeout(2000)  # 等待子菜单展开
                    
                    # 步骤3: 根据格式选择对应的导出选项
                    print(f"步骤3: 选择导出格式 ({export_format})...")
                    
                    if export_format.lower() in ['excel', 'xlsx']:
                        # 选择Excel格式
                        excel_selectors = [
                            'li.dui-menu-item.mainmenu-item-export-local',
                            '.mainmenu-item-export-local',
                            'li[role="menuitem"]:has-text("本地Excel表格")',
                            'text=本地Excel表格 (.xlsx)'
                        ]
                        
                        for selector in excel_selectors:
                            excel_btn = await self.page.query_selector(selector)
                            if excel_btn:
                                is_visible = await excel_btn.is_visible()
                                is_enabled = await excel_btn.is_enabled()
                                print(f"找到Excel导出选项: {selector}, 可见={is_visible}, 可点击={is_enabled}")
                                
                                if is_visible and is_enabled:
                                    await excel_btn.click()
                                    print("成功点击Excel导出选项")
                                    return True
                                
                    elif export_format.lower() == 'csv':
                        # 选择CSV格式  
                        csv_selectors = [
                            'li.dui-menu-item.mainmenu-item-export-csv',
                            '.mainmenu-item-export-csv',
                            'li[role="menuitem"]:has-text("本地CSV文件")',
                            'text=本地CSV文件（.csv，当前工作表）'
                        ]
                        
                        for selector in csv_selectors:
                            csv_btn = await self.page.query_selector(selector)
                            if csv_btn:
                                is_visible = await csv_btn.is_visible()
                                is_enabled = await csv_btn.is_enabled()
                                print(f"找到CSV导出选项: {selector}, 可见={is_visible}, 可点击={is_enabled}")
                                
                                if is_visible and is_enabled:
                                    await csv_btn.click()
                                    print("成功点击CSV导出选项")
                                    return True
                    
                else:
                    print("未找到可用的'导出为'选项")
            else:
                print("未找到可用的三横线菜单按钮")
                        
        except Exception as e:
            print(f"精确菜单导出方法异常: {e}")
            
        return False
    
    async def _try_toolbar_export(self, export_format):
        """方法2: 通过工具栏导出"""
        toolbar_selectors = [
            '.toolbar button:has-text("导出")',
            '.toolbar button:has-text("下载")',
            '.header button:has-text("导出")',
            '.header button:has-text("下载")',
            'button[class*="export"]',
            'button[class*="download"]'
        ]
        
        for selector in toolbar_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn:
                    print(f"找到工具栏导出按钮: {selector}")
                    await btn.click()
                    await self.page.wait_for_timeout(1000)
                    
                    if await self._select_export_format(export_format):
                        return True
                        
            except Exception as e:
                print(f"工具栏导出方法异常: {e}")
                continue
                
        return False
    
    async def _try_keyboard_shortcut_export(self, export_format):
        """方法3: 通过快捷键导出"""
        try:
            # 尝试Ctrl+S或Ctrl+E快捷键
            shortcuts = ['Control+s', 'Control+e', 'Control+Shift+e']
            
            for shortcut in shortcuts:
                print(f"尝试快捷键: {shortcut}")
                await self.page.keyboard.press(shortcut)
                await self.page.wait_for_timeout(2000)
                
                # 检查是否弹出导出对话框
                if await self._check_export_dialog():
                    if await self._select_export_format(export_format):
                        return True
                        
        except Exception as e:
            print(f"快捷键导出方法异常: {e}")
            
        return False
    
    async def _try_right_click_export(self, export_format):
        """方法4: 通过右键菜单导出"""
        try:
            # 右键点击表格区域
            table_area = await self.page.query_selector('.edit-area, [class*="table"], [class*="sheet"], #app')
            if table_area:
                await table_area.click(button='right')
                await self.page.wait_for_timeout(1000)
                
                # 寻找上下文菜单中的导出选项
                context_menu_selectors = [
                    'text=导出',
                    'text=下载', 
                    'text=Export',
                    'text=Download'
                ]
                
                for selector in context_menu_selectors:
                    export_option = await self.page.query_selector(selector)
                    if export_option:
                        print(f"找到右键菜单导出选项: {selector}")
                        await export_option.click()
                        await self.page.wait_for_timeout(1000)
                        
                        if await self._select_export_format(export_format):
                            return True
                            
        except Exception as e:
            print(f"右键菜单导出方法异常: {e}")
            
        return False
    
    async def _check_export_dialog(self):
        """检查是否有导出对话框出现"""
        dialog_selectors = [
            '.dialog',
            '.modal',
            '[class*="export-dialog"]',
            '[class*="download-dialog"]',
            '[role="dialog"]'
        ]
        
        for selector in dialog_selectors:
            if await self.page.query_selector(selector):
                return True
        return False
    
    async def _select_export_format(self, export_format):
        """选择导出格式"""
        try:
            if export_format.lower() in ['excel', 'xlsx']:
                format_selectors = [
                    'text=Excel',
                    'text=XLSX', 
                    'text=xlsx',
                    'button:has-text("Excel")',
                    'button:has-text("XLSX")'
                ]
            elif export_format.lower() == 'csv':
                format_selectors = [
                    'text=CSV',
                    'text=csv',
                    'button:has-text("CSV")'
                ]
            else:
                format_selectors = [
                    'text=Excel',
                    'text=XLSX'
                ]
            
            for selector in format_selectors:
                format_btn = await self.page.query_selector(selector)
                if format_btn:
                    print(f"选择导出格式: {selector}")
                    await format_btn.click()
                    await self.page.wait_for_timeout(1000)
                    
                    # 寻找确认按钮
                    confirm_selectors = [
                        'button:has-text("确定")',
                        'button:has-text("下载")',
                        'button:has-text("导出")',
                        'button:has-text("OK")',
                        'button:has-text("Download")',
                        'button:has-text("Export")',
                        '.btn-primary',
                        '.confirm-btn'
                    ]
                    
                    for confirm_selector in confirm_selectors:
                        confirm_btn = await self.page.query_selector(confirm_selector)
                        if confirm_btn:
                            print(f"点击确认按钮: {confirm_selector}")
                            await confirm_btn.click()
                            return True
                            
            # 如果没有找到格式选择，直接寻找确认按钮
            confirm_selectors = [
                'button:has-text("确定")',
                'button:has-text("下载")',
                'button:has-text("导出")',
                '.btn-primary'
            ]
            
            for confirm_selector in confirm_selectors:
                confirm_btn = await self.page.query_selector(confirm_selector)
                if confirm_btn:
                    print(f"点击确认按钮: {confirm_selector}")
                    await confirm_btn.click()
                    return True
                    
        except Exception as e:
            print(f"选择导出格式失败: {e}")
            
        return False
    
    async def _wait_for_download(self, timeout=30):
        """等待下载完成"""
        start_time = time.time()
        initial_count = len(self.downloaded_files)
        
        print(f"开始等待下载，当前文件数: {initial_count}")
        
        while time.time() - start_time < timeout:
            current_count = len(self.downloaded_files)
            if current_count > initial_count:
                print(f"检测到新文件通过下载事件，总数: {current_count}")
                # 再等待2秒确保下载完成
                await self.page.wait_for_timeout(2000)
                return True
            
            await self.page.wait_for_timeout(1000)
            print(f"等待中... ({int(time.time() - start_time)}/{timeout}s)")
            
        print(f"下载等待超时，最终文件数: {len(self.downloaded_files)}")
        return len(self.downloaded_files) > initial_count
    
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()


async def main():
    parser = argparse.ArgumentParser(description='腾讯文档自动导出工具')
    parser.add_argument('url', help='腾讯文档URL')
    parser.add_argument('-c', '--cookies', help='登录Cookie')
    parser.add_argument('-f', '--format', default='excel', choices=['excel', 'xlsx', 'csv'], help='导出格式')
    parser.add_argument('-d', '--download-dir', help='下载目录')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口')
    
    args = parser.parse_args()
    
    exporter = TencentDocAutoExporter(download_dir=args.download_dir)
    
    try:
        await exporter.start_browser(headless=not args.visible)
        
        if args.cookies:
            await exporter.login_with_cookies(args.cookies)
        
        result = await exporter.auto_export_document(args.url, args.format)
        
        if result:
            print(f"[成功] 自动导出完成，文件保存在: {result}")
        else:
            print("[失败] 自动导出失败")
            
    except Exception as e:
        print(f"程序出错: {e}")
    finally:
        await exporter.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序出错: {e}")