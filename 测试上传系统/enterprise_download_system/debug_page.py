#!/usr/bin/env python3
"""
调试版本 - 查看页面实际内容和状态
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_page_content():
    """调试页面内容"""
    
    cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZvaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
    
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
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            extra_http_headers={
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
        )
        
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        print("🔍 调试页面访问...")
        
        # 访问桌面页面
        response = await page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded', timeout=30000)
        print(f"📊 状态码: {response.status}")
        
        # 等待页面加载
        await page.wait_for_timeout(10000)
        
        print(f"📄 标题: {await page.title()}")
        print(f"📍 URL: {page.url}")
        
        # 截取页面内容的前500字符
        content = await page.content()
        print(f"📝 页面内容长度: {len(content)}")
        print("📄 页面内容片段:")
        print(content[:1000])
        print("---")
        
        # 查找可能的文档列表元素
        possible_selectors = [
            '.desktop-file-list-item',
            '.file-item',
            '.desktop-list-view-item',
            '[data-testid*="file"]',
            '.document-item',
            '.file-row',
            '[class*="file"]',
            '[class*="document"]',
            '[class*="list"]'
        ]
        
        print("🔍 查找文档列表元素:")
        for selector in possible_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"✅ 找到 {selector}: {len(elements)} 个元素")
                else:
                    print(f"❌ {selector}: 0 个元素")
            except Exception as e:
                print(f"⚠️  {selector}: 错误 - {e}")
        
        # 查找任何包含"文档"、"document"、"file"的元素
        print("\n🔍 搜索相关文本:")
        try:
            doc_elements = await page.query_selector_all('text=/文档|document|file/i')
            print(f"包含文档相关文本的元素: {len(doc_elements)}")
            
            if doc_elements:
                for i, elem in enumerate(doc_elements[:5]):  # 只显示前5个
                    try:
                        text = await elem.inner_text()
                        print(f"  {i+1}. {text[:50]}...")
                    except:
                        print(f"  {i+1}. [无法获取文本]")
        except Exception as e:
            print(f"搜索相关文本失败: {e}")
        
        # 检查是否有任何可点击的元素
        print("\n🔍 查找可点击元素:")
        try:
            clickable = await page.query_selector_all('button, a, [onclick], [role="button"]')
            print(f"可点击元素数量: {len(clickable)}")
            
            if clickable:
                for i, elem in enumerate(clickable[:10]):  # 显示前10个
                    try:
                        text = await elem.inner_text()
                        if text.strip():
                            print(f"  {i+1}. {text.strip()[:30]}")
                    except:
                        pass
        except Exception as e:
            print(f"查找可点击元素失败: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page_content())