#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档生产级上传模块 v2
修复：精确获取新上传文档的链接
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TencentDocProductionUploaderV2:
    """
    腾讯文档生产级上传器 v2
    改进：更精确的文档链接提取
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.initial_doc_links = set()  # 记录初始文档链接
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
        
    async def start(self) -> bool:
        """启动浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--start-maximized'
                ]
            )
            
            self.context = await self.browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN'
            )
            
            self.page = await self.context.new_page()
            self.page.set_default_timeout(30000)
            
            logger.info("✅ 浏览器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 浏览器启动失败: {e}")
            return False
    
    def parse_cookie_string(self, cookie_string: str) -> list:
        """解析Cookie字符串"""
        cookies = []
        
        for cookie_pair in cookie_string.split('; '):
            if '=' in cookie_pair:
                name, value = cookie_pair.strip().split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.docs.qq.com',
                    'path': '/'
                })
        
        return cookies
    
    async def login_with_cookies(self, cookie_string: str) -> bool:
        """使用Cookie登录腾讯文档"""
        try:
            logger.info("🔐 开始Cookie登录...")
            
            cookies = self.parse_cookie_string(cookie_string)
            await self.context.add_cookies(cookies)
            logger.info(f"✅ 已添加 {len(cookies)} 个Cookies")
            
            await self.page.goto(
                'https://docs.qq.com/desktop/',
                wait_until='domcontentloaded',
                timeout=30000
            )
            
            await self.page.wait_for_timeout(5000)
            
            # 记录初始页面上的文档链接
            await self.record_initial_doc_links()
            
            is_logged_in = await self.verify_login_status()
            
            if is_logged_in:
                logger.info("✅ 登录成功！")
                return True
            else:
                logger.warning("⚠️ 登录失败，可能Cookie已过期")
                return False
                
        except Exception as e:
            logger.error(f"❌ 登录异常: {e}")
            return False
    
    async def record_initial_doc_links(self):
        """记录页面初始的文档链接"""
        try:
            initial_links = await self.page.query_selector_all('a[href*="/sheet/"], a[href*="/doc/"]')
            for link in initial_links:
                href = await link.get_attribute('href')
                if href:
                    self.initial_doc_links.add(href)
            logger.info(f"📝 记录了 {len(self.initial_doc_links)} 个初始文档链接")
        except Exception as e:
            logger.warning(f"记录初始链接失败: {e}")
    
    async def verify_login_status(self) -> bool:
        """验证登录状态"""
        try:
            login_btn = await self.page.query_selector('button:has-text("登录")')
            has_login_btn = login_btn is not None
            
            import_btn = await self.page.query_selector('button.desktop-import-button-pc')
            has_import_btn = import_btn is not None
            
            user_info = await self.page.query_selector('[class*="avatar"], [class*="user"]')
            has_user_info = user_info is not None
            
            logger.info(f"🔍 状态: 登录按钮={has_login_btn}, 导入按钮={has_import_btn}, 用户信息={has_user_info}")
            
            return not has_login_btn and (has_import_btn or has_user_info)
            
        except Exception as e:
            logger.error(f"❌ 状态验证失败: {e}")
            return False
    
    async def upload_file(self, file_path: str) -> Dict[str, Any]:
        """上传文件到腾讯文档"""
        result = {
            'success': False,
            'url': None,
            'message': '',
            'doc_name': None
        }
        
        try:
            file_path = Path(file_path).resolve()
            if not file_path.exists():
                result['message'] = f"文件不存在: {file_path}"
                return result
            
            logger.info(f"📤 开始上传: {file_path.name}")
            
            # 点击导入按钮
            import_btn = await self.click_import_button()
            if not import_btn:
                result['message'] = "未找到导入按钮"
                return result
            
            # 处理文件选择
            await self.handle_file_selection(str(file_path))
            
            # 确认上传
            await self.confirm_upload_dialog()
            
            # 等待上传完成并获取URL
            success, url = await self.wait_for_upload_complete_v2(file_path.name)
            
            if success:
                result['success'] = True
                result['url'] = url if url else "https://docs.qq.com/desktop/"
                result['message'] = "上传成功"
                result['doc_name'] = file_path.stem
                logger.info(f"✅ 上传成功: {result['url']}")
                
                if url == self.page.url and '/desktop/' in url:
                    logger.info("📝 上传成功但未跳转，文档已添加到文档列表")
                    result['message'] = "上传成功，请在文档列表查看"
            else:
                result['message'] = "上传可能成功但未能获取文档链接，请在文档列表查看"
                logger.warning("⚠️ 未能确认上传状态")
                
        except Exception as e:
            result['message'] = f"上传异常: {str(e)}"
            logger.error(f"❌ 上传异常: {e}")
            
        return result
    
    async def click_import_button(self) -> bool:
        """点击导入按钮"""
        import_selectors = [
            'button.desktop-import-button-pc',
            'nav button:has(i.desktop-icon-import)',
            'button:has-text("导入")',
        ]
        
        for selector in import_selectors:
            try:
                btn = await self.page.wait_for_selector(selector, timeout=3000)
                if btn:
                    await btn.click()
                    logger.info(f"✅ 点击导入按钮: {selector}")
                    return True
            except:
                continue
                
        logger.error("❌ 未找到导入按钮")
        return False
    
    async def handle_file_selection(self, file_path: str):
        """处理文件选择"""
        await self.page.wait_for_timeout(1000)
        
        file_inputs = await self.page.query_selector_all('input[type="file"]')
        
        if file_inputs:
            await file_inputs[-1].set_input_files(file_path)
            logger.info(f"✅ 通过input选择文件: {file_path}")
        else:
            logger.info("使用filechooser选择文件")
            async with self.page.expect_file_chooser() as fc_info:
                await self.click_import_button()
            
            file_chooser = await fc_info.value
            await file_chooser.set_files(file_path)
            logger.info(f"✅ 通过filechooser选择文件: {file_path}")
    
    async def confirm_upload_dialog(self):
        """确认上传对话框"""
        try:
            await self.page.wait_for_timeout(2000)
            
            confirm_selectors = [
                'button.dui-button-type-primary:has-text("确定")',
                '.import-kit-import-file-footer button.dui-button-type-primary',
                'button.dui-button-type-primary .dui-button-container:has-text("确定")'
            ]
            
            for selector in confirm_selectors:
                try:
                    btn = await self.page.wait_for_selector(selector, timeout=2000)
                    if btn:
                        await btn.click()
                        logger.info("✅ 点击确定按钮")
                        return
                except:
                    continue
            
            await self.page.keyboard.press('Enter')
            logger.info("✅ 使用Enter键确认")
            
        except Exception as e:
            logger.warning(f"⚠️ 确认对话框处理: {e}")
    
    async def wait_for_upload_complete_v2(self, filename: str, timeout: int = 60) -> tuple:
        """
        等待上传完成 v2 - 更精确的链接检测
        
        Args:
            filename: 上传的文件名
            timeout: 超时时间（秒）
            
        Returns:
            tuple: (是否成功, 文档URL)
        """
        logger.info("⏳ 等待上传完成...")
        
        for i in range(timeout // 5):
            await self.page.wait_for_timeout(5000)
            
            # 方法1: 检查URL变化
            current_url = self.page.url
            if '/sheet/' in current_url or '/doc/' in current_url or '/slide/' in current_url:
                logger.info(f"✅ URL已跳转: {current_url}")
                return True, current_url
            
            # 方法2: 检测导入对话框是否关闭
            import_dialog = await self.page.query_selector('.import-kit-import-file')
            if not import_dialog and i > 2:
                logger.info("✅ 导入对话框已关闭")
                
                # 获取所有文档链接
                all_doc_links = await self.page.query_selector_all('a[href*="/sheet/"], a[href*="/doc/"]')
                
                # 查找新增的链接
                new_links = []
                for link in all_doc_links:
                    href = await link.get_attribute('href')
                    if href and href not in self.initial_doc_links:
                        # 检查链接文本是否包含文件名
                        link_text = await link.text_content()
                        if link_text:
                            logger.info(f"  发现新链接: {link_text} -> {href}")
                            # 如果链接文本包含上传的文件名（去掉扩展名）
                            if filename.rsplit('.', 1)[0] in link_text:
                                doc_url = f"https://docs.qq.com{href}" if href.startswith('/') else href
                                logger.info(f"✅ 找到匹配的文档链接: {doc_url}")
                                return True, doc_url
                        new_links.append(href)
                
                # 如果有新链接但没有名称匹配，返回最新的
                if new_links:
                    latest_link = new_links[-1]
                    doc_url = f"https://docs.qq.com{latest_link}" if latest_link.startswith('/') else latest_link
                    logger.info(f"✅ 找到新文档链接（可能不匹配名称）: {doc_url}")
                    return True, doc_url
                
                # 方法3：尝试查找包含"刚刚"或"秒前"的时间标记
                time_indicators = await self.page.query_selector_all('span:has-text("刚刚"), span:has-text("秒前")')
                if time_indicators:
                    for indicator in time_indicators:
                        # 查找最近的链接元素
                        parent = await indicator.evaluate_handle('(el) => el.closest("a") || el.parentElement.querySelector("a")')
                        if parent:
                            href = await parent.get_property('href')
                            if href:
                                doc_url = await href.json_value()
                                logger.info(f"✅ 通过时间标记找到文档: {doc_url}")
                                return True, doc_url
                
                # 如果没有找到新链接，但对话框已关闭，认为上传成功
                return True, current_url
            
            # 方法4: 检查成功提示
            success_msgs = await self.page.query_selector_all('.dui-message-success, [class*="success"]')
            if success_msgs:
                for msg in success_msgs:
                    text = await msg.text_content()
                    if text and ('成功' in text or '完成' in text or 'success' in text.lower()):
                        logger.info(f"✅ 检测到成功提示: {text}")
                        # 再次尝试获取新链接
                        await self.page.wait_for_timeout(2000)
                        all_links = await self.page.query_selector_all('a[href*="/sheet/"], a[href*="/doc/"]')
                        for link in reversed(all_links):  # 从后往前找
                            href = await link.get_attribute('href')
                            if href and href not in self.initial_doc_links:
                                doc_url = f"https://docs.qq.com{href}" if href.startswith('/') else href
                                return True, doc_url
                        return True, current_url
            
            # 方法5: 检查错误提示
            error_msgs = await self.page.query_selector_all('.dui-message-error, [class*="error"]')
            if error_msgs:
                for msg in error_msgs:
                    text = await msg.text_content()
                    if text and ('失败' in text or '错误' in text or 'error' in text.lower()):
                        logger.error(f"❌ 检测到错误提示: {text}")
                        return False, None
            
            if i % 3 == 0:
                logger.info(f"⏳ 已等待 {(i+1)*5} 秒...")
        
        logger.warning("⚠️ 上传超时，但可能已成功")
        return False, None
    
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("🔚 资源已清理")


# ============= 便捷函数 =============

async def quick_upload_v2(cookie_string: str, file_path: str, headless: bool = True) -> Dict[str, Any]:
    """
    快速上传文件 v2
    
    Args:
        cookie_string: Cookie字符串
        file_path: 文件路径
        headless: 是否无头模式
        
    Returns:
        dict: 上传结果
    """
    async with TencentDocProductionUploaderV2(headless=headless) as uploader:
        # 登录
        login_success = await uploader.login_with_cookies(cookie_string)
        if not login_success:
            return {
                'success': False,
                'message': '登录失败，请检查Cookie'
            }
        
        # 上传文件
        result = await uploader.upload_file(file_path)
        return result


def sync_upload_v2(cookie_string: str, file_path: str, headless: bool = True) -> Dict[str, Any]:
    """
    同步版本的上传函数 v2（供Flask等同步框架使用）
    
    Args:
        cookie_string: Cookie字符串
        file_path: 文件路径
        headless: 是否无头模式
        
    Returns:
        dict: 上传结果
    """
    return asyncio.run(quick_upload_v2(cookie_string, file_path, headless))


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python tencent_doc_upload_production_v2.py <文件路径>")
        sys.exit(1)
    
    # 读取配置
    config_path = Path('/root/projects/tencent-doc-manager/config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            cookie = config.get('cookie', '')
    else:
        print("❌ 配置文件不存在")
        sys.exit(1)
    
    # 执行上传
    file_to_upload = sys.argv[1]
    result = sync_upload_v2(cookie, file_to_upload, headless=False)
    
    # 显示结果
    print(json.dumps(result, ensure_ascii=False, indent=2))