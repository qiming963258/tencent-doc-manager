#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扩展筛选测试器 - 尝试不同的筛选条件获得更多文档
"""

import asyncio
from playwright.async_api import async_playwright

class ExtendedFilterTest:
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

    async def test_different_filters(self):
        """测试不同的筛选条件，寻找更多文档"""
        print("\n" + "="*60)
        print("        扩展筛选测试")
        print("   测试不同筛选条件获得更多文档")
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
            page.on("dialog", lambda dialog: dialog.accept())
            
            try:
                # 1. 登录
                await context.add_cookies(self.parse_cookies())
                await page.goto('https://docs.qq.com/desktop/', wait_until='domcontentloaded', timeout=30000)
                print("[SUCCESS] 页面加载完成")
                await asyncio.sleep(5)
                
                # 测试方案1：全部文档 + 全部时间
                print("\n" + "="*50)
                print("[TEST 1] 尝试：全部文档 + 全部时间")
                await self.test_filter_combination(page, "全部", "全部时间")
                
                # 等待3秒
                await asyncio.sleep(3)
                
                # 测试方案2：我所有的 + 全部时间
                print("\n" + "="*50)
                print("[TEST 2] 尝试：我所有的 + 全部时间")
                await self.test_filter_combination(page, "我所有的", "全部时间")
                
                return True
                
            except Exception as e:
                print(f"[ERROR] 测试失败: {e}")
                return False
                
            finally:
                print(f"\n[WAIT] 保持浏览器15秒供观察...")
                await asyncio.sleep(15)
                await browser.close()

    async def test_filter_combination(self, page, owner_choice, time_choice):
        """测试特定的筛选组合"""
        try:
            # 点击筛选按钮
            filter_btn = await page.wait_for_selector('button:has-text("筛选")', timeout=10000)
            if filter_btn:
                await filter_btn.click()
                print(f"[SUCCESS] 筛选按钮点击成功")
                await asyncio.sleep(3)
            else:
                print(f"[ERROR] 筛选按钮未找到")
                return
            
            # 设置所有者选项
            print(f"[SETTING] 设置所有者: {owner_choice}")
            owner_radios = await page.query_selector_all('header:has-text("所有者") + div input[type="radio"]')
            if owner_choice == "全部" and len(owner_radios) >= 1:
                await owner_radios[0].check()  # 第1项：全部
                print(f"[SUCCESS] 已选择: 全部")
            elif owner_choice == "我所有的" and len(owner_radios) >= 2:
                await owner_radios[1].check()  # 第2项：我所有的
                print(f"[SUCCESS] 已选择: 我所有的")
            
            # 设置时间选项
            print(f"[SETTING] 设置时间: {time_choice}")
            time_radios = await page.query_selector_all('header:has-text("查看时间") + div input[type="radio"]')
            if time_choice == "全部时间" and len(time_radios) >= 1:
                await time_radios[0].check()  # 第1项：全部时间
                print(f"[SUCCESS] 已选择: 全部时间")
            elif time_choice == "近1个月" and len(time_radios) >= 3:
                await time_radios[2].check()  # 第3项：近1个月
                print(f"[SUCCESS] 已选择: 近1个月")
            
            # 应用筛选
            apply_btn = await page.wait_for_selector('text=应用', timeout=5000)
            if apply_btn:
                await apply_btn.click()
                print(f"[SUCCESS] 筛选应用成功")
                await asyncio.sleep(8)
            
            # 统计文档数量
            await self.count_documents(page, f"{owner_choice} + {time_choice}")
            
        except Exception as e:
            print(f"[ERROR] 筛选组合测试失败: {e}")

    async def count_documents(self, page, filter_name):
        """统计当前筛选条件下的文档数量"""
        print(f"\n[COUNT] 统计 {filter_name} 筛选结果...")
        
        # 等待页面稳定
        await asyncio.sleep(5)
        
        doc_selectors = [
            'a[href*="/doc/"]',
            'a[href*="/sheet/"]', 
            'a[href*="/slide/"]',
            'a[href*="/form/"]'
        ]
        
        total_docs = {}
        
        # 初始扫描
        for selector in doc_selectors:
            try:
                elements = await page.query_selector_all(selector)
                print(f"[COUNT] {selector}: {len(elements)} 个")
                
                for element in elements:
                    try:
                        href = await element.get_attribute('href')
                        if href and href not in total_docs:
                            title = await element.evaluate('(el) => el.textContent || el.innerText || ""')
                            total_docs[href] = title.strip()[:30]
                    except:
                        continue
            except:
                continue
        
        print(f"[RESULT] {filter_name}: 共找到 {len(total_docs)} 个不重复文档")
        
        # 尝试滚动查看是否有更多
        if len(total_docs) > 0:
            print(f"[SCROLL] 尝试滚动获取更多文档...")
            
            # 滚动到底部
            await page.evaluate('() => window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(4)
            
            # 再次统计
            total_after_scroll = {}
            for selector in doc_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        try:
                            href = await element.get_attribute('href')
                            if href and href not in total_after_scroll:
                                title = await element.evaluate('(el) => el.textContent || el.innerText || ""')
                                total_after_scroll[href] = title.strip()[:30]
                        except:
                            continue
                except:
                    continue
            
            if len(total_after_scroll) > len(total_docs):
                print(f"[SCROLL] 滚动后新增 {len(total_after_scroll) - len(total_docs)} 个文档")
                print(f"[FINAL] {filter_name}: 总计 {len(total_after_scroll)} 个文档")
            else:
                print(f"[SCROLL] 滚动后无新增文档")
                print(f"[FINAL] {filter_name}: 总计 {len(total_docs)} 个文档")

async def main():
    tester = ExtendedFilterTest()
    success = await tester.test_different_filters()
    
    if success:
        print("\n[SUCCESS] 扩展筛选测试完成")
    else:
        print("\n[FAILED] 扩展筛选测试失败")

if __name__ == "__main__":
    asyncio.run(main())