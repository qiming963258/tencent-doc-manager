#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
筛选功能测试器 - 只测试筛选，不扫描文档
"""

import asyncio
from playwright.async_api import async_playwright

class FilterOnlyTest:
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

    async def test_filter_only(self):
        """只测试筛选功能，不扫描文档"""
        print("\n" + "="*60)
        print("        筛选功能隔离测试")
        print("   只执行筛选，不扫描文档元素")
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
            
            # Dialog监听器
            page.on("dialog", lambda dialog: dialog.accept())
            print("[SETUP] Dialog监听器已设置")
            
            try:
                # 1. 登录
                await context.add_cookies(self.parse_cookies())
                await page.goto('https://docs.qq.com/desktop/', wait_until='domcontentloaded', timeout=30000)
                print("[SUCCESS] 页面加载完成")
                await asyncio.sleep(5)
                
                # 2. 点击筛选按钮
                print("\n[STEP 1] 点击筛选按钮...")
                filter_btn = await page.wait_for_selector('button:has-text("筛选")', timeout=10000)
                if filter_btn:
                    await filter_btn.click()
                    print("[SUCCESS] 筛选按钮点击成功")
                    await asyncio.sleep(3)
                else:
                    print("[ERROR] 筛选按钮未找到")
                    return False
                
                # 3. 设置筛选选项
                print("\n[STEP 2] 设置筛选选项...")
                
                # 选择"我所有的"
                owner_header = await page.wait_for_selector('header:has-text("所有者")', timeout=5000)
                if owner_header:
                    owner_radios = await page.query_selector_all('header:has-text("所有者") + div input[type="radio"]')
                    if len(owner_radios) >= 2:
                        await owner_radios[1].check()
                        print("[SUCCESS] '我所有的'选项已选中")
                    else:
                        print("[ERROR] 所有者选项不足")
                        
                # 选择"近1个月"
                time_header = await page.wait_for_selector('header:has-text("查看时间")', timeout=5000)
                if time_header:
                    time_radios = await page.query_selector_all('header:has-text("查看时间") + div input[type="radio"]')
                    if len(time_radios) >= 3:
                        await time_radios[2].check()
                        print("[SUCCESS] '近1个月'选项已选中")
                    else:
                        print("[ERROR] 时间选项不足")
                
                # 应用筛选
                apply_btn = await page.wait_for_selector('text=应用', timeout=5000)
                if apply_btn:
                    await apply_btn.click()
                    print("[SUCCESS] 筛选应用成功")
                    await asyncio.sleep(8)
                else:
                    print("[ERROR] 应用按钮未找到")
                
                # 4. 关键测试：筛选完成后什么都不做，观察是否有意外跳转
                print("\n[CRITICAL] 筛选完成，等待30秒观察页面行为...")
                print("[WATCH] 请观察是否有意外的页面跳转或点击")
                
                current_url = page.url
                print(f"[URL] 当前页面: {current_url}")
                
                # 等待30秒，每5秒检查一次URL
                for i in range(6):
                    await asyncio.sleep(5)
                    new_url = page.url
                    if new_url != current_url:
                        print(f"[ALERT] 检测到页面跳转: {current_url} -> {new_url}")
                        current_url = new_url
                    else:
                        print(f"[OK] 第{i+1}次检查，页面稳定")
                
                print(f"\n[FINAL] 最终页面: {page.url}")
                print("[RESULT] 如果没有跳转到文件内部，说明筛选功能正常")
                
                return True
                
            except Exception as e:
                print(f"[ERROR] 测试失败: {e}")
                return False
                
            finally:
                print(f"\n[WAIT] 保持浏览器10秒供观察...")
                await asyncio.sleep(10)
                await browser.close()

async def main():
    tester = FilterOnlyTest()
    success = await tester.test_filter_only()
    
    if success:
        print("\n[SUCCESS] 筛选功能隔离测试完成")
    else:
        print("\n[FAILED] 筛选功能隔离测试失败")

if __name__ == "__main__":
    asyncio.run(main())