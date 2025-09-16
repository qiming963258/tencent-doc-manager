#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面元素探测器 - 专门找到真实的筛选按钮
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

class PageExplorer:
    def __init__(self):
        self.cookie_string = "fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; traceid=a473487816; TOK=a473487816963a48; hashkey=a4734878; dark_mode_setting=system; optimal_cdn_domain=docs.qq.com; ES2=f88c0411768984b9; _qpsvr_localtk=0.5895351222297797; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1ppSTZJbEZLVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1RZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; language=zh-CN; backup_cdn_domain=docs.gtimg.com"

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

    async def explore_all_clickable_elements(self):
        """探测页面上所有可点击的元素"""
        print("\n[EXPLORE] 探测所有可点击元素...")
        
        # 等待页面完全加载
        await asyncio.sleep(8)
        
        # 查找所有可能的可点击元素
        clickable_selectors = [
            'button',           # 所有按钮
            'a',               # 所有链接 
            '[role="button"]', # 角色为按钮的元素
            '[tabindex]',      # 可tab导航的元素
            '[onclick]',       # 有点击事件的元素
            'span[class*="click"]',  # class包含click的span
            'div[class*="click"]',   # class包含click的div
            'input[type="button"]',  # 按钮类型的input
            'input[type="submit"]',  # 提交按钮
            '.btn',            # 常见按钮class
            '.button',         # 常见按钮class
        ]
        
        all_clickable = {}
        
        for selector in clickable_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                print(f"[SELECTOR] {selector}: 找到 {len(elements)} 个元素")
                
                for element in elements:
                    try:
                        # 获取元素信息
                        tag_name = await element.evaluate('el => el.tagName')
                        text_content = await element.inner_text()
                        class_name = await element.get_attribute('class') or ''
                        id_attr = await element.get_attribute('id') or ''
                        role = await element.get_attribute('role') or ''
                        
                        # 清理文本
                        clean_text = text_content.strip() if text_content else ''
                        
                        # 只保留有意义的元素
                        if len(clean_text) > 0 and len(clean_text) < 200:
                            element_key = f"{tag_name}_{clean_text[:20]}_{class_name[:20]}"
                            
                            if element_key not in all_clickable:
                                all_clickable[element_key] = {
                                    'element': element,
                                    'tag': tag_name,
                                    'text': clean_text,
                                    'class': class_name,
                                    'id': id_attr,
                                    'role': role,
                                    'selector': selector
                                }
                    except:
                        continue
                        
            except Exception as e:
                print(f"[ERROR] {selector} 失败: {e}")
        
        return list(all_clickable.values())

    async def find_filter_related_elements(self, all_elements):
        """从所有元素中找到筛选相关的元素"""
        print(f"\n[FILTER] 从 {len(all_elements)} 个元素中查找筛选相关...")
        
        # 筛选关键词（中英文）
        filter_keywords = [
            # 中文关键词
            '筛选', '过滤', '筛选器', 'filter', 
            '我的', 'my', '我的文档', 'my docs',
            '时间', 'time', '日期', 'date',
            '近期', 'recent', '最近', 'latest',
            '一个月', 'month', '近一个月', 'last month',
            '全部', 'all', '所有', 'everything',
            # 可能的UI文本
            '下拉', 'dropdown', '选择', 'select',
            '排序', 'sort', '分类', 'category'
        ]
        
        filter_elements = []
        
        for element_info in all_elements:
            text = element_info['text'].lower()
            class_name = element_info['class'].lower()
            id_attr = element_info['id'].lower()
            
            # 检查是否包含筛选关键词
            is_filter_related = any(
                keyword in text or 
                keyword in class_name or 
                keyword in id_attr 
                for keyword in filter_keywords
            )
            
            if is_filter_related:
                filter_elements.append(element_info)
                print(f"[FOUND] {element_info['tag']} - {element_info['text'][:30]} - {element_info['class'][:30]}")
        
        return filter_elements

    async def interactive_click_test(self, filter_elements):
        """交互式点击测试筛选元素"""
        print(f"\n[TEST] 交互式测试 {len(filter_elements)} 个筛选元素...")
        
        for i, element_info in enumerate(filter_elements):
            try:
                element = element_info['element']
                text = element_info['text']
                tag = element_info['tag']
                class_name = element_info['class']
                
                print(f"\n[TEST {i+1}] 测试元素:")
                print(f"  标签: {tag}")
                print(f"  文本: {text[:50]}")
                print(f"  类名: {class_name[:50]}")
                
                # 滚动到元素
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                
                # 高亮元素
                await self.page.evaluate('''(element) => {
                    element.style.border = '5px solid red';
                    element.style.backgroundColor = 'yellow';
                    element.style.zIndex = '9999';
                }''', element)
                
                print(f"[HIGHLIGHT] 元素已高亮红色，暂停10秒供观察...")
                await asyncio.sleep(10)
                
                # 尝试点击
                print(f"[CLICK] 尝试点击...")
                await element.click()
                await asyncio.sleep(3)
                
                # 检查页面是否有变化
                print(f"[CHECK] 检查页面变化...")
                await asyncio.sleep(2)
                
                # 移除高亮
                await self.page.evaluate('''(element) => {
                    element.style.border = '';
                    element.style.backgroundColor = '';
                    element.style.zIndex = '';
                }''', element)
                
                print(f"[COMPLETE] 元素 {i+1} 测试完成")
                
                # 每个元素之间暂停
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[ERROR] 测试元素 {i+1} 失败: {e}")

    async def save_page_html(self):
        """保存页面HTML供分析"""
        try:
            content = await self.page.content()
            with open('current_page.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[SAVE] 页面HTML已保存到 current_page.html")
        except Exception as e:
            print(f"[ERROR] 保存HTML失败: {e}")

    async def run_exploration(self):
        """执行页面探测"""
        print("\n" + "="*60)
        print("              页面元素探测器")
        print("            专门找到真实的筛选按钮")  
        print("="*60)
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            self.page = await context.new_page()
            
            try:
                # 1. 设置Cookie并访问
                await context.add_cookies(self.parse_cookies())
                await self.page.goto('https://docs.qq.com/desktop/', 
                                    wait_until='domcontentloaded', timeout=30000)
                
                print("[SUCCESS] 页面加载完成")
                
                # 2. 保存页面HTML
                await self.save_page_html()
                
                # 3. 探测所有可点击元素
                all_clickable = await self.explore_all_clickable_elements()
                
                # 4. 筛选出筛选相关元素
                filter_elements = await self.find_filter_related_elements(all_clickable)
                
                if not filter_elements:
                    print("\n[ERROR] 未找到任何筛选相关元素!")
                    print("[INFO] 可能的原因:")
                    print("  1. 筛选按钮使用了特殊的实现方式")
                    print("  2. 筛选功能在页面的其他位置")
                    print("  3. 需要先执行某些操作才能显示筛选")
                    
                    # 显示前20个可点击元素供参考
                    print(f"\n[REFERENCE] 前20个可点击元素:")
                    for i, elem in enumerate(all_clickable[:20]):
                        print(f"  [{i+1}] {elem['tag']} - {elem['text'][:30]} - {elem['class'][:20]}")
                else:
                    # 5. 交互式测试筛选元素
                    await self.interactive_click_test(filter_elements)
                
                return True
                
            except Exception as e:
                print(f"[ERROR] 探测失败: {e}")
                return False
                
            finally:
                print(f"\n[WAIT] 保持浏览器30秒供手动检查...")
                await asyncio.sleep(30)
                await browser.close()

async def main():
    explorer = PageExplorer()
    success = await explorer.run_exploration()
    
    if success:
        print("\n[COMPLETE] 页面探测完成")
        print("[CHECK] 请查看:")
        print("  1. 终端输出的筛选元素列表")
        print("  2. current_page.html 文件")
        print("  3. 浏览器中高亮显示的元素")
    else:
        print("\n[FAILED] 页面探测失败")

if __name__ == "__main__":
    asyncio.run(main())