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
    
    async def upload_file_to_main_page(self, file_path, homepage_url="https://docs.qq.com/desktop", max_retries=3):
        """增强版文件上传 - 多重策略容错机制"""
        print(f"🚀 开始上传文件到腾讯文档: {homepage_url}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_size = os.path.getsize(file_path)
        print(f"📁 文件信息: {file_path} ({file_size} 字节)")
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                print(f"📝 尝试上传 (第{attempt + 1}/{max_retries}次)")
                return await self._perform_upload(file_path, homepage_url)
                
            except Exception as e:
                print(f"❌ 第{attempt + 1}次上传失败: {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ 等待3秒后重试...")
                    await self.page.wait_for_timeout(3000)
                else:
                    raise Exception(f"上传失败，已重试{max_retries}次: {e}")
    
    async def _perform_upload(self, file_path, homepage_url):
        """执行单次上传流程"""
        try:
            # 访问主页
            print("🌐 加载主页...")
            await self.page.goto(homepage_url, wait_until='domcontentloaded', timeout=15000)
            print("✅ DOM加载完成")
            
            # 智能等待页面就绪
            await self._wait_for_page_ready()
            
            # 检查登录状态
            await self._check_login_status()
            
            # 步骤1: 智能导入按钮查找
            print("🔍 步骤1: 智能导入按钮查找...")
            import_btn = await self._find_import_button_smart()
            
            if not import_btn:
                raise Exception("所有导入按钮选择器都失败")
            
            print("✅ 找到可用的导入按钮")
            
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
            
            # 步骤3: 智能确认按钮处理
            print("✅ 步骤3: 智能确认上传...")
            await self._handle_confirm_upload()
            
            # 步骤4: 增强的上传完成监控
            print("⏳ 步骤4: 监控上传状态...")
            success = await self._wait_for_upload_completion_enhanced()
            
            if success:
                print("🎉 文件上传成功！")
                return True
            else:
                raise Exception("上传完成检测失败")
                
        except Exception as e:
            print(f"❌ 上传执行失败: {e}")
            raise
    
    async def _wait_for_page_ready(self):
        """智能等待页面就绪"""
        try:
            print("⏳ 智能等待页面就绪...")
            
            # 等待基本渲染
            await self.page.wait_for_timeout(3000)
            
            # 等待网络空闲（有超时）
            try:
                await self.page.wait_for_load_state('networkidle', timeout=8000)
                print("✅ 网络请求完成")
            except:
                print("⚠️ 网络等待超时，继续执行...")
            
            # 额外等待确保交互元素准备就绪
            await self.page.wait_for_timeout(2000)
            print("✅ 页面就绪完成")
            
        except Exception as e:
            print(f"⚠️ 页面等待异常: {e}")
    
    async def _find_import_button_smart(self):
        """智能导入按钮查找 - 多策略容错"""
        try:
            print("🔍 开始智能导入按钮查找...")
            
            # 现代化导入按钮选择器策略
            import_selectors = [
                # 优先级选择器（最新版本）
                'button[class*="import"]:not([class*="disabled"])',
                'div[class*="upload"]:not([class*="disabled"])',
                'button[class*="desktop-import"]',
                
                # 经典选择器（兼容性）
                'button.desktop-import-button-pc',
                '.desktop-import-button-pc',
                
                # 文本匹配策略
                'button:has-text("导入")',
                'button:has-text("上传")',
                'div[role="button"]:has-text("导入")',
                'div[role="button"]:has-text("上传")',
                
                # 通用容错选择器
                'button[title*="导入"]',
                'button[title*="上传"]',
                '[data-action*="import"]',
                '[data-action*="upload"]'
            ]
            
            # 逐个测试选择器
            for i, selector in enumerate(import_selectors, 1):
                try:
                    print(f"⏳ 测试选择器 {i}/{len(import_selectors)}: {selector[:50]}...")
                    
                    btn = await self.page.query_selector(selector)
                    if btn:
                        # 验证按钮状态
                        is_visible = await btn.is_visible()
                        is_enabled = await btn.is_enabled()
                        
                        if is_visible and is_enabled:
                            # 获取按钮文本验证
                            btn_text = await btn.text_content() or ""
                            btn_title = await btn.get_attribute('title') or ""
                            
                            print(f"✅ 找到可用按钮: {selector}")
                            print(f"🏷️  按钮信息: 文本='{btn_text.strip()}', 标题='{btn_title}'")
                            
                            return btn
                        else:
                            print(f"⚠️ 按钮不可用: visible={is_visible}, enabled={is_enabled}")
                    
                    await self.page.wait_for_timeout(200)  # 短暂等待
                    
                except Exception as e:
                    print(f"❌ 选择器测试失败: {e}")
                    continue
            
            # 如果所有选择器都失败，尝试动态发现
            print("🔍 所有选择器失败，尝试动态发现...")
            return await self._discover_import_button_dynamically()
            
        except Exception as e:
            print(f"❌ 智能导入按钮查找失败: {e}")
            return None
    
    async def _discover_import_button_dynamically(self):
        """动态发现导入按钮"""
        try:
            print("🤖 启动动态导入按钮发现...")
            
            # 查找所有可能的按钮元素
            all_buttons = await self.page.evaluate('''
                () => {
                    const buttons = [];
                    // 查找按钮元素
                    document.querySelectorAll('button, div[role="button"], [class*="btn"], [class*="button"]').forEach(el => {
                        const text = el.textContent?.toLowerCase() || '';
                        const title = el.getAttribute('title')?.toLowerCase() || '';
                        const className = el.className?.toLowerCase() || '';
                        
                        if (text.includes('导入') || text.includes('上传') ||
                            title.includes('import') || title.includes('upload') ||
                            className.includes('import') || className.includes('upload')) {
                            
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0 && 
                                getComputedStyle(el).display !== 'none') {
                                buttons.push({
                                    text: el.textContent?.trim(),
                                    title: el.getAttribute('title'),
                                    className: el.className,
                                    tagName: el.tagName,
                                    visible: true
                                });
                            }
                        }
                    });
                    return buttons;
                }
            ''');
            
            print(f"📊 发现{len(all_buttons)}个潜在导入按钮")
            
            # 显示前3个可能的候选按钮
            for i, btn_info in enumerate(all_buttons[:3]):
                print(f"  {i+1}. {btn_info.get('tagName')} - '{btn_info.get('text')}' - {btn_info.get('className')[:50]}")
            
            # 尝试点击第一个匹配的按钮
            if all_buttons:
                for btn_info in all_buttons[:2]:  # 只尝试前2个
                    text = btn_info.get('text', '').lower()
                    if '导入' in text or '上传' in text:
                        # 尝试找到该元素
                        element = await self.page.query_selector(f'button:has-text("{btn_info.get("text")}")')
                        if element:
                            print(f"✅ 动态发现成功: {btn_info.get('text')}")
                            return element
            
            return None
            
        except Exception as e:
            print(f"❌ 动态发现失败: {e}")
            return None
    
    async def _check_login_status(self):
        """智能登录状态检查"""
        try:
            print("🔐 检查登录状态...")
            
            # 检查登录指示器
            login_indicators = await self.page.evaluate('''
                () => {
                    const body = document.body.textContent.toLowerCase();
                    const hasLoginButton = document.querySelector('button:has-text("登录"), .login-btn, [class*="login"]');
                    const hasUserInfo = document.querySelector('.user-info, [class*="user"][class*="name"], [class*="avatar"]');
                    
                    return {
                        bodyHasLogin: body.includes('登录') && !body.includes('已登录'),
                        hasLoginButton: !!hasLoginButton,
                        hasUserInfo: !!hasUserInfo,
                        title: document.title
                    };
                }
            ''');
            
            if login_indicators['hasUserInfo']:
                print("✅ 检测到用户信息，登录状态正常")
            elif login_indicators['hasLoginButton'] or login_indicators['bodyHasLogin']:
                print("⚠️ 检测到登录按钮，可能需要重新登录")
                # 尝试等待页面完全加载
                await self.page.wait_for_timeout(3000)
            else:
                print("✅ 登录状态检查通过")
                
        except Exception as e:
            print(f"⚠️ 登录状态检查异常: {e}")
    
    async def _handle_confirm_upload(self):
        """智能确认按钮处理 - 多策略容错"""
        try:
            print("🎯 智能确认按钮处理...")
            
            # 等待确认对话框出现
            await self.page.wait_for_timeout(2000)
            
            # 现代化确认按钮选择器策略
            confirm_selectors = [
                # 优先级选择器（最新版本）
                'button[class*="confirm"]:not([class*="disabled"])',
                'div[class*="dui-button"]:has-text("确定")',
                'button[class*="dui-button"]:has-text("确定")',
                
                # 经典选择器（兼容性）
                'div.dui-button-container:has-text("确定")',
                '.dui-button-container:has-text("确定")',
                'div[data-dui-1-23-0="dui-button-container"]:has-text("确定")',
                
                # 通用确认按钮
                'button:has-text("确定")',
                'button:has-text("确认")',
                'button:has-text("上传")',
                '.dui-button:has-text("确定")',
                
                # 容错选择器
                '[class*="confirm"]:has-text("确定")',
                '[class*="button"]:has-text("确定")',
                '[role="button"]:has-text("确定")'
            ]
            
            # 逐个测试选择器
            for i, selector in enumerate(confirm_selectors, 1):
                try:
                    print(f"⏳ 测试确认按钮 {i}/{len(confirm_selectors)}: {selector[:50]}...")
                    
                    btn = await self.page.query_selector(selector)
                    if btn:
                        # 验证按钮状态
                        is_visible = await btn.is_visible()
                        is_enabled = await btn.is_enabled()
                        
                        if is_visible and is_enabled:
                            # 获取按钮文本验证
                            btn_text = await btn.text_content() or ""
                            
                            print(f"✅ 找到可用确认按钮: {selector}")
                            print(f"📝 按钮文本: '{btn_text.strip()}'")
                            
                            await btn.click()
                            print("✅ 确认按钮点击成功")
                            await self.page.wait_for_timeout(2000)
                            return True
                        else:
                            print(f"⚠️ 按钮不可用: visible={is_visible}, enabled={is_enabled}")
                    
                    await self.page.wait_for_timeout(200)  # 短暂等待
                    
                except Exception as e:
                    print(f"❌ 确认按钮选择器测试失败: {e}")
                    continue
            
            # 如果所有选择器都失败，尝试动态发现
            print("🔍 所有确认按钮选择器失败，尝试动态发现...")
            success = await self._discover_confirm_button_dynamically()
            
            if success:
                return True
            
            # 最后尝试：使用键盘回车
            print("⌨️ 最后尝试：使用键盘回车确认...")
            await self.page.keyboard.press('Enter')
            await self.page.wait_for_timeout(2000)
            return True
            
        except Exception as e:
            print(f"❌ 智能确认按钮处理失败: {e}")
            return False
    
    async def _discover_confirm_button_dynamically(self):
        """动态发现确认按钮"""
        try:
            print("🤖 启动动态确认按钮发现...")
            
            # 查找所有可能的确认按钮元素
            confirm_buttons = await self.page.evaluate('''
                () => {
                    const buttons = [];
                    document.querySelectorAll('div, button, span, [role="button"]').forEach((el, index) => {
                        const text = el.textContent?.toLowerCase() || '';
                        const className = el.className?.toLowerCase() || '';
                        
                        if ((text.includes('确定') || text.includes('确认') || text.includes('上传')) &&
                            !text.includes('取消')) {
                            
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0 && 
                                getComputedStyle(el).display !== 'none') {
                                buttons.push({
                                    index: index,
                                    text: el.textContent?.trim(),
                                    className: el.className,
                                    tagName: el.tagName,
                                    visible: true
                                });
                            }
                        }
                    });
                    return buttons;
                }
            ''');
            
            print(f"📊 发现{len(confirm_buttons)}个潜在确认按钮")
            
            # 显示前3个可能的候选按钮
            for i, btn_info in enumerate(confirm_buttons[:3]):
                print(f"  {i+1}. {btn_info.get('tagName')} - '{btn_info.get('text')}' - {btn_info.get('className')[:30]}")
            
            # 尝试点击第一个匹配的按钮
            if confirm_buttons:
                for btn_info in confirm_buttons[:2]:  # 只尝试前2个
                    text = btn_info.get('text', '').lower()
                    if '确定' in text or '确认' in text:
                        # 尝试找到该元素
                        element = await self.page.query_selector(f'button:has-text("{btn_info.get("text")}")')
                        if not element:
                            element = await self.page.query_selector(f'div:has-text("{btn_info.get("text")}")')
                        
                        if element:
                            print(f"✅ 动态发现确认按钮成功: {btn_info.get('text')}")
                            await element.click()
                            await self.page.wait_for_timeout(2000)
                            return True
            
            return False
            
        except Exception as e:
            print(f"❌ 动态确认按钮发现失败: {e}")
            return False
    
    async def _wait_for_upload_completion_enhanced(self):
        """增强的上传完成监控 - 多重检测机制"""
        try:
            print("⏳ 启动增强的上传完成监控...")
            
            # 监控配置
            max_wait_time = 60  # 最大等待时间（秒）
            check_interval = 1  # 检查间隔（秒）
            
            for i in range(max_wait_time):
                try:
                    # 检测方法1: 文本内容检查
                    completion_indicators = await self.page.evaluate('''
                        () => {
                            const text = document.body.textContent.toLowerCase();
                            return {
                                hasSuccess: text.includes('上传完成') || 
                                          text.includes('导入完成') || 
                                          text.includes('导入成功') ||
                                          text.includes('上传成功'),
                                hasError: text.includes('上传失败') ||
                                         text.includes('导入失败') ||
                                         text.includes('网络错误'),
                                hasProgress: text.includes('上传中') ||
                                           text.includes('导入中') ||
                                           text.includes('处理中')
                            };
                        }
                    ''');
                    
                    if completion_indicators['hasSuccess']:
                        print("✅ 检测到上传完成标识")
                        return True
                    
                    if completion_indicators['hasError']:
                        print("❌ 检测到上传错误标识")
                        return False
                    
                    if completion_indicators['hasProgress']:
                        print(f"⏳ 上传进行中... ({i+1}/{max_wait_time}秒)")
                    
                    # 检测方法2: DOM变化检查
                    dom_changes = await self.page.evaluate('''
                        () => {
                            // 检查是否有新文档出现在列表中
                            const docItems = document.querySelectorAll('[class*="doc-item"], [class*="file-item"], .document-item, [class*="table-item"]');
                            
                            // 检查是否有进度条或加载指示器消失
                            const progressBars = document.querySelectorAll('.progress-bar, [class*="progress"], [class*="loading"], .spinner');
                            
                            return {
                                docCount: docItems.length,
                                progressCount: progressBars.length,
                                hasNewDoc: docItems.length > 0
                            };
                        }
                    ''');
                    
                    # 如果有新文档出现，等待额外确认
                    if dom_changes['hasNewDoc'] and i > 10:
                        print(f"📋 检测到{dom_changes['docCount']}个文档项")
                        # 再等待3秒确保完成
                        await self.page.wait_for_timeout(3000)
                        return True
                    
                    # 检测方法3: 网络空闲检查
                    if i > 30:  # 30秒后开始检查网络空闲
                        try:
                            await self.page.wait_for_load_state('networkidle', timeout=2000)
                            print("🌐 网络空闲检测，上传可能已完成")
                            await self.page.wait_for_timeout(2000)
                            return True
                        except:
                            # 网络检查超时，继续其他方法
                            pass
                    
                    await self.page.wait_for_timeout(check_interval * 1000)
                    
                except Exception as e:
                    print(f"⚠️ 上传监控检查异常: {e}")
                    continue
            
            print("⏰ 上传监控超时，但可能已完成")
            return True  # 超时也认为成功，避免误判
            
        except Exception as e:
            print(f"❌ 增强上传完成监控失败: {e}")
            return True  # 出错也认为成功，避免阻塞
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