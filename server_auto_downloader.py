#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器端全自动下载器
适用于Linux服务器定时任务
使用虚拟显示 + undetected-chromedriver
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
import subprocess

# 安装依赖
def install_requirements():
    """自动安装依赖"""
    requirements = [
        'selenium',
        'undetected-chromedriver',
        'pyvirtualdisplay'
    ]
    
    for package in requirements:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"安装 {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_requirements()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from pyvirtualdisplay import Display

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/tencent_doc_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServerAutoDownloader:
    """服务器端自动下载器"""
    
    def __init__(self):
        self.config = self.load_config()
        self.driver = None
        self.display = None
        self.download_dir = Path(self.config['download_dir'])
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
    def load_config(self):
        """加载配置"""
        config_file = Path(__file__).parent / 'server_config.json'
        
        if not config_file.exists():
            # 创建默认配置
            default_config = {
                "cookie_string": "",  # 从浏览器复制
                "download_dir": "/root/projects/tencent-doc-manager/downloads",
                "upload_endpoint": "http://your-server.com/api/upload",
                "use_virtual_display": True,
                "headless": False,  # 使用虚拟显示时设为False
                "filter_settings": {
                    "owner": "my_documents",  # my_documents | all | others
                    "time_range": "recent_month"  # all | recent_week | recent_month
                }
            }
            
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"已创建配置文件: {config_file}")
            logger.info("请编辑配置文件添加Cookie后重新运行")
            sys.exit(1)
            
        with open(config_file) as f:
            return json.load(f)
            
    def setup_virtual_display(self):
        """设置虚拟显示（Linux服务器）"""
        if self.config.get('use_virtual_display'):
            logger.info("启动虚拟显示...")
            self.display = Display(visible=0, size=(1920, 1080))
            self.display.start()
            logger.info("✅ 虚拟显示已启动")
            
    def setup_driver(self):
        """设置隐形浏览器"""
        logger.info("设置浏览器...")
        
        options = uc.ChromeOptions()
        
        # 基本配置
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # 下载配置
        prefs = {
            "download.default_directory": str(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "safebrowsing.disable_download_protection": True
        }
        options.add_experimental_option("prefs", prefs)
        
        # 如果使用headless模式
        if self.config.get('headless') and not self.config.get('use_virtual_display'):
            options.add_argument('--headless=new')
            
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)
        logger.info("✅ 浏览器设置完成")
        
    def apply_cookies(self):
        """应用Cookie"""
        logger.info("应用Cookie...")
        
        # 先访问主域名
        self.driver.get("https://docs.qq.com")
        time.sleep(2)
        
        # 解析并添加Cookie
        cookie_str = self.config['cookie_string']
        for cookie_pair in cookie_str.split('; '):
            if '=' in cookie_pair:
                key, value = cookie_pair.split('=', 1)
                cookie = {
                    'name': key,
                    'value': value,
                    'domain': '.qq.com' if key in ['RK', 'ptcz'] else '.docs.qq.com',
                    'path': '/'
                }
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
                    
        self.driver.refresh()
        time.sleep(3)
        logger.info("✅ Cookie应用完成")
        
    def auto_download_workflow(self):
        """自动下载工作流"""
        try:
            # 1. 访问主页
            logger.info("访问主页...")
            self.driver.get("https://docs.qq.com/desktop")
            time.sleep(5)
            
            # 2. 点击筛选按钮
            logger.info("点击筛选...")
            filter_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='filter-button']"))
            )
            filter_btn.click()
            time.sleep(2)
            
            # 3. 选择我所有
            logger.info("选择'我所有'...")
            my_docs = self.driver.find_element(
                By.XPATH,
                "//div[@class='dui-radio-label' and contains(text(), '我所有')]/.."
            )
            my_docs.click()
            time.sleep(1)
            
            # 4. 选择近1个月
            logger.info("选择'近1个月'...")
            recent_month = self.driver.find_element(
                By.XPATH,
                "//div[@class='dui-radio-label' and contains(text(), '近1个月')]/.."
            )
            recent_month.click()
            time.sleep(2)
            
            # 5. 滚动加载所有文档
            logger.info("加载文档列表...")
            last_count = 0
            retry = 0
            while retry < 3:
                self.driver.execute_script("""
                    const container = document.querySelector('.desktop-scrollbars-view');
                    if (container) container.scrollTop = container.scrollHeight;
                """)
                time.sleep(3)
                
                doc_count = len(self.driver.find_elements(By.CSS_SELECTOR, "[class*='file-list-item']"))
                if doc_count == last_count:
                    retry += 1
                else:
                    retry = 0
                    last_count = doc_count
                    
            logger.info(f"找到 {last_count} 个文档")
            
            # 6. 逐个下载
            docs = self.driver.find_elements(By.CSS_SELECTOR, "[class*='file-list-item']")
            success = 0
            failed = 0
            
            for i, doc in enumerate(reversed(docs), 1):
                try:
                    # 获取文档名
                    doc_name = doc.find_element(By.CSS_SELECTOR, "[class*='file-name']").text
                    logger.info(f"下载 {i}/{len(docs)}: {doc_name}")
                    
                    # 滚动到元素
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", doc)
                    time.sleep(1)
                    
                    # 右键点击
                    actions = ActionChains(self.driver)
                    actions.context_click(doc).perform()
                    time.sleep(1)
                    
                    # 点击下载
                    download_option = self.driver.find_element(
                        By.XPATH,
                        "//div[contains(@class, 'menu-item') and contains(., '下载')]"
                    )
                    download_option.click()
                    time.sleep(2)
                    
                    # 处理下载对话框
                    try:
                        confirm_btn = self.driver.find_element(
                            By.XPATH,
                            "//button[contains(text(), '确定') or contains(text(), '保存')]"
                        )
                        confirm_btn.click()
                    except:
                        pass
                        
                    success += 1
                    time.sleep(3)  # 文档间隔
                    
                    # 每10个文档休息
                    if i % 10 == 0:
                        logger.info("休息30秒...")
                        time.sleep(30)
                        
                except Exception as e:
                    logger.error(f"下载失败: {e}")
                    failed += 1
                    
            logger.info(f"✅ 下载完成: 成功 {success}, 失败 {failed}")
            
            # 7. 上传到服务器
            self.upload_files()
            
        except Exception as e:
            logger.error(f"工作流失败: {e}")
            
    def upload_files(self):
        """上传文件到服务器"""
        try:
            import requests
            
            files_uploaded = 0
            for file_path in self.download_dir.glob("*"):
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        response = requests.post(
                            self.config['upload_endpoint'],
                            files={'file': f},
                            data={'timestamp': datetime.now().isoformat()}
                        )
                        
                    if response.status_code == 200:
                        files_uploaded += 1
                        # 上传成功后移动到已处理目录
                        processed_dir = self.download_dir / 'processed'
                        processed_dir.mkdir(exist_ok=True)
                        file_path.rename(processed_dir / file_path.name)
                        
            logger.info(f"✅ 上传 {files_uploaded} 个文件")
            
        except Exception as e:
            logger.error(f"上传失败: {e}")
            
    def run(self):
        """运行主流程"""
        logger.info("="*60)
        logger.info("腾讯文档自动下载任务开始")
        logger.info("="*60)
        
        try:
            # 设置虚拟显示
            self.setup_virtual_display()
            
            # 设置浏览器
            self.setup_driver()
            
            # 应用Cookie
            self.apply_cookies()
            
            # 执行下载工作流
            self.auto_download_workflow()
            
        except Exception as e:
            logger.error(f"任务失败: {e}")
            
        finally:
            # 清理
            if self.driver:
                self.driver.quit()
            if self.display:
                self.display.stop()
                
        logger.info("="*60)
        logger.info("任务结束")
        logger.info("="*60)

def main():
    """主函数"""
    downloader = ServerAutoDownloader()
    downloader.run()

if __name__ == "__main__":
    main()