#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版安全下载器 - 解决下滑刷新、导出弹窗、按次序下载问题
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

class OptimizedDownloader:
    def __init__(self):
        self.download_dir = Path("./downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        
        # 使用验证有效的最新Cookie
        self.cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZwaEVRbVE0eVFlTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1UQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; dark_mode_setting=system"
        
        self.downloaded_files = []
        self.processed_docs = set()
        
        print("[SETUP] 优化版安全下载器")
        print("[SETUP] 解决下滑刷新、导出弹窗、按次序下载问题")

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
            print(f"[DOWNLOAD] 开始下载: {filename}")
            await download.save_as(download_path)
            self.downloaded_files.append(str(download_path))
            file_size = download_path.stat().st_size if download_path.exists() else 0
            print(f"[SUCCESS] 下载完成: {filename} ({file_size:,} 字节)")
        except Exception as e:
            print(f"[ERROR] 下载失败: {e}")

    async def setup_dialog_handlers(self):
        """设置弹窗处理器"""
        print("[SETUP] 设置弹窗处理器...")
        
        # 处理JavaScript弹窗
        self.page.on("dialog", lambda dialog: dialog.accept())
        
        # 监听新页面打开（处理文档打开）
        def handle_new_page(page):
            print("[INFO] 检测到新页面打开，将在稍后关闭")
            # 不立即关闭，等下载完成后统一处理
        
        self.page.context.on("page", handle_new_page)
        print("[SETUP] 弹窗处理器设置完成")

    async def scroll_and_load_more_documents(self):
        """下滑刷新列表，加载更多文档"""
        print("\n[SCROLL] 开始下滑加载更多文档...")
        
        doc_selectors = [
            'a[href*="/doc/"]',
            'a[href*="/sheet/"]',
            'a[href*="/slide/"]',
            'a[href*="/form/"]'
        ]
        
        all_docs = {}
        last_count = 0
        scroll_attempts = 0
        max_scrolls = 10
        
        while scroll_attempts < max_scrolls:
            print(f"\n[SCROLL {scroll_attempts + 1}] 扫描当前页面文档...")
            
            # 扫描当前可见文档
            current_docs = {}
            for selector in doc_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    
                    for element in elements:
                        try:
                            doc_info = await element.evaluate('''(el) => {
                                return {
                                    href: el.href || el.getAttribute('href') || '',
                                    title: el.textContent || el.innerText || el.getAttribute('title') || '未知文档',
                                    rect: {
                                        x: el.getBoundingClientRect().x,
                                        y: el.getBoundingClientRect().y,
                                        width: el.getBoundingClientRect().width,
                                        height: el.getBoundingClientRect().height
                                    }
                                };
                            }''')
                            
                            href = doc_info['href']
                            title = doc_info['title']
                            rect = doc_info['rect']
                            
                            if href and href not in current_docs and title.strip():
                                current_docs[href] = {
                                    'href': href,
                                    'title': title.strip()[:50],
                                    'position': rect,
                                    'type': self.get_doc_type(href)
                                }
                                
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    continue
            
            # 更新总文档列表
            all_docs.update(current_docs)
            current_count = len(all_docs)
            
            print(f"[SCROLL {scroll_attempts + 1}] 当前总文档数: {current_count}")
            
            # 检查是否有新文档
            if current_count == last_count:
                print(f"[SCROLL {scroll_attempts + 1}] 没有发现新文档")
                if scroll_attempts >= 3:  # 连续3次没有新文档就停止
                    print("[SCROLL] 连续多次无新文档，停止滚动")
                    break
            else:
                new_docs = current_count - last_count
                print(f"[SCROLL {scroll_attempts + 1}] 发现 {new_docs} 个新文档")
                last_count = current_count
                
                # 如果已经有足够多的文档，可以停止
                if current_count >= 20:
                    print(f"[SCROLL] 已获取足够文档 ({current_count} 个)，停止滚动")
                    break
            
            # 滚动到页面底部
            print(f"[SCROLL {scroll_attempts + 1}] 向下滚动...")
            await self.page.evaluate('''() => {
                window.scrollTo(0, document.body.scrollHeight);
            }''')
            
            # 等待新内容加载
            await asyncio.sleep(4)
            
            # 检查是否有"加载更多"按钮
            load_more_selectors = [
                'button:has-text("加载更多")',
                'text=加载更多',
                'text=查看更多',
                '[class*="load-more"]'
            ]
            
            for selector in load_more_selectors:
                try:
                    btn = await self.page.wait_for_selector(selector, timeout=2000)
                    if btn and await btn.is_visible():
                        await btn.click()
                        print(f"[SCROLL {scroll_attempts + 1}] 点击了加载更多按钮")
                        await asyncio.sleep(3)
                        break
                except:
                    continue
            
            scroll_attempts += 1
        
        # 按位置排序
        sorted_docs = sorted(all_docs.values(), 
                           key=lambda x: x['position']['y'] if x['position'] else 0)
        
        print(f"\n[SCROLL] 滚动完成，总共找到 {len(sorted_docs)} 个文档:")
        for i, doc in enumerate(sorted_docs[:10], 1):
            print(f"  [{i:2d}] {doc['type']} - {doc['title']}")
        
        return sorted_docs

    def get_doc_type(self, href):
        if '/doc/' in href:
            return '文档'
        elif '/sheet/' in href:
            return '表格'
        elif '/slide/' in href:
            return '演示'
        elif '/form/' in href:
            return '表单'
        return '文件'

    async def handle_export_dialog(self):
        """处理导出确认弹窗"""
        export_confirm_selectors = [
            'text=确定',
            'text=导出',
            'text=Export',
            'text=OK',
            'button:has-text("确定")',
            'button:has-text("导出")',
            '[class*="confirm"]',
            '[class*="export"]'
        ]
        
        for selector in export_confirm_selectors:
            try:
                btn = await self.page.wait_for_selector(selector, timeout=2000)
                if btn and await btn.is_visible():
                    await btn.click()
                    print("[EXPORT] 自动确认导出弹窗")
                    await asyncio.sleep(2)
                    return True
            except:
                continue
        
        return False

    async def download_documents_in_sequence(self, documents, max_count=10):
        """按次序安全下载文档，处理导出弹窗"""
        print(f"\n[DOWNLOAD] 开始按次序下载前 {min(max_count, len(documents))} 个文档...")
        
        success_count = 0
        
        for i, doc in enumerate(documents[:max_count]):
            try:
                if doc['href'] in self.processed_docs:
                    print(f"[SKIP {i+1}] 已处理: {doc['title'][:30]}")
                    continue
                
                print(f"\n[DOC {i+1}/{min(max_count, len(documents))}] 下载: {doc['type']} - {doc['title'][:40]}")
                
                # 重新定位元素
                fresh_element = await self.page.query_selector(f'a[href="{doc["href"]}"]')
                if not fresh_element:
                    print(f"[ERROR {i+1}] 无法重新定位元素")
                    continue
                
                self.processed_docs.add(doc['href'])
                
                # 滚动到元素可见
                await fresh_element.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                
                # 执行右键点击
                bounding_box = await fresh_element.bounding_box()
                if bounding_box:
                    center_x = bounding_box['x'] + bounding_box['width'] / 2
                    center_y = bounding_box['y'] + bounding_box['height'] / 2
                    
                    print(f"[ACTION {i+1}] 右键点击位置: ({center_x:.0f}, {center_y:.0f})")
                    await self.page.mouse.click(center_x, center_y, button='right')
                    await asyncio.sleep(2)
                    
                    # 查找下载选项
                    download_options = [
                        'text=下载',
                        'text=导出',
                        'text=Download',
                        'text=Export'
                    ]
                    
                    downloaded = False
                    for option in download_options:
                        try:
                            btn = await self.page.wait_for_selector(option, timeout=3000)
                            if btn and await btn.is_visible():
                                await btn.click()
                                print(f"[CLICK {i+1}] 点击了: {option}")
                                
                                # 等待可能的导出弹窗并处理
                                await asyncio.sleep(2)
                                await self.handle_export_dialog()
                                
                                downloaded = True
                                success_count += 1
                                break
                        except Exception as e:
                            continue
                    
                    if not downloaded:
                        print(f"[MISS {i+1}] 未找到下载选项")
                
                # 使用ESC键关闭任何菜单
                await self.page.keyboard.press('Escape')
                await asyncio.sleep(1)
                
                # 每下载一个文档后等待一下，避免操作过快
                print(f"[WAIT {i+1}] 等待下载处理...")
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"[ERROR {i+1}] 处理失败: {e}")
        
        return success_count

    async def close_extra_tabs(self):
        """关闭多余的标签页，只保留主页面"""
        try:
            pages = self.page.context.pages
            print(f"[CLEANUP] 当前有 {len(pages)} 个标签页")
            
            # 关闭除第一个页面外的所有页面
            for i, page in enumerate(pages[1:], 1):
                try:
                    await page.close()
                    print(f"[CLEANUP] 关闭第 {i+1} 个标签页")
                except:
                    continue
                    
        except Exception as e:
            print(f"[CLEANUP] 清理标签页失败: {e}")

    async def run_optimized_download(self):
        """运行优化的下载流程"""
        print("\n" + "="*60)
        print("        优化版安全下载器")
        print("      解决下滑刷新、导出弹窗、按次序下载")
        print("="*60)
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
                accept_downloads=True
            )
            
            context.on('download', self.handle_download)
            self.page = await context.new_page()
            
            try:
                # 1. 设置Cookie访问页面
                await context.add_cookies(self.parse_cookies())
                await self.page.goto('https://docs.qq.com/desktop/', 
                                    wait_until='domcontentloaded', timeout=30000)
                
                print("[SUCCESS] 页面加载完成")
                await asyncio.sleep(5)
                
                # 2. 设置弹窗处理器
                await self.setup_dialog_handlers()
                
                # 3. 下滑刷新列表，加载更多文档
                documents = await self.scroll_and_load_more_documents()
                
                if not documents:
                    print("[ERROR] 未找到任何文档")
                    return False
                
                # 4. 按次序下载文档
                success_count = await self.download_documents_in_sequence(documents, 10)
                
                # 5. 等待所有下载完成
                print("\n[WAIT] 等待所有下载完成...")
                await asyncio.sleep(15)
                
                # 6. 清理多余标签页
                await self.close_extra_tabs()
                
                # 7. 最终统计
                final_files = list(self.download_dir.glob('*'))
                
                print(f"\n" + "="*50)
                print("              最终结果")
                print("="*50)
                print(f"触发下载次数: {success_count}")
                print(f"实际下载文件: {len(final_files)}")
                print(f"下载目录: {self.download_dir}")
                
                if final_files:
                    print(f"\n下载的文件:")
                    for i, file_path in enumerate(final_files, 1):
                        size = file_path.stat().st_size
                        print(f"  {i}. {file_path.name} ({size:,} 字节)")
                
                return success_count > 0
                
            except Exception as e:
                print(f"[ERROR] 执行失败: {e}")
                return False
                
            finally:
                print(f"\n[WAIT] 保持浏览器20秒供检查...")
                await asyncio.sleep(20)
                await browser.close()

async def main():
    downloader = OptimizedDownloader()
    success = await downloader.run_optimized_download()
    
    if success:
        print("\n[SUCCESS] 优化版下载完成！")
    else:
        print("\n[FAILED] 优化版下载失败")

if __name__ == "__main__":
    asyncio.run(main())