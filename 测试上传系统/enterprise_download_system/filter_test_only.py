#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
筛选功能专项测试器 - 只测试弹窗内radio按钮选择
"""

import asyncio
from playwright.async_api import async_playwright

class FilterTest:
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

    async def test_filter_selection(self):
        """专门测试筛选弹窗内的radio按钮选择"""
        print("\n" + "="*60)
        print("        筛选功能专项测试")
        print("   只测试弹窗内radio按钮选择功能")
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
            
            # 重要：在操作前设置dialog监听器
            page.on("dialog", lambda dialog: dialog.accept())
            print("[SETUP] 已设置dialog监听器")
            
            try:
                # 1. 登录
                await context.add_cookies(self.parse_cookies())
                await page.goto('https://docs.qq.com/desktop/', wait_until='domcontentloaded', timeout=30000)
                print("[SUCCESS] 页面加载完成")
                await asyncio.sleep(5)
                
                # 2. 点击筛选按钮
                print("\n[STEP 1] 点击筛选按钮...")
                
                filter_selectors = [
                    'button:has-text("筛选")',
                    '.desktop-filter-button-inner'
                ]
                
                filter_clicked = False
                for selector in filter_selectors:
                    try:
                        print(f"[试图] 选择器: {selector}")
                        filter_btn = await page.wait_for_selector(selector, timeout=5000)
                        if filter_btn:
                            await filter_btn.click()
                            print(f"[SUCCESS] 筛选按钮点击成功!")
                            filter_clicked = True
                            await asyncio.sleep(3)
                            break
                    except Exception as e:
                        print(f"[SKIP] {selector} 失败: {e}")
                        continue
                
                if not filter_clicked:
                    print("[ERROR] 筛选按钮点击失败")
                    return False
                
                # 3. 等待筛选弹窗出现并分析
                print("\n[STEP 2] 分析筛选弹窗...")
                await asyncio.sleep(5)
                
                # 查找所有radio按钮
                radio_buttons = await page.query_selector_all('input[type="radio"]')
                print(f"[FOUND] 筛选弹窗中找到 {len(radio_buttons)} 个radio按钮")
                
                if not radio_buttons:
                    print("[ERROR] 未找到任何radio按钮")
                    return False
                
                # 4. 测试radio按钮选择
                print("\n[STEP 3] 测试radio按钮选择...")
                
                success_count = 0
                
                for i, radio in enumerate(radio_buttons):
                    try:
                        # 检查当前状态
                        is_checked_before = await radio.is_checked()
                        print(f"[测试 {i+1}] Radio按钮初始状态: checked={is_checked_before}")
                        
                        # 尝试选中
                        await radio.check()
                        await asyncio.sleep(1)
                        
                        # 验证选择结果
                        is_checked_after = await radio.is_checked()
                        print(f"[测试 {i+1}] Radio按钮选择后状态: checked={is_checked_after}")
                        
                        if is_checked_after:
                            print(f"[SUCCESS {i+1}] Radio按钮选择成功!")
                            success_count += 1
                        else:
                            print(f"[FAIL {i+1}] Radio按钮选择失败")
                        
                    except Exception as e:
                        print(f"[ERROR {i+1}] Radio按钮测试异常: {e}")
                        continue
                
                # 5. 特别测试用户提供的XPath
                print("\n[STEP 4] 测试用户提供的XPath...")
                try:
                    xpath_radio = await page.wait_for_selector('xpath=/html/body/div[1]/div[1]/div[4]/div/div/div/div/div[1]/div/div[6]/div[3]/input', timeout=5000)
                    if xpath_radio:
                        before_check = await xpath_radio.is_checked()
                        await xpath_radio.check()
                        await asyncio.sleep(1)
                        after_check = await xpath_radio.is_checked()
                        
                        print(f"[XPATH] 用户XPath测试: {before_check} -> {after_check}")
                        if after_check:
                            print("[SUCCESS] 用户XPath选择成功!")
                            success_count += 1
                        else:
                            print("[FAIL] 用户XPath选择失败")
                    else:
                        print("[INFO] 用户XPath元素未找到")
                except Exception as e:
                    print(f"[ERROR] 用户XPath测试失败: {e}")
                
                # 6. 总结结果
                print(f"\n" + "="*50)
                print("              测试结果")
                print("="*50)
                print(f"筛选按钮点击: {'✅' if filter_clicked else '❌'}")
                print(f"Radio按钮总数: {len(radio_buttons)}")
                print(f"成功选择数量: {success_count}")
                print(f"选择成功率: {success_count/max(len(radio_buttons),1)*100:.1f}%")
                
                # 保持浏览器打开供观察
                print(f"\n[等待] 保持浏览器30秒供检查...")
                await asyncio.sleep(30)
                
                return success_count > 0
                
            except Exception as e:
                print(f"[ERROR] 测试执行失败: {e}")
                return False
                
            finally:
                await browser.close()

async def main():
    tester = FilterTest()
    success = await tester.test_filter_selection()
    
    if success:
        print("\n[SUCCESS] 筛选功能测试通过!")
    else:
        print("\n[FAILED] 筛选功能测试失败")

if __name__ == "__main__":
    asyncio.run(main())