#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows云服务器全自动下载方案
可以在阿里云/腾讯云Windows服务器上24小时运行
完全模拟真实用户，不会被检测
"""

import os
import time
import json
import schedule
import logging
from datetime import datetime
from pathlib import Path
import subprocess
import sys

# 尝试导入playwright
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("正在安装playwright...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WindowsCloudAutomation:
    """
    Windows云服务器自动化下载器
    特点：
    1. 使用持久化浏览器配置，保持登录状态
    2. 模拟真实用户行为，避免检测
    3. 自动重试和错误恢复
    4. 下载后自动上传到指定位置
    """
    
    def __init__(self):
        # Windows路径配置
        self.base_dir = Path("C:/TencentDocAutomation")
        self.chrome_data_dir = self.base_dir / "ChromeData"
        self.download_dir = self.base_dir / "Downloads"
        self.upload_dir = self.base_dir / "Uploads"
        self.config_file = self.base_dir / "config.json"
        
        # 创建必要的目录
        for dir_path in [self.base_dir, self.download_dir, self.upload_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # 加载配置
        self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "doc_ids": [
                "DWEVjZndkR2xVSWJN",  # 测试文档
                "DRFppYm15RGZ2WExN",
                "DRHZrS1hOS3pwRGZB"
            ],
            "download_time": "09:00",  # 每天下载时间
            "retry_times": 3,
            "upload_endpoint": "http://your-server.com/api/upload",
            "notification_webhook": "",  # 可选：钉钉/企业微信通知
            "headless": False,  # Windows服务器可以用有界面模式
            "cookie_string": ""  # 可选：预设Cookie
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"已创建默认配置文件：{self.config_file}")
            
    def setup_browser(self):
        """
        设置持久化浏览器
        使用用户配置文件保持登录状态
        """
        logger.info("启动浏览器...")
        
        with sync_playwright() as p:
            # 使用持久化上下文，保持登录状态
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(self.chrome_data_dir),
                headless=self.config['headless'],
                channel='chrome',  # 使用系统Chrome
                downloads_path=str(self.download_dir),
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--start-maximized'
                ],
                # 模拟真实浏览器
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            
            return browser
            
    def check_login_status(self, page):
        """检查登录状态"""
        try:
            page.goto("https://docs.qq.com", wait_until='networkidle', timeout=30000)
            
            # 检查是否有用户头像（已登录标志）
            user_avatar = page.locator('img[class*="avatar"]').first
            if user_avatar.is_visible(timeout=5000):
                logger.info("✅ 已登录")
                return True
                
            # 检查是否有登录按钮
            login_button = page.locator('button:has-text("登录")').first
            if login_button.is_visible(timeout=5000):
                logger.warning("❌ 未登录，需要手动登录")
                return False
                
        except Exception as e:
            logger.error(f"检查登录状态失败：{e}")
            
        return False
        
    def manual_login(self, browser):
        """手动登录流程"""
        logger.info("请手动登录腾讯文档...")
        logger.info("1. 在打开的浏览器中登录")
        logger.info("2. 登录成功后，按Enter继续")
        
        if browser.pages:
            page = browser.pages[0]
        else:
            page = browser.new_page()
            
        page.goto("https://docs.qq.com")
        
        # 等待用户手动登录
        input("登录完成后按Enter继续...")
        
        # 保存登录状态
        logger.info("✅ 登录状态已保存")
        
    def download_document(self, browser, doc_id):
        """
        下载单个文档
        使用真实的用户行为模式
        """
        logger.info(f"开始下载文档：{doc_id}")
        
        try:
            page = browser.new_page()
            
            # 访问文档
            doc_url = f"https://docs.qq.com/sheet/{doc_id}"
            page.goto(doc_url, wait_until='networkidle')
            
            # 模拟用户阅读（重要！避免检测）
            time.sleep(3)  # 先等待页面完全加载
            page.mouse.wheel(0, 300)  # 向下滚动
            time.sleep(1)
            page.mouse.wheel(0, -150)  # 向上滚动一点
            time.sleep(2)
            
            # 查找导出按钮
            export_button = None
            for selector in ['button:has-text("导出")', 
                           'button:has-text("下载")',
                           '[aria-label*="导出"]',
                           'button:has-text("更多")']:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        export_button = btn
                        break
                except:
                    continue
                    
            if not export_button:
                logger.warning(f"未找到导出按钮：{doc_id}")
                page.close()
                return False
                
            # 点击导出按钮
            export_button.click()
            time.sleep(2)
            
            # 选择Excel格式
            excel_option = None
            for selector in ['text="Excel(.xlsx)"', 
                           'text="Microsoft Excel"',
                           '[data-format="xlsx"]']:
                try:
                    opt = page.locator(selector).first
                    if opt.is_visible(timeout=2000):
                        excel_option = opt
                        break
                except:
                    continue
                    
            if excel_option:
                # 监听下载
                with page.expect_download(timeout=30000) as download_info:
                    excel_option.click()
                    
                download = download_info.value
                
                # 保存文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"doc_{doc_id}_{timestamp}.xlsx"
                filepath = self.download_dir / filename
                download.save_as(str(filepath))
                
                logger.info(f"✅ 下载成功：{filename}")
                
                # 验证文件
                if filepath.exists() and filepath.stat().st_size > 1000:
                    page.close()
                    return str(filepath)
                    
            page.close()
            return False
            
        except Exception as e:
            logger.error(f"下载失败 {doc_id}：{e}")
            if 'page' in locals():
                page.close()
            return False
            
    def upload_file(self, filepath):
        """
        上传文件到服务器
        """
        try:
            import requests
            
            with open(filepath, 'rb') as f:
                files = {'file': f}
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'source': 'windows_cloud',
                    'filename': os.path.basename(filepath)
                }
                
                response = requests.post(
                    self.config['upload_endpoint'],
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ 上传成功：{filepath}")
                    return True
                else:
                    logger.error(f"上传失败：{response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"上传出错：{e}")
            return False
            
    def send_notification(self, message):
        """发送通知（钉钉/企业微信）"""
        if not self.config.get('notification_webhook'):
            return
            
        try:
            import requests
            
            # 钉钉webhook
            if 'dingtalk' in self.config['notification_webhook']:
                data = {
                    "msgtype": "text",
                    "text": {"content": f"【腾讯文档下载】{message}"}
                }
            # 企业微信webhook
            else:
                data = {
                    "msgtype": "text",
                    "text": {"content": f"【腾讯文档下载】{message}"}
                }
                
            requests.post(self.config['notification_webhook'], json=data)
            
        except Exception as e:
            logger.error(f"发送通知失败：{e}")
            
    def daily_task(self):
        """
        每日定时任务
        """
        logger.info("="*60)
        logger.info(f"开始执行每日任务 - {datetime.now()}")
        logger.info("="*60)
        
        success_count = 0
        fail_count = 0
        
        # 启动浏览器
        browser = self.setup_browser()
        
        try:
            # 检查登录状态
            if browser.pages:
                page = browser.pages[0]
            else:
                page = browser.new_page()
                
            if not self.check_login_status(page):
                self.manual_login(browser)
                
            # 下载所有文档
            for doc_id in self.config['doc_ids']:
                retry = 0
                while retry < self.config['retry_times']:
                    filepath = self.download_document(browser, doc_id)
                    
                    if filepath:
                        # 上传文件
                        if self.upload_file(filepath):
                            success_count += 1
                        break
                    else:
                        retry += 1
                        if retry < self.config['retry_times']:
                            logger.info(f"重试 {retry}/{self.config['retry_times']}...")
                            time.sleep(10)
                        else:
                            fail_count += 1
                            
                # 文档之间的间隔
                time.sleep(10)
                
        finally:
            browser.close()
            
        # 发送通知
        message = f"任务完成！成功：{success_count}，失败：{fail_count}"
        logger.info(message)
        self.send_notification(message)
        
    def run_once(self):
        """立即执行一次"""
        self.daily_task()
        
    def run_scheduled(self):
        """按计划执行"""
        schedule_time = self.config['download_time']
        schedule.every().day.at(schedule_time).do(self.daily_task)
        
        logger.info(f"已设置每日 {schedule_time} 执行任务")
        logger.info("按Ctrl+C停止...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def create_windows_service():
    """
    创建Windows服务（可选）
    使用nssm工具将Python脚本注册为Windows服务
    """
    service_config = """
