#!/usr/bin/env python3
"""
Windows观察版智能下载器 - 可视化调试
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

class WindowsObservableDownloader:
    def __init__(self):
        # Windows路径适配
        self.download_dir = Path("./downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        self.cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZpaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
        self.downloaded_files = []
        self.debug_mode = True
        
        print(f"📁 Windows下载目录: {self.download_dir}")
        print("👁️  观察模式：浏览器将保持可见，便于观察和调试")

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
            
            # Windows弹窗通知
            if self.debug_mode:
                print(f"🎉 Windows用户请查看: {download_path}")
                
        except Exception as e:
            print(f"❌ 下载失败: {e}")

    async def wait_for_user_input(self, message, timeout_seconds=30):
        """等待用户输入指导"""
        print(f"\n🔔 {message}")
        print(f"   在{timeout_seconds}秒内输入指令 (或直接回车继续):")
        print("   - 'c' 或回车: 继续")
        print("   - 's': 跳过当前步骤") 
        print("   - 'p': 暂停60秒观察")
        print("   - 'q': 退出程序")
        
        try:
            # 简化版：不等待输入，直接继续（Windows环境下可以手动观察）
            await asyncio.sleep(3)  # 给用户3秒观察时间
            return 'c'
        except:
            return 'c'

    async def observable_navigation(self, page):
        """可观察的导航过程"""
        print("\n🧭 开始导航过程...")
        await page.wait_for_timeout(8000)
        
        action = await self.wait_for_user_input("观察页面是否正确加载，用户信息是否正常？")
        if action == 'q':
            return False
        if action == 's':
            print("⏭️  跳过导航，直接在当前页面查找文档")
            return True
            
        # 尝试点击Cloud Docs
        try:
            print("🔍 尝试点击Cloud Docs按钮...")
            cloud_docs_btn = await page.wait_for_selector('text=Cloud Docs', timeout=10000)
            if cloud_docs_btn:
                print("✅ 找到Cloud Docs按钮")
                
                action = await self.wait_for_user_input("是否看到Cloud Docs按钮？要点击吗？")
                if action != 's':
                    # 高亮显示按钮
                    await cloud_docs_btn.evaluate("element => element.style.border = '3px solid red'")
                    await page.wait_for_timeout(2000)
                    
                    await cloud_docs_btn.click()
                    print("🖱️  已点击Cloud Docs")
                    
                    await page.wait_for_timeout(10000)
                    print(f"📍 点击后URL: {page.url}")
                    
                    action = await self.wait_for_user_input("页面是否成功跳转？看到文档列表了吗？")
                    if action == 'q':
                        return False
        except Exception as e:
            print(f"⚠️  Cloud Docs点击失败: {e}")
        
        return True

    async def observable_document_search(self, page):
        """可观察的文档搜索"""
        print("\n🔍 开始搜索文档...")
        
        # 基于服务器分析的选择器，但在Windows环境可视化测试
        selectors_to_try = [
            '.dui-tabs-bar-item',
            '[class*="item"]',
            '.menu-item', 
            '.desktop-sidebar-nav a',
            '.desktop-icon-nav-link',
            'a[href*="pad"]', 'a[href*="sheet"]', 'a[href*="slide"]',
            '[data-*]'
        ]
        
        found_elements = []
        
        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"✅ {selector}: {len(elements)} 个元素")
                    
                    # 高亮显示找到的元素
                    for i, elem in enumerate(elements[:3]):
                        try:
                            await elem.evaluate("element => element.style.border = '2px solid blue'")
                            text = await elem.inner_text()
                            if text and len(text.strip()) > 3:
                                print(f"   {i+1}. {text.strip()[:50]}")
                                
                                # 检查是否可能是文档
                                text_lower = text.lower().strip()
                                if any(keyword in text_lower for keyword in 
                                      ['doc', 'sheet', 'slide', '文档', '表格', '演示']):
                                    found_elements.append((elem, text.strip()))
                                    await elem.evaluate("element => element.style.border = '3px solid green'")
                                    print(f"   ✅ 发现可能的文档: {text.strip()[:40]}")
                        except:
                            continue
                    
                    if found_elements:
                        action = await self.wait_for_user_input(f"找到 {len(found_elements)} 个可能的文档(绿色边框)，继续查找更多还是开始下载？")
                        if action == 's':  # 开始下载
                            break
                        if action == 'q':
                            return []
            except:
                continue
        
        print(f"🎯 总共找到 {len(found_elements)} 个潜在文档元素")
        return found_elements

    async def observable_download_attempt(self, page, elements, limit=3):
        """可观察的下载尝试"""
        print(f"\n⬇️  开始下载尝试 (最多{limit}个)...")
        
        download_count = 0
        for i, (elem, text) in enumerate(elements[:limit]):
            try:
                print(f"\n📄 处理文档 {i+1}: {text[:50]}")
                
                # 高亮当前处理的元素
                await elem.evaluate("element => element.style.border = '4px solid orange'")
                
                action = await self.wait_for_user_input(f"即将处理文档 '{text[:30]}'，继续吗？")
                if action == 'q':
                    break
                if action == 's':
                    continue
                
                # 滚动到元素
                await elem.scroll_into_view_if_needed()
                await page.wait_for_timeout(2000)
                
                # 尝试右键
                print("🖱️  右键点击...")
                await elem.click(button='right')
                await page.wait_for_timeout(3000)
                
                action = await self.wait_for_user_input("右键菜单出现了吗？看到下载选项了吗？")
                if action == 'q':
                    break
                
                # 查找下载选项
                download_selectors = [
                    'text=下载', 'text=Download', 'text=导出', 'text=Export'
                ]
                
                download_success = False
                for selector in download_selectors:
                    try:
                        download_btn = await page.wait_for_selector(selector, timeout=3000)
                        if download_btn:
                            await download_btn.evaluate("element => element.style.border = '3px solid red'")
                            print(f"✅ 找到下载按钮: {selector}")
                            
                            action = await self.wait_for_user_input("看到红色边框的下载按钮了吗？点击吗？")
                            if action != 's':
                                await download_btn.click()
                                print("🎉 已点击下载！")
                                download_count += 1
                                download_success = True
                                
                                await page.wait_for_timeout(3000)
                                # 处理可能的确认对话框
                                try:
                                    await page.click('text=允许', timeout=2000)
                                    print("✅ 已允许下载")
                                except:
                                    pass
                            break
                    except:
                        continue
                
                if not download_success:
                    print("⚠️  未找到或未点击下载选项")
                    await page.click('body')  # 关闭菜单
                
                # 重置高亮
                await elem.evaluate("element => element.style.border = ''")
                
            except Exception as e:
                print(f"❌ 处理文档 {i+1} 失败: {e}")
                continue
        
        return download_count

    async def run_observable_download(self):
        """运行可观察的下载流程"""
        try:
            print("🌟 开始Windows可观察下载流程")
            print("=" * 70)
            
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(
                    headless=False,  # Windows环境使用有头模式
                    slow_mo=1000,    # 放慢操作速度便于观察
                    args=['--start-maximized']  # 最大化窗口
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    accept_downloads=True,
                    extra_http_headers={
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
                    }
                )
                
                await context.add_cookies(self.parse_cookies())
                page = await context.new_page()
                page.on('download', self.handle_download)
                
                print("🏠 访问腾讯文档桌面...")
                await page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded')
                
                # 可观察的导航
                if not await self.observable_navigation(page):
                    return False
                
                # 可观察的文档搜索
                elements = await self.observable_document_search(page)
                
                if not elements:
                    print("❌ 未找到文档元素")
                    action = await self.wait_for_user_input("未找到文档，是否手动指导？")
                    if action == 'q':
                        return False
                
                # 可观察的下载尝试
                if elements:
                    downloaded = await self.observable_download_attempt(page, elements, 3)
                    print(f"🎯 尝试下载了 {downloaded} 个文档")
                
                # 等待下载完成
                print("⏳ 等待下载完成...")
                await page.wait_for_timeout(15000)
                
                action = await self.wait_for_user_input("所有操作完成，是否要关闭浏览器？")
                if action != 's':
                    await browser.close()
                
                return True
                
        except Exception as e:
            print(f"❌ 可观察下载失败: {e}")
            return False

async def main():
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║                Windows环境可观察智能下载器                               ║")
    print("║          浏览器将保持可见，用户可以观察每个步骤并提供指导                  ║") 
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    
    downloader = WindowsObservableDownloader()
    success = await downloader.run_observable_download()
    
    # 检查结果
    files = list(downloader.download_dir.glob("*"))
    
    print("\n" + "=" * 70)
    print("📊 Windows下载结果:")
    print(f"📁 下载目录: {downloader.download_dir}")
    print(f"📄 下载文件数: {len(files)}")
    
    if files:
        print("\n📋 下载的文件:")
        for i, file_path in enumerate(files, 1):
            size = file_path.stat().st_size
            print(f"{i:2d}. {file_path.name}")
            print(f"     大小: {size:,} 字节")
            print(f"     位置: {file_path}")
    
    print("=" * 70)
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        print(f"\n{'🎉 任务完成' if result else '❌ 任务未完成'}")
    except KeyboardInterrupt:
        print("\n👋 用户中断程序")
    except Exception as e:
        print(f"\n💥 程序异常: {e}")