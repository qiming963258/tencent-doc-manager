#!/usr/bin/env python3
"""
稳定的Cookie下载器 - 优化版
通过直接URL访问和智能Cookie管理实现高稳定性
"""

import os
import time
import json
import hashlib
import requests
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StableCookieDownloader:
    """
    稳定的Cookie下载器
    核心优化：
    1. 直接使用导出URL，避免页面自动化
    2. Cookie智能管理和自动轮换
    3. 多种导出接口备份
    4. 智能重试和降级机制
    """
    
    def __init__(self, cookie_file: str = None):
        self.cookie_file = cookie_file or '/root/projects/tencent-doc-manager/config/cookies.json'
        self.cookies_pool = []  # Cookie池
        self.current_cookie_index = 0
        self.download_stats = {
            'success': 0,
            'failed': 0,
            'total_time': 0,
            'last_success': None
        }
        
        # 导出URL模板（按优先级排序）
        self.export_endpoints = [
            {
                'name': 'v1_export',
                'url': 'https://docs.qq.com/v1/export/export_office',
                'method': 'GET',
                'success_rate': 0.95
            },
            {
                'name': 'sheet_export',  
                'url': 'https://docs.qq.com/sheet/export',
                'method': 'GET',
                'success_rate': 0.90
            },
            {
                'name': 'cgi_export',
                'url': 'https://docs.qq.com/cgi-bin/excel/export',
                'method': 'POST',
                'success_rate': 0.85
            }
        ]
        
        # 加载Cookie
        self._load_cookies()
    
    def _load_cookies(self):
        """加载Cookie配置"""
        try:
            if os.path.exists(self.cookie_file):
                with open(self.cookie_file, 'r') as f:
                    config = json.load(f)
                    
                # 主Cookie
                if config.get('current_cookies'):
                    self.cookies_pool.append({
                        'cookie_string': config['current_cookies'],
                        'last_used': None,
                        'failure_count': 0,
                        'success_count': 0
                    })
                
                # 备用Cookie
                if config.get('backup_cookies'):
                    for backup in config['backup_cookies']:
                        self.cookies_pool.append({
                            'cookie_string': backup,
                            'last_used': None,
                            'failure_count': 0,
                            'success_count': 0
                        })
                
                logger.info(f"✅ 加载了 {len(self.cookies_pool)} 个Cookie")
            else:
                logger.warning(f"Cookie文件不存在: {self.cookie_file}")
                
        except Exception as e:
            logger.error(f"加载Cookie失败: {e}")
    
    def _get_current_cookie(self) -> Dict:
        """获取当前使用的Cookie"""
        if not self.cookies_pool:
            raise Exception("没有可用的Cookie")
        
        # 选择失败次数最少的Cookie
        sorted_cookies = sorted(self.cookies_pool, key=lambda x: x['failure_count'])
        return sorted_cookies[0]
    
    def _rotate_cookie(self):
        """轮换到下一个Cookie"""
        if len(self.cookies_pool) > 1:
            self.current_cookie_index = (self.current_cookie_index + 1) % len(self.cookies_pool)
            logger.info(f"切换到Cookie #{self.current_cookie_index + 1}")
    
    def _extract_doc_id(self, url: str) -> Tuple[str, Optional[str]]:
        """
        从URL提取文档ID和tab ID
        
        支持的URL格式：
        - https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN?tab=c2p5hs
        - https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN
        """
        # 提取路径中的文档ID
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        doc_id = None
        for part in path_parts:
            if part.startswith('D') and len(part) > 10:
                doc_id = part
                break
        
        # 提取查询参数中的tab
        query = parse_qs(parsed.query)
        tab_id = query.get('tab', [None])[0]
        
        if not doc_id:
            # 尝试从查询参数获取
            doc_id = query.get('id', [None])[0] or query.get('docid', [None])[0]
        
        return doc_id, tab_id
    
    def _build_export_url(self, doc_id: str, export_type: str = 'csv', 
                         endpoint: Dict = None, tab_id: str = None) -> str:
        """构建导出URL"""
        if not endpoint:
            endpoint = self.export_endpoints[0]
        
        base_url = endpoint['url']
        
        if endpoint['name'] == 'v1_export':
            # V1导出接口
            params = {
                'docid': doc_id,
                'type': export_type,
                'download': '1',
                'normal': '1',
                'preview': '0',
                'export_source': 'client'
            }
            if tab_id:
                params['tab'] = tab_id
            return f"{base_url}?{urlencode(params)}"
            
        elif endpoint['name'] == 'sheet_export':
            # Sheet导出接口
            params = {
                'id': doc_id,
                'type': export_type,
                'download': '1'
            }
            if tab_id:
                params['sheet_id'] = tab_id
            return f"{base_url}?{urlencode(params)}"
            
        else:
            # CGI导出接口
            return f"{base_url}?id={doc_id}&type={export_type}"
    
    def download_document(self, url: str, export_type: str = 'csv', 
                         save_dir: str = None) -> Dict:
        """
        下载腾讯文档
        
        Args:
            url: 腾讯文档URL
            export_type: 导出类型 (csv/xlsx)
            save_dir: 保存目录
            
        Returns:
            下载结果字典
        """
        start_time = time.time()
        
        # 提取文档ID
        doc_id, tab_id = self._extract_doc_id(url)
        if not doc_id:
            return {
                'success': False,
                'error': '无法从URL提取文档ID',
                'url': url
            }
        
        logger.info(f"📥 开始下载文档: {doc_id} (格式: {export_type})")
        
        # 尝试每个导出端点
        for endpoint_index, endpoint in enumerate(self.export_endpoints):
            try:
                # 构建导出URL
                export_url = self._build_export_url(doc_id, export_type, endpoint, tab_id)
                logger.info(f"尝试端点 #{endpoint_index + 1}: {endpoint['name']}")
                
                # 获取Cookie
                cookie_info = self._get_current_cookie()
                headers = {
                    'Cookie': cookie_info['cookie_string'],
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                # 发送请求
                response = requests.get(
                    export_url,
                    headers=headers,
                    allow_redirects=True,
                    stream=True,
                    timeout=30
                )
                
                # 检查响应
                if response.status_code == 200:
                    # 检查内容类型
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'application/json' in content_type:
                        # 可能是错误响应
                        error_data = response.json()
                        if error_data.get('ret') != 0:
                            logger.warning(f"接口返回错误: {error_data}")
                            cookie_info['failure_count'] += 1
                            continue
                    
                    # 保存文件
                    if not save_dir:
                        save_dir = '/root/projects/tencent-doc-manager/downloads'
                    os.makedirs(save_dir, exist_ok=True)
                    
                    # 生成文件名
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{doc_id}_{timestamp}.{export_type}"
                    filepath = os.path.join(save_dir, filename)
                    
                    # 写入文件
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    # 验证文件
                    file_size = os.path.getsize(filepath)
                    if file_size < 100:  # 文件太小，可能是错误页面
                        logger.warning(f"文件大小异常: {file_size} bytes")
                        os.remove(filepath)
                        continue
                    
                    # 更新统计
                    elapsed = time.time() - start_time
                    self.download_stats['success'] += 1
                    self.download_stats['total_time'] += elapsed
                    self.download_stats['last_success'] = datetime.now()
                    cookie_info['success_count'] += 1
                    cookie_info['last_used'] = datetime.now()
                    
                    logger.info(f"✅ 下载成功: {filepath} ({file_size/1024:.1f} KB, {elapsed:.1f}秒)")
                    
                    return {
                        'success': True,
                        'filepath': filepath,
                        'file_size': file_size,
                        'download_time': elapsed,
                        'endpoint_used': endpoint['name'],
                        'doc_id': doc_id
                    }
                
                elif response.status_code == 401:
                    logger.warning("Cookie已失效 (401)")
                    cookie_info['failure_count'] += 5  # 严重失败
                    self._rotate_cookie()
                    
                elif response.status_code == 403:
                    logger.warning("访问被拒绝 (403)")
                    cookie_info['failure_count'] += 2
                    
                else:
                    logger.warning(f"HTTP {response.status_code}")
                    cookie_info['failure_count'] += 1
                    
            except requests.exceptions.Timeout:
                logger.warning(f"请求超时: {endpoint['name']}")
                continue
                
            except Exception as e:
                logger.error(f"下载异常: {e}")
                continue
        
        # 所有尝试都失败
        self.download_stats['failed'] += 1
        elapsed = time.time() - start_time
        
        return {
            'success': False,
            'error': '所有下载尝试均失败',
            'doc_id': doc_id,
            'attempts': len(self.export_endpoints),
            'elapsed': elapsed
        }
    
    def batch_download(self, urls: List[str], export_type: str = 'csv') -> List[Dict]:
        """批量下载文档"""
        results = []
        total = len(urls)
        
        logger.info(f"开始批量下载 {total} 个文档")
        
        for index, url in enumerate(urls, 1):
            logger.info(f"[{index}/{total}] 处理: {url}")
            
            # 下载
            result = self.download_document(url, export_type)
            results.append(result)
            
            # 智能延时
            if result['success']:
                time.sleep(2)  # 成功后短延时
            else:
                time.sleep(5)  # 失败后长延时
                self._rotate_cookie()  # 失败后切换Cookie
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"批量下载完成: {success_count}/{total} 成功")
        
        return results
    
    def get_statistics(self) -> Dict:
        """获取下载统计信息"""
        total = self.download_stats['success'] + self.download_stats['failed']
        success_rate = self.download_stats['success'] / total if total > 0 else 0
        avg_time = self.download_stats['total_time'] / self.download_stats['success'] \
                   if self.download_stats['success'] > 0 else 0
        
        return {
            'total_downloads': total,
            'successful': self.download_stats['success'],
            'failed': self.download_stats['failed'],
            'success_rate': f"{success_rate * 100:.1f}%",
            'average_time': f"{avg_time:.1f}秒",
            'last_success': self.download_stats['last_success'],
            'cookie_pool_size': len(self.cookies_pool),
            'cookies_health': [
                {
                    'index': i,
                    'success': c['success_count'],
                    'failure': c['failure_count'],
                    'health': c['success_count'] / (c['success_count'] + c['failure_count']) * 100
                              if (c['success_count'] + c['failure_count']) > 0 else 100
                }
                for i, c in enumerate(self.cookies_pool)
            ]
        }


# 测试代码
if __name__ == "__main__":
    downloader = StableCookieDownloader()
    
    # 测试单个下载
    test_url = "https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN?tab=c2p5hs"
    
    print("测试CSV下载...")
    result = downloader.download_document(test_url, 'csv')
    print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 测试批量下载
    urls = [
        "https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN?tab=c2p5hs",
        # 添加更多URL
    ]
    
    print("\n测试批量下载...")
    results = downloader.batch_download(urls)
    
    # 显示统计
    print("\n下载统计:")
    stats = downloader.get_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))