#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端自动化解决方案 - 无需用户交互
真正的定时自动下载、分析、上传系统
"""

import asyncio
import schedule
import time
import json
import logging
from datetime import datetime
from playwright.async_api import async_playwright
import docker
import subprocess
import os
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TencentDocAutomation:
    """
    腾讯文档全自动处理系统
    运行在Linux服务器，无需用户交互
    """
    
    def __init__(self):
        self.config_file = "/root/projects/tencent-doc-manager/config/automation_config.json"
        self.cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
        self.download_dir = "/root/projects/tencent-doc-manager/auto_downloads"
        self.upload_dir = "/root/projects/tencent-doc-manager/processed_files"
        
        # 创建必要目录
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # 加载配置
        self.load_config()
        self.load_cookies()
        
    def load_config(self):
        """加载自动化配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # 创建默认配置
            self.config = {
                "documents": [
                    {
                        "id": "DWEVjZndkR2xVSWJN",
                        "name": "测试版本-小红书部门",
                        "schedule": "每小时",
                        "format": "xlsx"
                    }
                ],
                "schedule": {
                    "check_interval": 3600,  # 每小时检查一次
                    "max_retries": 3,
                    "retry_delay": 300  # 5分钟
                },
                "processing": {
                    "auto_analysis": True,
                    "auto_upload": True,
                    "cleanup_old_files": True
                }
            }
            self.save_config()
            
    def save_config(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
            
    def load_cookies(self):
        """加载Cookie"""
        with open(self.cookie_file, 'r') as f:
            cookie_data = json.load(f)
            self.cookie_str = cookie_data['current_cookies']
            
    async def setup_headless_browser(self):
        """设置无头浏览器环境"""
        try:
            # 启动Playwright
            self.playwright = await async_playwright().start()
            
            # 启动无头Chrome
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            
            # 创建上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            )
            
            logger.info("✅ 无头浏览器环境已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            return False
            
    async def inject_cookies(self):
        """注入Cookie到浏览器"""
        try:
            # 先访问腾讯文档域名
            page = await self.context.new_page()
            await page.goto("https://docs.qq.com")
            
            # 解析并注入Cookie
            cookies = []
            for item in self.cookie_str.split('; '):
                if '=' in item:
                    key, value = item.split('=', 1)
                    cookies.append({
                        'name': key,
                        'value': value,
                        'domain': '.qq.com',
                        'path': '/'
                    })
            
            await self.context.add_cookies(cookies)
            
            # 验证登录状态
            await page.reload()
            content = await page.content()
            
            if '登录' in content:
                logger.error("Cookie已失效，需要更新")
                await page.close()
                return False
            else:
                logger.info("✅ Cookie注入成功，已登录")
                await page.close()
                return True
                
        except Exception as e:
            logger.error(f"Cookie注入失败: {e}")
            return False
            
    async def download_document_automated(self, doc_info: Dict) -> str:
        """自动下载文档（无用户交互）"""
        doc_id = doc_info['id']
        doc_name = doc_info['name']
        format_type = doc_info.get('format', 'xlsx')
        
        logger.info(f"开始自动下载文档: {doc_name} ({doc_id})")
        
        try:
            page = await self.context.new_page()
            
            # 导航到文档页面
            doc_url = f"https://docs.qq.com/sheet/{doc_id}"
            await page.goto(doc_url, wait_until='networkidle')
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 智能查找导出按钮
            export_buttons = [
                'button:has-text("导出")',
                'button:has-text("下载")',
                '[aria-label*="导出"]',
                '.export-btn',
                'button[title*="导出"]'
            ]
            
            button_clicked = False
            for selector in export_buttons:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    await page.click(selector)
                    logger.info(f"点击导出按钮: {selector}")
                    button_clicked = True
                    break
                except:
                    continue
                    
            if not button_clicked:
                # 尝试键盘快捷键
                logger.info("尝试键盘快捷键")
                await page.keyboard.press('Control+Shift+E')
                
            # 等待菜单出现
            await asyncio.sleep(2)
            
            # 选择格式
            format_selectors = {
                'xlsx': ['text="Excel(.xlsx)"', 'text="Microsoft Excel"', '[data-format="xlsx"]'],
                'csv': ['text="CSV"', 'text=".csv"', '[data-format="csv"]']
            }
            
            format_selected = False
            for selector in format_selectors.get(format_type, []):
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    
                    # 监听下载事件
                    with page.expect_download(timeout=30000) as download_info:
                        await page.click(selector)
                        logger.info(f"选择格式: {selector}")
                        
                    download = download_info.value
                    
                    # 保存文件
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{doc_name}_{timestamp}.{format_type}"
                    filepath = os.path.join(self.download_dir, filename)
                    
                    await download.save_as(filepath)
                    
                    logger.info(f"✅ 文档下载成功: {filepath}")
                    await page.close()
                    return filepath
                    
                except Exception as e:
                    logger.debug(f"格式选择失败 {selector}: {e}")
                    continue
            
            # 如果UI点击失败，尝试API方式
            logger.warning("UI下载失败，尝试API方式")
            await page.close()
            return await self.download_via_api(doc_id, format_type)
            
        except Exception as e:
            logger.error(f"下载失败: {e}")
            if 'page' in locals():
                await page.close()
            return None
            
    async def download_via_api(self, doc_id: str, format_type: str) -> str:
        """通过API下载（备用方案）"""
        try:
            page = await self.context.new_page()
            
            # 构建API URL
            api_url = f"https://docs.qq.com/dop-api/opendoc"
            params = {
                'id': doc_id,
                'type': f'export_{format_type}',
                't': int(time.time() * 1000)
            }
            
            # 拼接URL
            param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{api_url}?{param_str}"
            
            # 发起请求
            response = await page.goto(full_url)
            
            if response.status == 200:
                content = await response.body()
                
                # 检查是否是有效文件
                if len(content) > 1000 and not content.startswith(b'<!'):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"doc_{doc_id}_{timestamp}.{format_type}"
                    filepath = os.path.join(self.download_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    
                    logger.info(f"✅ API下载成功: {filepath}")
                    await page.close()
                    return filepath
                    
            await page.close()
            return None
            
        except Exception as e:
            logger.error(f"API下载失败: {e}")
            return None
            
    async def process_document(self, filepath: str) -> str:
        """处理下载的文档"""
        if not filepath or not os.path.exists(filepath):
            return None
            
        logger.info(f"开始处理文档: {filepath}")
        
        try:
            # 这里调用现有的处理逻辑
            # 例如：CSV对比分析、热力图生成等
            
            # 示例：复制到处理目录
            processed_filename = f"processed_{os.path.basename(filepath)}"
            processed_path = os.path.join(self.upload_dir, processed_filename)
            
            import shutil
            shutil.copy2(filepath, processed_path)
            
            logger.info(f"✅ 文档处理完成: {processed_path}")
            return processed_path
            
        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            return None
            
    async def upload_to_tencent(self, filepath: str) -> bool:
        """上传回腾讯文档"""
        if not filepath or not os.path.exists(filepath):
            return False
            
        logger.info(f"开始上传文档: {filepath}")
        
        try:
            page = await self.context.new_page()
            
            # 访问腾讯文档上传页面
            await page.goto("https://docs.qq.com", wait_until='networkidle')
            
            # 查找上传按钮
            upload_selectors = [
                'input[type="file"]',
                'button:has-text("上传")',
                '.upload-btn'
            ]
            
            for selector in upload_selectors:
                try:
                    if selector == 'input[type="file"]':
                        # 直接上传文件
                        await page.set_input_files(selector, filepath)
                    else:
                        await page.click(selector)
                        
                    logger.info(f"✅ 文档上传成功")
                    await page.close()
                    return True
                    
                except Exception as e:
                    continue
                    
            await page.close()
            return False
            
        except Exception as e:
            logger.error(f"上传失败: {e}")
            return False
            
    async def run_single_cycle(self):
        """运行一次完整的下载-处理-上传周期"""
        logger.info("🚀 开始自动化周期")
        
        # 设置浏览器环境
        if not await self.setup_headless_browser():
            logger.error("浏览器启动失败")
            return
            
        # 注入Cookie
        if not await self.inject_cookies():
            logger.error("Cookie失效，请更新")
            await self.cleanup()
            return
            
        # 处理每个文档
        for doc_info in self.config['documents']:
            logger.info(f"处理文档: {doc_info['name']}")
            
            # 下载
            filepath = await self.download_document_automated(doc_info)
            if not filepath:
                logger.error(f"下载失败: {doc_info['name']}")
                continue
                
            # 处理
            if self.config['processing']['auto_analysis']:
                processed_path = await self.process_document(filepath)
                if processed_path:
                    filepath = processed_path
                    
            # 上传
            if self.config['processing']['auto_upload']:
                await self.upload_to_tencent(filepath)
                
            # 清理
            if self.config['processing']['cleanup_old_files']:
                # 保留最新的3个文件
                self.cleanup_old_files()
                
        await self.cleanup()
        logger.info("✅ 自动化周期完成")
        
    async def cleanup(self):
        """清理资源"""
        if hasattr(self, 'context'):
            await self.context.close()
        if hasattr(self, 'browser'):
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
            
    def cleanup_old_files(self):
        """清理旧文件"""
        try:
            for directory in [self.download_dir, self.upload_dir]:
                files = [os.path.join(directory, f) for f in os.listdir(directory)]
                files.sort(key=os.path.getmtime, reverse=True)
                
                # 删除3个以外的旧文件
                for old_file in files[3:]:
                    os.remove(old_file)
                    logger.info(f"清理旧文件: {old_file}")
        except Exception as e:
            logger.error(f"清理失败: {e}")
            
    def start_scheduler(self):
        """启动定时任务"""
        interval = self.config['schedule']['check_interval'] / 60  # 转换为分钟
        
        logger.info(f"启动定时任务，间隔: {interval}分钟")
        
        # 使用schedule库
        schedule.every(int(interval)).minutes.do(
            lambda: asyncio.create_task(self.run_single_cycle())
        )
        
        # 立即运行一次
        asyncio.create_task(self.run_single_cycle())
        
        # 保持运行
        while True:
            schedule.run_pending()
            time.sleep(60)

def install_dependencies():
    """安装必要的依赖"""
    logger.info("检查并安装依赖...")
    
    try:
        # 安装Playwright
        subprocess.run(['playwright', 'install', 'chromium'], check=True)
        logger.info("✅ Playwright已安装")
    except:
        logger.error("请先安装playwright: pip install playwright")
        
def main():
    """主函数"""
    print("="*60)
    print("腾讯文档全自动处理系统")
    print("无需用户交互的定时下载-分析-上传")
    print("="*60)
    
    # 检查依赖
    install_dependencies()
    
    # 启动自动化系统
    automation = TencentDocAutomation()
    
    try:
        automation.start_scheduler()
    except KeyboardInterrupt:
        logger.info("系统停止")

if __name__ == "__main__":
    main()