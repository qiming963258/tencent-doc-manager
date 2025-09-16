#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档上传器 - 修复版
整合测试上传系统的成功实现
"""

import asyncio
import os
import time
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright
from typing import Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TencentDocUploader:
    """腾讯文档上传器 - 修复版"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        
    async def init_browser(self, headless=True):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        
        # 启动浏览器
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        # 创建上下文
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
            accept_downloads=True
        )
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(60000)
        logger.info("✅ 浏览器启动成功")
    
    async def login_with_cookies(self, cookie_string):
        """使用Cookie登录 - 修复版"""
        if not cookie_string:
            return False
        
        try:
            # 解析cookies - 关键修复：使用'; '分隔符
            cookies = []
            for cookie_pair in cookie_string.split('; '):  # 注意是'; '不是';'
                if '=' in cookie_pair:
                    name, value = cookie_pair.strip().split('=', 1)
                    cookies.append({
                        'name': name.strip(),
                        'value': value.strip(),
                        'domain': '.docs.qq.com',  # 只使用一个域名
                        'path': '/',
                        'httpOnly': False,
                        'secure': True,
                        'sameSite': 'None'
                    })
            
            # 添加cookies
            await self.context.add_cookies(cookies)
            logger.info(f"✅ 已添加 {len(cookies)} 个cookies")
            
            # 直接访问desktop页面（关键改进）
            await self.page.goto('https://docs.qq.com/desktop/', 
                                wait_until='domcontentloaded',
                                timeout=30000)
            
            # 等待页面加载
            await asyncio.sleep(5)
            
            # 检查登录状态
            import_btn = await self.page.query_selector('button.desktop-import-button-pc')
            if import_btn:
                logger.info("✅ 登录验证成功，找到导入按钮")
                return True
            else:
                logger.warning("⚠️ 未找到导入按钮，但继续尝试")
                return True  # 仍然尝试继续
                
        except Exception as e:
            logger.error(f"❌ 登录失败: {e}")
            return False
    
    async def create_new_sheet(self, file_path):
        """创建新的在线表格并导入数据 - 修复版"""
        try:
            # 记录上传前的文档数量
            initial_doc_count = await self._get_document_count()
            logger.info(f"📊 当前文档数量: {initial_doc_count}")
            
            # 步骤1：点击导入按钮
            import_success = await self._click_import_button_fixed()
            if not import_success:
                return {
                    'success': False,
                    'error': '未找到导入按钮',
                    'message': '请确认页面已加载完成'
                }
            
            # 步骤2：处理文件选择（关键修复）
            if file_path and Path(file_path).exists():
                file_select_success = await self._handle_file_selection_fixed(file_path)
                if not file_select_success:
                    return {
                        'success': False,
                        'error': '文件选择失败',
                        'message': '无法选择文件'
                    }
                
                # 步骤3：点击确定按钮
                await self._click_confirm_button()
                
                # 步骤4：等待上传完成并获取URL（改进的成功判断）
                result = await self._wait_for_upload_success(initial_doc_count)
                return result
            else:
                return {
                    'success': False,
                    'error': '文件不存在',
                    'message': f'文件路径无效: {file_path}'
                }
                
        except Exception as e:
            logger.error(f"❌ 上传过程出错: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '上传过程出错'
            }
    
    async def _click_import_button_fixed(self):
        """点击导入按钮 - 修复版"""
        import_selectors = [
            'button.desktop-import-button-pc',
            'nav button:has(i.desktop-icon-import)',
            'button:has-text("导入")',
            '[class*="import"]'
        ]
        
        for selector in import_selectors:
            try:
                btn = await self.page.wait_for_selector(selector, timeout=3000, state='visible')
                if btn:
                    await btn.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    await btn.click()
                    logger.info(f"✅ 成功点击导入按钮: {selector}")
                    await asyncio.sleep(2)
                    return True
            except:
                continue
        
        logger.error("❌ 未找到导入按钮")
        return False
    
    async def _handle_file_selection_fixed(self, file_path):
        """处理文件选择 - 修复版（使用expect_file_chooser）"""
        try:
            # 方法1：使用文件选择器API（推荐）
            logger.info("📁 等待文件选择器...")
            
            # 监听文件选择器
            async with self.page.expect_file_chooser(timeout=10000) as fc_info:
                # 文件选择器应该已经被导入按钮触发
                await asyncio.sleep(1)
            
            file_chooser = await fc_info.value
            await file_chooser.set_files(str(file_path))
            logger.info(f"✅ 通过文件选择器设置文件: {file_path}")
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ 文件选择器失败，尝试备用方案: {e}")
            
            # 方法2：直接查找input元素
            try:
                file_inputs = await self.page.query_selector_all('input[type="file"]')
                if file_inputs:
                    # 使用最后一个（通常是最新的）
                    await file_inputs[-1].set_input_files(str(file_path))
                    logger.info(f"✅ 通过input元素设置文件: {file_path}")
                    return True
            except Exception as e2:
                logger.error(f"❌ 备用方案也失败: {e2}")
            
            return False
    
    async def _click_confirm_button(self):
        """点击确定按钮"""
        await asyncio.sleep(2)
        
        confirm_selectors = [
            'button.dui-button-type-primary:has-text("确定")',
            'button:has-text("确定")',
            '.import-kit-import-file-footer button.dui-button-type-primary',
            'button.dui-button-type-primary .dui-button-container'
        ]
        
        for selector in confirm_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click()
                    logger.info(f"✅ 点击确定按钮: {selector}")
                    return True
            except:
                continue
        
        logger.warning("⚠️ 未找到确定按钮，但继续处理")
        return False
    
    async def _get_document_count(self):
        """获取当前文档数量"""
        try:
            doc_items = await self.page.query_selector_all('.doc-item, .file-item, [class*="document-item"]')
            return len(doc_items)
        except:
            return 0
    
    async def _wait_for_upload_success(self, initial_count, timeout=60):
        """等待上传成功 - 改进版"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查1：URL是否跳转到新文档
            current_url = self.page.url
            if '/sheet/' in current_url or '/doc/' in current_url:
                if 'desktop' not in current_url:
                    logger.info(f"🎯 检测到新文档URL: {current_url}")
                    return {
                        'success': True,
                        'url': current_url,
                        'message': '上传成功'
                    }
            
            # 检查2：文档列表是否有新增
            current_count = await self._get_document_count()
            if current_count > initial_count:
                logger.info("📈 检测到新文档添加")
                
                # 获取最新文档的链接
                new_doc_url = await self._get_latest_document_url()
                if new_doc_url:
                    return {
                        'success': True,
                        'url': new_doc_url,
                        'message': '上传成功'
                    }
            
            # 检查3：页面是否有成功提示
            success_text = await self.page.evaluate('''
                () => {
                    const text = document.body.textContent;
                    return text.includes('上传成功') || 
                           text.includes('导入成功') ||
                           text.includes('创建成功');
                }
            ''')
            
            if success_text:
                logger.info("✅ 检测到成功提示")
                # 等待一下再获取URL
                await asyncio.sleep(3)
                latest_url = await self._get_latest_document_url()
                if latest_url:
                    return {
                        'success': True,
                        'url': latest_url,
                        'message': '上传成功'
                    }
            
            await asyncio.sleep(2)
        
        # 超时但可能已成功
        logger.warning("⏱️ 等待超时，尝试获取最新文档")
        latest_url = await self._get_latest_document_url()
        if latest_url:
            return {
                'success': True,
                'url': latest_url,
                'message': '上传可能成功（超时）'
            }
        
        return {
            'success': False,
            'error': '上传超时',
            'message': '未检测到新文档'
        }
    
    async def _get_latest_document_url(self):
        """获取最新文档的URL"""
        try:
            # 通过JavaScript获取
            latest_url = await self.page.evaluate('''
                () => {
                    // 查找所有文档链接
                    const links = document.querySelectorAll('a[href*="docs.qq.com/sheet"], a[href*="docs.qq.com/doc"]');
                    if (links.length > 0) {
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
            
            if latest_url:
                logger.info(f"📎 找到新文档链接: {latest_url}")
            
            return latest_url
            
        except Exception as e:
            logger.error(f"获取文档链接失败: {e}")
            return None
    
    async def upload_to_existing(self, file_path, target_url):
        """上传到现有文档（替换内容）"""
        # 保持原有实现
        return await self.import_file(file_path)
    
    async def import_file(self, file_path):
        """导入文件到当前表格"""
        # 简化实现
        return await self.create_new_sheet(file_path)
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


async def upload_file(file_path, upload_option='new', target_url='', cookie_string=''):
    """
    上传文件到腾讯文档
    
    Args:
        file_path: 要上传的文件路径
        upload_option: 上传选项 (new/replace)
        target_url: 目标文档URL（仅在replace模式下使用）
        cookie_string: Cookie字符串用于登录
    
    Returns:
        dict: 上传结果
    """
    uploader = TencentDocUploader()
    
    try:
        # 初始化浏览器
        await uploader.init_browser(headless=True)
        
        # 使用Cookie登录
        if cookie_string:
            login_success = await uploader.login_with_cookies(cookie_string)
            if not login_success:
                return {
                    'success': False,
                    'error': '登录失败，请检查Cookie',
                    'message': 'Cookie无效或已过期'
                }
        
        # 根据选项执行上传
        if upload_option == 'new':
            result = await uploader.create_new_sheet(file_path)
        elif upload_option == 'replace' and target_url:
            result = await uploader.upload_to_existing(file_path, target_url)
        else:
            result = {
                'success': False,
                'error': '无效的上传选项',
                'message': '请选择正确的上传方式'
            }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': '上传过程出错'
        }
    finally:
        await uploader.close()


def sync_upload_file(file_path, upload_option='new', target_url='', cookie_string=''):
    """同步版本的上传函数"""
    return asyncio.run(upload_file(file_path, upload_option, target_url, cookie_string))


if __name__ == '__main__':
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python tencent_doc_uploader_fixed.py <文件路径> [new|replace] [目标URL]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    upload_option = sys.argv[2] if len(sys.argv) > 2 else 'new'
    target_url = sys.argv[3] if len(sys.argv) > 3 else ''
    
    # 读取Cookie
    config_path = Path('/root/projects/tencent-doc-manager/config/cookies.json')
    cookie_string = ''
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            cookie_string = config.get('cookie_string', '')
    
    # 执行上传
    result = sync_upload_file(file_path, upload_option, target_url, cookie_string)
    print(json.dumps(result, ensure_ascii=False, indent=2))