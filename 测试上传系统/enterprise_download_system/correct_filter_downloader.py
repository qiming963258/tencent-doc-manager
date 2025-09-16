#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确筛选版下载器 - 使用发现的真实筛选按钮
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

class CorrectFilterDownloader:
    def __init__(self):
        self.download_dir = Path("./downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        
        self.cookie_string = "fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; traceid=a473487816; TOK=a473487816963a48; hashkey=a4734878; dark_mode_setting=system; optimal_cdn_domain=docs.qq.com; ES2=f88c0411768984b9; _qpsvr_localtk=0.5895351222297797; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1ppSTZJbEZLVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1RZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; language=zh-CN; backup_cdn_domain=docs.gtimg.com"
        
        self.downloaded_files = []
        self.processed_docs = set()
        
        print("[SETUP] 正确筛选版下载器")
        print("[SETUP] 使用发现的真实筛选按钮: .desktop-filter-button-inner")

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
        """点击真正的筛选按钮"""
        print("\n[FILTER] 点击筛选按钮...")
        
        # 重要：设置dialog监听器防止弹窗卡顿
        self.page.on("dialog", lambda dialog: dialog.accept())
        print("[SETUP] 已设置dialog监听器")
        
        try:
            # 使用发现的真正选择器
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
                    
                    # 等待元素出现
                    filter_button = await self.page.wait_for_selector(selector, timeout=5000)
                    
                    if filter_button:
                        # 高亮显示
                        await self.page.evaluate('''(element) => {
                            element.style.border = '3px solid green';
                            element.style.backgroundColor = 'lightgreen';
                        }''', filter_button)
                        
                        print(f"[FOUND] 找到筛选按钮，高亮显示3秒...")
                        await asyncio.sleep(3)
                        
                        # 点击筛选按钮
                        await filter_button.click()
                        print(f"[CLICK] 成功点击筛选按钮！")
                        filter_clicked = True
                        
                        # 等待筛选面板出现
                        await asyncio.sleep(3)
                        break
                        
                except Exception as e:
                    print(f"[SKIP] {selector} 失败: {e}")
                    continue
            
            if not filter_clicked:
                print("[WARNING] 未能点击筛选按钮")
                return False
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 筛选按钮点击失败: {e}")
            return False

    async def analyze_filter_panel(self):
        """详细分析筛选面板结构"""
        print("\n[ANALYZE] 深度分析筛选面板结构...")
        
        try:
            # 查找筛选面板容器
            panel_selectors = [
                '.filter-panel',
                '.dui-modal',
                '.dropdown-menu',
                '[class*="filter"]',
                '[class*="dropdown"]',
                '[role="dialog"]'
            ]
            
            filter_panel = None
            for selector in panel_selectors:
                try:
                    panel = await self.page.wait_for_selector(selector, timeout=2000)
                    if panel:
                        filter_panel = panel
                        print(f"[FOUND] 筛选面板容器: {selector}")
                        break
                except:
                    continue
            
            if not filter_panel:
                print("[INFO] 未找到筛选面板容器，分析所有可见元素")
            
            # 获取筛选面板内的所有元素
            print("[ANALYZE] 筛选面板内容分析:")
            
            # 查找所有可能的筛选相关元素
            filter_elements = await self.page.query_selector_all('*')
            
            relevant_elements = []
            keywords = ['我的', '文档', '时间', '近', '月', '最近', '全部', 'my', 'document', 'time', 'recent', 'month', 'all']
            
            for element in filter_elements[:100]:  # 限制数量避免过多
                try:
                    text = await element.inner_text()
                    tag = await element.evaluate('el => el.tagName')
                    class_name = await element.get_attribute('class') or ''
                    
                    if any(keyword in text.lower() or keyword in class_name.lower() for keyword in keywords):
                        if len(text.strip()) > 0 and len(text) < 50:
                            element_info = {
                                'tag': tag,
                                'text': text.strip(),
                                'class': class_name,
                                'element': element
                            }
                            relevant_elements.append(element_info)
                except:
                    continue
            
            print(f"[FOUND] 找到 {len(relevant_elements)} 个相关元素:")
            for i, elem in enumerate(relevant_elements[:15]):  # 只显示前15个
                print(f"  [{i+1}] {elem['tag']} - '{elem['text']}' - {elem['class'][:30]}")
            
            # 特别查找具体的选项
            print(f"\n[SPECIFIC] 查找具体选项:")
            
            # 查找包含"我的"的元素
            my_elements = await self.page.query_selector_all('*:has-text("我的")')
            print(f"[MY] 包含'我的'的元素: {len(my_elements)} 个")
            
            # 查找包含"月"的元素
            month_elements = await self.page.query_selector_all('*:has-text("月")')
            print(f"[MONTH] 包含'月'的元素: {len(month_elements)} 个")
            
            # 查找所有radio/checkbox
            radio_elements = await self.page.query_selector_all('input[type="radio"], input[type="checkbox"]')
            print(f"[INPUT] 单选/复选框: {len(radio_elements)} 个")
            
            for i, radio in enumerate(radio_elements[:5]):
                try:
                    value = await radio.get_attribute('value') or ''
                    name = await radio.get_attribute('name') or ''
                    checked = await radio.is_checked()
                    print(f"  [INPUT {i+1}] value='{value}' name='{name}' checked={checked}")
                except:
                    continue
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 筛选面板分析失败: {e}")
            return False

    async def set_filter_options(self):
        """设置筛选选项：使用成功经验总结中的方法"""
        print("\n[FILTER] 使用成功经验总结中的方法设置筛选选项...")
        
        try:
            # 等待筛选面板加载
            print("[WAIT] 等待筛选面板完全加载...")
            await asyncio.sleep(5)
            
            # 1. 选择"所有者"区域的"我所有的"（第2项）
            print("\n[STEP 1] 选择所有者区域的'我所有的'...")
            
            owner_success = False
            try:
                # 找到"所有者"标题
                owner_header = await self.page.wait_for_selector('header:has-text("所有者")', timeout=5000)
                if owner_header:
                    print("[FOUND] 找到'所有者'标题")
                    
                    # 在所有者标题后找到对应的radio组
                    owner_radios = await self.page.query_selector_all('header:has-text("所有者") + div input[type="radio"]')
                    print(f"[DEBUG] 所有者区域找到 {len(owner_radios)} 个radio按钮")
                    
                    if len(owner_radios) >= 2:
                        # 选择第2项："我所有的"
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
                # 找到"查看时间"标题
                time_header = await self.page.wait_for_selector('header:has-text("查看时间")', timeout=5000)
                if time_header:
                    print("[FOUND] 找到'查看时间'标题")
                    
                    # 在查看时间标题后找到对应的radio组
                    time_radios = await self.page.query_selector_all('header:has-text("查看时间") + div input[type="radio"]')
                    print(f"[DEBUG] 查看时间区域找到 {len(time_radios)} 个radio按钮")
                    
                    if len(time_radios) >= 3:
                        # 选择第3项："近1个月"
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
                'button:has-text("确定")',
                '.filter-apply',
                '.apply-button'
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
            
            return owner_success and time_success
            
        except Exception as e:
            print(f"[ERROR] 设置筛选选项失败: {e}")
            return True  # 继续执行，即使筛选失败

    async def find_filtered_documents(self):
        """查找筛选后的文档 - 增强版：支持分页和滚动加载"""
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
        initial_count = 0
        
        # 第一次查找，获取初始文档数量
        print("[SEARCH] 第一次扫描当前可见文档...")
        for selector in doc_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                print(f"[SEARCH] {selector}: 找到 {len(elements)} 个")
                initial_count += len(elements)
                
                for element in elements:
                    try:
                        # 关键修复：避免意外触发点击，使用textContent而不是inner_text
                        href = await element.get_attribute('href')
                        # 使用evaluate获取文本内容，避免触发点击事件
                        text = await element.evaluate('el => el.textContent || el.innerText || ""')
                        bbox = await element.bounding_box()
                        
                        if href and text and href not in all_docs:
                            all_docs[href] = {
                                'element': element,
                                'href': href,
                                'title': text.strip(),
                                'position': bbox,
                                'type': self.get_doc_type(href)
                            }
                    except Exception as e:
                        # 调试信息：如果出现异常，记录但不中断
                        print(f"[DEBUG] 元素处理异常: {str(e)[:50]}")
                        continue
            except:
                continue
        
        print(f"[SEARCH] 初始扫描找到 {len(all_docs)} 个不重复文档")
        
        # 智能滚动加载更多文档（如果需要超过当前数量）
        if len(all_docs) < 10:  # 如果文档不足10个，尝试滚动加载更多
            print(f"[SCROLL] 当前文档数量不足10个，尝试滚动加载更多...")
            
            max_scrolls = 5  # 最多滚动5次
            last_count = len(all_docs)
            
            for scroll_count in range(max_scrolls):
                print(f"[SCROLL] 第 {scroll_count + 1} 次滚动加载...")
                
                # 滚动到页面底部
                await self.page.evaluate('''() => {
                    window.scrollTo(0, document.body.scrollHeight);
                }''')
                
                # 等待新内容加载
                await asyncio.sleep(3)
                
                # 检查是否有"加载更多"按钮
                load_more_selectors = [
                    'button:has-text("加载更多")',
                    'button:has-text("Load More")', 
                    'text=查看更多',
                    'text=Show More',
                    '[class*="load-more"]',
                    '[class*="show-more"]'
                ]
                
                for selector in load_more_selectors:
                    try:
                        load_more_btn = await self.page.wait_for_selector(selector, timeout=2000)
                        if load_more_btn and await load_more_btn.is_visible():
                            await load_more_btn.click()
                            print(f"[SCROLL] 点击了加载更多按钮: {selector}")
                            await asyncio.sleep(3)
                            break
                    except:
                        continue
                
                # 重新扫描文档
                current_docs = {}
                current_total = 0
                
                for selector in doc_selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        current_total += len(elements)
                        
                        for element in elements:
                            try:
                                # 关键修复：避免意外触发点击，使用textContent而不是inner_text
                                href = await element.get_attribute('href')
                                # 使用evaluate获取文本内容，避免触发点击事件
                                text = await element.evaluate('el => el.textContent || el.innerText || ""')
                                bbox = await element.bounding_box()
                                
                                if href and text and href not in current_docs:
                                    current_docs[href] = {
                                        'element': element,
                                        'href': href,
                                        'title': text.strip(),
                                        'position': bbox,
                                        'type': self.get_doc_type(href)
                                    }
                            except Exception as e:
                                # 调试信息：如果出现异常，记录但不中断
                                print(f"[DEBUG] 滚动扫描元素异常: {str(e)[:50]}")
                                continue
                    except:
                        continue
                
                print(f"[SCROLL] 滚动后找到 {len(current_docs)} 个不重复文档（总计 {current_total} 个元素）")
                
                # 检查是否有新文档加载
                if len(current_docs) > last_count:
                    print(f"[SCROLL] 新增 {len(current_docs) - last_count} 个文档")
                    all_docs.update(current_docs)
                    last_count = len(current_docs)
                    
                    # 如果达到目标数量，停止滚动
                    if len(all_docs) >= 10:
                        print(f"[SCROLL] 已达到目标数量，停止滚动")
                        break
                else:
                    print(f"[SCROLL] 未发现新文档，可能已到底部")
                    break
                    
                all_docs = current_docs
        
        # 按位置排序（从上到下）
        sorted_docs = sorted(all_docs.values(), 
                           key=lambda x: x['position']['y'] if x['position'] else 0)
        
        print(f"\n[FOUND] 最终找到 {len(sorted_docs)} 个筛选后的文档:")
        for i, doc in enumerate(sorted_docs, 1):
            print(f"  [{i}] {doc['type']} - {doc['title'][:40]}...")
        
    async def find_filtered_documents_safe(self):
        """安全查找筛选后的文档 - 支持滚动加载更多文档"""
        print("\n[SAFE-SEARCH] 安全扫描模式：只查看，不点击...")
        
        # 等待一下确保页面完全加载
        await asyncio.sleep(3)
        
        # 文档选择器
        doc_selectors = [
            'a[href*="/doc/"]',
            'a[href*="/sheet/"]', 
            'a[href*="/slide/"]',
            'a[href*="/form/"]'
        ]
        
        all_docs = {}
        
        # 第一次扫描
        print("[SAFE-SEARCH] 第一次安全扫描当前可见文档...")
        for selector in doc_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                print(f"[SAFE-SEARCH] {selector}: 找到 {len(elements)} 个")
                
                for i, element in enumerate(elements):
                    try:
                        href = await element.get_attribute('href') 
                        if not href or href in all_docs:
                            continue
                            
                        try:
                            title = await element.evaluate('(el) => el.textContent || el.innerText || el.getAttribute("title") || "未知文档"')
                        except:
                            title = f"文档_{len(all_docs)+1}"
                            
                        try:
                            bbox = await element.bounding_box()
                        except:
                            bbox = {'x': 0, 'y': len(all_docs) * 50, 'width': 100, 'height': 20}
                        
                        all_docs[href] = {
                            'element': None,  
                            'href': href,
                            'title': title.strip() if title else f"文档_{len(all_docs)+1}",
                            'position': bbox,
                            'type': self.get_doc_type(href)
                        }
                            
                    except Exception as e:
                        print(f"[DEBUG] 安全扫描元素异常: {str(e)[:30]}")
                        continue
                        
            except Exception as e:
                print(f"[DEBUG] 安全扫描选择器异常: {str(e)[:30]}")
                continue
        
        print(f"[SAFE-SEARCH] 初始扫描找到 {len(all_docs)} 个文档")
        
        # 智能滚动加载更多文档（目标20个）
        if len(all_docs) < 20:
            print(f"[SCROLL] 当前文档数量不足20个，开始滚动加载更多...")
            
            max_scrolls = 8  # 增加滚动次数
            last_count = len(all_docs)
            
            for scroll_count in range(max_scrolls):
                print(f"[SCROLL] 第 {scroll_count + 1} 次滚动加载...")
                
                # 滚动到页面底部
                await self.page.evaluate('''() => {
                    window.scrollTo(0, document.body.scrollHeight);
                }''')
                
                # 等待新内容加载
                await asyncio.sleep(4)
                
                # 检查是否有"加载更多"按钮
                load_more_selectors = [
                    'button:has-text("加载更多")',
                    'button:has-text("Load More")', 
                    'text=查看更多',
                    'text=Show More',
                    '[class*="load-more"]',
                    '[class*="show-more"]',
                    'button:has-text("展示更多")'
                ]
                
                for selector in load_more_selectors:
                    try:
                        load_more_btn = await self.page.wait_for_selector(selector, timeout=2000)
                        if load_more_btn and await load_more_btn.is_visible():
                            await load_more_btn.click()
                            print(f"[SCROLL] 点击了加载更多按钮: {selector}")
                            await asyncio.sleep(4)
                            break
                    except:
                        continue
                
                # 重新扫描所有文档
                current_docs = {}
                current_total = 0
                
                for selector in doc_selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        current_total += len(elements)
                        
                        for i, element in enumerate(elements):
                            try:
                                href = await element.get_attribute('href')
                                if not href or href in current_docs:
                                    continue
                                    
                                try:
                                    title = await element.evaluate('(el) => el.textContent || el.innerText || el.getAttribute("title") || "未知文档"')
                                except:
                                    title = f"文档_{len(current_docs)+1}"
                                    
                                try:
                                    bbox = await element.bounding_box()
                                except:
                                    bbox = {'x': 0, 'y': len(current_docs) * 50, 'width': 100, 'height': 20}
                                
                                current_docs[href] = {
                                    'element': None,
                                    'href': href,
                                    'title': title.strip() if title else f"文档_{len(current_docs)+1}",
                                    'position': bbox,
                                    'type': self.get_doc_type(href)
                                }
                                
                            except Exception as e:
                                print(f"[DEBUG] 滚动扫描元素异常: {str(e)[:30]}")
                                continue
                    except:
                        continue
                
                print(f"[SCROLL] 滚动后找到 {len(current_docs)} 个不重复文档（总计 {current_total} 个元素）")
                
                # 检查是否有新文档加载
                if len(current_docs) > last_count:
                    new_count = len(current_docs) - last_count
                    print(f"[SCROLL] 新增 {new_count} 个文档")
                    all_docs.update(current_docs)
                    last_count = len(current_docs)
                    
                    # 如果达到目标数量，停止滚动
                    if len(all_docs) >= 20:
                        print(f"[SCROLL] 已达到目标数量20个，停止滚动")
                        break
                else:
                    print(f"[SCROLL] 未发现新文档，尝试继续滚动...")
                    # 即使没有新文档也继续滚动几次，可能需要时间加载
                    if scroll_count >= 3:  # 至少滚动4次
                        print(f"[SCROLL] 滚动4次后仍无新文档，可能已到底部")
                        break
                    
                all_docs = current_docs
        
        # 按位置排序（从上到下）
        sorted_docs = sorted(all_docs.values(), 
                           key=lambda x: x['position']['y'] if x['position'] else 0)
        
        print(f"\n[SAFE-SEARCH] 安全扫描完成，找到 {len(sorted_docs)} 个文档:")
        for i, doc in enumerate(sorted_docs, 1):
            print(f"  [{i:2d}] {doc['type']} - {doc['title'][:40]}...")
            
        # 文档数量分析
        if len(sorted_docs) >= 20:
            print(f"\n[SUCCESS] 找到足够文档进行20个下载测试")
        elif len(sorted_docs) >= 10:
            print(f"\n[INFO] 找到 {len(sorted_docs)} 个文档，可进行基础下载测试")
        else:
            print(f"\n[WARNING] 文档数量较少 ({len(sorted_docs)} 个)")
            
    async def ensure_desktop_page(self):
        """确保当前在桌面页面，如果不是则想办法回到桌面"""
        current_url = self.page.url
        print(f"[URL-CHECK] 当前页面: {current_url}")
        
        # 如果已经在桌面页面，直接返回
        if '/desktop' in current_url and 'docs.qq.com' in current_url:
            print(f"[OK] 已在腾讯文档桌面页面")
            return True
        
        # 如果在文件内部或其他页面，尝试返回桌面
        if any(path in current_url for path in ['/doc/', '/sheet/', '/slide/', '/form/', '/pad/']):
            print(f"[DETECTED] 当前在文件内部，准备返回桌面...")
            
            # 尝试多种返回方式
            methods = [
                ("浏览器后退", lambda: self.page.go_back(wait_until='domcontentloaded', timeout=10000)),
                ("点击桌面按钮", lambda: self._click_desktop_button()),
                ("直接跳转", lambda: self.page.goto('https://docs.qq.com/desktop/', wait_until='domcontentloaded', timeout=15000))
            ]
            
            for method_name, method_func in methods:
                try:
                    print(f"[TRY] 尝试{method_name}...")
                    await method_func()
                    await asyncio.sleep(3)
                    
                    # 检查是否成功返回桌面
                    new_url = self.page.url
                    if '/desktop' in new_url:
                        print(f"[SUCCESS] 通过{method_name}成功返回桌面")
                        return True
                    else:
                        print(f"[FAIL] {method_name}未能返回桌面，当前: {new_url}")
                        
                except Exception as e:
                    print(f"[ERROR] {method_name}失败: {str(e)[:50]}")
                    continue
                    
            print(f"[ERROR] 所有返回桌面的方法都失败了")
            return False
        
        else:
            print(f"[INFO] 当前在其他腾讯文档页面: {current_url}")
            # 尝试直接跳转到桌面
            try:
                await self.page.goto('https://docs.qq.com/desktop/', wait_until='domcontentloaded', timeout=15000)
                print(f"[SUCCESS] 已跳转到腾讯文档桌面")
                return True
            except Exception as e:
                print(f"[ERROR] 跳转到桌面失败: {e}")
                return False

    async def _click_desktop_button(self):
        """尝试点击桌面按钮返回"""
        desktop_selectors = [
            'text=桌面',
            'text=Desktop', 
            'a[href*="/desktop"]',
            'button:has-text("桌面")',
            '[title="桌面"]',
            '.desktop-nav-item'
        ]
        
        for selector in desktop_selectors:
            try:
                desktop_btn = await self.page.wait_for_selector(selector, timeout=3000)
                if desktop_btn and await desktop_btn.is_visible():
                    await desktop_btn.click()
                    print(f"[SUCCESS] 点击了桌面按钮: {selector}")
                    return
            except:
                continue
                
        raise Exception("未找到桌面按钮")

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
        """按顺序下载文档 - 修复版：避免错误进入文件内部"""
        print(f"\n[DOWNLOAD] 开始按顺序下载前 {min(max_count, len(documents))} 个文档...")
        
        success_count = 0
        
        for i, doc in enumerate(documents[:max_count]):
            try:
                if doc['href'] in self.processed_docs:
                    print(f"[SKIP {i+1}] 已处理: {doc['title'][:30]}")
                    continue
                
                print(f"\n[DOC {i+1}] 下载: {doc['type']} - {doc['title'][:40]}")
                
                # 重新定位元素 - 关键：避免stale元素
                fresh_element = await self.page.query_selector(f'a[href="{doc["href"]}"]')
                if not fresh_element:
                    print(f"[ERROR {i+1}] 无法重新定位元素")
                    continue
                
                self.processed_docs.add(doc['href'])
                
                # 滚动到元素并高亮
                await fresh_element.scroll_into_view_if_needed()
                await self.page.evaluate('''(element) => {
                    element.style.border = '3px solid blue';
                    element.style.backgroundColor = 'lightblue';
                }''', fresh_element)
                
                await asyncio.sleep(2)
                
                # 关键修复：精确的右键下载逻辑
                print(f"[ACTION {i+1}] 执行精确右键下载...")
                
                # 方法1：尝试直接在元素中心位置右键点击
                bounding_box = await fresh_element.bounding_box()
                if bounding_box:
                    # 计算元素中心位置
                    center_x = bounding_box['x'] + bounding_box['width'] / 2
                    center_y = bounding_box['y'] + bounding_box['height'] / 2
                    
                    print(f"[DEBUG {i+1}] 右键点击位置: ({center_x:.0f}, {center_y:.0f})")
                    
                    # 在精确位置右键点击
                    await self.page.mouse.click(center_x, center_y, button='right')
                    await asyncio.sleep(3)
                    
                    # 查找右键菜单中的下载选项
                    download_options = [
                        'text=下载',
                        'text=导出', 
                        'text=Download',
                        'text=Export',
                        '[aria-label*="下载"]',
                        '[title*="下载"]',
                        'div:has-text("下载")',
                        'li:has-text("下载")',
                        'button:has-text("下载")'
                    ]
                    
                    downloaded = False
                    
                    for option in download_options:
                        try:
                            print(f"[SEARCH {i+1}] 查找下载选项: {option}")
                            btn = await self.page.wait_for_selector(option, timeout=2000)
                            if btn:
                                # 验证按钮可见且可点击
                                is_visible = await btn.is_visible()
                                if is_visible:
                                    await btn.click()
                                    print(f"[SUCCESS {i+1}] 点击了下载选项: {option}")
                                    downloaded = True
                                    success_count += 1
                                    await asyncio.sleep(3)
                                    break
                                else:
                                    print(f"[SKIP {i+1}] 选项不可见: {option}")
                        except Exception as e:
                            print(f"[SKIP {i+1}] {option} 失败: {str(e)[:50]}")
                            continue
                    
                    if not downloaded:
                        print(f"[FALLBACK {i+1}] 尝试备用下载方法...")
                        
                        # 备用方法：尝试hover + 右键
                        try:
                            await fresh_element.hover()
                            await asyncio.sleep(1)
                            await fresh_element.click(button='right')
                            await asyncio.sleep(2)
                            
                            # 再次尝试查找下载选项
                            for option in download_options[:3]:  # 只尝试主要选项
                                try:
                                    btn = await self.page.wait_for_selector(option, timeout=1500)
                                    if btn and await btn.is_visible():
                                        await btn.click()
                                        print(f"[BACKUP {i+1}] 备用方法成功: {option}")
                                        downloaded = True
                                        success_count += 1
                                        break
                                except:
                                    continue
                        except Exception as e:
                            print(f"[FAIL {i+1}] 备用方法也失败: {e}")
                    
                    if not downloaded:
                        print(f"[MISS {i+1}] 未找到可用的下载选项")
                
                # 清除高亮并点击空白处关闭菜单
                try:
                    await self.page.evaluate('''(element) => {
                        element.style.border = '';
                        element.style.backgroundColor = '';
                    }''', fresh_element)
                    
                    # 点击页面空白处关闭任何弹出菜单
                    await self.page.click('body', position={'x': 50, 'y': 50})
                    await asyncio.sleep(2)
                except:
                    pass
                
            except Exception as e:
                print(f"[ERROR {i+1}] 处理失败: {e}")
        
    async def download_docs_in_sequence_safe(self, documents, max_count=10):
        """安全的按顺序下载文档 - 重新查找元素避免stale引用"""
        print(f"\n[SAFE-DOWNLOAD] 开始安全下载前 {min(max_count, len(documents))} 个文档...")
        
        success_count = 0
        
        for i, doc in enumerate(documents[:max_count]):
            try:
                if doc['href'] in self.processed_docs:
                    print(f"[SKIP {i+1}] 已处理: {doc['title'][:30]}")
                    continue
                
                print(f"\n[DOC {i+1}] 准备下载: {doc['type']} - {doc['title'][:40]}")
                
                # 重新查找元素（因为安全扫描时没有保存element引用）
                print(f"[LOCATE {i+1}] 重新定位元素...")
                fresh_element = await self.page.query_selector(f'a[href="{doc["href"]}"]')
                
                if not fresh_element:
                    print(f"[ERROR {i+1}] 无法重新定位元素: {doc['href']}")
                    continue
                
                self.processed_docs.add(doc['href'])
                
                # 滚动到元素并高亮
                await fresh_element.scroll_into_view_if_needed()
                await self.page.evaluate('''(element) => {
                    element.style.border = '3px solid blue';
                    element.style.backgroundColor = 'lightblue';
                }''', fresh_element)
                
                await asyncio.sleep(2)
                
                # 精确的右键下载逻辑
                print(f"[ACTION {i+1}] 执行精确右键下载...")
                
                bounding_box = await fresh_element.bounding_box()
                if bounding_box:
                    # 计算元素中心位置
                    center_x = bounding_box['x'] + bounding_box['width'] / 2
                    center_y = bounding_box['y'] + bounding_box['height'] / 2
                    
                    print(f"[DEBUG {i+1}] 右键点击位置: ({center_x:.0f}, {center_y:.0f})")
                    
                    # 在精确位置右键点击
                    await self.page.mouse.click(center_x, center_y, button='right')
                    await asyncio.sleep(3)
                    
                    # 查找右键菜单中的下载选项
                    download_options = [
                        'text=下载',
                        'text=导出', 
                        'text=Download',
                        'text=Export'
                    ]
                    
                    downloaded = False
                    
                    for option in download_options:
                        try:
                            print(f"[SEARCH {i+1}] 查找下载选项: {option}")
                            btn = await self.page.wait_for_selector(option, timeout=2000)
                            if btn and await btn.is_visible():
                                await btn.click()
                                print(f"[SUCCESS {i+1}] 点击了下载选项: {option}")
                                downloaded = True
                                success_count += 1
                                await asyncio.sleep(3)
                                break
                        except Exception as e:
                            print(f"[SKIP {i+1}] {option} 失败: {str(e)[:30]}")
                            continue
                    
                    if not downloaded:
                        print(f"[MISS {i+1}] 未找到可用的下载选项")
                
                # 清除高亮并点击空白处关闭菜单
                try:
                    await self.page.evaluate('''(element) => {
                        element.style.border = '';
                        element.style.backgroundColor = '';
                    }''', fresh_element)
                    
                    # 点击页面空白处关闭任何弹出菜单
                    await self.page.click('body', position={'x': 50, 'y': 50})
                    await asyncio.sleep(2)
                except:
                    pass
                
            except Exception as e:
                print(f"[ERROR {i+1}] 处理失败: {e}")
        
        return success_count

    async def run_correct_filter_download(self):
        """执行正确的筛选下载"""
        print("\n" + "="*60)
        print("        正确筛选版腾讯文档下载器")
        print("      使用真实的筛选按钮和筛选逻辑")
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
                
                # 2. 点击真正的筛选按钮
                if await self.click_filter_button():
                    # 3. 设置筛选选项
                    await self.set_filter_options()
                else:
                    print("[WARNING] 筛选按钮点击失败，继续使用默认筛选")
                
                # 4. 筛选完成后等待页面稳定，然后处理可能的意外跳转
                print("\n[WAIT] 筛选完成，等待页面稳定...")
                await asyncio.sleep(10)  # 给足时间让筛选结果加载
                
                # 使用增强的桌面页面检查功能
                if not await self.ensure_desktop_page():
                    print("[ERROR] 无法返回到桌面页面")
                    return False
                
                print("[INFO] 筛选设置完成，停止执行，不进行文档扫描！")
                
                # 紧急停止：不执行任何文档相关操作
                print("\n[STOP] 为防止意外点击文件，程序在筛选后停止")
                print("[SUCCESS] 筛选功能测试完成")
                
                # 保持浏览器打开供用户观察筛选结果
                print("\n[WAIT] 保持浏览器30秒供检查筛选结果...")
                await asyncio.sleep(30)
                
                return True
                
            except Exception as e:
                print(f"[ERROR] 执行失败: {e}")
                return False
                
            finally:
                print(f"\n[WAIT] 保持浏览器20秒供检查...")
                await asyncio.sleep(20)
                await browser.close()

async def main():
    downloader = CorrectFilterDownloader()
    success = await downloader.run_correct_filter_download()
    
    if success:
        print("\n[SUCCESS] 正确筛选版下载完成！")
    else:
        print("\n[FAILED] 正确筛选版下载失败")

if __name__ == "__main__":
    asyncio.run(main())