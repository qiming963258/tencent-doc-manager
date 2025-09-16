#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试版下载器 - 解决筛选和重复下载问题
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

class DebugDownloader:
    def __init__(self):
        self.download_dir = Path("./downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        
        self.cookie_string = "fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; traceid=a473487816; TOK=a473487816963a48; hashkey=a4734878; dark_mode_setting=system; optimal_cdn_domain=docs.qq.com; ES2=f88c0411768984b9; _qpsvr_localtk=0.5895351222297797; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1ppSTZJbEZLVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1RZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; language=zh-CN; backup_cdn_domain=docs.gtimg.com"
        
        self.downloaded_files = []
        
        print("[DEBUG] 调试版下载器启动")
        print("[DEBUG] 将详细分析页面结构和下载流程")

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
            print(f"[DOWNLOAD] 检测到下载: {filename}")
            await download.save_as(download_path)
            self.downloaded_files.append(str(download_path))
            print(f"[SUCCESS] 下载完成: {filename}")
        except Exception as e:
            print(f"[ERROR] 下载失败: {e}")

    async def debug_page_structure(self):
        """详细分析页面结构"""
        print("\n[DEBUG] 分析页面结构...")
        
        try:
            # 等待页面加载
            await asyncio.sleep(8)
            
            # 1. 分析筛选相关元素
            print("\n[DEBUG] === 筛选元素分析 ===")
            
            # 查找所有可能的筛选相关元素
            filter_elements = await self.page.query_selector_all('*')
            filter_keywords = ['筛选', '过滤', 'filter', '我的', 'my', '时间', 'time', '近期', 'recent']
            
            found_filters = []
            for element in filter_elements[:50]:  # 只检查前50个元素
                try:
                    text = await element.inner_text()
                    tag_name = await element.evaluate('el => el.tagName')
                    class_name = await element.get_attribute('class') or ''
                    
                    if any(keyword in text.lower() or keyword in class_name.lower() for keyword in filter_keywords):
                        if len(text.strip()) > 0 and len(text) < 100:
                            found_filters.append({
                                'tag': tag_name,
                                'class': class_name,
                                'text': text.strip(),
                                'element': element
                            })
                except:
                    continue
            
            print(f"[DEBUG] 找到 {len(found_filters)} 个可能的筛选元素:")
            for i, filter_info in enumerate(found_filters[:10]):  # 只显示前10个
                print(f"  [{i+1}] {filter_info['tag']} - {filter_info['class'][:30]} - {filter_info['text'][:30]}")
            
            # 2. 分析文档元素
            print(f"\n[DEBUG] === 文档元素分析 ===")
            
            # 查找所有文档链接
            doc_links = await self.page.query_selector_all('a[href*="/doc/"], a[href*="/sheet/"], a[href*="/slide/"]')
            print(f"[DEBUG] 找到 {len(doc_links)} 个文档链接")
            
            unique_docs = {}
            for i, link in enumerate(doc_links):
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    bounding_box = await link.bounding_box()
                    
                    if href and text and href not in unique_docs:
                        unique_docs[href] = {
                            'index': len(unique_docs) + 1,
                            'href': href,
                            'text': text.strip(),
                            'position': bounding_box,
                            'element': link
                        }
                        
                        y_pos = bounding_box['y'] if bounding_box else 0
                        print(f"  [DOC {unique_docs[href]['index']}] Y={y_pos:.0f} - {text[:40]}...")
                        
                except Exception as e:
                    print(f"  [SKIP] 链接{i}解析失败: {e}")
            
            # 按Y坐标排序
            sorted_docs = sorted(unique_docs.values(), key=lambda x: x['position']['y'] if x['position'] else 0)
            
            print(f"\n[DEBUG] 排序后的文档列表:")
            for doc in sorted_docs:
                y_pos = doc['position']['y'] if doc['position'] else 0
                print(f"  [排序 {doc['index']}] Y={y_pos:.0f} - {doc['text'][:40]}...")
            
            return found_filters, sorted_docs
            
        except Exception as e:
            print(f"[DEBUG] 页面结构分析失败: {e}")
            return [], []

    async def try_click_filters_manually(self, filter_elements):
        """手动尝试点击筛选元素"""
        print(f"\n[DEBUG] 手动尝试点击筛选元素...")
        
        for i, filter_info in enumerate(filter_elements[:5]):  # 只尝试前5个
            try:
                element = filter_info['element']
                text = filter_info['text']
                
                print(f"\n[DEBUG] 尝试点击筛选元素 {i+1}: {text[:30]}")
                
                # 滚动到元素
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                
                # 高亮元素
                await self.page.evaluate('''(element) => {
                    element.style.border = '3px solid red';
                    element.style.backgroundColor = 'yellow';
                }''', element)
                
                print(f"[DEBUG] 元素已高亮，暂停5秒供观察...")
                await asyncio.sleep(5)
                
                # 尝试点击
                await element.click()
                print(f"[DEBUG] 已点击，等待反应...")
                await asyncio.sleep(3)
                
                # 移除高亮
                await self.page.evaluate('''(element) => {
                    element.style.border = '';
                    element.style.backgroundColor = '';
                }''', element)
                
            except Exception as e:
                print(f"[DEBUG] 点击筛选元素 {i+1} 失败: {e}")

    async def download_different_documents(self, sorted_docs, max_count=3):
        """确保下载不同的文档"""
        print(f"\n[DEBUG] 开始下载不同的文档 (最多{max_count}个)...")
        
        download_count = 0
        
        for i, doc_info in enumerate(sorted_docs[:max_count]):
            try:
                doc_index = doc_info['index']
                doc_text = doc_info['text']
                doc_href = doc_info['href']
                element = doc_info['element']
                
                print(f"\n[DOC {doc_index}] 准备下载第 {i+1} 个不同文档")
                print(f"[TITLE] {doc_text}")
                print(f"[URL] {doc_href}")
                
                # 重新查找元素避免stale问题
                fresh_element = await self.page.query_selector(f'a[href="{doc_href}"]')
                if not fresh_element:
                    print(f"[ERROR] 无法重新定位元素")
                    continue
                
                # 滚动到元素
                await fresh_element.scroll_into_view_if_needed()
                await asyncio.sleep(2)
                
                # 高亮当前要下载的元素
                await self.page.evaluate('''(element) => {
                    element.style.border = '5px solid blue';
                    element.style.backgroundColor = 'lightblue';
                }''', fresh_element)
                
                print(f"[DEBUG] 当前要下载的文档已高亮蓝色，暂停3秒...")
                await asyncio.sleep(3)
                
                # 右键点击
                await fresh_element.click(button='right')
                await asyncio.sleep(2)
                
                # 查找下载选项
                download_options = ['text=下载', 'text=导出', 'text=Download']
                download_success = False
                
                for option in download_options:
                    try:
                        download_btn = await self.page.wait_for_selector(option, timeout=3000)
                        if download_btn:
                            await download_btn.click()
                            print(f"[SUCCESS] 点击了: {option}")
                            download_success = True
                            download_count += 1
                            break
                    except:
                        continue
                
                if download_success:
                    print(f"[SUCCESS] 文档 {doc_index} 下载请求已发送")
                else:
                    print(f"[MISS] 文档 {doc_index} 未找到下载选项")
                
                # 移除高亮
                await self.page.evaluate('''(element) => {
                    element.style.border = '';
                    element.style.backgroundColor = '';
                }''', fresh_element)
                
                # 点击空白处
                await self.page.click('body', position={'x': 100, 'y': 100})
                await asyncio.sleep(2)
                
                print(f"[PROGRESS] 已处理 {i+1}/{max_count} 个文档")
                
            except Exception as e:
                print(f"[ERROR] 处理文档 {doc_info['index']} 失败: {e}")
        
        return download_count

    async def run_debug_task(self):
        """执行调试任务"""
        print("\n" + "="*60)
        print("            调试版腾讯文档下载器")
        print("        专门解决筛选和重复下载问题")
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
                # 1. 设置Cookie并访问页面
                await context.add_cookies(self.parse_cookies())
                await self.page.goto('https://docs.qq.com/desktop/', 
                                    wait_until='domcontentloaded', timeout=30000)
                
                print("[SUCCESS] 页面加载完成")
                
                # 2. 分析页面结构
                filter_elements, sorted_docs = await self.debug_page_structure()
                
                # 3. 尝试手动点击筛选
                if filter_elements:
                    await self.try_click_filters_manually(filter_elements)
                
                # 4. 重新分析文档（筛选后）
                print(f"\n[DEBUG] 重新分析筛选后的文档...")
                await asyncio.sleep(5)
                _, updated_docs = await self.debug_page_structure()
                
                # 5. 下载不同的文档
                if updated_docs or sorted_docs:
                    docs_to_download = updated_docs if updated_docs else sorted_docs
                    download_count = await self.download_different_documents(docs_to_download, 3)
                    
                    print(f"\n[SUMMARY] 下载尝试完成")
                    print(f"[STATS] 触发下载: {download_count} 次")
                    print(f"[STATS] 实际文件: {len(self.downloaded_files)} 个")
                
                # 6. 等待下载完成
                await asyncio.sleep(10)
                
                return True
                
            except Exception as e:
                print(f"[ERROR] 调试任务失败: {e}")
                return False
                
            finally:
                print(f"\n[DEBUG] 保持浏览器20秒供最终检查...")
                await asyncio.sleep(20)
                await browser.close()

async def main():
    downloader = DebugDownloader()
    success = await downloader.run_debug_task()
    
    if success:
        print("\n[DEBUG] 调试任务完成，请查看输出分析问题")
    else:
        print("\n[DEBUG] 调试任务失败")

if __name__ == "__main__":
    asyncio.run(main())