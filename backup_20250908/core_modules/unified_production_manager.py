#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产级上传下载统一管理器 - Stage 2 完成版
整合Cookie管理器 + 上传系统 + 下载系统 + 稳定性保证
"""

import sys
import os
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List
from cookie_manager import get_cookie_manager
from stability_enhanced_downloader import StabilityEnhancedDownloader
from production_upload_manager import ProductionUploadDownloadManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedProductionManager:
    """
    统一的生产级上传下载管理器
    提供企业级稳定性保证
    """
    
    def __init__(self, base_dir: str = None):
        """初始化统一管理器"""
        self.base_dir = base_dir or "/root/projects/tencent-doc-manager"
        self.cookie_manager = get_cookie_manager()
        
        # 子系统初始化
        self.download_manager = StabilityEnhancedDownloader(
            os.path.join(self.base_dir, "downloads")
        )
        self.upload_manager = ProductionUploadDownloadManager(self.base_dir)
        
        # 统计信息
        self.session_stats = {
            'session_start': datetime.now().isoformat(),
            'downloads': {'total': 0, 'success': 0, 'failed': 0},
            'uploads': {'total': 0, 'success': 0, 'failed': 0},
            'cookie_operations': 0,
            'system_health_checks': 0
        }
        
        logger.info("✅ 统一生产级管理器初始化完成")
    
    async def download_document(self, url: str, format_type: str = 'csv', 
                              cookies: str = None) -> Dict:
        """
        统一下载接口
        
        Args:
            url: 腾讯文档URL
            format_type: 导出格式 ('csv', 'excel', 'xlsx')
            cookies: 可选的Cookie
            
        Returns:
            dict: 下载结果
        """
        self.session_stats['downloads']['total'] += 1
        
        try:
            logger.info(f"📥 统一下载接口: {url} (格式: {format_type})")
            
            result = await self.download_manager.download_with_stability(
                url, format_type, cookies
            )
            
            if result.get('success'):
                self.session_stats['downloads']['success'] += 1
                logger.info("✅ 下载成功")
            else:
                self.session_stats['downloads']['failed'] += 1
                logger.error(f"❌ 下载失败: {result.get('error')}")
            
            # 增强结果信息
            result['session_stats'] = self.session_stats.copy()
            result['manager_type'] = 'unified_production'
            
            return result
            
        except Exception as e:
            self.session_stats['downloads']['failed'] += 1
            logger.error(f"❌ 统一下载接口异常: {e}")
            return {
                'success': False,
                'error': str(e),
                'manager_type': 'unified_production',
                'session_stats': self.session_stats.copy()
            }
    
    async def upload_file(self, file_path: str, description: str = None, 
                         cookies: str = None) -> Dict:
        """
        统一上传接口
        
        Args:
            file_path: 文件路径
            description: 文件描述
            cookies: 可选的Cookie
            
        Returns:
            dict: 上传结果
        """
        self.session_stats['uploads']['total'] += 1
        
        try:
            logger.info(f"📤 统一上传接口: {file_path}")
            
            # 确保浏览器已初始化
            if not self.upload_manager.browser:
                await self.upload_manager.initialize_browser()
            
            # 设置Cookie
            await self.upload_manager.setup_cookies(cookies)
            
            result = await self.upload_manager.upload_file_with_stability(
                file_path, description
            )
            
            if result.get('success'):
                self.session_stats['uploads']['success'] += 1
                logger.info("✅ 上传成功")
            else:
                self.session_stats['uploads']['failed'] += 1
                logger.error(f"❌ 上传失败: {result.get('error')}")
            
            # 增强结果信息
            result['session_stats'] = self.session_stats.copy()
            result['manager_type'] = 'unified_production'
            
            return result
            
        except Exception as e:
            self.session_stats['uploads']['failed'] += 1
            logger.error(f"❌ 统一上传接口异常: {e}")
            return {
                'success': False,
                'error': str(e),
                'manager_type': 'unified_production',
                'session_stats': self.session_stats.copy()
            }
    
    async def update_cookies(self, cookies: str, set_as_backup: bool = False) -> Dict:
        """
        更新Cookie管理
        
        Args:
            cookies: Cookie字符串
            set_as_backup: 是否设为备用Cookie
            
        Returns:
            dict: 更新结果
        """
        self.session_stats['cookie_operations'] += 1
        
        try:
            logger.info("🍪 更新Cookie管理...")
            
            if set_as_backup:
                success = await self.cookie_manager.add_backup_cookie(cookies)
                operation = "backup"
            else:
                success = await self.cookie_manager.update_primary_cookie(cookies)
                operation = "primary"
            
            if success:
                logger.info(f"✅ {operation} Cookie更新成功")
                return {
                    'success': True,
                    'operation': operation,
                    'message': f'{operation} Cookie更新成功'
                }
            else:
                logger.error(f"❌ {operation} Cookie更新失败")
                return {
                    'success': False,
                    'operation': operation,
                    'error': f'{operation} Cookie更新失败'
                }
                
        except Exception as e:
            logger.error(f"❌ Cookie更新异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_comprehensive_status(self) -> Dict:
        """获取综合系统状态"""
        self.session_stats['system_health_checks'] += 1
        
        try:
            logger.info("📊 获取综合系统状态...")
            
            # 获取各子系统状态
            cookie_health = await self.cookie_manager.get_health_status()
            download_report = await self.download_manager.get_stability_report()
            
            # 上传系统状态
            upload_status = {'error': 'upload manager not initialized'}
            try:
                if self.upload_manager.browser:
                    upload_status = await self.upload_manager.get_system_status()
                else:
                    upload_status = {
                        'browser_ready': False,
                        'note': 'browser not initialized - will auto-initialize on first upload'
                    }
            except Exception as e:
                upload_status = {'error': str(e)}
            
            # 计算综合成功率
            total_operations = (self.session_stats['downloads']['total'] + 
                              self.session_stats['uploads']['total'])
            total_successes = (self.session_stats['downloads']['success'] + 
                             self.session_stats['uploads']['success'])
            
            overall_success_rate = (total_successes / max(total_operations, 1)) * 100
            
            # 系统等级评估
            system_grade = self._calculate_system_grade(
                overall_success_rate, cookie_health, download_report
            )
            
            comprehensive_status = {
                'system_grade': system_grade,
                'overall_success_rate': f"{overall_success_rate:.1f}%",
                'session_stats': self.session_stats,
                'cookie_system': cookie_health,
                'download_system': {
                    'success_rate': download_report.get('overall_success_rate', '0.0%'),
                    'stability_grade': download_report.get('stability_grade', 'Unknown'),
                    'stats': download_report.get('session_stats', {})
                },
                'upload_system': upload_status,
                'directories': {
                    'base_dir': self.base_dir,
                    'downloads': os.path.join(self.base_dir, "downloads"),
                    'uploads': os.path.join(self.base_dir, "uploads"),
                    'records': os.path.join(self.base_dir, "upload_records")
                },
                'recommendations': self._get_system_recommendations(
                    cookie_health, download_report, upload_status
                )
            }
            
            return comprehensive_status
            
        except Exception as e:
            logger.error(f"❌ 获取综合状态失败: {e}")
            return {
                'error': str(e),
                'session_stats': self.session_stats
            }
    
    def _calculate_system_grade(self, success_rate: float, cookie_health: Dict, 
                               download_report: Dict) -> str:
        """计算系统综合等级"""
        if (success_rate >= 95 and 
            cookie_health.get('healthy', False) and 
            'A' in download_report.get('stability_grade', '')):
            return "🏅 A+ (企业级生产就绪)"
        elif success_rate >= 90 and cookie_health.get('healthy', False):
            return "✅ A (生产级稳定)"
        elif success_rate >= 80:
            return "🟢 B+ (良好运行)"
        elif success_rate >= 70:
            return "🟡 B (基本可用)"
        elif success_rate >= 50:
            return "🟠 C (不稳定)"
        else:
            return "🔴 D+ (原型阶段)"
    
    def _get_system_recommendations(self, cookie_health: Dict, download_report: Dict, 
                                   upload_status: Dict) -> List[str]:
        """获取系统优化建议"""
        recommendations = []
        
        # Cookie系统建议
        if not cookie_health.get('healthy', False):
            recommendations.append("🍪 需要更新主Cookie认证")
        
        if cookie_health.get('backup_cookies_count', 0) == 0:
            recommendations.append("🍪 建议添加备用Cookie提高可用性")
        
        # 下载系统建议
        download_recs = download_report.get('recommendations', [])
        for rec in download_recs[:2]:  # 只取前2个建议
            recommendations.append(f"📥 {rec}")
        
        # 上传系统建议
        if upload_status.get('error'):
            recommendations.append("📤 上传系统需要初始化")
        
        # 通用建议
        if len(recommendations) == 0:
            recommendations.append("✨ 系统运行良好，建议定期检查Cookie有效性")
        
        return recommendations
    
    async def cleanup(self):
        """清理所有资源"""
        try:
            logger.info("🧹 清理统一管理器资源...")
            
            # 清理上传管理器
            if self.upload_manager:
                await self.upload_manager.cleanup()
            
            logger.info("✅ 统一管理器资源清理完成")
            
        except Exception as e:
            logger.error(f"❌ 资源清理失败: {e}")


# 命令行接口
async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='统一生产级上传下载管理器')
    parser.add_argument('--download', help='下载文档URL')
    parser.add_argument('--upload', help='上传文件路径')
    parser.add_argument('-f', '--format', choices=['csv', 'excel', 'xlsx'], 
                       default='csv', help='下载格式')
    parser.add_argument('-d', '--description', help='上传文件描述')
    parser.add_argument('-c', '--cookies', help='Cookie认证')
    parser.add_argument('--add-backup-cookie', help='添加备用Cookie')
    parser.add_argument('--status', action='store_true', help='显示系统状态')
    
    args = parser.parse_args()
    
    manager = UnifiedProductionManager()
    
    try:
        # Cookie管理
        if args.add_backup_cookie:
            result = await manager.update_cookies(args.add_backup_cookie, set_as_backup=True)
            if result['success']:
                print(f"✅ 备用Cookie添加成功")
            else:
                print(f"❌ 备用Cookie添加失败: {result['error']}")
            print()
        
        # 下载操作
        if args.download:
            print(f"📥 开始下载: {args.download}")
            result = await manager.download_document(args.download, args.format, args.cookies)
            
            if result['success']:
                print(f"✅ 下载成功!")
                if result.get('files'):
                    print(f"📁 文件 ({len(result['files'])}个):")
                    for file_path in result['files']:
                        from pathlib import Path
                        print(f"   - {Path(file_path).name}")
            else:
                print(f"❌ 下载失败: {result['error']}")
            print()
        
        # 上传操作
        if args.upload:
            print(f"📤 开始上传: {args.upload}")
            result = await manager.upload_file(args.upload, args.description, args.cookies)
            
            if result['success']:
                print(f"✅ 上传成功!")
                if result.get('doc_url'):
                    print(f"🔗 文档链接: {result['doc_url']}")
            else:
                print(f"❌ 上传失败: {result['error']}")
            print()
        
        # 系统状态
        if args.status or (not args.download and not args.upload):
            print("📊 统一系统状态:")
            status = await manager.get_comprehensive_status()
            
            print(f"   系统等级: {status.get('system_grade', 'Unknown')}")
            print(f"   总成功率: {status.get('overall_success_rate', '0.0%')}")
            
            if 'recommendations' in status:
                print("   优化建议:")
                for rec in status['recommendations']:
                    print(f"     • {rec}")
            
            print(f"   会话统计: {status.get('session_stats', {})}")
        
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
    finally:
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())