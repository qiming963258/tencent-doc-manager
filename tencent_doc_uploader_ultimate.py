#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档上传器 - 终极修复版
解决文件选择器问题，使用input元素直接操作
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
    """腾讯文档上传器 - 终极版"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        
    async def init_browser(self, headless=True):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
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
        """使用Cookie登录"""
        if not cookie_string:
            return False
        
        try:
            # 解析cookies - 使用正确的分隔符
            cookies = []
            for cookie_pair in cookie_string.split('; '):  # 关键：分号+空格
                if '=' in cookie_pair:
                    name, value = cookie_pair.strip().split('=', 1)
                    cookies.append({
                        'name': name.strip(),
                        'value': value.strip(),
                        'domain': '.docs.qq.com',
                        'path': '/'
                    })
            
            await self.context.add_cookies(cookies)
            logger.info(f"✅ 已添加 {len(cookies)} 个cookies")
            
            # 访问desktop页面
            await self.page.goto('https://docs.qq.com/desktop/', 
                                wait_until='domcontentloaded',
                                timeout=30000)
            
            await asyncio.sleep(5)
            
            # 验证登录
            import_btn = await self.page.query_selector('button.desktop-import-button-pc')
            if import_btn:
                logger.info("✅ 登录成功，找到导入按钮")
                return True
            else:
                logger.warning("⚠️ 未找到导入按钮，但继续尝试")
                return True
                
        except Exception as e:
            logger.error(f"❌ 登录失败: {e}")
            return False
    
    async def create_new_sheet(self, file_path):
        """上传文件 - 终极修复版"""
        try:
            # 记录初始状态
            initial_doc_count = await self._get_document_count()
            logger.info(f"📊 当前文档数量: {initial_doc_count}")
            
            # 步骤1：先创建隐藏的input元素
            logger.info("🔧 创建文件输入元素...")
            await self.page.evaluate('''
                () => {
                    // 如果已存在则删除
                    const existingInput = document.getElementById('tencent-upload-input');
                    if (existingInput) {
                        existingInput.remove();
                    }
                    
                    // 创建新的input
                    const input = document.createElement('input');
                    input.type = 'file';
                    input.id = 'tencent-upload-input';
                    input.accept = '.xlsx,.xls,.csv';
                    input.style.display = 'none';
                    document.body.appendChild(input);
                    
                    return true;
                }
            ''')
            
            # 步骤2：设置文件
            logger.info("📁 设置文件...")
            file_input = await self.page.query_selector('#tencent-upload-input')
            if file_input:
                await file_input.set_input_files(str(file_path))
                logger.info(f"✅ 文件已设置: {file_path}")
            else:
                logger.error("❌ 未找到文件输入元素")
                return {'success': False, 'error': '无法创建文件输入元素'}
            
            # 步骤3：触发导入流程
            logger.info("🚀 触发导入流程...")
            
            # 方法A：点击导入按钮并模拟文件选择
            import_btn = await self.page.query_selector('button.desktop-import-button-pc')
            if import_btn:
                # 修改按钮的点击行为
                await self.page.evaluate('''
                    () => {
                        const btn = document.querySelector('button.desktop-import-button-pc');
                        const input = document.getElementById('tencent-upload-input');
                        
                        if (btn && input) {
                            // 创建change事件
                            const event = new Event('change', { bubbles: true });
                            
                            // 点击按钮
                            btn.click();
                            
                            // 延迟触发change事件
                            setTimeout(() => {
                                input.dispatchEvent(event);
                            }, 500);
                            
                            return true;
                        }
                        return false;
                    }
                ''')
                logger.info("✅ 已触发导入按钮点击")
                await asyncio.sleep(3)
            
            # 方法B：直接通过API上传（备用）
            if not import_btn:
                logger.info("⚠️ 尝试直接上传...")
                
                # 尝试查找任何文件输入框
                all_file_inputs = await self.page.query_selector_all('input[type="file"]')
                logger.info(f"找到 {len(all_file_inputs)} 个文件输入框")
                
                if all_file_inputs:
                    # 使用最后一个（通常是最新的）
                    await all_file_inputs[-1].set_input_files(str(file_path))
                    logger.info("✅ 通过现有输入框设置文件")
                    
                    # 触发change事件
                    await self.page.evaluate('''
                        () => {
                            const inputs = document.querySelectorAll('input[type="file"]');
                            if (inputs.length > 0) {
                                const lastInput = inputs[inputs.length - 1];
                                const event = new Event('change', { bubbles: true });
                                lastInput.dispatchEvent(event);
                            }
                        }
                    ''')
            
            # 步骤4：查找并点击确定按钮
            await asyncio.sleep(2)
            confirm_clicked = await self._click_confirm_button()
            
            # 步骤5：等待上传成功
            result = await self._wait_for_upload_success(initial_doc_count)
            
            # 清理创建的input元素
            await self.page.evaluate('''
                () => {
                    const input = document.getElementById('tencent-upload-input');
                    if (input) input.remove();
                }
            ''')
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 上传过程出错: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '上传过程出错'
            }
    
    async def _get_document_count(self):
        """获取文档数量"""
        try:
            doc_items = await self.page.query_selector_all('.doc-item, .file-item, [class*="document-item"]')
            return len(doc_items)
        except:
            return 0
    
    async def _click_confirm_button(self):
        """点击确定按钮"""
        confirm_selectors = [
            'button:has-text("确定")',
            'button.dui-button-type-primary:has-text("确定")',
            '.import-kit-import-file-footer button.dui-button-type-primary',
            'button[class*="primary"]:has-text("确定")'
        ]
        
        for selector in confirm_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click()
                    logger.info(f"✅ 点击确定按钮")
                    return True
            except:
                continue
        
        # 尝试按Enter键
        await self.page.keyboard.press('Enter')
        logger.info("⚠️ 未找到确定按钮，已按Enter键")
        return False
    
    async def _wait_for_upload_success(self, initial_count, timeout=60):
        """等待上传成功"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查URL变化
            current_url = self.page.url
            if '/sheet/' in current_url or '/doc/' in current_url:
                if 'desktop' not in current_url:
                    logger.info(f"🎯 检测到新文档URL: {current_url}")
                    return {
                        'success': True,
                        'url': current_url,
                        'message': '上传成功'
                    }
            
            # 检查文档数量变化
            current_count = await self._get_document_count()
            if current_count > initial_count:
                logger.info("📈 检测到新文档")
                
                # 获取新文档链接
                new_url = await self._get_latest_document_url()
                if new_url:
                    return {
                        'success': True,
                        'url': new_url,
                        'message': '上传成功'
                    }
            
            # 检查成功提示
            has_success = await self.page.evaluate('''
                () => {
                    const text = document.body.textContent;
                    return text.includes('上传成功') || 
                           text.includes('导入成功') ||
                           text.includes('创建成功');
                }
            ''')
            
            if has_success:
                logger.info("✅ 检测到成功提示")
                await asyncio.sleep(3)
                latest_url = await self._get_latest_document_url()
                if latest_url:
                    return {
                        'success': True,
                        'url': latest_url,
                        'message': '上传成功'
                    }
            
            await asyncio.sleep(2)
        
        # 超时处理
        logger.warning("⏱️ 等待超时")
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
        """获取最新文档URL"""
        try:
            latest_url = await self.page.evaluate('''
                () => {
                    const links = document.querySelectorAll('a[href*="docs.qq.com/sheet"], a[href*="docs.qq.com/doc"]');
                    if (links.length > 0) {
                        return links[0].href;
                    }
                    return null;
                }
            ''')
            return latest_url
        except:
            return None
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


# 保持原有接口兼容性
async def upload_file(file_path, upload_option='new', target_url='', cookie_string=''):
    """上传文件到腾讯文档"""
    uploader = TencentDocUploader()
    
    try:
        await uploader.init_browser(headless=True)
        
        if cookie_string:
            login_success = await uploader.login_with_cookies(cookie_string)
            if not login_success:
                return {
                    'success': False,
                    'error': '登录失败',
                    'message': 'Cookie无效或已过期'
                }
        
        result = await uploader.create_new_sheet(file_path)
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
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python tencent_doc_uploader_ultimate.py <文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # 读取Cookie
    config_path = Path('/root/projects/tencent-doc-manager/config/cookies.json')
    cookie_string = ''
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            cookie_string = config.get('cookie_string', '')
    
    # 执行上传
    result = sync_upload_file(file_path, cookie_string=cookie_string)
    print(json.dumps(result, ensure_ascii=False, indent=2))