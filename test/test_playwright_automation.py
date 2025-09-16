#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright自动化测试脚本
测试腾讯文档浏览器自动化的可行性
"""

import json
import asyncio
import time
from pathlib import Path
from datetime import datetime

# 检查Playwright是否已安装
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# 配置信息
COOKIE_FILE = "/root/projects/tencent-doc-manager/config/cookies_new.json"
TEST_DOC_ID = "DWEVjZndkR2xVSWJN"
DOWNLOADS_DIR = "/root/projects/tencent-doc-manager/downloads"

class PlaywrightTester:
    """Playwright自动化测试器"""
    
    def __init__(self):
        self.cookie_data = {}
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "playwright_available": PLAYWRIGHT_AVAILABLE,
            "tests": {}
        }
        self.load_cookies()
    
    def load_cookies(self):
        """加载cookie"""
        try:
            with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
                self.cookie_data = json.load(f)
        except Exception as e:
            print(f"❌ 无法加载cookie: {e}")
    
    async def test_basic_browser_automation(self):
        """基础浏览器自动化测试"""
        test_name = "basic_browser_automation"
        print(f"\n🔬 测试方案: {test_name}")
        
        if not PLAYWRIGHT_AVAILABLE:
            result = {
                "success": False,
                "error": "Playwright未安装",
                "description": "需要先安装: pip install playwright && playwright install chromium"
            }
            self.test_results["tests"][test_name] = result
            print("❌ Playwright未安装")
            return result
        
        try:
            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(
                    headless=True,  # 无头模式
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                # 设置cookie
                if self.cookie_data.get("current_cookies"):
                    cookie_str = self.cookie_data["current_cookies"]
                    cookies = []
                    for cookie in cookie_str.split('; '):
                        if '=' in cookie:
                            name, value = cookie.split('=', 1)
                            cookies.append({
                                'name': name,
                                'value': value,
                                'domain': '.docs.qq.com',
                                'path': '/'
                            })
                    
                    await context.add_cookies(cookies)
                    print(f"✅ 已设置 {len(cookies)} 个cookie")
                
                page = await context.new_page()
                
                # 测试访问腾讯文档主页
                print("📄 访问腾讯文档主页...")
                await page.goto('https://docs.qq.com/', wait_until='networkidle')
                
                title = await page.title()
                url = page.url
                
                result = {
                    "success": True,
                    "page_title": title,
                    "final_url": url,
                    "can_access_main_page": True
                }
                
                # 尝试访问具体文档
                print(f"📄 访问测试文档: {TEST_DOC_ID}")
                doc_url = f"https://docs.qq.com/sheet/{TEST_DOC_ID}"
                
                response = await page.goto(doc_url, wait_until='networkidle')
                doc_title = await page.title()
                
                result.update({
                    "doc_access_status": response.status,
                    "doc_title": doc_title,
                    "can_access_document": response.status == 200
                })
                
                # 截图保存
                screenshot_path = f"{DOWNLOADS_DIR}/playwright_screenshot_{int(time.time())}.png"
                await page.screenshot(path=screenshot_path)
                result["screenshot_saved"] = screenshot_path
                
                print(f"✅ 文档访问成功，标题: {doc_title}")
                print(f"📸 截图已保存: {screenshot_path}")
                
                await browser.close()
                
                self.test_results["tests"][test_name] = result
                return result
                
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
            self.test_results["tests"][test_name] = result
            print(f"❌ 浏览器自动化测试失败: {e}")
            return result
    
    async def test_desktop_page_automation(self):
        """测试桌面版页面自动化"""
        test_name = "desktop_page_automation"
        print(f"\n🔬 测试方案: {test_name}")
        
        if not PLAYWRIGHT_AVAILABLE:
            result = {
                "success": False,
                "error": "Playwright未安装"
            }
            self.test_results["tests"][test_name] = result
            print("❌ Playwright未安装")
            return result
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                
                # 设置cookie
                if self.cookie_data.get("current_cookies"):
                    cookie_str = self.cookie_data["current_cookies"]
                    cookies = []
                    for cookie in cookie_str.split('; '):
                        if '=' in cookie:
                            name, value = cookie.split('=', 1)
                            cookies.append({
                                'name': name,
                                'value': value,
                                'domain': '.docs.qq.com',
                                'path': '/'
                            })
                    await context.add_cookies(cookies)
                
                page = await context.new_page()
                
                # 访问桌面版
                print("🖥️ 访问桌面版页面...")
                await page.goto('https://docs.qq.com/desktop', wait_until='networkidle')
                
                title = await page.title()
                
                # 尝试查找筛选相关元素
                print("🔍 查找页面元素...")
                
                # 查找可能的筛选按钮
                filter_selectors = [
                    'button[class*="filter"]',
                    'button[class*="筛选"]',
                    '[data-testid*="filter"]',
                    '.filter-button',
                    '[aria-label*="筛选"]',
                    '[aria-label*="filter"]'
                ]
                
                found_elements = {}
                for selector in filter_selectors:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        found_elements[selector] = len(elements)
                
                # 获取页面的所有按钮
                all_buttons = await page.query_selector_all('button')
                button_texts = []
                for button in all_buttons[:20]:  # 只取前20个避免过多
                    try:
                        text = await button.inner_text()
                        if text.strip():
                            button_texts.append(text.strip())
                    except:
                        pass
                
                result = {
                    "success": True,
                    "page_title": title,
                    "filter_elements_found": found_elements,
                    "button_count": len(all_buttons),
                    "sample_button_texts": button_texts[:10]
                }
                
                # 截图
                screenshot_path = f"{DOWNLOADS_DIR}/desktop_screenshot_{int(time.time())}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                result["screenshot_saved"] = screenshot_path
                
                print(f"✅ 桌面版访问成功")
                print(f"📋 找到 {len(all_buttons)} 个按钮元素")
                print(f"📸 截图已保存: {screenshot_path}")
                
                await browser.close()
                
                self.test_results["tests"][test_name] = result
                return result
                
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
            self.test_results["tests"][test_name] = result
            print(f"❌ 桌面版自动化测试失败: {e}")
            return result
    
    def save_test_results(self):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"{DOWNLOADS_DIR}/playwright_test_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 测试结果已保存: {results_file}")
        return results_file
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("🎯 Playwright自动化测试结果摘要")
        print("="*60)
        
        if not self.test_results.get("playwright_available", False):
            print("❌ Playwright不可用，需要安装:")
            print("   pip install playwright")
            print("   playwright install chromium")
            return
        
        total_tests = len(self.test_results["tests"])
        successful_tests = 0
        
        for test_name, test_data in self.test_results["tests"].items():
            if test_data.get("success", False):
                successful_tests += 1
                status = "✅ 成功"
            else:
                status = "❌ 失败"
            
            print(f"{status} {test_name}")
            
            if test_data.get("success", False):
                if "page_title" in test_data:
                    print(f"    📄 页面标题: {test_data['page_title']}")
                if "screenshot_saved" in test_data:
                    print(f"    📸 截图: {test_data['screenshot_saved']}")
            else:
                if "error" in test_data:
                    print(f"    ❌ 错误: {test_data['error']}")
        
        print(f"\n总体结果: {successful_tests}/{total_tests} 个测试成功")
        
        if successful_tests > 0:
            print("\n💡 后续建议:")
            print("   ✅ 浏览器自动化可行")
            print("   ✅ 可以通过Playwright进行文档自动化")
            print("   ✅ 建议开发完整的自动化下载脚本")
        
        print("="*60)

async def main():
    """主函数"""
    print("🚀 开始Playwright自动化测试")
    print(f"📝 测试文档ID: {TEST_DOC_ID}")
    
    tester = PlaywrightTester()
    
    try:
        # 执行测试
        await tester.test_basic_browser_automation()
        await tester.test_desktop_page_automation()
        
        # 保存结果和打印摘要
        tester.save_test_results()
        tester.print_summary()
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")

if __name__ == "__main__":
    # 检查Playwright是否可用
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright未安装")
        print("请先安装Playwright:")
        print("pip install playwright")
        print("playwright install chromium")
        exit(1)
    
    asyncio.run(main())