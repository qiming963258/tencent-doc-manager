#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版浏览器下载 - 使用requests-html或selenium
更容易安装和使用
"""

import json
import time
import os
from pathlib import Path

def browser_download_with_selenium():
    """使用Selenium下载（更通用）"""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        
        print("✅ Selenium已安装")
    except ImportError:
        print("❌ 需要安装Selenium")
        print("运行: pip install selenium")
        return None
    
    # 加载cookie
    with open('/root/projects/tencent-doc-manager/config/cookies_new.json', 'r') as f:
        cookie_data = json.load(f)
    cookie_str = cookie_data['current_cookies']
    
    # 设置下载目录
    download_dir = Path('/root/projects/tencent-doc-manager/selenium_downloads')
    download_dir.mkdir(exist_ok=True)
    
    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument('--headless')  # 无头模式，调试时注释掉
    
    # 设置下载目录
    prefs = {
        'download.default_directory': str(download_dir),
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'safebrowsing.enabled': True
    }
    chrome_options.add_experimental_option('prefs', prefs)
    
    # 启动浏览器
    print("\n启动Chrome浏览器...")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 先访问主页设置cookie
        driver.get('https://docs.qq.com')
        
        # 添加cookies
        for cookie_pair in cookie_str.split('; '):
            if '=' in cookie_pair:
                name, value = cookie_pair.split('=', 1)
                driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': '.docs.qq.com'
                })
        
        print("✅ Cookie设置完成")
        
        # 访问文档
        doc_id = 'DWEVjZndkR2xVSWJN'
        doc_url = f'https://docs.qq.com/sheet/{doc_id}'
        print(f"\n访问文档: {doc_url}")
        driver.get(doc_url)
        
        # 等待页面加载
        time.sleep(5)
        
        # 截图
        screenshot_path = download_dir / f'page_{doc_id}.png'
        driver.save_screenshot(str(screenshot_path))
        print(f"📸 页面截图: {screenshot_path}")
        
        # 方法1：执行JavaScript直接下载
        print("\n尝试JavaScript直接下载...")
        result = driver.execute_script(f"""
            // 创建下载链接
            var link = document.createElement('a');
            link.href = 'https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx';
            link.download = 'document.xlsx';
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            return 'Download triggered';
        """)
        print(f"JavaScript结果: {result}")
        
        # 等待下载
        time.sleep(10)
        
        # 检查下载的文件
        downloaded_files = list(download_dir.glob('*.xlsx'))
        if downloaded_files:
            latest_file = max(downloaded_files, key=lambda x: x.stat().st_mtime)
            print(f"\n✅ 找到下载文件: {latest_file}")
            
            # 检查文件格式
            with open(latest_file, 'rb') as f:
                header = f.read(100)
                if header[:4] == b'PK\x03\x04':
                    print("✅ 确认是真实的Excel文件！")
                    return str(latest_file)
                elif b'head' in header and b'json' in header:
                    print("❌ 仍然是EJS格式")
                else:
                    print(f"❓ 未知格式: {header[:50]}")
        else:
            print("❌ 没有找到下载的文件")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        
    finally:
        driver.quit()
        print("\n浏览器已关闭")
    
    return None

def alternative_pyppeteer():
    """使用Pyppeteer（Python版Puppeteer）"""
    try:
        import asyncio
        from pyppeteer import launch
        
        async def download():
            browser = await launch({
                'headless': False,
                'args': ['--no-sandbox', '--disable-setuid-sandbox']
            })
            
            page = await browser.newPage()
            
            # 设置cookie
            with open('/root/projects/tencent-doc-manager/config/cookies_new.json', 'r') as f:
                cookie_data = json.load(f)
            cookie_str = cookie_data['current_cookies']
            
            # 转换cookie格式
            cookies = []
            for item in cookie_str.split('; '):
                if '=' in item:
                    name, value = item.split('=', 1)
                    cookies.append({
                        'name': name,
                        'value': value,
                        'domain': '.docs.qq.com'
                    })
            
            await page.setCookie(*cookies)
            
            # 访问文档
            doc_id = 'DWEVjZndkR2xVSWJN'
            await page.goto(f'https://docs.qq.com/sheet/{doc_id}')
            
            # 等待加载
            await page.waitFor(3000)
            
            # 触发下载
            await page.evaluate(f'''() => {{
                const link = document.createElement('a');
                link.href = 'https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx';
                link.download = 'document.xlsx';
                document.body.appendChild(link);
                link.click();
            }}''')
            
            # 等待下载
            await page.waitFor(10000)
            
            await browser.close()
            print("✅ Pyppeteer执行完成")
        
        asyncio.run(download())
        
    except ImportError:
        print("需要安装: pip install pyppeteer")
        print("首次运行会自动下载Chromium")

def main():
    """主函数"""
    print("="*60)
    print("浏览器自动化下载方案测试")
    print("="*60)
    
    # 检查可用的工具
    methods = []
    
    try:
        import selenium
        methods.append("Selenium")
    except:
        pass
    
    try:
        import playwright
        methods.append("Playwright")
    except:
        pass
    
    try:
        import pyppeteer
        methods.append("Pyppeteer")
    except:
        pass
    
    if methods:
        print(f"可用的工具: {', '.join(methods)}")
    else:
        print("❌ 没有安装浏览器自动化工具")
        print("\n请安装以下任一工具:")
        print("1. pip install selenium")
        print("2. pip install playwright && playwright install")
        print("3. pip install pyppeteer")
        return
    
    # 使用Selenium（最通用）
    if "Selenium" in methods:
        print("\n使用Selenium进行测试...")
        result = browser_download_with_selenium()
        
        if result:
            print(f"\n🎉 成功下载真实Excel文件: {result}")
        else:
            print("\n需要调整下载策略")
    
    print("\n" + "="*60)
    print("浏览器自动化优势:")
    print("="*60)
    print("✅ 浏览器自动处理EJS解密")
    print("✅ 获得真实的Excel文件")
    print("✅ 完全模拟用户操作")
    print("✅ 可以处理动态页面")

if __name__ == "__main__":
    main()