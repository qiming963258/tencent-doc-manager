#!/usr/bin/env python3
"""
腾讯文档极简批量下载器
Tencent Document Bulk Downloader

使用方法:
1. 运行程序: python downloader.py
2. 输入Cookie字符串
3. 自动开始批量下载

Author: Claude Code AI
Version: 1.0
"""

import asyncio
import os
import sys
import json
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from playwright.async_api import async_playwright, BrowserContext, Page

class TencentDocDownloader:
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = Path(download_dir).resolve()
        self.download_dir.mkdir(exist_ok=True)
        self.browser = None
        self.context = None
        self.page = None
        self.cookie_string = ""
        
        print(f"📁 下载目录: {self.download_dir}")

    def parse_cookies(self, cookie_string: str) -> list:
        """解析Cookie字符串为Playwright格式"""
        cookies = []
        for cookie_pair in cookie_string.split('; '):
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
        """设置浏览器环境"""
        print("🚀 启动浏览器...")
        
        playwright = await async_playwright().start()
        
        # 启动Chrome浏览器（服务器环境无头模式）
        self.browser = await playwright.chromium.launch(
            headless=True,  # 服务器环境必须使用无头模式
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--allow-running-insecure-content',
                f'--user-data-dir={self.download_dir}/browser_data'
            ]
        )
        
        # 创建浏览器上下文，使用真实浏览器环境设置
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True,
            permissions=['downloads'],
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'Sec-Ch-Ua': '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin'
            }
        )
        
        # 注入Cookie
        cookies = self.parse_cookies(self.cookie_string)
        await self.context.add_cookies(cookies)
        
        self.page = await self.context.new_page()
        
        # 设置下载处理
        self.page.on('download', self.handle_download)
        
        print("✅ 浏览器设置完成")

    async def handle_download(self, download):
        """处理下载事件"""
        filename = download.suggested_filename
        download_path = self.download_dir / filename
        
        print(f"⬇️  下载: {filename}")
        await download.save_as(download_path)
        print(f"✅ 完成: {filename}")

    async def validate_cookie(self) -> bool:
        """验证Cookie有效性"""
        print("🔍 验证Cookie有效性...")
        
        try:
            # 先测试用户信息API（确保认证有效）
            api_response = await self.page.goto('https://docs.qq.com/cgi-bin/online_docs/user_info?xsrf=25ea7d9ac7e65c7d&get_vip_info=1',
                                              wait_until='domcontentloaded', timeout=30000)
            
            if api_response.status == 200:
                print("✅ API认证成功")
            else:
                print(f"⚠️  API认证状态: {api_response.status}")
            
            # 访问腾讯文档桌面主页
            await self.page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded', timeout=30000)
            
            # 等待页面加载完成
            await self.page.wait_for_timeout(5000)
            
            # 检查是否成功登录（查找用户相关元素）
            login_indicators = [
                '.desktop-user-info',
                '.user-avatar',
                '[data-testid="user-info"]',
                '.header-user',
                '[class*="user"]'
            ]
            
            for indicator in login_indicators:
                try:
                    element = await self.page.wait_for_selector(indicator, timeout=5000)
                    if element:
                        print("✅ Cookie验证成功，已登录")
                        return True
                except:
                    continue
            
            # 检查是否显示登录页面
            login_page_indicators = [
                '.login-container',
                '.qrcode-login',
                'text=登录'
            ]
            
            for indicator in login_page_indicators:
                try:
                    element = await self.page.wait_for_selector(indicator, timeout=2000)
                    if element:
                        print("❌ Cookie验证失败，未登录")
                        return False
                except:
                    continue
            
            # 获取页面标题
            title = await self.page.title()
            if '腾讯文档' in title and '登录' not in title:
                print("✅ Cookie验证成功（基于页面标题）")
                return True
            
            print("⚠️  Cookie状态不确定，尝试继续...")
            return True
            
        except Exception as e:
            print(f"❌ Cookie验证失败: {e}")
            return False

    async def setup_filters(self):
        """设置筛选条件：我所有 + 近一个月"""
        print("🔧 设置筛选条件...")
        
        try:
            # 等待页面加载完成
            await self.page.wait_for_timeout(2000)
            
            # 查找并点击筛选按钮
            filter_button_selectors = [
                'button.desktop-filter-button-inner-pc',
                'button[class*="filter-button"]',
                '.desktop-filter-button-pc',
                'text=筛选'
            ]
            
            filter_clicked = False
            for selector in filter_button_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.click(selector)
                    print("✅ 已点击筛选按钮")
                    filter_clicked = True
                    break
                except Exception as e:
                    print(f"⚠️  尝试筛选按钮选择器 {selector} 失败: {e}")
                    continue
            
            if not filter_clicked:
                print("⚠️  未找到筛选按钮，可能页面结构已变化")
                return False
            
            # 等待筛选面板出现
            await self.page.wait_for_timeout(1000)
            
            # 查找并选择"我所有"选项
            try:
                # 查找所有radio按钮
                radio_buttons = await self.page.query_selector_all('input[type="radio"]')
                print(f"🔍 找到 {len(radio_buttons)} 个选项")
                
                # 通常第一个是"我所有"，第二个可能是"近一个月"
                if len(radio_buttons) >= 2:
                    # 点击"我所有"（通常是第一个）
                    await radio_buttons[0].click()
                    print("✅ 已选择'我所有'")
                    
                    await self.page.wait_for_timeout(500)
                    
                    # 点击"近一个月"（查找文本相关的radio）
                    # 尝试查找包含时间相关文本的元素
                    time_options = await self.page.query_selector_all('text=/近.*月|最近|月/')
                    if time_options:
                        for option in time_options:
                            try:
                                # 查找该文本元素关联的radio按钮
                                parent = await option.query_selector('xpath=..')
                                radio = await parent.query_selector('input[type="radio"]')
                                if radio:
                                    await radio.click()
                                    print("✅ 已选择时间筛选")
                                    break
                            except:
                                continue
                    else:
                        # 如果找不到特定的时间选项，尝试点击第二个radio
                        if len(radio_buttons) >= 4:  # 假设有文件类型和时间筛选
                            await radio_buttons[2].click()  # 尝试时间筛选的第一个选项
                            print("✅ 已选择时间筛选（默认）")
                
                # 等待筛选生效
                await self.page.wait_for_timeout(2000)
                print("✅ 筛选条件设置完成")
                return True
                
            except Exception as e:
                print(f"⚠️  设置筛选选项时出错: {e}")
                # 即使筛选设置失败，也继续执行
                return True
                
        except Exception as e:
            print(f"⚠️  筛选设置失败: {e}")
            print("继续执行下载...")
            return True

    async def load_all_files(self) -> int:
        """滚动加载所有文件，返回文件总数"""
        print("📜 开始滚动加载所有文件...")
        
        last_file_count = 0
        stable_count = 0
        max_attempts = 50  # 最大滚动次数
        
        for attempt in range(max_attempts):
            # 滚动到页面底部
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # 等待内容加载
            await self.page.wait_for_timeout(2000)
            
            # 计算当前文件行数
            try:
                # 尝试不同的文件行选择器
                file_selectors = [
                    '.desktop-file-list-item',
                    '.file-item',
                    '.document-item',
                    '[data-testid*="file"]',
                    '.desktop-list-view-item'
                ]
                
                current_file_count = 0
                for selector in file_selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if elements and len(elements) > current_file_count:
                            current_file_count = len(elements)
                        break
                    except:
                        continue
                
                print(f"🔍 第{attempt + 1}次滚动，当前文件数: {current_file_count}")
                
                # 如果文件数没有增加，增加稳定计数
                if current_file_count == last_file_count:
                    stable_count += 1
                    if stable_count >= 3:  # 连续3次无变化，认为加载完成
                        print(f"✅ 滚动加载完成，总共发现 {current_file_count} 个文件")
                        return current_file_count
                else:
                    stable_count = 0
                    last_file_count = current_file_count
                
            except Exception as e:
                print(f"⚠️  统计文件数时出错: {e}")
                
        print(f"✅ 达到最大滚动次数，当前文件数: {last_file_count}")
        return last_file_count

    async def download_all_files(self):
        """批量下载所有文件"""
        print("🎯 开始批量下载...")
        
        try:
            # 查找所有文件行
            file_selectors = [
                '.desktop-file-list-item',
                '.file-item',
                '.document-item',
                '[data-testid*="file"]',
                '.desktop-list-view-item'
            ]
            
            file_elements = []
            for selector in file_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        file_elements = elements
                        print(f"✅ 使用选择器 {selector}，找到 {len(elements)} 个文件")
                        break
                except:
                    continue
            
            if not file_elements:
                print("❌ 未找到文件元素，可能页面结构已变化")
                return
            
            print(f"🚀 开始下载 {len(file_elements)} 个文件...")
            successful_downloads = 0
            
            for i, file_element in enumerate(file_elements):
                try:
                    print(f"\n📄 处理第 {i + 1}/{len(file_elements)} 个文件...")
                    
                    # 获取文件名（用于日志）
                    try:
                        file_name = await file_element.inner_text()
                        if file_name:
                            print(f"📝 文件: {file_name[:50]}...")
                    except:
                        print(f"📝 文件: [第{i + 1}个]")
                    
                    # 滚动到元素位置
                    await file_element.scroll_into_view_if_needed()
                    await self.page.wait_for_timeout(500)
                    
                    # 右键点击元素
                    await file_element.click(button='right')
                    print("🖱️  已右键点击")
                    
                    # 等待菜单出现
                    await self.page.wait_for_timeout(1000)
                    
                    # 查找下载选项
                    download_selectors = [
                        'text=下载',
                        '.desktop-menu-item-content:has-text("下载")',
                        '[data-testid*="download"]',
                        '.menu-item:has-text("下载")'
                    ]
                    
                    download_clicked = False
                    for selector in download_selectors:
                        try:
                            download_element = await self.page.wait_for_selector(selector, timeout=3000)
                            if download_element:
                                await download_element.click()
                                print("✅ 已点击下载")
                                download_clicked = True
                                successful_downloads += 1
                                break
                        except:
                            continue
                    
                    if not download_clicked:
                        print("⚠️  未找到下载选项")
                    
                    # 等待下载开始
                    await self.page.wait_for_timeout(1500)
                    
                    # 处理可能的浏览器下载确认对话框
                    try:
                        # 如果出现"此网站想要下载多个文件"的提示，点击允许
                        await self.page.click('text=允许', timeout=1000)
                        print("✅ 已允许下载")
                    except:
                        pass  # 没有对话框，继续
                    
                except Exception as e:
                    print(f"❌ 下载第 {i + 1} 个文件失败: {e}")
                    continue
            
            print(f"\n🎉 批量下载完成！")
            print(f"✅ 成功处理: {successful_downloads}/{len(file_elements)} 个文件")
            print(f"📁 文件保存在: {self.download_dir}")
                    
        except Exception as e:
            print(f"❌ 批量下载过程出错: {e}")

    async def run(self, cookie_string: str):
        """运行完整下载流程"""
        self.cookie_string = cookie_string
        
        try:
            # 1. 设置浏览器
            await self.setup_browser()
            
            # 2. 验证Cookie
            if not await self.validate_cookie():
                print("❌ Cookie验证失败，请检查Cookie是否有效")
                return False
            
            # 3. 设置筛选条件
            await self.setup_filters()
            
            # 4. 滚动加载所有文件
            file_count = await self.load_all_files()
            if file_count == 0:
                print("⚠️  未找到任何文件")
                return False
            
            # 5. 批量下载
            await self.download_all_files()
            
            return True
            
        except Exception as e:
            print(f"❌ 执行过程出错: {e}")
            return False
        
        finally:
            if self.browser:
                await self.browser.close()
                print("🔚 浏览器已关闭")

async def main():
    """主函数"""
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║                     腾讯文档极简批量下载器                                  ║")
    print("║                  Tencent Document Bulk Downloader                        ║")
    print("║                                                                          ║")
    print("║  🎯 只需输入Cookie，自动批量下载所有文档                                    ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # 输入Cookie
    print("请输入腾讯文档Cookie字符串:")
    print("💡 提示: Cookie应该类似 'RK=xxx; ptcz=xxx; uid=xxx; ...'")
    print()
    
    cookie_input = input("🔑 Cookie: ").strip()
    
    if not cookie_input:
        print("❌ Cookie不能为空")
        sys.exit(1)
    
    print(f"📊 Cookie长度: {len(cookie_input)} 字符")
    print()
    
    # 创建下载器实例
    downloader = TencentDocDownloader()
    
    # 开始下载
    success = await downloader.run(cookie_input)
    
    if success:
        print("\n🎉 下载任务完成！")
    else:
        print("\n❌ 下载任务失败！")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 用户中断程序")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1)