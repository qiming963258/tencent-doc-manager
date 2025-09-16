#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows兼容版智能下载器 - 解决中文编码问题
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

class WindowsCompatibleDownloader:
    def __init__(self):
        # Windows路径适配
        self.download_dir = Path("./downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        self.cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZpaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
        self.downloaded_files = []
        self.debug_mode = True
        
        print("[FOLDER] Windows下载目录:", str(self.download_dir))
        print("[EYE] 观察模式：浏览器将保持可见，便于观察和调试")

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
            print("[DOWN] 下载:", filename)
            await download.save_as(download_path)
            self.downloaded_files.append(str(download_path))
            file_size = download_path.stat().st_size if download_path.exists() else 0
            print("[OK] 完成:", filename, f"({file_size:,} 字节)")
            
            # Windows弹窗通知
            if self.debug_mode:
                print("[WIN] Windows用户请查看:", str(download_path))
                
        except Exception as e:
            print("[ERROR] 下载失败:", str(e))

    async def wait_for_user_observation(self, message, wait_seconds=8):
        """等待用户观察页面状态"""
        print(f"\n[WAIT] {message}")
        print(f"[INFO] 等待 {wait_seconds} 秒供观察...")
        await asyncio.sleep(wait_seconds)

    async def highlight_element(self, page, selector, color="red"):
        """高亮显示找到的元素"""
        try:
            await page.evaluate(f"""
                (selector) => {{
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {{
                        el.style.border = '3px solid {color}';
                        el.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
                        el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }});
                    return elements.length;
                }}
            """, selector)
        except:
            pass

    async def verify_access(self):
        """验证访问权限和用户状态"""
        try:
            print("\n[STEP] 验证用户权限状态...")
            
            # API认证测试
            response = await self.page.goto(
                'https://docs.qq.com/cgi-bin/online_docs/user_info?xsrf=25ea7d9ac7e65c7d&get_vip_info=1',
                wait_until='domcontentloaded',
                timeout=30000
            )
            
            print("[API] 状态码:", response.status)
            if response.status == 200:
                print("[OK] API认证成功")
                
            # 回到桌面页面
            await self.page.goto('https://docs.qq.com/desktop/', 
                                wait_until='domcontentloaded', timeout=30000)
            
            await self.wait_for_user_observation("【观察点1】请查看页面右上角用户信息是否正常显示", 10)
            
            # 检查页面内容
            try:
                page_content = await self.page.content()
                if 'userType":"guest"' in page_content:
                    print("[WARN] 页面显示为guest用户，但API认证成功，继续执行")
                elif 'uid":"144115414584628119"' in page_content:
                    print("[OK] 发现用户ID，认证状态良好")
                    
                title = await self.page.title()
                print("[PAGE] 页面标题:", title)
                print("[URL] 当前URL:", self.page.url)
                return True
                
            except Exception as e:
                print("[WARN] 内容检查异常:", str(e))
                return True  # API成功就继续
                
        except Exception as e:
            print("[ERROR] 验证失败:", str(e))
            return False

    async def navigate_to_documents(self):
        """导航到文档列表页面"""
        print("\n[STEP] 导航到文档列表...")
        
        try:
            await self.wait_for_user_observation("【观察点2】查找并准备点击Cloud Docs导航按钮", 8)
            
            # 尝试多种导航方式
            navigation_selectors = [
                'text=Cloud Docs',
                'text=文档',
                'text=我的文档', 
                '[class*="cloud"]',
                '[href*="/desktop"]',
                'button:has-text("Cloud")',
                'a:has-text("Cloud")',
                '.dui-tabs-bar-item:has-text("Cloud")'
            ]
            
            nav_success = False
            for selector in navigation_selectors:
                try:
                    print(f"[TRY] 尝试选择器: {selector}")
                    await self.highlight_element(self.page, selector, "blue")
                    
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        print(f"[FOUND] 找到导航元素: {selector}")
                        await element.click()
                        print(f"[CLICK] 成功点击导航")
                        nav_success = True
                        break
                except Exception as e:
                    print(f"[SKIP] {selector} 不可用: {str(e)[:50]}")
                    continue
            
            if nav_success:
                await self.wait_for_user_observation("【观察点3】导航点击后页面是否跳转到文档列表", 10)
                print("[URL] 导航后URL:", self.page.url)
                print("[PAGE] 导航后标题:", await self.page.title())
            else:
                print("[TRY] 尝试直接访问文档列表URL")
                await self.page.goto('https://docs.qq.com/desktop/mydocs', 
                                    wait_until='domcontentloaded', timeout=30000)
                await self.wait_for_user_observation("【观察点4】直接访问mydocs页面结果", 8)
            
            return True
        except Exception as e:
            print("[ERROR] 导航失败:", str(e))
            return False

    async def find_documents(self):
        """查找页面上的文档元素"""
        print("\n[STEP] 查找文档元素...")
        
        await self.wait_for_user_observation("【观察点5】查看页面是否显示文档列表", 8)
        
        # 多种文档选择器
        document_selectors = [
            '[class*="file-item"]',
            '[class*="document"]', 
            '[class*="item"]',
            '.dui-list-item',
            '[data-test*="file"]',
            '[role="listitem"]',
            '.file-name',
            'a[href*="/doc/"]',
            'tr[class*="file"]'
        ]
        
        found_documents = []
        for selector in document_selectors:
            try:
                print(f"[SEARCH] 搜索选择器: {selector}")
                await self.highlight_element(self.page, selector, "green")
                
                elements = await self.page.query_selector_all(selector)
                if elements:
                    print(f"[FOUND] {selector}: {len(elements)}个元素")
                    for i, element in enumerate(elements[:5]):  # 只处理前5个
                        try:
                            text = await element.inner_text()
                            print(f"  [{i+1}] 内容: {text[:50]}...")
                            found_documents.append((element, text))
                        except:
                            pass
                    
                    if found_documents:
                        break  # 找到就停止搜索
                        
            except Exception as e:
                print(f"[SKIP] {selector} 搜索失败: {str(e)[:30]}")
        
        await self.wait_for_user_observation(f"【观察点6】找到{len(found_documents)}个文档元素，高亮显示", 10)
        return found_documents

    async def download_documents(self, max_count=3):
        """尝试下载文档"""
        print(f"\n[STEP] 开始下载最多{max_count}个文档...")
        
        documents = await self.find_documents()
        if not documents:
            print("[ERROR] 未找到任何可下载的文档元素")
            return []
        
        downloaded = []
        for i, (element, text) in enumerate(documents[:max_count]):
            try:
                print(f"\n[DOC {i+1}] 尝试下载: {text[:30]}...")
                
                await self.wait_for_user_observation(f"【观察点7】准备右键点击文档{i+1}", 5)
                
                # 滚动到元素
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                
                # 右键点击触发下载
                await element.click(button='right')
                await asyncio.sleep(2)
                
                # 查找下载相关选项
                download_selectors = [
                    'text=下载', 'text=Download', 'text=导出', 'text=Export',
                    '[class*="download"]', '[data-action="download"]'
                ]
                
                download_clicked = False
                for sel in download_selectors:
                    try:
                        download_option = await self.page.wait_for_selector(sel, timeout=3000)
                        if download_option:
                            await download_option.click()
                            print(f"[CLICK] 点击下载选项: {sel}")
                            download_clicked = True
                            break
                    except:
                        continue
                
                if download_clicked:
                    await asyncio.sleep(3)  # 等待下载开始
                    downloaded.append(text)
                    print(f"[SUCCESS] 文档{i+1}下载请求已发送")
                else:
                    print(f"[MISS] 文档{i+1}未找到下载选项")
                    
            except Exception as e:
                print(f"[ERROR] 文档{i+1}下载失败: {str(e)}")
                
        await self.wait_for_user_observation(f"【最终观察】检查downloads文件夹，应有{len(downloaded)}个文件", 15)
        
        return downloaded

    async def run_download_task(self):
        """执行主要的下载任务"""
        print("\n" + "="*60)
        print("     Windows环境腾讯文档自动化下载 - 可观察版")
        print("        浏览器将保持可见，便于用户观察全过程") 
        print("="*60)
        
        async with async_playwright() as playwright:
            print("\n[START] 启动Chrome浏览器...")
            browser = await playwright.chromium.launch(
                headless=False,  # Windows下使用有头模式！
                args=[
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--start-maximized'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                accept_downloads=True
            )
            
            # 监听下载事件
            context.on('download', self.handle_download)
            
            self.page = await context.new_page()
            
            # 设置Cookie
            print("[SETUP] 设置Cookie认证...")
            await context.add_cookies(self.parse_cookies())
            
            try:
                # 1. 验证访问权限
                if not await self.verify_access():
                    return False
                
                # 2. 导航到文档列表 
                if not await self.navigate_to_documents():
                    print("[WARN] 导航失败，但继续尝试查找文档")
                
                # 3. 下载文档
                downloaded = await self.download_documents(3)
                
                print(f"\n[RESULT] 下载完成！共处理 {len(downloaded)} 个文档")
                print(f"[FILES] 实际下载文件: {len(self.downloaded_files)} 个")
                for file_path in self.downloaded_files:
                    print(f"  - {file_path}")
                
                await self.wait_for_user_observation("【任务完成】请检查最终结果", 10)
                
                return True
                
            except Exception as e:
                print(f"[ERROR] 执行异常: {str(e)}")
                return False
            finally:
                print("[WAIT] 保持浏览器10秒供最终观察...")
                await asyncio.sleep(10)
                await browser.close()

async def main():
    print("="*60)
    print("        Windows环境腾讯文档可观察下载器")
    print("     解决编码问题，支持实时观察和调试")
    print("="*60)
    
    downloader = WindowsCompatibleDownloader()
    success = await downloader.run_download_task()
    
    if success:
        print("\n[COMPLETE] 任务执行完成！请检查downloads文件夹中的文件。")
    else:
        print("\n[FAILED] 任务执行失败，请查看上述日志了解具体问题。")
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] 用户中断执行")
    except Exception as e:
        print(f"\n[FATAL] 程序异常: {str(e)}")