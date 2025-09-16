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
from csv_version_manager import CSVVersionManager


class TencentDocAutoExporter:
    """腾讯文档自动导出工具 - 专注下载自动化"""
    
    def __init__(self, download_dir=None, enable_version_management=True):
        """初始化导出工具"""
        self.browser = None
        self.page = None
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        
        # 初始化版本管理器
        self.enable_version_management = enable_version_management
        if self.enable_version_management:
            self.version_manager = CSVVersionManager()
        else:
            self.version_manager = None
        
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
    
    def _analyze_document_url(self, doc_url):
        """
        阶段4增强功能：智能URL解析和文档类型识别
        
        Args:
            doc_url: 文档URL
            
        Returns:
            dict: URL分析结果和推荐策略
        """
        import re
        
        analysis = {
            "url": doc_url,
            "url_type": "unknown",
            "document_id": None,
            "is_specific_document": False,
            "recommended_methods": [],
            "expected_challenges": [],
            "adaptive_config": {}
        }
        
        try:
            print(f"🔍 开始智能URL分析: {doc_url}")
            
            # 1. 基础URL类型识别
            if "docs.qq.com/desktop" in doc_url.lower() and len(doc_url.replace("https://docs.qq.com/desktop", "").strip("/?")) == 0:
                analysis["url_type"] = "desktop_general"
                analysis["is_specific_document"] = False
                analysis["expected_challenges"].append("需要从列表中选择文档")
                analysis["recommended_methods"] = ["_try_right_click_export", "_try_keyboard_shortcut_export", "_try_menu_export"]
                analysis["adaptive_config"]["require_document_selection"] = True
                
            elif "docs.qq.com/sheet/" in doc_url.lower():
                # 具体表格文档
                sheet_match = re.search(r'/sheet/([A-Za-z0-9]+)', doc_url)
                if sheet_match:
                    analysis["document_id"] = sheet_match.group(1)
                    analysis["url_type"] = "specific_sheet"
                    analysis["is_specific_document"] = True
                    analysis["recommended_methods"] = ["_try_menu_export", "_try_toolbar_export", "_try_keyboard_shortcut_export"]
                    analysis["adaptive_config"]["direct_export_available"] = True
                    
            elif "docs.qq.com/doc/" in doc_url.lower():
                # 具体文档
                doc_match = re.search(r'/doc/([A-Za-z0-9]+)', doc_url)
                if doc_match:
                    analysis["document_id"] = doc_match.group(1)
                    analysis["url_type"] = "specific_document"
                    analysis["is_specific_document"] = True
                    analysis["recommended_methods"] = ["_try_menu_export", "_try_toolbar_export"]
                    analysis["adaptive_config"]["direct_export_available"] = True
                    
            elif "docs.qq.com/slide/" in doc_url.lower():
                # 幻灯片文档
                slide_match = re.search(r'/slide/([A-Za-z0-9]+)', doc_url)
                if slide_match:
                    analysis["document_id"] = slide_match.group(1)
                    analysis["url_type"] = "specific_slide"
                    analysis["is_specific_document"] = True
                    analysis["recommended_methods"] = ["_try_menu_export", "_try_toolbar_export"]
                    analysis["expected_challenges"].append("幻灯片导出格式可能受限")
                    
            elif "pad.qq.com" in doc_url.lower():
                # 智能表格或其他pad域名
                analysis["url_type"] = "pad_domain"
                analysis["is_specific_document"] = True
                analysis["recommended_methods"] = ["_try_menu_export", "_try_right_click_export"]
                analysis["adaptive_config"]["alternative_domain"] = True
                
            else:
                # 未知类型，使用全方位方法
                analysis["url_type"] = "unknown"
                analysis["recommended_methods"] = ["_try_menu_export", "_try_toolbar_export", "_try_keyboard_shortcut_export", "_try_right_click_export"]
                analysis["expected_challenges"].append("未知URL格式，使用全方位尝试")
                
            # 2. URL参数分析
            if "?tab=" in doc_url:
                analysis["adaptive_config"]["has_tab_parameter"] = True
                analysis["expected_challenges"].append("多标签页文档，需要确认当前标签")
                
            if "#" in doc_url:
                analysis["adaptive_config"]["has_anchor"] = True
                
            # 3. 特殊情况检测
            if "readonly" in doc_url.lower():
                analysis["expected_challenges"].append("只读文档，导出功能可能受限")
                analysis["adaptive_config"]["readonly_mode"] = True
                
            print(f"📊 URL分析完成:")
            print(f"   类型: {analysis['url_type']}")
            print(f"   文档ID: {analysis.get('document_id', 'N/A')}")
            print(f"   推荐方法: {len(analysis['recommended_methods'])}个")
            print(f"   预期挑战: {len(analysis['expected_challenges'])}个")
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ URL分析异常: {e}")
            # 返回安全的默认分析结果
            analysis["url_type"] = "fallback"
            analysis["recommended_methods"] = ["_try_menu_export", "_try_toolbar_export", "_try_keyboard_shortcut_export", "_try_right_click_export"]
            return analysis

    async def auto_export_document(self, doc_url, export_format="excel"):
        """
        阶段4增强：智能导出文档（统一4重备用机制）
        """
        print(f"🚀 开始智能文档导出: {doc_url}")
        
        try:
            # 阶段4新功能：智能URL分析
            url_analysis = self._analyze_document_url(doc_url)
            
            # 访问页面 - 根据URL类型调整策略
            print("📋 开始加载页面...")
            load_timeout = 45000 if url_analysis["url_type"] == "desktop_general" else 30000
            await self.page.goto(doc_url, wait_until='domcontentloaded', timeout=load_timeout)
            print("✅ DOM加载完成")
            
            # 智能等待策略
            base_wait = 8000
            if url_analysis["url_type"] == "desktop_general":
                base_wait = 12000  # 桌面页面需要更多时间加载文档列表
            elif url_analysis.get("adaptive_config", {}).get("has_tab_parameter"):
                base_wait = 10000  # 多标签页文档需要更多加载时间
                
            print(f"⏳ 智能等待策略: {base_wait}ms")
            await self.page.wait_for_timeout(base_wait)
            print("✅ 页面智能渲染完成")
            
            # 增强状态检测逻辑
            await self._enhanced_page_status_detection(url_analysis)
            
            # 等待页面完全渲染和所有元素可交互
            print("⚙️ 等待页面元素完全加载...")
            await self.page.wait_for_timeout(5000)
            
            # 网络状态检测 - 根据URL类型调整超时
            network_timeout = 15000 if url_analysis["url_type"] == "desktop_general" else 10000
            try:
                await self.page.wait_for_load_state('networkidle', timeout=network_timeout)
                print("🌐 网络请求完成")
            except:
                print("⚠️ 网络等待超时，继续...")
                
            # 确保交互元素准备就绪
            await self.page.wait_for_timeout(3000)
            
            # 阶段4核心：智能方法选择和执行
            success = await self._execute_smart_export_strategy(url_analysis, export_format)
            
            if not success:
                raise Exception("所有智能导出策略都失败了")
            
            # 等待下载完成
            print("📥 等待下载完成...")
            await self._wait_for_download(timeout=30)
            
            if self.downloaded_files:
                print(f"🎉 成功下载文件: {self.downloaded_files}")
                return self.downloaded_files
            else:
                raise Exception("未检测到下载的文件")
                
        except Exception as e:
            print(f"❌ 智能文档导出失败: {e}")
            return None
    
    async def _enhanced_page_status_detection(self, url_analysis):
        """
        阶段4增强：智能页面状态检测
        
        Args:
            url_analysis: URL分析结果
        """
        try:
            print("🔍 开始增强页面状态检测...")
            
            # 根据URL类型调整检测策略
            if url_analysis["url_type"] == "desktop_general":
                await self._detect_desktop_page_status()
            else:
                await self._detect_specific_document_status(url_analysis)
                
        except Exception as e:
            print(f"⚠️ 页面状态检测异常: {e}")
    
    async def _detect_desktop_page_status(self):
        """检测桌面页面状态"""
        print("📋 检测桌面页面状态...")
        
        # 检测文档列表是否加载完成
        document_list_selectors = [
            '[class*="doc-list"]',
            '[class*="file-list"]', 
            '[class*="document-item"]',
            '.desktop-content'
        ]
        
        list_found = False
        for selector in document_list_selectors:
            elements = await self.page.query_selector_all(selector)
            if elements:
                print(f"✅ 检测到文档列表: {selector} ({len(elements)}个元素)")
                list_found = True
                break
        
        if not list_found:
            print("⚠️ 未检测到明确的文档列表，但继续进行...")
    
    async def _detect_specific_document_status(self, url_analysis):
        """检测具体文档页面状态"""
        print(f"📄 检测具体文档状态 (类型: {url_analysis['url_type']})...")
        
        # 检查登录状态
        readonly_btn = await self.page.query_selector('.readonly-button')
        menu_btn = await self.page.query_selector('.titlebar-icon-more')
        has_edit_access = await self.page.query_selector('[class*="edit"]')
        
        current_url = self.page.url
        print(f"📊 页面状态检测结果:")
        print(f"   当前URL: {current_url[:100]}...")
        print(f"   只读按钮: {'存在' if readonly_btn else '不存在'}")
        print(f"   菜单按钮: {'存在' if menu_btn else '不存在'}")
        print(f"   编辑元素: {'存在' if has_edit_access else '不存在'}")
        
        # 根据URL分析结果调整状态判断
        if url_analysis.get("adaptive_config", {}).get("readonly_mode"):
            print("📖 只读模式文档，调整导出策略")
        
        if menu_btn:
            print("✅ 检测到导出菜单，用户已登录，继续导出流程...")
        elif readonly_btn:
            print("ℹ️ 文档为只读模式，但可能仍可导出")
        else:
            print("⚠️ 未检测到明确的登录/菜单元素，将尝试继续...")

    async def _execute_smart_export_strategy(self, url_analysis, export_format):
        """
        阶段4核心：智能导出策略执行
        
        Args:
            url_analysis: URL分析结果
            export_format: 导出格式
            
        Returns:
            bool: 是否成功
        """
        try:
            print(f"🎯 执行智能导出策略 (文档类型: {url_analysis['url_type']})")
            
            # 获取推荐的导出方法
            recommended_methods = url_analysis.get("recommended_methods", [])
            if not recommended_methods:
                print("⚠️ 没有推荐方法，使用默认顺序")
                recommended_methods = ["_try_menu_export", "_try_toolbar_export", "_try_keyboard_shortcut_export", "_try_right_click_export"]
            
            print(f"📋 推荐方法顺序: {recommended_methods}")
            
            # 智能重试策略
            max_attempts_per_method = 2 if url_analysis["url_type"] == "desktop_general" else 1
            
            for attempt in range(max_attempts_per_method):
                print(f"🔄 第{attempt + 1}轮尝试 (最多{max_attempts_per_method}轮)")
                
                for method_name in recommended_methods:
                    try:
                        print(f"⚙️ 尝试方法: {method_name}")
                        
                        # 获取方法对象
                        method = getattr(self, method_name)
                        
                        # 根据URL分析结果调整方法执行
                        method_config = self._get_method_adaptive_config(url_analysis, method_name)
                        
                        # 执行前置处理
                        if method_config.get("pre_processing_required"):
                            await self._handle_pre_processing(url_analysis, method_name)
                        
                        # 执行导出方法
                        if await method(export_format):
                            print(f"✅ 方法 {method_name} 执行成功!")
                            return True
                        else:
                            print(f"❌ 方法 {method_name} 执行失败")
                            
                        # 执行后置处理（失败时的恢复措施）
                        if method_config.get("post_processing_on_failure"):
                            await self._handle_post_processing_failure(url_analysis, method_name)
                            
                    except Exception as e:
                        print(f"❌ 方法 {method_name} 异常: {e}")
                        continue
                
                # 如果所有方法都失败了，在重试之前执行页面恢复
                if attempt < max_attempts_per_method - 1:
                    print("🔄 执行页面恢复后重试...")
                    await self._recovery_page_state(url_analysis)
                    await self.page.wait_for_timeout(3000)
            
            print("❌ 所有智能导出策略都失败了")
            return False
            
        except Exception as e:
            print(f"❌ 智能导出策略执行异常: {e}")
            return False
    
    def _get_method_adaptive_config(self, url_analysis, method_name):
        """获取方法的自适应配置"""
        config = {
            "pre_processing_required": False,
            "post_processing_on_failure": False,
            "timeout_adjustment": 1.0
        }
        
        # 根据URL类型和方法名称调整配置
        if url_analysis["url_type"] == "desktop_general":
            if method_name == "_try_right_click_export":
                config["pre_processing_required"] = True  # 需要先选择文档
            config["timeout_adjustment"] = 1.5
            
        elif url_analysis.get("adaptive_config", {}).get("has_tab_parameter"):
            config["timeout_adjustment"] = 1.2  # 多标签页需要更多时间
            
        return config
    
    async def _handle_pre_processing(self, url_analysis, method_name):
        """处理方法执行前的预处理"""
        try:
            if url_analysis["url_type"] == "desktop_general" and method_name == "_try_right_click_export":
                print("🎯 桌面页面右键导出预处理：尝试选择第一个文档")
                
                # 尝试找到并点击第一个文档
                document_selectors = [
                    '[class*="document-item"]:first-child',
                    '[class*="file-item"]:first-child',
                    '.doc-list-item:first-child'
                ]
                
                for selector in document_selectors:
                    element = await self.page.query_selector(selector)
                    if element:
                        print(f"✅ 找到文档元素: {selector}")
                        await element.click()
                        await self.page.wait_for_timeout(2000)
                        break
                        
        except Exception as e:
            print(f"⚠️ 预处理失败: {e}")
    
    async def _handle_post_processing_failure(self, url_analysis, method_name):
        """处理方法失败后的后置处理"""
        try:
            # 关闭可能打开的菜单或对话框
            escape_selectors = [
                'body',  # 点击页面空白处关闭菜单
            ]
            
            for selector in escape_selectors:
                try:
                    await self.page.keyboard.press('Escape')
                    await self.page.wait_for_timeout(500)
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️ 后置处理失败: {e}")
    
    async def _recovery_page_state(self, url_analysis):
        """页面状态恢复"""
        try:
            print("🔧 执行页面状态恢复...")
            
            # 按ESC键关闭任何打开的菜单或对话框
            await self.page.keyboard.press('Escape')
            await self.page.wait_for_timeout(1000)
            
            # 如果是桌面页面，尝试刷新页面
            if url_analysis["url_type"] == "desktop_general":
                print("🔄 桌面页面：执行轻量级刷新")
                # 轻量级刷新，不完全重新加载
                await self.page.keyboard.press('F5')
                await self.page.wait_for_timeout(5000)
            else:
                # 具体文档页面，只需要滚动到顶部
                print("📄 文档页面：滚动到顶部")
                await self.page.keyboard.press('Home')
                await self.page.wait_for_timeout(1000)
                
        except Exception as e:
            print(f"⚠️ 页面状态恢复失败: {e}")
    
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
    
    def export_document(self, url: str, cookies: str = None, format: str = 'csv', download_dir: str = None) -> dict:
        """
        统一接口包装器 - 兼容现有系统调用
        
        Args:
            url: 腾讯文档URL
            cookies: 登录Cookie字符串  
            format: 导出格式 ('csv', 'excel', 'xlsx')
            download_dir: 下载目录
            
        Returns:
            dict: {
                'success': bool,
                'file_path': str,
                'files': list,
                'error': str
            }
        """
        async def _async_export():
            """
            异步导出的内部实现
            """
            try:
                print(f"📥 统一下载接口启动: {url}")
                
                # 更新下载目录
                if download_dir:
                    self.download_dir = download_dir
                    os.makedirs(self.download_dir, exist_ok=True)
                
                # 启动浏览器
                await self.start_browser(headless=True)
                
                # 如果提供了Cookie，进行登录
                if cookies:
                    print("🍪 应用提供的Cookie...")
                    await self.login_with_cookies(cookies)
                
                # 执行自动导出（4重备用机制）
                print("🚀 启动4重备用导出机制...")
                result_files = await self.auto_export_document(url, format)
                
                if result_files and len(result_files) > 0:
                    first_file = result_files[0]
                    print(f"✅ 下载成功: {first_file}")
                    return {
                        'success': True,
                        'file_path': first_file,
                        'files': result_files,
                        'error': None,
                        'backup_methods_used': True,
                        'export_format': format,
                        'file_count': len(result_files)
                    }
                else:
                    error_msg = "所有4重备用导出方法都失败了"
                    print(f"❌ {error_msg}")
                    return {
                        'success': False,
                        'file_path': None,
                        'files': [],
                        'error': error_msg,
                        'backup_methods_used': True,
                        'methods_attempted': ['menu_export', 'toolbar_export', 'keyboard_shortcut', 'right_click_export']
                    }
                    
            except Exception as e:
                error_msg = f"统一接口导出异常: {e}"
                print(f"💥 {error_msg}")
                return {
                    'success': False,
                    'file_path': None,
                    'files': [],
                    'error': error_msg,
                    'backup_methods_used': False
                }
            finally:
                # 确保清理资源
                try:
                    await self.cleanup()
                except:
                    pass
        
        # 运行异步导出并返回结果
        try:
            # 在同步函数中运行异步代码
            import asyncio
            try:
                # 尝试获取当前事件循环
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，创建新的线程执行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _async_export())
                    result = future.result()
            except RuntimeError:
                # 如果没有运行的事件循环，直接运行
                result = asyncio.run(_async_export())
                
            print(f"🎯 统一接口返回结果: success={result.get('success')}, file={result.get('file_path')}")
            return result
            
        except Exception as e:
            error_msg = f"统一接口调用失败: {e}"
            print(f"🚨 {error_msg}")
            return {
                'success': False,
                'file_path': None,
                'files': [],
                'error': error_msg,
                'interface_error': True
            }
    
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
    parser.add_argument('--disable-version-management', action='store_true', help='禁用版本管理功能')
    
    args = parser.parse_args()
    
    exporter = TencentDocAutoExporter(
        download_dir=args.download_dir,
        enable_version_management=not args.disable_version_management
    )
    
    try:
        await exporter.start_browser(headless=not args.visible)
        
        if args.cookies:
            await exporter.login_with_cookies(args.cookies)
        
        result = await exporter.auto_export_document(args.url, args.format)
        
        if result:
            print(f"[成功] 自动导出完成，文件保存在: {result}")
            
            # 版本管理处理
            if exporter.enable_version_management and exporter.version_manager:
                print("正在进行版本管理处理...")
                
                for file_path in result:
                    # 从文件名提取表格名称
                    file_name = Path(file_path).stem
                    version_result = exporter.version_manager.add_new_version(file_path, file_name)
                    
                    if version_result["success"]:
                        print(f"✅ {version_result['message']}")
                        if version_result.get("archived_files"):
                            print(f"📁 已归档旧版本: {', '.join(version_result['archived_files'])}")
                        
                        # 准备对比文件
                        table_name = version_result["table_name"]
                        comparison_result = exporter.version_manager.prepare_comparison(table_name)
                        if comparison_result["success"]:
                            print(f"📊 对比文件已准备: {comparison_result['message']}")
                            print(f"📄 当前版本: {Path(comparison_result['current_file']).name}")
                            print(f"📄 对比版本: {Path(comparison_result['previous_file']).name}")
                        else:
                            print(f"⚠️  {comparison_result.get('message', '无法准备对比文件')}")
                    else:
                        action = version_result.get("action", "unknown")
                        if action == "duplicate_content":
                            print(f"ℹ️  文件内容未变化，与 {version_result.get('duplicate_file', '现有文件')} 相同")
                        else:
                            print(f"⚠️  版本管理处理失败: {version_result.get('error', version_result.get('message', '未知错误'))}")
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