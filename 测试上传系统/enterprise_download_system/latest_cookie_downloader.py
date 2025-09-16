#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最新Cookie完全安全下载器 - 使用用户提供的最新Cookie
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

class LatestCookieDownloader:
    def __init__(self):
        self.download_dir = Path("./downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        
        # 使用用户提供的最新有效Cookie
        self.cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZwaEVRbVE0eVFlTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1UQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; dark_mode_setting=system"
        
        self.downloaded_files = []
        self.processed_docs = set()
        
        print("[SETUP] 最新Cookie完全安全下载器")
        print("[SETUP] 使用用户提供的最新有效Cookie")

    def parse_cookies(self):
        """解析Cookie - 使用成功经验方法"""
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
        """处理下载事件"""
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

    async def click_filter_button(self):
        """点击筛选按钮 - 使用验证成功的多选择器方法"""
        print("\n[FILTER] 点击筛选按钮...")
        
        # 关键：设置dialog监听器防止弹窗卡顿
        self.page.on("dialog", lambda dialog: dialog.accept())
        print("[SETUP] 已设置dialog监听器")
        
        try:
            # 使用验证成功的多个备选筛选按钮选择器
            filter_button_selectors = [
                '.desktop-filter-button-inner',
                'button:has-text("筛选")',
                '.desktop-icon-button-pc.desktop-filter-button-inner',
                'button.desktop-filter-button-inner'
            ]
            
            filter_clicked = False
            
            for selector in filter_button_selectors:
                try:
                    print(f"[FILTER] 尝试选择器: {selector}")
                    
                    filter_button = await self.page.wait_for_selector(selector, timeout=5000)
                    
                    if filter_button:
                        print(f"[FOUND] 找到筛选按钮: {selector}")
                        await filter_button.click()
                        print("[SUCCESS] 筛选按钮点击成功！")
                        filter_clicked = True
                        await asyncio.sleep(3)
                        break
                        
                except Exception as e:
                    print(f"[SKIP] {selector} 失败: {str(e)[:50]}")
                    continue
            
            if not filter_clicked:
                print("[ERROR] 所有筛选按钮选择器都失败")
                return False
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 筛选按钮点击失败: {e}")
            return False

    async def set_filter_options(self):
        """设置筛选选项 - 使用成功经验文档中的精确方法"""
        print("\n[FILTER] 使用成功经验文档中的方法设置筛选选项...")
        
        try:
            # 等待筛选面板加载
            print("[WAIT] 等待筛选面板完全加载...")
            await asyncio.sleep(5)
            
            # 1. 选择"所有者"区域的"我所有的"（第2项）
            print("\n[STEP 1] 选择所有者区域的'我所有的'...")
            
            owner_success = False
            try:
                owner_header = await self.page.wait_for_selector('header:has-text("所有者")', timeout=5000)
                if owner_header:
                    print("[FOUND] 找到'所有者'标题")
                    
                    owner_radios = await self.page.query_selector_all('header:has-text("所有者") + div input[type="radio"]')
                    print(f"[DEBUG] 所有者区域找到 {len(owner_radios)} 个radio按钮")
                    
                    if len(owner_radios) >= 2:
                        my_docs_radio = owner_radios[1]  # 索引1 = 第2项
                        
                        is_checked_before = await my_docs_radio.is_checked()
                        print(f"[DEBUG] '我所有的'选项当前状态: {is_checked_before}")
                        
                        if not is_checked_before:
                            await my_docs_radio.check()
                            await asyncio.sleep(2)
                            
                            is_checked_after = await my_docs_radio.is_checked()
                            if is_checked_after:
                                print("[SUCCESS] '我所有的'选项已选中！")
                                owner_success = True
                            else:
                                print("[FAIL] '我所有的'选项选择失败")
                        else:
                            print("[INFO] '我所有的'选项已经选中")
                            owner_success = True
                    else:
                        print("[ERROR] 所有者区域radio按钮数量不足")
                        
            except Exception as e:
                print(f"[ERROR] 所有者区域选择失败: {e}")
            
            # 2. 选择"查看时间"区域的"近1个月"（第3项）
            print("\n[STEP 2] 选择查看时间区域的'近1个月'...")
            
            time_success = False
            try:
                time_header = await self.page.wait_for_selector('header:has-text("查看时间")', timeout=5000)
                if time_header:
                    print("[FOUND] 找到'查看时间'标题")
                    
                    time_radios = await self.page.query_selector_all('header:has-text("查看时间") + div input[type="radio"]')
                    print(f"[DEBUG] 查看时间区域找到 {len(time_radios)} 个radio按钮")
                    
                    if len(time_radios) >= 3:
                        month_radio = time_radios[2]  # 索引2 = 第3项
                        
                        is_checked_before = await month_radio.is_checked()
                        print(f"[DEBUG] '近1个月'选项当前状态: {is_checked_before}")
                        
                        if not is_checked_before:
                            await month_radio.check()
                            await asyncio.sleep(2)
                            
                            is_checked_after = await month_radio.is_checked()
                            if is_checked_after:
                                print("[SUCCESS] '近1个月'选项已选中！")
                                time_success = True
                            else:
                                print("[FAIL] '近1个月'选项选择失败")
                        else:
                            print("[INFO] '近1个月'选项已经选中")
                            time_success = True
                    else:
                        print("[ERROR] 查看时间区域radio按钮数量不足")
                        
            except Exception as e:
                print(f"[ERROR] 查看时间区域选择失败: {e}")
            
            # 3. 查找并点击确定/应用按钮
            apply_options = [
                'text=确定',
                'text=应用',
                'text=Apply',
                'text=OK',
                'button:has-text("确定")'
            ]
            
            apply_clicked = False
            for option in apply_options:
                try:
                    print(f"[FILTER] 查找应用按钮: {option}")
                    element = await self.page.wait_for_selector(option, timeout=3000)
                    if element:
                        await element.click()
                        print(f"[SUCCESS] 点击了: {option}")
                        apply_clicked = True
                        await asyncio.sleep(3)
                        break
                except:
                    continue
            
            # 报告筛选结果
            print(f"\n" + "="*50)
            print("           筛选设置结果")
            print("="*50)
            print(f"所有者选择: {'[成功] 我所有的' if owner_success else '[失败]'}")
            print(f"时间筛选: {'[成功] 近1个月' if time_success else '[失败]'}")
            print(f"应用设置: {'[成功] 已点击' if apply_clicked else '[失败] 未找到'}")
            
            # 等待筛选结果加载
            print(f"\n[WAIT] 等待筛选结果加载...")
            await asyncio.sleep(8)
            
            return owner_success and time_success and apply_clicked
            
        except Exception as e:
            print(f"[ERROR] 设置筛选选项失败: {e}")
            return False

    async def safe_scan_documents(self):
        """100%安全的文档扫描"""
        print("\n[SAFE-SCAN] 开始100%安全的文档扫描...")
        
        await asyncio.sleep(5)
        
        doc_selectors = [
            'a[href*="/doc/"]',
            'a[href*="/sheet/"]', 
            'a[href*="/slide/"]',
            'a[href*="/form/"]'
        ]
        
        all_docs = {}
        
        for selector in doc_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                print(f"[SAFE-SCAN] {selector}: 找到 {len(elements)} 个")
                
                for i, element in enumerate(elements):
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
                        
                        if href and href not in all_docs and title.strip():
                            all_docs[href] = {
                                'href': href,
                                'title': title.strip()[:50],
                                'position': rect,
                                'type': self.get_doc_type(href)
                            }
                            
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
        
        sorted_docs = sorted(all_docs.values(), 
                           key=lambda x: x['position']['y'] if x['position'] else 0)
        
        print(f"\n[SAFE-SCAN] 安全扫描完成，找到 {len(sorted_docs)} 个文档:")
        for i, doc in enumerate(sorted_docs[:10], 1):
            print(f"  [{i:2d}] {doc['type']} - {doc['title']}")
        
        return sorted_docs

    def get_doc_type(self, href):
        """判断文档类型"""
        if '/doc/' in href:
            return '文档'
        elif '/sheet/' in href:
            return '表格'
        elif '/slide/' in href:
            return '演示'
        elif '/form/' in href:
            return '表单'
        return '文件'

    async def safe_download_documents(self, documents, max_count=10):
        """安全下载文档"""
        print(f"\n[DOWNLOAD] 开始安全下载前 {min(max_count, len(documents))} 个文档...")
        
        success_count = 0
        
        for i, doc in enumerate(documents[:max_count]):
            try:
                if doc['href'] in self.processed_docs:
                    print(f"[SKIP {i+1}] 已处理: {doc['title'][:30]}")
                    continue
                
                print(f"\n[DOC {i+1}] 下载: {doc['type']} - {doc['title'][:40]}")
                
                fresh_element = await self.page.query_selector(f'a[href="{doc["href"]}"]')
                if not fresh_element:
                    print(f"[ERROR {i+1}] 无法重新定位元素")
                    continue
                
                self.processed_docs.add(doc['href'])
                
                await fresh_element.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                
                print(f"[ACTION {i+1}] 执行精确右键下载...")
                
                bounding_box = await fresh_element.bounding_box()
                if bounding_box:
                    center_x = bounding_box['x'] + bounding_box['width'] / 2
                    center_y = bounding_box['y'] + bounding_box['height'] / 2
                    
                    await self.page.mouse.click(center_x, center_y, button='right')
                    await asyncio.sleep(3)
                    
                    download_options = [
                        'text=下载',
                        'text=导出',
                        'text=Download',
                        'text=Export'
                    ]
                    
                    downloaded = False
                    for option in download_options:
                        try:
                            btn = await self.page.wait_for_selector(option, timeout=2000)
                            if btn and await btn.is_visible():
                                await btn.click()
                                print(f"[SUCCESS {i+1}] 点击了下载选项: {option}")
                                downloaded = True
                                success_count += 1
                                await asyncio.sleep(3)
                                break
                        except Exception as e:
                            continue
                    
                    if not downloaded:
                        print(f"[MISS {i+1}] 未找到可用的下载选项")
                
                # 使用ESC键关闭右键菜单，避免意外点击文档
                await self.page.keyboard.press('Escape')
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"[ERROR {i+1}] 处理失败: {e}")
        
        return success_count

    async def run_latest_cookie_download(self):
        """运行最新Cookie下载流程"""
        print("\n" + "="*60)
        print("        最新Cookie完全安全下载器")
        print("      使用用户提供的最新有效Cookie")
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
                
                # 2. 点击筛选按钮
                if not await self.click_filter_button():
                    print("[ERROR] 筛选按钮点击失败")
                    return False
                
                # 3. 设置筛选选项
                if not await self.set_filter_options():
                    print("[WARNING] 筛选设置失败，使用默认筛选")
                
                # 4. 100%安全的文档扫描
                documents = await self.safe_scan_documents()
                
                if not documents:
                    print("[ERROR] 未找到任何文档")
                    return False
                
                # 5. 安全下载文档
                success_count = await self.safe_download_documents(documents, 10)
                
                # 6. 等待下载完成
                await asyncio.sleep(10)
                
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
    downloader = LatestCookieDownloader()
    success = await downloader.run_latest_cookie_download()
    
    if success:
        print("\n[SUCCESS] 最新Cookie安全下载完成！")
    else:
        print("\n[FAILED] 最新Cookie下载失败")

if __name__ == "__main__":
    asyncio.run(main())