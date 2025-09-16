#!/usr/bin/env python3
"""
基于UI分析的智能下载器 - 使用真实的CSS选择器
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

class SmartDownloader:
    def __init__(self):
        self.download_dir = Path("/root/projects/tencent-doc-manager/enterprise_download_system/downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        self.cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZpaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
        self.downloaded_files = []
        
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

    async def handle_download(self, download):
        try:
            filename = download.suggested_filename
            download_path = self.download_dir / filename
            print(f"⬇️  下载: {filename}")
            await download.save_as(download_path)
            self.downloaded_files.append(str(download_path))
            file_size = download_path.stat().st_size if download_path.exists() else 0
            print(f"✅ 完成: {filename} ({file_size:,} 字节)")
        except Exception as e:
            print(f"❌ 下载失败: {e}")

    async def smart_navigation(self, page):
        """基于UI分析的智能导航"""
        print("🧭 智能导航到文档列表...")
        
        # 第一步：等待页面完全加载
        await page.wait_for_timeout(10000)
        
        # 第二步：基于分析结果，尝试点击Cloud Docs
        try:
            print("🔍 查找Cloud Docs按钮...")
            # 使用精确的文本选择器
            cloud_docs_btn = await page.wait_for_selector('text=Cloud Docs', timeout=15000)
            if cloud_docs_btn:
                print("✅ 找到Cloud Docs，点击...")
                await cloud_docs_btn.click(timeout=10000)  # 增加点击超时
                
                # 等待页面跳转
                print("⏳ 等待页面跳转...")
                await page.wait_for_timeout(15000)  # 等待15秒
                
                print(f"📍 跳转后URL: {page.url}")
                print(f"📄 跳转后标题: {await page.title()}")
                
                return True
        except Exception as e:
            print(f"⚠️  Cloud Docs点击失败: {e}")
        
        # 第三步：尝试直接访问不同的文档页面URL
        doc_urls = [
            'https://docs.qq.com/desktop/mydocs',
            'https://docs.qq.com/desktop/file/recent', 
            'https://docs.qq.com/desktop/recent',
            'https://docs.qq.com/folder',
            'https://docs.qq.com/desktop/file'
        ]
        
        for url in doc_urls:
            try:
                print(f"🔗 尝试访问: {url}")
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(10000)
                
                # 检查是否成功跳转到文档列表
                current_url = page.url
                if 'mydocs' in current_url or 'file' in current_url or 'recent' in current_url:
                    print(f"✅ 成功导航到: {current_url}")
                    return True
                    
            except Exception as e:
                print(f"⚠️  访问失败: {e}")
                continue
        
        print("⚠️  所有导航方式都失败，继续在当前页面查找文档")
        return False

    async def find_documents_intelligently(self, page):
        """智能查找文档元素"""
        print("🔍 智能搜索文档元素...")
        
        # 基于UI分析，使用发现的实际选择器
        selectors_to_try = [
            # 基于分析发现的有效选择器
            '.dui-tabs-bar-item',  # 发现有标签项
            '[class*="item"]',     # 分析显示有47个item元素
            '.menu-item',          # 发现有菜单项
            '.login-item-gIZco',   # 发现的具体类名
            
            # 尝试导航相关的
            '.desktop-sidebar-nav a',
            '.desktop-icon-nav-link',
            
            # 通用文档相关选择器
            'a[href*="pad"]', 'a[href*="sheet"]', 'a[href*="slide"]',
            'div[data-*]', 'li[data-*]', '[role="menuitem"]',
            
            # 文本内容搜索
            'text=/.*\\.doc.*/', 'text=/.*\\.xls.*/', 'text=/.*\\.ppt.*/',
            'text=/.*文档.*/', 'text=/.*表格.*/', 'text=/.*演示.*/'
        ]
        
        found_elements = []
        
        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"✅ {selector}: {len(elements)} 个元素")
                    
                    # 检查元素内容
                    for elem in elements[:5]:  # 检查前5个
                        try:
                            text = await elem.inner_text()
                            if text and len(text.strip()) > 3:
                                # 检查是否像文档名
                                text_lower = text.lower().strip()
                                if any(keyword in text_lower for keyword in 
                                      ['doc', 'sheet', 'slide', '文档', '表格', '演示', 
                                       '.doc', '.xls', '.ppt', 'excel', 'word', 'powerpoint']):
                                    found_elements.append((elem, text.strip()))
                                    print(f"   📄 发现文档: {text.strip()[:50]}")
                        except:
                            continue
                    
                    if found_elements:
                        break  # 找到就停止
            except:
                continue
        
        if not found_elements:
            print("⚠️  未找到明确的文档元素，尝试更广泛的搜索...")
            
            # 最后的尝试：查找所有可点击元素
            try:
                all_clickable = await page.query_selector_all('a, button, div[onclick], [role="button"], li, span')
                for elem in all_clickable[:30]:  # 检查前30个
                    try:
                        text = await elem.inner_text()
                        if text and 10 < len(text.strip()) < 100:
                            found_elements.append((elem, text.strip()))
                            print(f"   🎯 候选元素: {text.strip()[:40]}")
                    except:
                        continue
            except Exception as e:
                print(f"⚠️  广泛搜索失败: {e}")
        
        return found_elements

    async def try_download_elements(self, page, elements, limit=3):
        """尝试下载元素"""
        print(f"🎯 尝试下载 {min(limit, len(elements))} 个元素...")
        
        download_count = 0
        
        for i, (elem, text) in enumerate(elements[:limit]):
            try:
                print(f"\\n📄 处理元素 {i+1}: {text[:50]}")
                
                # 滚动到元素
                await elem.scroll_into_view_if_needed()
                await page.wait_for_timeout(2000)
                
                # 右键点击
                print("🖱️  右键点击...")
                await elem.click(button='right', timeout=15000)
                await page.wait_for_timeout(3000)
                
                # 查找下载选项 - 基于分析发现的菜单结构
                download_selectors = [
                    'text=下载', 'text=Download', 'text=导出', 'text=Export',
                    '.menu-item:has-text("下载")', '.menu-item:has-text("Download")',
                    '[class*="menu"]:has-text("下载")',
                    '.dui-menu-item:has-text("下载")'  # 基于分析的菜单类名
                ]
                
                download_success = False
                for selector in download_selectors:
                    try:
                        download_btn = await page.wait_for_selector(selector, timeout=5000)
                        if download_btn:
                            await download_btn.click()
                            print(f"✅ 点击下载: {selector}")
                            download_count += 1
                            download_success = True
                            
                            # 等待下载开始
                            await page.wait_for_timeout(3000)
                            
                            # 处理确认对话框
                            try:
                                await page.click('text=允许', timeout=2000)
                            except:
                                try:
                                    await page.click('text=Allow', timeout=2000)
                                except:
                                    pass
                            
                            break
                    except:
                        continue
                
                if not download_success:
                    print("⚠️  未找到下载选项")
                    # 点击空白处关闭菜单
                    await page.click('body')
                
                await page.wait_for_timeout(2000)
                
            except Exception as e:
                print(f"❌ 处理元素失败: {e}")
                continue
        
        return download_count

    async def run_smart_download(self):
        """运行智能下载流程"""
        try:
            print("🌟 开始基于UI分析的智能下载")
            print("=" * 60)
            
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    accept_downloads=True,
                    extra_http_headers={
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    }
                )
                
                await context.add_cookies(self.parse_cookies())
                page = await context.new_page()
                page.on('download', self.handle_download)
                
                # 第一步：访问桌面页面
                print("🏠 访问桌面页面...")
                await page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded', timeout=60000)
                
                # 第二步：智能导航
                await self.smart_navigation(page)
                
                # 第三步：智能查找文档
                elements = await self.find_documents_intelligently(page)
                
                if not elements:
                    print("❌ 未找到任何可操作的文档元素")
                    return False
                
                # 第四步：尝试下载
                downloaded = await self.try_download_elements(page, elements, 3)
                
                # 等待下载完成
                print("⏳ 等待所有下载完成...")
                await page.wait_for_timeout(20000)
                
                await browser.close()
                
                return downloaded > 0
                
        except Exception as e:
            print(f"❌ 智能下载失败: {e}")
            return False

async def main():
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║                    基于UI分析的智能下载器                                 ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    
    downloader = SmartDownloader()
    success = await downloader.run_smart_download()
    
    # 检查结果
    downloads_path = downloader.download_dir
    files = list(downloads_path.glob("*"))
    
    print("\\n" + "=" * 60)
    print("📊 智能下载结果:")
    print(f"📁 下载目录: {downloads_path}")
    print(f"📄 成功下载: {len(downloader.downloaded_files)} 个文件")
    print(f"📄 目录文件: {len(files)} 个文件")
    
    if files:
        print("\\n📋 下载的文件:")
        for i, file_path in enumerate(files, 1):
            size = file_path.stat().st_size
            print(f"{i:2d}. {file_path.name}")
            print(f"     大小: {size:,} 字节")
            print(f"     路径: {file_path}")
    else:
        print("⚠️  下载目录为空")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            print("🎉 智能下载任务完成")
        else:
            print("❌ 智能下载任务失败")
    except Exception as e:
        print(f"💥 程序异常: {e}")