#!/usr/bin/env python3
"""
服务器环境腾讯文档自动下载器 - 下载10个文档
Server Environment Tencent Document Downloader
"""

import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright

class ServerDownloader:
    def __init__(self):
        self.download_dir = Path("/root/projects/tencent-doc-manager/enterprise_download_system/downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        self.browser = None
        self.context = None
        self.page = None
        
        # 用户提供的Cookie
        self.cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZpaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
        
        print(f"📁 下载目录: {self.download_dir}")

    def parse_cookies(self):
        """解析Cookie字符串"""
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
        """设置服务器环境浏览器"""
        print("🚀 启动服务器环境浏览器...")
        
        playwright = await async_playwright().start()
        
        # 无头模式启动，适配服务器环境
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection'
            ]
        )
        
        # 创建浏览器上下文
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True,
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'Sec-Ch-Ua': '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
            }
        )
        
        # 注入Cookie
        cookies = self.parse_cookies()
        await self.context.add_cookies(cookies)
        
        self.page = await self.context.new_page()
        
        # 设置下载事件处理
        self.page.on('download', self.handle_download)
        
        print("✅ 服务器浏览器环境设置完成")

    async def handle_download(self, download):
        """处理下载事件"""
        try:
            filename = download.suggested_filename
            download_path = self.download_dir / filename
            
            print(f"⬇️  开始下载: {filename}")
            await download.save_as(download_path)
            print(f"✅ 下载完成: {filename} -> {download_path}")
            
            # 记录下载文件信息
            file_size = download_path.stat().st_size if download_path.exists() else 0
            print(f"📊 文件大小: {file_size} 字节")
            
        except Exception as e:
            print(f"❌ 下载处理失败: {e}")

    async def verify_access(self):
        """验证访问权限"""
        print("🔍 验证Cookie和访问权限...")
        
        try:
            # 测试API访问
            response = await self.page.goto('https://docs.qq.com/cgi-bin/online_docs/user_info?xsrf=25ea7d9ac7e65c7d&get_vip_info=1',
                                          wait_until='domcontentloaded', timeout=30000)
            
            if response.status == 200:
                print("✅ API认证成功")
                # API成功说明Cookie有效，继续进行
            else:
                print(f"⚠️  API状态: {response.status}")
                
            # 访问桌面页面
            print("🏠 访问桌面主页...")
            response2 = await self.page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded', timeout=30000)
            print(f"📊 桌面页面状态码: {response2.status}")
            
            # 增加更长的等待时间
            await self.page.wait_for_timeout(8000)
            
            title = await self.page.title()
            print(f"📄 页面标题: {title}")
            
            # 获取页面URL确认
            current_url = self.page.url
            print(f"📍 当前URL: {current_url}")
            
            # 检查页面内容而不仅仅是标题
            try:
                page_content = await self.page.content()
                if '登录' in page_content and ('扫码' in page_content or 'login' in page_content.lower()):
                    print("⚠️  页面显示需要登录，但API认证成功，强制继续执行")
                    # 不返回False，继续执行
                elif 'desktop' in current_url.lower() or 'docs' in title.lower():
                    print("✅ 桌面页面访问成功（基于URL和内容）")
                    return True
                else:
                    print("⚠️  页面状态不确定，但API认证成功，继续尝试...")
                    return True
            except Exception as e:
                print(f"⚠️  内容检查失败: {e}")
            
            # 如果API成功，就继续尝试
            if response.status == 200:
                print("✅ 基于API认证成功，强制继续执行")
                return True
            return False
                
        except Exception as e:
            print(f"❌ 验证失败: {e}")
            return False

    async def navigate_to_documents(self):
        """导航到文档列表页面"""
        print("🧭 导航到文档列表...")
        
        try:
            # 等待页面完全加载
            await self.page.wait_for_timeout(5000)
            
            # 尝试点击"Cloud Docs"按钮来进入文档页面
            navigation_selectors = [
                'text=Cloud Docs',
                'text=文档',
                'text=我的文档',
                '[class*="cloud"]',
                '[href*="/desktop"]',
                'button:has-text("Cloud")',
                'a:has-text("Cloud")'
            ]
            
            nav_success = False
            for selector in navigation_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.click()
                        print(f"✅ 成功点击导航: {selector}")
                        nav_success = True
                        break
                except:
                    continue
            
            if nav_success:
                # 等待导航后的页面加载
                await self.page.wait_for_timeout(8000)
                print(f"📄 导航后页面标题: {await self.page.title()}")
                print(f"📍 导航后URL: {self.page.url}")
            else:
                print("⚠️  未找到导航按钮，尝试直接访问文档列表URL")
                # 尝试直接访问文档列表页面
                await self.page.goto('https://docs.qq.com/desktop/mydocs', wait_until='domcontentloaded', timeout=30000)
                await self.page.wait_for_timeout(5000)
                print("✅ 直接访问文档列表页面")
            
            return True
        except Exception as e:
            print(f"❌ 导航失败: {e}")
            return False

    async def setup_filters(self):
        """设置筛选条件"""
        print("🔧 设置筛选条件（我所有+近一个月）...")
        
        try:
            await self.page.wait_for_timeout(3000)
            
            # 查找筛选按钮
            filter_selectors = [
                'button.desktop-filter-button-inner-pc',
                'button[class*="filter-button"]',
                '.desktop-filter-button-pc',
                'text=筛选'
            ]
            
            for selector in filter_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.click(selector)
                    print("✅ 筛选按钮点击成功")
                    break
                except:
                    continue
            
            await self.page.wait_for_timeout(2000)
            
            # 设置筛选选项
            radio_buttons = await self.page.query_selector_all('input[type="radio"]')
            if len(radio_buttons) >= 2:
                await radio_buttons[0].click()  # 我所有
                await self.page.wait_for_timeout(500)
                if len(radio_buttons) >= 4:
                    await radio_buttons[2].click()  # 时间筛选
                
            await self.page.wait_for_timeout(3000)
            print("✅ 筛选条件设置完成")
            
        except Exception as e:
            print(f"⚠️  筛选设置失败，继续执行: {e}")

    async def load_all_content(self):
        """滚动加载所有内容"""
        print("📜 滚动加载所有内容...")
        
        last_file_count = 0
        stable_count = 0
        max_attempts = 30
        
        for attempt in range(max_attempts):
            # 滚动到底部
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(3000)
            
            # 统计文件数量
            file_selectors = [
                '.desktop-file-list-item',
                '.file-item',
                '.desktop-list-view-item',
                '[data-testid*="file"]'
            ]
            
            current_count = 0
            for selector in file_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    current_count = max(current_count, len(elements))
                except:
                    continue
            
            print(f"🔄 滚动 {attempt + 1}/{max_attempts}，当前文件数: {current_count}")
            
            if current_count == last_file_count:
                stable_count += 1
                if stable_count >= 3:
                    break
            else:
                stable_count = 0
                last_file_count = current_count
        
        print(f"✅ 内容加载完成，共 {last_file_count} 个文件")
        return last_file_count

    async def download_documents(self, limit=10):
        """下载文档"""
        print(f"🎯 开始下载前 {limit} 个文档...")
        
        try:
            # 获取文件元素
            file_selectors = [
                '.desktop-file-list-item',
                '.file-item', 
                '.desktop-list-view-item',
                '[data-testid*="file"]'
            ]
            
            file_elements = []
            for selector in file_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        file_elements = elements[:limit]
                        print(f"✅ 找到 {len(file_elements)} 个文件元素")
                        break
                except:
                    continue
            
            if not file_elements:
                print("❌ 未找到文件元素")
                return 0
            
            downloaded_count = 0
            skipped_count = 0
            
            for i, file_element in enumerate(file_elements):
                try:
                    print(f"\n📄 处理文件 {i + 1}/{len(file_elements)}...")
                    
                    # 滚动到元素
                    await file_element.scroll_into_view_if_needed()
                    await self.page.wait_for_timeout(1000)
                    
                    # 获取文件名
                    try:
                        file_text = await file_element.inner_text()
                        file_name = file_text.replace('\n', ' ')[:50] if file_text else f"文件{i+1}"
                        print(f"📝 {file_name}")
                    except:
                        file_name = f"文件{i+1}"
                    
                    # 右键点击
                    await file_element.click(button='right')
                    print("🖱️  右键点击成功")
                    
                    await self.page.wait_for_timeout(2000)
                    
                    # 查找并点击下载
                    download_selectors = [
                        'text=下载',
                        '.desktop-menu-item-content:has-text("下载")',
                        '[data-testid*="download"]',
                        '.menu-item:has-text("下载")',
                        '.context-menu-item:has-text("下载")'
                    ]
                    
                    download_found = False
                    for selector in download_selectors:
                        try:
                            download_elem = await self.page.wait_for_selector(selector, timeout=3000)
                            if download_elem:
                                await download_elem.click()
                                print("✅ 下载点击成功")
                                downloaded_count += 1
                                download_found = True
                                break
                        except:
                            continue
                    
                    if not download_found:
                        print("⚠️  未找到下载选项，跳过")
                        skipped_count += 1
                        await self.page.click('body')  # 关闭菜单
                    
                    await self.page.wait_for_timeout(2000)
                    
                    # 处理下载确认
                    try:
                        await self.page.click('text=允许', timeout=1000)
                    except:
                        pass
                    
                except Exception as e:
                    print(f"❌ 处理文件{i+1}失败: {e}")
                    skipped_count += 1
                    continue
            
            print(f"\n🎉 下载处理完成！")
            print(f"✅ 成功下载: {downloaded_count}")
            print(f"⚠️  跳过文件: {skipped_count}")
            
            return downloaded_count
            
        except Exception as e:
            print(f"❌ 下载过程出错: {e}")
            return 0

    async def run_download_task(self):
        """执行下载任务"""
        try:
            print("🌟 开始自动化下载任务")
            print("=" * 60)
            
            # 1. 设置浏览器
            await self.setup_browser()
            
            # 2. 验证访问
            if not await self.verify_access():
                return False
            
            # 3. 导航到文档列表
            if not await self.navigate_to_documents():
                print("❌ 导航到文档列表失败")
                return False
            
            # 4. 设置筛选
            await self.setup_filters()
            
            # 5. 加载内容
            await self.load_all_content()
            
            # 6. 下载文档
            downloaded = await self.download_documents(10)
            
            # 等待所有下载完成
            print("⏳ 等待下载完成...")
            await self.page.wait_for_timeout(10000)
            
            return downloaded > 0
            
        except Exception as e:
            print(f"❌ 任务执行失败: {e}")
            return False
            
        finally:
            if self.browser:
                await self.browser.close()
                print("🔚 浏览器已关闭")

async def main():
    """主函数"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║              服务器环境自动化下载 - 10个文档测试                ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    downloader = ServerDownloader()
    success = await downloader.run_download_task()
    
    # 检查下载结果
    downloads_path = Path("/root/projects/tencent-doc-manager/enterprise_download_system/downloads")
    downloaded_files = list(downloads_path.glob("*"))
    
    print("\n" + "=" * 60)
    print("📊 下载结果统计:")
    print(f"📁 下载目录: {downloads_path}")
    print(f"📄 下载文件数: {len(downloaded_files)}")
    
    if downloaded_files:
        print("\n📋 已下载文件列表:")
        for i, file_path in enumerate(downloaded_files, 1):
            file_size = file_path.stat().st_size
            print(f"{i:2d}. {file_path.name} ({file_size:,} 字节)")
            print(f"     路径: {file_path}")
    else:
        print("⚠️  未发现下载文件")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            print("🎉 自动化下载任务完成")
        else:
            print("❌ 自动化下载任务失败")
    except Exception as e:
        print(f"💥 程序异常: {e}")