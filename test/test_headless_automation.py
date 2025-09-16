#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试无头浏览器自动化的核心功能
不依赖复杂库，直接验证可行性
"""

import asyncio
import json
import os
import time
from playwright.async_api import async_playwright

class HeadlessTest:
    def __init__(self):
        self.cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
        
    async def test_basic_automation(self):
        """测试基础的无头浏览器自动化"""
        print("="*60)
        print("测试1: 无头浏览器基础功能")
        print("="*60)
        
        try:
            playwright = await async_playwright().start()
            
            # 启动无头浏览器
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            
            context = await browser.new_context()
            page = await context.new_page()
            
            # 访问测试页面
            await page.goto('https://httpbin.org/get')
            content = await page.content()
            
            if 'httpbin' in content:
                print("✅ 无头浏览器工作正常")
            else:
                print("❌ 无头浏览器异常")
                
            await browser.close()
            await playwright.stop()
            return True
            
        except Exception as e:
            print(f"❌ 无头浏览器测试失败: {e}")
            return False
            
    async def test_tencent_access(self):
        """测试访问腾讯文档"""
        print("\n" + "="*60)
        print("测试2: 腾讯文档访问")
        print("="*60)
        
        try:
            # 加载Cookie
            if not os.path.exists(self.cookie_file):
                print("❌ Cookie文件不存在")
                return False
                
            with open(self.cookie_file, 'r') as f:
                cookie_data = json.load(f)
                cookie_str = cookie_data['current_cookies']
                
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context()
            page = await context.new_page()
            
            # 访问腾讯文档首页
            await page.goto("https://docs.qq.com")
            
            # 设置Cookie
            cookies = []
            for item in cookie_str.split('; '):
                if '=' in item:
                    key, value = item.split('=', 1)
                    cookies.append({
                        'name': key,
                        'value': value,
                        'domain': '.qq.com',
                        'path': '/'
                    })
            
            await context.add_cookies(cookies)
            print(f"✅ 已设置 {len(cookies)} 个Cookie")
            
            # 重新访问检查登录状态
            await page.goto("https://docs.qq.com")
            await page.wait_for_timeout(3000)
            
            content = await page.content()
            
            if "登录" not in content and "docs.qq.com" in content:
                print("✅ Cookie有效，已登录腾讯文档")
                success = True
            else:
                print("❌ Cookie无效或已过期")
                success = False
                
            await browser.close()
            await playwright.stop()
            return success
            
        except Exception as e:
            print(f"❌ 腾讯文档访问测试失败: {e}")
            return False
            
    async def test_document_download(self):
        """测试实际文档下载"""
        print("\n" + "="*60)
        print("测试3: 文档下载功能")
        print("="*60)
        
        try:
            # 加载Cookie
            with open(self.cookie_file, 'r') as f:
                cookie_data = json.load(f)
                cookie_str = cookie_data['current_cookies']
                
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context()
            page = await context.new_page()
            
            # 设置Cookie
            await page.goto("https://docs.qq.com")
            cookies = []
            for item in cookie_str.split('; '):
                if '=' in item:
                    key, value = item.split('=', 1)
                    cookies.append({
                        'name': key,
                        'value': value,
                        'domain': '.qq.com',
                        'path': '/'
                    })
            await context.add_cookies(cookies)
            
            # 测试下载
            doc_id = "DWEVjZndkR2xVSWJN"
            
            # 方法1: 直接API下载
            print("尝试直接API下载...")
            timestamp = int(time.time() * 1000)
            download_url = f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx&download=1&t={timestamp}"
            
            response = await page.goto(download_url)
            
            if response.status == 200:
                content = await response.body()
                print(f"✅ API下载成功，内容长度: {len(content)} bytes")
                
                # 检查是否是真正的Excel文件
                if content.startswith(b'PK\x03\x04'):
                    print("✅ 确认是Excel格式文件")
                    
                    # 保存测试文件
                    test_file = f"/tmp/test_download_{int(time.time())}.xlsx"
                    with open(test_file, 'wb') as f:
                        f.write(content)
                    print(f"✅ 文件已保存: {test_file}")
                    success = True
                    
                elif b'text' in content[:100] or b'<html' in content[:100]:
                    print("⚠️ 返回的是文本/HTML格式，可能是EJS数据")
                    print(f"前100字节: {content[:100]}")
                    success = False
                else:
                    print(f"❓ 未知格式，前20字节: {content[:20]}")
                    success = False
            else:
                print(f"❌ 下载失败，状态码: {response.status}")
                success = False
                
            await browser.close()
            await playwright.stop()
            return success
            
        except Exception as e:
            print(f"❌ 文档下载测试失败: {e}")
            return False

async def run_comprehensive_test():
    """运行完整测试"""
    print("腾讯文档服务器端自动化 - 实际可行性测试")
    print("="*60)
    
    tester = HeadlessTest()
    results = {}
    
    # 测试1: 基础功能
    results['basic'] = await tester.test_basic_automation()
    
    # 测试2: 腾讯文档访问
    results['access'] = await tester.test_tencent_access()
    
    # 测试3: 文档下载
    if results['access']:
        results['download'] = await tester.test_document_download()
    else:
        print("\n跳过下载测试（访问测试失败）")
        results['download'] = False
    
    # 结果汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test.ljust(15)}: {status}")
        
    print(f"\n总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 服务器端自动化方案完全可行！")
    elif passed >= total * 0.7:
        print("⚠️ 方案基本可行，但需要解决部分问题")
    else:
        print("❌ 方案存在重大问题，需要重新设计")
        
    return results

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())