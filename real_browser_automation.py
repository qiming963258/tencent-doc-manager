#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实浏览器自动化 - 控制您自己的Chrome浏览器
核心思想：不是伪装，而是真的用您的浏览器！
"""

import os
import time
import json
import subprocess
from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealBrowserController:
    """
    控制真实的Chrome浏览器实例
    使用您自己的用户配置文件，保持完整的登录状态
    """
    
    def __init__(self):
        self.chrome_debug_port = 9222
        self.download_dir = "/root/projects/tencent-doc-manager/real_downloads"
        os.makedirs(self.download_dir, exist_ok=True)
        
    def launch_chrome_with_debugging(self):
        """
        启动带调试端口的Chrome
        使用真实的用户配置文件
        """
        logger.info("启动真实的Chrome浏览器...")
        
        # Chrome配置路径（根据系统调整）
        chrome_paths = {
            'linux': [
                '/usr/bin/google-chrome',
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser'
            ],
            'darwin': ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'],
            'win32': ['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe']
        }
        
        # 用户数据目录（使用独立的自动化配置）
        user_data_dir = os.path.expanduser("~/.config/google-chrome-automation")
        
        # 查找Chrome可执行文件
        chrome_exe = None
        import platform
        system = platform.system().lower()
        if system == 'linux':
            for path in chrome_paths['linux']:
                if os.path.exists(path):
                    chrome_exe = path
                    break
        
        if not chrome_exe:
            logger.error("未找到Chrome，请安装Chrome浏览器")
            return False
            
        # 启动命令
        cmd = [
            chrome_exe,
            f'--remote-debugging-port={self.chrome_debug_port}',
            f'--user-data-dir={user_data_dir}',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-popup-blocking',
            '--disable-translate',
            '--start-maximized'
        ]
        
        try:
            # 启动Chrome
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(3)  # 等待Chrome启动
            
            logger.info(f"✅ Chrome已启动，调试端口: {self.chrome_debug_port}")
            logger.info(f"用户数据目录: {user_data_dir}")
            logger.info("请手动登录腾讯文档...")
            
            return True
            
        except Exception as e:
            logger.error(f"启动Chrome失败: {e}")
            return False
            
    def connect_to_existing_chrome(self):
        """
        连接到已经运行的Chrome实例
        这是关键：使用您真实的浏览器会话
        """
        try:
            with sync_playwright() as p:
                # 连接到调试端口
                logger.info(f"连接到Chrome调试端口 {self.chrome_debug_port}...")
                browser = p.chromium.connect_over_cdp(f"http://localhost:{self.chrome_debug_port}")
                
                logger.info(f"✅ 成功连接！发现 {len(browser.contexts)} 个上下文")
                
                # 获取默认上下文（包含您的所有Cookie和登录状态）
                if browser.contexts:
                    context = browser.contexts[0]
                    logger.info(f"使用默认上下文，包含 {len(context.pages)} 个页面")
                else:
                    logger.info("创建新上下文")
                    context = browser.new_context()
                
                return browser, context
                
        except Exception as e:
            logger.error(f"连接失败: {e}")
            logger.info("请确保Chrome已经以调试模式启动")
            logger.info(f"检查 http://localhost:{self.chrome_debug_port} 是否可访问")
            return None, None
            
    def download_document_naturally(self, doc_id: str):
        """
        自然地下载文档 - 就像您手动操作一样
        """
        browser, context = self.connect_to_existing_chrome()
        if not browser:
            return False
            
        try:
            # 创建新页面或使用现有页面
            if context.pages:
                page = context.pages[0]
            else:
                page = context.new_page()
            
            doc_url = f"https://docs.qq.com/sheet/{doc_id}"
            logger.info(f"访问文档: {doc_url}")
            
            # 自然地访问页面（不急不躁）
            page.goto(doc_url, wait_until='domcontentloaded')
            
            # 像人类一样等待页面加载
            logger.info("等待页面完全加载...")
            time.sleep(3 + np.random.random() * 2)  # 3-5秒随机等待
            
            # 检查是否已登录
            if "登录" in page.content() or "login" in page.url.lower():
                logger.warning("需要登录！请手动登录后重试")
                input("登录完成后按Enter继续...")
            
            # 模拟人类行为：先滚动查看
            logger.info("模拟查看文档...")
            page.mouse.wheel(0, 300)
            time.sleep(1)
            page.mouse.wheel(0, -300)
            time.sleep(1)
            
            # 查找并点击导出按钮（多种可能的选择器）
            export_selectors = [
                'button:has-text("导出")',
                'button[title*="导出"]',
                '[aria-label*="导出"]',
                'button:has-text("下载")',
                '[class*="export"]',
                'button[class*="download"]',
                # 更多按钮
                'button:has-text("更多")',
                '[aria-label="更多操作"]',
                'button[title="更多"]'
            ]
            
            export_clicked = False
            for selector in export_selectors:
                try:
                    if page.locator(selector).is_visible():
                        logger.info(f"找到按钮: {selector}")
                        
                        # 像人类一样移动鼠标到按钮
                        button = page.locator(selector).first
                        box = button.bounding_box()
                        if box:
                            # 移动到按钮中心附近的随机位置
                            x = box['x'] + box['width'] / 2 + (np.random.random() - 0.5) * 10
                            y = box['y'] + box['height'] / 2 + (np.random.random() - 0.5) * 5
                            page.mouse.move(x, y)
                            time.sleep(0.5)
                        
                        # 点击
                        button.click()
                        export_clicked = True
                        time.sleep(2)
                        break
                except:
                    continue
            
            if not export_clicked:
                # 尝试键盘快捷键
                logger.info("尝试使用键盘快捷键...")
                page.keyboard.press("Control+Shift+E")
                time.sleep(2)
            
            # 选择Excel格式
            excel_selectors = [
                'text="Excel(.xlsx)"',
                'text="Microsoft Excel"',
                'text="下载为 Excel"',
                '[data-format="xlsx"]',
                'li:has-text("Excel")'
            ]
            
            for selector in excel_selectors:
                try:
                    if page.locator(selector).is_visible():
                        logger.info(f"选择Excel格式: {selector}")
                        
                        # 设置下载监听
                        with page.expect_download() as download_info:
                            page.locator(selector).click()
                            logger.info("等待下载...")
                            
                        download = download_info.value
                        
                        # 保存文件
                        filename = f"doc_{doc_id}_{int(time.time())}.xlsx"
                        filepath = os.path.join(self.download_dir, filename)
                        download.save_as(filepath)
                        
                        logger.info(f"✅ 下载成功: {filepath}")
                        
                        # 验证文件
                        if os.path.exists(filepath):
                            size = os.path.getsize(filepath)
                            with open(filepath, 'rb') as f:
                                header = f.read(4)
                            
                            if header == b'PK\x03\x04':
                                logger.info(f"✅ 确认是真正的Excel文件! 大小: {size} bytes")
                                return filepath
                            else:
                                logger.warning(f"文件格式异常: {header}")
                        
                        break
                except Exception as e:
                    logger.debug(f"尝试 {selector} 失败: {e}")
            
            # 如果自动下载失败，提示手动操作
            if not export_clicked:
                logger.info("\n自动化遇到困难，请手动操作：")
                logger.info("1. 点击导出按钮")
                logger.info("2. 选择Excel格式")
                logger.info("3. 等待下载完成")
                input("手动下载完成后按Enter继续...")
                
                # 检查下载目录
                downloads = os.listdir(self.download_dir)
                if downloads:
                    latest = max(downloads, key=lambda x: os.path.getctime(os.path.join(self.download_dir, x)))
                    logger.info(f"发现下载文件: {latest}")
                    return os.path.join(self.download_dir, latest)
            
        except Exception as e:
            logger.error(f"下载过程出错: {e}")
            
        finally:
            # 不关闭浏览器，保持会话
            logger.info("保持浏览器打开")
            
        return None

    def batch_download_naturally(self, doc_ids: list):
        """
        批量下载，模拟真实的使用场景
        """
        results = []
        
        for i, doc_id in enumerate(doc_ids):
            logger.info(f"\n处理第 {i+1}/{len(doc_ids)} 个文档...")
            
            # 像人类一样，不要太快
            if i > 0:
                wait_time = 10 + np.random.random() * 10  # 10-20秒
                logger.info(f"休息 {wait_time:.1f} 秒...")
                time.sleep(wait_time)
            
            result = self.download_document_naturally(doc_id)
            results.append({
                'doc_id': doc_id,
                'success': result is not None,
                'file': result
            })
            
            # 每下载3个文档，休息更长时间
            if (i + 1) % 3 == 0:
                logger.info("下载了3个文档，休息1分钟...")
                time.sleep(60)
        
        return results

# 添加numpy的简单替代（如果没有安装numpy）
try:
    import numpy as np
except ImportError:
    import random
    class np:
        @staticmethod
        def random():
            return random.random()

def main():
    """主函数"""
    controller = RealBrowserController()
    
    logger.info("="*60)
    logger.info("真实浏览器自动化控制")
    logger.info("使用您自己的Chrome，保持完整登录状态")
    logger.info("="*60)
    
    # 步骤1：启动Chrome（如果需要）
    logger.info("\n步骤1: 启动Chrome浏览器")
    logger.info("如果Chrome已经运行，请先关闭它")
    
    choice = input("\n是否需要启动Chrome？(y/n): ")
    if choice.lower() == 'y':
        if controller.launch_chrome_with_debugging():
            logger.info("请在浏览器中手动登录腾讯文档")
            input("登录完成后按Enter继续...")
    else:
        logger.info(f"请手动启动Chrome：")
        logger.info(f"chrome --remote-debugging-port={controller.chrome_debug_port}")
    
    # 步骤2：连接到Chrome
    logger.info("\n步骤2: 连接到Chrome")
    browser, context = controller.connect_to_existing_chrome()
    
    if browser:
        # 步骤3：下载文档
        logger.info("\n步骤3: 下载文档")
        
        # 测试文档
        test_docs = [
            "DWEVjZndkR2xVSWJN",  # 测试版本-小红书部门
            "DRFppYm15RGZ2WExN",  # 测试版本-回国销售计划表
            "DRHZrS1hOS3pwRGZB"   # 测试版本-出国销售计划表
        ]
        
        choice = input("\n下载测试文档？(y/n): ")
        if choice.lower() == 'y':
            for doc_id in test_docs:
                logger.info(f"\n下载文档: {doc_id}")
                result = controller.download_document_naturally(doc_id)
                if result:
                    logger.info(f"✅ 成功: {result}")
                else:
                    logger.info("❌ 失败")
                
                # 人类般的间隔
                time.sleep(5)
    
    logger.info("\n" + "="*60)
    logger.info("完成！")

if __name__ == "__main__":
    main()