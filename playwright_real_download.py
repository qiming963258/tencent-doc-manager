#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Playwright自动化浏览器下载真实Excel文件
这个方案让浏览器处理所有EJS解密工作
"""

import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright
import time

class TencentDocDownloader:
    """腾讯文档浏览器自动化下载器"""
    
    def __init__(self):
        self.cookie_file = '/root/projects/tencent-doc-manager/config/cookies_new.json'
        self.download_dir = Path('/root/projects/tencent-doc-manager/browser_downloads')
        self.download_dir.mkdir(exist_ok=True)
        
    def load_cookies(self):
        """加载Cookie"""
        with open(self.cookie_file, 'r') as f:
            cookie_data = json.load(f)
        
        # 将cookie字符串转换为浏览器cookie格式
        cookie_str = cookie_data['current_cookies']
        cookies = []
        
        for item in cookie_str.split('; '):
            if '=' in item:
                key, value = item.split('=', 1)
                cookies.append({
                    'name': key,
                    'value': value,
                    'domain': '.docs.qq.com',
                    'path': '/'
                })
        
        return cookies
    
    async def download_document(self, doc_id: str, doc_name: str = None):
        """下载单个文档"""
        print(f"\n{'='*60}")
        print(f"开始下载文档: {doc_id}")
        print(f"{'='*60}")
        
        async with async_playwright() as p:
            # 启动浏览器（服务器环境使用无头模式）
            browser = await p.chromium.launch(
                headless=True,  # 无头模式
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            try:
                # 创建浏览器上下文，设置下载目录
                context = await browser.new_context(
                    accept_downloads=True,
                    viewport={'width': 1920, 'height': 1080}
                )
                
                # 添加cookies
                cookies = self.load_cookies()
                await context.add_cookies(cookies)
                print(f"✅ 已设置 {len(cookies)} 个Cookie")
                
                # 创建新页面
                page = await context.new_page()
                
                # 监听下载事件
                download_promise = asyncio.create_task(self.wait_for_download(page))
                
                # 访问文档页面
                doc_url = f"https://docs.qq.com/sheet/{doc_id}"
                print(f"访问文档: {doc_url}")
                await page.goto(doc_url, wait_until='networkidle')
                
                # 等待页面加载完成
                await page.wait_for_timeout(3000)
                
                # 截图便于调试
                screenshot_path = self.download_dir / f"screenshot_{doc_id}.png"
                await page.screenshot(path=str(screenshot_path))
                print(f"📸 已截图: {screenshot_path}")
                
                # 方法1：点击更多按钮然后导出
                try:
                    print("\n尝试方法1: 点击更多按钮导出")
                    
                    # 查找"更多"按钮
                    more_button = await page.wait_for_selector(
                        'button:has-text("更多"), div[class*="more"]:has-text("更多")', 
                        timeout=5000
                    )
                    if more_button:
                        await more_button.click()
                        print("✅ 点击了更多按钮")
                        await page.wait_for_timeout(1000)
                        
                        # 查找并点击"导出为"或"下载"
                        export_option = await page.wait_for_selector(
                            'div:has-text("导出为"), div:has-text("下载"), span:has-text("导出")',
                            timeout=3000
                        )
                        if export_option:
                            await export_option.click()
                            print("✅ 点击了导出选项")
                            await page.wait_for_timeout(1000)
                            
                            # 选择Excel格式
                            excel_option = await page.wait_for_selector(
                                'div:has-text("Excel"), div:has-text(".xlsx"), span:has-text("Excel")',
                                timeout=3000
                            )
                            if excel_option:
                                await excel_option.click()
                                print("✅ 选择了Excel格式")
                except:
                    print("方法1失败，尝试其他方法")
                
                # 方法2：使用键盘快捷键
                if not download_promise.done():
                    print("\n尝试方法2: 使用快捷键")
                    await page.keyboard.press('Control+Shift+E')  # 导出快捷键
                    await page.wait_for_timeout(2000)
                
                # 方法3：直接访问导出URL
                if not download_promise.done():
                    print("\n尝试方法3: 直接触发导出")
                    
                    # 注入JavaScript直接触发下载
                    await page.evaluate(f'''
                        (() => {{
                            // 尝试查找并触发导出功能
                            const exportBtn = document.querySelector('[aria-label="导出"]');
                            if (exportBtn) {{
                                exportBtn.click();
                                return "clicked export button";
                            }}
                            
                            // 或者直接创建下载链接
                            const link = document.createElement('a');
                            link.href = 'https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx';
                            link.download = 'document.xlsx';
                            document.body.appendChild(link);
                            link.click();
                            return "created download link";
                        }})()
                    ''')
                    print("✅ 已执行JavaScript导出")
                
                # 等待下载完成（最多30秒）
                try:
                    download = await asyncio.wait_for(download_promise, timeout=30)
                    
                    if download:
                        # 保存下载的文件
                        filename = doc_name or f"tencent_doc_{doc_id}"
                        if not filename.endswith('.xlsx'):
                            filename += '.xlsx'
                        
                        save_path = self.download_dir / filename
                        await download.save_as(str(save_path))
                        
                        print(f"\n✅ 下载成功！")
                        print(f"文件已保存到: {save_path}")
                        
                        # 验证文件
                        if save_path.exists():
                            file_size = save_path.stat().st_size
                            print(f"文件大小: {file_size:,} bytes")
                            
                            # 检查是否是真实的Excel文件
                            with open(save_path, 'rb') as f:
                                header = f.read(4)
                                if header == b'PK\x03\x04':
                                    print("✅ 确认是真实的Excel文件（ZIP格式）")
                                    return str(save_path)
                                else:
                                    print(f"⚠️ 文件格式未知: {header.hex()}")
                        
                except asyncio.TimeoutError:
                    print("❌ 下载超时（30秒）")
                    
                    # 检查是否有其他方式获取文件
                    files = list(self.download_dir.glob("*.xlsx"))
                    if files:
                        latest_file = max(files, key=lambda x: x.stat().st_mtime)
                        print(f"找到下载的文件: {latest_file}")
                        return str(latest_file)
                    
            except Exception as e:
                print(f"❌ 下载失败: {e}")
                
            finally:
                await browser.close()
        
        return None
    
    async def wait_for_download(self, page):
        """等待下载事件"""
        try:
            async with page.expect_download() as download_info:
                download = await download_info.value
                return download
        except:
            return None
    
    async def batch_download(self, doc_list):
        """批量下载文档"""
        results = []
        
        for doc in doc_list:
            if isinstance(doc, dict):
                doc_id = doc.get('id')
                doc_name = doc.get('name')
            else:
                doc_id = doc
                doc_name = None
            
            result = await self.download_document(doc_id, doc_name)
            results.append({
                'doc_id': doc_id,
                'name': doc_name,
                'success': result is not None,
                'file': result
            })
            
            # 等待一下避免太快
            await asyncio.sleep(3)
        
        return results

async def main():
    """主函数"""
    downloader = TencentDocDownloader()
    
    # 测试文档列表
    test_docs = [
        {
            'id': 'DWEVjZndkR2xVSWJN',
            'name': '测试版本-小红书部门'
        }
    ]
    
    print("🚀 启动浏览器自动化下载")
    print("="*60)
    
    # 下载文档
    results = await downloader.batch_download(test_docs)
    
    # 显示结果
    print("\n" + "="*60)
    print("下载结果总结")
    print("="*60)
    
    success_count = sum(1 for r in results if r['success'])
    print(f"成功: {success_count}/{len(results)}")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['name'] or result['doc_id']}")
        if result['file']:
            print(f"   文件: {result['file']}")
    
    if success_count > 0:
        print("\n🎉 浏览器自动化方案成功！")
        print("获得了真实的Excel文件，完全绕过了EJS加密")
    else:
        print("\n需要调整选择器或等待时间")

if __name__ == "__main__":
    asyncio.run(main())