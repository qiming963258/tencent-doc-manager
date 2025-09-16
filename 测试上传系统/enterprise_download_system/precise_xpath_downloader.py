#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确XPath筛选下载器 - 使用用户提供的精确XPath定位
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

class PreciseXPathDownloader:
    def __init__(self):
        self.download_dir = Path("./downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        
        self.cookie_string = "fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; traceid=a473487816; TOK=a473487816963a48; hashkey=a4734878; dark_mode_setting=system; optimal_cdn_domain=docs.qq.com; ES2=f88c0411768984b9; _qpsvr_localtk=0.5895351222297797; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1ppSTZJbEZLVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1pZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; language=zh-CN; backup_cdn_domain=docs.gtimg.com"
        
        self.downloaded_files = []
        self.processed_docs = set()
        
        print("[SETUP] 精确XPath筛选下载器")
        print("[SETUP] 使用用户提供的精确XPath定位筛选选项")

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
        
        # 设置dialog监听器防止弹窗卡顿
        self.page.on("dialog", lambda dialog: dialog.accept())
        print("[SETUP] 已设置dialog监听器")
        
        try:
            # 使用已验证的筛选按钮选择器
            filter_btn = await self.page.wait_for_selector('button:has-text("筛选")', timeout=10000)
            
            if filter_btn:
                # 高亮显示
                await self.page.evaluate('''(element) => {
                    element.style.border = '3px solid green';
                    element.style.backgroundColor = 'lightgreen';
                }''', filter_btn)
                
                print(f"[FOUND] 找到筛选按钮，高亮显示3秒...")
                await asyncio.sleep(3)
                
                # 点击筛选按钮
                await filter_btn.click()
                print(f"[CLICK] 成功点击筛选按钮！")
                
                # 等待筛选面板出现
                await asyncio.sleep(5)
                return True
            else:
                print("[ERROR] 未找到筛选按钮")
                return False
            
        except Exception as e:
            print(f"[ERROR] 筛选按钮点击失败: {e}")
            return False

    async def analyze_filter_structure(self):
        """深度分析筛选弹窗的DOM结构"""
        print("\n[ANALYZE] 深度分析筛选弹窗DOM结构...")
        
        try:
            # 等待弹窗完全加载
            await asyncio.sleep(3)
            
            # 查找所有radio按钮并分析它们的位置关系
            all_radios = await self.page.query_selector_all('input[type="radio"]')
            print(f"[FOUND] 弹窗内共有 {len(all_radios)} 个radio按钮")
            
            # 分析每个radio的详细信息
            for i, radio in enumerate(all_radios):
                try:
                    # 获取基本属性
                    class_name = await radio.get_attribute('class')
                    value = await radio.get_attribute('value') or ''
                    name = await radio.get_attribute('name') or ''
                    is_checked = await radio.is_checked()
                    
                    # 尝试找到关联的标签文本
                    try:
                        # 查找父元素或附近的文本
                        parent = await radio.evaluate('''(el) => {
                            // 向上查找包含文本的父元素
                            let parent = el.parentElement;
                            while (parent && parent.innerText.trim().length < 2) {
                                parent = parent.parentElement;
                                if (!parent || parent.tagName === 'BODY') break;
                            }
                            return parent ? parent.innerText.trim() : '';
                        }''')
                    except:
                        parent = ''
                    
                    # 获取XPath
                    try:
                        xpath = await radio.evaluate('''(el) => {
                            function getXPath(element) {
                                if (element.id) return `//*[@id="${element.id}"]`;
                                if (element === document.body) return '/html/body';
                                
                                let path = '';
                                while (element && element.nodeType === Node.ELEMENT_NODE) {
                                    let selector = element.nodeName.toLowerCase();
                                    if (element.previousSibling) {
                                        let sibling = element.previousSibling;
                                        let nth = 1;
                                        while (sibling) {
                                            if (sibling.nodeType === Node.ELEMENT_NODE && sibling.nodeName === element.nodeName) {
                                                nth++;
                                            }
                                            sibling = sibling.previousSibling;
                                        }
                                        if (nth !== 1) selector += `[${nth}]`;
                                    }
                                    path = '/' + selector + path;
                                    element = element.parentNode;
                                }
                                return '/html' + path;
                            }
                            return getXPath(el);
                        }''')
                    except:
                        xpath = 'XPath获取失败'
                    
                    print(f"[RADIO {i+1}]")
                    print(f"  - class: {class_name}")
                    print(f"  - value: {value}")
                    print(f"  - name: {name}")
                    print(f"  - checked: {is_checked}")
                    print(f"  - 关联文本: {parent[:50]}...")
                    print(f"  - XPath: {xpath}")
                    print(f"  - 匹配用户XPath: {'YES' if xpath == '/html/body/div[1]/div[1]/div[4]/div/div/div/div/div[1]/div/div[6]/div[3]/input' else 'NO'}")
                    print()
                    
                except Exception as e:
                    print(f"[ERROR] Radio {i+1} 分析失败: {e}")
                    continue
            
            return True
            
        except Exception as e:
            print(f"[ERROR] DOM结构分析失败: {e}")
            return False

    async def set_precise_filter_options(self):
        """使用精确方法设置筛选选项"""
        print("\n[FILTER] 使用精确XPath设置筛选选项...")
        
        try:
            # 等待筛选面板完全加载
            await asyncio.sleep(5)
            
            success_count = 0
            
            # 1. 尝试选择"我所有的"选项 - 基于DOM结构推测位置
            print("\n[STEP 1] 选择'我所有的'选项...")
            
            # 由于用户只提供了"近一个月"的XPath，我们需要推测"我所有的"位置
            # 根据筛选弹窗的一般结构，"我所有的"应该在"所有者"区域
            my_docs_selectors = [
                # 尝试通过文本关联找到
                'input[type="radio"] + label:has-text("我所有")',
                'label:has-text("我所有") input[type="radio"]',
                # 尝试通过相对XPath位置推测
                'xpath=/html/body/div[1]/div[1]/div[4]/div/div/div/div/div[1]/div/div[2]/div[2]/input',
                'xpath=/html/body/div[1]/div[1]/div[4]/div/div/div/div/div[1]/div/div[3]/div[2]/input',
                'xpath=/html/body/div[1]/div[1]/div[4]/div/div/div/div/div[1]/div/div[4]/div[2]/input',
            ]
            
            for selector in my_docs_selectors:
                try:
                    print(f"[TRY] 尝试'我所有的'选择器: {selector}")
                    my_option = await self.page.wait_for_selector(selector, timeout=3000)
                    if my_option:
                        # 检查当前状态
                        is_checked_before = await my_option.is_checked()
                        print(f"[DEBUG] '我所有的'初始状态: {is_checked_before}")
                        
                        # 选择
                        await my_option.check()
                        await asyncio.sleep(2)
                        
                        # 验证
                        is_checked_after = await my_option.is_checked()
                        if is_checked_after:
                            print(f"[SUCCESS] '我所有的'选项选择成功！")
                            success_count += 1
                            break
                        else:
                            print(f"[FAIL] '我所有的'选项选择失败")
                except Exception as e:
                    print(f"[SKIP] {selector} 失败: {str(e)[:50]}")
                    continue
            
            # 2. 使用用户提供的精确XPath选择"近一个月"
            print("\n[STEP 2] 使用用户精确XPath选择'近一个月'...")
            
            try:
                user_xpath = '/html/body/div[1]/div[1]/div[4]/div/div/div/div/div[1]/div/div[6]/div[3]/input'
                print(f"[XPATH] 用户提供的精确路径: {user_xpath}")
                
                month_option = await self.page.wait_for_selector(f'xpath={user_xpath}', timeout=5000)
                if month_option:
                    # 高亮显示找到的元素
                    await self.page.evaluate('''(element) => {
                        element.style.border = '3px solid red';
                        element.style.backgroundColor = 'yellow';
                    }''', month_option)
                    
                    print(f"[FOUND] 找到'近一个月'选项，高亮显示3秒...")
                    await asyncio.sleep(3)
                    
                    # 检查当前状态
                    is_checked_before = await month_option.is_checked()
                    print(f"[DEBUG] '近一个月'初始状态: {is_checked_before}")
                    
                    # 选择
                    await month_option.check()
                    await asyncio.sleep(2)
                    
                    # 验证
                    is_checked_after = await month_option.is_checked()
                    if is_checked_after:
                        print(f"[SUCCESS] '近一个月'选项选择成功！")
                        success_count += 1
                    else:
                        print(f"[FAIL] '近一个月'选项选择失败")
                        
                    # 清除高亮
                    await self.page.evaluate('''(element) => {
                        element.style.border = '';
                        element.style.backgroundColor = '';
                    }''', month_option)
                    
                else:
                    print(f"[ERROR] 用户XPath未找到元素")
                    
            except Exception as e:
                print(f"[ERROR] 用户XPath选择失败: {e}")
            
            # 3. 应用筛选设置
            print("\n[STEP 3] 应用筛选设置...")
            
            apply_options = [
                'text=应用',
                'text=确定',
                'text=Apply',
                'text=OK',
                'button:has-text("应用")',
                'button:has-text("确定")'
            ]
            
            apply_clicked = False
            for option in apply_options:
                try:
                    print(f"[APPLY] 查找应用按钮: {option}")
                    apply_btn = await self.page.wait_for_selector(option, timeout=3000)
                    if apply_btn:
                        await apply_btn.click()
                        print(f"[SUCCESS] 点击了应用按钮: {option}")
                        apply_clicked = True
                        await asyncio.sleep(5)
                        break
                except:
                    continue
            
            # 报告结果
            print(f"\n" + "="*50)
            print("           筛选设置结果")
            print("="*50)
            print(f"成功设置选项数: {success_count}/2")
            print(f"应用设置: {'[成功]' if apply_clicked else '[失败]'}")
            print(f"整体状态: {'[成功]' if success_count >= 1 and apply_clicked else '[部分成功]' if success_count > 0 else '[失败]'}")
            
            return success_count > 0 and apply_clicked
            
        except Exception as e:
            print(f"[ERROR] 设置筛选选项失败: {e}")
            return False

    async def find_and_download_documents(self, max_count=10):
        """查找并下载文档"""
        print(f"\n[SEARCH] 查找筛选后的文档（目标:{max_count}个）...")
        
        # 等待筛选结果加载
        await asyncio.sleep(8)
        
        # 文档选择器
        doc_selectors = [
            'a[href*="/doc/"]',
            'a[href*="/sheet/"]',
            'a[href*="/slide/"]',
            'a[href*="/form/"]'
        ]
        
        all_docs = {}
        
        # 查找文档
        for selector in doc_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                print(f"[SEARCH] {selector}: 找到 {len(elements)} 个")
                
                for element in elements:
                    try:
                        href = await element.get_attribute('href')
                        if href and href not in all_docs:
                            # 安全获取文本内容
                            title = await element.evaluate('el => el.textContent || el.innerText || "未知文档"')
                            bbox = await element.bounding_box()
                            
                            all_docs[href] = {
                                'element': None,  # 不保存引用避免stale
                                'href': href,
                                'title': title.strip()[:40],
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
        
        print(f"\n[FOUND] 找到 {len(sorted_docs)} 个筛选后的文档:")
        for i, doc in enumerate(sorted_docs[:max_count], 1):
            print(f"  [{i}] {doc['type']} - {doc['title']}")
        
        # 下载文档
        if sorted_docs:
            success_count = await self.download_docs_sequence(sorted_docs[:max_count])
            return success_count
        else:
            print("[ERROR] 未找到任何文档")
            return 0

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

    async def download_docs_sequence(self, documents):
        """按顺序下载文档"""
        print(f"\n[DOWNLOAD] 开始下载 {len(documents)} 个文档...")
        
        success_count = 0
        
        for i, doc in enumerate(documents):
            try:
                if doc['href'] in self.processed_docs:
                    print(f"[SKIP {i+1}] 已处理: {doc['title']}")
                    continue
                
                print(f"\n[DOC {i+1}] 下载: {doc['type']} - {doc['title']}")
                
                # 重新定位元素
                fresh_element = await self.page.query_selector(f'a[href="{doc["href"]}"]')
                if not fresh_element:
                    print(f"[ERROR {i+1}] 无法定位元素")
                    continue
                
                self.processed_docs.add(doc['href'])
                
                # 滚动到元素
                await fresh_element.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                
                # 右键点击
                await fresh_element.click(button='right')
                await asyncio.sleep(3)
                
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
                        btn = await self.page.wait_for_selector(option, timeout=2000)
                        if btn and await btn.is_visible():
                            await btn.click()
                            print(f"[SUCCESS {i+1}] 下载选项点击成功: {option}")
                            downloaded = True
                            success_count += 1
                            await asyncio.sleep(3)
                            break
                    except:
                        continue
                
                if not downloaded:
                    print(f"[MISS {i+1}] 未找到下载选项")
                
                # 点击空白处关闭菜单
                await self.page.click('body', position={'x': 50, 'y': 50})
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[ERROR {i+1}] 下载处理失败: {e}")
        
        return success_count

    async def run_precise_download(self):
        """运行精确筛选下载"""
        print("\n" + "="*60)
        print("        精确XPath筛选下载器")
        print("      使用用户提供的精确元素定位")
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
                
                # 3. 深度分析筛选弹窗结构
                await self.analyze_filter_structure()
                
                # 4. 设置精确的筛选选项
                if not await self.set_precise_filter_options():
                    print("[WARNING] 筛选设置可能不完整，但继续执行")
                
                # 5. 查找并下载文档
                success_count = await self.find_and_download_documents(10)
                
                # 6. 等待下载完成
                await asyncio.sleep(15)
                
                # 7. 最终统计
                final_files = list(self.download_dir.glob('*'))
                
                print(f"\n" + "="*50)
                print("              最终结果")
                print("="*50)
                print(f"下载触发次数: {success_count}")
                print(f"实际文件数量: {len(final_files)}")
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
                print(f"\n[WAIT] 保持浏览器30秒供检查...")
                await asyncio.sleep(30)
                await browser.close()

async def main():
    downloader = PreciseXPathDownloader()
    success = await downloader.run_precise_download()
    
    if success:
        print("\n[SUCCESS] 精确XPath筛选下载完成！")
    else:
        print("\n[FAILED] 精确XPath筛选下载失败")

if __name__ == "__main__":
    asyncio.run(main())