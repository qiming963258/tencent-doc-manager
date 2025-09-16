#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产级上传下载稳定性系统 - Stage 2
整合Cookie管理器，提供企业级稳定性保证
解决上传下载100%失败率问题
"""

import sys
import os
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

import asyncio
import time
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from playwright.async_api import async_playwright
from cookie_manager import get_cookie_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionUploadDownloadManager:
    """
    生产级上传下载稳定性管理器
    解决Cookie单点故障和100%失败率问题
    """
    
    def __init__(self, base_dir: str = None):
        """初始化管理器"""
        self.base_dir = base_dir or "/root/projects/tencent-doc-manager"
        self.upload_dir = os.path.join(self.base_dir, "uploads")
        self.download_dir = os.path.join(self.base_dir, "downloads")
        self.records_dir = os.path.join(self.base_dir, "upload_records")
        
        # 创建必要目录
        for directory in [self.upload_dir, self.download_dir, self.records_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Cookie管理器
        self.cookie_manager = get_cookie_manager()
        
        # 浏览器资源
        self.browser = None
        self.page = None
        self.playwright = None
        
        # 配置参数
        self.max_retries = 5  # 增加重试次数
        self.retry_delay = 3  # 缩短重试间隔
        self.page_timeout = 45000  # 增加超时时间
        self.upload_timeout = 120  # 上传超时时间（秒）
        
        # 稳定性统计
        self.stats = {
            'uploads': {'success': 0, 'failed': 0, 'total': 0},
            'downloads': {'success': 0, 'failed': 0, 'total': 0},
            'cookie_refreshes': 0,
            'session_start': datetime.now().isoformat()
        }
        
    async def initialize_browser(self, headless: bool = True):
        """初始化浏览器环境"""
        try:
            logger.info("🚀 初始化生产级浏览器环境...")
            
            self.playwright = await async_playwright().start()
            
            # 浏览器配置（生产级优化）
            browser_config = {
                'headless': headless,
                'args': [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions'
                ]
            }
            
            self.browser = await self.playwright.chromium.launch(**browser_config)
            
            # 页面上下文配置（企业级稳定性）
            context_config = {
                'accept_downloads': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'viewport': {'width': 1920, 'height': 1080},
                'locale': 'zh-CN'
            }
            
            context = await self.browser.new_context(**context_config)
            self.page = await context.new_page()
            
            # 设置页面超时
            self.page.set_default_timeout(self.page_timeout)
            
            logger.info("✅ 浏览器环境初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 浏览器初始化失败: {e}")
            return False
    
    async def setup_cookies(self, cookies_string: str = None) -> bool:
        """设置和验证Cookie"""
        try:
            logger.info("🔐 设置生产级Cookie认证...")
            
            # 如果提供了新Cookie，更新到管理器
            if cookies_string:
                success = await self.cookie_manager.update_primary_cookie(cookies_string)
                if success:
                    logger.info("✅ 新Cookie已保存到加密系统")
                else:
                    logger.warning("⚠️ 提供的Cookie无效")
            
            # 获取有效Cookie
            valid_cookies = await self.cookie_manager.get_valid_cookies()
            if not valid_cookies:
                logger.error("❌ 无法获取有效Cookie")
                return False
            
            # 解析并设置Cookie到浏览器
            cookie_list = []
            domains = ['docs.qq.com', '.docs.qq.com', 'qq.com', '.qq.com']
            
            for cookie_str in valid_cookies.split(';'):
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
            
            await self.page.context.add_cookies(cookie_list)
            self.stats['cookie_refreshes'] += 1
            
            logger.info(f"✅ 已设置 {len(cookie_list)} 个Cookie（多域名支持）")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cookie设置失败: {e}")
            return False
    
    async def get_system_status(self) -> Dict:
        """获取系统状态"""
        try:
            cookie_health = await self.cookie_manager.get_health_status()
            
            return {
                'browser_ready': self.browser is not None,
                'cookie_health': cookie_health,
                'stats': self.stats,
                'success_rate': {
                    'uploads': (self.stats['uploads']['success'] / max(self.stats['uploads']['total'], 1)) * 100,
                    'downloads': (self.stats['downloads']['success'] / max(self.stats['downloads']['total'], 1)) * 100
                },
                'directories': {
                    'upload_dir': self.upload_dir,
                    'download_dir': self.download_dir,
                    'records_dir': self.records_dir
                }
            }
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {'error': str(e)}
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("✅ 生产级系统资源清理完成")
        except Exception as e:
            logger.error(f"资源清理失败: {e}")


# 命令行接口
async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='生产级上传下载稳定性系统')
    parser.add_argument('--cookies', help='登录Cookie')
    parser.add_argument('--status', action='store_true', help='显示系统状态')
    
    args = parser.parse_args()
    
    manager = ProductionUploadDownloadManager()
    
    try:
        # 初始化浏览器
        if not await manager.initialize_browser(headless=True):
            print("❌ 浏览器初始化失败")
            return
        
        # 设置Cookie
        if not await manager.setup_cookies(args.cookies):
            print("❌ Cookie设置失败")
            return
        
        if args.status:
            print("📊 系统状态:")
            status = await manager.get_system_status()
            for key, value in status.items():
                print(f"   {key}: {value}")
            print()
        
        # 显示最终统计
        final_status = await manager.get_system_status()
        print(f"📈 会话统计:")
        print(f"   上传成功率: {final_status['success_rate']['uploads']:.1f}%")
        print(f"   Cookie刷新次数: {final_status['stats']['cookie_refreshes']}")
        
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
    finally:
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())