#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地浏览器桥接服务
允许网页通过WebSocket控制用户的本地浏览器
解决服务器无法直接控制客户端浏览器的问题
"""

import asyncio
import websockets
import json
import logging
import os
import time
from playwright.sync_api import sync_playwright
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalBrowserBridge:
    """
    本地浏览器桥接器
    在用户电脑上运行，接收来自网页的命令
    """
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.download_dir = os.path.expanduser("~/Downloads/TencentDocs")
        os.makedirs(self.download_dir, exist_ok=True)
        
    async def handle_websocket(self, websocket, path):
        """处理WebSocket连接"""
        client_ip = websocket.remote_address[0]
        logger.info(f"新连接来自: {client_ip}")
        
        try:
            async for message in websocket:
                try:
                    command = json.loads(message)
                    logger.info(f"收到命令: {command['action']}")
                    
                    result = await self.execute_command(command)
                    
                    # 返回结果给网页
                    await websocket.send(json.dumps(result))
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': '无效的JSON格式'
                    }))
                except Exception as e:
                    logger.error(f"处理命令出错: {e}")
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': str(e)
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"连接关闭: {client_ip}")
            
    async def execute_command(self, command):
        """执行具体命令"""
        action = command.get('action')
        
        if action == 'check_status':
            return {
                'status': 'success',
                'data': {
                    'bridge_version': '1.0.0',
                    'browser_connected': self.browser is not None,
                    'download_dir': self.download_dir
                }
            }
            
        elif action == 'init_browser':
            return await self.init_browser(command)
            
        elif action == 'login_check':
            return await self.check_login()
            
        elif action == 'download_document':
            return await self.download_document(command)
            
        elif action == 'close_browser':
            return await self.close_browser()
            
        else:
            return {
                'status': 'error',
                'message': f'未知的操作: {action}'
            }
            
    async def init_browser(self, command):
        """初始化浏览器"""
        try:
            if self.browser:
                return {
                    'status': 'success',
                    'message': '浏览器已经在运行'
                }
            
            # 启动Playwright
            self.playwright = sync_playwright().start()
            
            # 使用用户的Chrome配置
            user_data_dir = os.path.expanduser("~/.config/google-chrome-tencent")
            
            # 启动浏览器
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                channel='chrome',
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage'
                ],
                downloads_path=self.download_dir
            )
            
            # 打开新标签页
            self.page = self.browser.new_page()
            
            # 如果提供了cookie，设置它
            if 'cookies' in command:
                await self.set_cookies(command['cookies'])
            
            return {
                'status': 'success',
                'message': '浏览器启动成功'
            }
            
        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            return {
                'status': 'error',
                'message': f'启动浏览器失败: {str(e)}'
            }
            
    async def check_login(self):
        """检查登录状态"""
        try:
            if not self.page:
                return {
                    'status': 'error',
                    'message': '浏览器未启动'
                }
            
            # 访问腾讯文档首页
            self.page.goto("https://docs.qq.com", wait_until='networkidle')
            
            # 检查是否有登录标识
            is_logged_in = False
            try:
                # 查找用户信息元素
                user_element = self.page.locator('[class*="user"]').first
                if user_element.is_visible(timeout=3000):
                    is_logged_in = True
            except:
                pass
            
            if not is_logged_in:
                # 检查是否有登录按钮
                try:
                    login_button = self.page.locator('button:has-text("登录")').first
                    if login_button.is_visible(timeout=1000):
                        is_logged_in = False
                except:
                    is_logged_in = True  # 没有登录按钮可能已登录
            
            return {
                'status': 'success',
                'data': {
                    'logged_in': is_logged_in,
                    'url': self.page.url
                }
            }
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def download_document(self, command):
        """下载文档"""
        try:
            if not self.page:
                return {
                    'status': 'error',
                    'message': '浏览器未启动'
                }
            
            doc_id = command.get('doc_id')
            if not doc_id:
                return {
                    'status': 'error',
                    'message': '缺少文档ID'
                }
            
            # 访问文档
            doc_url = f"https://docs.qq.com/sheet/{doc_id}"
            logger.info(f"访问文档: {doc_url}")
            self.page.goto(doc_url, wait_until='networkidle')
            
            # 等待页面加载
            time.sleep(3)
            
            # 查找导出按钮
            export_selectors = [
                'button:has-text("导出")',
                'button:has-text("下载")',
                '[aria-label*="导出"]',
                'button:has-text("更多")'
            ]
            
            export_clicked = False
            for selector in export_selectors:
                try:
                    button = self.page.locator(selector).first
                    if button.is_visible(timeout=1000):
                        logger.info(f"点击按钮: {selector}")
                        button.click()
                        export_clicked = True
                        break
                except:
                    continue
            
            if not export_clicked:
                return {
                    'status': 'error',
                    'message': '未找到导出按钮'
                }
            
            # 等待菜单出现
            time.sleep(2)
            
            # 选择Excel格式
            format_type = command.get('format', 'xlsx')
            format_selectors = {
                'xlsx': ['text="Excel(.xlsx)"', 'text="Microsoft Excel"'],
                'csv': ['text="CSV"', 'text=".csv"']
            }
            
            # 监听下载
            download_started = False
            with self.page.expect_download(timeout=10000) as download_info:
                for selector in format_selectors.get(format_type, []):
                    try:
                        option = self.page.locator(selector).first
                        if option.is_visible(timeout=1000):
                            logger.info(f"选择格式: {selector}")
                            option.click()
                            download_started = True
                            break
                    except:
                        continue
            
            if download_started:
                download = download_info.value
                
                # 保存文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"doc_{doc_id}_{timestamp}.{format_type}"
                filepath = os.path.join(self.download_dir, filename)
                download.save_as(filepath)
                
                logger.info(f"文件已保存: {filepath}")
                
                return {
                    'status': 'success',
                    'data': {
                        'filepath': filepath,
                        'filename': filename,
                        'size': os.path.getsize(filepath)
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': '下载未开始'
                }
                
        except Exception as e:
            logger.error(f"下载文档失败: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def set_cookies(self, cookie_str):
        """设置Cookie"""
        try:
            # 先访问域名
            self.page.goto("https://docs.qq.com")
            
            # 解析cookie字符串
            cookies = []
            for item in cookie_str.split('; '):
                if '=' in item:
                    key, value = item.split('=', 1)
                    cookies.append({
                        'name': key,
                        'value': value,
                        'domain': '.qq.com',
                        'path': '/'
                    })
            
            # 添加cookies
            self.browser.add_cookies(cookies)
            
            logger.info(f"已设置 {len(cookies)} 个Cookie")
            
        except Exception as e:
            logger.error(f"设置Cookie失败: {e}")
            
    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
                self.page = None
                
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
                
            return {
                'status': 'success',
                'message': '浏览器已关闭'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

async def main():
    """主函数"""
    bridge = LocalBrowserBridge()
    
    logger.info("="*60)
    logger.info("腾讯文档本地浏览器桥接服务")
    logger.info("监听端口: ws://localhost:8765")
    logger.info("="*60)
    logger.info("\n使用说明:")
    logger.info("1. 保持此程序运行")
    logger.info("2. 访问网页控制面板")
    logger.info("3. 网页将通过WebSocket控制您的浏览器")
    logger.info("-"*60)
    
    # 启动WebSocket服务器
    async with websockets.serve(bridge.handle_websocket, "localhost", 8765):
        logger.info("✅ 服务已启动，等待连接...")
        await asyncio.Future()  # 永远运行

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n服务已停止")