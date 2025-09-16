#!/usr/bin/env python3
"""
修复版自动化下载器 - 处理导航和英文界面
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

class FixedServerDownloader:
    def __init__(self):
        self.download_dir = Path("/root/projects/tencent-doc-manager/enterprise_download_system/downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        self.browser = None
        self.context = None
        self.page = None
        
        self.cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZwaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
        
        print(f"📁 下载目录: {self.download_dir}")

    def parse_cookies(self):
        cookies = []
        for cookie_pair in self.cookie_string.split('; '):
            if '=' in cookie_pair:
                name, value = cookie_pair.split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.docs.qq.com',
                    'path': '/'
                })
        return cookies

    async def setup_browser(self):
        print("🚀 启动浏览器...")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True,
            extra_http_headers={
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://docs.qq.com/desktop'
            }
        )
        
        await self.context.add_cookies(self.parse_cookies())
        self.page = await self.context.new_page()
        self.page.on('download', self.handle_download)
        
        print("✅ 浏览器设置完成")

    async def handle_download(self, download):
        try:
            filename = download.suggested_filename
            download_path = self.download_dir / filename
            
            print(f"⬇️  下载: {filename}")
            await download.save_as(download_path)
            
            file_size = download_path.stat().st_size if download_path.exists() else 0
            print(f"✅ 完成: {filename} ({file_size:,} 字节)")
            
        except Exception as e:
            print(f"❌ 下载失败: {e}")

    async def navigate_to_documents(self):
        """导航到文档列表页面"""
        print("🧭 导航到文档列表...")
        
        try:
            # 访问桌面页面
            await self.page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded', timeout=30000)
            await self.page.wait_for_timeout(5000)
            
            print(f"📄 当前标题: {await self.page.title()}")
            print(f"📍 当前URL: {self.page.url}")
            
            # 尝试点击"Cloud Docs"或类似的导航按钮
            nav_selectors = [
                'text=Cloud Docs',
                'text=文档',
                'text=我的文档',
                'text=My Documents',
                '[href*="/desktop"]',
                '[href*="/mydocs"]',
                'button:has-text("Cloud")',
                'a:has-text("Cloud")'
            ]
            
            nav_clicked = False
            for selector in nav_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.click()
                        print(f"✅ 点击了导航: {selector}")
                        nav_clicked = True
                        break
                except:
                    continue
            
            if nav_clicked:
                await self.page.wait_for_timeout(5000)
                print(f"📄 导航后标题: {await self.page.title()}")
                print(f"📍 导航后URL: {self.page.url}")
            else:
                print("⚠️  未找到导航按钮，尝试直接访问")
            
            # 尝试直接访问文档列表URL
            try:
                await self.page.goto('https://docs.qq.com/desktop/mydocs', wait_until='domcontentloaded', timeout=30000)
                await self.page.wait_for_timeout(5000)
                print("✅ 直接访问文档列表页面")
                print(f"📄 新标题: {await self.page.title()}")
                print(f"📍 新URL: {self.page.url}")
            except Exception as e:
                print(f"⚠️  直接访问失败: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ 导航失败: {e}")
            return False

    async def find_and_download_files(self, limit=10):
        """查找并下载文件"""
        print(f"🔍 查找文档并下载前{limit}个...")
        
        try:
            # 等待页面稳定
            await self.page.wait_for_timeout(8000)
            
            # 尝试各种可能的文件元素选择器
            file_selectors = [
                '.file-item',
                '.document-item', 
                '.doc-item',
                '[class*="file"]',
                '[class*="doc"]',
                '[data-testid*="file"]',
                'tr[class*="item"]',
                '.list-item',
                'div[role="row"]',
                'li[data-*]'
            ]
            
            found_elements = []
            for selector in file_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements and len(elements) > len(found_elements):
                        found_elements = elements
                        print(f"✅ 使用选择器 {selector}，找到 {len(elements)} 个元素")
                except:
                    continue
            
            if not found_elements:
                print("❌ 未找到文档元素")
                
                # 尝试查找任何可右键的元素
                print("🔍 查找任何包含文本的可交互元素...")
                try:
                    all_elements = await self.page.query_selector_all('div, span, a, li, tr')
                    text_elements = []
                    
                    for elem in all_elements[:50]:  # 限制检查数量
                        try:
                            text = await elem.inner_text()
                            if text and len(text.strip()) > 5 and len(text.strip()) < 100:
                                # 排除明显的导航和界面元素
                                if not any(skip in text.lower() for skip in ['home', 'template', 'trash', 'space', 'nav', 'menu', 'button']):
                                    text_elements.append((elem, text.strip()))
                        except:
                            continue
                    
                    print(f"🔍 找到 {len(text_elements)} 个可能的文档元素")
                    if text_elements:
                        found_elements = [elem for elem, text in text_elements]
                        for i, (elem, text) in enumerate(text_elements[:10]):
                            print(f"  {i+1}. {text[:50]}...")
                    
                except Exception as e:
                    print(f"⚠️  查找文本元素失败: {e}")
            
            if not found_elements:
                print("❌ 完全未找到可操作的元素")
                return 0
            
            # 尝试下载
            download_count = 0
            skip_count = 0
            
            files_to_process = found_elements[:limit]
            print(f"🎯 开始处理前 {len(files_to_process)} 个元素...")
            
            for i, element in enumerate(files_to_process):
                try:
                    print(f"\n📄 处理元素 {i+1}/{len(files_to_process)}...")
                    
                    # 滚动到元素
                    await element.scroll_into_view_if_needed()
                    await self.page.wait_for_timeout(1000)
                    
                    # 尝试获取元素文本
                    try:
                        element_text = await element.inner_text()
                        if element_text:
                            print(f"📝 内容: {element_text[:50]}...")
                    except:
                        print(f"📝 元素 {i+1}")
                    
                    # 右键点击
                    await element.click(button='right')
                    print("🖱️  右键点击")
                    
                    # 等待右键菜单
                    await self.page.wait_for_timeout(2000)
                    
                    # 查找下载选项
                    download_selectors = [
                        'text=Download',
                        'text=下载', 
                        'text=Export',
                        'text=导出',
                        '[data-testid*="download"]',
                        '.menu-item:has-text("Download")',
                        '.menu-item:has-text("下载")',
                        '.context-menu-item:has-text("Download")',
                        '.context-menu-item:has-text("下载")'
                    ]
                    
                    download_clicked = False
                    for selector in download_selectors:
                        try:
                            download_elem = await self.page.wait_for_selector(selector, timeout=3000)
                            if download_elem:
                                await download_elem.click()
                                print("✅ 点击下载选项")
                                download_count += 1
                                download_clicked = True
                                break
                        except:
                            continue
                    
                    if not download_clicked:
                        print("⚠️  未找到下载选项")
                        skip_count += 1
                        # 点击其他地方关闭菜单
                        await self.page.click('body')
                    
                    # 等待一段时间
                    await self.page.wait_for_timeout(3000)
                    
                    # 处理下载确认对话框
                    try:
                        await self.page.click('text=Allow', timeout=1000)
                        print("✅ 允许下载")
                    except:
                        try:
                            await self.page.click('text=允许', timeout=1000)
                        except:
                            pass
                    
                except Exception as e:
                    print(f"❌ 处理元素{i+1}失败: {e}")
                    skip_count += 1
                    continue
            
            print(f"\n🎉 处理完成!")
            print(f"✅ 尝试下载: {download_count}")
            print(f"⚠️  跳过: {skip_count}")
            
            return download_count
            
        except Exception as e:
            print(f"❌ 查找文件失败: {e}")
            return 0

    async def run_download(self):
        try:
            print("🌟 开始修复版下载任务")
            print("=" * 60)
            
            await self.setup_browser()
            
            # 导航到文档页面
            if not await self.navigate_to_documents():
                print("❌ 导航失败")
                return False
            
            # 查找并下载文件
            download_count = await self.find_and_download_files(10)
            
            # 等待下载完成
            print("⏳ 等待下载完成...")
            await self.page.wait_for_timeout(15000)
            
            return download_count > 0
            
        finally:
            if self.browser:
                await self.browser.close()
                print("🔚 浏览器已关闭")

async def main():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                修复版自动化下载测试                              ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    downloader = FixedServerDownloader()
    success = await downloader.run_download()
    
    # 检查结果
    downloads_path = Path("/root/projects/tencent-doc-manager/enterprise_download_system/downloads")
    files = list(downloads_path.glob("*"))
    
    print("\n" + "=" * 60)
    print("📊 最终结果:")
    print(f"📁 下载目录: {downloads_path}")
    print(f"📄 下载文件数: {len(files)}")
    
    if files:
        print("\n📋 下载的文件:")
        for i, file_path in enumerate(files, 1):
            size = file_path.stat().st_size
            print(f"{i:2d}. {file_path.name}")
            print(f"     大小: {size:,} 字节")
            print(f"     路径: {file_path}")
    else:
        print("⚠️  没有成功下载任何文件")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    asyncio.run(main())