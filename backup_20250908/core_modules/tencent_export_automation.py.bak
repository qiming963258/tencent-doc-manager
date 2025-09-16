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
    
    def __init__(self, download_dir=None):
        """初始化导出工具 - 强制使用规范命名"""
        self.browser = None
        self.page = None
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        
        # 始终启用版本管理器 - 不再作为可选项
        from csv_version_manager import CSVVersionManager
        self.version_manager = CSVVersionManager()
        
    async def start_browser(self, headless=False):
        """启动浏览器 - 2025增强版反检测配置"""
        self.playwright = await async_playwright().start()
        
        # 创建下载目录
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 🆕 2025增强：30+反检测参数
        launch_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-size=1920,1080',
            '--start-maximized',
            '--disable-extensions',
            '--disable-default-apps',
            '--disable-features=IsolateOrigins,site-per-process',
            '--enable-features=NetworkService,NetworkServiceInProcess',
            '--disable-features=VizDisplayCompositor',
            '--disable-features=TranslateUI',
            '--disable-features=BlinkGenPropertyTrees',
            '--disable-ipc-flooding-protection',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-features=OptimizationGuideModelDownloading,OptimizationHintsFetching,OptimizationTargetPrediction,OptimizationHints',
            '--disable-backgrounding-occluded-windows',
            '--disable-features=BackForwardCache',
            '--disable-features=GlobalMediaControls,GlobalMediaControlsModernUI',
            '--disable-features=InterestFeedContentSuggestions',
            '--disable-component-extensions-with-background-pages',
            '--disable-features=CalculateNativeWinOcclusion',
            '--disable-features=OptimizationGuideModelDownloading',
            '--metrics-recording-only',
            '--no-first-run',
            '--mute-audio',
            '--no-default-browser-check',
            '--no-pings'
        ]
        
        # 启动浏览器，设置下载目录和反检测参数
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            downloads_path=self.download_dir,
            args=launch_args,
            ignore_default_args=['--enable-automation'],
            chromium_sandbox=False
        )
        
        # 创建页面上下文，设置下载行为和增强配置
        context = await self.browser.new_context(
            accept_downloads=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            permissions=['clipboard-read', 'clipboard-write', 'notifications'],
            extra_http_headers={
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            ignore_https_errors=True,
            java_script_enabled=True,
            bypass_csp=True,
            device_scale_factor=1,
            has_touch=False,
            is_mobile=False
        )
        
        self.page = await context.new_page()
        
        # 监听下载事件
        self.downloaded_files = []
        self.page.on("download", self._handle_download)
    
    async def _handle_download(self, download):
        """处理下载事件 - 强制使用规范文件命名和目录结构"""
        filename = download.suggested_filename
        
        # 强制使用规范文件命名 - 删除所有降级逻辑
        from file_version_manager import FileVersionManager
        from datetime import datetime
        file_manager = FileVersionManager()
        
        # 确保有URL信息
        if not hasattr(self, 'current_url'):
            self.current_url = ""  # 防御性编程
        
        # 自动判断版本类型（根据当前时间和下载类型）
        def determine_version_type():
            now = datetime.now()
            weekday = now.weekday()  # 0=周一, 1=周二...
            hour = now.hour
            
            # 严格规则：只有周二12点的自动下载才能是baseline
            # 所有手动测试、临时下载都归类到midweek
            if weekday == 1 and hour >= 12 and hour <= 13:
                # 即使是周二，手动测试也应该是midweek
                # 只有自动化任务才能创建baseline
                return 'midweek'  # 手动测试一律使用midweek
            # 周六晚上7点 → weekend（周末版）
            elif weekday == 5 and hour >= 19 and hour <= 20:
                return 'weekend'
            else:
                # 所有其他时间的手动下载都归类到midweek
                return 'midweek'  # 默认使用midweek作为临时/测试文件
        
        version_type = determine_version_type()
        print(f"🔍 自动判断版本类型: {version_type} (当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        
        # 先使用临时文件名下载（防止并行冲突）
        temp_filename = file_manager.get_temp_filename(self.current_url)
        temp_filepath = os.path.join(self.download_dir, temp_filename)
        
        print(f"📥 使用临时文件名下载: {temp_filename}")
        await download.save_as(str(temp_filepath))
        
        # 下载完成后，生成规范文件名并移动到规范目录
        standard_filename = file_manager.get_standard_filename(
            self.current_url, 
            filename, 
            version_type=version_type  # 使用自动判断的版本类型
        )
        
        # 获取规范保存目录
        save_dir = file_manager.get_save_directory(version_type=version_type)
        final_filepath = save_dir / standard_filename
        
        # 移动文件到规范位置
        import shutil
        shutil.move(str(temp_filepath), str(final_filepath))
        
        print(f"🎯 规范文件命名: {standard_filename}")
        print(f"📁 规范保存目录: {save_dir}")
        
        filepath = final_filepath
        
        self.downloaded_files.append(str(filepath))
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
            # 设置当前URL供_handle_download使用
            self.current_url = doc_url
            
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
                recommended_methods = [
                    "_try_menu_export", 
                    "_try_toolbar_export", 
                    "_try_keyboard_shortcut_export", 
                    "_try_right_click_export",
                    "_try_keyboard_combination_export",
                    "_try_js_injection_export",  # 🆕 2025新增方法
                    "_try_api_download"
                ]
            
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
        """方法1: 通过菜单导出 - 使用2025年最新腾讯文档UI选择器"""
        try:
            # 步骤1: 智能寻找三横线菜单按钮
            print("步骤1: 智能寻找菜单按钮...")
            menu_selectors = [
                # 🆕 2025年1月最新腾讯文档UI选择器（优先级从高到低）
                '[data-testid="more-menu-button"]',  # 最精确的测试ID
                '[data-testid*="more"]',             # React组件测试ID
                '[data-cy="more-menu"]',             # Cypress测试选择器
                'button[aria-label="更多操作"]',     # 精确的aria标签
                'button[aria-label*="更多"]',        # 模糊的aria标签
                '[role="button"][title*="更多"]',   # 角色+标题组合
                '.dui-more-dropdown-trigger',        # DUI组件库选择器
                '.dui-dropdown-trigger',              # DUI下拉触发器
                '[class*="more-dropdown"]',          # 更多下拉类名
                '[class*="more-menu"]',              # 更多菜单类名
                '[class*="dropdown-trigger"]',       # 下拉菜单触发器
                'button[title="更多"]',              # 精确标题
                'button[title*="更多"]',             # 模糊标题
                '.header-more-btn',                   # 头部更多按钮
                '.toolbar-more-action',               # 工具栏更多操作
                '.doc-toolbar [class*="more"]',      # 文档工具栏
                '.header-toolbar [class*="more"]',   # 头部工具栏
                '.toolbar-action [class*="more"]',   # 工具栏操作
                'button[class*="icon-more"]',        # 图标更多按钮
                'div[class*="icon-more"]',           # DIV图标更多
                '.menu-trigger-button',               # 菜单触发按钮
                '.menu-trigger',                      # 菜单触发器
                '[class*="three-dots"]',             # 三点菜单
                '[class*="ellipsis-menu"]',          # 省略号菜单
                '[class*="overflow-menu"]',          # 溢出菜单
                'svg[class*="more"]',                # SVG更多图标
                'i[class*="more"]',                  # 图标字体更多
                
                # 2024-2025兼容选择器
                '.desktop-icon-more-menu',
                '.desktop-icon-more',
                '.titlebar-icon.titlebar-icon-more',
                'div.titlebar-icon-more',
                '.titlebar-icon-more',
                
                # 通用后备选择器
                'button[class*="more"][class*="menu"]',
                '[aria-label*="更多选项"]',
                '[aria-label*="菜单"]',
                '[title*="菜单"]',
                '[class*="more"]'
            ]
            
            menu_btn = None
            print(f"正在测试 {len(menu_selectors)} 个菜单选择器...")
            
            for i, selector in enumerate(menu_selectors, 1):
                try:
                    menu_btn = await self.page.query_selector(selector)
                    if menu_btn:
                        print(f"[{i}] 找到菜单按钮: {selector}")
                        
                        # 增强状态检查
                        is_visible = await menu_btn.is_visible()
                        is_enabled = await menu_btn.is_enabled()
                        bbox = await menu_btn.bounding_box() if menu_btn else None
                        
                        print(f"    状态: 可见={is_visible}, 可点击={is_enabled}, 有边界={bbox is not None}")
                        
                        if is_visible and bbox:  # 确保元素真正可交互
                            try:
                                # 滚动到视图中并hover激活
                                await menu_btn.scroll_into_view_if_needed()
                                await self.page.wait_for_timeout(1000)
                                await menu_btn.hover()
                                await self.page.wait_for_timeout(800)
                                print(f"    ✅ 成功激活菜单按钮: {selector}")
                                break
                            except Exception as e:
                                print(f"    ⚠️ 激活失败但继续使用: {e}")
                                break
                        else:
                            print(f"    ❌ 菜单按钮不可用")
                            menu_btn = None
                except Exception as e:
                    print(f"[{i}] ❌ 选择器测试失败: {selector} - {e}")
                    continue
            
            if menu_btn:
                print("找到可用的三横线菜单按钮，正在点击...")
                
                # 滚动到元素可见位置
                await menu_btn.scroll_into_view_if_needed()
                await self.page.wait_for_timeout(1000)
                
                # 🆕 强制点击策略
                try:
                    await menu_btn.click(force=True)  # 强制点击
                    await self.page.wait_for_timeout(2000)
                    print("✅ 强制点击成功")
                except Exception as click_error:
                    print(f"强制点击失败: {click_error}")
                    # 🆕 JavaScript备用点击
                    try:
                        await self.page.evaluate('(element) => element.click()', menu_btn)
                        await self.page.wait_for_timeout(2000)
                        print("✅ JavaScript点击成功")
                    except Exception as js_error:
                        print(f"JavaScript点击失败: {js_error}")
                        return False
                
                # 步骤2: 智能寻找导出选项
                print("步骤2: 智能寻找导出选项...")
                export_as_selectors = [
                    # 🆕 2025年最新UI选择器（优先级高）
                    '[data-testid*="export"]',
                    '[data-testid*="download"]', 
                    '.menu-item[title*="导出"]',
                    '.menu-item[title*="下载"]',
                    '.dropdown-item:has-text("导出")',
                    '.dropdown-item:has-text("下载")',
                    '.context-menu-item:has-text("导出")',
                    '.context-menu-item:has-text("下载")',
                    
                    # 通用语义化选择器
                    '[role="menuitem"][title*="导出"]',
                    '[role="menuitem"][title*="下载"]',
                    '[role="menuitem"]:has-text("导出")',
                    '[role="menuitem"]:has-text("下载")',
                    '[aria-label*="导出"]',
                    '[aria-label*="下载"]',
                    
                    # 文本内容匹配（最通用）
                    'li:has-text("导出")',
                    'li:has-text("下载")',
                    'div:has-text("导出")',
                    'div:has-text("下载")',
                    'button:has-text("导出")',
                    'button:has-text("下载")',
                    'span:has-text("导出")',
                    'span:has-text("下载")',
                    
                    # 英文界面支持
                    'li:has-text("Export")',
                    'li:has-text("Download")',
                    '[role="menuitem"]:has-text("Export")',
                    '[role="menuitem"]:has-text("Download")',
                    
                    # 兼容旧版本UI
                    'li.dui-menu-item.dui-menu-submenu.mainmenu-submenu-exportAs',
                    '.mainmenu-submenu-exportAs',
                    'li[role="menuitem"]:has-text("导出为")',
                    'text=导出为',
                    'text=导出',
                    'text=下载'
                ]
                
                export_as_btn = None
                print(f"测试 {len(export_as_selectors)} 个导出选择器...")
                
                # 等待菜单完全展开
                await self.page.wait_for_timeout(3000)
                
                for i, selector in enumerate(export_as_selectors, 1):
                    try:
                        export_as_btn = await self.page.query_selector(selector)
                        if export_as_btn:
                            is_visible = await export_as_btn.is_visible()
                            is_enabled = await export_as_btn.is_enabled()
                            bbox = await export_as_btn.bounding_box() if export_as_btn else None
                            
                            print(f"[{i}] 找到导出选项: {selector}")
                            print(f"    状态: 可见={is_visible}, 可点击={is_enabled}, 有边界={bbox is not None}")
                            
                            if is_visible and bbox:  # 确保元素可交互
                                # 获取元素文本验证
                                try:
                                    text = await export_as_btn.inner_text()
                                    print(f"    文本: '{text.strip()}'")
                                    if any(keyword in text for keyword in ['导出', '下载', 'Export', 'Download']):
                                        print(f"    ✅ 验证通过，选择此选项")
                                        break
                                except:
                                    # 即使获取文本失败，如果其他条件满足也继续
                                    print(f"    ✅ 基于选择器匹配，选择此选项")
                                    break
                            else:
                                print(f"    ❌ 选项不可用")
                                export_as_btn = None
                    except Exception as e:
                        print(f"[{i}] ❌ 选择器测试失败: {e}")
                        continue
                
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
            '.desktop-toolbar button:has-text("导出")', # 🆕 新桌面UI工具栏
            '.desktop-toolbar button:has-text("下载")',
            '.desktop-header button:has-text("导出")',  # 🆕 新桌面UI头部
            '.desktop-header button:has-text("下载")',
            '.toolbar button:has-text("导出")',        # 原有选择器
            '.toolbar button:has-text("下载")',
            '.header button:has-text("导出")',
            '.header button:has-text("下载")',
            'button[class*="export"]',
            'button[class*="download"]',
            'button[aria-label*="导出"]',              # 🆕 语义化选择器
            'button[aria-label*="下载"]'
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
                
                # 不再使用URL哈希作为属性（已改用临时文件机制）
                
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
                
                # 记录下载前的文件列表
                import glob
                from pathlib import Path
                csv_dir = Path('/root/projects/tencent-doc-manager/csv_versions')
                before_files = set(csv_dir.glob('**/*.csv'))
                
                # 执行下载
                result_files = await self.auto_export_document(url, format)
                
                # 扫描新增的文件（智能解决方案，避开线程状态问题）
                after_files = set(csv_dir.glob('**/*.csv'))
                new_files = after_files - before_files
                
                # 如果原方法返回空但实际有新文件，使用新文件
                if not result_files and new_files:
                    result_files = [str(f) for f in sorted(new_files, key=lambda x: x.stat().st_mtime, reverse=True)]
                    print(f"🔧 通过文件系统扫描找到新文件: {result_files}")
                
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
                    future = executor.submit(asyncio.run, _async_export)  # 传递函数引用，不是调用结果
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
    
    async def _try_api_download(self, export_format):
        """方法5: API直接下载 - 终极备用方案"""
        try:
            print("🔍 尝试API直接下载...")
            
            # 获取当前页面URL和文档ID
            current_url = self.page.url
            print(f"当前URL: {current_url}")
            
            # 提取文档ID
            import re
            doc_id_match = re.search(r'/(?:sheet|doc|slide)/([A-Za-z0-9]+)', current_url)
            if not doc_id_match:
                print("❌ 无法提取文档ID")
                return False
            
            doc_id = doc_id_match.group(1)
            print(f"文档ID: {doc_id}")
            
            # 尝试通过JavaScript获取下载链接
            try:
                download_info = await self.page.evaluate("""
                    () => {
                        // 尝试查找可能的下载相关API调用
                        const apis = [];
                        
                        // 检查网络请求
                        if (window.performance && window.performance.getEntriesByType) {
                            const entries = window.performance.getEntriesByType('resource');
                            for (const entry of entries) {
                                if (entry.name.includes('export') || entry.name.includes('download')) {
                                    apis.push(entry.name);
                                }
                            }
                        }
                        
                        // 检查全局变量
                        const globalVars = {};
                        for (const key in window) {
                            if (typeof window[key] === 'object' && window[key] !== null) {
                                if (key.toLowerCase().includes('doc') || 
                                    key.toLowerCase().includes('export') ||
                                    key.toLowerCase().includes('api')) {
                                    try {
                                        globalVars[key] = Object.keys(window[key]).slice(0, 5);
                                    } catch(e) {}
                                }
                            }
                        }
                        
                        return {
                            apis: apis,
                            globalVars: globalVars,
                            location: window.location.href,
                            title: document.title
                        };
                    }
                """)
                
                if download_info['apis']:
                    print(f"🔍 发现可能的API: {download_info['apis'][:3]}")
                    
            except Exception as e:
                print(f"⚠️ JavaScript信息获取失败: {e}")
            
            # 尝试直接构造下载链接
            possible_export_urls = [
                f"https://docs.qq.com/dop-api/opendoc/export?docId={doc_id}&format=csv",
                f"https://docs.qq.com/dop-api/opendoc/export?padId={doc_id}&format=csv",
                f"https://docs.qq.com/cgi-bin/doc_export?docid={doc_id}&format=csv",
                f"https://docs.qq.com/sheet/{doc_id}/export?format=csv"
            ]
            
            for url in possible_export_urls:
                try:
                    print(f"尝试直接访问: {url[:80]}...")
                    response = await self.page.goto(url, timeout=10000)
                    
                    if response and response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'csv' in content_type.lower() or 'excel' in content_type.lower():
                            print(f"✅ 可能的下载链接: {url}")
                            # 等待下载完成
                            await self.page.wait_for_timeout(5000)
                            return True
                            
                except Exception as e:
                    print(f"❌ API访问失败: {str(e)[:50]}")
                    continue
            
            print("❌ 所有API下载尝试都失败")
            return False
            
        except Exception as e:
            print(f"❌ API下载方法异常: {e}")
            return False
    
    async def _try_keyboard_combination_export(self, export_format):
        """方法6: 键盘组合键导出 - 高级备用方案"""
        try:
            print("🎹 尝试高级键盘组合键导出...")
            
            # 2025年更多的导出快捷键组合
            key_combinations = [
                'Control+Shift+E',  # 导出
                'Control+Shift+S',  # 另存为  
                'Control+Alt+E',    # 替代导出
                'Control+E',        # 简单导出
                'Control+S',        # 保存
                'F12',              # 另存为
                'Alt+F, E',         # Alt+File, Export
                'Control+Shift+D',  # 下载
            ]
            
            for combination in key_combinations:
                try:
                    print(f"🎹 尝试组合键: {combination}")
                    
                    if ', ' in combination:
                        # 处理组合按键 (如 Alt+F, E)
                        keys = combination.split(', ')
                        for key in keys:
                            await self.page.keyboard.press(key)
                            await self.page.wait_for_timeout(500)
                    else:
                        # 单一组合键
                        await self.page.keyboard.press(combination)
                    
                    await self.page.wait_for_timeout(3000)
                    
                    # 检查是否弹出对话框或菜单
                    dialog_appeared = await self._check_export_dialog()
                    
                    if dialog_appeared:
                        print(f"✅ {combination} 成功触发导出对话框")
                        
                        if await self._select_export_format(export_format):
                            return True
                        else:
                            print("⚠️ 导出格式选择失败")
                    else:
                        print(f"❌ {combination} 未触发对话框")
                        
                        # 检查是否直接开始下载
                        await self.page.wait_for_timeout(2000)
                        if len(self.downloaded_files) > 0:
                            print(f"✅ {combination} 直接触发了下载")
                            return True
                        
                except Exception as e:
                    print(f"❌ {combination} 执行失败: {e}")
                    continue
            
            print("❌ 所有键盘组合都失败")
            return False
            
        except Exception as e:
            print(f"❌ 键盘组合导出方法异常: {e}")
            return False

    async def _try_js_injection_export(self, export_format):
        """方法7: JavaScript注入导出 - 2025新增"""
        try:
            print("🚀 尝试JavaScript注入导出方法...")
            
            # 注入增强的导出函数
            export_result = await self.page.evaluate(f"""
                async () => {{
                    console.log('开始注入导出函数...');
                    
                    // 方法1: 查找并触发React组件的导出方法
                    const findReactComponent = (dom) => {{
                        const key = Object.keys(dom).find(key => key.startsWith('__reactInternalInstance') || key.startsWith('__reactFiber'));
                        return dom[key];
                    }};
                    
                    // 查找所有可能的导出按钮
                    const exportButtons = document.querySelectorAll(
                        '[data-testid*="export"], [data-testid*="download"], ' +
                        '[class*="export"], [class*="download"], ' +
                        'button:contains("导出"), button:contains("下载")'
                    );
                    
                    for (const button of exportButtons) {{
                        const fiber = findReactComponent(button);
                        if (fiber && fiber.memoizedProps && fiber.memoizedProps.onClick) {{
                            console.log('找到React导出按钮，触发点击');
                            fiber.memoizedProps.onClick();
                            return true;
                        }}
                    }}
                    
                    // 方法2: 直接调用全局导出函数
                    if (window.exportDocument) {{
                        console.log('调用全局exportDocument函数');
                        window.exportDocument('{export_format}');
                        return true;
                    }}
                    
                    // 方法3: 触发自定义导出事件
                    const exportEvent = new CustomEvent('export-document', {{
                        detail: {{ format: '{export_format}' }}
                    }});
                    document.dispatchEvent(exportEvent);
                    
                    // 方法4: 模拟完整的用户交互流程
                    const moreBtn = document.querySelector('[data-testid*="more"], [class*="more-menu"]');
                    if (moreBtn) {{
                        // 创建并派发鼠标事件
                        const mouseOverEvent = new MouseEvent('mouseover', {{ bubbles: true }});
                        const clickEvent = new MouseEvent('click', {{ bubbles: true }});
                        
                        moreBtn.dispatchEvent(mouseOverEvent);
                        await new Promise(r => setTimeout(r, 500));
                        moreBtn.dispatchEvent(clickEvent);
                        await new Promise(r => setTimeout(r, 1000));
                        
                        // 查找导出选项
                        const exportOption = document.querySelector('[role="menuitem"]:contains("导出")');
                        if (exportOption) {{
                            exportOption.dispatchEvent(clickEvent);
                            return true;
                        }}
                    }}
                    
                    // 方法5: 通过URL历史记录查找导出API
                    const entries = performance.getEntriesByType('resource');
                    for (const entry of entries) {{
                        if (entry.name.includes('export') || entry.name.includes('download')) {{
                            console.log('找到导出API:', entry.name);
                            // 构造新的导出请求
                            fetch(entry.name, {{
                                credentials: 'include',
                                headers: {{
                                    'X-Export-Format': '{export_format}'
                                }}
                            }});
                            return true;
                        }}
                    }}
                    
                    return false;
                }}
            """)
            
            if export_result:
                print("✅ JavaScript注入成功触发导出")
                await self.page.wait_for_timeout(3000)
                
                # 检查是否有下载
                if self.downloaded_files:
                    return True
                    
                # 等待可能的对话框
                if await self._check_export_dialog():
                    if await self._select_export_format(export_format):
                        return True
            
            return False
            
        except Exception as e:
            print(f"❌ JavaScript注入导出方法异常: {e}")
            return False
    
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
    
    exporter = TencentDocAutoExporter(
        download_dir=args.download_dir
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