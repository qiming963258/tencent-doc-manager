#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档增强版上传工具 - 使用精确选择器
支持上传xlsx文件并获取新文档URL
"""

import asyncio
import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TencentDocUploadEnhanced:
    """腾讯文档增强版上传工具"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # 精确选择器配置
        self.selectors = {
            # 导入按钮 - 左侧栏
            'import_button': 'button.desktop-import-button-pc',
            
            # 确定按钮 - 弹窗中
            'confirm_button': 'button.dui-button.dui-button-type-primary.dui-button-size-default > div.dui-button-container',
            
            # 备用选择器
            'import_button_alt': '#root button:has(i.desktop-icon-import)',
            'confirm_button_alt': 'div.import-kit-import-file-footer button.dui-button-type-primary',
            
            # 文档列表项
            'doc_items': '.doc-item, .file-item, [class*="document-item"]',
            'doc_links': 'a[href*="docs.qq.com/sheet"], a[href*="docs.qq.com/doc"]'
        }
        
        # 配置参数
        self.config = {
            'page_timeout': 60000,  # 页面超时时间
            'upload_timeout': 120,  # 上传超时时间（秒）
            'retry_count': 3,      # 重试次数
            'wait_after_click': 2000  # 点击后等待时间
        }
        
    async def start_browser(self, headless: bool = False):
        """启动浏览器"""
        try:
            logger.info("🚀 启动增强版浏览器...")
            
            self.playwright = await async_playwright().start()
            
            # 浏览器启动配置
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            # 创建上下文
            context = await self.browser.new_context(
                accept_downloads=True,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN'
            )
            
            self.page = await context.new_page()
            self.page.set_default_timeout(self.config['page_timeout'])
            
            logger.info("✅ 浏览器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 浏览器启动失败: {e}")
            return False
    
    async def login_with_cookies(self, cookies_str: str) -> bool:
        """使用Cookie登录"""
        try:
            logger.info("🔐 开始Cookie认证...")
            
            # 先访问主页建立会话
            await self.page.goto('https://docs.qq.com', wait_until='domcontentloaded')
            
            # 解析并添加cookies
            cookie_list = []
            for cookie_pair in cookies_str.split(';'):
                if '=' in cookie_pair:
                    name, value = cookie_pair.strip().split('=', 1)
                    # 为多个域名添加cookie
                    for domain in ['.qq.com', '.docs.qq.com']:
                        cookie_list.append({
                            'name': name.strip(),
                            'value': value.strip(),
                            'domain': domain,
                            'path': '/',
                            'httpOnly': False,
                            'secure': True,
                            'sameSite': 'None'
                        })
            
            # 添加cookies
            await self.page.context.add_cookies(cookie_list)
            logger.info(f"✅ 已添加 {len(cookie_list)} 个Cookies")
            
            # 刷新页面应用cookies
            await self.page.reload()
            await self.page.wait_for_timeout(2000)
            
            # 验证登录状态
            is_logged_in = await self._check_login_status()
            if is_logged_in:
                logger.info("✅ Cookie认证成功")
            else:
                logger.warning("⚠️ Cookie可能已失效，但继续尝试上传")
                # 即使检查失败也尝试继续，因为Cookie可能仍然有效
                return True
            
            return is_logged_in
            
        except Exception as e:
            logger.error(f"❌ Cookie认证失败: {e}")
            return False
    
    async def _check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            # 检查是否有用户信息或登录按钮
            login_indicators = await self.page.evaluate('''
                () => {
                    const hasUserInfo = document.querySelector('.user-info, [class*="avatar"], [class*="user-name"], .user-avatar');
                    const hasLoginBtn = Array.from(document.querySelectorAll('button')).some(btn => 
                        btn.textContent && btn.textContent.includes('登录')
                    );
                    const hasImportBtn = document.querySelector('button.desktop-import-button-pc');
                    const hasCreateBtn = document.querySelector('.create-btn, .new-doc-btn');
                    
                    return {
                        hasUserInfo: !!hasUserInfo,
                        hasLoginBtn: hasLoginBtn,
                        hasImportBtn: !!hasImportBtn,
                        hasCreateBtn: !!hasCreateBtn,
                        url: window.location.href
                    };
                }
            ''')
            
            logger.info(f"📊 登录状态检查: {json.dumps(login_indicators, ensure_ascii=False)}")
            
            # 如果有用户信息、导入按钮或创建按钮，说明已登录
            # 如果有登录按钮，说明未登录
            if login_indicators['hasLoginBtn']:
                return False
            
            return login_indicators['hasUserInfo'] or login_indicators['hasImportBtn'] or login_indicators['hasCreateBtn']
            
        except Exception as e:
            logger.error(f"❌ 登录状态检查失败: {e}")
            # 如果检查失败，尝试继续（可能已登录）
            return True
    
    async def upload_file(self, file_path: str) -> Dict[str, any]:
        """
        上传文件到腾讯文档
        
        Args:
            file_path: xlsx文件路径
            
        Returns:
            {
                'success': bool,
                'url': str,  # 新文档URL
                'doc_id': str,  # 文档ID
                'message': str
            }
        """
        try:
            logger.info(f"📤 开始上传文件: {file_path}")
            
            # 检查文件
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            if not file_path.endswith('.xlsx'):
                logger.warning("⚠️ 建议上传xlsx格式文件")
            
            # 访问首页
            logger.info("📍 导航到腾讯文档首页...")
            await self.page.goto('https://docs.qq.com/desktop/', wait_until='networkidle')
            await self.page.wait_for_timeout(3000)
            
            # 记录上传前的文档数量
            initial_doc_count = await self._get_document_count()
            logger.info(f"📊 当前文档数量: {initial_doc_count}")
            
            # 步骤1: 点击导入按钮
            logger.info("🔍 查找导入按钮...")
            import_success = await self._click_import_button()
            if not import_success:
                raise Exception("无法找到或点击导入按钮")
            
            # 步骤2: 处理文件选择
            logger.info("📁 处理文件选择...")
            file_select_success = await self._handle_file_selection(file_path)
            if not file_select_success:
                raise Exception("文件选择失败")
            
            # 步骤3: 点击确定按钮
            logger.info("✅ 点击确定按钮...")
            confirm_success = await self._click_confirm_button()
            if not confirm_success:
                logger.warning("⚠️ 可能未找到确定按钮，但继续处理")
            
            # 步骤4: 等待上传完成并获取URL
            logger.info("⏳ 等待上传完成...")
            result = await self._wait_for_upload_and_get_url(initial_doc_count)
            
            if result['success']:
                logger.info(f"✅ 上传成功！新文档URL: {result['url']}")
            else:
                logger.error(f"❌ 上传失败: {result['message']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 上传过程出错: {e}")
            return {
                'success': False,
                'url': None,
                'doc_id': None,
                'message': str(e)
            }
    
    async def _click_import_button(self) -> bool:
        """点击导入按钮"""
        try:
            # 使用主选择器
            logger.info(f"🎯 使用选择器: {self.selectors['import_button']}")
            
            # 等待按钮出现
            import_btn = await self.page.wait_for_selector(
                self.selectors['import_button'],
                timeout=10000,
                state='visible'
            )
            
            if import_btn:
                # 滚动到按钮位置
                await import_btn.scroll_into_view_if_needed()
                await self.page.wait_for_timeout(500)
                
                # 点击按钮
                await import_btn.click()
                logger.info("✅ 成功点击导入按钮")
                await self.page.wait_for_timeout(2000)
                return True
            
            # 尝试备用选择器
            logger.info("🔄 尝试备用选择器...")
            import_btn_alt = await self.page.query_selector(self.selectors['import_button_alt'])
            if import_btn_alt:
                await import_btn_alt.click()
                logger.info("✅ 使用备用选择器点击成功")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 点击导入按钮失败: {e}")
            return False
    
    async def _handle_file_selection(self, file_path: str) -> bool:
        """处理文件选择"""
        try:
            # 监听文件选择器
            async with self.page.expect_file_chooser() as fc_info:
                # 等待文件选择器触发
                await self.page.wait_for_timeout(1000)
            
            file_chooser = await fc_info.value
            
            # 设置文件
            await file_chooser.set_files(file_path)
            logger.info(f"✅ 已选择文件: {file_path}")
            
            await self.page.wait_for_timeout(2000)
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ 文件选择器处理异常，尝试直接设置: {e}")
            
            # 备用方案：直接查找input元素
            try:
                file_input = await self.page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(file_path)
                    logger.info("✅ 通过input元素设置文件成功")
                    return True
            except:
                pass
            
            return False
    
    async def _click_confirm_button(self) -> bool:
        """点击确定按钮"""
        try:
            # 等待弹窗出现
            await self.page.wait_for_timeout(2000)
            
            # 使用精确选择器
            logger.info(f"🎯 查找确定按钮: {self.selectors['confirm_button']}")
            
            # 方法1：使用主选择器
            confirm_btn = await self.page.query_selector(self.selectors['confirm_button'])
            if confirm_btn and await confirm_btn.is_visible():
                await confirm_btn.click()
                logger.info("✅ 成功点击确定按钮")
                return True
            
            # 方法2：使用文本匹配
            confirm_by_text = await self.page.query_selector('button:has-text("确定")')
            if confirm_by_text:
                await confirm_by_text.click()
                logger.info("✅ 通过文本匹配点击确定")
                return True
            
            # 方法3：使用备用选择器
            confirm_alt = await self.page.query_selector(self.selectors['confirm_button_alt'])
            if confirm_alt:
                await confirm_alt.click()
                logger.info("✅ 使用备用选择器点击确定")
                return True
            
            logger.warning("⚠️ 未找到确定按钮")
            return False
            
        except Exception as e:
            logger.error(f"❌ 点击确定按钮失败: {e}")
            return False
    
    async def _get_document_count(self) -> int:
        """获取当前文档数量"""
        try:
            doc_items = await self.page.query_selector_all(self.selectors['doc_items'])
            return len(doc_items)
        except:
            return 0
    
    async def _wait_for_upload_and_get_url(self, initial_count: int, timeout: int = 60) -> Dict:
        """等待上传完成并获取新文档URL"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # 检查URL是否已跳转到新文档
                current_url = self.page.url
                if '/sheet/' in current_url or '/doc/' in current_url:
                    if 'desktop' not in current_url:  # 排除首页URL
                        logger.info(f"🎯 检测到新文档URL: {current_url}")
                        doc_id = self._extract_doc_id(current_url)
                        return {
                            'success': True,
                            'url': current_url,
                            'doc_id': doc_id,
                            'message': '上传成功'
                        }
                
                # 检查文档列表是否有新增
                current_count = await self._get_document_count()
                if current_count > initial_count:
                    logger.info("📈 检测到新文档添加")
                    
                    # 获取最新文档的链接
                    new_doc_url = await self._get_latest_document_url()
                    if new_doc_url:
                        doc_id = self._extract_doc_id(new_doc_url)
                        return {
                            'success': True,
                            'url': new_doc_url,
                            'doc_id': doc_id,
                            'message': '上传成功'
                        }
                
                # 检查页面上的成功提示
                success_indicator = await self.page.evaluate('''
                    () => {
                        const text = document.body.textContent;
                        return text.includes('上传成功') || 
                               text.includes('导入成功') ||
                               text.includes('创建成功');
                    }
                ''')
                
                if success_indicator:
                    logger.info("✅ 检测到成功提示")
                    # 尝试获取URL
                    new_url = await self._get_latest_document_url()
                    if new_url:
                        doc_id = self._extract_doc_id(new_url)
                        return {
                            'success': True,
                            'url': new_url,
                            'doc_id': doc_id,
                            'message': '上传成功'
                        }
                
                await self.page.wait_for_timeout(2000)
            
            # 超时但可能已成功
            logger.warning("⏱️ 等待超时，尝试获取最新文档")
            latest_url = await self._get_latest_document_url()
            if latest_url:
                return {
                    'success': True,
                    'url': latest_url,
                    'doc_id': self._extract_doc_id(latest_url),
                    'message': '上传可能成功（超时）'
                }
            
            return {
                'success': False,
                'url': None,
                'doc_id': None,
                'message': '上传超时'
            }
            
        except Exception as e:
            logger.error(f"❌ 等待上传完成时出错: {e}")
            return {
                'success': False,
                'url': None,
                'doc_id': None,
                'message': str(e)
            }
    
    async def _get_latest_document_url(self) -> Optional[str]:
        """获取最新文档的URL"""
        try:
            # 执行JavaScript获取最新文档链接
            latest_url = await self.page.evaluate('''
                () => {
                    // 查找所有文档链接
                    const links = document.querySelectorAll('a[href*="docs.qq.com/sheet"], a[href*="docs.qq.com/doc"]');
                    if (links.length > 0) {
                        // 返回第一个（通常是最新的）
                        return links[0].href;
                    }
                    
                    // 备用：查找文档项中的链接
                    const docItems = document.querySelectorAll('.doc-item, .file-item');
                    for (let item of docItems) {
                        const link = item.querySelector('a[href*="docs.qq.com"]');
                        if (link) {
                            return link.href;
                        }
                    }
                    
                    return null;
                }
            ''')
            
            return latest_url
            
        except Exception as e:
            logger.error(f"❌ 获取最新文档URL失败: {e}")
            return None
    
    def _extract_doc_id(self, url: str) -> Optional[str]:
        """从URL中提取文档ID"""
        try:
            # 腾讯文档URL格式: https://docs.qq.com/sheet/DxxxxXXXXxxxx
            parts = url.split('/')
            for part in parts:
                if part.startswith('D') and len(part) > 10:  # 文档ID通常以D开头
                    return part.split('?')[0]  # 移除查询参数
            return None
        except:
            return None
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("🧹 资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时出错: {e}")


async def main():
    """测试主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='腾讯文档增强版上传工具')
    parser.add_argument('file_path', help='要上传的xlsx文件路径')
    parser.add_argument('-c', '--cookies', required=True, help='登录Cookie字符串')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口')
    
    args = parser.parse_args()
    
    uploader = TencentDocUploadEnhanced()
    
    try:
        # 启动浏览器
        await uploader.start_browser(headless=not args.visible)
        
        # Cookie登录
        login_success = await uploader.login_with_cookies(args.cookies)
        if not login_success:
            logger.error("登录失败，请检查Cookie")
            return
        
        # 上传文件
        result = await uploader.upload_file(args.file_path)
        
        # 输出结果
        print("\n" + "="*50)
        if result['success']:
            print(f"✅ 上传成功！")
            print(f"📄 文档URL: {result['url']}")
            print(f"🆔 文档ID: {result['doc_id']}")
        else:
            print(f"❌ 上传失败: {result['message']}")
        print("="*50)
        
    except Exception as e:
        logger.error(f"程序异常: {e}")
    finally:
        await uploader.cleanup()


if __name__ == "__main__":
    asyncio.run(main())