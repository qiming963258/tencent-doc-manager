#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产级下载稳定性增强器 - Stage 2 完整版
整合Cookie管理器 + 现有下载系统 + 稳定性优化
"""

import sys
import os
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from cookie_manager import get_cookie_manager
from production_downloader import ProductionTencentDownloader

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StabilityEnhancedDownloader:
    """
    稳定性增强的下载系统
    结合Cookie管理器 + 生产级下载器 + 现有系统
    """
    
    def __init__(self, download_dir: str = None):
        """初始化增强下载器"""
        self.download_dir = download_dir or "/root/projects/tencent-doc-manager/downloads"
        self.cookie_manager = get_cookie_manager()
        
        # 确保下载目录存在
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 统计信息
        self.stats = {
            'attempts': 0,
            'successes': 0,
            'failures': 0,
            'cookie_refreshes': 0,
            'session_start': datetime.now().isoformat()
        }
        
        # 稳定性配置
        self.max_retries = 3
        self.timeout_extend_factor = 1.5  # 扩展超时倍数
        
    async def download_with_stability(self, url: str, format_type: str = 'csv', 
                                     cookies: str = None) -> Dict:
        """
        稳定性增强的下载接口
        
        Args:
            url: 腾讯文档URL
            format_type: 导出格式 ('csv', 'excel', 'xlsx')
            cookies: 可选的新Cookie
            
        Returns:
            dict: 下载结果
        """
        self.stats['attempts'] += 1
        
        try:
            logger.info(f"🚀 稳定性增强下载启动: {url}")
            
            # Step 1: Cookie管理与验证
            effective_cookies = await self._ensure_valid_cookies(cookies)
            if not effective_cookies:
                self.stats['failures'] += 1
                return {
                    'success': False,
                    'error': 'Cookie获取失败，无法进行认证',
                    'cookie_status': 'failed'
                }
            
            # Step 2: 使用生产级下载器执行下载
            downloader = ProductionTencentDownloader(self.download_dir)
            
            try:
                # 启动浏览器（增强配置）
                await downloader.start_browser(headless=True)
                
                # 设置Cookie
                login_success = await downloader.login_with_cookies(effective_cookies)
                if not login_success:
                    logger.warning("⚠️ 初始Cookie设置失败，尝试刷新Cookie...")
                    # 刷新Cookie并重试
                    fresh_cookies = await self.cookie_manager.get_valid_cookies()
                    if fresh_cookies:
                        login_success = await downloader.login_with_cookies(fresh_cookies)
                        effective_cookies = fresh_cookies
                        self.stats['cookie_refreshes'] += 1
                
                if not login_success:
                    raise Exception("Cookie认证失败，无法登录")
                
                # 执行下载（带稳定性增强）
                success, message, files = await downloader.download_document(
                    url, format_type
                )
                
                if success and files:
                    self.stats['successes'] += 1
                    result = {
                        'success': True,
                        'message': message,
                        'files': files,
                        'file_count': len(files),
                        'primary_file': files[0] if files else None,
                        'cookie_status': 'valid',
                        'download_method': 'production_downloader',
                        'stats': self.stats.copy()
                    }
                    
                    logger.info(f"✅ 下载成功: {len(files)} 个文件")
                    await self._record_success(url, result)
                    return result
                else:
                    # 下载失败，尝试使用备用方法
                    logger.warning("⚠️ 生产下载器失败，尝试备用方法...")
                    return await self._fallback_download(url, format_type, effective_cookies)
                    
            finally:
                # 确保清理资源
                try:
                    await downloader.cleanup()
                except:
                    pass
                    
        except Exception as e:
            self.stats['failures'] += 1
            logger.error(f"❌ 稳定性增强下载失败: {e}")
            
            # 记录失败
            await self._record_failure(url, str(e))
            
            return {
                'success': False,
                'error': str(e),
                'cookie_status': 'unknown',
                'stats': self.stats.copy()
            }
    
    async def _ensure_valid_cookies(self, provided_cookies: str = None) -> Optional[str]:
        """确保获取有效Cookie"""
        try:
            # 如果提供了新Cookie，更新到管理器
            if provided_cookies:
                logger.info("🔄 更新提供的Cookie到管理器...")
                success = await self.cookie_manager.update_primary_cookie(provided_cookies)
                if success:
                    logger.info("✅ 新Cookie已保存")
                    return provided_cookies
                else:
                    logger.warning("⚠️ 提供的Cookie无效")
            
            # 从管理器获取有效Cookie
            logger.info("📋 从Cookie管理器获取有效Cookie...")
            valid_cookies = await self.cookie_manager.get_valid_cookies()
            
            if valid_cookies:
                logger.info("✅ 已获取有效Cookie")
                return valid_cookies
            else:
                logger.error("❌ 无法从管理器获取有效Cookie")
                return None
                
        except Exception as e:
            logger.error(f"Cookie确保过程失败: {e}")
            return None
    
    async def _fallback_download(self, url: str, format_type: str, cookies: str) -> Dict:
        """备用下载方法"""
        try:
            logger.info("🔄 启动备用下载方法...")
            
            # 使用现有的下载自动化系统
            from tencent_export_automation import TencentDocAutoExporter
            
            exporter = TencentDocAutoExporter(
                download_dir=self.download_dir
                # 版本管理现在是强制启用的，不再需要参数
            )
            
            # 使用统一接口
            result = exporter.export_document(
                url=url,
                cookies=cookies,
                format=format_type,
                download_dir=self.download_dir
            )
            
            if result.get('success'):
                self.stats['successes'] += 1
                enhanced_result = {
                    'success': True,
                    'message': '备用方法下载成功',
                    'files': result.get('files', []),
                    'file_count': len(result.get('files', [])),
                    'primary_file': result.get('file_path'),
                    'cookie_status': 'valid',
                    'download_method': 'fallback_automation',
                    'stats': self.stats.copy(),
                    'original_result': result
                }
                
                logger.info("✅ 备用方法下载成功")
                await self._record_success(url, enhanced_result)
                return enhanced_result
            else:
                self.stats['failures'] += 1
                logger.error(f"❌ 备用方法也失败: {result.get('error')}")
                await self._record_failure(url, f"备用方法失败: {result.get('error')}")
                return {
                    'success': False,
                    'error': f"所有下载方法都失败: {result.get('error')}",
                    'download_method': 'fallback_failed',
                    'stats': self.stats.copy()
                }
            
        except Exception as e:
            self.stats['failures'] += 1
            logger.error(f"备用下载方法异常: {e}")
            await self._record_failure(url, f"备用方法异常: {str(e)}")
            return {
                'success': False,
                'error': f"备用下载方法异常: {str(e)}",
                'download_method': 'fallback_error',
                'stats': self.stats.copy()
            }
    
    async def _record_success(self, url: str, result: Dict):
        """记录成功的下载"""
        try:
            record = {
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'result': 'success',
                'files': result.get('files', []),
                'method': result.get('download_method', 'unknown'),
                'stats': self.stats.copy()
            }
            
            # 保存记录
            record_file = os.path.join(
                self.download_dir, 
                f"download_success_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
                
            logger.info(f"📝 成功记录已保存: {record_file}")
            
        except Exception as e:
            logger.error(f"保存成功记录失败: {e}")
    
    async def _record_failure(self, url: str, error_msg: str):
        """记录失败的下载"""
        try:
            record = {
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'result': 'failure',
                'error': error_msg,
                'stats': self.stats.copy()
            }
            
            # 保存记录
            record_file = os.path.join(
                self.download_dir, 
                f"download_failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
                
            logger.info(f"📝 失败记录已保存: {record_file}")
            
        except Exception as e:
            logger.error(f"保存失败记录失败: {e}")
    
    async def get_stability_report(self) -> Dict:
        """获取稳定性报告"""
        try:
            cookie_health = await self.cookie_manager.get_health_status()
            
            success_rate = (self.stats['successes'] / max(self.stats['attempts'], 1)) * 100
            
            report = {
                'overall_success_rate': f"{success_rate:.1f}%",
                'session_stats': self.stats,
                'cookie_health': cookie_health,
                'download_directory': self.download_dir,
                'stability_grade': self._calculate_stability_grade(success_rate),
                'recommendations': self._get_stability_recommendations(success_rate, cookie_health)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"获取稳定性报告失败: {e}")
            return {'error': str(e)}
    
    def _calculate_stability_grade(self, success_rate: float) -> str:
        """计算稳定性等级"""
        if success_rate >= 95:
            return "A+ (企业级)"
        elif success_rate >= 90:
            return "A (生产级)"
        elif success_rate >= 80:
            return "B+ (良好)"
        elif success_rate >= 70:
            return "B (可用)"
        elif success_rate >= 50:
            return "C (不稳定)"
        else:
            return "D (失败)"
    
    def _get_stability_recommendations(self, success_rate: float, cookie_health: Dict) -> List[str]:
        """获取稳定性建议"""
        recommendations = []
        
        if success_rate < 90:
            recommendations.append("建议增加网络重试机制")
            recommendations.append("建议延长页面加载超时时间")
        
        if not cookie_health.get('healthy', False):
            recommendations.append("需要更新Cookie认证信息")
            recommendations.append("建议添加备用Cookie")
        
        if cookie_health.get('backup_cookies_count', 0) == 0:
            recommendations.append("建议添加备用Cookie以提高可用性")
        
        if self.stats['cookie_refreshes'] > 3:
            recommendations.append("Cookie刷新频繁，建议检查Cookie有效期")
        
        if not recommendations:
            recommendations.append("系统运行稳定，保持当前配置")
        
        return recommendations


# 命令行接口
async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='稳定性增强下载系统')
    parser.add_argument('url', nargs='?', help='要下载的文档URL')
    parser.add_argument('-f', '--format', choices=['csv', 'excel', 'xlsx'], 
                       default='csv', help='导出格式')
    parser.add_argument('-d', '--download-dir', help='下载目录')
    parser.add_argument('-c', '--cookies', help='登录Cookie')
    parser.add_argument('--report', action='store_true', help='显示稳定性报告')
    
    args = parser.parse_args()
    
    downloader = StabilityEnhancedDownloader(args.download_dir)
    
    try:
        if args.url:
            print(f"📥 开始稳定性增强下载: {args.url}")
            result = await downloader.download_with_stability(
                args.url, args.format, args.cookies
            )
            
            if result['success']:
                print(f"✅ 下载成功!")
                if result.get('files'):
                    print(f"📁 下载文件 ({len(result['files'])}个):")
                    for file_path in result['files']:
                        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                        print(f"   - {Path(file_path).name} ({file_size:,} bytes)")
                print(f"🔧 下载方法: {result.get('download_method', 'unknown')}")
                print(f"🍪 Cookie状态: {result.get('cookie_status', 'unknown')}")
            else:
                print(f"❌ 下载失败: {result['error']}")
        
        if args.report or not args.url:
            print("\n📊 稳定性报告:")
            report = await downloader.get_stability_report()
            for key, value in report.items():
                if key == 'recommendations':
                    print(f"   {key}:")
                    for rec in value:
                        print(f"     • {rec}")
                else:
                    print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())