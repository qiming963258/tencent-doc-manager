#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档批量下载器 - 隐形模式
精确模拟真实用户操作流程，避免检测
基于用户提供的详细步骤实现
"""

import os
import time
import json
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 使用 undetected-chromedriver 避免检测
try:
    import undetected_chromedriver as uc
    USE_UC = True
except ImportError:
    print("安装 undetected-chromedriver 以获得最佳隐形效果...")
    print("pip install undetected-chromedriver")
    USE_UC = False

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StealthBatchDownloader:
    """
    隐形批量下载器
    通过主页筛选界面批量下载文档
    """
    
    def __init__(self, cookie_file: str = None):
        self.cookie_file = cookie_file or "/root/projects/tencent-doc-manager/config/cookies_new.json"
        self.download_dir = Path("/root/projects/tencent-doc-manager/batch_downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.driver = None
        self.wait = None
        
    def setup_driver(self, headless: bool = False):
        """设置隐形浏览器"""
        logger.info("设置隐形浏览器...")
        
        if USE_UC:
            # 使用 undetected-chromedriver
            options = uc.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # 设置下载目录
            prefs = {
                "download.default_directory": str(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            options.add_experimental_option("prefs", prefs)
            
            if not headless:
                options.add_argument('--start-maximized')
            else:
                options.add_argument('--headless=new')  # 新版headless模式
                
            # 添加更多隐形参数
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            
            # 设置真实的User-Agent
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36')
            
            self.driver = uc.Chrome(options=options)
            
        else:
            # 使用普通Selenium
            options = Options()
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 设置下载目录
            prefs = {
                "download.default_directory": str(self.download_dir),
                "download.prompt_for_download": False,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            }
            options.add_experimental_option("prefs", prefs)
            
            if headless:
                options.add_argument('--headless')
                
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36')
            
            self.driver = webdriver.Chrome(options=options)
            
            # 移除webdriver特征
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en']
                    });
                    window.chrome = {
                        runtime: {}
                    };
                    Object.defineProperty(navigator, 'permissions', {
                        get: () => ({
                            query: () => Promise.resolve({ state: 'granted' })
                        })
                    });
                '''
            })
        
        self.wait = WebDriverWait(self.driver, 20)
        logger.info("✅ 浏览器设置完成")
        
    def load_cookies(self):
        """加载Cookie"""
        logger.info("加载Cookie...")
        
        # 先访问主域名以设置Cookie
        self.driver.get("https://docs.qq.com")
        time.sleep(2)
        
        # 加载Cookie
        with open(self.cookie_file, 'r') as f:
            cookie_data = json.load(f)
            cookie_str = cookie_data['current_cookies']
            
        # 解析并添加Cookie
        for cookie_pair in cookie_str.split('; '):
            if '=' in cookie_pair:
                key, value = cookie_pair.split('=', 1)
                cookie = {
                    'name': key,
                    'value': value,
                    'domain': '.qq.com' if key in ['RK', 'ptcz'] else '.docs.qq.com',
                    'path': '/',
                    'secure': True
                }
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Cookie {key} 添加失败: {e}")
                    
        # 刷新页面以应用Cookie
        self.driver.refresh()
        time.sleep(3)
        logger.info("✅ Cookie加载完成")
        
    def human_like_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """模拟人类延迟"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
        
    def smooth_scroll(self, element):
        """平滑滚动到元素"""
        self.driver.execute_script("""
            arguments[0].scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        """, element)
        self.human_like_delay(0.5, 1)
        
    def enter_homepage(self):
        """进入主页"""
        logger.info("访问腾讯文档主页...")
        self.driver.get("https://docs.qq.com/desktop")
        self.human_like_delay(3, 5)
        
        # 检查登录状态
        try:
            # 查找用户头像或用户名元素
            user_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='user'], [class*='avatar']"))
            )
            logger.info("✅ 已登录")
        except:
            logger.warning("⚠️ 可能未登录，请检查Cookie")
            
    def click_filter_button(self):
        """点击筛选按钮"""
        logger.info("点击筛选按钮...")
        
        try:
            # 使用多种方式定位筛选按钮
            selectors = [
                "button.desktop-filter-button-inner-pc",
                "button[class*='filter-button']",
                "button:has(label:contains('筛选'))",
                "//button[contains(., '筛选')]"
            ]
            
            filter_button = None
            for selector in selectors:
                try:
                    if selector.startswith('//'):
                        filter_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        filter_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if filter_button:
                        break
                except:
                    continue
                    
            if filter_button:
                self.smooth_scroll(filter_button)
                filter_button.click()
                self.human_like_delay(1, 2)
                logger.info("✅ 筛选菜单已打开")
            else:
                logger.error("❌ 未找到筛选按钮")
                
        except Exception as e:
            logger.error(f"点击筛选按钮失败: {e}")
            
    def select_my_documents(self):
        """选择'我所有'选项"""
        logger.info("选择'我所有'...")
        
        try:
            # 方法1：通过文本定位
            my_docs_label = self.driver.find_element(
                By.XPATH, 
                "//div[@class='dui-radio-label' and text()='我所有的']"
            )
            
            # 找到对应的radio input
            radio_container = my_docs_label.find_element(By.XPATH, "..")
            radio_input = radio_container.find_element(By.CSS_SELECTOR, "input[type='radio']")
            
            # 使用JavaScript点击（更可靠）
            self.driver.execute_script("arguments[0].click();", radio_input)
            self.human_like_delay(0.5, 1)
            
            logger.info("✅ 已选择'我所有'")
            
        except Exception as e:
            logger.error(f"选择'我所有'失败: {e}")
            # 尝试备用方法
            self.select_by_structure("所有者", 2)  # 第二个选项
            
    def select_recent_month(self):
        """选择'近1个月'选项"""
        logger.info("选择'近1个月'...")
        
        try:
            # 方法1：通过文本定位
            month_label = self.driver.find_element(
                By.XPATH, 
                "//div[@class='dui-radio-label' and contains(text(), '近1个月')]"
            )
            
            # 找到对应的radio input
            radio_container = month_label.find_element(By.XPATH, "..")
            radio_input = radio_container.find_element(By.CSS_SELECTOR, "input[type='radio']")
            
            # 使用JavaScript点击
            self.driver.execute_script("arguments[0].click();", radio_input)
            self.human_like_delay(0.5, 1)
            
            logger.info("✅ 已选择'近1个月'")
            
        except Exception as e:
            logger.error(f"选择'近1个月'失败: {e}")
            # 尝试备用方法
            self.select_by_structure("查看时间", 3)  # 第三个选项
            
    def select_by_structure(self, section_title: str, option_index: int):
        """通过结构定位选择选项（备用方法）"""
        try:
            # 找到对应的section header
            header = self.driver.find_element(
                By.XPATH,
                f"//header[contains(@class, 'desktop-filter-section-title-pc') and contains(text(), '{section_title}')]"
            )
            
            # 找到header后面的radio group
            radio_group = header.find_element(
                By.XPATH,
                "following-sibling::div[@class='desktop-filter-radio-group-pc']"
            )
            
            # 找到所有radio选项
            radios = radio_group.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            
            if option_index <= len(radios):
                # 点击指定索引的选项（索引从1开始）
                self.driver.execute_script("arguments[0].click();", radios[option_index - 1])
                logger.info(f"✅ 已选择 {section_title} 的第 {option_index} 个选项")
            else:
                logger.error(f"选项索引 {option_index} 超出范围")
                
        except Exception as e:
            logger.error(f"结构定位失败: {e}")
            
    def scroll_to_load_all(self):
        """滚动加载所有文档"""
        logger.info("滚动加载所有文档...")
        
        last_height = 0
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            # 获取当前文档列表高度
            current_height = self.driver.execute_script(
                "return document.querySelector('.desktop-scrollbars-view').scrollHeight"
            )
            
            if current_height == last_height:
                retry_count += 1
                logger.info(f"没有新内容加载 ({retry_count}/{max_retries})")
            else:
                retry_count = 0
                last_height = current_height
                
            # 滚动到底部
            self.driver.execute_script("""
                const scrollContainer = document.querySelector('.desktop-scrollbars-view');
                if (scrollContainer) {
                    scrollContainer.scrollTop = scrollContainer.scrollHeight;
                }
            """)
            
            # 等待加载
            self.human_like_delay(2, 3)
            
        logger.info("✅ 文档列表加载完成")
        
    def get_document_list(self) -> List[Dict]:
        """获取文档列表"""
        logger.info("获取文档列表...")
        
        documents = []
        
        try:
            # 查找所有文档行
            doc_rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "[class*='desktop-file-list-item'], [class*='file-row']"
            )
            
            for row in doc_rows:
                try:
                    # 提取文档信息
                    doc_name = row.find_element(By.CSS_SELECTOR, "[class*='file-name']").text
                    
                    # 获取文档类型（通过图标判断）
                    doc_type = "unknown"
                    if "sheet" in row.get_attribute("innerHTML").lower():
                        doc_type = "sheet"
                    elif "doc" in row.get_attribute("innerHTML").lower():
                        doc_type = "doc"
                    elif "slide" in row.get_attribute("innerHTML").lower():
                        doc_type = "slide"
                        
                    documents.append({
                        'name': doc_name,
                        'type': doc_type,
                        'element': row
                    })
                    
                except Exception as e:
                    logger.debug(f"解析文档行失败: {e}")
                    
            logger.info(f"✅ 找到 {len(documents)} 个文档")
            
        except Exception as e:
            logger.error(f"获取文档列表失败: {e}")
            
        return documents
        
    def download_single_document(self, doc_element, doc_info: Dict) -> bool:
        """下载单个文档"""
        try:
            logger.info(f"下载文档: {doc_info['name']}")
            
            # 滚动到文档
            self.smooth_scroll(doc_element)
            
            # 右键点击打开菜单
            actions = ActionChains(self.driver)
            actions.context_click(doc_element).perform()
            self.human_like_delay(1, 1.5)
            
            # 查找并点击下载选项
            download_option = None
            selectors = [
                "//div[contains(@class, 'desktop-menu-item-content') and contains(., '下载')]",
                "//div[contains(text(), '下载')]",
                "[class*='menu-item']:has-text('下载')"
            ]
            
            for selector in selectors:
                try:
                    if selector.startswith('//'):
                        download_option = self.driver.find_element(By.XPATH, selector)
                    else:
                        download_option = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if download_option:
                        break
                except:
                    continue
                    
            if download_option:
                download_option.click()
                self.human_like_delay(1, 2)
                
                # 处理下载对话框（如果有）
                self.handle_download_dialog()
                
                logger.info(f"✅ {doc_info['name']} 下载成功")
                return True
            else:
                logger.warning(f"⚠️ {doc_info['name']} 未找到下载选项")
                return False
                
        except Exception as e:
            logger.error(f"下载 {doc_info['name']} 失败: {e}")
            return False
            
    def handle_download_dialog(self):
        """处理下载对话框"""
        try:
            # 查找确认按钮
            confirm_selectors = [
                "button:has-text('确定')",
                "button:has-text('保存')",
                "button:has-text('下载')",
                "[class*='confirm'], [class*='submit']"
            ]
            
            for selector in confirm_selectors:
                try:
                    confirm_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if confirm_btn and confirm_btn.is_displayed():
                        confirm_btn.click()
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"处理下载对话框: {e}")
            
    def batch_download(self) -> Dict[str, any]:
        """批量下载流程"""
        logger.info("="*60)
        logger.info("开始批量下载流程")
        logger.info("="*60)
        
        results = {
            'success': [],
            'failed': [],
            'total': 0
        }
        
        try:
            # 1. 设置浏览器
            self.setup_driver(headless=False)  # 建议使用有界面模式
            
            # 2. 加载Cookie
            self.load_cookies()
            
            # 3. 进入主页
            self.enter_homepage()
            
            # 4. 点击筛选按钮
            self.click_filter_button()
            
            # 5. 选择"我所有"
            self.select_my_documents()
            
            # 6. 选择"近1个月"
            self.select_recent_month()
            
            # 7. 滚动加载所有文档
            self.scroll_to_load_all()
            
            # 8. 获取文档列表
            documents = self.get_document_list()
            results['total'] = len(documents)
            
            # 9. 从下往上逐个下载
            logger.info("开始逐个下载...")
            for i, doc in enumerate(reversed(documents), 1):  # 从下往上
                logger.info(f"处理 {i}/{len(documents)}: {doc['name']}")
                
                if self.download_single_document(doc['element'], doc):
                    results['success'].append(doc['name'])
                else:
                    results['failed'].append(doc['name'])
                    
                # 文档间隔
                self.human_like_delay(3, 5)
                
                # 每10个文档休息一下
                if i % 10 == 0:
                    logger.info("休息30秒...")
                    time.sleep(30)
                    
        except Exception as e:
            logger.error(f"批量下载失败: {e}")
            
        finally:
            # 保持浏览器打开以便调试
            logger.info("\n" + "="*60)
            logger.info("下载完成统计:")
            logger.info(f"总计: {results['total']}")
            logger.info(f"成功: {len(results['success'])}")
            logger.info(f"失败: {len(results['failed'])}")
            logger.info("="*60)
            
            if self.driver:
                input("\n按Enter关闭浏览器...")
                self.driver.quit()
                
        return results

def main():
    """主函数"""
    print("="*60)
    print("腾讯文档批量下载器 - 隐形模式")
    print("="*60)
    print("\n功能说明:")
    print("1. 通过主页筛选界面批量下载")
    print("2. 精确模拟真实用户操作")
    print("3. 使用隐形技术避免检测")
    print("4. 自动处理动态加载")
    print("-"*60)
    
    # 检查Cookie文件
    cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
    if not os.path.exists(cookie_file):
        print(f"\n❌ Cookie文件不存在: {cookie_file}")
        print("请先获取Cookie并保存到配置文件")
        return
        
    print(f"\n✅ Cookie文件已找到")
    
    # 确认开始
    choice = input("\n是否开始批量下载？(y/n): ")
    if choice.lower() != 'y':
        print("已取消")
        return
        
    # 开始下载
    downloader = StealthBatchDownloader(cookie_file)
    results = downloader.batch_download()
    
    # 保存结果
    result_file = f"download_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {result_file}")

if __name__ == "__main__":
    main()