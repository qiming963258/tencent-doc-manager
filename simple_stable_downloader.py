#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单稳定的下载器 - 回归本质
您说得对：之前能成功，现在也一定能！
关键是做得更像真实用户
"""

import os
import time
import json
import random
import requests
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleStableDownloader:
    """
    简单稳定的下载方案
    核心：模拟真实用户行为，不触发任何检测
    """
    
    def __init__(self):
        self.cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
        self.download_dir = "/root/projects/tencent-doc-manager/stable_downloads"
        os.makedirs(self.download_dir, exist_ok=True)
        self.session = requests.Session()
        self.setup_session()
        
    def setup_session(self):
        """设置真实的会话"""
        # 加载Cookie
        with open(self.cookie_file, 'r') as f:
            cookie_data = json.load(f)
            self.cookie_str = cookie_data['current_cookies']
        
        # 设置真实的请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'sec-ch-ua': '"Google Chrome";v="120", "Chromium";v="120", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1'
        })
        
        # 设置Cookie
        self.session.headers['Cookie'] = self.cookie_str
        
    def warm_up_session(self, doc_id: str):
        """
        预热会话 - 像真实用户一样先访问页面
        这是关键：建立完整的会话上下文
        """
        doc_url = f"https://docs.qq.com/sheet/{doc_id}"
        
        logger.info("预热会话...")
        
        # 1. 先访问主页（建立会话）
        try:
            response = self.session.get("https://docs.qq.com", timeout=10)
            logger.info(f"访问主页: {response.status_code}")
            time.sleep(random.uniform(1, 2))
        except:
            pass
        
        # 2. 访问文档页面（加载必要的token）
        response = self.session.get(doc_url, timeout=15)
        logger.info(f"访问文档页面: {response.status_code}")
        
        if response.status_code == 200:
            # 从页面提取必要的参数
            content = response.text
            
            # 提取各种可能的token
            import re
            
            # XSRF Token
            xsrf_match = re.search(r'xsrf["\']?\s*[:=]\s*["\']([^"\']+)', content)
            if xsrf_match:
                self.xsrf_token = xsrf_match.group(1)
                logger.info(f"找到XSRF Token: {self.xsrf_token[:20]}...")
            
            # Session ID
            sid_match = re.search(r'sessionId["\']?\s*[:=]\s*["\']([^"\']+)', content)
            if sid_match:
                self.session_id = sid_match.group(1)
                logger.info(f"找到Session ID: {self.session_id[:20]}...")
            
            return True
        
        return False
        
    def download_with_retry(self, doc_id: str, format_type: str = "xlsx"):
        """
        带重试的下载
        关键：每次失败后调整策略
        """
        max_retries = 3
        strategies = [
            self.strategy_direct_api,
            self.strategy_with_referer,
            self.strategy_with_full_context
        ]
        
        for attempt in range(max_retries):
            logger.info(f"\n尝试 {attempt + 1}/{max_retries}")
            
            # 使用不同的策略
            strategy = strategies[min(attempt, len(strategies)-1)]
            result = strategy(doc_id, format_type)
            
            if result:
                return result
            
            # 失败后等待（递增等待时间）
            wait_time = (attempt + 1) * 5 + random.uniform(0, 5)
            logger.info(f"等待 {wait_time:.1f} 秒后重试...")
            time.sleep(wait_time)
        
        return None
        
    def strategy_direct_api(self, doc_id: str, format_type: str):
        """策略1：直接API调用"""
        logger.info("策略1: 直接API调用")
        
        # 构建下载URL
        timestamp = int(time.time() * 1000)
        download_url = f"https://docs.qq.com/dop-api/opendoc"
        
        params = {
            'id': doc_id,
            'type': f'export_{format_type}',
            't': timestamp,
            'download': '1',
            'normal': '1'
        }
        
        # 如果有XSRF token，添加它
        if hasattr(self, 'xsrf_token'):
            params['xsrf'] = self.xsrf_token
        
        try:
            response = self.session.get(download_url, params=params, timeout=30, stream=True)
            
            if response.status_code == 200:
                return self.save_response(response, doc_id, format_type)
            else:
                logger.warning(f"API返回: {response.status_code}")
                
        except Exception as e:
            logger.error(f"策略1失败: {e}")
            
        return None
        
    def strategy_with_referer(self, doc_id: str, format_type: str):
        """策略2：带Referer的请求"""
        logger.info("策略2: 带完整Referer")
        
        # 先预热会话
        self.warm_up_session(doc_id)
        
        # 设置Referer
        self.session.headers['Referer'] = f'https://docs.qq.com/sheet/{doc_id}'
        
        # 使用不同的端点
        endpoints = [
            f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_{format_type}",
            f"https://docs.qq.com/sheet/{doc_id}/export?format={format_type}",
            f"https://docs.qq.com/api/export?docid={doc_id}&format={format_type}"
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(endpoint, timeout=30, stream=True)
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    # 检查是否是二进制文件
                    if 'application' in content_type or len(response.content) > 1000:
                        return self.save_response(response, doc_id, format_type)
            except:
                continue
                
        return None
        
    def strategy_with_full_context(self, doc_id: str, format_type: str):
        """策略3：完整上下文请求"""
        logger.info("策略3: 完整会话上下文")
        
        # 完整的会话流程
        self.warm_up_session(doc_id)
        time.sleep(random.uniform(2, 4))
        
        # 添加Ajax头部
        self.session.headers.update({
            'X-Requested-With': 'XMLHttpRequest',
            'X-XSRF-TOKEN': getattr(self, 'xsrf_token', ''),
        })
        
        # 构建请求
        timestamp = int(time.time() * 1000)
        url = "https://docs.qq.com/dop-api/opendoc"
        
        # 完整的参数集
        params = {
            'id': doc_id,
            'type': f'export_{format_type}',
            't': timestamp,
            'xsrf': getattr(self, 'xsrf_token', ''),
            'sid': getattr(self, 'session_id', ''),
            'uid': self.extract_uid_from_cookie(),
            'utype': 'qq',
            'download': '1',
            'normal': '1',
            'outputformat': format_type,
            '_': timestamp
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30, stream=True)
            if response.status_code == 200:
                return self.save_response(response, doc_id, format_type)
        except Exception as e:
            logger.error(f"策略3失败: {e}")
            
        return None
        
    def extract_uid_from_cookie(self):
        """从Cookie提取UID"""
        import re
        uid_match = re.search(r'uid=(\d+)', self.cookie_str)
        if uid_match:
            return uid_match.group(1)
        return ''
        
    def save_response(self, response, doc_id: str, format_type: str):
        """保存响应内容"""
        content = response.content
        
        # 检查内容
        if len(content) < 100:
            logger.warning("响应内容太小，可能不是有效文件")
            return None
            
        # 检查是否是HTML错误页面
        if content[:100].lower().startswith(b'<!doctype') or b'<html' in content[:100]:
            logger.warning("响应是HTML页面，不是文件")
            return None
            
        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"doc_{doc_id}_{timestamp}.{format_type}"
        filepath = os.path.join(self.download_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(content)
            
        logger.info(f"✅ 文件已保存: {filepath}")
        logger.info(f"文件大小: {len(content)} bytes")
        
        # 验证文件格式
        with open(filepath, 'rb') as f:
            header = f.read(4)
            
        if format_type == 'xlsx' and header == b'PK\x03\x04':
            logger.info("✅ 确认是真正的Excel文件!")
            return filepath
        elif format_type == 'csv' and (b',' in content[:1000] or b'\t' in content[:1000]):
            logger.info("✅ 看起来是CSV文件")
            return filepath
        elif b'text\ntext' in content[:20]:
            logger.info("⚠️ 是EJS格式，需要进一步处理")
            # 但至少我们拿到了数据！
            return filepath
        else:
            logger.warning(f"未知格式: {header}")
            return filepath

def main():
    """主函数"""
    downloader = SimpleStableDownloader()
    
    logger.info("="*60)
    logger.info("简单稳定下载器")
    logger.info("回归本质：像真实用户一样下载")
    logger.info("="*60)
    
    # 测试文档
    test_docs = [
        "DWEVjZndkR2xVSWJN",  # 测试版本-小红书部门
    ]
    
    for doc_id in test_docs:
        logger.info(f"\n下载文档: {doc_id}")
        logger.info("-"*40)
        
        # 先预热会话
        if downloader.warm_up_session(doc_id):
            # 尝试下载
            result = downloader.download_with_retry(doc_id, "xlsx")
            
            if result:
                logger.info(f"\n✅ 下载成功: {result}")
            else:
                logger.info("\n❌ 下载失败")
                
                # 尝试CSV格式
                logger.info("\n尝试CSV格式...")
                result = downloader.download_with_retry(doc_id, "csv")
                if result:
                    logger.info(f"\n✅ CSV下载成功: {result}")
        
        # 人性化的间隔
        time.sleep(random.uniform(5, 10))
    
    logger.info("\n" + "="*60)
    logger.info("如果自动下载失败，请考虑：")
    logger.info("1. 更新Cookie（从浏览器复制最新的）")
    logger.info("2. 使用real_browser_automation.py控制真实浏览器")
    logger.info("3. 在浏览器中手动下载一次，然后立即运行脚本")
    logger.info("="*60)

if __name__ == "__main__":
    main()