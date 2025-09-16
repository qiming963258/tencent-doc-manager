#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面状态诊断器 - 检查登录状态和页面元素
"""

import asyncio
from playwright.async_api import async_playwright

class PageDiagnostic:
    def __init__(self):
        self.cookie_string = "fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; traceid=a473487816; TOK=a473487816963a48; hashkey=a4734878; dark_mode_setting=system; optimal_cdn_domain=docs.qq.com; ES2=f88c0411768984b9; _qpsvr_localtk=0.5895351222297797; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1ppSTZJbEZKVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1pZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; language=zh-CN; backup_cdn_domain=docs.gtimg.com"
    
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

    async def diagnose_page(self):
        print("\n" + "="*60)
        print("        页面状态诊断器")
        print("="*60)
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # 1. 设置Cookie并访问页面
                await context.add_cookies(self.parse_cookies())
                await page.goto('https://docs.qq.com/desktop/', 
                               wait_until='domcontentloaded', timeout=30000)
                
                print("[SUCCESS] 页面加载完成")
                
                # 等待页面完全稳定
                print("\n[WAIT] 等待页面完全稳定（15秒）...")
                await asyncio.sleep(15)
                
                # 2. 检查页面基本信息
                print("\n[CHECK] 检查页面基本信息...")
                title = await page.title()
                url = page.url
                print(f"页面标题: {title}")
                print(f"当前URL: {url}")
                
                # 3. 检查是否有登录相关的提示
                login_indicators = [
                    'text=登录',
                    'text=login', 
                    '.login-button',
                    'button:has-text("登录")'
                ]
                
                print(f"\n[CHECK] 检查登录状态...")
                login_found = False
                for indicator in login_indicators:
                    try:
                        element = await page.wait_for_selector(indicator, timeout=2000)
                        if element:
                            login_found = True
                            print(f"[WARNING] 发现登录元素: {indicator}")
                            break
                    except:
                        continue
                
                if not login_found:
                    print("[OK] 未发现登录提示，可能已登录")
                
                # 4. 搜索所有可能的筛选相关元素
                print(f"\n[SEARCH] 搜索所有可能的筛选元素...")
                
                filter_keywords = ['筛选', '过滤', 'filter', 'Filter']
                filter_elements_found = []
                
                for keyword in filter_keywords:
                    try:
                        elements = await page.query_selector_all(f'*:has-text("{keyword}")')
                        print(f"包含'{keyword}'的元素: {len(elements)} 个")
                        filter_elements_found.extend(elements)
                    except:
                        continue
                
                # 5. 搜索所有button元素
                print(f"\n[SEARCH] 搜索所有button元素...")
                all_buttons = await page.query_selector_all('button')
                print(f"页面总计button元素: {len(all_buttons)} 个")
                
                # 显示前10个button的文本
                print("前10个button的文本内容:")
                for i, button in enumerate(all_buttons[:10]):
                    try:
                        text = await button.evaluate('el => el.textContent || el.innerText || ""')
                        class_name = await button.get_attribute('class') or ''
                        print(f"  [{i+1}] '{text.strip()}' - class: {class_name[:50]}")
                    except:
                        continue
                
                # 6. 搜索所有可能的class包含filter的元素
                print(f"\n[SEARCH] 搜索class包含'filter'的元素...")
                filter_class_elements = await page.query_selector_all('[class*="filter"]')
                print(f"class包含'filter'的元素: {len(filter_class_elements)} 个")
                
                for i, element in enumerate(filter_class_elements[:5]):
                    try:
                        tag = await element.evaluate('el => el.tagName')
                        class_name = await element.get_attribute('class')
                        text = await element.evaluate('el => el.textContent || el.innerText || ""')
                        print(f"  [{i+1}] {tag} - '{text.strip()[:30]}' - {class_name}")
                    except:
                        continue
                
                # 7. 搜索desktop相关元素
                print(f"\n[SEARCH] 搜索class包含'desktop'的元素...")
                desktop_elements = await page.query_selector_all('[class*="desktop"]')
                print(f"class包含'desktop'的元素: {len(desktop_elements)} 个")
                
                # 显示前5个desktop元素
                for i, element in enumerate(desktop_elements[:5]):
                    try:
                        tag = await element.evaluate('el => el.tagName')
                        class_name = await element.get_attribute('class')
                        text = await element.evaluate('el => (el.textContent || el.innerText || "").slice(0, 20)')
                        print(f"  [{i+1}] {tag} - '{text.strip()}' - {class_name[:50]}")
                    except:
                        continue
                
                # 8. 保持浏览器打开供观察
                print(f"\n[WAIT] 保持浏览器60秒供手动观察...")
                await asyncio.sleep(60)
                
            except Exception as e:
                print(f"[ERROR] 诊断失败: {e}")
                
            finally:
                await browser.close()

async def main():
    diagnostic = PageDiagnostic()
    await diagnostic.diagnose_page()

if __name__ == "__main__":
    asyncio.run(main())