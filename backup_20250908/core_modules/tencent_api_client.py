#!/usr/bin/env python3
"""
腾讯文档API客户端 - 生产级实现
用于替代不稳定的Cookie+爬虫方式
"""

import os
import json
import time
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TencentDocsAPIClient:
    """腾讯文档API客户端 - OAuth方式"""
    
    def __init__(self, config_file: str = None):
        """
        初始化API客户端
        
        Args:
            config_file: 配置文件路径，包含client_id, client_secret等
        """
        self.config_file = config_file or '/root/projects/tencent-doc-manager/config/api_config.json'
        self.config = self._load_config()
        
        # API端点
        self.auth_base = "https://docs.qq.com/oauth/v2"
        self.api_base = "https://docs.qq.com/openapi"
        
        # Token管理
        self.access_token = self.config.get('access_token')
        self.refresh_token = self.config.get('refresh_token')
        self.token_expires_at = self._parse_expires(self.config.get('token_expires_at'))
        
        # 统计信息
        self.stats = {
            'api_calls': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'token_refreshes': 0
        }
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # 默认配置模板
            default_config = {
                'client_id': '',
                'client_secret': '',
                'redirect_uri': 'http://localhost:8089/oauth/callback',
                'access_token': None,
                'refresh_token': None,
                'token_expires_at': None,
                'auto_refresh': True,
                'fallback_to_cookie': True  # 失败时降级到Cookie方式
            }
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.warning(f"已创建配置文件模板: {self.config_file}")
            return default_config
    
    def _save_config(self):
        """保存配置到文件"""
        self.config['access_token'] = self.access_token
        self.config['refresh_token'] = self.refresh_token
        self.config['token_expires_at'] = self.token_expires_at.isoformat() if self.token_expires_at else None
        
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _parse_expires(self, expires_str: str) -> Optional[datetime]:
        """解析过期时间"""
        if not expires_str:
            return None
        try:
            return datetime.fromisoformat(expires_str)
        except:
            return None
    
    def is_token_valid(self) -> bool:
        """检查token是否有效"""
        if not self.access_token or not self.token_expires_at:
            return False
        
        # 提前5分钟刷新
        return datetime.now() < (self.token_expires_at - timedelta(minutes=5))
    
    async def ensure_valid_token(self) -> bool:
        """确保有有效的token"""
        if self.is_token_valid():
            return True
        
        if self.refresh_token and self.config.get('auto_refresh'):
            return await self.refresh_access_token()
        
        logger.error("Token已过期且无法自动刷新，请重新授权")
        return False
    
    async def refresh_access_token(self) -> bool:
        """刷新access token"""
        logger.info("正在刷新Access Token...")
        
        url = f"{self.auth_base}/token"
        data = {
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                self.refresh_token = result.get('refresh_token', self.refresh_token)
                
                # 更新过期时间
                expires_in = result.get('expires_in', 7200)  # 默认2小时
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # 保存到配置文件
                self._save_config()
                
                self.stats['token_refreshes'] += 1
                logger.info("✅ Token刷新成功")
                return True
            else:
                logger.error(f"Token刷新失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Token刷新异常: {e}")
            return False
    
    async def download_document_as_csv(self, file_id: str, save_path: str = None) -> Tuple[bool, str]:
        """
        下载文档为CSV格式
        
        Args:
            file_id: 腾讯文档ID
            save_path: 保存路径，如果为None则自动生成
            
        Returns:
            (成功标志, 文件路径或错误信息)
        """
        # 确保token有效
        if not await self.ensure_valid_token():
            return False, "Token无效"
        
        self.stats['api_calls'] += 1
        
        try:
            # Step 1: 发起异步导出请求
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            export_response = requests.post(
                f"{self.api_base}/drive/v2/files/{file_id}/async-export",
                headers=headers,
                json={'exportType': 'csv'},
                timeout=30
            )
            
            if export_response.status_code != 200:
                error_msg = f"导出请求失败: {export_response.status_code}"
                logger.error(error_msg)
                self.stats['failed_downloads'] += 1
                return False, error_msg
            
            operation_id = export_response.json().get('operationID')
            logger.info(f"导出任务已创建: {operation_id}")
            
            # Step 2: 轮询导出进度
            download_url = None
            for attempt in range(30):  # 最多等待60秒
                await asyncio.sleep(2)
                
                progress_response = requests.get(
                    f"{self.api_base}/drive/v2/files/{file_id}/export-progress",
                    headers=headers,
                    params={'operationID': operation_id},
                    timeout=10
                )
                
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()['data']
                    progress = progress_data.get('progress', 0)
                    
                    logger.info(f"导出进度: {progress}%")
                    
                    if progress == 100:
                        download_url = progress_data.get('url')
                        break
            
            if not download_url:
                error_msg = "导出超时"
                logger.error(error_msg)
                self.stats['failed_downloads'] += 1
                return False, error_msg
            
            # Step 3: 下载文件
            csv_response = requests.get(download_url, timeout=60)
            
            # 生成保存路径
            if not save_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                save_path = f'/root/projects/tencent-doc-manager/downloads/api_download_{file_id}_{timestamp}.csv'
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 保存文件
            with open(save_path, 'wb') as f:
                f.write(csv_response.content)
            
            self.stats['successful_downloads'] += 1
            logger.info(f"✅ 文档已下载: {save_path}")
            return True, save_path
            
        except Exception as e:
            error_msg = f"下载异常: {str(e)}"
            logger.error(error_msg)
            self.stats['failed_downloads'] += 1
            return False, error_msg
    
    async def batch_download_documents(self, doc_list: List[Dict]) -> List[Dict]:
        """
        批量下载文档
        
        Args:
            doc_list: 文档列表，每个元素包含 file_id 和 name
            
        Returns:
            下载结果列表
        """
        results = []
        
        for doc in doc_list:
            file_id = doc.get('file_id')
            name = doc.get('name', 'unknown')
            
            logger.info(f"正在下载: {name} ({file_id})")
            
            success, result = await self.download_document_as_csv(file_id)
            
            results.append({
                'file_id': file_id,
                'name': name,
                'success': success,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
            # 避免频率限制
            await asyncio.sleep(1)
        
        return results
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'token_valid': self.is_token_valid(),
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None
        }


class HybridDownloader:
    """
    混合下载器 - 支持API和Cookie两种方式
    优先使用API，失败时降级到Cookie
    """
    
    def __init__(self):
        self.api_client = TencentDocsAPIClient()
        self.cookie_downloader = None  # 延迟加载
        
    def _get_cookie_downloader(self):
        """延迟加载Cookie下载器"""
        if not self.cookie_downloader:
            try:
                from stability_enhanced_downloader import StabilityEnhancedDownloader
                self.cookie_downloader = StabilityEnhancedDownloader()
            except ImportError:
                logger.warning("Cookie下载器不可用")
        return self.cookie_downloader
    
    async def download(self, url_or_id: str, use_api_first: bool = True) -> Dict:
        """
        智能下载 - 自动选择最佳方式
        
        Args:
            url_or_id: 文档URL或ID
            use_api_first: 是否优先使用API
            
        Returns:
            下载结果
        """
        # 从URL提取文档ID
        file_id = self._extract_file_id(url_or_id)
        
        if use_api_first and self.api_client.is_token_valid():
            # 尝试API方式
            logger.info("使用API方式下载...")
            success, result = await self.api_client.download_document_as_csv(file_id)
            
            if success:
                return {
                    'success': True,
                    'method': 'api',
                    'file_path': result,
                    'file_id': file_id
                }
        
        # 降级到Cookie方式
        logger.info("降级到Cookie方式下载...")
        cookie_downloader = self._get_cookie_downloader()
        
        if cookie_downloader:
            try:
                result = await cookie_downloader.download_with_stability(
                    url_or_id, 
                    format_type='csv'
                )
                return {
                    'success': result.get('success', False),
                    'method': 'cookie',
                    'file_path': result.get('file_path'),
                    'file_id': file_id
                }
            except Exception as e:
                logger.error(f"Cookie下载失败: {e}")
        
        return {
            'success': False,
            'method': 'none',
            'error': '所有下载方式均失败',
            'file_id': file_id
        }
    
    def _extract_file_id(self, url_or_id: str) -> str:
        """从URL提取文档ID"""
        if url_or_id.startswith('http'):
            # 从URL提取ID，例如: https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN
            parts = url_or_id.split('/')
            for part in parts:
                if part.startswith('D') and len(part) > 10:
                    return part.split('?')[0]  # 去除查询参数
        return url_or_id


# 测试代码
async def test_api_client():
    """测试API客户端"""
    client = TencentDocsAPIClient()
    
    # 测试下载单个文档
    success, result = await client.download_document_as_csv('DWEVjZndkR2xVSWJN')
    print(f"下载结果: {success}, {result}")
    
    # 获取统计信息
    print(f"统计信息: {client.get_stats()}")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_api_client())