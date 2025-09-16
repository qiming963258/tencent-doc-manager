#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版下载器 - 添加筛选功能和精确下载监测
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import time

class ImprovedDownloader:
    def __init__(self):
        self.download_dir = Path("./downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        
        # 使用最新有效Cookie
        self.cookie_string = "fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; traceid=a473487816; TOK=a473487816963a48; hashkey=a4734878; dark_mode_setting=system; optimal_cdn_domain=docs.qq.com; ES2=f88c0411768984b9; _qpsvr_localtk=0.5895351222297797; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1ppSTZJbEZLVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1RZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; language=zh-CN; backup_cdn_domain=docs.gtimg.com"
        
        self.downloaded_files = []
        self.download_queue = []  # 下载队列
        self.current_downloads = {}  # 当前下载状态追踪
        
        print("[SETUP] 改进版下载器 - 支持筛选和精确监测")
        print("[SETUP] 下载目录:", str(self.download_dir))

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
        """精确监测每个下载"""
        try:
            filename = download.suggested_filename
            download_path = self.download_dir / filename
            
            # 记录下载开始
            download_id = len(self.downloaded_files) + 1
            start_time = time.time()
            
            print(f"[DOWN {download_id}] 开始下载: {filename}")
            self.current_downloads[download_id] = {
                'filename': filename,
                'start_time': start_time,
                'status': 'downloading'
            }
            
            # 执行下载
            await download.save_as(download_path)
            
            # 验证下载完成
            if download_path.exists():
                file_size = download_path.stat().st_size
                end_time = time.time()
                duration = end_time - start_time
                
                self.downloaded_files.append(str(download_path))
                self.current_downloads[download_id]['status'] = 'completed'
                self.current_downloads[download_id]['size'] = file_size
                self.current_downloads[download_id]['duration'] = duration
                
                print(f"[OK {download_id}] 完成: {filename}")
                print(f"  文件大小: {file_size:,} 字节")
                print(f"  下载耗时: {duration:.1f} 秒")
            else:
                print(f"[ERROR {download_id}] 下载失败: 文件不存在")
                self.current_downloads[download_id]['status'] = 'failed'
                
        except Exception as e:
            print(f"[ERROR] 下载异常: {e}")
            if download_id in self.current_downloads:
                self.current_downloads[download_id]['status'] = 'error'

    async def setup_filters(self):
        """设置筛选条件：我的文档 + 最近一个月"""
        print("\n[FILTER] 设置筛选条件...")
        
        try:
            # 等待页面加载完成
            await asyncio.sleep(5)
            
            # 1. 确保在"我的文档"选项卡
            my_docs_selectors = [
                'text=我的文档',
                'text=My Documents', 
                '[data-test="my-docs"]',
                '.tab-item:has-text("我的")',
                'a[href*="mydocs"]'
            ]
            
            for selector in my_docs_selectors:
                try:
                    print(f"[FILTER] 尝试点击: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.click()
                        print(f"[OK] 已切换到我的文档")
                        await asyncio.sleep(3)
                        break
                except:
                    continue
            
            # 2. 设置时间筛选为"最近一个月"
            time_filter_selectors = [
                'text=最近一个月',
                'text=近一个月',
                'text=Last Month',
                '[data-test="time-filter"]',
                '.time-filter-dropdown'
            ]
            
            for selector in time_filter_selectors:
                try:
                    print(f"[FILTER] 尝试时间筛选: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.click()
                        print(f"[OK] 已设置时间筛选")
                        await asyncio.sleep(3)
                        break
                except:
                    continue
            
            # 3. 检查筛选器下拉菜单
            try:
                print("[FILTER] 查找筛选器下拉菜单...")
                filter_dropdown = await self.page.wait_for_selector('.filter-dropdown, .dui-select, [class*="filter"]', timeout=5000)
                if filter_dropdown:
                    await filter_dropdown.click()
                    await asyncio.sleep(2)
                    
                    # 尝试选择"我所有"和"近一个月"
                    all_mine_option = await self.page.wait_for_selector('text=我所有', timeout=3000)
                    if all_mine_option:
                        await all_mine_option.click()
                        print("[OK] 选择了'我所有'")
                        await asyncio.sleep(1)
                    
                    recent_option = await self.page.wait_for_selector('text=近一个月', timeout=3000)
                    if recent_option:
                        await recent_option.click()
                        print("[OK] 选择了'近一个月'")
                        await asyncio.sleep(2)
            except:
                print("[INFO] 未找到筛选器下拉菜单，可能已是默认设置")
            
            print("[FILTER] 筛选设置完成，等待页面刷新...")
            await asyncio.sleep(5)
            return True
            
        except Exception as e:
            print(f"[WARNING] 筛选设置失败: {e}")
            print("[INFO] 继续使用默认筛选条件")
            return True

    async def find_documents_with_details(self):
        """查找文档并获取详细信息"""
        print("\n[SEARCH] 查找筛选后的文档...")
        
        # 等待筛选后的内容加载
        await asyncio.sleep(5)
        
        # 多种文档选择器
        document_selectors = [
            'a[href*="/doc/"]',
            'a[href*="/sheet/"]', 
            'a[href*="/slide/"]',
            '[class*="file-item"] a',
            '[class*="document-item"] a',
            'tr[class*="file"] a',
            '.file-name a'
        ]
        
        all_documents = []
        
        for selector in document_selectors:
            try:
                print(f"[SEARCH] 使用选择器: {selector}")
                elements = await self.page.query_selector_all(selector)
                
                if elements:
                    print(f"[FOUND] 找到 {len(elements)} 个文档")
                    
                    for i, element in enumerate(elements):
                        try:
                            # 获取文档详细信息
                            doc_text = await element.inner_text()
                            doc_href = await element.get_attribute('href')
                            
                            if doc_text and doc_href and len(doc_text.strip()) > 0:
                                doc_info = {
                                    'element': element,
                                    'title': doc_text.strip(),
                                    'href': doc_href,
                                    'type': self.get_doc_type(doc_href),
                                    'index': len(all_documents) + 1
                                }
                                all_documents.append(doc_info)
                                print(f"  [DOC {doc_info['index']}] {doc_info['type']} - {doc_info['title'][:50]}...")
                                
                        except Exception as e:
                            print(f"  [SKIP] 元素{i}解析失败: {e}")
                    
                    break  # 找到文档就停止尝试其他选择器
                    
            except Exception as e:
                print(f"[SKIP] {selector} 失败: {e}")
        
        if not all_documents:
            print("[WARNING] 未找到任何文档，可能筛选条件过严格")
            return []
        
        print(f"\n[SUMMARY] 共找到 {len(all_documents)} 个符合筛选条件的文档")
        return all_documents

    def get_doc_type(self, href):
        """根据URL判断文档类型"""
        if '/doc/' in href:
            return '文档'
        elif '/sheet/' in href:
            return '表格'
        elif '/slide/' in href:
            return '演示'
        elif '/form/' in href:
            return '表单'
        else:
            return '未知'

    async def download_documents_sequentially(self, documents, max_count=10):
        """按次序下载文档并监测每个下载"""
        print(f"\n[START] 开始按次序下载前 {min(max_count, len(documents))} 个文档...")
        
        download_count = 0
        success_count = 0
        
        for doc_info in documents[:max_count]:
            try:
                doc_index = doc_info['index']
                doc_title = doc_info['title']
                doc_type = doc_info['type']
                element = doc_info['element']
                
                print(f"\n[DOC {doc_index}] 准备下载: {doc_type} - {doc_title[:30]}...")
                
                # 滚动到元素位置
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                
                # 记录下载前的文件数量
                files_before = len(list(self.download_dir.glob('*')))
                downloads_before = len(self.downloaded_files)
                
                # 右键点击
                await element.click(button='right')
                await asyncio.sleep(2)
                
                # 查找并点击下载选项
                download_options = [
                    'text=下载',
                    'text=导出', 
                    'text=Download',
                    'text=Export',
                    '[data-action="download"]'
                ]
                
                download_triggered = False
                for option in download_options:
                    try:
                        download_btn = await self.page.wait_for_selector(option, timeout=3000)
                        if download_btn:
                            await download_btn.click()
                            print(f"[TRIGGER {doc_index}] 点击了: {option}")
                            download_triggered = True
                            download_count += 1
                            break
                    except:
                        continue
                
                if download_triggered:
                    # 等待下载开始和可能的格式选择对话框
                    await asyncio.sleep(3)
                    
                    # 处理可能的格式选择
                    await self.handle_download_format_dialog()
                    
                    # 等待下载完成（最多30秒）
                    wait_time = 0
                    max_wait = 30
                    
                    while wait_time < max_wait:
                        # 检查是否有新文件
                        files_after = len(list(self.download_dir.glob('*')))
                        downloads_after = len(self.downloaded_files)
                        
                        if files_after > files_before or downloads_after > downloads_before:
                            print(f"[SUCCESS {doc_index}] 下载完成检测到文件变化")
                            success_count += 1
                            break
                        
                        await asyncio.sleep(1)
                        wait_time += 1
                    
                    if wait_time >= max_wait:
                        print(f"[TIMEOUT {doc_index}] 下载超时，继续下一个")
                else:
                    print(f"[MISS {doc_index}] 未找到下载选项")
                
                # 点击空白处关闭菜单
                try:
                    await self.page.click('body', position={'x': 100, 'y': 100})
                    await asyncio.sleep(1)
                except:
                    pass
                
                # 显示进度
                print(f"[PROGRESS] 已处理 {doc_index}/{len(documents)} 个文档")
                
            except Exception as e:
                print(f"[ERROR] 文档 {doc_info['index']} 处理失败: {e}")
        
        return download_count, success_count

    async def handle_download_format_dialog(self):
        """处理下载格式选择对话框"""
        try:
            # 等待可能的格式选择对话框
            format_selectors = [
                'text=PDF',
                'text=Word',
                'text=Excel', 
                'text=确定',
                'text=下载',
                '.format-option',
                '[data-format="pdf"]'
            ]
            
            for selector in format_selectors:
                try:
                    option = await self.page.wait_for_selector(selector, timeout=2000)
                    if option:
                        await option.click()
                        print(f"[FORMAT] 选择了格式: {selector}")
                        await asyncio.sleep(1)
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"[INFO] 无格式选择对话框或处理失败: {e}")

    async def navigate_to_documents(self):
        """导航到文档页面"""
        print("\n[STEP] 访问腾讯文档桌面...")
        
        try:
            await self.page.goto('https://docs.qq.com/desktop/', 
                                wait_until='domcontentloaded', timeout=30000)
            
            print("[PAGE] 桌面页面加载完成")
            await asyncio.sleep(5)
            
            title = await self.page.title()
            print(f"[PAGE] 标题: {title}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 页面导航失败: {e}")
            return False

    async def print_download_summary(self):
        """打印下载总结"""
        print(f"\n" + "="*60)
        print("                  下载任务总结")
        print("="*60)
        
        print(f"实际下载文件数: {len(self.downloaded_files)}")
        print(f"下载目录: {self.download_dir}")
        
        if self.downloaded_files:
            print(f"\n下载的文件:")
            for i, file_path in enumerate(self.downloaded_files, 1):
                file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
                print(f"  {i}. {Path(file_path).name} ({file_size:,} 字节)")
        
        if self.current_downloads:
            print(f"\n下载状态详情:")
            for download_id, info in self.current_downloads.items():
                status = info['status']
                filename = info['filename']
                if status == 'completed':
                    size = info.get('size', 0)
                    duration = info.get('duration', 0)
                    print(f"  [{download_id}] ✅ {filename} - {size:,}字节 - {duration:.1f}秒")
                elif status == 'failed':
                    print(f"  [{download_id}] ❌ {filename} - 失败")
                elif status == 'error':
                    print(f"  [{download_id}] ⚠️ {filename} - 错误")

    async def run_download_task(self):
        """执行完整的下载任务"""
        print("\n" + "="*60)
        print("     改进版腾讯文档自动化下载 - 支持筛选和监测")
        print("="*60)
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                args=['--start-maximized', '--no-sandbox']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                accept_downloads=True
            )
            
            # 监听下载事件
            context.on('download', self.handle_download)
            
            self.page = await context.new_page()
            
            try:
                # 1. 设置Cookie
                print("[SETUP] 设置Cookie...")
                await context.add_cookies(self.parse_cookies())
                
                # 2. 导航到文档页面
                if not await self.navigate_to_documents():
                    return False
                
                # 3. 设置筛选条件
                await self.setup_filters()
                
                # 4. 查找筛选后的文档
                documents = await self.find_documents_with_details()
                
                if not documents:
                    print("[ERROR] 未找到任何文档")
                    return False
                
                # 5. 按次序下载文档
                download_count, success_count = await self.download_documents_sequentially(documents, 10)
                
                # 6. 等待所有下载完成
                print(f"\n[WAIT] 等待所有下载任务完成...")
                await asyncio.sleep(15)
                
                # 7. 打印总结
                await self.print_download_summary()
                
                print(f"\n[RESULT] 任务完成!")
                print(f"[STATS] 触发下载: {download_count} 个")
                print(f"[STATS] 成功下载: {success_count} 个")
                print(f"[STATS] 保存文件: {len(self.downloaded_files)} 个")
                
                return True
                
            except Exception as e:
                print(f"[ERROR] 执行异常: {e}")
                return False
                
            finally:
                print(f"\n[WAIT] 保持浏览器15秒供最终检查...")
                await asyncio.sleep(15)
                await browser.close()

async def main():
    downloader = ImprovedDownloader()
    success = await downloader.run_download_task()
    
    if success:
        print("\n[SUCCESS] 改进版下载任务执行成功！")
    else:
        print("\n[FAILED] 改进版下载任务执行失败")

if __name__ == "__main__":
    asyncio.run(main())