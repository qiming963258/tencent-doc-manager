#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的自动下载器 - 基于现有Cookie方案优化
无需浏览器，直接HTTP请求，适合定时任务
"""

import requests
import json
import time
import schedule
import os
import logging
from datetime import datetime
import random
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAutomatedDownloader:
    """
    简化自动下载器
    基于HTTP请求，适合服务器部署
    """
    
    def __init__(self):
        self.config_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
        self.download_dir = "/root/projects/tencent-doc-manager/scheduled_downloads"
        self.processed_dir = "/root/projects/tencent-doc-manager/processed_files"
        
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        
        self.session = requests.Session()
        self.setup_session()
        
        # 文档配置
        self.documents = [
            {
                "id": "DWEVjZndkR2xVSWJN",
                "name": "测试版本-小红书部门",
                "interval": 3600  # 每小时
            },
            {
                "id": "DRFppYm15RGZ2WExN", 
                "name": "测试版本-回国销售计划表",
                "interval": 1800  # 每30分钟
            },
            {
                "id": "DRHZrS1hOS3pwRGZB",
                "name": "测试版本-出国销售计划表", 
                "interval": 3600  # 每小时
            }
        ]
        
    def setup_session(self):
        """设置请求会话"""
        # 加载Cookie
        with open(self.config_file, 'r') as f:
            cookie_data = json.load(f)
            self.cookie_str = cookie_data['current_cookies']
            
        # 设置请求头 - 模拟真实浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cookie': self.cookie_str
        })
        
    def warm_up_session(self, doc_id: str):
        """预热会话"""
        try:
            # 访问主页
            response = self.session.get("https://docs.qq.com", timeout=10)
            time.sleep(random.uniform(1, 3))
            
            # 访问文档页面
            doc_url = f"https://docs.qq.com/sheet/{doc_id}"
            response = self.session.get(doc_url, timeout=15)
            
            if response.status_code == 200:
                # 提取XSRF token
                import re
                content = response.text
                
                xsrf_match = re.search(r'xsrf["\']?\s*[:=]\s*["\']([^"\']+)', content)
                if xsrf_match:
                    self.xsrf_token = xsrf_match.group(1)
                    logger.info(f"获取XSRF Token: {self.xsrf_token[:20]}...")
                    
                return True
            return False
            
        except Exception as e:
            logger.error(f"会话预热失败: {e}")
            return False
            
    def download_document(self, doc_info: dict) -> str:
        """下载单个文档"""
        doc_id = doc_info['id']
        doc_name = doc_info['name']
        
        logger.info(f"开始下载: {doc_name}")
        
        # 预热会话
        if not self.warm_up_session(doc_id):
            logger.error("会话预热失败")
            return None
            
        # 尝试多种API端点
        endpoints = [
            f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx&t={int(time.time()*1000)}",
            f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_csv&t={int(time.time()*1000)}",
            f"https://docs.qq.com/api/export?docid={doc_id}&format=xlsx"
        ]
        
        for i, endpoint in enumerate(endpoints):
            try:
                # 添加XSRF token
                if hasattr(self, 'xsrf_token'):
                    endpoint += f"&xsrf={self.xsrf_token}"
                    
                logger.info(f"尝试端点 {i+1}: {endpoint[:50]}...")
                
                response = self.session.get(endpoint, timeout=30, stream=True)
                
                if response.status_code == 200:
                    content = response.content
                    
                    # 检查内容有效性
                    if len(content) > 1000 and not content.startswith(b'<!'):
                        # 保存文件
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        format_ext = 'xlsx' if 'xlsx' in endpoint else 'csv'
                        filename = f"{doc_name}_{timestamp}.{format_ext}"
                        filepath = os.path.join(self.download_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(content)
                            
                        # 验证文件
                        if self.validate_file(filepath, format_ext):
                            logger.info(f"✅ 下载成功: {filepath}")
                            return filepath
                        else:
                            logger.warning("文件验证失败，继续尝试其他端点")
                            os.remove(filepath)
                            
                else:
                    logger.warning(f"端点返回状态码: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"端点 {i+1} 失败: {e}")
                continue
                
        logger.error(f"所有端点都失败了: {doc_name}")
        return None
        
    def validate_file(self, filepath: str, format_type: str) -> bool:
        """验证下载的文件"""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(10)
                
            if format_type == 'xlsx':
                # Excel文件应该以PK开头（ZIP格式）
                return header.startswith(b'PK\x03\x04')
            elif format_type == 'csv':
                # CSV文件检查是否包含逗号或制表符
                with open(filepath, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    return ',' in first_line or '\t' in first_line
                    
            return True
            
        except Exception as e:
            logger.error(f"文件验证失败: {e}")
            return False
            
    def process_downloaded_file(self, filepath: str) -> str:
        """处理下载的文件"""
        if not filepath or not os.path.exists(filepath):
            return None
            
        logger.info(f"处理文件: {os.path.basename(filepath)}")
        
        try:
            # 这里集成现有的处理逻辑
            # 例如：CSV对比、热力图生成、Excel标记等
            
            # 示例：简单复制到处理目录
            processed_filename = f"processed_{os.path.basename(filepath)}"
            processed_path = os.path.join(self.processed_dir, processed_filename)
            
            import shutil
            shutil.copy2(filepath, processed_path)
            
            # 可以在这里添加实际的处理逻辑
            # self.csv_comparison(filepath)
            # self.generate_heatmap(filepath)
            # self.excel_marking(filepath)
            
            logger.info(f"✅ 处理完成: {processed_filename}")
            return processed_path
            
        except Exception as e:
            logger.error(f"文件处理失败: {e}")
            return None
            
    def upload_to_tencent_docs(self, filepath: str) -> bool:
        """上传到腾讯文档（可选）"""
        if not filepath or not os.path.exists(filepath):
            return False
            
        logger.info(f"上传文件: {os.path.basename(filepath)}")
        
        try:
            # 腾讯文档上传API
            upload_url = "https://docs.qq.com/api/upload"
            
            with open(filepath, 'rb') as f:
                files = {'file': f}
                data = {
                    'type': 'sheet',
                    'name': os.path.basename(filepath)
                }
                
                response = self.session.post(upload_url, files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        logger.info(f"✅ 上传成功: {result.get('url')}")
                        return True
                        
            return False
            
        except Exception as e:
            logger.error(f"上传失败: {e}")
            return False
            
    def cleanup_old_files(self):
        """清理旧文件"""
        try:
            for directory in [self.download_dir, self.processed_dir]:
                files = [os.path.join(directory, f) for f in os.listdir(directory)]
                files = [f for f in files if os.path.isfile(f)]
                files.sort(key=os.path.getmtime, reverse=True)
                
                # 保留最新的5个文件
                for old_file in files[5:]:
                    os.remove(old_file)
                    logger.info(f"清理旧文件: {os.path.basename(old_file)}")
                    
        except Exception as e:
            logger.error(f"清理失败: {e}")
            
    def run_download_cycle(self):
        """运行一次下载周期"""
        logger.info("🚀 开始下载周期")
        
        success_count = 0
        total_count = len(self.documents)
        
        for doc_info in self.documents:
            # 下载
            filepath = self.download_document(doc_info)
            
            if filepath:
                success_count += 1
                
                # 处理
                processed_path = self.process_downloaded_file(filepath)
                
                # 上传（可选）
                # self.upload_to_tencent_docs(processed_path)
                
                # 间隔
                time.sleep(random.uniform(5, 15))
            else:
                logger.error(f"下载失败: {doc_info['name']}")
                
        # 清理旧文件
        self.cleanup_old_files()
        
        logger.info(f"✅ 下载周期完成: {success_count}/{total_count}")
        
    def start_scheduled_downloads(self):
        """启动定时下载"""
        logger.info("="*60)
        logger.info("腾讯文档自动下载系统")
        logger.info("基于HTTP请求的轻量级解决方案")
        logger.info("="*60)
        
        # 配置定时任务
        schedule.every().hour.do(self.run_download_cycle)
        
        # 立即运行一次
        self.run_download_cycle()
        
        logger.info("定时任务已启动，每小时执行一次")
        logger.info("按 Ctrl+C 停止")
        
        # 保持运行
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("系统停止")

def create_systemd_service():
    """创建systemd服务文件"""
    service_content = """[Unit]
Description=Tencent Docs Auto Downloader
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/projects/tencent-doc-manager
ExecStart=/usr/bin/python3 /root/projects/tencent-doc-manager/simple_automated_downloader.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
"""
    
    try:
        with open("/etc/systemd/system/tencent-docs-downloader.service", "w") as f:
            f.write(service_content)
            
        print("systemd服务文件已创建")
        print("启用服务: sudo systemctl enable tencent-docs-downloader")
        print("启动服务: sudo systemctl start tencent-docs-downloader")
        print("查看状态: sudo systemctl status tencent-docs-downloader")
        
    except Exception as e:
        print(f"创建服务文件失败: {e}")

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "install-service":
        create_systemd_service()
        return
        
    downloader = SimpleAutomatedDownloader()
    downloader.start_scheduled_downloads()

if __name__ == "__main__":
    main()