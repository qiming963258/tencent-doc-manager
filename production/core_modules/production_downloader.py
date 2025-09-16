#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产级腾讯文档下载器 - 集成Cookie管理器
实现自动Cookie管理、失败恢复、下载完整性验证
"""

import sys
import os
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

import asyncio
import time
import argparse
from pathlib import Path
from playwright.async_api import async_playwright
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from cookie_manager import get_cookie_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionTencentDownloader:
    """生产级腾讯文档下载器"""
    
    def __init__(self, download_dir=None):
        """初始化下载器"""
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        self.browser = None
        self.page = None
        self.downloaded_files = []
        
        # 集成Cookie管理器
        self.cookie_manager = get_cookie_manager()
        
        # 下载配置
        self.max_retries = 3
        self.retry_delay = 5
        self.download_timeout = 60
        self.page_load_timeout = 30
        
        # 元素选择器（更新版本，兼容腾讯文档UI变更）
        self.selectors = {
            'menu_button': [
                '.titlebar-icon.titlebar-icon-more',
                'button[class*="menu"]',
                '[aria-label*="菜单"]',
                '.toolbar-more-btn',
                'button[title*="更多"]'
            ],
            'export_submenu': [
                'li.dui-menu-item.dui-menu-submenu.mainmenu-submenu-exportAs',
                'li[class*="export"]',
                '[aria-label*="导出"]',
                'li:has-text("导出为")',
                '.menu-item-export'
            ],
            'csv_option': [
                'li.dui-menu-item.mainmenu-item-export-csv',
                'li:has-text("CSV")',
                '[data-export="csv"]',
                '.export-csv',
                'button:has-text("CSV")'
            ],
            'excel_option': [
                'li.dui-menu-item.mainmenu-item-export-local',
                'li:has-text("Excel")',
                '[data-export="excel"]',
                '.export-excel',
                'button:has-text("Excel")'
            ]
        }
        
    async def start_browser(self, headless=True):
        """启动浏览器"""
        try:
            logger.info("🚀 启动生产级浏览器...")
            
            # 创建下载目录
            os.makedirs(self.download_dir, exist_ok=True)
            
            self.playwright = await async_playwright().start()
            
            # 浏览器配置
            browser_config = {
                'headless': headless,
                'downloads_path': self.download_dir,
                'args': [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions'
                ]
            }
            
            self.browser = await self.playwright.chromium.launch(**browser_config)
            
            # 页面上下文配置
            context_config = {
                'accept_downloads': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'viewport': {'width': 1920, 'height': 1080},
                'locale': 'zh-CN'
            }
            
            context = await self.browser.new_context(**context_config)
            self.page = await context.new_page()
            
            # 监听下载事件
            self.page.on("download", self._handle_download)
            
            logger.info("✅ 浏览器启动成功")
            
        except Exception as e:
            logger.error(f"❌ 浏览器启动失败: {e}")
            raise
    
    async def _handle_download(self, download):
        """处理下载事件"""
        try:
            filename = download.suggested_filename
            filepath = os.path.join(self.download_dir, filename)
            
            logger.info(f"📥 开始下载文件: {filename}")
            
            # 下载文件
            await download.save_as(filepath)
            
            # 验证下载完整性
            if await self._verify_download(filepath):
                self.downloaded_files.append(filepath)
                logger.info(f"✅ 文件下载验证成功: {filename}")
            else:
                logger.error(f"❌ 文件下载验证失败: {filename}")
                if os.path.exists(filepath):
                    os.remove(filepath)
            
        except Exception as e:
            logger.error(f"❌ 下载处理失败: {e}")
    
    async def _verify_download(self, filepath: str) -> bool:
        """验证下载文件完整性"""
        try:
            if not os.path.exists(filepath):
                return False
            
            # 检查文件大小
            file_size = os.path.getsize(filepath)
            if file_size < 100:  # 小于100字节可能是错误文件
                logger.warning(f"⚠️ 下载文件过小: {file_size} bytes")
                return False
            
            # 检查文件扩展名
            ext = Path(filepath).suffix.lower()
            if ext not in ['.csv', '.xlsx', '.xls']:
                logger.warning(f"⚠️ 下载文件格式异常: {ext}")
                return False
            
            # 简单内容验证
            try:
                with open(filepath, 'rb') as f:
                    first_bytes = f.read(1024)
                    if len(first_bytes) > 0:
                        return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"文件验证失败: {e}")
            return False
    
    async def login_with_cookies(self, cookies_string: str = None) -> bool:
        """使用Cookie管理器进行登录"""
        try:
            # 如果没有提供Cookie，从管理器获取
            if not cookies_string:
                logger.info("📋 从Cookie管理器获取有效Cookie...")
                cookies_string = await self.cookie_manager.get_valid_cookies()
            
            if not cookies_string:
                logger.error("❌ 未获取到有效Cookie，无法登录")
                return False
            
            # 解析Cookie
            cookie_list = []
            domains = ['docs.qq.com', '.docs.qq.com', 'qq.com', '.qq.com']
            
            for cookie_str in cookies_string.split(';'):
                if '=' in cookie_str:
                    name, value = cookie_str.strip().split('=', 1)
                    
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
            
            # 添加Cookie
            await self.page.context.add_cookies(cookie_list)
            logger.info(f"✅ 已设置 {len(cookie_list)} 个Cookie（多域名支持）")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Cookie登录失败: {e}")
            return False
    
    async def download_document(self, doc_url: str, format_type: str = 'csv') -> Tuple[bool, str, List[str]]:
        """下载文档（生产级实现）"""
        try:
            logger.info(f"📁 开始下载文档: {doc_url} (格式: {format_type})")
            
            # 重试机制
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"🔄 下载尝试 {attempt + 1}/{self.max_retries}")
                    
                    success, message = await self._attempt_download(doc_url, format_type)
                    if success:
                        return True, message, self.downloaded_files
                    else:
                        logger.warning(f"⚠️ 第{attempt + 1}次尝试失败: {message}")
                        
                        if attempt < self.max_retries - 1:
                            logger.info(f"⏳ 等待 {self.retry_delay} 秒后重试...")
                            await asyncio.sleep(self.retry_delay)
                        
                except Exception as e:
                    logger.error(f"❌ 第{attempt + 1}次尝试异常: {e}")
                    
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
            
            # 所有尝试都失败
            return False, f"经过{self.max_retries}次重试后仍然失败", []
            
        except Exception as e:
            logger.error(f"❌ 下载文档过程失败: {e}")
            return False, str(e), []
    
    async def _attempt_download(self, doc_url: str, format_type: str) -> Tuple[bool, str]:
        """单次下载尝试"""
        try:
            # 清空下载文件列表
            self.downloaded_files = []
            
            # 访问文档页面
            logger.info("🌐 加载文档页面...")
            response = await self.page.goto(doc_url, timeout=self.page_load_timeout * 1000)
            
            if response.status != 200:
                return False, f"页面加载失败，HTTP状态: {response.status}"
            
            # 等待页面完全加载
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            await self.page.wait_for_timeout(3000)
            
            # 检查登录状态
            login_check = await self._check_login_status()
            if not login_check:
                return False, "用户未登录或Cookie已失效"
            
            # 执行导出操作
            export_success = await self._perform_export(format_type)
            if not export_success:
                return False, "导出操作失败"
            
            # 等待下载完成
            download_success = await self._wait_for_download()
            if not download_success:
                return False, "等待下载超时或下载失败"
            
            return True, f"下载成功，文件数量: {len(self.downloaded_files)}"
            
        except Exception as e:
            logger.error(f"单次下载尝试失败: {e}")
            return False, str(e)
    
    async def _check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            # 检查页面内容是否包含登录相关元素
            login_indicators = await self.page.evaluate('''() => {
                const text = document.body.textContent.toLowerCase();
                const hasLogin = text.includes('登录') && !text.includes('已登录');
                const hasUserInfo = document.querySelector('.user-info, [class*="user"][class*="name"], [class*="avatar"]');
                
                return {
                    hasLogin: hasLogin,
                    hasUserInfo: !!hasUserInfo,
                    bodyText: text.substring(0, 500)
                };
            }''')
            
            if login_indicators['hasUserInfo']:
                logger.info("✅ 检测到用户信息，登录状态正常")
                return True
            elif login_indicators['hasLogin']:
                logger.warning("⚠️ 检测到登录提示，可能需要重新登录")
                
                # 尝试刷新Cookie
                logger.info("🔄 尝试刷新Cookie...")
                fresh_cookies = await self.cookie_manager.get_valid_cookies()
                if fresh_cookies:
                    await self.login_with_cookies(fresh_cookies)
                    await self.page.reload()
                    await self.page.wait_for_timeout(3000)
                    
                    # 重新检查
                    return await self._check_login_status()
                else:
                    return False
            else:
                logger.info("ℹ️ 未检测到明确的登录状态指示，假设已登录")
                return True
            
        except Exception as e:
            logger.error(f"登录状态检查失败: {e}")
            return False
    
    async def _perform_export(self, format_type: str) -> bool:
        """执行导出操作"""
        try:
            logger.info(f"📋 开始执行 {format_type.upper()} 导出操作...")
            
            # 1. 寻找并点击菜单按钮
            menu_clicked = await self._click_element_with_selectors(
                self.selectors['menu_button'], 
                "菜单按钮"
            )
            if not menu_clicked:
                return False
            
            await self.page.wait_for_timeout(2000)
            
            # 2. 点击导出子菜单
            export_clicked = await self._click_element_with_selectors(
                self.selectors['export_submenu'], 
                "导出为子菜单"
            )
            if not export_clicked:
                return False
            
            await self.page.wait_for_timeout(1000)
            
            # 3. 点击具体格式选项
            format_selectors = self.selectors['csv_option'] if format_type == 'csv' else self.selectors['excel_option']
            format_clicked = await self._click_element_with_selectors(
                format_selectors, 
                f"{format_type.upper()}导出选项"
            )
            if not format_clicked:
                return False
            
            logger.info("✅ 导出操作执行成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 导出操作失败: {e}")
            return False
    
    async def _click_element_with_selectors(self, selectors: List[str], element_name: str) -> bool:
        """使用多个选择器尝试点击元素"""
        try:
            for i, selector in enumerate(selectors):
                try:
                    logger.debug(f"尝试选择器 {i+1}/{len(selectors)}: {selector}")
                    
                    element = await self.page.query_selector(selector)
                    if element:
                        # 检查元素可见性和可点击性
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        
                        if is_visible and is_enabled:
                            await element.click()
                            logger.info(f"✅ 成功点击{element_name}: {selector}")
                            return True
                        else:
                            logger.debug(f"元素不可用: visible={is_visible}, enabled={is_enabled}")
                    
                    await self.page.wait_for_timeout(500)
                    
                except Exception as selector_error:
                    logger.debug(f"选择器失败: {selector_error}")
                    continue
            
            logger.error(f"❌ 所有选择器都无法找到{element_name}")
            return False
            
        except Exception as e:
            logger.error(f"❌ 点击{element_name}失败: {e}")
            return False
    
    async def _wait_for_download(self) -> bool:
        """等待下载完成"""
        try:
            logger.info("⏳ 等待下载完成...")
            
            start_time = time.time()
            while time.time() - start_time < self.download_timeout:
                if self.downloaded_files:
                    logger.info(f"✅ 下载完成，文件数量: {len(self.downloaded_files)}")
                    return True
                
                await asyncio.sleep(1)
            
            logger.error("❌ 等待下载超时")
            return False
            
        except Exception as e:
            logger.error(f"❌ 等待下载失败: {e}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("✅ 资源清理完成")
        except Exception as e:
            logger.error(f"❌ 资源清理失败: {e}")
    
    async def get_download_summary(self) -> Dict:
        """获取下载摘要"""
        try:
            summary = {
                'total_files': len(self.downloaded_files),
                'files': [],
                'total_size': 0,
                'download_time': datetime.now().isoformat()
            }
            
            for filepath in self.downloaded_files:
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    summary['files'].append({
                        'name': os.path.basename(filepath),
                        'path': filepath,
                        'size': file_size,
                        'size_mb': round(file_size / 1024 / 1024, 2)
                    })
                    summary['total_size'] += file_size
            
            summary['total_size_mb'] = round(summary['total_size'] / 1024 / 1024, 2)
            return summary
            
        except Exception as e:
            logger.error(f"获取下载摘要失败: {e}")
            return {'error': str(e)}


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生产级腾讯文档下载器')
    parser.add_argument('url', help='文档URL')
    parser.add_argument('-f', '--format', choices=['csv', 'excel'], default='csv', help='导出格式')
    parser.add_argument('-d', '--download-dir', help='下载目录')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口')
    parser.add_argument('-c', '--cookies', help='手动提供Cookie')
    
    args = parser.parse_args()
    
    downloader = ProductionTencentDownloader(args.download_dir)
    
    try:
        # 启动浏览器
        await downloader.start_browser(headless=not args.visible)
        
        # 登录
        login_success = await downloader.login_with_cookies(args.cookies)
        if not login_success:
            logger.error("❌ 登录失败，无法继续")
            return
        
        # 下载文档
        success, message, files = await downloader.download_document(args.url, args.format)
        
        if success:
            print(f"\n✅ 下载成功: {message}")
            summary = await downloader.get_download_summary()
            print(f"📊 下载摘要: {summary}")
        else:
            print(f"\n❌ 下载失败: {message}")
            
    except Exception as e:
        logger.error(f"❌ 程序执行失败: {e}")
    finally:
        await downloader.cleanup()


if __name__ == "__main__":
    asyncio.run(main())