# 安装为Windows服务的步骤：

1. 下载NSSM（Non-Sucking Service Manager）
   https://nssm.cc/download

2. 以管理员身份运行命令提示符

3. 安装服务：
   nssm install TencentDocDownloader "C:\\Python39\\python.exe" "C:\\TencentDocAutomation\\windows_cloud_automation.py"

4. 配置服务：
   nssm set TencentDocDownloader AppDirectory "C:\\TencentDocAutomation"
   nssm set TencentDocDownloader DisplayName "腾讯文档自动下载服务"
   nssm set TencentDocDownloader Description "自动下载腾讯文档并上传到服务器"
   nssm set TencentDocDownloader Start SERVICE_AUTO_START

5. 启动服务：
   nssm start TencentDocDownloader

6. 查看状态：
   nssm status TencentDocDownloader
"""
    print(service_config)

def main():
    """主函数"""
    print("="*60)
    print("腾讯文档Windows云服务器自动化系统")
    print("="*60)
    
    automation = WindowsCloudAutomation()
    
    print("\n请选择运行模式：")
    print("1. 立即执行一次")
    print("2. 定时执行（每天）")
    print("3. 安装为Windows服务")
    
    choice = input("\n请输入选项 (1/2/3): ")
    
    if choice == "1":
        automation.run_once()
    elif choice == "2":
        automation.run_scheduled()
    elif choice == "3":
        create_windows_service()
    else:
        print("无效选项")

if __name__ == "__main__":
    main()