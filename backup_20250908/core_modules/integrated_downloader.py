#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产级集成下载器 - 整合新Cookie管理器与现有下载系统
解决Stage 1的Cookie单点故障问题
"""

import sys
import os
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, List
from cookie_manager import get_cookie_manager
from tencent_export_automation import TencentDocAutoExporter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegratedProductionDownloader:
    """
    生产级集成下载器
    整合Cookie管理器 + 现有下载系统
    """
    
    def __init__(self, download_dir: str = None):
        """初始化集成下载器"""
        self.download_dir = download_dir or "/root/projects/tencent-doc-manager/downloads"
        self.cookie_manager = get_cookie_manager()
        self.exporter = None
        
        # 确保下载目录存在
        os.makedirs(self.download_dir, exist_ok=True)
        
    async def download_document(self, url: str, format: str = 'csv', cookies: str = None) -> Dict:
        """
        生产级下载文档接口
        
        Args:
            url: 腾讯文档URL
            format: 导出格式 ('csv', 'excel', 'xlsx')
            cookies: 可选的新Cookie（如果提供会更新Cookie管理器）
            
        Returns:
            dict: {
                'success': bool,
                'file_path': str,
                'files': list,
                'error': str,
                'cookie_status': dict
            }
        """
        try:
            logger.info(f"🚀 生产级下载启动: {url}")
            
            # Step 1: Cookie管理
            effective_cookies = None
            cookie_status = {"source": None, "valid": False}
            
            # 如果提供了新Cookie，更新Cookie管理器
            if cookies:
                logger.info("🔄 更新Cookie到生产级管理器...")
                success = await self.cookie_manager.update_primary_cookie(cookies)
                if success:
                    effective_cookies = cookies
                    cookie_status = {"source": "provided", "valid": True}
                    logger.info("✅ 新Cookie已保存到加密系统")
                else:
                    logger.warning("⚠️ 提供的Cookie无效，尝试使用存储的Cookie")
            
            # 如果没有有效Cookie，从管理器获取
            if not effective_cookies:
                logger.info("📋 从Cookie管理器获取有效Cookie...")
                stored_cookies = await self.cookie_manager.get_valid_cookies()
                if stored_cookies:
                    effective_cookies = stored_cookies
                    cookie_status = {"source": "stored", "valid": True}
                    logger.info("✅ 已获取存储的有效Cookie")
                else:
                    cookie_status = {"source": "none", "valid": False}
                    return {
                        'success': False,
                        'file_path': None,
                        'files': [],
                        'error': 'Cookie管理器中没有有效Cookie，请提供新Cookie',
                        'cookie_status': cookie_status
                    }
            
            # Step 2: 使用现有下载器执行下载
            logger.info("🚀 启动腾讯文档自动导出器...")
            self.exporter = TencentDocAutoExporter(
                download_dir=self.download_dir
                # 版本管理现在是强制启用的，不再需要参数
            )
            
            # 使用统一接口进行下载
            result = self.exporter.export_document(
                url=url,
                cookies=effective_cookies,
                format=format,
                download_dir=self.download_dir
            )
            
            # 增强结果信息
            result['cookie_status'] = cookie_status
            result['cookie_manager_active'] = True
            result['production_grade'] = True
            
            if result.get('success'):
                logger.info(f"✅ 生产级下载成功: {result.get('file_path')}")
            else:
                logger.error(f"❌ 生产级下载失败: {result.get('error')}")
            
            return result
            
        except Exception as e:
            error_msg = f"生产级下载异常: {e}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'file_path': None,
                'files': [],
                'error': error_msg,
                'cookie_status': cookie_status,
                'production_grade': False
            }
        finally:
            # 清理资源
            if self.exporter:
                try:
                    await self.exporter.cleanup()
                except:
                    pass
    
    async def get_cookie_health_status(self) -> Dict:
        """获取Cookie系统健康状态"""
        try:
            return await self.cookie_manager.get_health_status()
        except Exception as e:
            logger.error(f"获取Cookie健康状态失败: {e}")
            return {'healthy': False, 'error': str(e)}
    
    async def add_backup_cookie(self, cookie_string: str) -> bool:
        """添加备用Cookie"""
        try:
            return await self.cookie_manager.add_backup_cookie(cookie_string)
        except Exception as e:
            logger.error(f"添加备用Cookie失败: {e}")
            return False
    
    async def refresh_cookies(self) -> bool:
        """刷新Cookie状态"""
        try:
            valid_cookies = await self.cookie_manager.get_valid_cookies()
            return valid_cookies is not None
        except Exception as e:
            logger.error(f"刷新Cookie失败: {e}")
            return False


async def main():
    """主函数 - 命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='生产级集成下载器')
    parser.add_argument('url', help='文档URL')
    parser.add_argument('-f', '--format', choices=['csv', 'excel', 'xlsx'], default='csv', help='导出格式')
    parser.add_argument('-d', '--download-dir', help='下载目录')
    parser.add_argument('-c', '--cookies', help='登录Cookie')
    parser.add_argument('--health', action='store_true', help='显示Cookie健康状态')
    
    args = parser.parse_args()
    
    downloader = IntegratedProductionDownloader(args.download_dir)
    
    try:
        if args.health:
            print("📊 Cookie系统健康状态:")
            health = await downloader.get_cookie_health_status()
            for key, value in health.items():
                print(f"   {key}: {value}")
            print()
        
        # 执行下载
        result = await downloader.download_document(args.url, args.format, args.cookies)
        
        if result['success']:
            print(f"✅ 下载成功: {result['file_path']}")
            print(f"📊 Cookie状态: {result['cookie_status']}")
            if result.get('files'):
                print(f"📁 下载文件数: {len(result['files'])}")
                for file_path in result['files']:
                    file_size = os.path.getsize(file_path)
                    print(f"   - {Path(file_path).name} ({file_size:,} bytes)")
        else:
            print(f"❌ 下载失败: {result['error']}")
            print(f"📊 Cookie状态: {result['cookie_status']}")
            
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())