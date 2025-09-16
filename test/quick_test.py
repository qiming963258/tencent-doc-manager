#!/usr/bin/env python3
"""
快速测试脚本 - 测试导航和查找文档
"""

import asyncio
from playwright.async_api import async_playwright

async def quick_test():
    cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZvaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJOaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
    
    # 解析Cookie
    cookies = []
    for cookie_pair in cookie_string.split('; '):
        if '=' in cookie_pair:
            name, value = cookie_pair.split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': '.docs.qq.com',
                'path': '/'
            })
    
    async with async_playwright() as playwright:
        print("🚀 启动浏览器...")
        browser = await playwright.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            extra_http_headers={'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'}
        )
        
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        print("🏠 访问桌面页面...")
        await page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(8000)
        
        print(f"📄 标题: {await page.title()}")
        print(f"📍 URL: {page.url}")
        
        # 尝试点击Cloud Docs
        print("🔍 查找Cloud Docs按钮...")
        try:
            cloud_docs = await page.wait_for_selector('text=Cloud Docs', timeout=5000)
            if cloud_docs:
                print("✅ 找到Cloud Docs按钮，点击...")
                await cloud_docs.click()
                await page.wait_for_timeout(10000)
                print(f"📄 点击后标题: {await page.title()}")
                print(f"📍 点击后URL: {page.url}")
        except Exception as e:
            print(f"⚠️  Cloud Docs点击失败: {e}")
        
        # 尝试直接访问mydocs
        print("🔗 尝试直接访问mydocs...")
        try:
            await page.goto('https://docs.qq.com/desktop/mydocs', wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(8000)
            print(f"📄 mydocs标题: {await page.title()}")
            print(f"📍 mydocs URL: {page.url}")
        except Exception as e:
            print(f"⚠️  mydocs访问失败: {e}")
        
        # 查找文档元素
        print("🔍 查找文档元素...")
        file_selectors = [
            '.desktop-file-list-item',
            '.file-item', 
            '.desktop-list-view-item',
            '[data-testid*="file"]',
            '[class*="file"]',
            '[class*="list"]',
            'tr[class*="row"]',
            'div[role="row"]'
        ]
        
        for selector in file_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"✅ 找到 {selector}: {len(elements)} 个元素")
                    # 显示前3个元素的文本
                    for i, elem in enumerate(elements[:3]):
                        try:
                            text = await elem.inner_text()
                            if text.strip():
                                print(f"   {i+1}. {text.strip()[:50]}...")
                        except:
                            pass
                    
                    if len(elements) >= 1:
                        # 尝试对第一个元素右键点击
                        print("🖱️  尝试右键点击第一个元素...")
                        try:
                            await elements[0].scroll_into_view_if_needed()
                            await page.wait_for_timeout(1000)
                            await elements[0].click(button='right')
                            await page.wait_for_timeout(3000)
                            
                            # 查找下载选项
                            download_options = await page.query_selector_all('text=下载')
                            print(f"📋 找到下载选项: {len(download_options)} 个")
                            
                            if download_options:
                                print("✅ 发现下载选项！")
                                break
                        except Exception as e:
                            print(f"⚠️  右键测试失败: {e}")
                    break
                else:
                    print(f"❌ {selector}: 0 个元素")
            except Exception as e:
                print(f"⚠️  {selector}: 错误 - {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(quick_test())