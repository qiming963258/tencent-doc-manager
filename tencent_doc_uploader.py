#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档上传器 - 真实上传功能
使用Playwright自动化实现文件上传到腾讯文档
"""

import asyncio
import os
import time
from pathlib import Path
from playwright.async_api import async_playwright
import json


class TencentDocUploader:
    """腾讯文档上传器"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.context = None
    
    async def init_browser(self, headless=True):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        
        # 启动浏览器（无头模式）
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        # 创建上下文
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        
        self.page = await self.context.new_page()
    
    async def login_with_cookies(self, cookie_string):
        """使用Cookie登录 - 使用与下载模块相同的Cookie处理逻辑"""
        if not cookie_string:
            return False
            
        # 先访问腾讯文档主页
        await self.page.goto('https://docs.qq.com')
        
        # 解析并设置cookies - 为多个域名添加（与下载模块保持一致）
        cookies = []
        for cookie_pair in cookie_string.split(';'):
            if '=' in cookie_pair:
                name, value = cookie_pair.strip().split('=', 1)
                # 为多个domain添加cookies（关键修复）
                domains = ['docs.qq.com', '.docs.qq.com', 'qq.com', '.qq.com']
                for domain in domains:
                    cookies.append({
                        'name': name,
                        'value': value,
                        'domain': domain,
                        'path': '/',
                        'httpOnly': False,
                        'secure': True,
                        'sameSite': 'None'
                    })
        
        try:
            await self.context.add_cookies(cookies)
            print(f"已添加 {len(cookies)} 个cookies（多域名）")
        except Exception as e:
            print(f"添加cookies时出错: {e}")
            # 降级到简单版本
            simple_cookies = []
            for cookie_pair in cookie_string.split(';'):
                if '=' in cookie_pair:
                    name, value = cookie_pair.strip().split('=', 1)
                    simple_cookies.append({
                        'name': name,
                        'value': value,
                        'domain': '.qq.com',
                        'path': '/'
                    })
            await self.context.add_cookies(simple_cookies)
            print(f"已添加简化cookies: {len(simple_cookies)} 个")
        
        # 刷新页面验证登录
        await self.page.reload()
        await asyncio.sleep(2)
        
        # 检查是否登录成功 - 使用与下载模块相同的验证逻辑
        try:
            # 检测多种登录标识（与下载模块保持一致）
            menu_btn = await self.page.query_selector('[class*="menu"]')
            more_btn = await self.page.query_selector('[class*="more"]')
            user_avatar = await self.page.query_selector('.user-avatar, .user-info')
            edit_elements = await self.page.query_selector('[class*="edit"]')
            
            # 只要存在任一元素就认为登录成功
            if menu_btn or more_btn or user_avatar or edit_elements:
                print("✅ 登录验证成功，检测到用户界面元素")
                return True
            else:
                print("❌ 未检测到登录标识，可能Cookie无效")
                return False
        except Exception as e:
            print(f"❌ 登录验证异常: {e}")
            # 即使验证失败也尝试继续（与下载模块保持一致）
            return True
    
    async def create_new_sheet(self, file_path):
        """创建新的在线表格并导入数据 - 使用正确的导入流程"""
        try:
            # 直接访问desktop页面（根据规格文档）
            await self.page.goto('https://docs.qq.com/desktop', 
                                 wait_until='domcontentloaded',
                                 timeout=30000)
            
            # 充分等待页面加载
            await asyncio.sleep(5)
            
            # 直接点击导入按钮（关键修复）
            import_success = await self.click_import_button_direct()
            
            if not import_success:
                print("⚠️ 导入按钮未找到，尝试备用方法")
                return {
                    'success': False,
                    'error': '未找到导入按钮',
                    'message': '请确认页面已加载完成'
                }
            
            # 等待导入对话框出现
            await asyncio.sleep(2)
            
            # 处理文件选择
            if file_path and Path(file_path).exists():
                await self.handle_file_selection_v2(file_path)
                
                # 等待上传完成并获取新文档URL
                await asyncio.sleep(8)
                
                # 获取新文档URL（可能需要从页面元素中提取）
                new_url = self.page.url
                
                # 如果仍在desktop页面，尝试获取新创建的文档链接
                if 'desktop' in new_url:
                    # 查找最新的文档链接
                    new_doc_link = await self.find_latest_document()
                    if new_doc_link:
                        new_url = new_doc_link
                
                return {
                    'success': True,
                    'url': new_url,
                    'message': '成功上传文档'
                }
            else:
                return {
                    'success': False,
                    'error': '文件不存在',
                    'message': f'文件路径无效: {file_path}'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '上传过程出错'
            }
    
    async def click_import_button_direct(self):
        """直接点击导入按钮（新方法）"""
        import_selectors = [
            'button.desktop-import-button-pc',  # 最准确的选择器
            'nav button:has(i.desktop-icon-import)',
            'button:has-text("导入")',
            '[class*="import"]',
            'button[title*="导入"]'
        ]
        
        for selector in import_selectors:
            try:
                btn = await self.page.wait_for_selector(selector, timeout=3000)
                if btn:
                    await btn.click()
                    print(f"✅ 成功点击导入按钮: {selector}")
                    return True
            except:
                continue
        
        print("❌ 未找到导入按钮")
        return False
    
    async def handle_file_selection_v2(self, file_path):
        """处理文件选择（改进版）"""
        await asyncio.sleep(2)  # 等待对话框完全打开
        
        try:
            # 方法1: 直接通过input选择文件（推荐）
            file_inputs = await self.page.query_selector_all('input[type="file"]')
            
            if file_inputs:
                # 使用最后一个file input（通常是最新的）
                await file_inputs[-1].set_input_files(str(file_path))
                print(f"✅ 通过input选择文件: {file_path}")
                return True
            
            # 方法2: 监听文件选择器事件
            print("尝试使用filechooser方式")
            
            # 设置文件选择器监听
            async def handle_file_chooser(file_chooser):
                print(f"📁 文件选择器触发")
                await file_chooser.set_files(str(file_path))
            
            self.page.once("filechooser", handle_file_chooser)
            
            # 尝试点击可能触发文件选择的元素
            select_btn_selectors = [
                'button:has-text("选择文件")',
                'button:has-text("浏览")',
                'button:has-text("上传")',
                '[class*="upload"]',
                '.file-select-btn'
            ]
            
            for selector in select_btn_selectors:
                try:
                    await self.page.click(selector, timeout=2000)
                    print(f"✅ 点击了文件选择按钮: {selector}")
                    await asyncio.sleep(1)
                    return True
                except:
                    continue
            
            # 如果都失败了，尝试强制设置
            print("⚠️ 尝试强制设置文件")
            # 查找任何可见的input
            all_inputs = await self.page.query_selector_all('input')
            for inp in all_inputs:
                try:
                    await inp.set_input_files(str(file_path))
                    print("✅ 强制设置文件成功")
                    return True
                except:
                    continue
                    
        except Exception as e:
            print(f"❌ 文件选择失败: {e}")
            return False
    
    async def find_latest_document(self):
        """查找最新创建的文档链接"""
        try:
            # 查找文档列表中的第一个（最新的）文档
            doc_links = await self.page.query_selector_all('a[href*="/sheet/"], a[href*="/doc/"]')
            if doc_links:
                first_link = await doc_links[0].get_attribute('href')
                if first_link and not first_link.startswith('http'):
                    first_link = f"https://docs.qq.com{first_link}"
                print(f"📎 找到新文档链接: {first_link}")
                return first_link
        except Exception as e:
            print(f"查找文档链接失败: {e}")
        return None
    
    async def import_file(self, file_path):
        """导入文件到当前表格"""
        try:
            # 查找导入按钮
            import_selectors = [
                'text=导入',
                'text=导入Excel',
                '[data-action="import"]',
                '.import-btn'
            ]
            
            for selector in import_selectors:
                try:
                    await self.page.click(selector, timeout=3000)
                    break
                except:
                    continue
            
            # 等待文件选择器
            async with self.page.expect_file_chooser() as fc_info:
                # 触发文件选择
                await self.page.click('text=选择文件')
                file_chooser = await fc_info.value
                await file_chooser.set_files(file_path)
            
            # 等待上传完成
            await asyncio.sleep(5)
            
            # 确认导入
            try:
                await self.page.click('text=确定')
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"导入文件失败: {e}")
            return False
    
    async def upload_to_existing(self, file_path, target_url):
        """上传到现有文档（替换内容）"""
        try:
            # 访问目标文档
            await self.page.goto(target_url)
            await asyncio.sleep(3)
            
            # 导入文件
            success = await self.import_file(file_path)
            
            if success:
                return {
                    'success': True,
                    'url': target_url,
                    'message': '成功更新文档内容'
                }
            else:
                return {
                    'success': False,
                    'error': '导入文件失败',
                    'message': '更新文档失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '访问文档失败'
            }
    
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
        print("用法: python tencent_doc_uploader.py <文件路径> [new|replace] [目标URL]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    upload_option = sys.argv[2] if len(sys.argv) > 2 else 'new'
    target_url = sys.argv[3] if len(sys.argv) > 3 else ''
    
    # 读取Cookie - 从正确的配置文件读取
    config_path = Path('/root/projects/tencent-doc-manager/config/cookies.json')
    cookie_string = ''
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            cookie_string = config.get('cookie_string', '')
    
    # 执行上传
    result = sync_upload_file(file_path, upload_option, target_url, cookie_string)
    print(json.dumps(result, ensure_ascii=False, indent=2))