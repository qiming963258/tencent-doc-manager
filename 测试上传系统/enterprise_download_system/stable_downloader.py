#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保守稳定版下载器 - 避免崩溃，采用最稳定的策略
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import traceback

class StableDownloader:
    def __init__(self):
        self.download_dir = Path("./downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        
        # 使用验证有效的Cookie
        self.cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZwaEVRbVE0eVFlTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1UQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; dark_mode_setting=system"
        
        self.downloaded_files = []
        self.processed_docs = set()
        
        print("[SETUP] 保守稳定版下载器")
        print("[SETUP] 采用最稳定策略，避免崩溃")

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

    async def conservative_document_scan(self):
        """保守的文档扫描 - 只获取当前可见的文档，不滚动"""
        print("\n[SCAN] 保守文档扫描（仅当前可见）...")
        
        try:
            # 等待页面稳定
            await asyncio.sleep(3)
            
            doc_selectors = [
                'a[href*="/doc/"]',
                'a[href*="/sheet/"]',
                'a[href*="/slide/"]',
                'a[href*="/form/"]'
            ]
            
            all_docs = []
            
            for selector in doc_selectors:
                try:
                    print(f"[SCAN] 搜索: {selector}")
                    elements = await self.page.query_selector_all(selector)
                    print(f"[SCAN] 找到 {len(elements)} 个")
                    
                    # 只处理前10个元素，避免过多操作
                    for i, element in enumerate(elements[:10]):
                        try:
                            # 安全获取信息
                            element_info = await element.evaluate('''(el) => {
                                try {
                                    return {
                                        href: el.href || el.getAttribute('href') || '',
                                        title: (el.textContent || el.innerText || '').slice(0, 50),
                                        visible: el.offsetParent !== null
                                    };
                                } catch(e) {
                                    return null;
                                }
                            }''')
                            
                            if element_info and element_info['href'] and element_info['visible']:
                                all_docs.append({
                                    'href': element_info['href'],
                                    'title': element_info['title'].strip() or f'文档_{len(all_docs)+1}',
                                    'type': self.get_doc_type(element_info['href']),
                                    'element_index': i
                                })
                                
                        except Exception as e:
                            print(f"[DEBUG] 元素 {i} 处理异常: {str(e)[:50]}")
                            continue
                            
                except Exception as e:
                    print(f"[DEBUG] 选择器 {selector} 异常: {str(e)[:50]}")
                    continue
            
            print(f"\n[SCAN] 扫描完成，找到 {len(all_docs)} 个可见文档:")
            for i, doc in enumerate(all_docs, 1):
                print(f"  [{i:2d}] {doc['type']} - {doc['title']}")
            
            return all_docs
            
        except Exception as e:
            print(f"[ERROR] 文档扫描失败: {e}")
            return []

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

    async def safe_download_single_document(self, doc, doc_index):
        """安全下载单个文档"""
        try:
            print(f"\n[DOC {doc_index}] 开始处理: {doc['type']} - {doc['title'][:30]}")
            
            if doc['href'] in self.processed_docs:
                print(f"[SKIP {doc_index}] 已处理过")
                return False
            
            # 重新定位元素，使用更安全的方式
            fresh_element = None
            try:
                fresh_element = await self.page.query_selector(f'a[href="{doc["href"]}"]')
                if not fresh_element:
                    print(f"[ERROR {doc_index}] 无法定位元素")
                    return False
            except Exception as e:
                print(f"[ERROR {doc_index}] 元素定位失败: {e}")
                return False
            
            self.processed_docs.add(doc['href'])
            
            try:
                # 滚动到可见区域
                await fresh_element.scroll_into_view_if_needed()
                await asyncio.sleep(2)
                
                # 获取边界框
                bounding_box = await fresh_element.bounding_box()
                if not bounding_box:
                    print(f"[ERROR {doc_index}] 无法获取边界框")
                    return False
                
                # 计算点击位置
                center_x = bounding_box['x'] + bounding_box['width'] / 2
                center_y = bounding_box['y'] + bounding_box['height'] / 2
                
                print(f"[ACTION {doc_index}] 右键点击位置: ({center_x:.0f}, {center_y:.0f})")
                
                # 右键点击
                await self.page.mouse.click(center_x, center_y, button='right')
                await asyncio.sleep(3)
                
                # 查找下载选项
                download_options = [
                    'text=下载',
                    'text=导出', 
                    'text=Download',
                    'text=Export'
                ]
                
                download_success = False
                for option in download_options:
                    try:
                        print(f"[SEARCH {doc_index}] 查找: {option}")
                        btn = await self.page.wait_for_selector(option, timeout=3000)
                        if btn and await btn.is_visible():
                            await btn.click()
                            print(f"[CLICK {doc_index}] 点击: {option}")
                            
                            # 等待可能的确认弹窗
                            await asyncio.sleep(2)
                            
                            # 处理可能的确认弹窗
                            confirm_options = [
                                'text=确定',
                                'text=导出',
                                'text=OK',
                                'button:has-text("确定")',
                                'button:has-text("导出")'
                            ]
                            
                            for confirm_option in confirm_options:
                                try:
                                    confirm_btn = await self.page.wait_for_selector(confirm_option, timeout=2000)
                                    if confirm_btn and await confirm_btn.is_visible():
                                        await confirm_btn.click()
                                        print(f"[CONFIRM {doc_index}] 确认弹窗")
                                        break
                                except:
                                    continue
                            
                            download_success = True
                            await asyncio.sleep(2)
                            break
                            
                    except Exception as e:
                        print(f"[DEBUG {doc_index}] {option} 失败: {str(e)[:30]}")
                        continue
                
                if not download_success:
                    print(f"[MISS {doc_index}] 未找到下载选项")
                
                # 安全关闭菜单
                await self.page.keyboard.press('Escape')
                await asyncio.sleep(1)
                
                return download_success
                
            except Exception as e:
                print(f"[ERROR {doc_index}] 下载操作失败: {e}")
                # 确保关闭任何菜单
                try:
                    await self.page.keyboard.press('Escape')
                except:
                    pass
                return False
                
        except Exception as e:
            print(f"[ERROR {doc_index}] 文档处理失败: {e}")
            return False

    async def run_stable_download(self):
        """运行稳定版下载"""
        print("\n" + "="*60)
        print("        保守稳定版下载器")  
        print("      避免崩溃，采用最稳定策略")
        print("="*60)
        
        browser = None
        
        try:
            async with async_playwright() as playwright:
                print("[STEP 1] 启动浏览器...")
                browser = await playwright.chromium.launch(
                    headless=False,
                    args=[
                        '--start-maximized',
                        '--disable-blink-features=AutomationControlled',
                        '--no-first-run'
                    ]
                )
                
                print("[STEP 2] 创建上下文...")
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
                    accept_downloads=True
                )
                
                # 设置下载处理
                context.on('download', self.handle_download)
                
                print("[STEP 3] 创建页面...")
                self.page = await context.new_page()
                
                # 设置基本的弹窗处理
                self.page.on("dialog", lambda dialog: dialog.accept())
                
                print("[STEP 4] 设置Cookie...")
                await context.add_cookies(self.parse_cookies())
                
                print("[STEP 5] 访问页面...")
                await self.page.goto('https://docs.qq.com/desktop/', 
                                    wait_until='domcontentloaded', timeout=30000)
                
                print("[SUCCESS] 页面访问成功")
                await asyncio.sleep(5)
                
                print("[STEP 6] 保守文档扫描...")
                documents = await self.conservative_document_scan()
                
                if not documents:
                    print("[ERROR] 未找到文档")
                    return False
                
                print(f"[STEP 7] 开始下载 {len(documents)} 个文档...")
                success_count = 0
                
                # 逐个下载，最大处理10个
                for i, doc in enumerate(documents[:10], 1):
                    try:
                        print(f"\n{'='*40}")
                        print(f"处理文档 {i}/{min(10, len(documents))}")
                        print(f"{'='*40}")
                        
                        if await self.safe_download_single_document(doc, i):
                            success_count += 1
                            print(f"[SUCCESS {i}] 下载成功")
                        else:
                            print(f"[FAIL {i}] 下载失败")
                        
                        # 每个文档处理后等待，避免操作过快
                        print(f"[WAIT {i}] 等待5秒后继续...")
                        await asyncio.sleep(5)
                        
                    except Exception as e:
                        print(f"[ERROR {i}] 文档处理异常: {e}")
                        continue
                
                print(f"\n[STEP 8] 等待下载完成...")
                await asyncio.sleep(10)
                
                # 最终统计
                final_files = list(self.download_dir.glob('*'))
                
                print(f"\n" + "="*50)
                print("              最终结果")
                print("="*50)
                print(f"触发下载次数: {success_count}")
                print(f"实际文件数量: {len(final_files)}")
                print(f"下载目录: {self.download_dir}")
                
                if final_files:
                    print(f"\n下载的文件:")
                    for i, file_path in enumerate(final_files, 1):
                        size = file_path.stat().st_size
                        print(f"  {i}. {file_path.name} ({size:,} 字节)")
                
                print(f"\n[WAIT] 保持浏览器30秒供检查...")
                await asyncio.sleep(30)
                
                return success_count > 0
                
        except Exception as e:
            print(f"\n[CRITICAL ERROR] 程序执行失败:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误消息: {str(e)}")
            print(f"详细堆栈:")
            print(traceback.format_exc())
            return False
            
        finally:
            try:
                if browser:
                    print("[CLEANUP] 关闭浏览器...")
                    await browser.close()
            except Exception as e:
                print(f"[CLEANUP ERROR] {e}")

async def main():
    try:
        downloader = StableDownloader()
        success = await downloader.run_stable_download()
        
        if success:
            print("\n[SUCCESS] 稳定版下载完成！")
        else:
            print("\n[FAILED] 稳定版下载失败")
            
    except Exception as e:
        print(f"\n[MAIN ERROR] 主程序异常: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断程序")
    except Exception as e:
        print(f"\n[FATAL ERROR] 程序崩溃: {e}")
        print(traceback.format_exc())