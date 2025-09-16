#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确筛选版下载器 - 使用用户提供的准确元素选择器
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

class PreciseFilterDownloader:
    def __init__(self):
        self.download_dir = Path("./downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        
        self.cookie_string = "fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; traceid=a473487816; TOK=a473487816963a48; hashkey=a4734878; dark_mode_setting=system; optimal_cdn_domain=docs.qq.com; ES2=f88c0411768984b9; _qpsvr_localtk=0.5895351222297797; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1ppSTZJbEZKVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1RZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; language=zh-CN; backup_cdn_domain=docs.gtimg.com"
        
        self.downloaded_files = []
        self.processed_docs = set()
        
        print("[SETUP] 精确筛选版下载器")
        print("[SETUP] 使用用户提供的准确元素选择器")

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

    async def click_filter_button(self):
        """点击筛选按钮"""
        print("\n[FILTER] 点击筛选按钮...")
        
        try:
            # 使用成功的筛选按钮选择器
            filter_button = await self.page.wait_for_selector('button:has-text("筛选")', timeout=10000)
            
            if filter_button:
                # 高亮显示
                await self.page.evaluate('''(element) => {
                    element.style.border = '3px solid green';
                    element.style.backgroundColor = 'lightgreen';
                }''', filter_button)
                
                print("[FOUND] 找到筛选按钮，高亮显示...")
                await asyncio.sleep(2)
                
                # 点击筛选按钮
                await filter_button.click()
                print("[CLICK] 成功点击筛选按钮！")
                
                # 等待筛选面板出现
                await asyncio.sleep(5)
                return True
        
        except Exception as e:
            print(f"[ERROR] 筛选按钮点击失败: {e}")
            return False

    async def scroll_filter_panel_to_bottom(self):
        """拖动滑块到最下方"""
        print("\n[SCROLL] 拖动筛选面板滑块到最下方...")
        
        try:
            # 查找滑块轨道
            scrollbar_selectors = [
                '.desktop-scrollbars-track.vertical.rc-scrollbars-track.rc-scrollbars-track-v',
                '.desktop-scrollbars-track.vertical',
                '.rc-scrollbars-track-v',
                '[class*="scrollbars-track"][class*="vertical"]'
            ]
            
            scrollbar_track = None
            for selector in scrollbar_selectors:
                try:
                    track = await self.page.wait_for_selector(selector, timeout=3000)
                    if track:
                        scrollbar_track = track
                        print(f"[FOUND] 找到滑块轨道: {selector}")
                        break
                except:
                    continue
            
            if scrollbar_track:
                # 获取滑块轨道的边界
                track_box = await scrollbar_track.bounding_box()
                
                if track_box:
                    # 点击轨道底部来滚动到底部
                    bottom_y = track_box['y'] + track_box['height'] - 10
                    center_x = track_box['x'] + track_box['width'] / 2
                    
                    print(f"[SCROLL] 点击滑块轨道底部: ({center_x}, {bottom_y})")
                    await self.page.click(f'css=.desktop-scrollbars-track.vertical', position={'x': center_x - track_box['x'], 'y': bottom_y - track_box['y']})
                    await asyncio.sleep(2)
                    
                    # 多次滚动确保到底部
                    for i in range(3):
                        await self.page.keyboard.press('End')
                        await asyncio.sleep(1)
                    
                    print("[SUCCESS] 滑块已拖动到最下方")
                    
            else:
                print("[INFO] 未找到滑块轨道，尝试键盘滚动")
                # 尝试键盘滚动
                await self.page.keyboard.press('End')
                await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 滑块拖动失败: {e}")
            return True  # 继续执行

    async def select_recent_month_radio(self):
        """选择"近一个月"radio按钮"""
        print("\n[RADIO] 选择'近一个月'radio按钮...")
        
        try:
            # 使用用户提供的精确选择器
            precise_selectors = [
                # 用户提供的精确CSS选择器
                '#root > div.desktop-layout-pc.desktop-dropdown-container.desktop-skin-default > div:nth-child(4) > div > div > div > div > div.desktop-scrollbars-view.rc-scrollbars-view.auto-height > div > div:nth-child(9) > div:nth-child(3) > input',
                # 用户提供的XPath转换为CSS
                'div:nth-child(9) > div:nth-child(3) > input[type="radio"]',
                # 通用radio选择器
                'input[type="radio"].dui-radio-input.dui-radio-input-full',
                'input.dui-radio-input-full[type="radio"]',
                # 基于类名的选择器
                '.dui-radio-input.dui-radio-input-full'
            ]
            
            radio_found = False
            
            for selector in precise_selectors:
                try:
                    print(f"[RADIO] 尝试选择器: {selector}")
                    
                    # 等待radio按钮出现
                    radio_element = await self.page.wait_for_selector(selector, timeout=5000)
                    
                    if radio_element:
                        # 检查当前状态
                        is_checked = await radio_element.is_checked()
                        print(f"[RADIO] 找到radio按钮，当前状态: {'选中' if is_checked else '未选中'}")
                        
                        # 高亮显示
                        await self.page.evaluate('''(element) => {
                            element.style.outline = '3px solid red';
                            element.style.outlineOffset = '2px';
                        }''', radio_element)
                        
                        print("[RADIO] radio按钮已高亮显示...")
                        await asyncio.sleep(3)
                        
                        if not is_checked:
                            # 点击选择
                            await radio_element.click()
                            print("[CLICK] 成功点击radio按钮！")
                            
                            # 验证选择结果
                            await asyncio.sleep(1)
                            new_state = await radio_element.is_checked()
                            print(f"[VERIFY] 点击后状态: {'选中' if new_state else '未选中'}")
                            
                            if new_state:
                                radio_found = True
                                break
                        else:
                            print("[INFO] radio按钮已经选中")
                            radio_found = True
                            break
                            
                except Exception as e:
                    print(f"[SKIP] {selector} 失败: {e}")
                    continue
            
            if radio_found:
                print("[SUCCESS] '近一个月'radio按钮选择成功！")
            else:
                print("[WARNING] 未能找到或选择'近一个月'radio按钮")
                
                # 显示当前页面的所有radio按钮供调试
                try:
                    all_radios = await self.page.query_selector_all('input[type="radio"]')
                    print(f"[DEBUG] 页面上共有 {len(all_radios)} 个radio按钮")
                    
                    for i, radio in enumerate(all_radios[:5]):  # 只显示前5个
                        try:
                            classes = await radio.get_attribute('class') or ''
                            checked = await radio.is_checked()
                            print(f"  [RADIO {i+1}] class='{classes}' checked={checked}")
                        except:
                            continue
                except:
                    pass
            
            return radio_found
            
        except Exception as e:
            print(f"[ERROR] radio按钮选择失败: {e}")
            return False

    async def apply_filter_settings(self):
        """应用筛选设置"""
        print("\n[APPLY] 应用筛选设置...")
        
        try:
            # 查找应用/确定按钮
            apply_selectors = [
                'text=应用',
                'text=确定',
                'text=Apply',
                'text=OK',
                'button:has-text("应用")',
                'button:has-text("确定")',
                '.apply-button',
                '.confirm-button',
                '[data-action="apply"]'
            ]
            
            apply_clicked = False
            
            for selector in apply_selectors:
                try:
                    print(f"[APPLY] 查找应用按钮: {selector}")
                    apply_button = await self.page.wait_for_selector(selector, timeout=3000)
                    
                    if apply_button:
                        await apply_button.click()
                        print(f"[SUCCESS] 点击了: {selector}")
                        apply_clicked = True
                        break
                        
                except:
                    continue
            
            if apply_clicked:
                print("[SUCCESS] 筛选设置已应用！")
                # 等待筛选结果加载
                await asyncio.sleep(8)
            else:
                print("[WARNING] 未找到应用按钮，筛选可能自动应用")
                await asyncio.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 应用筛选设置失败: {e}")
            return True

    async def find_filtered_documents(self):
        """查找筛选后的文档"""
        print("\n[SEARCH] 查找筛选后的文档...")
        
        await asyncio.sleep(5)
        
        # 文档选择器
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
                print(f"[SEARCH] {selector}: 找到 {len(elements)} 个")
                
                for element in elements:
                    try:
                        href = await element.get_attribute('href')
                        text = await element.inner_text()
                        bbox = await element.bounding_box()
                        
                        if href and text and href not in all_docs:
                            all_docs[href] = {
                                'element': element,
                                'href': href,
                                'title': text.strip(),
                                'position': bbox,
                                'type': self.get_doc_type(href)
                            }
                    except:
                        continue
            except:
                continue
        
        # 按位置排序
        sorted_docs = sorted(all_docs.values(), 
                           key=lambda x: x['position']['y'] if x['position'] else 0)
        
        print(f"\n[FOUND] 筛选后找到 {len(sorted_docs)} 个文档:")
        for i, doc in enumerate(sorted_docs, 1):
            print(f"  [{i}] {doc['type']} - {doc['title'][:40]}...")
        
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

    async def download_docs_in_sequence(self, documents, max_count=10):
        """按顺序下载文档"""
        print(f"\n[DOWNLOAD] 开始按顺序下载前 {min(max_count, len(documents))} 个文档...")
        
        success_count = 0
        
        for i, doc in enumerate(documents[:max_count]):
            try:
                if doc['href'] in self.processed_docs:
                    print(f"[SKIP {i+1}] 已处理: {doc['title'][:30]}")
                    continue
                
                print(f"\n[DOC {i+1}] 下载: {doc['type']} - {doc['title'][:40]}")
                
                # 重新定位元素
                fresh_element = await self.page.query_selector(f'a[href="{doc["href"]}"]')
                if not fresh_element:
                    print(f"[ERROR {i+1}] 无法重新定位元素")
                    continue
                
                self.processed_docs.add(doc['href'])
                
                # 滚动并高亮
                await fresh_element.scroll_into_view_if_needed()
                await self.page.evaluate('''(element) => {
                    element.style.border = '3px solid blue';
                    element.style.backgroundColor = 'lightblue';
                }''', fresh_element)
                
                await asyncio.sleep(2)
                
                # 右键下载
                await fresh_element.click(button='right')
                await asyncio.sleep(2)
                
                # 查找下载选项
                download_options = ['text=下载', 'text=导出', 'text=Download']
                downloaded = False
                
                for option in download_options:
                    try:
                        btn = await self.page.wait_for_selector(option, timeout=3000)
                        if btn:
                            await btn.click()
                            print(f"[SUCCESS {i+1}] 点击了: {option}")
                            downloaded = True
                            success_count += 1
                            break
                    except:
                        continue
                
                if not downloaded:
                    print(f"[MISS {i+1}] 未找到下载选项")
                
                # 清除高亮
                await self.page.evaluate('''(element) => {
                    element.style.border = '';
                    element.style.backgroundColor = '';
                }''', fresh_element)
                
                # 点击空白处
                await self.page.click('body', position={'x': 50, 'y': 50})
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[ERROR {i+1}] 处理失败: {e}")
        
        return success_count

    async def run_precise_filter_download(self):
        """执行精确筛选下载"""
        print("\n" + "="*60)
        print("        精确筛选版腾讯文档下载器")
        print("      使用用户提供的准确元素选择器")
        print("="*60)
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
                
                # 3. 拖动滑块到最下方
                await self.scroll_filter_panel_to_bottom()
                
                # 4. 选择"近一个月"radio按钮
                radio_success = await self.select_recent_month_radio()
                
                # 5. 应用筛选设置
                await self.apply_filter_settings()
                
                # 6. 查找筛选后的文档
                documents = await self.find_filtered_documents()
                
                if not documents:
                    print("[ERROR] 未找到任何文档")
                    return False
                
                # 7. 按顺序下载
                success_count = await self.download_docs_in_sequence(documents, 10)
                
                # 8. 等待下载完成
                await asyncio.sleep(15)
                
                # 9. 最终统计
                final_files = list(self.download_dir.glob('*'))
                
                print(f"\n" + "="*50)
                print("              最终结果")
                print("="*50)
                print(f"radio按钮选择: {'成功' if radio_success else '失败'}")
                print(f"触发下载次数: {success_count}")
                print(f"实际下载文件: {len(final_files)}")
                print(f"下载目录: {self.download_dir}")
                
                if final_files:
                    print(f"\n下载的文件:")
                    for i, file_path in enumerate(final_files, 1):
                        size = file_path.stat().st_size
                        print(f"  {i}. {file_path.name} ({size:,} 字节)")
                
                return True
                
            except Exception as e:
                print(f"[ERROR] 执行失败: {e}")
                return False
                
            finally:
                print(f"\n[WAIT] 保持浏览器25秒供检查...")
                await asyncio.sleep(25)
                await browser.close()

async def main():
    downloader = PreciseFilterDownloader()
    success = await downloader.run_precise_filter_download()
    
    if success:
        print("\n[SUCCESS] 精确筛选版下载完成！")
    else:
        print("\n[FAILED] 精确筛选版下载失败")

if __name__ == "__main__":
    asyncio.run(main())